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
from django.urls import reverse
from django.urls import reverse
import json
import re
import requests
import pytz
from datetime import datetime, timedelta
from django.utils.timezone import now, timedelta

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

@login_required(login_url='/login/')
def create_reminder_api(request):
    if request.method == 'POST':
        # Extract the necessary data from the POST request
        username = request.POST.get('username')
        trip_title = request.POST.get('tripTitle')
        start_date = request.POST.get('startDate')
        end_date_str = request.POST.get('endDate')
        email = request.POST.get('email')

        try:
            # If no end date is provided, show an error and redirect
            if not end_date_str:
                messages.error(request, 'End date (due date) is required for the trip.')
                return redirect(reverse('fetch_trip_details'))  # Redirect to fetch_trip_details if no due date

            # Ensure the date is in the correct format
            try:
                # Convert the end date to date-only format and set time to 00:00:00
                due_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                due_date = due_date.replace(hour=0, minute=0, second=0)  # Set the time to 00:00:00
            except ValueError:
                # If the format is incorrect, show an error message
                messages.error(request, 'Invalid date format for due date. Please use YYYY-MM-DD.')
                return redirect(reverse('fetch_trip_details'))  # Redirect if the date format is incorrect

        except Exception as e:
            messages.error(request, f'Error fetching trip details: {e}')
            return redirect(reverse('fetch_trip_details'))  # Redirect back if an error occurs

        # Now let's create the reminder
        try:
            # Fetch the user by the provided username
            user = User.objects.get(username=username)

            # Create the reminder with the provided due_date (end_date)
            reminder = Reminder.objects.create(
                user=user,  # Associate the reminder with the user
                due_date=due_date,  # Set the due date as the trip's end date
                note=f"Reminder for the trip: {trip_title}",
                email=email,  # Ensure the email is added
            )

            messages.success(request, f'Reminder for trip "{trip_title}" created successfully!')
            return redirect(reverse('reminders'))  # Redirect to reminders.html if the reminder is created successfully

        except User.DoesNotExist:
            # If the user doesn't exist, show an error message and redirect
            messages.error(request, f'No user found with username: {username}')
            return redirect(reverse('fetch_trip_details'))  # Redirect to fetch_trip_details if user not found

    # If the method is not POST, redirect to the fetch_trip_details page
    return redirect(reverse('fetch_trip_details'))

def reminder_list(request):
    # Fetch all reminders for the logged-in user or apply a different filter if needed
    reminders = Reminder.objects.filter(user=request.user)
    print("Inside Reminder list")
    print(request.user)
    return render(request, 'events/reminders.html', {'reminders': reminders})
    
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

def fetch_trip_details(request):
    username = request.GET.get('username')
    trip_title = request.GET.get('tripTitle')

    # Check if both parameters are provided
    if username and trip_title:
        # Make the API request with username and tripTitle as parameters
        api_url = f"https://1csykikez9.execute-api.us-east-1.amazonaws.com/prod/detail?userId={username}&title={trip_title}"
        try:
            response = requests.get(api_url)

            if response.status_code == 200:
                data = response.json()
                trip_data = {
                    "trips": data.get('trips', [])
                }
            else:
                trip_data = {"trips": [], "error": "Failed to fetch trip details."}
        except Exception as e:
            trip_data = {"trips": [], "error": f"Error occurred: {str(e)}"}
        
    else:
        trip_data = {"trips": [], "error": "Username and Trip Title are required."}

    # Pass the trip data (and error message if any) to the template
    return render(request, "events/fetch_trip_details.html", {'trip_data': trip_data})
        

def test_mail(request):
    try:
        # Get T-1 date
        #t_minus_1 = now() + timedelta(days=7)
        t_minus_1 = now()
        # Query for reminders due tomorrow
        reminders = Reminder.objects.filter(due_date__date=t_minus_1.date(), is_completed=False)
        if not reminders:
            messages.info(request, "No reminders pending for today.")  # Add message
        
        for reminder in reminders:
            email_message = {
                "email": reminder.user.email,  # Sending to user's email
                "subject": "Upcoming Reminder Event",
                "body": f"Reminder: {reminder.note} is due on {reminder.due_date}.",
            }
            print(email_message)

            # Send email to SQS
            message_body = json.dumps(email_message)
            response = send_message_to_sqs(message_body)
            print(response)

            # Send actual email via API Gateway/SNS
            status_code = sendEmail()
            print(f"Status code: {status_code} ")
            reminder.is_completed = True
            reminder.save()
        
    except Exception as e:
        print(f"Error in send_t_minus_1_email: {e}")
        #return HttpResponse("Failed to send T-1 emails", status=500)
    reminders = Reminder.objects.filter(user=request.user)
    return render(request, 'events/reminders.html', {'reminders': reminders})
        
