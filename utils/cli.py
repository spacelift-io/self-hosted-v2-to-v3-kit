import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--region",
        type=str,
        required=True,
        help="Name of the AWS region where the resources are located",
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
    return parser.parse_args()
