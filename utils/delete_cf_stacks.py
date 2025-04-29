"""
This script requires some explanation. Deleting Cloudformation stacks with retaining resources is painful.

You can only retain resources if the stack state is DELETE_FAILED (!). Otherwise, CF doesn't let you specify retained resources.
The workaround looks like that:
- You create an IAM role with zero permissions, that doesn't have permissions to delete anything.
- You try to delete the stack with that role
- This will make the CF stack DELETE_FAILED - with an error something like 'badRole does not have permission to delete an SQS queue'
- After this, you try to delete it with a proper (admin) role, and you can now specify retained resources too

So this script follows that logic: first, try to delete the stack with a "bad" role, then try to delete it with an admin role.
"""
import argparse
import json
import sys
import time
from typing import Dict, List, Optional

from botocore.exceptions import WaiterError, ClientError
import boto3

temp_role_bad_name = "TempBadRoleForShv2toV3"
temp_role_name_admin = "TempAdminRoleForShv2toV3"


def create_session(region: str, profile: Optional[str] = None) -> boto3.Session:
    boto_args: Dict[str, str] = {"region_name": region}
    if profile:
        boto_args["profile_name"] = profile
    return boto3.Session(**boto_args)


def create_temp_iam_role(
    session: boto3.Session, role_name: str, policy_document: Dict, is_admin: bool
) -> str:
    print(f"  > Checking for IAM role: {role_name}")

    iam_client = session.client("iam")
    role_arn = None

    # Check if role already exists
    try:
        role_response = iam_client.get_role(RoleName=role_name)
        role_arn = role_response["Role"]["Arn"]
        print(f"  > Role {role_name} already exists, using existing role")
        return role_arn
    except iam_client.exceptions.NoSuchEntityException:
        # Role doesn't exist, create a new one
        print(f"  > Creating temporary IAM role for CloudFormation stack deletion: {role_name}")

        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"Service": "cloudformation.amazonaws.com"},
                }
            ],
        }

        role_response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Temporary role for CloudFormation stack deletion",
        )

        role_arn = role_response["Role"]["Arn"]

        if is_admin:
            # Attach AdministratorAccess policy
            iam_client.attach_role_policy(
                RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess"
            )
        else:
            # Attach custom policy that's not allowed to delete anything
            policy_name = "TempCloudformationManagingShv2toV3"
            iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
            )

        return role_arn


def create_temp_iam_roles(session: boto3.Session) -> tuple:
    policy_document_for_bad_role = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": [
                    "cloudformation:DeleteStack",
                    "cloudformation:DescribeStackResources",
                    "iam:PassRole",
                ],
                "Effect": "Allow",
                "Resource": "*",
            }
        ],
    }

    bad_role_arn = create_temp_iam_role(
        session, temp_role_bad_name, policy_document_for_bad_role, False
    )
    admin_role_arn = create_temp_iam_role(session, temp_role_name_admin, None, is_admin=True)

    print(f"  > IAM role permissions need a while to propagate. Waiting 15 seconds...")
    time.sleep(15)

    return bad_role_arn, admin_role_arn


