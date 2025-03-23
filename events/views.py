from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.urls import reverse  # ✅ Import reverse
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets
from urllib.parse import urlencode
from dotenv import load_dotenv
import os
import json
import re
import requests
import pytz
from datetime import datetime, timedelta

# Google API imports
import google.auth
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from google.cloud import language_v1

# Local app imports
from .models import Reminder, Event
from .forms import ReminderForm, EventSuggestionForm
from .serializers import EventSerializer
from .google_cloud_nlp import analyze_text
from events.services.gateway_utils import sendEmail, send_message_to_sqs
from . import views  # Import views from the current directory (event_suggestions/views.py)

# Load environment variables
load_dotenv()


def create_reminder_external_api_old(request):
    api_data = {
        "trips": [
            {
                "tripTitle": "Mumbai",
                "username": "urvashi",
                "endDate": "2025-03-22",
                "startDate": "2025-03-19",
                "email": "user@example.com"
            }
        ]
    }
    create_reminder_from_api_data(api_data)
    context = {
        "message": "Reminders created successfully!"
    }

    return render(request, "events/create_reminder_external_api.html", context)

def create_reminder_external_api(request):
    if request.method == 'POST':
        # Get the selected city from the form
        city = request.POST.get('city')

        if city:
            # Construct the API URL using the city data
            api_url = f"https://1csykikez9.execute-api.us-east-1.amazonaws.com/prod/detail?userId=user1&title={city}"

            # Make the API request to fetch data
            response = requests.get(api_url)

            if response.status_code == 200:
                # If the API call is successful, get the JSON data
                api_data = response.json()

                # Pass the API data to the function that creates reminders
                create_reminder_from_api_data(api_data)

                # Prepare the success message
                context = {
                    "message": "Reminders created successfully!"
                }
            else:
                # Handle errors if the API call fails
                context = {
                    "message": "Failed to fetch data from the external API."
                }
        else:
            # If no city is selected, return an error message
            context = {
                "message": "Please select a city."
            }
    else:
        # If the request method is not POST
        context = {
            "message": "Invalid request. Please submit the form."
        }

    # Render the HTML template with the context
    return render(request, "events/create_reminder_external_api.html", context)

def test_mail(request):
    try:
        # Prepare email data
        email_message = {
            "email": "urvashisardare@yahoo.com",  # Replace with actual recipient email
            "subject": "Reminder Event",
            "body": "Reminder sent successfully.",
        }
        print(email_message)
        # Send email data to SQS
        message_body = json.dumps(email_message)
        response = send_message_to_sqs(message_body)
        print(response)
        status_code = sendEmail()
        print(f"Status code: {status_code} ")
        # Render a success message
        return HttpResponse("Mail sent successfully!")
    except Exception as e:
        print(f"Error in test_mail: {e}")
        return HttpResponse("Failed to send mail and message", status=500)
    
def create_reminder_from_api_data(api_data):

    for trip in api_data.get('trips', []):
        # Extract fields from the API data
        username = trip['username']
        trip_title = trip['tripTitle']
        start_date = datetime.strptime(trip['startDate'], '%Y-%m-%d').date()

        # Fetch the user object based on the username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            continue  # Skip if user doesn't exist

        # Create the reminder
        reminder = Reminder(
            user=user,
            due_date=start_date,  # Assuming 'startDate' should be the reminder due date
            note=trip_title,  # Using trip title as note
        )
        reminder.save()

@api_view(['GET'])
def fetch_events(request):
    # Get the country query parameter from the URL (e.g., ?country=USA)
    country = request.GET.get('country', None)

    # If the country parameter is provided, filter events by country
    if country:
        events = Event.objects.filter(country__iexact=country)
    else:
        # Otherwise, return all events
        events = Event.objects.all()

    # Serialize the events data
    serializer = EventSerializer(events, many=True)
    
    # Return the serialized data in the response
    return Response(serializer.data)
    
# Redirect to login page if not logged in
@login_required(login_url='/login/')
def dashboard_view(request):
    return render(request, 'events/dashboard.html', {'user': request.user})

API_GATEWAY_URL = "https://<your-api-id>.execute-api.<region>.amazonaws.com/prod/suggest-events"

@login_required(login_url='/login/')
def create_reminder(request):
    if request.method == 'POST':
        user_input = request.POST.get('note', '')
        print("1.................")
        # Use Google NLP to extract entities
        entities = analyze_text(user_input)
        print("2.................")
        # Extract date/time from entities (or fallback to default parsing logic)
        reminder_time = parse_date_from_entities(entities, user_input)
        
        print(reminder_time, user_input)
        
        if reminder_time:
            # Store the reminder in the database
            reminder = Reminder.objects.create(
                note =user_input,
                due_date =reminder_time,
                user = request.user
            )
            
            messages.success(request, "Reminder created successfully!")
            return redirect('dashboard')
            
        else:
            messages.error(request, "Error creating reminder. Check your input.")
    # Handle the GET request and render the form
    return render(request, 'events/create_reminder.html')

@login_required(login_url='/login/')
def create_reminder_1(request):
    if request.method == 'POST':
        form = ReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.user = request.user
            reminder.save()
            messages.success(request, "Reminder created successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Error creating reminder. Check your input.")
            print(form.errors)  # Debug output
    else:
        form = ReminderForm()
    return render(request, 'events/create_reminder.html', {'form': form})

def home(request):
    return render(request, 'events/home.html')
    
@api_view(['GET'])
def event_list_api(request):
    """Returns a list of all events"""
    return Response({"events": dummy_data})

