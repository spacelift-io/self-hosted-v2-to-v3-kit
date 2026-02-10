import boto3
import sys
from pathlib import Path
from typing import Optional
from packaging import version

from converters.ecr_to_terraform import ECRTerraformer
from converters.iot_to_terraform import IOTTerraformer
from converters.rds_to_terraform import RDSTerraformer
from converters.s3_to_terraform import S3Terraformer
from converters.kms_to_terraform import KMSTerraformer
from converters.ec2_to_terraform import EC2Terraformer
from converters.sm_to_terraform import SMTerraformer
from converters.migration_context import MigrationContext, TargetType

from converters.sqs_to_terraform import SQSTerraformer
from scanners.iot_scanner import scan_iot_resources
from scanners.sqs_scanner import scan_sqs_resources
from utils.cli import parse_args
from utils.aws import create_session, get_ssm_parameter
from scanners.s3_scanner import scan_s3_resources
from scanners.kms_scanner import scan_kms_resources
from scanners.ec2_scanner import scan_ec2_resources
from scanners.ecr_scanner import scan_ecr_resources
from scanners.rds_scanner import scan_rds_resources
from scanners.sm_scanner import scan_sm_resources
from utils.terraform_generator import generate_tf_files
from utils.config import load_app_config


def initialize_output_dir(output_dir: str) -> str:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    existing_files = list(output_path.iterdir())
    if existing_files:
        print(
            f"\n    !!! Warning: Output directory '{output_dir}' is not empty. You will lose all {len(existing_files)} file(s) if you continue.\n"
        )
        confirmation = input("Continue? (y/n): ")
        if confirmation.lower() != "y":
            print("Operation cancelled.")
            sys.exit(0)

    f = output_path / "imports.tf"
    f.unlink(missing_ok=True)
    f.touch()

    return str(f)


def initialize_terraformers(terraform_file: str, context: MigrationContext) -> tuple:
    return (
        EC2Terraformer(terraform_file, context),
        KMSTerraformer(terraform_file, context),
        S3Terraformer(terraform_file, context),
        ECRTerraformer(terraform_file, context),
        RDSTerraformer(terraform_file, context),
        SMTerraformer(terraform_file, context),
        IOTTerraformer(terraform_file, context),
        SQSTerraformer(terraform_file, context),
    )


def check_version_requirement(session: boto3.Session) -> None:
    param_name = "/spacelift/install-version"
    min_version_str = "2.6.0"
    min_version = version.parse(min_version_str)

    version_str = get_ssm_parameter(session, param_name)
    if not version_str:
        print(
            f"Warning: SSM Parameter '{param_name}' not found. Cannot verify version requirements."
        )
        return

    # Parse the version, handling both formats with and without 'v' prefix
    try:
        current_version = version.parse(version_str.lstrip("v"))
        print(f"Found Spacelift version: {version_str}")
    except ValueError:
        print(f"Warning: Could not parse version string: {version_str}")
        return

    if current_version < min_version:
        print(f"Error: Required minimum version is {min_version_str}, but found {version_str}")
        sys.exit(1)

    print(
        f"Version check passed: {version_str} meets or exceeds required minimum version {min_version_str}"
    )


def get_unique_suffix(session: boto3.Session) -> str:
    param_name = "/spacelift/random-suffix"

    ssm_suffix = get_ssm_parameter(session, param_name)
    if ssm_suffix:
        print(f"Found unique suffix in SSM Parameter Store ({param_name}): {ssm_suffix}")
        return ssm_suffix
    else:
        raise ValueError(
            f"SSM Parameter '{param_name}' is required but not found. Make sure it exists in the SSM Parameter Store."
        )


def main(
    config_path: str, profile: Optional[str], output_dir: str, target_module: str = "ecs"
) -> None:
    config = load_app_config(config_path)

    session = create_session(config.aws_region, profile)

    check_version_requirement(session)
    unique_suffix = get_unique_suffix(session)

    terraform_file = initialize_output_dir(output_dir)
    migration_context = MigrationContext()
    migration_context.target = TargetType(target_module)
    migration_context.config = config

    (
        ec2_terraformer,
        kms_terraformer,
        s3_terraformer,
        ecr_terraformer,
        rds_terraformer,
        sm_terraformer,
        iot_terraformer,
        sqs_terraformer,
    ) = initialize_terraformers(terraform_file, migration_context)

    print("Alright, let's start scanning for resources...")

    scan_s3_resources(session, unique_suffix, s3_terraformer)
    scan_kms_resources(session, kms_terraformer)
    scan_ec2_resources(session, ec2_terraformer)
    scan_ecr_resources(ecr_terraformer)
    scan_sm_resources(session, sm_terraformer)
    scan_rds_resources(session, rds_terraformer)
    scan_iot_resources(iot_terraformer)
    scan_sqs_resources(session, sqs_terraformer)

    generate_tf_files(unique_suffix, migration_context, output_dir)

    print(
        f"Terraform files have been generated in the following directory: {output_dir}\n"
        "Everything is ready to go!\n"
    )


if __name__ == "__main__":
    args = parse_args()
    main(
        config_path=args.config,
        profile=args.profile,
        output_dir=args.output,
        target_module=args.target_module,
    )
