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
        "--create-eks",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Create a new EKS cluster, or use --no-create-eks to bring your own "
        "(only applies to --target-module eks, default: create)",
    )
    args = parser.parse_args()
    if not args.create_eks and args.target_module != "eks":
        parser.error("--no-create-eks can only be used with --target-module eks")
    return args
