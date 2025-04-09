from converters.terraformer import Terraformer
from .migration_context import MigrationContext


class ECRTerraformer(Terraformer):
    def ecr_to_terraform(self, repository_name: str):
        if repository_name == "spacelift":
            self.process(
                "module.spacelift.module.ecr.aws_ecr_repository.backend",
                repository_name,
            )
            self.process(
                "module.spacelift.module.ecr.aws_ecr_lifecycle_policy.backend[0]",
                repository_name,
            )
        elif repository_name == "spacelift-launcher":
            self.process(
                "module.spacelift.module.ecr.aws_ecr_repository.launcher",
                repository_name,
            )
            self.process(
                "module.spacelift.module.ecr.aws_ecr_lifecycle_policy.launcher[0]",
                repository_name,
            )
