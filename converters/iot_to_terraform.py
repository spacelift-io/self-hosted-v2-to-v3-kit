from converters.terraformer import Terraformer
from .migration_context import MigrationContext


class IOTTerraformer(Terraformer):
    def __init__(self, file_path: str, migration_context: MigrationContext):
        super().__init__(file_path, migration_context)

    def iot_to_terraform(self):
        self.process(
            "aws_iam_role.iot_message_sender_role",
            f"spacelift-iot-{self.migration_context.config.aws_region}",
        )
        self.process("aws_iot_topic_rule.iot_message_sending_rule", "spacelift")
        self.process(
            "aws_iam_role_policy.iot_message_sender_role_policy",
            f"spacelift-iot-{self.migration_context.config.aws_region}:allow-iot-sqs-sending",
        )
