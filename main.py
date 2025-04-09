import boto3
import argparse
from typing import List, Dict
from converters.ecr_to_terraform import ECRTerraformer
from converters.rds_to_terraform import RDSTerraformer
from converters.s3_to_terraform import S3Terraformer
from converters.kms_to_terraform import KMSTerraformer
from converters.ec2_to_terraform import EC2Terraformer
from converters.migration_context import MigrationContext
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--unique-suffix",
        type=str,
        required=False,
        help="Unique suffix of the existing resources to be imported",
    )
    parser.add_argument(
        "--region",
        type=str,
        required=True,
        help="Name of the AWS region where the resources are located",
    )
    parser.add_argument(
        "--profile",
        type=str,
        required=False,
        help="AWS profile to use",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    unique_suffix: str = args.unique_suffix
    region: str = args.region
    profile: str = args.profile

    f = "imports.tf"
    Path(f).unlink(missing_ok=True)
    Path(f).touch()

    migrationContext = MigrationContext()
    ec2Terraformer = EC2Terraformer(f, migrationContext)
    kmsTerraformer = KMSTerraformer(f, migrationContext)
    s3Terraformer = S3Terraformer(f, migrationContext)
    ecrTerraformer = ECRTerraformer(f, migrationContext)
    rdsTerraformer = RDSTerraformer(f, migrationContext)

    boto_args = {"region_name": region}
    if profile:
        boto_args["profile_name"] = profile
    session = boto3.Session(**boto_args)

    s3 = session.client("s3")
    listResp: List[Dict] = s3.list_buckets()
    for bucket in listResp["Buckets"]:
        if unique_suffix and unique_suffix in bucket["Name"]:
            bucketName = Bucket = bucket["Name"]
            versioningResp = s3.get_bucket_versioning(Bucket=bucketName)
            encryptionResp = s3.get_bucket_encryption(Bucket=bucketName)
            publicAccessResp = s3.get_public_access_block(Bucket=bucketName)
            publicAccessBlocked = publicAccessResp.get(
                "PublicAccessBlockConfiguration", {}
            ).get("BlockPublicAcls", False)
            try:
                corsResp = s3.get_bucket_cors(Bucket=bucketName)
            except s3.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchCORSConfiguration":
                    corsResp = {"CORSRules": []}
                else:
                    raise

            try:
                lifecycleResp = s3.get_bucket_lifecycle_configuration(Bucket=bucketName)
            except s3.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchLifecycleConfiguration":
                    lifecycleResp = {"Rules": []}
                else:
                    raise

            lifecycleEnabled = False

            for rule in lifecycleResp["Rules"]:
                if rule.get("Status") == "Enabled":
                    lifecycleEnabled = rule.get("Status") == "Enabled"

            rules = encryptionResp["ServerSideEncryptionConfiguration"]["Rules"]
            sse_enabled = False
            for rule in rules:
                sse_algorithm = rule["ApplyServerSideEncryptionByDefault"][
                    "SSEAlgorithm"
                ]
                kms_key_id = rule["ApplyServerSideEncryptionByDefault"].get(
                    "KMSMasterKeyID"
                )
                sse_enabled = sse_algorithm == "aws:kms" and kms_key_id is not None

            s3Terraformer.s3_to_terraform(
                bucketName,
                versioningResp.get("Status") == "Enabled",
                sse_enabled,
                lifecycleEnabled,
                publicAccessBlocked,
                corsResp.get("CORSRules", []),
            )

    kms = session.client("kms")
    listResp = kms.list_keys()
    for key in listResp["Keys"]:
        key_id = key["KeyId"]
        key_metadata = kms.describe_key(KeyId=key_id)
        if key_metadata["KeyMetadata"]["KeyState"] == "Enabled":
            kmsTerraformer.kms_to_terraform(
                key_id,
                key_metadata["KeyMetadata"]["MultiRegion"],
                key_metadata["KeyMetadata"]["Description"],
            )

    ec2 = session.client("ec2")
    listResp = ec2.describe_vpcs()
    for vpc in listResp["Vpcs"]:
        for tag in vpc.get("Tags", []):
            if tag["Key"] == "aws:cloudformation:logical-id" and tag["Value"] == "VPC":
                ec2Terraformer.vpc_to_terraform(
                    vpc["VpcId"], vpc["CidrBlock"], vpc.get("Tags") or []
                )

    listResp = ec2.describe_subnets()
    for subnet in listResp["Subnets"]:
        ec2Terraformer.subnet_to_terraform(
            subnet["SubnetId"], subnet["CidrBlock"], subnet.get("Tags") or []
        )

    internet_gateway_resp = ec2.describe_internet_gateways()
    for igw in internet_gateway_resp["InternetGateways"]:
        ec2Terraformer.internet_gateway_to_terraform(
            igw["InternetGatewayId"], igw.get("Tags") or []
        )

    internet_gateway_resp = ec2.describe_route_tables()
    for route_table in internet_gateway_resp["RouteTables"]:
        ec2Terraformer.route_table_to_terraform(
            route_table, route_table.get("Tags") or []
        )

    elastic_ip_resp = ec2.describe_addresses()
    for elastic_ip in elastic_ip_resp["Addresses"]:
        ec2Terraformer.elastic_ip_to_terraform(
            elastic_ip["AllocationId"], elastic_ip.get("Tags") or []
        )

    nat_gateway_resp = ec2.describe_nat_gateways()
    for nat_gateway in nat_gateway_resp["NatGateways"]:
        ec2Terraformer.nat_gateway_to_terraform(
            nat_gateway, nat_gateway.get("Tags") or []
        )

    security_group_resp = ec2.describe_security_groups()
    for security_group in security_group_resp["SecurityGroups"]:
        rules = ec2.describe_security_group_rules(
            Filters=[{"Name": "group-id", "Values": [security_group["GroupId"]]}]
        )
        ec2Terraformer.security_group_to_terraform(
            security_group["GroupId"],
            rules["SecurityGroupRules"],
            security_group.get("Tags") or [],
        )

    for ecr_repo in [
        "spacelift",
        "spacelift-launcher",
    ]:  # These names are hardcoded in Cloudformation
        ecrTerraformer.ecr_to_terraform(ecr_repo)

    rds = session.client("rds")
    listResp = rds.describe_db_clusters(DBClusterIdentifier="spacelift")
    for cluster in listResp["DBClusters"]:
        cluster_members = cluster.get("DBClusterMembers", [])
        if len(cluster_members) != 1:
            raise Exception(
                "Expected exactly one cluster member, but found {}".format(
                    len(cluster_members)
                )
            )

        instance_resp = rds.describe_db_instances(
            DBInstanceIdentifier=cluster_members[0]["DBInstanceIdentifier"]
        )
        instances = instance_resp.get("DBInstances", [])
        if len(instances) != 1:
            raise Exception(
                "Expected exactly one instance, but found {}".format(len(instances))
            )

        rdsTerraformer.rds_to_terraform(cluster, instances[0])

    main_file = "main.tf"
    Path(main_file).unlink(missing_ok=True)
    Path(main_file).touch()
    with open(main_file, "a") as f:
        f.write(
            """
terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "{0}"
}}

locals {{
  region            = "{0}"
  spacelift_version = "v3.1.0"
  website_domain    = "{3}"
  website_endpoint  = "https://${{local.website_domain}}"
  mqtt_domain       = "THIS-MUST-BE-FILLED-BY-YOU"
  mqtt_endpoint     = "tls://${{local.mqtt_domain}}:1984"
}}
            
module "spacelift" {{
  source = "../terraform-aws-spacelift-selfhosted"

  region           = local.region
  website_endpoint = local.website_endpoint
  vpc_cidr_block   = "{3}"
  unique_suffix    = "{4}"
  s3_bucket_names  = {{
    binaries     = "{5}"
    deliveries   = "{6}"
    large_queue  = "{7}"
    metadata     = "{8}"
    modules      = "{9}"
    policy       = "{10}"
    run_logs     = "{11}"
    states       = "{12}"
    uploads      = "{13}"
    user_uploads = "{14}"
    workspace    = "{15}"
  }}
  kms_master_key_multi_regional = false
  kms_jwt_key_multi_regional    = false
 
  public_subnet_cidr_blocks  = [{16}]
  private_subnet_cidr_blocks = [{17}]
            
  number_of_images_to_retain   = 10
  backend_ecr_repository_name  = "spacelift"
  launcher_ecr_repository_name = "spacelift-launcher"
  security_group_names = {{
    database  = "database_sg"
    drain     = "drain_sg"
    scheduler = "scheduler_sg"
    server    = "server_sg"
  }}
            
  rds_engine_version              = "{18}"
  rds_preferred_backup_window     = "{19}"
  rds_regional_cluster_identifier = "spacelift"
  rds_parameter_group_name        = "spacelift"
  rds_subnet_group_name           = "spacelift"
  rds_instance_configuration      = {{
    "primary" = {{
      instance_identifier = "{20}"
      instance_class      = "{21}"
    }}
  }}         
}}

# Uncomment after the first part applied
#module "spacelift_services" {{
#  source = "../terraform-aws-ecs-spacelift-selfhosted"
#
#  region               = local.region
#  unique_suffix        = module.spacelift_infra.unique_suffix
#  kms_key_arn          = module.spacelift_infra.kms_key_arn
#  server_domain        = local.website_domain
#  mqtt_broker_endpoint = local.mqtt_endpoint
#
#  license_token = "<your-license-token-issued-by-Spacelift>"
#
#  encryption_type        = "kms"
#  kms_encryption_key_arn = module.spacelift_infra.kms_encryption_key_arn
#  kms_signing_key_arn    = module.spacelift_infra.kms_signing_key_arn
#
#  database_url           = format("postgres://%s:%s@%s:5432/spacelift?statement_cache_capacity=0", module.spacelift_infra.rds_username, module.spacelift_infra.rds_password, module.spacelift_infra.rds_cluster_endpoint)
#  database_read_only_url = format("postgres://%s:%s@%s:5432/spacelift?statement_cache_capacity=0", module.spacelift_infra.rds_username, module.spacelift_infra.rds_password, module.spacelift_infra.rds_cluster_reader_endpoint)
#
#  backend_image      = module.spacelift_infra.ecr_backend_repository_url
#  backend_image_tag  = local.spacelift_version
#  launcher_image     = module.spacelift_infra.ecr_launcher_repository_url
#  launcher_image_tag = local.spacelift_version
#
#  # admin_username = ""
#  # admin_password = ""
#
#  vpc_id      = module.spacelift_infra.vpc_id
#  ecs_subnets = module.spacelift_infra.private_subnet_ids
#
#  server_lb_subnets           = module.spacelift_infra.public_subnet_ids
#  server_security_group_id    = module.spacelift_infra.server_security_group_id
#  server_lb_certificate_arn   = "<LB certificate ARN>" # Note that this certificate MUST be successfully issued. It cannot be attached to the load balancer in a pending state.
#
#  drain_security_group_id     = module.spacelift_infra.drain_security_group_id
#  scheduler_security_group_id = module.spacelift_infra.scheduler_security_group_id
#
#  mqtt_lb_subnets = module.spacelift_infra.public_subnet_ids
#
#  deliveries_bucket_name               = module.spacelift_infra.deliveries_bucket_name
#  large_queue_messages_bucket_name     = module.spacelift_infra.large_queue_messages_bucket_name
#  metadata_bucket_name                 = module.spacelift_infra.metadata_bucket_name
#  modules_bucket_name                  = module.spacelift_infra.modules_bucket_name
#  policy_inputs_bucket_name            = module.spacelift_infra.policy_inputs_bucket_name
#  run_logs_bucket_name                 = module.spacelift_infra.run_logs_bucket_name
#  states_bucket_name                   = module.spacelift_infra.states_bucket_name
#  uploads_bucket_name                  = module.spacelift_infra.uploads_bucket_name
#  uploads_bucket_url                   = module.spacelift_infra.uploads_bucket_url
#  user_uploaded_workspaces_bucket_name = module.spacelift_infra.user_uploaded_workspaces_bucket_name
#  workspace_bucket_name                = module.spacelift_infra.workspace_bucket_name
#}}
            """.format(
                region,
                region,
                migrationContext.cors_origin.replace("https://", ""),
                migrationContext.vpc_cidr_block,
                unique_suffix,
                migrationContext.binaries_bucket_name,
                migrationContext.deliveries_bucket_name,
                migrationContext.large_queue_name,
                migrationContext.metadata_bucket_name,
                migrationContext.modules_bucket_name,
                migrationContext.policy_bucket_name,
                migrationContext.run_logs_bucket_name,
                migrationContext.states_bucket_name,
                migrationContext.uploads_bucket_name,
                migrationContext.user_uploads_bucket_name,
                migrationContext.workspace_bucket_name,
                ", ".join(
                    f'"{item}"' for item in migrationContext.public_subnet_cidr_blocks
                ),
                ", ".join(
                    f'"{item}"' for item in migrationContext.private_subnet_cidr_blocks
                ),
                migrationContext.rds_engine_version,
                migrationContext.rds_preferred_backup_window,
                migrationContext.rds_instance_identifier,
                migrationContext.rds_instance_class,
            )
        )
