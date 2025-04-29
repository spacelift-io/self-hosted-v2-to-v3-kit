from pathlib import Path
from typing import List, Optional
from converters.migration_context import MigrationContext
import os
import shutil


def generate_tf_files(
    unique_suffix: Optional[str], context: MigrationContext, output_dir: str
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(
        str(Path(__file__).parent.parent / "README.md"),
        str(output_path / "README.md"),
    )

    shutil.copyfile(
        str(Path(__file__).parent / "delete_cf_stacks.py"),
        str(output_path / "delete_cf_stacks.py"),
    )

    if not context.config.vpc_config.use_custom_vpc:
        shutil.copyfile(
            str(Path(__file__).parent / "internet_gateway_refactor.py"),
            str(output_path / "internet_gateway_refactor.py"),
        )
        replace_variables_in_gateway_refactor_file(
            context, str(output_path / "internet_gateway_refactor.py")
        )

    data_source_file = output_path / "data_sources.tf"
    data_source_file.unlink(missing_ok=True)
    data_source_file.touch()
    with open(data_source_file, "a") as f:
        write_data_source_terraform_content(f)

    kms_file = output_path / "kms.tf"
    kms_file.unlink(missing_ok=True)
    kms_file.touch()
    with open(kms_file, "a") as f:
        write_kms_terraform_content(f, context)

    secrets_manager_file = output_path / "secrets_manager.tf"
    secrets_manager_file.unlink(missing_ok=True)
    secrets_manager_file.touch()
    with open(secrets_manager_file, "a") as f:
        write_secret_resources(f, context)

    sqs_file = output_path / "sqs.tf"
    sqs_file.unlink(missing_ok=True)
    sqs_file.touch()
    with open(sqs_file, "a") as f:
        write_sqs_terraform_content(f)

    if context.s3_replication_role_name and context.s3_replication_policy_name:
        s3_replication_file = output_path / "s3_replication.tf"
        s3_replication_file.unlink(missing_ok=True)
        s3_replication_file.touch()
        with open(s3_replication_file, "a") as f:
            write_s3_replication_terraform_content(f, context)

    iot_file = output_path / "iot.tf"
    iot_file.unlink(missing_ok=True)
    iot_file.touch()
    with open(iot_file, "a") as f:
        write_iot_terraform_content(f, context)

    main_file = output_path / "main.tf"
    main_file.unlink(missing_ok=True)
    main_file.touch()

    with open(main_file, "a") as f:
        write_main_terraform_content(f, unique_suffix, context)


def write_main_terraform_content(f, unique_suffix: str, context: MigrationContext) -> None:
    """Write all Terraform configuration blocks to the provided file object."""
    f.write(create_terraform_provider_block(context))
    f.write(create_locals_block(context))
    f.write(create_spacelift_module(unique_suffix, context))
    f.write(create_spacelift_services_module(context))


def replace_variables_in_gateway_refactor_file(
    context: MigrationContext, script_file_path: str
) -> None:
    with open(script_file_path, "r") as template_file:
        template_content = template_file.read()

    # Replace template placeholders with actual values
    script_content = template_content
    script_content = script_content.replace("{REGION}", context.config.aws_region)
    script_content = script_content.replace(
        "{GATEWAY1_ROUTE_TABLE_ID}", context.gateway1_route_table_id
    )
    script_content = script_content.replace("{PUBLIC_SUBNET_ID_2}", context.public_subnet_id_2)
    script_content = script_content.replace("{PUBLIC_SUBNET_ID_3}", context.public_subnet_id_3)

    # Handle optional parameters
    gateway2_id = context.gateway2_association_id if context.gateway2_association_id else "None"
    gateway3_id = context.gateway3_association_id if context.gateway3_association_id else "None"
    script_content = script_content.replace("{GATEWAY2_ASSOCIATION_ID}", gateway2_id)
    script_content = script_content.replace("{GATEWAY3_ASSOCIATION_ID}", gateway3_id)

    with open(script_file_path, "w") as f:
        f.write(script_content)

    # Make the script executable
    os.chmod(script_file_path, 0o755)


def create_terraform_provider_block(context: MigrationContext) -> str:
    if context.config.vpc_config and context.config.vpc_config.use_custom_vpc:
        top_of_file_message = ""
    else:
        top_of_file_message = (
            "# Apply this file once internet_gateway_refactor.py script has finished running\n\n"
        )

    return f"""
{top_of_file_message}
terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}

  # Optionally, set up a remote backend here
}}

provider "aws" {{
  region = local.region
}}
""".lstrip()


def create_locals_block(context: MigrationContext) -> str:
    return f"""
locals {{
  region            = "{context.config.aws_region}"
  spacelift_version = "v3.0.0" # TODO: This is a tag of a Docker image uploaded to the "spacelift" and "spacelift-launcher" ECRs.
  website_domain    = "{context.cors_origin.replace('https://', '')}"
  website_endpoint  = "https://${{local.website_domain}}"
  license_token     = "<TODO: you need to set this value>" # This value must be set to the license token you received from Spacelift.
}}
"""


def format_subnet_cidr_blocks(cidr_blocks: List[str]) -> str:
    return "[" + ", ".join(f'"{item}"' for item in cidr_blocks) + "]"


def format_subnet_ids(subnet_ids_str: Optional[str]) -> str:
    if not subnet_ids_str:
        return '["<TODO: you need to set this value>"]'

    subnet_ids = [s.strip() for s in subnet_ids_str.split(",")]
    return "[" + ", ".join(f'"{subnet_id}"' for subnet_id in subnet_ids) + "]"


def get_db_password_arn(context: MigrationContext) -> str:
    if context.config.uses_custom_database_connection_string():
        # Use the custom connection string ARN from config
        return f'"{context.config.database.connection_string_ssm_arn}"'
    else:
        # Use the default created secret
        return "aws_secretsmanager_secret.db_pw.arn"


def create_spacelift_module(unique_suffix: str, context: MigrationContext) -> str:
    if not context.config.uses_custom_database_connection_string():
        rds_section = f"""
  rds_engine_version              = "{context.rds_engine_version}"
  rds_preferred_backup_window     = "{context.rds_preferred_backup_window}"
  rds_regional_cluster_identifier = "spacelift"
  rds_parameter_group_name        = "spacelift"
  rds_subnet_group_name           = "spacelift"
  rds_parameter_group_description = "Spacelift core product database"
  rds_password_sm_arn             = {get_db_password_arn(context)}
  rds_instance_configuration      = {{
    "primary" = {{
      instance_identifier = "{context.rds_instance_identifier}"
      instance_class      = "{context.rds_instance_class}"
    }}
  }}
""".rstrip()
    else:
        rds_section = "  create_database = false  # Note: RDS resources are untracked by Terraform. Feel free to import them."

    if context.config.vpc_config and context.config.vpc_config.use_custom_vpc:
        vpc_config = f"""
  create_vpc             = false
  rds_subnet_ids         = {format_subnet_ids(context.config.vpc_config.private_subnet_ids)}
  rds_security_group_ids = ["{context.config.vpc_config.database_security_group_id}"]
"""
    else:
        public_subnet_cidr_blocks = format_subnet_cidr_blocks(context.public_subnet_cidr_blocks)
        private_subnet_cidr_blocks = format_subnet_cidr_blocks(context.private_subnet_cidr_blocks)
        vpc_config = f"""
  vpc_cidr_block             = "{context.vpc_cidr_block}"
  public_subnet_cidr_blocks  = {public_subnet_cidr_blocks}
  private_subnet_cidr_blocks = {private_subnet_cidr_blocks}
"""

    return f"""        
module "spacelift" {{
  source = "github.com/spacelift-io/terraform-aws-spacelift-selfhosted?ref=v1.3.0"

  region           = local.region
  website_endpoint = local.website_endpoint
  unique_suffix    = "{unique_suffix}"
  s3_bucket_names  = {{
    binaries     = "{context.binaries_bucket_name}"
    deliveries   = "{context.deliveries_bucket_name}"
    large_queue  = "{context.large_queue_name}"
    metadata     = "{context.metadata_bucket_name}"
    modules      = "{context.modules_bucket_name}"
    policy       = "{context.policy_bucket_name}"
    run_logs     = "{context.run_logs_bucket_name}"
    states       = "{context.states_bucket_name}"
    uploads      = "{context.uploads_bucket_name}"
    user_uploads = "{context.user_uploads_bucket_name}"
    workspace    = "{context.workspace_bucket_name}"
  }}

  kms_arn                       = aws_kms_key.master.arn
  kms_master_key_multi_regional = false
  kms_jwt_key_multi_regional    = false
{vpc_config}        
  number_of_images_to_retain   = 10
  backend_ecr_repository_name  = "spacelift"
  launcher_ecr_repository_name = "spacelift-launcher"

  security_group_names = {{
    database  = "database_sg"
    drain     = "drain_sg"
    scheduler = "scheduler_sg"
    server    = "server_sg"
  }}
        
{rds_section}        
}}
"""


def create_spacelift_services_module(context: MigrationContext) -> str:
    if context.config.vpc_config and context.config.vpc_config.use_custom_vpc:
        vpc_config = f"""
#  vpc_id                      = "{context.config.vpc_config.vpc_id}"
#  ecs_subnets                 = {format_subnet_ids(context.config.vpc_config.private_subnet_ids)}
#  server_lb_subnets           = {format_subnet_ids(context.config.vpc_config.public_subnet_ids)}
#  server_security_group_id    = "{context.config.vpc_config.server_security_group_id}"
#  drain_security_group_id     = "{context.config.vpc_config.drain_security_group_id}"
#  scheduler_security_group_id = "{context.config.vpc_config.scheduler_security_group_id}"
""".lstrip()
    else:
        vpc_config = """
#  vpc_id      = module.spacelift.vpc_id
#  ecs_subnets = module.spacelift.private_subnet_ids
#  
#  server_lb_subnets           = module.spacelift.public_subnet_ids
#  server_security_group_id    = module.spacelift.server_security_group_id
#  
#  drain_security_group_id     = module.spacelift.drain_security_group_id
#  scheduler_security_group_id = module.spacelift.scheduler_security_group_id
""".lstrip()
    ecs_service_desired_count = ""
    if not context.config.is_primary_region():
        ecs_service_desired_count = """
#  drain_desired_count = 0
#  scheduler_desired_count = 0
#  server_desired_count = 0
        """.strip()

    if context.config.uses_custom_database_connection_string():
        db_secret = f"""
#    {{
#      name = "DATABASE_URL"
#      valueFrom = "{context.config.database.connection_string_ssm_arn}:DATABASE_URL::"
#    }}
        """.strip()
    else:
        db_secret = """
#    {
#      name = "DATABASE_URL"
#      valueFrom = "${module.spacelift.database_secret_arn}:DATABASE_URL::"
#    },
#    {
#      name = "DATABASE_READ_ONLY_URL"
#      valueFrom = "${module.spacelift.database_secret_arn}:DATABASE_READ_ONLY_URL::"
#    }
""".lstrip()

    additional_env_vars = ""
    if context.config.has_custom_proxy_config():
        additional_env_vars = "  additional_env_vars = ["
        if context.config.proxy_config.http_proxy:
            additional_env_vars += f'\n#    {{ name = "HTTP_PROXY", value = "{context.config.proxy_config.http_proxy}" }},'
        if context.config.proxy_config.https_proxy:
            additional_env_vars += f'\n#    {{ name = "HTTPS_PROXY", value = "{context.config.proxy_config.https_proxy}" }},'
        if context.config.proxy_config.no_proxy:
            additional_env_vars += (
                f'\n#    {{ name = "NO_PROXY", value = "{context.config.proxy_config.no_proxy}" }},'
            )
        additional_env_vars += "\n#  ]"

    return f"""
# Uncomment after the above module applied successfully
#module "spacelift_services" {{
#  source = "github.com/spacelift-io/terraform-aws-ecs-spacelift-selfhosted?ref=v1.1.0"
#  
#  region               = local.region
#  unique_suffix        = module.spacelift.unique_suffix
#  kms_key_arn          = module.spacelift.kms_key_arn
#  server_domain        = local.website_domain
#  
#  license_token = local.license_token
#  
#  encryption_type        = "kms"
#  kms_encryption_key_arn = {"aws_kms_key.encryption_primary.arn" if context.config.is_primary_region() else "aws_kms_replica_key.encryption_replica_key.arn"}  
#  kms_signing_key_arn    = aws_kms_key.jwt.arn
{f'#  iot_endpoint = "{context.config.iot_broker_endpoint}"' if context.config.iot_broker_endpoint else ""}
#{additional_env_vars}
#  secrets_manager_secret_arns = [
{"#    module.spacelift.database_secret_arn," if not context.config.uses_custom_database_connection_string() else f'#    "{context.config.database.connection_string_ssm_arn}",'}
#    aws_secretsmanager_secret.slack_credentials.arn,
#    aws_secretsmanager_secret.additional_root_ca_certificates.arn,
#    aws_secretsmanager_secret.saml_credentials.arn,
#  ]
#  sensitive_env_vars          = [
#    {{
#      name = "SAML_CERT"
#      valueFrom = "${{aws_secretsmanager_secret.saml_credentials.arn}}:certificate::"
#    }},
#    {{
#      name = "SAML_KEY"
#      valueFrom = "${{aws_secretsmanager_secret.saml_credentials.arn}}:key::"
#    }},
#    {{
#      name = "SLACK_APP_CLIENT_ID"
#      valueFrom = "${{aws_secretsmanager_secret.slack_credentials.arn}}:SLACK_APP_CLIENT_ID::"
#    }},
#    {{
#      name = "SLACK_APP_CLIENT_SECRET"
#      valueFrom = "${{aws_secretsmanager_secret.slack_credentials.arn}}:SLACK_APP_CLIENT_SECRET::"
#    }},
#    {{
#      name = "SLACK_SECRET"
#      valueFrom = "${{aws_secretsmanager_secret.slack_credentials.arn}}:SLACK_SECRET::"
#    }},
{db_secret}
#  ]
#  
#  backend_image      = module.spacelift.ecr_backend_repository_url
#  backend_image_tag  = local.spacelift_version
#  launcher_image     = module.spacelift.ecr_launcher_repository_url
#  launcher_image_tag = local.spacelift_version

#  server_log_configuration = {{
#    logDriver : "awslogs",
#    options : {{
#      "awslogs-region": local.region,
#      "awslogs-group": "/ecs/spacelift-server",
#      "awslogs-create-group": "true",
#      "awslogs-stream-prefix": "server"
#      "mode": "non-blocking"
#      "max-buffer-size": "25m"
#    }}
#  }}
#
#  drain_log_configuration = {{
#    logDriver : "awslogs",
#    options : {{
#      "awslogs-region": local.region,
#      "awslogs-group": "/ecs/spacelift-drain",
#      "awslogs-create-group": "true",
#      "awslogs-stream-prefix": "drain"
#      "mode": "non-blocking"
#      "max-buffer-size": "25m"
#    }}
#  }}
#
#  scheduler_log_configuration = {{
#    logDriver : "awslogs",
#    options : {{
#      "awslogs-region": local.region,
#      "awslogs-group": "/ecs/spacelift-scheduler",
#      "awslogs-create-group": "true",
#      "awslogs-stream-prefix": "scheduler"
#      "mode": "non-blocking"
#      "max-buffer-size": "25m"
#    }}
#  }}
#
{ecs_service_desired_count}
{vpc_config}
#  server_lb_certificate_arn   = "{context.config.load_balancer.certificate_arn}"
#  
#  mqtt_broker_type = "iotcore"
#  
#  deliveries_bucket_name               = module.spacelift.deliveries_bucket_name
#  large_queue_messages_bucket_name     = module.spacelift.large_queue_messages_bucket_name
#  metadata_bucket_name                 = module.spacelift.metadata_bucket_name
#  modules_bucket_name                  = module.spacelift.modules_bucket_name
#  policy_inputs_bucket_name            = module.spacelift.policy_inputs_bucket_name
#  run_logs_bucket_name                 = module.spacelift.run_logs_bucket_name
#  states_bucket_name                   = module.spacelift.states_bucket_name
#  uploads_bucket_name                  = module.spacelift.uploads_bucket_name
#  uploads_bucket_url                   = module.spacelift.uploads_bucket_url
#  user_uploaded_workspaces_bucket_name = module.spacelift.user_uploaded_workspaces_bucket_name
#  workspace_bucket_name                = module.spacelift.workspace_bucket_name
#
#  sqs_queues = {{
#    deadletter      = aws_sqs_queue.deadletter_queue.name
#    deadletter_fifo = aws_sqs_queue.deadletter_fifo_queue.name
#    async_jobs      = aws_sqs_queue.async_jobs_queue.name
#    events_inbox    = aws_sqs_queue.events_inbox_queue.name
#    async_jobs_fifo = aws_sqs_queue.async_jobs_fifo_queue.name
#    cronjobs        = aws_sqs_queue.cronjobs_queue.name
#    webhooks        = aws_sqs_queue.webhooks_queue.name
#    iot             = aws_sqs_queue.iot_queue.name
#  }}
#}}
#
# output "load_balancer_dns_name" {{
#   value = module.spacelift_services.server_lb_dns_name
# }}
"""


def write_data_source_terraform_content(f) -> None:
    f.write(
        """
data "aws_partition" "current" {}
data "aws_caller_identity" "current" {}
""".lstrip()
    )


def write_secret_resources(f, context: MigrationContext) -> None:
    has_custom_connection_string = (
        context.config
        and context.config.database
        and context.config.database.connection_string_ssm_arn
        and len(context.config.database.connection_string_ssm_arn) > 0
    )

    if not has_custom_connection_string:
        f.write(
            """
resource "aws_secretsmanager_secret" "db_pw" {
  name        = "spacelift/database"
  description = "Connection string for the Spacelift database"
  kms_key_id  = aws_kms_key.master.arn
}
""".lstrip()
        )

    f.write(
        """
resource "aws_secretsmanager_secret" "slack_credentials" {
  name        = "spacelift/slack-application"
  description = "Contains the Spacelift Slack application configuration"
  kms_key_id  = aws_kms_key.master.arn
}

resource "aws_secretsmanager_secret" "additional_root_ca_certificates" {
  name        = "spacelift/additional-root-ca-certificates"
  description = "Contains additional CA certificates to use when making HTTPS requests"
  kms_key_id  = aws_kms_key.master.arn
}

resource "aws_secretsmanager_secret" "external" {
  name        = "spacelift/external"
  description = "Externally managed and supplied secrets used by Spacelift app"
  kms_key_id  = aws_kms_key.master.arn
}

resource "aws_secretsmanager_secret" "saml_credentials" {
  name        = "spacelift/saml-credentials"
  description = "Contains the SAML certificate and signing key"
  kms_key_id  = aws_kms_key.master.arn
}
""".lstrip()
    )


def write_kms_terraform_content(f, context: MigrationContext) -> None:
    if (
        context.config.disaster_recovery
        and context.config.disaster_recovery.encryption_primary_key_arn
    ):
        primary_key_resource = f"""
resource "aws_kms_replica_key" "encryption_replica_key" {{
  primary_key_arn = "{context.config.disaster_recovery.encryption_primary_key_arn}"
  description     = "Spacelift in-app encryption primary key. Used to encrypt user data stored in the database like VCS tokens."

  policy = jsonencode({{
    Version = "2012-10-17",
    Statement = [
      {{
        Effect = "Allow",
        Action = "kms:*",
        Resource = "*",
        Principal = {{
           AWS = "arn:${{data.aws_partition.current.partition}}:iam::${{data.aws_caller_identity.current.account_id}}:root"
        }}
      }}
    ]
  }})
}}
            """.lstrip()
    else:
        primary_key_resource = """
resource "aws_kms_key" "encryption_primary" {
  description         = "Spacelift in-app encryption primary key. Used to encrypt user data stored in the database like VCS tokens."
  enable_key_rotation = true
  multi_region        = true

  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      }
    ]
  })
}
            """.lstrip()

    f.write(
        f"""
resource "aws_kms_key" "master" {{
  description         = "Spacelift master KMS key"
  enable_key_rotation = true

  policy = jsonencode({{
    Version   = "2012-10-17"
    Statement = [
      {{
        Effect    = "Allow"
        Principal = {{ AWS = "arn:${{data.aws_partition.current.partition}}:iam::${{data.aws_caller_identity.current.account_id}}:root" }}
        Action    = "kms:*"
        Resource  = "*"
      }},
      {{
        Effect    = "Allow"
        Principal = {{
          Service = "logs.${{local.region}}.amazonaws.com"
        }}
        Action   = [
          "kms:Encrypt*",
          "kms:Decrypt*",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:Describe*"
        ]
        Resource = "*"
      }},
      {{
        Effect    = "Allow"
        Principal = {{
          Service = ["sns.amazonaws.com", "events.amazonaws.com"]
        }}
        Action   = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }}
    ]
  }})
}}

resource "aws_kms_key" "jwt" {{
  description = "Spacelift KMS key used to sign and verify JWTs"
  key_usage   = "SIGN_VERIFY"
  customer_master_key_spec = "RSA_4096"

  policy = jsonencode({{
    Version   = "2012-10-17"
    Statement = [
      {{
        Effect    = "Allow"
        Principal = {{ AWS = "arn:${{data.aws_partition.current.partition}}:iam::${{data.aws_caller_identity.current.account_id}}:root" }}
        Action    = "kms:*"
        Resource  = "*"
      }}
    ]
  }})
}}

{primary_key_resource}

resource "aws_kms_key" "jwt_backup_key" {{
  description              = "Backup Spacelift KMS key used to sign and verify JWTs"
  key_usage                = "SIGN_VERIFY"
  customer_master_key_spec = "RSA_4096"

  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Effect = "Allow"
        Action = "kms:*"
        Principal = {{
          AWS = "arn:${{data.aws_partition.current.partition}}:iam::${{data.aws_caller_identity.current.account_id}}:root"
        }}
        Resource = "*"
      }}
    ]
  }})
}}

resource "aws_kms_alias" "jwt_alias" {{
  name          = "alias/spacelift-jwt"
  target_key_id = aws_kms_key.jwt.key_id
}}
""".lstrip()
    )


def write_sqs_terraform_content(f) -> None:
    f.write(
        """
resource "aws_sqs_queue" "deadletter_queue" {
  name                      = "spacelift-dlq"
  kms_master_key_id         = aws_kms_key.master.arn
  visibility_timeout_seconds = 300
}

resource "aws_sqs_queue" "deadletter_fifo_queue" {
  name                      = "spacelift-dlq.fifo"
  fifo_queue                = true
  kms_master_key_id         = aws_kms_key.master.arn
  visibility_timeout_seconds = 300
}

resource "aws_sqs_queue" "async_jobs_queue" {
  name                       = "spacelift-async-jobs"
  kms_master_key_id          = aws_kms_key.master.arn
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 300

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.deadletter_queue.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "events_inbox_queue" {
  name                       = "spacelift-events-inbox"
  kms_master_key_id          = aws_kms_key.master.arn
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 300

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.deadletter_queue.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "async_jobs_fifo_queue" {
  name                       = "spacelift-async-jobs.fifo"
  fifo_queue                 = true
  deduplication_scope        = "messageGroup"
  fifo_throughput_limit      = "perMessageGroupId"
  kms_master_key_id          = aws_kms_key.master.arn
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 300

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.deadletter_fifo_queue.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "cronjobs_queue" {
  name                       = "spacelift-cronjobs"
  kms_master_key_id          = aws_kms_key.master.arn
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 300
  message_retention_seconds  = 3600

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.deadletter_queue.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "webhooks_queue" {
  name                       = "spacelift-webhooks"
  kms_master_key_id          = aws_kms_key.master.arn
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 600

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.deadletter_queue.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "iot_queue" {
  name                       = "spacelift-iot"
  kms_master_key_id          = aws_kms_key.master.arn
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 45

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.deadletter_queue.arn
    maxReceiveCount     = 3
  })
}
""".lstrip()
    )


def write_s3_replication_terraform_content(f, context: MigrationContext) -> None:
    f.write(
        f"""
locals {{
  replication_region_name        = "{context.s3_replica_region_name}"
  replication_region_key_kms_arn = "{context.s3_replica_region_key_kms_arn}"
}}

resource "aws_iam_role" "replication_role" {{
  name        = "{context.s3_replication_role_name}"
  description = "Used to allow S3 replication from the Spacelift primary region to the DR region"

  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {{
          Service = "s3.amazonaws.com"
        }}
      }},
    ]
  }})
}}

resource "aws_iam_policy" "s3_replication_policy" {{
  name        = "{context.s3_replication_policy_name}"
  description = "Used to allow S3 replication from the Spacelift primary region to the DR region"

  policy = jsonencode({{
    Version = "2012-10-17",
    Statement = [
      {{
        Action = [
          "s3:ListBucket",
          "s3:GetReplicationConfiguration",
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging",
          "s3:GetObjectRetention",
          "s3:GetObjectLegalHold"
        ],
        Effect   = "Allow",
        Resource = [
          module.spacelift.states_bucket_arn,
          "${{module.spacelift.states_bucket_arn}}/*",
          module.spacelift.run_logs_bucket_arn,
          "${{module.spacelift.run_logs_bucket_arn}}/*",
          module.spacelift.modules_bucket_arn,
          "${{module.spacelift.modules_bucket_arn}}/*",
          module.spacelift.policy_inputs_bucket_arn,
          "${{module.spacelift.policy_inputs_bucket_arn}}/*",
          module.spacelift.workspace_bucket_arn,
          "${{module.spacelift.workspace_bucket_arn}}/*",
        ]
      }},
      {{
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags",
          "s3:GetObjectVersionTagging",
          "s3:ObjectOwnerOverrideToBucketOwner"
        ],
        Effect    = "Allow",
        Condition = {{
          StringLikeIfExists = {{
            "s3:x-amz-server-side-encryption" = ["aws:kms", "AES256"],
            "s3:x-amz-server-side-encryption-aws-kms-key-id" = "${{local.replication_region_key_kms_arn}}"
          }}
        }},
        Resource = [
          "{context.s3_states_bucket_replica_arn}/*",
          "{context.s3_run_logs_bucket_replica_arn}/*",
          "{context.s3_modules_bucket_replica_arn}/*",
          "{context.s3_policy_input_bucket_replica_arn}/*",
          "{context.s3_workspace_bucket_replica_arn}/*",
        ]
      }},
      {{
        Action = [
          "kms:Decrypt"
        ],
        Effect    = "Allow",
        Condition = {{
          StringLike = {{
            "kms:ViaService"                   = "s3.${{local.region}}.amazonaws.com",
            "kms:EncryptionContext:aws:s3:arn" = [
              "${{module.spacelift.states_bucket_arn}}/*",
              "${{module.spacelift.run_logs_bucket_arn}}/*",
              "${{module.spacelift.modules_bucket_arn}}/*",
              "${{module.spacelift.policy_inputs_bucket_arn}}/*",
              "${{module.spacelift.workspace_bucket_arn}}/*"
            ]
          }}
        }},
        Resource = aws_kms_key.master.arn
      }},
      {{
        Action = [
          "kms:Encrypt"
        ],
        Effect    = "Allow",
        Condition = {{
          StringLike = {{
            "kms:ViaService"                   = "s3.${{local.replication_region_name}}.amazonaws.com",
            "kms:EncryptionContext:aws:s3:arn" = [
              "{context.s3_states_bucket_replica_arn}/*",
              "{context.s3_run_logs_bucket_replica_arn}/*",
              "{context.s3_modules_bucket_replica_arn}/*",
              "{context.s3_policy_input_bucket_replica_arn}/*",
              "{context.s3_workspace_bucket_replica_arn}/*",
            ]
          }}
        }},
        Resource = "${{local.replication_region_key_kms_arn}}"
      }}
    ]
  }})
}}

resource "aws_iam_role_policy_attachment" "s3_replication_attachment" {{
  role       = aws_iam_role.replication_role.name
  policy_arn = aws_iam_policy.s3_replication_policy.arn
}}

{generate_s3_replication_bucket_resource("states", "module.spacelift.states_bucket_name", context.s3_states_bucket_replica_arn, context.s3_replica_region_key_kms_arn)}

{generate_s3_replication_bucket_resource("run_logs", "module.spacelift.run_logs_bucket_name", context.s3_run_logs_bucket_replica_arn, context.s3_replica_region_key_kms_arn)}

{generate_s3_replication_bucket_resource("modules", "module.spacelift.modules_bucket_name", context.s3_modules_bucket_replica_arn, context.s3_replica_region_key_kms_arn)}

{generate_s3_replication_bucket_resource("policy_inputs", "module.spacelift.policy_inputs_bucket_name", context.s3_policy_input_bucket_replica_arn, context.s3_replica_region_key_kms_arn)}

{generate_s3_replication_bucket_resource("workspaces", "module.spacelift.workspace_bucket_name", context.s3_workspace_bucket_replica_arn, context.s3_replica_region_key_kms_arn)}
        """.lstrip()
    )


def generate_s3_replication_bucket_resource(
    bucket_friendly_name: str,
    source_bucket_name: str,
    destination_bucket_arn: str,
    replica_kms_key_arn: str,
) -> str:
    return f"""
resource "aws_s3_bucket_replication_configuration" "{bucket_friendly_name}" {{
  bucket = {source_bucket_name}

  role = aws_iam_role.replication_role.arn

  rule {{
    id       = "spacelift-dr-replication-rule"
    priority = 0
    status   = "Enabled"

    filter {{
      prefix = ""
    }}

    destination {{
      bucket        = "{destination_bucket_arn}"
      storage_class = "STANDARD"

      encryption_configuration {{
        replica_kms_key_id = "{replica_kms_key_arn}"
      }}
    }}

    delete_marker_replication {{
      status = "Enabled"
    }}

    source_selection_criteria {{
      replica_modifications {{
        status = "Enabled"
      }}

      sse_kms_encrypted_objects {{
        status = "Enabled"
      }}
    }}
  }}
}}
    """.lstrip().rstrip()


def write_iot_terraform_content(f, migration_context: MigrationContext) -> None:
    f.write(
        f"""
resource "aws_iam_role" "iot_message_sender_role" {{
  name = "spacelift-iot-{migration_context.config.aws_region}"

  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Effect = "Allow"
        Principal = {{
          Service = "iot.amazonaws.com"
        }}
        Action = "sts:AssumeRole"
      }}
    ]
  }})

  description = "Used by the API Gateway when publishing messages to the webhooks SNS topic"
}}

resource "aws_iam_role_policy" "iot_message_sender_role_policy" {{
  name = "allow-iot-sqs-sending"
  role = aws_iam_role.iot_message_sender_role.id

  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey*"
        ]
        Resource = aws_kms_key.master.arn
      }},
      {{
        Effect = "Allow"
        Action = "sqs:SendMessage"
        Resource = aws_sqs_queue.iot_queue.arn
      }}
    ]
  }})
}}

resource "aws_iot_topic_rule" "iot_message_sending_rule" {{
  name = "spacelift"

  sql = "SELECT *, Timestamp() as timestamp, topic(3) as worker_pool_ulid, topic(4) as worker_ulid FROM 'spacelift/writeonly/#'"
  sql_version = "2016-03-23"
  description = "Send all messages published in the spacelift namespace to the ${{aws_sqs_queue.iot_queue.name}}"
  enabled = true

  sqs {{
    role_arn  = aws_iam_role.iot_message_sender_role.arn
    queue_url = aws_sqs_queue.iot_queue.id
    use_base64 = true
  }}
}}
""".lstrip()
    )
