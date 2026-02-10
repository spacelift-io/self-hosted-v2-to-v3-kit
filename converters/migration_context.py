from enum import Enum

from utils.config import AppConfig


class TargetType(Enum):
    ECS = "ecs"
    EKS = "eks"


class MigrationContext:
    def __init__(self):
        self.target: TargetType = TargetType.ECS

        # App config loaded from the SH v2 config file
        self.config: AppConfig = None

        # S3 bucket names
        self.binaries_bucket_name: str | None = None
        self.deliveries_bucket_name: str | None = None
        self.large_queue_name: str | None = None
        self.metadata_bucket_name: str | None = None
        self.modules_bucket_name: str | None = None
        self.policy_bucket_name: str | None = None
        self.run_logs_bucket_name: str | None = None
        self.states_bucket_name: str | None = None
        self.uploads_bucket_name: str | None = None
        self.user_uploads_bucket_name: str | None = None
        self.workspace_bucket_name: str | None = None

        # S3 bucket expirations
        self.binaries_bucket_expiration_days: str | None = None
        self.deliveries_bucket_expiration_days: str | None = None
        self.large_queue_name: str | None = None
        self.metadata_bucket_expiration_days: str | None = None
        self.modules_bucket_expiration_days: str | None = None
        self.policy_bucket_expiration_days: str | None = None
        self.run_logs_bucket_expiration_days: str | None = None
        self.states_bucket_expiration_days: str | None = None
        self.uploads_bucket_expiration_days: str | None = None
        self.user_uploads_bucket_expiration_days: str | None = None
        self.workspace_bucket_expiration_days: str | None = None

        # S3 replication configuration
        self.s3_replication_role_name: str | None = None
        self.s3_replication_policy_name: str | None = None
        self.s3_replica_region_name: str | None = None
        self.s3_replica_region_key_kms_arn: str | None = None
        self.s3_states_bucket_replica_arn: str | None = None
        self.s3_run_logs_bucket_replica_arn: str | None = None
        self.s3_modules_bucket_replica_arn: str | None = None
        self.s3_policy_input_bucket_replica_arn: str | None = None
        self.s3_workspace_bucket_replica_arn: str | None = None

        # Website configuration
        self.cors_origin: str | None = None

        # VPC and network configuration
        self.vpc_cidr_block: str | None = None
        self.private_subnet_cidr_blocks: list[str] = ["", "", ""]
        self.public_subnet_cidr_blocks: list[str] = ["", "", ""]
        self.public_subnet_id_1: str | None = None
        self.public_subnet_id_2: str | None = None
        self.public_subnet_id_3: str | None = None
        self.gateway1_route_table_id: str | None = None
        self.gateway2_association_id: str | None = None
        self.gateway3_association_id: str | None = None
        self.gateway2_route_table_id: str | None = None
        self.gateway3_route_table_id: str | None = None

        # RDS configuration
        self.rds_engine_version: str | None = None
        self.rds_preferred_backup_window: str | None = None
        self.rds_instance_identifier: str | None = None
        self.rds_instance_class: str | None = None
        self.rds_parameter_group_name: str | None = None
        self.rds_parameter_group_description: str | None = None

    @property
    def module_prefix(self) -> str:
        if self.target == TargetType.EKS:
            return "module.spacelift_eks.module.spacelift."
        return "module.spacelift."

    @property
    def module_output_ref(self) -> str:
        if self.target == TargetType.EKS:
            return "module.spacelift_eks"
        return "module.spacelift"
