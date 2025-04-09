from typing import Dict, List
from converters.migration_context import MigrationContext
from converters.terraformer import Terraformer


class S3Terraformer(Terraformer):
    def __init__(self, file_path: str, migration_context: MigrationContext):
        super().__init__(file_path, migration_context)

        self.binaries_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket.binaries"
        )
        self.binaries_encryption_resource_name = "module.spacelift.module.s3.aws_s3_bucket_server_side_encryption_configuration.binaries"
        self.binaries_versioning_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_versioning.binaries"
        )

        self.deliveries_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket.deliveries"
        )
        self.deliveries_encryption_resource_name = "module.spacelift.module.s3.aws_s3_bucket_server_side_encryption_configuration.deliveries"
        self.deliveries_lifecycle_resource_name = "module.spacelift.module.s3.aws_s3_bucket_lifecycle_configuration.deliveries"
        self.deliveries_public_access_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_public_access_block.deliveries"
        )

        self.large_queue_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket.large_queue_messages"
        )
        self.large_queue_encryption_resource_name = "module.spacelift.module.s3.aws_s3_bucket_server_side_encryption_configuration.large_queue_messages"
        self.large_queue_versioning_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_versioning.large_queue_messages"
        )
        self.large_queue_lifecycle_resource_name = "module.spacelift.module.s3.aws_s3_bucket_lifecycle_configuration.large_queue_messages"
        self.large_queue_public_access_resource_name = "module.spacelift.module.s3.aws_s3_bucket_public_access_block.large_queue_messages"

        self.metadata_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket.metadata"
        )
        self.metadata_encryption_resource_name = "module.spacelift.module.s3.aws_s3_bucket_server_side_encryption_configuration.metadata"
        self.metadata_versioning_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_versioning.metadata"
        )
        self.metadata_lifecycle_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_lifecycle_configuration.metadata"
        )
        self.metadata_public_access_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_public_access_block.metadata"
        )

        self.modules_resource_name = "module.spacelift.module.s3.aws_s3_bucket.modules"
        self.modules_encryption_resource_name = "module.spacelift.module.s3.aws_s3_bucket_server_side_encryption_configuration.modules"
        self.modules_versioning_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_versioning.modules"
        )
        self.modules_lifecycle_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_lifecycle_configuration.modules"
        )
        self.modules_public_access_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_public_access_block.modules"
        )

        self.policy_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket.policy_inputs"
        )
        self.policy_encryption_resource_name = "module.spacelift.module.s3.aws_s3_bucket_server_side_encryption_configuration.policy_inputs"
        self.policy_versioning_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_versioning.policy_inputs"
        )
        self.policy_lifecycle_resource_name = "module.spacelift.module.s3.aws_s3_bucket_lifecycle_configuration.policy_inputs"
        self.policy_public_access_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_public_access_block.policy_inputs"
        )

        self.run_logs_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket.run_logs"
        )
        self.run_logs_encryption_resource_name = "module.spacelift.module.s3.aws_s3_bucket_server_side_encryption_configuration.run_logs"
        self.run_logs_versioning_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_versioning.run_logs"
        )
        self.run_logs_lifecycle_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_lifecycle_configuration.run_logs"
        )
        self.run_logs_public_access_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_public_access_block.run_logs"
        )

        self.states_resource_name = "module.spacelift.module.s3.aws_s3_bucket.states"
        self.states_encryption_resource_name = "module.spacelift.module.s3.aws_s3_bucket_server_side_encryption_configuration.states"
        self.states_versioning_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_versioning.states"
        )
        self.states_public_access_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_public_access_block.states"
        )

        self.uploads_resource_name = "module.spacelift.module.s3.aws_s3_bucket.uploads"
        self.uploads_encryption_resource_name = "module.spacelift.module.s3.aws_s3_bucket_server_side_encryption_configuration.uploads"
        self.uploads_versioning_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_versioning.uploads"
        )
        self.uploads_lifecycle_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_lifecycle_configuration.uploads"
        )
        self.uploads_public_access_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_public_access_block.uploads"
        )
        self.uploads_cors_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_cors_configuration.uploads[0]"
        )

        self.user_uploads_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket.user_uploads"
        )
        self.user_uploads_encryption_resource_name = "module.spacelift.module.s3.aws_s3_bucket_server_side_encryption_configuration.user_uploads"
        self.user_uploads_versioning_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_versioning.user_uploads"
        )
        self.user_uploads_lifecycle_resource_name = "module.spacelift.module.s3.aws_s3_bucket_lifecycle_configuration.user_uploads"
        self.user_uploads_public_access_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_public_access_block.user_uploads"
        )

        self.workspace_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket.workspaces"
        )
        self.workspace_encryption_resource_name = "module.spacelift.module.s3.aws_s3_bucket_server_side_encryption_configuration.workspaces"
        self.workspace_versioning_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_versioning.workspaces"
        )
        self.workspace_lifecycle_resource_name = "module.spacelift.module.s3.aws_s3_bucket_lifecycle_configuration.workspaces"
        self.workspace_public_access_resource_name = (
            "module.spacelift.module.s3.aws_s3_bucket_public_access_block.workspaces"
        )

        with open(self.file_path, "w") as f:
            f.write("# S3 buckets\n\n")

    def s3_to_terraform(
        self,
        bucketName,
        versioning_enabled,
        sse_enabled,
        lifecycle_enabled,
        public_access_blocked,
        cors_rules: List[Dict],
    ):
        if (
            "downloads" in bucketName
        ):  # In v2 we called it downloads, in v3 we call it binaries
            self.migration_context.binaries_bucket_name = bucketName
            self.process(self.binaries_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.binaries_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.binaries_encryption_resource_name, bucketName)

        elif "deliveries" in bucketName:
            self.migration_context.deliveries_bucket_name = bucketName
            self.process(self.deliveries_resource_name, bucketName)
            if sse_enabled:
                self.process(self.deliveries_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.deliveries_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.deliveries_public_access_resource_name, bucketName)

        elif "large-queue" in bucketName:
            self.migration_context.large_queue_name = bucketName
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
            self.process(self.modules_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.modules_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.modules_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.modules_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.modules_public_access_resource_name, bucketName)

        elif "policy-inputs" in bucketName:
            self.migration_context.policy_bucket_name = bucketName
            self.process(self.policy_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.policy_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.policy_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.policy_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.policy_public_access_resource_name, bucketName)

        elif "run-logs" in bucketName:
            self.migration_context.run_logs_bucket_name = bucketName
            self.process(self.run_logs_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.run_logs_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.run_logs_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.run_logs_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.run_logs_public_access_resource_name, bucketName)

        elif "states" in bucketName:
            self.migration_context.states_bucket_name = bucketName
            self.process(self.states_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.states_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.states_encryption_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.states_public_access_resource_name, bucketName)

        elif "uploads" in bucketName:
            self.migration_context.uploads_bucket_name = bucketName
            self.process(self.uploads_resource_name, bucketName)
            for rule in cors_rules:
                allowed_origins = rule.get("AllowedOrigins")
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
            self.process(self.workspace_resource_name, bucketName)
            if versioning_enabled:
                self.process(self.workspace_versioning_resource_name, bucketName)
            if sse_enabled:
                self.process(self.workspace_encryption_resource_name, bucketName)
            if lifecycle_enabled:
                self.process(self.workspace_lifecycle_resource_name, bucketName)
            if public_access_blocked:
                self.process(self.workspace_public_access_resource_name, bucketName)
