from converters.migration_context import MigrationContext
from converters.terraformer import Terraformer


class KMSTerraformer(Terraformer):
    def __init__(self, file_path: str, migration_context: MigrationContext):
        super().__init__(file_path, migration_context)
        self.kms_master_key_resource_name = "aws_kms_key.master"
        self.kms_encryption_key_resource_name = "aws_kms_key.encryption_primary"
        self.kms_jwt_encryption_key_resource_name = "aws_kms_key.jwt"
        self.kms_jwt_alias_resource_name = "aws_kms_alias.jwt_alias"
        self.kms_jwt_backup_key_resource_name = "aws_kms_key.jwt_backup_key"
        self.kms_replica_key_resource_name = "aws_kms_replica_key.encryption_replica_key"

    def kms_to_terraform(self, key_id: str, logical_id: str):
        if logical_id == "KMSMasterKey":
            self.process(self.kms_master_key_resource_name, key_id)
        elif logical_id == "KMSJWTKey":
            self.process(self.kms_jwt_encryption_key_resource_name, key_id)
        elif logical_id == "KMSEncryptionPrimaryKey":
            self.process(self.kms_encryption_key_resource_name, key_id)
        elif logical_id == "KMSJWTAlias":
            self.process(self.kms_jwt_alias_resource_name, key_id)
        elif logical_id == "KMSJWTBackupKey":
            self.process(self.kms_jwt_backup_key_resource_name, key_id)
        elif logical_id == "KMSEncryptionReplicaKey":
            self.process(self.kms_replica_key_resource_name, key_id)
