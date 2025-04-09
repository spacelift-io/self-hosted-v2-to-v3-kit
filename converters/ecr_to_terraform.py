from converters.terraformer import Terraformer
from .migration_context import MigrationContext


class ECRTerraformer(Terraformer):
    def __init__(self, file_path: str, migration_context: MigrationContext):
        super().__init__(file_path, migration_context)

        self.backend_repository_resource_name = (
            "module.spacelift.module.ecr.aws_ecr_repository.backend"
        )
        self.backend_lifecycle_policy_resource_name = (
            "module.spacelift.module.ecr.aws_ecr_lifecycle_policy.backend[0]"
        )
        self.launcher_repository_resource_name = (
            "module.spacelift.module.ecr.aws_ecr_repository.launcher"
        )
        self.launcher_lifecycle_policy_resource_name = (
            "module.spacelift.module.ecr.aws_ecr_lifecycle_policy.launcher[0]"
        )

    def ecr_to_terraform(self, repository_name: str):
        if repository_name == "spacelift":
            self.process(
                self.backend_repository_resource_name,
                repository_name,
            )
            self.process(
                self.backend_lifecycle_policy_resource_name,
                repository_name,
            )
        elif repository_name == "spacelift-launcher":
            self.process(
                self.launcher_repository_resource_name,
                repository_name,
            )
            self.process(
                self.launcher_lifecycle_policy_resource_name,
                repository_name,
            )
