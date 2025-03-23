import boto3

# Initialize DynamoDB
dynamodb = boto3.resource("dynamodb")
EVENTS_TABLE = "EventSuggestions"
table = dynamodb.Table(EVENTS_TABLE)

# Dummy event suggestions
DUMMY_EVENTS = {
    "New York": ["Broadway Show", "Central Park Tour", "Museum Visit"],
    "Los Angeles": ["Hollywood Walk", "Universal Studios", "Santa Monica Beach"],
    "Paris": ["Eiffel Tower Tour", "Louvre Museum", "Seine River Cruise"],
    "Tokyo": ["Shibuya Crossing", "Mount Fuji Tour", "Sushi Tasting"],
    "Dublin": ["Guinness Storehouse", "Trinity College Library", "Temple Bar"]
}

def populate_event_suggestions():
    """Populate DynamoDB with event suggestions (Run this once)."""
    for city, events in DUMMY_EVENTS.items():
        table.put_item(Item={"location": city, "events": events})
    print("Event data inserted successfully.")

def get_event_suggestions(location):
    """Retrieve event suggestions for a given location."""
    try:
        response = table.get_item(Key={"location": location})
        return response.get("Item", {}).get("events", ["No events found"])
    except Exception as e:
        print(f"Error fetching events: {str(e)}")
        return ["No events available"]
