from converters.terraformer import Terraformer


class RDSTerraformer(Terraformer):
    def rds_to_terraform(self, cluster: dict, instance: dict):
        self.migration_context.rds_engine_version = cluster["EngineVersion"]
        self.migration_context.rds_preferred_backup_window = cluster[
            "PreferredBackupWindow"
        ]
        self.migration_context.rds_instance_identifier = instance[
            "DBInstanceIdentifier"
        ]
        self.migration_context.rds_instance_class = instance["DBInstanceClass"]

        self.process(
            "module.spacelift.module.rds[0].aws_db_subnet_group.db_subnet_group",
            "spacelift",
        )
        self.process(
            "module.spacelift.module.rds[0].aws_rds_cluster.db_cluster", "spacelift"
        )
        self.process(
            'module.spacelift.module.rds[0].aws_rds_cluster_instance.db_instance["primary"]',
            instance["DBInstanceIdentifier"],
        )
        self.process(
            "module.spacelift.module.rds[0].aws_rds_cluster_parameter_group.spacelift",
            "spacelift",
        )
