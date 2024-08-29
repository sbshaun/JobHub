import pytest
from lambdas.functions.CleanOldJobPostings import lambda_handler
from psycopg2.extensions import cursor as PgCursor

@pytest.mark.usefixtures("db")  
class TestCleanOldJobPostings:
    def test_invalid_input(self):
        invalid_event = {'daysAgo': 'ThisShouldNotBeAString'}
        result = lambda_handler(invalid_event, None)
        assert result['statusCode'] == 500 
        assert 'error' in result['body']

    def test_lambda_handler(self, db: PgCursor):
        result = lambda_handler({'daysAgo': '29'}, None)

        assert result['statusCode'] == 200
        assert result['records_deleted'] == 15

        db.execute("SELECT COUNT(*) FROM jobs")
        db_remaining_records = db.fetchone()[0]
        assert result['records_remaining'] == db_remaining_records