def delete_stack(
    session: boto3.Session,
    stack_name: str,
    role_arn: str,
    admin_role_arn: str,
    retain_resources: Optional[List[str]] = None,
) -> None:
    print(f"  > Deleting stack: {stack_name}...")

    cf_client = session.client("cloudformation")

    # Check if stack exists and its status
    try:
        stack_response = cf_client.describe_stacks(StackName=stack_name)
        stack = stack_response["Stacks"][0]
        stack_status = stack["StackStatus"]
    except ClientError as e:
        if "does not exist" in str(e):
            print(f"  > Stack {stack_name} does not exist, skipping deletion.")
            return
        else:
            print(f"Error checking stack {stack_name}: {e}")
            return

    # If no retained resources, use admin role to delete directly
    if not retain_resources:
        print(f"  > No retained resources for {stack_name}, deleting with admin role...")
        try:
            cf_client.delete_stack(StackName=stack_name, RoleARN=admin_role_arn)
        except Exception as e:
            if "is invalid or cannot be assumed" in str(e):
                print(
                    "  > The IAM role did not propagate yet. Wait a minute, then re-run the script."
                )
                sys.exit(0)
            print(f"Error deleting stack with admin role: {e}")
    else:
        # If the stack is already in DELETE_FAILED state, try to delete with admin role
        if stack_status == "DELETE_FAILED":
            print(f"  > Stack {stack_name} is in DELETE_FAILED state, deleting with admin role...")
            try:
                delete_params = {"StackName": stack_name, "RoleARN": admin_role_arn}
                if retain_resources:
                    delete_params["RetainResources"] = retain_resources
                cf_client.delete_stack(**delete_params)
            except Exception as e:
                print(f"Error deleting stack in DELETE_FAILED state: {e}")
        else:
            # With retained resources, first attempt with temp role to get to DELETE_FAILED state
            print(
                f"  > Stack {stack_name} has retained resources, attempting deletion with temp role first..."
            )
            try:
                # First try with temp role to get to DELETE_FAILED state
                cf_client.delete_stack(StackName=stack_name, RoleARN=role_arn)

                # Wait for stack to enter DELETE_FAILED state
                print("  > Waiting for potential DELETE_FAILED state...")
                time.sleep(10)

                # Check if stack is now in DELETE_FAILED state
                try:
                    updated_stack = cf_client.describe_stacks(StackName=stack_name)["Stacks"][0]
                    updated_status = updated_stack["StackStatus"]

                    # If it's in DELETE_FAILED state, retry with admin role and retain resources
                    if updated_status == "DELETE_FAILED":
                        print(
                            f"  > Stack {stack_name} is now in DELETE_FAILED state, deleting with admin role..."
                        )
                        delete_params = {
                            "StackName": stack_name,
                            "RoleARN": admin_role_arn,
                            "RetainResources": retain_resources,
                        }
                        cf_client.delete_stack(**delete_params)
                except ClientError:
                    # Stack might be gone already
                    pass
            except Exception as e:
                if "is invalid or cannot be assumed" in str(e):
                    print(
                        "  > The IAM role did not propagate yet. Wait a minute, then re-run the script."
                    )
                    sys.exit(0)

                print(f"Error in first delete attempt: {e}")
                # Try with admin role and retain resources
                try:
                    delete_params = {
                        "StackName": stack_name,
                        "RoleARN": admin_role_arn,
                        "RetainResources": retain_resources,
                    }
                    cf_client.delete_stack(**delete_params)
                except Exception as e2:
                    print(f"Error in second delete attempt: {e2}")

    # Wait for the stack deletion to complete
    try:
        print(f"  > Waiting for stack deletion to complete...")
        waiter = cf_client.get_waiter("stack_delete_complete")
        waiter.wait(StackName=stack_name, WaiterConfig={"Delay": 10, "MaxAttempts": 30})
        print(f"  > Stack {stack_name} successfully deleted")
    except WaiterError:
        print(f"  > Stack {stack_name} deletion did not complete within the wait time")
    except ClientError as e:
        if "does not exist" in str(e):
            print(f"  > Stack {stack_name} was successfully deleted")
        else:
            print(f"Error waiting for stack {stack_name} deletion: {e}")
    except Exception as e:
        print(f"Error during stack {stack_name} deletion process: {e}")


