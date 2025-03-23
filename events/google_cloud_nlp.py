import os
import boto3
from google.cloud import language_v1
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

# Example usage
bucket_name = "eventdataforremindernotification"  # Specify your S3 bucket name
s3_key = "google-cloud/my-project-1532453810103-0c2b2ba12833.json"  # The path to the file in S3 (with directory structure, if applicable)
download_path = "/tmp/my-project-1532453810103-0c2b2ba12833.json"  # Local path where the file will be downloaded temporarily

# Function to read file from S3
def read_file_from_s3(bucket_name, s3_key, download_path):
    """Download file from S3 bucket and return its content."""
    s3 = boto3.client('s3')
    
    try:
        # Download the file from S3 to the local path
        s3.download_file(bucket_name, s3_key, download_path)
        print(f"File downloaded to {download_path}")

    except Exception as e:
        print(f"Error reading file from S3: {e}")
        return None

# Set the environment variable for Google Cloud SDK
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = download_path
# You can now proceed to use file content for further operations

def analyze_text(text):
    print("working")
    read_file_from_s3(bucket_name, s3_key, download_path)
    with open(download_path, 'r') as file:
        content = file.read()
        print("3.....................")    
        print(content) 
    client = language_v1.LanguageServiceClient()
    
    # Prepare the document to be analyzed
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)

    # Analyze the text using Google's NLP API
    response = client.analyze_entities(request={'document': document})
    
    entities = []
    for entity in response.entities:
        entities.append({
            'name': entity.name,
            'type': language_v1.Entity.Type(entity.type_).name,
            'salience': entity.salience
        })

    # You can also implement sentiment analysis, syntax analysis, etc. here if needed

    return entities
    