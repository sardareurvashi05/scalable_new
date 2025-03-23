# /home/ec2-user/environment/My_App/reminder_project/event_suggestions/urls.py
from django.contrib import admin
from django.urls import re_path
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from events.views import fetch_events,test_mail

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('events.urls')),  # Include events/urls.py at root level
    path('events_api/', fetch_events, name='fetch_events'),
    path('email/', test_mail, name='test_mail'),
]