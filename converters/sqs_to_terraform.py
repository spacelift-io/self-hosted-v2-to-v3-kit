from converters.terraformer import Terraformer
from .migration_context import MigrationContext


class SQSTerraformer(Terraformer):
    def __init__(self, file_path: str, migration_context: MigrationContext):
        super().__init__(file_path, migration_context)

        self.sqs_deadletter_queue_resource_name = "aws_sqs_queue.deadletter_queue"
        self.sqs_deadletter_fifo_queue_resource_name = "aws_sqs_queue.deadletter_fifo_queue"
        self.sqs_async_jobs_queue_resource_name = "aws_sqs_queue.async_jobs_queue"
        self.sqs_events_inbox_queue_resource_name = "aws_sqs_queue.events_inbox_queue"
        self.sqs_async_jobs_fifo_queue_resource_name = "aws_sqs_queue.async_jobs_fifo_queue"
        self.sqs_cronjobs_queue_resource_name = "aws_sqs_queue.cronjobs_queue"
        self.sqs_webhooks_queue_resource_name = "aws_sqs_queue.webhooks_queue"
        self.sqs_iot_queue_resource_name = "aws_sqs_queue.iot_queue"

    def sqs_to_terraform(self, queue_name: str, queue_url: str) -> None:
        if queue_name == "spacelift-dlq":
            self.process(self.sqs_deadletter_queue_resource_name, queue_url)
        elif queue_name == "spacelift-dlq.fifo":
            self.process(self.sqs_deadletter_fifo_queue_resource_name, queue_url)
        elif queue_name == "spacelift-async-jobs":
            self.process(self.sqs_async_jobs_queue_resource_name, queue_url)
        elif queue_name == "spacelift-events-inbox":
            self.process(self.sqs_events_inbox_queue_resource_name, queue_url)
        elif queue_name == "spacelift-async-jobs.fifo":
            self.process(self.sqs_async_jobs_fifo_queue_resource_name, queue_url)
        elif queue_name == "spacelift-cronjobs":
            self.process(self.sqs_cronjobs_queue_resource_name, queue_url)
        elif queue_name == "spacelift-webhooks":
            self.process(self.sqs_webhooks_queue_resource_name, queue_url)
        elif queue_name == "spacelift-iot":
            self.process(self.sqs_iot_queue_resource_name, queue_url)