def delete_temp_iam_roles(session: boto3.Session) -> None:
    print("  > Cleaning up temporary IAM roles...")

    iam_client = session.client("iam")

    # Delete the basic role
    try:
        print(f"  > Deleting temporary role: {temp_role_bad_name}")
        policy_name = "TempCloudformationManagingShv2toV3"
        try:
            iam_client.delete_role_policy(RoleName=temp_role_bad_name, PolicyName=policy_name)
            print(f"  > Deleted inline policy {policy_name} from role {temp_role_bad_name}")
        except iam_client.exceptions.NoSuchEntityException:
            pass  # Policy might not exist

        iam_client.delete_role(RoleName=temp_role_bad_name)
        print(f"  > Successfully deleted role: {temp_role_bad_name}")
    except iam_client.exceptions.NoSuchEntityException:
        print(f"  > Role {temp_role_bad_name} does not exist, skipping deletion")
    except Exception as e:
        print(f"  > Error deleting role {temp_role_bad_name}: {e}")

    # Delete the admin role
    try:
        print(f"  > Deleting temporary role: {temp_role_name_admin}")
        try:
            iam_client.detach_role_policy(
                RoleName=temp_role_name_admin,
                PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess",
            )
            print(f"  > Detached AdministratorAccess policy from role {temp_role_name_admin}")
        except iam_client.exceptions.NoSuchEntityException:
            pass  # Policy might not be attached

        iam_client.delete_role(RoleName=temp_role_name_admin)
        print(f"  > Successfully deleted role: {temp_role_name_admin}")
    except iam_client.exceptions.NoSuchEntityException:
        print(f"  > Role {temp_role_name_admin} does not exist, skipping deletion")
    except Exception as e:
        print(f"  > Error deleting role {temp_role_name_admin}: {e}")


