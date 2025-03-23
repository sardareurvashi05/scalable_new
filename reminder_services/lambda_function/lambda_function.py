import json
import boto3
import requests
from datetime import datetime, timedelta
import os

# Initialize AWS services
dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
sns = boto3.client("sns")

# Environment Variables
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "Reminders")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:TripReminders")
S3_BUCKET = os.getenv("S3_BUCKET", "my-reminders-bucket")
API_URL = os.getenv("API_URL", "https://api.example.com/trips")  # Replace with actual API URL

# DynamoDB Table
table = dynamodb.Table(DYNAMODB_TABLE)

def fetch_trip_data():
    """Fetch trip data from an external API."""
    response = requests.get(API_URL)
    
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch API data")
        return {}

def create_reminder(trip_title, start_date):
    """Create a reminder 1 day before the trip start date."""
    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        due_date = start_date_obj - timedelta(days=1)  # 1 day before start date

        # Store in DynamoDB
        table.put_item(
            Item={
                "title": trip_title,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Store in S3
        reminder_data = {"title": trip_title, "due_date": due_date.strftime("%Y-%m-%d")}
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=f"reminders/{trip_title}.json",
            Body=json.dumps(reminder_data)
        )

        # Send SNS notification
        message = f"Reminder: Your trip '{trip_title}' starts soon! Due Date: {due_date.strftime('%Y-%m-%d')}"
        sns.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject="Trip Reminder")

        print(f"Reminder created: {trip_title} - Due: {due_date.strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"Error creating reminder: {str(e)}")

def lambda_handler(event, context):
    """AWS Lambda function handler."""
    trip_data = fetch_trip_data()
    if "trips" in trip_data:
        for trip in trip_data["trips"]:
            trip_title = trip.get("title")
            start_date = trip.get("start_date")
            
            if trip_title and start_date:
                create_reminder(trip_title, start_date)
    
    return {
        "statusCode": 200,
        "body": json.dumps("Reminders created successfully!")
    }
