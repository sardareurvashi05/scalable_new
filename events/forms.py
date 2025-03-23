from django import forms
from .models import Reminder
# Event suggestion form does not need to be a ModelForm
class EventSuggestionForm(forms.Form):
    user_id = forms.IntegerField(required=False)
    location = forms.CharField(max_length=100, required=False)
    category = forms.CharField(max_length=50, required=False)

class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ['due_date', 'note']  # Adjusted to match template
        widgets = {
            'due_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'required': True
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reminder details...',
                'rows': 4,
                'required': True
            }),
        }
        
"""class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ['note']  # Adjusted to match template
        widgets = {
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reminder details...',
                'rows': 4,
                'required': True
            }),
        }"""