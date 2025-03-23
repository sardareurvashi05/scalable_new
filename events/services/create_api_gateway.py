import boto3
import time

LAMBDA_FUNCTION_NAME='EventsLambda'

def create_api_gateway(lambda_function_arn):
    apigateway_client = boto3.client('apigateway', region_name='us-east-1')

    # Create a new REST API
    api_response = apigateway_client.create_rest_api(
        name='APIGatewayEvents',
        description='API Gateway for Lambda',
        endpointConfiguration={
            'types': ['REGIONAL']
        }
    )
    api_id = api_response['id']

    # Get the root resource
    resources = apigateway_client.get_resources(
        restApiId=api_id
    )
    root_resource_id = resources['items'][0]['id']

    # Create a new resource (e.g., /myresource)
    resource_response = apigateway_client.create_resource(
        restApiId=api_id,
        parentId=root_resource_id,
        pathPart='sendemail'
    )
    resource_id = resource_response['id']

    # Create a method (GET) for the resource
    apigateway_client.put_method(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod='GET',
        authorizationType='NONE'
    )

    # Integrate the Lambda function with the GET method
    apigateway_client.put_integration(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod='GET',
        integrationHttpMethod='POST',
        type='AWS_PROXY',
        uri=f'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_function_arn}/invocations'
    )

    # Grant API Gateway permissions to invoke Lambda
    lambda_client = boto3.client('lambda')
    lambda_client.add_permission(
        FunctionName=LAMBDA_FUNCTION_NAME,
        StatementId='SNSapigateway-access' + str(int(time.time())),
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com'
    )

    # Deploy the API
    apigateway_client.create_deployment(
        restApiId=api_id,
        stageName='prod'
    )
    
    print(f"API Gateway created with URL: https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/sendemail")
    
if __name__ == "__main__":
    lambda_arn = 'arn:aws:lambda:us-east-1:865249859257:function:EventsLambda'
    create_api_gateway(lambda_arn)