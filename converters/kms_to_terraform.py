from converters.migration_context import MigrationContext
from converters.terraformer import Terraformer


class KMSTerraformer(Terraformer):
    def __init__(self, file_path: str, migration_context: MigrationContext):
        super().__init__(file_path, migration_context)
        self.kms_master_key_resource_name = (
            "module.spacelift.module.kms[0].aws_kms_key.kms_master_key"
        )
        self.kms_encryption_key_resource_name = (
            "module.spacelift.module.kms[0].aws_kms_key.encryption_key"
        )
        self.kms_jwt_encryption_key_resource_name = (
            "module.spacelift.module.kms[0].aws_kms_key.jwt_key"
        )

    def kms_to_terraform(self, key_id: str, multi_regional: bool, description: str):
        if "Spacelift master KMS key" == description:
            self.process(self.kms_master_key_resource_name, key_id)
        elif "Spacelift KMS key used to sign and verify JWTs" == description:
            self.process(self.kms_jwt_encryption_key_resource_name, key_id)
        elif "Spacelift in-app encryption primary key" in description:
            self.process(self.kms_encryption_key_resource_name, key_id)
