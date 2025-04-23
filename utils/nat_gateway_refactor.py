import sys
from typing import Optional

import boto3
from botocore.exceptions import ClientError


def create_session(region: str, profile: Optional[str] = None) -> boto3.Session:
    boto_args = {"region_name": region}
    if profile:
        boto_args["profile_name"] = profile
    return boto3.Session(**boto_args)


def refactor_nat_gateways(profile: Optional[str] = None) -> None:
    # Configuration (will be injected during generation)
    region = "{REGION}"
    gateway1_route_table_id = "{GATEWAY1_ROUTE_TABLE_ID}"
    public_subnet_id_2 = "{PUBLIC_SUBNET_ID_2}"
    public_subnet_id_3 = "{PUBLIC_SUBNET_ID_3}"
    gateway2_association_id = "{GATEWAY2_ASSOCIATION_ID}"
    gateway3_association_id = "{GATEWAY3_ASSOCIATION_ID}"

    print("Refactoring NAT Gateway configuration...")
    print("\nSummary of what this script will do:")
    print("1. Disassociate existing route tables if provided")
    print("2. Associate subnets 2 and 3 with the main route table (gateway1)")
    print("\nThis is required for migrating from v2 to v3 while preserving network resources.")

    print("\nConfiguration:")
    print(f"  Region: {region}")
    print(f"  Main route table ID: {gateway1_route_table_id}")
    print(f"  Public subnet 2 ID: {public_subnet_id_2}")
    print(f"  Public subnet 3 ID: {public_subnet_id_3}")
    if gateway2_association_id and gateway2_association_id != "None":
        print(f"  Gateway 2 association ID: {gateway2_association_id}")
    if gateway3_association_id and gateway3_association_id != "None":
        print(f"  Gateway 3 association ID: {gateway3_association_id}")

    # Create boto3 session
    session = create_session(region, profile)
    ec2_client = session.client("ec2")

    # Check if the task is already done by checking if the first gateway has 3 associated subnets
    try:
        route_table = ec2_client.describe_route_tables(RouteTableIds=[gateway1_route_table_id])[
            "RouteTables"
        ][0]
        associations = route_table.get("Associations", [])

        # Count explicit subnet associations (not the main route table association which has no SubnetId)
        subnet_associations = [assoc for assoc in associations if assoc.get("SubnetId")]

        if len(subnet_associations) >= 3:
            print(
                "\nTask already completed! The main route table already has 3 or more subnet associations."
            )
            print("No changes needed.")
            return

        # Prompt for confirmation only if there's work to be done
        confirm = input("\nAre you sure you want to proceed? (y/n): ")
        if confirm.lower() != "y":
            print("Operation cancelled.")
            sys.exit(1)

        # Step 1: Disassociate existing Gateway2 and Gateway3 associations
        if gateway2_association_id and gateway2_association_id.startswith("rtbassoc-"):
            print(f"  > Disassociating route table with association ID: {gateway2_association_id}")
            ec2_client.disassociate_route_table(AssociationId=gateway2_association_id)
            print("Disassociation successful")
        if gateway3_association_id and gateway3_association_id.startswith("rtbassoc-"):
            print(f"  > Disassociating route table with association ID: {gateway3_association_id}")
            ec2_client.disassociate_route_table(AssociationId=gateway3_association_id)
            print("Disassociation successful")

        # Step 2: associate PublicSubnet2 and PublicSubnet3 with the main route table
        print(
            f"  > Associating subnet {public_subnet_id_2} with route table {gateway1_route_table_id}"
        )
        response = ec2_client.associate_route_table(
            RouteTableId=gateway1_route_table_id, SubnetId=public_subnet_id_2
        )
        print(f"Association successful: {response['AssociationId']}")
        print(
            f"  > Associating subnet {public_subnet_id_3} with route table {gateway1_route_table_id}"
        )
        response = ec2_client.associate_route_table(
            RouteTableId=gateway1_route_table_id, SubnetId=public_subnet_id_3
        )
        print(f"Association successful: {response['AssociationId']}")
        print("\nNAT Gateway refactoring completed successfully.")
    except ClientError as e:
        print(f"Error during NAT Gateway refactoring: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Refactor NAT Gateway configuration")
    parser.add_argument("--profile", type=str, help="AWS profile name to use")
    args = parser.parse_args()

    refactor_nat_gateways(profile=args.profile)
