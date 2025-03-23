import boto3

# Initialize API Gateway client
apigateway_client = boto3.client('apigatewayv2')

# Step 1: Create an API Gateway HTTP API
api_response = apigateway_client.create_api(
    Name='EventsAPI',
    ProtocolType='HTTP',
    Target='https://1234abcd.ngrok.io/api/events/'  # Replace with your Django API URL
)
api_id = api_response['ApiId']
print(f"Created API Gateway with ID: {api_id}")

# Step 2: Deploy the API
deployment_response = apigateway_client.create_deployment(
    ApiId=api_id,
    StageName='prod'
)
print("API deployed to stage 'prod'.")

# Step 3: Get the API Gateway URL
api_url = f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/events"
print(f"API Gateway URL: {api_url}")