@api_view(['GET'])
def event_by_country_api(request, country):
    """Returns events for a specific country"""
    country = country.capitalize()
    if country in dummy_data:
        return Response({country: dummy_data[country]})
    return Response({"error": "Country not found"}, status=404)

@login_required(login_url='/login/')
def reminder_delete(request, reminder_id):
    reminder = Reminder.objects.get(id=reminder_id, user=request.user)
    if request.method == 'POST':
        reminder.delete()
        messages.success(request, "Reminder deleted successfully!")
        return redirect('reminders')
    return render(request, 'events/reminder_delete.html', {'reminder': reminder})
    
@login_required(login_url='/login/')
def reminders(request):
    reminders = Reminder.objects.filter(user=request.user)  # Get user's reminders
    return render(request, 'events/reminders.html', {'reminders': reminders})


@login_required(login_url='/login/')
def reminder_edit(request, reminder_id):
    reminder = get_object_or_404(Reminder, id=reminder_id, user=request.user)
    if request.method == 'POST':
        form = ReminderForm(request.POST, instance=reminder)
        if form.is_valid():
            form.save()
            messages.success(request, "Reminder updated successfully!")
            return redirect('reminders')
        else:
            messages.error(request, "Error updating reminder. Check your input.")
            print(form.errors)
    else:
        form = ReminderForm(instance=reminder)
    return render(request, 'events/reminder_edit.html', {'form': form, 'reminder': reminder})
   
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! Please log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'events/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, 'events/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Change to your desired redirect
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'events/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')

SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_events(request):
    """Fetches and displays all events on the front page"""
    # Your dummy data for events
    dummy_data = {
        "USA": [
            "New Year's Eve in NYC", "Coachella Music Festival", "Comic-Con San Diego",
            "Burning Man", "SXSW Festival", "Mardi Gras in New Orleans", "Lollapalooza",
            "The Masters Golf Tournament", "Kentucky Derby", "CES Las Vegas", 
            "Ultra Music Festival", "Electric Daisy Carnival", "Nashville Country Music Festival"
        ],
        "India": [
            "Diwali Festival", "Holi Festival", "Jaipur Literature Festival",
            "Kumbh Mela", "Pushkar Camel Fair", "Durga Puja", "Goa Carnival",
            "Sunburn Festival", "Rath Yatra", "Onam Festival", 
            "India Art Fair", "Jaisalmer Desert Festival", "Hornbill Festival"
        ],
        "Japan": [
            "Cherry Blossom Festival", "Gion Matsuri", "Tokyo Game Show",
            "Sumo Wrestling Tournament", "Osaka Castle Festival", "Sapporo Snow Festival",
            "Fuji Rock Festival", "Awa Odori Dance Festival", "Nebuta Matsuri", "Tanabata Festival",
            "Tokyo International Film Festival", "Hakata Gion Yamakasa", "Sanja Matsuri"
        ],
        "Germany": [
            "Oktoberfest", "Berlin International Film Festival", "Christmas Markets",
            "Cologne Carnival", "Wacken Open Air", "Frankfurt Book Fair",
            "Stuttgart Beer Festival", "Dresden Music Festival", "Hamburg DOM", "Berlin Marathon",
            "Cannstatter Volksfest", "Kiel Week", "Rheinkirmes Düsseldorf"
        ],
        "Brazil": [
            "Carnival in Rio", "Rock in Rio", "São Paulo Fashion Week",
            "Oktoberfest Blumenau", "Parintins Folklore Festival", "Lollapalooza Brazil",
            "Festival de Parintins", "Rio Film Festival", "Festa Junina", "New Year's Eve at Copacabana",
            "Bumba Meu Boi", "Festival de Cinema de Gramado", "Passion Play of Nova Jerusalem"
        ],
        "France": [
            "Cannes Film Festival", "Tour de France", "Bastille Day Celebrations",
            "Nice Carnival", "Paris Fashion Week", "Fête de la Musique",
            "Avignon Theatre Festival", "Champs-Elysées Christmas Market", "Lyon Festival of Lights", "24 Hours of Le Mans"
        ],
        "Australia": [
            "Sydney New Year's Eve Fireworks", "Australian Open", "Sydney Mardi Gras",
            "Melbourne Cup", "Splendour in the Grass", "Vivid Sydney Festival",
            "Byron Bay Bluesfest", "Adelaide Fringe Festival", "Dark Mofo Festival", "Perth Festival"
        ]
    }

    # Get the 'country' query parameter
    country = request.GET.get('country')

    if country:
        # If a country is provided, filter the events for that country
        events = dummy_data.get(country, [])
    else:
        # If no country is provided, return all events
        events = [
            {"name": event, "location": country} 
            for country, events_list in dummy_data.items()
            for event in events_list
        ]

    # Format the events list for the response
    formatted_events = [{"name": event, "location": country} for country, events_list in dummy_data.items() for event in events]

    return JsonResponse(formatted_events, safe=False)


# Function to parse date and time from entities text
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
    
@login_required(login_url='/login/')
def suggest_events(request):
    suggestions = []
    user_id = None

    if request.method == "POST":
        form = EventSuggestionForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            location = form.cleaned_data['location']
            category = form.cleaned_data['category']

            # Filter dummy events based on user input
            suggestions = [
                event for event in DUMMY_EVENTS
                if (not location or event["location"].lower() == location.lower()) and
                   (not category or event["category"].lower() == category.lower())
            ]
    else:
        form = EventSuggestionForm()

    return render(request, 'events/suggest.html', {
        'form': form,
        'suggestions': suggestions,
        'user_id': user_id
    })
