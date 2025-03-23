import boto3
from botocore.exceptions import ClientError

def create_s3_bucket():
    """Create an S3 bucket in the us-east-1 region."""
    bucket_name = 'eventdataforremindernotification'  # Replace with your desired bucket name
    region = 'us-east-1'  # Hardcoding the region to 'us-east-1'

    try:
        s3 = boto3.client('s3', region_name=region)
        
        # In 'us-east-1', we do not need to include LocationConstraint
        s3.create_bucket(Bucket=bucket_name)

        print(f'Bucket "{bucket_name}" created successfully in {region}.')
    except ClientError as e:
        print(f'Error creating bucket: {e}')
        return False  # Indicate failure
    return True  # Indicate success

# Call the function to create the S3 bucket
create_s3_bucket()


def upload_file_to_s3(bucket_name, file_path, s3_key):
    """Upload a file to an S3 bucket."""
    try:
        # Create an S3 client
        s3 = boto3.client('s3')

        # Upload the file
        s3.upload_file(file_path, bucket_name, s3_key)
        print(f"File '{file_path}' uploaded successfully to '{bucket_name}/{s3_key}'.")
    except ClientError as e:
        print(f"Error uploading file: {e}")
        return False  # Indicate failure
    return True  # Indicate success

# Define the S3 bucket and file details
bucket_name = 'eventdataforremindernotification'  # Replace with your S3 bucket name
file_path = '/home/ec2-user/environment/My_App/reminder_project/config/google-cloud/my-project-1532453810103-0c2b2ba12833.json'  # Full path to your file
s3_key = 'google-cloud/my-project-1532453810103-0c2b2ba12833.json'  # The key (name) for the file in the S3 bucket

# Call the function to upload the file
upload_file_to_s3(bucket_name, file_path, s3_key)