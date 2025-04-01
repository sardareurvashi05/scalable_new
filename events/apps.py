from django.apps import AppConfig
from django.core.management import call_command

class RemindersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'

    def ready(self):
        # Call the custom management command to send the email
        call_command('send_startup_email')