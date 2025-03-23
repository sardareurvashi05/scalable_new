import boto3

def create_sns_topic(topic_name):
    """
    Create an SNS topic using boto3.

    :param topic_name: Name of the SNS topic to create
    :return: ARN of the created topic
    """
    try:
        # Create an SNS client
        sns_client = boto3.client('sns',region_name='us-east-1')

        # Create the SNS topic
        response = sns_client.create_topic(Name=topic_name)

        # Get the ARN of the created topic
        topic_arn = response['TopicArn']
        print(f"Topic created successfully. ARN: {topic_arn}")
        return topic_arn

    except Exception as e:
        print(f"Error creating topic: {e}")
        return None

if __name__ == "__main__":
    # Replace with your desired topic name
    topic_name = "SNSTopicEvents"
    create_sns_topic(topic_name)