class MigrationContext:
    def __init__(self):
        # AWS region
        self.region: str | None = None

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

        # Website configuration
        self.cors_origin: str | None = None
        self.certificate_arn: str | None = None

        # VPC and network configuration
        self.vpc_cidr_block: str | None = None
        self.private_subnet_cidr_blocks: list[str] = ["", "", ""]
        self.public_subnet_cidr_blocks: list[str] = ["", "", ""]
        self.public_subnet_id_1: str | None = None
        self.public_subnet_id_2: str | None = None
        self.public_subnet_id_3: str | None = None

        # Route tables and associations
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
