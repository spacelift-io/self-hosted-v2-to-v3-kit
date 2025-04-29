from converters.terraformer import Terraformer
from .migration_context import MigrationContext


class RDSTerraformer(Terraformer):
    def __init__(self, file_path: str, migration_context: MigrationContext):
        super().__init__(file_path, migration_context)

        self.db_subnet_group_resource_name = (
            "module.spacelift.module.rds[0].aws_db_subnet_group.db_subnet_group"
        )
        self.db_cluster_resource_name = "module.spacelift.module.rds[0].aws_rds_cluster.db_cluster"
        self.db_instance_resource_name = (
            'module.spacelift.module.rds[0].aws_rds_cluster_instance.db_instance["primary"]'
        )
        self.parameter_group_resource_name = (
            "module.spacelift.module.rds[0].aws_rds_cluster_parameter_group.spacelift"
        )

    def rds_to_terraform(self, cluster: dict, instance: dict):
        if self.migration_context.config.uses_custom_database_connection_string():
            # The user handles their own database outside of Cloudformation
            return

        self.migration_context.rds_engine_version = cluster["EngineVersion"]
        self.migration_context.rds_preferred_backup_window = cluster["PreferredBackupWindow"]
        self.migration_context.rds_instance_identifier = instance["DBInstanceIdentifier"]
        self.migration_context.rds_instance_class = instance["DBInstanceClass"]

        self.process(
            self.db_subnet_group_resource_name,
            "spacelift",
        )
        self.process(self.db_cluster_resource_name, "spacelift")
        self.process(
            self.db_instance_resource_name,
            instance["DBInstanceIdentifier"],
        )
        self.process(
            self.parameter_group_resource_name,
            "spacelift",
        )
