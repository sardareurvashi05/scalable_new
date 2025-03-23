from rest_framework import serializers
from .models import Reminder
from .models import Event

"""class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = ['id', 'title', 'description', 'scheduled_time', 'created_at']"""

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['country', 'event_name', 'event_date', 'event_type'] 
