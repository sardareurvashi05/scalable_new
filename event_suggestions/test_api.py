import os
import re
from google.cloud import language_v1
from datetime import datetime, timedelta
from pathlib import Path

# Set the Google Cloud service account credentials (use your downloaded JSON key)
BASE_DIR = Path(__file__).resolve().parent.parent
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BASE_DIR, 'config', 'google-cloud', 'my-project-1532453810103-0c2b2ba12833.json')

# Function to analyze text with Google Cloud NLP
def analyze_text(text):
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
    return entities

# Function to parse date and time from entities
def parse_date_from_entities(entities, text):
    today = datetime.today()
    tomorrow = today + timedelta(days=1)

    # Loop through the entities and check for specific date-related terms
    for entity in entities:
        print(f"Entity: {entity['name']}, Type: {entity['type']}")  # Debug: Print each entity

        if entity['type'] == 'DATE':  # If a date entity is found
            entity_text = entity['name'].lower()

            if 'today' in entity_text:
                return today
            elif 'tomorrow' in entity_text:
                return tomorrow
            elif 'next' in entity_text:
                # Handle "next" term (e.g., "next Monday")
                return parse_next_day(entity_text, today)

    # Handle direct date expressions like "today" or "tomorrow"
    if "today" in text.lower():
        return today
    elif "tomorrow" in text.lower():
        return tomorrow

    # Check for "next Monday", "next Tuesday", etc.
    if "next" in text.lower():
        return parse_next_day(text.lower(), today)

    # Try parsing time directly from the text (e.g., "3 PM" or "9:00 AM")
    time_match = re.search(r'(\d{1,2}:\d{2}\s?[APap][Mm]|[APap][Mm]\s?\d{1,2})', text)
    if time_match:
        time_str = time_match.group(0)
        try:
            reminder_time = datetime.strptime(time_str, "%I:%M %p")  # Parse time like "3:00 PM"
            reminder_time = reminder_time.replace(year=today.year, month=today.month, day=today.day)
            return reminder_time
        except ValueError:
            pass  # Continue if time parsing fails

    # Try parsing explicit date formats (e.g., "10th April 2025")
    date_match = re.search(r'(\d{1,2}[a-z]{2}\s+[A-Za-z]+(?:\s+\d{4})?)', text)
    if date_match:
        date_str = date_match.group(0)
        try:
            # Parse date like "10th April 2025" or "10 April 2025"
            parsed_date = datetime.strptime(date_str, "%d %B %Y")
            return parsed_date
        except ValueError:
            # Try parsing with ordinal suffixes removed (e.g., "10th" -> "10")
            date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
            try:
                parsed_date = datetime.strptime(date_str, "%d %B %Y")
                return parsed_date
            except ValueError:
                pass

    # If no date or time-related entity is found, return None
    return None

# Helper function to parse "next <day>"
def parse_next_day(text, today):
    days_of_week = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    for day, day_num in days_of_week.items():
        if day in text:
            today_weekday = today.weekday()
            # Calculate how many days until the next occurrence of the given day
            days_diff = (day_num - today_weekday + 7) % 7
            if days_diff == 0:
                days_diff = 7  # If it's today, go to the next week

            next_day = today + timedelta(days=days_diff)
            return next_day

    # If no matching day was found, return None
    return None

# Example usage
text = "Birthday wishes on 10th April 2025."


"""
"Meet me tomorrow at 3 PM."
".Let's have a call next Friday at 2 PM"
"I'll remind you on next Wednesday at 10 AM."
"Birthday wishes on 10th April 2025."
"""
text = "Birthday wishes on 10th April 2025"
entities = analyze_text(text)
reminder_time = parse_date_from_entities(entities, text)
print("Parsed reminder time:", reminder_time)
