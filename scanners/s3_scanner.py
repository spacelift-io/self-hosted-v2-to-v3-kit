from typing import Dict, Any
import boto3
from converters.s3_to_terraform import S3Terraformer
from converters.migration_context import MigrationContext
from scanners.cloudformation_helper import get_resources_from_cf_stack


def scan_s3_resources(
    session: boto3.Session, unique_suffix: str, terraformer: S3Terraformer
) -> None:
    # Get the migration context which has the config
    migration_context = terraformer.migration_context
    print(" > Scanning S3 resources...")

    cloudformation = session.client("cloudformation")
    bucket_names = get_resources_from_cf_stack(
        cloudformation,
        "spacelift-infra-s3",
        [
            "DeliveriesBucket",
            "DownloadsBucket",
            "LargeQueueMessagesBucket",
            "MetadataBucket",
            "ModulesBucket",
            "PolicyInputsBucket",
            "RunLogsBucket",
            "StatesBucket",
            "UploadsBucket",
            "UserUploadedWorkspacesBucket",
            "WorkspacesBucket",
        ],
    )

    s3 = session.client("s3")

    for bucket_name in bucket_names:
        bucket_expiration = _get_bucket_expiration(s3, bucket_name)
        versioning_status = _get_versioning_status(s3, bucket_name)
        sse_enabled = _is_sse_enabled(s3, bucket_name)
        lifecycle_enabled = _is_lifecycle_enabled(s3, bucket_name)
        public_access_blocked = _is_public_access_blocked(s3, bucket_name)
        cors_rules = _get_bucket_cors(s3, bucket_name).get("CORSRules", [])
        bucket_replication_rules = (
            _get_bucket_replication(s3, bucket_name)
            .get("ReplicationConfiguration", {})
            .get("Rules", [])
        )

        terraformer.s3_to_terraform(
            bucket_name,
            bucket_expiration,
            versioning_status,
            sse_enabled,
            lifecycle_enabled,
            public_access_blocked,
            cors_rules,
            bucket_replication_rules,
        )

    _process_replication_role(session, cloudformation, terraformer, migration_context)


def _get_versioning_status(s3: Any, bucket_name: str) -> bool:
    versioning_resp = s3.get_bucket_versioning(Bucket=bucket_name)
    return versioning_resp.get("Status") == "Enabled"


def _is_sse_enabled(s3: Any, bucket_name: str) -> bool:
    try:
        encryption_resp = s3.get_bucket_encryption(Bucket=bucket_name)
        rules = encryption_resp["ServerSideEncryptionConfiguration"]["Rules"]

        for rule in rules:
            sse_algorithm = rule["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
            kms_key_id = rule["ApplyServerSideEncryptionByDefault"].get("KMSMasterKeyID")
            if sse_algorithm == "aws:kms" and kms_key_id is not None:
                return True
    except s3.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ServerSideEncryptionConfigurationNotFoundError":
            return False
        raise
    return False


def _is_lifecycle_enabled(s3: Any, bucket_name: str) -> bool:
    lifecycle_resp = _get_bucket_lifecycle(s3, bucket_name)

    for rule in lifecycle_resp["Rules"]:
        if rule.get("Status") == "Enabled":
            return True
    return False


def _get_bucket_expiration(s3: Any, bucket_name: str) -> int:
    lifecycle_resp = _get_bucket_lifecycle(s3, bucket_name)

    for rule in lifecycle_resp["Rules"]:
        if rule.get("ID").startswith("expire-after-"):
            return rule.get("Expiration").get("Days")
    return 0


def _is_public_access_blocked(s3: Any, bucket_name: str) -> bool:
    public_access_resp = s3.get_public_access_block(Bucket=bucket_name)
    return public_access_resp.get("PublicAccessBlockConfiguration", {}).get(
        "BlockPublicAcls", False
    )


def _get_bucket_cors(s3: Any, bucket_name: str) -> Dict:
    try:
        return s3.get_bucket_cors(Bucket=bucket_name)
    except s3.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchCORSConfiguration":
            return {"CORSRules": []}
        raise


def _get_bucket_lifecycle(s3: Any, bucket_name: str) -> Dict:
    try:
        return s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    except s3.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchLifecycleConfiguration":
            return {"Rules": []}
        raise


def _get_bucket_replication(s3: Any, bucket_name: str) -> Dict:
    try:
        return s3.get_bucket_replication(Bucket=bucket_name)
    except s3.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ReplicationConfigurationNotFoundError":
            return {"Rules": []}
        raise


def _process_replication_role(
    session: boto3.Session,
    cloudformation: Any,
    terraformer: S3Terraformer,
    migration_context: MigrationContext,
) -> None:
    if (
        not migration_context.config
        or not migration_context.config.disaster_recovery
        or not migration_context.config.disaster_recovery.s3_bucket_replication
        or not migration_context.config.disaster_recovery.s3_bucket_replication.enabled
    ):
        return

    replication_resources = get_resources_from_cf_stack(
        cloudformation, "spacelift-infra-s3", ["S3ReplicationRole", "S3ReplicationPolicy"]
    )

    if not replication_resources:
        return

    (replication_role_name, replication_policy_arn) = replication_resources

    iam = session.client("iam")
    policy = iam.get_policy(PolicyArn=replication_policy_arn)

    terraformer.replication_role_to_terraform(
        replication_role_name,
        policy["Policy"]["PolicyName"],
        replication_policy_arn,
        migration_context.config.disaster_recovery.s3_bucket_replication.replica_kms_key_arn,
        migration_context.config.disaster_recovery.replica_region,
    )

    print(" > Replication configuration is the following:")
    print(f" >   - Replication role name: {replication_role_name}")
    print(f" >   - Replication policy ARN: {replication_policy_arn}")
    print(
        f" >   - Replica KMS key ARN: {migration_context.config.disaster_recovery.encryption_primary_key_arn}"
    )
    print(f" >   - Replica region: {migration_context.config.disaster_recovery.replica_region}")
