from converters.ecr_to_terraform import ECRTerraformer


def scan_ecr_resources(terraformer: ECRTerraformer) -> None:
    for ecr_repo in ["spacelift", "spacelift-launcher"]:
        terraformer.ecr_to_terraform(ecr_repo)
