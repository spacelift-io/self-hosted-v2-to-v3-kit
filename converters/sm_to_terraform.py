from typing import Dict
from converters.terraformer import Terraformer
from .migration_context import MigrationContext


class SMTerraformer(Terraformer):
    def __init__(self, file_path: str, migration_context: MigrationContext):
        super().__init__(file_path, migration_context)

        self.sm_db_pw_resource_name = "aws_secretsmanager_secret.db_pw"
        self.sm_slack_resource_name = "aws_secretsmanager_secret.slack_credentials"

    def sm_to_terraform(self, logical_id: str, sm_secret_arn: str) -> None:
        if logical_id == "DBConnectionStringSecret":
            self.process(self.sm_db_pw_resource_name, sm_secret_arn)
        elif logical_id == "SlackCredentialsSecret":
            self.process(self.sm_slack_resource_name, sm_secret_arn)
