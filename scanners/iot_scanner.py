from converters.iot_to_terraform import IOTTerraformer


def scan_iot_resources(terraformer: IOTTerraformer) -> None:
    terraformer.iot_to_terraform()
