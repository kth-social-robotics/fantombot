import logging
import boto3


class SNSHandler(logging.Handler):
    def __init__(self, topic=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client = boto3.client("sns", region_name="us-east-1")
        self.topic = topic

    def emit(self, record):
        self.client.publish(
            TopicArn=self.topic,
            Message=self.format(record),
            Subject=f"{record.name}:{record.levelname}",
        )


def create_sns_logger():
    sns_handler = SNSHandler(topic="arn:aws:sns:us-east-1:ACCOUNT_NUMBER:code_errors")
    sns_handler = logging.Handler()
    sns_handler.setLevel(logging.WARNING)
    return sns_handler
