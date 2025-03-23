import boto3
import json
from django.conf import settings

# Uses Cloud9 IAM role credentials
sqs = boto3.client('sqs', region_name='us-east-1')

def send_to_sqs(reminder_id):
    queue_url = settings.SQS_QUEUE_URL
    message = {
        'reminder_id': reminder_id,
        'scheduled_time': str(Reminder.objects.get(id=reminder_id).scheduled_time),
        'user_email': Reminder.objects.get(id=reminder_id).user.email  # Pass email for SES
    }
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message)
    )