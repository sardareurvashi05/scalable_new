import requests
from requests_aws4auth import AWS4Auth
import boto3
from django.conf import settings

def sendEmail():
    region = 'us-east-1'
    service = 'execute-api'
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    aws_auth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    url = "https://e0qpmfrxf2.execute-api.us-east-1.amazonaws.com/prod/sendemail"
    
    try:
        response = requests.get(url, auth=aws_auth)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx/5xx)
        print(f"Response: {response.text}")
        return response.status_code
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        print(f"Response content: {err.response.content}")
    except Exception as err:
        print(f"Other error occurred: {err}")
        

def send_message_to_sqs(message_body):
    # Initialize SQS client
    sqs = boto3.client(
        'sqs',
        region_name="us-east-1",
    )

    response = sqs.send_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/865249859257/EventQueue',
        MessageBody=message_body,
    )
    return response