class MigrationContext:
    def __init__(self):
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
        self.cors_origin: str | None = None
        self.vpc_cidr_block: str | None = None
        self.private_subnet_cidr_blocks: list[str] | None = list(range(3))
        self.public_subnet_cidr_blocks: list[str] | None = list(range(3))
        self.rds_engine_version: str | None = None
        self.rds_preferred_backup_window: str | None = None
        self.rds_instance_identifier: str | None = None
        self.rds_instance_class: str | None = None
