"""from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
from datetime import timedelta

def sync_to_google_calendar(reminder):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    # Use project root directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Points to reminder_project/
    creds_path = os.path.join(BASE_DIR, 'credentials.json')
    token_path = os.path.join(BASE_DIR, 'token.json')

    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Credentials file not found at: {creds_path}")

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=0)  # For initial local setup only
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': reminder.title,
        'description': reminder.description,
        'start': {'dateTime': reminder.scheduled_time.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': (reminder.scheduled_time + timedelta(minutes=30)).isoformat(), 'timeZone': 'UTC'},
        'reminders': {'useDefault': True},
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event['id']"""