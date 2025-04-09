from pathlib import Path
from typing import List, Optional
from converters.migration_context import MigrationContext


def generate_main_tf(
    unique_suffix: Optional[str], context: MigrationContext, output_dir: str
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    generate_bash_script(context, output_path)

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


def generate_bash_script(context: MigrationContext, output_path: Path) -> None:
    script_file = output_path / "first_step.sh"
    script_file.unlink(missing_ok=True)
    script_file.touch()

    with open(script_file, "a") as f:
        f.write("#!/bin/bash\n\n")
        if context.gateway2_association_id:
            f.write(
                f"aws ec2 disassociate-route-table --no-cli-pager --region {context.region} --association-id {context.gateway2_association_id} --output json\n"
            )
        if context.gateway3_association_id:
            f.write(
                f"aws ec2 disassociate-route-table --no-cli-pager --region {context.region} --association-id {context.gateway3_association_id} --output json\n"
            )
        f.write(
            f"aws ec2 associate-route-table --no-cli-pager --region {context.region} --subnet-id {context.public_subnet_id_2} --route-table-id {context.gateway1_route_table_id} --output json\n"
        )
        f.write(
            f"aws ec2 associate-route-table --no-cli-pager --region {context.region} --subnet-id {context.public_subnet_id_3} --route-table-id {context.gateway1_route_table_id} --output json"
        )


def create_terraform_provider_block(context: MigrationContext) -> str:
    return f"""
# Apply this file once first_step.sh finished running

terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = local.region
}}
"""


def create_locals_block(context: MigrationContext) -> str:
    return f"""
locals {{
  region            = "{context.region}"
  spacelift_version = "v3.0.0" # TODO: This is a tag of a Docker image uploaded to the "spacelift" and "spacelift-launcher" ECRs.
  website_domain    = "{context.cors_origin.replace('https://', '')}"
  website_endpoint  = "https://${{local.website_domain}}"
  license_token     = "<TODO: you need to set this value>" # TODO: This value must be set to the license token you received from Spacelift.
}}
"""


def format_subnet_cidr_blocks(cidr_blocks: List[str]) -> str:
    return "[" + ", ".join(f'"{item}"' for item in cidr_blocks) + "]"


def create_spacelift_module(unique_suffix: str, context: MigrationContext) -> str:
    public_subnet_cidr_blocks = format_subnet_cidr_blocks(context.public_subnet_cidr_blocks)
    private_subnet_cidr_blocks = format_subnet_cidr_blocks(context.private_subnet_cidr_blocks)

    return f"""        
module "spacelift" {{
  source = "github.com/spacelift-io/terraform-aws-spacelift-selfhosted?ref=v2-v3-migration-improvements"

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
 
  vpc_cidr_block             = "{context.vpc_cidr_block}"
  public_subnet_cidr_blocks  = {public_subnet_cidr_blocks}
  private_subnet_cidr_blocks = {private_subnet_cidr_blocks}
        
  number_of_images_to_retain   = 10
  backend_ecr_repository_name  = "spacelift"
  launcher_ecr_repository_name = "spacelift-launcher"

  security_group_names = {{
    database  = "database_sg"
    drain     = "drain_sg"
    scheduler = "scheduler_sg"
    server    = "server_sg"
  }}
        
  rds_engine_version              = "{context.rds_engine_version}"
  rds_preferred_backup_window     = "{context.rds_preferred_backup_window}"
  rds_regional_cluster_identifier = "spacelift"
  rds_parameter_group_name        = "spacelift"
  rds_subnet_group_name           = "spacelift"
  rds_parameter_group_description = "Spacelift core product database"
  rds_password_sm_arn             = aws_secretsmanager_secret.db_pw.arn
  rds_instance_configuration      = {{
    "primary" = {{
      instance_identifier = "{context.rds_instance_identifier}"
      instance_class      = "{context.rds_instance_class}"
    }}
  }}         
}}
"""


def create_spacelift_services_module(context: MigrationContext) -> str:
    return f"""
# Uncomment after the above module applied successfully
#module "spacelift_services" {{
#  source = "github.com/spacelift-io/terraform-aws-ecs-spacelift-selfhosted?ref=add-sqs-queues-and-iot"
#  
#  region               = local.region
#  unique_suffix        = module.spacelift.unique_suffix
#  kms_key_arn          = module.spacelift.kms_key_arn
#  server_domain        = local.website_domain
#  
#  license_token = local.license_token
#  
#  encryption_type        = "kms"
#  kms_encryption_key_arn = aws_kms_key.encryption_primary.arn
#  kms_signing_key_arn    = aws_kms_key.jwt.arn
#  
#  database_url           = format("postgres://%s:%s@%s:5432/spacelift?statement_cache_capacity=0", module.spacelift.rds_username, module.spacelift.rds_password, module.spacelift.rds_cluster_endpoint)
#  database_read_only_url = format("postgres://%s:%s@%s:5432/spacelift?statement_cache_capacity=0", module.spacelift.rds_username, module.spacelift.rds_password, module.spacelift.rds_cluster_reader_endpoint)
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
#  vpc_id      = module.spacelift.vpc_id
#  ecs_subnets = module.spacelift.private_subnet_ids
#  
#  server_lb_subnets           = module.spacelift.public_subnet_ids
#  server_security_group_id    = module.spacelift.server_security_group_id
#  server_lb_certificate_arn   = "{context.certificate_arn}"
#  
#  drain_security_group_id     = module.spacelift.drain_security_group_id
#  scheduler_security_group_id = module.spacelift.scheduler_security_group_id
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
    f.write(
        """
resource "aws_secretsmanager_secret" "db_pw" {
  name        = "spacelift/database"
  description = "Connection string for the Spacelift database"
  kms_key_id  = aws_kms_key.master.arn
}

resource "aws_secretsmanager_secret" "slack_credentials" {
  name        = "spacelift/slack-application"
  description = "Contains the Spacelift Slack application configuration"
  kms_key_id  = aws_kms_key.master.arn
}
""".lstrip()
    )


def write_kms_terraform_content(f, context: MigrationContext) -> None:
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

resource "aws_kms_key" "encryption_primary" {{
  description         = "Spacelift in-app encryption primary key. Used to encrypt user data stored in the database like VCS tokens."
  enable_key_rotation = true
  multi_region        = true

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


def write_iot_terraform_content(f, migration_context: MigrationContext) -> None:
    f.write(
        f"""
resource "aws_iam_role" "iot_message_sender_role" {{
  name = "spacelift-iot-{migration_context.region}"

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
