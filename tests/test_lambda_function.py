import pytest
from lambda_function.lambda_function import create_reminder

def test_create_reminder():
    trip_title = "Test Trip"
    start_date = "2025-03-10"
    
    try:
        create_reminder(trip_title, start_date)
        assert True
    except Exception:
        assert False
