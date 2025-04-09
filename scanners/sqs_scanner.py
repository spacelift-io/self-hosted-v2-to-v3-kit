from typing import Dict, List, Any
import boto3
from converters.sqs_to_terraform import SQSTerraformer
from scanners.cloudformation_helper import get_resources_from_cf_stack


def scan_sqs_resources(session: boto3.Session, terraformer: SQSTerraformer) -> None:
    print(" > Scanning SQS resources...")

    cloudformation = session.client("cloudformation")
    queues_urls = get_resources_from_cf_stack(
        cloudformation,
        "spacelift-infra",
        [
            "AsyncJobsFIFOQueue",
            "AsyncJobsQueue",
            "CronjobsQueue",
            "DeadletterFIFOQueue",
            "DeadletterQueue",
            "EventsInboxQueue",
            "IoTQueue",
            "WebhooksQueue",
        ],
    )

    if not queues_urls:
        raise Exception("No SQS queues found")

    for url in queues_urls:
        name = url.split("/")[-1]
        terraformer.sqs_to_terraform(name, url)
