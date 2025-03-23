import boto3
import zipfile
import os

ROLE_ARN = 'arn:aws:iam::865249859257:role/LabRole'
SQS_QUEUE_ARN='arn:aws:sns:us-east-1:865249859257:SNSTopicEvents'
LAMBDA_FUNCTION_NAME='EventsLambda'
#SNS_QUEUE_ARN = 'arn:aws:sns:us-east-1:763605845924:SNSTopicInventory'
def create_lambda_function():
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Path to your lambda deployment package
    lambda_code_path = 'lambda_function.zip'

    # Ensure your lambda code is packaged in a .zip format
    with zipfile.ZipFile(lambda_code_path, 'w') as zf:
        zf.write('./lambda_function.py', arcname='lambda_function.py')
    
    with open(lambda_code_path, 'rb') as zip_file:
        lambda_response = lambda_client.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime='python3.8',
            Role=ROLE_ARN,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_file.read()}
        )
    print("Lambda Function Created:", lambda_response)
    
    # Add permission for SQS to invoke the Lambda function
    response_sqs = lambda_client.add_permission(
        FunctionName=LAMBDA_FUNCTION_NAME,  # Replace with your Lambda function name
        StatementId='SQSTriggerAccess',       # Unique ID for this permission
        Action='lambda:InvokeFunction',
        Principal='sqs.amazonaws.com',       # Principal for SQS
        SourceArn=SQS_QUEUE_ARN  # Replace with your SQS Queue ARN
    )
    print(f"SQS Permission added: {response_sqs}")
    
    # Link Lambda with SQS

    """lambda_client.create_event_source_mapping(
        EventSourceArn=SQS_QUEUE_ARN,
        FunctionName=LAMBDA_FUNCTION_NAME,
        BatchSize=1,
        Enabled=True
    )"""


if __name__ == "__main__":
    create_lambda_function()