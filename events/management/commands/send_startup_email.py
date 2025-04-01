from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.conf import settings
import json
from events.views import test_mail

class Command(BaseCommand):
    
    help = 'Sends an email when the app is started'

    def handle(self, *args, **kwargs):
        #test_mail()
        pass