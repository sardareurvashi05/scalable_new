import boto3
import os

def create_sqs_queue(queue_name):
    # Initialize SQS client
    sqs = boto3.client(
        'sqs',
        region_name='us-east-1',
    )

    try:
        # Create the queue
        response = sqs.create_queue(
            QueueName=queue_name,
            Attributes={
                'DelaySeconds': '0',
                'MessageRetentionPeriod': '86400',  # 1 day
            }
        )

        # Print the URL of the created queue
        print(f"Queue created successfully! URL: {response['QueueUrl']}")
        return response['QueueUrl']

    except Exception as e:
        print(f"Error creating queue: {str(e)}")
        return None


if __name__ == "__main__":
    queue_name = "EventQueue"  # Replace with your desired queue name
    create_sqs_queue(queue_name)