def test_mail_old():
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

        # Extract entities using Google NLP
        entities = analyze_text(user_input)

        # Extract email from user input
        email = extract_email(user_input)
        if not email:
            messages.error(request, "Email is required to create a reminder.")
            return redirect('create_reminder')

        # Extract date/time from entities or parse manually
        reminder_time = parse_date_from_entities(entities, user_input)

        if reminder_time:
            # Create and save the reminder
            reminder = Reminder.objects.create(
                note=user_input,
                due_date=reminder_time,
                user=request.user,
                email=email
            )
            messages.success(request, "Reminder created successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Could not determine a valid date. Please enter a valid reminder date.")

    return render(request, 'events/create_reminder.html')

def extract_email(text):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None

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
    reminders = Reminder.objects.filter(user=request.user)# Get user's reminders
    print("inside reminder")
    print(reminders)
    return render(request, 'events/reminders.html', {'reminders': reminders})

def update_reminder(request, reminder_id):
    reminder = get_object_or_404(Reminder, id=reminder_id)

    if request.method == "POST":
        form = ReminderForm(request.POST, instance=reminder)

        if form.is_valid():
            # Print values for debugging purposes
            print("Updated email:", form.cleaned_data['email'])
            reminder = form.save(commit=False)
            reminder.save()  # Save the changes to the database
            messages.success(request, "Reminder updated successfully!")
            return redirect('events/reminders')
        else:
            messages.error(request, "Error updating reminder. Please check your input.")

    else:
        form = ReminderForm(instance=reminder)

    return render(request, "events/reminders.html", {"form": form})
    
@login_required(login_url='/login/')
def reminder_edit(request, reminder_id):
    reminder = get_object_or_404(Reminder, id=reminder_id)

    if request.method == 'POST':
        form = ReminderForm(request.POST, instance=reminder)
        
        if form.is_valid():
            reminder = form.save(commit=False)  # Save the instance without committing to DB yet
            reminder.save()  # Commit the changes to the database
            messages.success(request, "Reminder updated successfully!")  # Display success message
            return render(request, "events/reminders.html", {"form": form})  # Redirect back to the list of reminders
        else:
            messages.error(request, "Please correct the errors below.")  # In case of form validation errors

    else:
        form = ReminderForm(instance=reminder)  # Initialize form with existing data

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


def parse_date_from_entities(entities, text):
    today = datetime.today()
    tomorrow = today + timedelta(days=1)

    for entity in entities:
        if entity['type'] == 'DATE':
            entity_text = entity['name'].lower()
            if 'today' in entity_text:
                return today
            elif 'tomorrow' in entity_text:
                return tomorrow
            elif 'next' in entity_text:
                return parse_next_day(entity_text, today)

    if "today" in text.lower():
        return today
    elif "tomorrow" in text.lower():
        return tomorrow
    elif "next" in text.lower():
        return parse_next_day(text.lower(), today)

    time_match = re.search(r'(\d{1,2}:\d{2}\s?[APap][Mm])', text)
    if time_match:
        time_str = time_match.group(0)
        try:
            reminder_time = datetime.strptime(time_str, "%I:%M %p")
            reminder_time = reminder_time.replace(year=today.year, month=today.month, day=today.day)
            return reminder_time
        except ValueError:
            pass

    date_match = re.search(r'(\d{1,2}[a-z]{2}\s+[A-Za-z]+(?:\s+\d{4})?)', text)
    if date_match:
        date_str = date_match.group(0)
        try:
            parsed_date = datetime.strptime(date_str, "%d %B %Y")
            return parsed_date
        except ValueError:
            date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
            try:
                parsed_date = datetime.strptime(date_str, "%d %B %Y")
                return parsed_date
            except ValueError:
                pass

    return None

def parse_next_day(text, today):
    days_of_week = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }

    for day, day_num in days_of_week.items():
        if day in text:
            today_weekday = today.weekday()
            days_diff = (day_num - today_weekday + 7) % 7
            if days_diff == 0:
                days_diff = 7  
            next_day = today + timedelta(days=days_diff)
            return next_day

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
