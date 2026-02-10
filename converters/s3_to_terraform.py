from typing import Dict, List
from converters.migration_context import MigrationContext
from converters.terraformer import Terraformer


class S3Terraformer(Terraformer):
    def __init__(self, file_path: str, migration_context: MigrationContext):
        super().__init__(file_path, migration_context)

        self.s3_replication_role_resource = "aws_iam_role.replication_role"
        self.s3_replication_policy_resource = "aws_iam_policy.s3_replication_policy"
        self.s3_replication_policy_attachment_resource = (
            "aws_iam_role_policy_attachment.s3_replication_attachment"
        )

        self.binaries_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket.binaries"
        self.binaries_encryption_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket_server_side_encryption_configuration.binaries"
        self.binaries_versioning_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_versioning.binaries"
        )

        self.deliveries_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket.deliveries"
        self.deliveries_encryption_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket_server_side_encryption_configuration.deliveries"
        self.deliveries_lifecycle_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_lifecycle_configuration.deliveries"
        )
        self.deliveries_public_access_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_public_access_block.deliveries[0]"
        )

        self.large_queue_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket.large_queue_messages"
        )
        self.large_queue_encryption_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket_server_side_encryption_configuration.large_queue_messages"
        self.large_queue_versioning_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_versioning.large_queue_messages"
        )
        self.large_queue_lifecycle_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket_lifecycle_configuration.large_queue_messages"
        self.large_queue_public_access_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket_public_access_block.large_queue_messages[0]"

        self.metadata_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket.metadata"
        self.metadata_encryption_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket_server_side_encryption_configuration.metadata"
        self.metadata_versioning_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_versioning.metadata"
        )
        self.metadata_lifecycle_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_lifecycle_configuration.metadata"
        )
        self.metadata_public_access_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_public_access_block.metadata[0]"
        )

        self.modules_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket.modules"
        self.modules_encryption_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket_server_side_encryption_configuration.modules"
        self.modules_versioning_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_versioning.modules"
        )
        self.modules_lifecycle_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_lifecycle_configuration.modules"
        )
        self.modules_public_access_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_public_access_block.modules[0]"
        )
        self.modules_replication_resource_name = "aws_s3_bucket_replication_configuration.modules"

        self.policy_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket.policy_inputs"
        self.policy_encryption_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket_server_side_encryption_configuration.policy_inputs"
        self.policy_versioning_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_versioning.policy_inputs"
        )
        self.policy_lifecycle_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_lifecycle_configuration.policy_inputs"
        )
        self.policy_public_access_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_public_access_block.policy_inputs[0]"
        )
        self.policy_bucket_replication_resource_name = (
            "aws_s3_bucket_replication_configuration.policy_inputs"
        )

        self.run_logs_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket.run_logs"
        self.run_logs_encryption_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket_server_side_encryption_configuration.run_logs"
        self.run_logs_versioning_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_versioning.run_logs"
        )
        self.run_logs_lifecycle_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_lifecycle_configuration.run_logs"
        )
        self.run_logs_public_access_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_public_access_block.run_logs[0]"
        )
        self.run_logs_bucket_replication_resource_name = (
            "aws_s3_bucket_replication_configuration.run_logs"
        )

        self.states_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket.states"
        self.states_encryption_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket_server_side_encryption_configuration.states"
        self.states_versioning_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_versioning.states"
        )
        self.states_public_access_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_public_access_block.states[0]"
        )
        self.states_bucket_replication_resource_name = (
            "aws_s3_bucket_replication_configuration.states"
        )

        self.uploads_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket.uploads"
        self.uploads_encryption_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket_server_side_encryption_configuration.uploads"
        self.uploads_versioning_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_versioning.uploads"
        )
        self.uploads_lifecycle_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_lifecycle_configuration.uploads"
        )
        self.uploads_public_access_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_public_access_block.uploads[0]"
        )
        self.uploads_cors_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_cors_configuration.uploads[0]"
        )

        self.user_uploads_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket.user_uploads"
        )
        self.user_uploads_encryption_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket_server_side_encryption_configuration.user_uploads"
        self.user_uploads_versioning_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_versioning.user_uploads"
        )
        self.user_uploads_lifecycle_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_lifecycle_configuration.user_uploads"
        )
        self.user_uploads_public_access_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_public_access_block.user_uploads[0]"
        )

        self.workspace_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket.workspaces"
        self.workspace_encryption_resource_name = f"{self.module_prefix}module.s3.aws_s3_bucket_server_side_encryption_configuration.workspaces"
        self.workspace_versioning_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_versioning.workspaces"
        )
        self.workspace_lifecycle_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_lifecycle_configuration.workspaces"
        )
        self.workspace_public_access_resource_name = (
            f"{self.module_prefix}module.s3.aws_s3_bucket_public_access_block.workspaces[0]"
        )
        self.workspace_bucket_replication_resource_name = (
            "aws_s3_bucket_replication_configuration.workspaces"
        )

    def s3_to_terraform(
        self,
        bucketName,
        bucketExpirationDays,
        versioning_enabled,
        sse_enabled,
        lifecycle_enabled,
        public_access_blocked,
        cors_rules: List[Dict],
        bucket_replication_rules: List[Dict],
    ):
        if "downloads" in bucketName:  # In v2 we called it downloads, in v3 we call it binaries
            self.migration_context.binaries_bucket_name = bucketName
            self.migration_context.binaries_bucket_expiration_days = bucketExpirationDays
            self.process(self.binaries_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.binaries_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.binaries_encryption_resource_name, bucketName)

        elif "deliveries" in bucketName:
            self.migration_context.deliveries_bucket_name = bucketName
            self.migration_context.deliveries_bucket_expiration_days = bucketExpirationDays
            self.process(self.deliveries_resource_name, bucketName)
            if sse_enabled:
                self.process(self.deliveries_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.deliveries_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.deliveries_public_access_resource_name, bucketName)

        elif "large-queue" in bucketName:
            self.migration_context.large_queue_name = bucketName
            self.migration_context.large_queue_bucket_expiration_days = bucketExpirationDays
            self.process(self.large_queue_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.large_queue_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.large_queue_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.large_queue_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.large_queue_public_access_resource_name, bucketName)

        elif "metadata" in bucketName:
            self.migration_context.metadata_bucket_name = bucketName
            self.migration_context.metadata_bucket_expiration_days = bucketExpirationDays
            self.process(self.metadata_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.metadata_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.metadata_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.metadata_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.metadata_public_access_resource_name, bucketName)

        elif "modules" in bucketName:
            self.migration_context.modules_bucket_name = bucketName
            self.migration_context.modules_bucket_expiration_days = bucketExpirationDays
            self.process(self.modules_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.modules_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.modules_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.modules_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.modules_public_access_resource_name, bucketName)
            if bucket_replication_rules:
                self.migration_context.s3_modules_bucket_replica_arn = (
                    bucket_replication_rules[0].get("Destination", {}).get("Bucket")
                )
                self.process(
                    self.modules_replication_resource_name,
                    bucketName,
                )

        elif "policy-inputs" in bucketName:
            self.migration_context.policy_bucket_name = bucketName
            self.migration_context.policy_bucket_expiration_days = bucketExpirationDays
            self.process(self.policy_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.policy_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.policy_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.policy_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.policy_public_access_resource_name, bucketName)
            if bucket_replication_rules:
                self.migration_context.s3_policy_input_bucket_replica_arn = (
                    bucket_replication_rules[0].get("Destination", {}).get("Bucket")
                )
                self.process(
                    self.policy_bucket_replication_resource_name,
                    bucketName,
                )

        elif "run-logs" in bucketName:
            self.migration_context.run_logs_bucket_name = bucketName
            self.migration_context.run_logs_bucket_expiration_days = bucketExpirationDays
            self.process(self.run_logs_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.run_logs_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.run_logs_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.run_logs_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.run_logs_public_access_resource_name, bucketName)
            if bucket_replication_rules:
                self.migration_context.s3_run_logs_bucket_replica_arn = (
                    bucket_replication_rules[0].get("Destination", {}).get("Bucket")
                )
                self.process(
                    self.run_logs_bucket_replication_resource_name,
                    bucketName,
                )

        elif "states" in bucketName:
            self.migration_context.states_bucket_name = bucketName
            self.migration_context.states_bucket_expiration_days = bucketExpirationDays
            self.process(self.states_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.states_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.states_encryption_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.states_public_access_resource_name, bucketName)
            if bucket_replication_rules:
                self.migration_context.s3_states_bucket_replica_arn = (
                    bucket_replication_rules[0].get("Destination", {}).get("Bucket")
                )
                self.process(
                    self.states_bucket_replication_resource_name,
                    bucketName,
                )
        elif "uploads" in bucketName:
            self.migration_context.uploads_bucket_name = bucketName
            self.migration_context.uploads_bucket_expiration_days = bucketExpirationDays
            self.process(self.uploads_resource_name, bucketName)
            for rule in cors_rules:
                allowed_origins = rule.get("AllowedOrigins", [])
                if len(allowed_origins) > 0:
                    self.migration_context.cors_origin = allowed_origins[0]
                    self.process(self.uploads_cors_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.uploads_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.uploads_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.uploads_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.uploads_public_access_resource_name, bucketName)

        elif "user-uploaded-workspaces" in bucketName:
            self.migration_context.user_uploads_bucket_name = bucketName
            self.migration_context.user_uploads_bucket_expiration_days = bucketExpirationDays
            self.process(self.user_uploads_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.user_uploads_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.user_uploads_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.user_uploads_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.user_uploads_public_access_resource_name, bucketName)

        elif "workspace" in bucketName:
            self.migration_context.workspace_bucket_name = bucketName
            self.migration_context.workspace_bucket_expiration_days = bucketExpirationDays
            self.process(self.workspace_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.workspace_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.workspace_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.workspace_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.workspace_public_access_resource_name, bucketName)
            if bucket_replication_rules:
                self.migration_context.s3_workspace_bucket_replica_arn = (
                    bucket_replication_rules[0].get("Destination", {}).get("Bucket")
                )
                self.process(
                    self.workspace_bucket_replication_resource_name,
                    bucketName,
                )

    def replication_role_to_terraform(
        self,
        role_name: str,
        policy_name: str,
        policy_arn: str,
        s3_replica_key_kms_arn: str,
        s3_replica_region_name: str,
    ):
        if role_name:
            self.process(self.s3_replication_role_resource, role_name)
            self.migration_context.s3_replication_role_name = role_name
        if policy_arn:
            self.process(self.s3_replication_policy_resource, policy_arn)
            self.migration_context.s3_replication_policy_name = policy_name

        if role_name and policy_arn:
            self.process(
                self.s3_replication_policy_attachment_resource,
                f"{role_name}/{policy_arn}",
            )

        self.migration_context.s3_replica_region_name = s3_replica_region_name
        self.migration_context.s3_replica_region_key_kms_arn = s3_replica_key_kms_arn