def delete_stacks(region: str, profile: Optional[str] = None) -> None:
    print(
        "WARNING: This script will delete CloudFormation stacks while retaining specific resources."
    )
    print("Make sure your Terraform deployment is fully functional before proceeding.")
    print("\nSummary of what this script will do:")
    print("1. Create temporary IAM roles for CloudFormation stack deletion")
    print("2. Delete Spacelift CloudFormation stacks in a specific order.")
    print("   - For stacks without retained resources: delete directly with admin role")
    print("   - For stacks with retained resources: first attempt with non-admin role,")
    print("     then with admin role to properly handle retained resources")
    print("3. Clean up the temporary IAM roles when finished")

    confirm = input("\nAre you sure you want to proceed? (y/n): ")
    if confirm.lower() != "y":
        print("Operation cancelled.")
        sys.exit(1)

    session = create_session(region, profile)

    bad_role_arn, admin_role_arn = create_temp_iam_roles(session)

    # Define stacks and resources to retain
    stacks = [
        {
            "name": "spacelift-monitoring",
            "retain": [],  # <-- Add Logical IDs here if you'd like to retain them
        },
        {"name": "spacelift-services", "retain": []},
        {"name": "spacelift-services-infra", "retain": []},
        {"name": "spacelift-services-loadbalancer", "retain": []},
        {
            "name": "spacelift-infra",
            "retain": [
                "AccessLogsBucketPolicy",  # Related to AccessLogsBucket - let the user manually delete it if they want to
                "AdditionalRootCAsSecret",
                "AsyncJobsFIFOQueue",
                "AsyncJobsQueue",
                "CronjobsQueue",
                "DBConnectionStringSecret",
                "DBSecretTargetAttachment",
                "DeadletterFIFOQueue",
                "DeadletterQueue",
                "ECRRepository",
                "EventsInboxQueue",
                "ExternalValuesSecret",
                "IoTMessageSenderRole",
                "IoTMessageSendingRule",
                "IoTQueue",
                "LauncherECRRepository",
                "SAMLCredentialsSecret",
                "SlackCredentialsSecret",
                "WebhooksQueue",
                "XrayECRRepository",  # Can't be deleted as it's not empty. Needs to be deleted manually.
            ],
        },
        {
            "name": "spacelift-infra-db",
            "retain": ["DBCluster", "DBClusterParameterGroup", "DBInstance", "DBSubnetGroup"],
        },
        {"name": "spacelift-infra-db-secrets", "retain": []},
        {
            "name": "spacelift-infra-vpc-config",
            "retain": [
                "BastionSecurityGroupDatabaseEgressRule",  # In case the user uses a bastion host, let's keep it. Can be deleted otherwise.
                "InternetGateway",
                "InternetGatewayRouteTable1",
                "InternetGatewayRouteTable1OutboundTrafficRoute",
                "InternetGatewayRouteTableSubnetAssociation1",
                "InternetGatewayVPCAttachment",
                "NATGateway1",
                "NATGateway2",
                "NATGateway3",
                "NATGatewayEIP1",
                "NATGatewayEIP2",
                "NATGatewayEIP3",
                "NATGatewayRouteTable1",
                "NATGatewayRouteTable1OutboundTrafficRoute",
                "NATGatewayRouteTable1SubnetAssociation",
                "NATGatewayRouteTable2",
                "NATGatewayRouteTable2OutboundTrafficRoute",
                "NATGatewayRouteTable2SubnetAssociation",
                "NATGatewayRouteTable3",
                "NATGatewayRouteTable3OutboundTrafficRoute",
                "NATGatewayRouteTable3SubnetAssociation",
                "PublicSubnet1",
                "PublicSubnet2",
                "PublicSubnet3",
            ],
        },
        {
            "name": "spacelift-infra-vpc",
            "retain": [
                "BastionSecurityGroup",  # Can't be deleted since the database security group references it. Needs to be deleted manually.
                "DatabaseSecurityGroup",
                "DrainSecurityGroup",
                "InstallationTaskSecurityGroup",  # Can't be deleted since the database security group references it. Needs to be deleted manually.
                "LoadBalancerSecurityGroup",
                "PrivateSubnet1",
                "PrivateSubnet2",
                "PrivateSubnet3",
                "SchedulerSecurityGroup",
                "ServerSecurityGroup",
                "VPC",
            ],
        },
        {"name": "spacelift-infra-s3-policies", "retain": []},
        {
            "name": "spacelift-infra-s3",
            "retain": [
                "AccessLogsBucket",  # Can't be deleted as it's not empty. Needs to be deleted manually.
                "BucketLogsBucket",  # Can't be deleted as it's not empty. Needs to be deleted manually.
                "DeliveriesBucket",
                "DownloadsBucket",
                "LargeQueueMessagesBucket",
                "MetadataBucket",
                "ModulesBucket",
                "PolicyInputsBucket",
                "RunLogsBucket",
                "S3ReplicationPolicy",
                "S3ReplicationRole",
                "StatesBucket",
                "UploadsBucket",
                "UserUploadedWorkspacesBucket",
                "WorkspacesBucket",
            ],
        },
        {
            "name": "spacelift-infra-kms",
            "retain": [
                "KMSEncryptionPrimaryKey",
                "KMSEncryptionReplicaKey",
                "KMSJWTAlias",
                "KMSJWTBackupKey",
                "KMSJWTKey",
                "KMSMasterKey",
            ],
        },
        {
            "name": "spacelift-bootstrap",
            "retain": [
                "BootstrapBucket"  # Can't be deleted as it's not empty. Needs to be deleted manually.
            ],
        },
    ]

    try:
        for stack in stacks:
            delete_stack(session, stack["name"], bad_role_arn, admin_role_arn, stack["retain"])

        # After all stacks are processed, delete the temporary IAM roles
        print("\nAll stack deletions completed. Cleaning up temporary IAM roles...")
        delete_temp_iam_roles(session)
        print("Cleanup completed successfully.")
    except Exception as e:
        print(f"Error during stack deletion process: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Delete CloudFormation stacks while retaining specific resources."
    )
    parser.add_argument("--region", help="AWS region", required=True)
    parser.add_argument("--profile", help="AWS profile name (optional)")
    args = parser.parse_args()

    delete_stacks(args.region, args.profile)
