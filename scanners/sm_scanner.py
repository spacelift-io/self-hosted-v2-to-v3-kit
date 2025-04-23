import boto3
from converters.sm_to_terraform import SMTerraformer
from scanners.cloudformation_helper import get_resources_from_cf_stack


def scan_sm_resources(session: boto3.Session, terraformer: SMTerraformer) -> None:
    print(" > Scanning Secrets Manager resources...")

    cloudformation = session.client("cloudformation")

    [conn_string_arn] = get_resources_from_cf_stack(
        cloudformation, "spacelift-infra", ["DBConnectionStringSecret"]
    )
    terraformer.sm_to_terraform("DBConnectionStringSecret", conn_string_arn)

    [slack_credentials_arn] = get_resources_from_cf_stack(
        cloudformation, "spacelift-infra", ["SlackCredentialsSecret"]
    )
    terraformer.sm_to_terraform("SlackCredentialsSecret", slack_credentials_arn)

    [additional_root_cert_arn] = get_resources_from_cf_stack(
        cloudformation, "spacelift-infra", ["AdditionalRootCAsSecret"]
    )
    terraformer.sm_to_terraform("AdditionalRootCAsSecret", additional_root_cert_arn)

    [external_arn] = get_resources_from_cf_stack(
        cloudformation, "spacelift-infra", ["ExternalValuesSecret"]
    )
    terraformer.sm_to_terraform("ExternalValuesSecret", external_arn)

    [saml_credentials_arn] = get_resources_from_cf_stack(
        cloudformation, "spacelift-infra", ["SAMLCredentialsSecret"]
    )
    terraformer.sm_to_terraform("SAMLCredentialsSecret", saml_credentials_arn)
