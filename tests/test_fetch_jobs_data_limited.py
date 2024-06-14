import pytest
import json
from lambdas.functions.FetchJobsDataLimited import lambda_handler

@pytest.mark.usefixtures("db")
class TestFetchJobsDataLimited:
    def test_fetch_with_days_old(self):
        # Fetch jobs posted within 30 days
        mock_event = {'location':'', 'title':'', 'postedWithin':'30'}
        result = lambda_handler(mock_event, None)
        fetched_jobs = json.loads(result['body'])
        assert len(fetched_jobs) == 25

    def test_fetch_with_location(self):
        # Fetch jobs from BC
        mock_event = {'location':'BC', 'title':'', 'postedWithin':''}
        result = lambda_handler(mock_event, None)
        fetched_jobs = json.loads(result['body'])
        print(len(fetched_jobs))
        assert len(fetched_jobs) == 20

    def test_fetch_with_title(self):
        # Fetch jobs with title 'Engineer'
        result = lambda_handler({'title': 'Engineer'}, None)
        fetched_jobs = json.loads(result['body'])
        assert len(fetched_jobs) == 20

        # Fetch jobs with title 'Software'
        result = lambda_handler({'title': 'Software'}, None)
        fetched_jobs = json.loads(result['body'])
        assert len(fetched_jobs) == 30

    def test_fetch_with_combined_filters(self):
        result = lambda_handler({'postedWithin': '30', 'location': 'BC', 'title': 'Software'}, None)
        fetched_jobs = json.loads(result['body'])
        assert len(fetched_jobs) == 15

        result = lambda_handler({'postedWithin': '40', 'location': '', 'title': 'Software'}, None)
        fetched_jobs = json.loads(result['body'])
        assert len(fetched_jobs) == 30

    def test_invalid_input(self):
        # Test with invalid input
        mock_event = {'location': 'TestLocation', 'postedWithin': 'invalid', 'title': 'TestTitle'}
        result = lambda_handler(mock_event, None)

        # Assertions for invalid input
        assert result['statusCode'] == 400
        assert 'error' in json.loads(result['body'])
        
    def test_fetch_default_limit(self):
        # Test fetching with the default limit
        mock_event = {}  # Empty event should use default limit
        result = lambda_handler(mock_event, None)
        fetched_jobs = json.loads(result['body'])
        assert len(fetched_jobs) == 25

    def test_fetch_custom_limit(self):
        # Test fetching with a custom limit
        mock_event = {'limit': 10}
        result = lambda_handler(mock_event, None)
        fetched_jobs = json.loads(result['body'])
        assert len(fetched_jobs) == 10

    def test_fetch_above_max_limit(self):
        # Max limit is 100, test fetching with a limit above the maximum
        mock_event = {'limit': 150}
        result = lambda_handler(mock_event, None)
        fetched_jobs = json.loads(result['body'])
        assert len(fetched_jobs) == 25

    def test_fetch_with_invalid_limit(self):
        # Test fetching with an invalid limit value (e.g., a string)
        mock_event = {'limit': 'this is a string lol'}
        result = lambda_handler(mock_event, None)
        assert result['statusCode'] == 200
        fetched_jobs = json.loads(result['body'])
        assert len(fetched_jobs) == 25

    def test_fetch_with_negative_limit(self):
        # Test fetching with a negative limit
        mock_event = {'limit': -10}
        result = lambda_handler(mock_event, None)
        assert result['statusCode'] == 200
        fetched_jobs = json.loads(result['body'])
        assert len(fetched_jobs) == 25
