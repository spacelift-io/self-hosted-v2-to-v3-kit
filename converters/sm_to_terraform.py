from converters.terraformer import Terraformer
from .migration_context import MigrationContext


class SMTerraformer(Terraformer):
    def __init__(self, file_path: str, migration_context: MigrationContext):
        super().__init__(file_path, migration_context)

        self.sm_db_pw_resource_name = "aws_secretsmanager_secret.db_pw"
        self.sm_slack_resource_name = "aws_secretsmanager_secret.slack_credentials"
        self.sm_additional_root_cas_resource_name = (
            "aws_secretsmanager_secret.additional_root_ca_certificates"
        )
        self.sm_external_values_resource_name = "aws_secretsmanager_secret.external"
        self.sm_saml_credentials_resource_name = "aws_secretsmanager_secret.saml_credentials"

    def sm_to_terraform(self, logical_id: str, sm_secret_arn: str) -> None:
        if logical_id == "DBConnectionStringSecret":
            self.process(self.sm_db_pw_resource_name, sm_secret_arn)
        elif logical_id == "SlackCredentialsSecret":
            self.process(self.sm_slack_resource_name, sm_secret_arn)
        elif logical_id == "AdditionalRootCAsSecret":
            self.process(self.sm_additional_root_cas_resource_name, sm_secret_arn)
        elif logical_id == "ExternalValuesSecret":
            self.process(self.sm_external_values_resource_name, sm_secret_arn)
        elif logical_id == "SAMLCredentialsSecret":
            self.process(self.sm_saml_credentials_resource_name, sm_secret_arn)
