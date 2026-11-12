import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to the configuration JSON file",
    )
    parser.add_argument(
        "--profile",
        type=str,
        required=False,
        help="AWS profile to use",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=False,
        default="dist",
        help="Output directory path for Terraform files",
    )
    parser.add_argument(
        "--target-module",
        type=str,
        required=False,
        default="ecs",
        choices=["ecs", "eks"],
        help="Target Terraform module type (default: ecs)",
    )
    parser.add_argument(
        "--container-registry",
        type=str,
        required=False,
        default="oci",
        choices=["oci", "ecr"],
        help="Where the services pull the images from: oci.spacelift.io, or the ECR repositories "
        "of your installation, for example in air-gapped or GovCloud setups (default: oci)",
    )
    return parser.parse_args()
