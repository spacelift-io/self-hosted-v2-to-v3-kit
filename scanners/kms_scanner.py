import boto3
from converters.kms_to_terraform import KMSTerraformer
from scanners.cloudformation_helper import get_resources_from_cf_stack


def scan_kms_resources(session: boto3.Session, terraformer: KMSTerraformer) -> None:
    print(" > Scanning KMS resources...")

    cloudformation = session.client("cloudformation")

    [master_key_id] = get_resources_from_cf_stack(
        cloudformation, "spacelift-infra-kms", ["KMSMasterKey"]
    )
    [jwt_key_id] = get_resources_from_cf_stack(cloudformation, "spacelift-infra-kms", ["KMSJWTKey"])
    [backup_key] = get_resources_from_cf_stack(
        cloudformation, "spacelift-infra-kms", ["KMSJWTBackupKey"]
    )
    [alias] = get_resources_from_cf_stack(cloudformation, "spacelift-infra-kms", ["KMSJWTAlias"])

    if terraformer.is_primary_region():
        [app_encryption_key_id] = get_resources_from_cf_stack(
            cloudformation, "spacelift-infra-kms", ["KMSEncryptionPrimaryKey"]
        )
        terraformer.kms_to_terraform(app_encryption_key_id, "KMSEncryptionPrimaryKey")
    else:
        [replica_key] = get_resources_from_cf_stack(
            cloudformation, "spacelift-infra-kms", ["KMSEncryptionReplicaKey"]
        )
        terraformer.kms_to_terraform(replica_key, "KMSEncryptionReplicaKey")

    terraformer.kms_to_terraform(master_key_id, "KMSMasterKey")
    terraformer.kms_to_terraform(jwt_key_id, "KMSJWTKey")
    terraformer.kms_to_terraform(backup_key, "KMSJWTBackupKey")
    terraformer.kms_to_terraform(alias, "KMSJWTAlias")
