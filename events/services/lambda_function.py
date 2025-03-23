import boto3
import json

sqs_client = boto3.client('sqs')
sns_client = boto3.client('sns')

def lambda_handler(event, context):
    sqs_queue_url = 'https://sqs.us-east-1.amazonaws.com/865249859257/EventQueue'
    sns_topic_arn = 'arn:aws:sns:us-east-1:865249859257:SNSTopicEvents'
    email_address = 'urvashisardare@yahoo.com'

    try:
        # Ensure email subscription
        ensure_email_subscription(sns_topic_arn, email_address)

        # Receive messages from SQS
        response = sqs_client.receive_message(
            QueueUrl=sqs_queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=10  # Enable long polling
        )
        print(f"Raw SQS response: {response}")

        # Process messages
        if "Messages" in response:
            for message in response["Messages"]:
                message_body = message["Body"]
                receipt_handle = message["ReceiptHandle"]
                message_text = json.loads(message_body)
                # Ensure email subscription
                ensure_email_subscription(sns_topic_arn, message_text["email"])
                # Publish to SNS
                sns_response = sns_client.publish(
                    TopicArn=sns_topic_arn,
                    Message=message_text["body"],
                    Subject = message_text["subject"]
                )
                print(f"Published message to SNS: {sns_response['MessageId']}")

                # Delete the message from SQS
                sqs_client.delete_message(
                    QueueUrl=sqs_queue_url,
                    ReceiptHandle=receipt_handle
                )
                print(f"Deleted message from SQS: {message_body}")
        else:
            print("No messages in the queue.")

    except Exception as e:
        print(f"Error processing messages: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps("Function executed successfully!")
    }


def ensure_email_subscription(topic_arn, email):
    try:
        subscriptions = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)['Subscriptions']
        for subscription in subscriptions:
            if subscription['Endpoint'] == email and subscription['Protocol'] == 'email':
                print(f"Email {email} is already subscribed.")
                return

        sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
        print(f"Confirmation email sent to {email}.")
    except Exception as e:
        print(f"Error ensuring email subscription: {e}")
        