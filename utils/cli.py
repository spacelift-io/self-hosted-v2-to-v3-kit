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
    return parser.parse_args()
