from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    due_date = models.DateTimeField(null=True, blank=True) 
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    email = models.EmailField(null=True, blank=True)

    def __str__(self):
        fields = ['note', 'due_date', 'email', 'is_completed']
        
       
"""class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Added ForeignKey to link with User
    country = models.CharField(max_length=100)
    event_name = models.CharField(max_length=200)
    date = models.DateField()

    def __str__(self):
        return f"{self.event_name} ({self.country})"
"""
class Event(models.Model):
    country = models.CharField(max_length=100)
    event_name = models.CharField(max_length=200)  # Ensure 'event_name' is used here
    event_date = models.DateField()
    event_type = models.IntegerField()

    def __str__(self):
        return self.event_name