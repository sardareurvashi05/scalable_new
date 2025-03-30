from django.urls import path
from . import views
from .views import fetch_events
from .views import event_list_api, event_by_country_api,home

urlpatterns = [
    path('', views.suggest_events, name='home'),
    path('get_events/', views.get_events, name='get_events'),
    #path('fetch-trip-details/', views.fetch_trip_details, name='fetch_trip_details'),
    path('create_reminder_external_api/', views.create_reminder_external_api, name='create_reminder_external_api'),# 
    path('suggest_events/', views.suggest_events, name='suggest_events'),
    path('reminders/', views.reminders, name='reminders'),  # Use views.reminder_list
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('create_reminder/', views.create_reminder, name='create_reminder'),  # Make sure this is correct
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('reminders/delete/<int:reminder_id>/', views.reminder_delete, name='reminder_delete'),  # Use views.reminder_delete
    path('reminders/edit/<int:reminder_id>/', views.reminder_edit, name='reminder_edit'),  # New edit route
    #path('api/events/', event_list_api, name='event_list_api'),  # Fetch all events
    #path('api/events/<str:country>/', event_by_country_api, name='event_by_country_api'),  # Fetch specific country events
    #path('api/events/', fetch_events, name='fetch_events'),
]
