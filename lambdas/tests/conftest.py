import pytest
import psycopg2
from lambdas.layers.dbConfigLayer.python.DbConfig import DB_CONFIG
from datetime import datetime, timedelta
from nanoid import generate

class DatabaseHelpers:
    @staticmethod
    def seed_job_postings(cursor, 
                          num_records, 
                          days_old, 
                          job_title="Software Engineer Intern", 
                          location="British Columbia"):
        """
        Seeds the database with dummy job postings.

        :param cursor: A database cursor.
        :param num_records: Number of job postings to create.
        :param days_old: Age of the job postings in days.
        :param job_title: Title of the job postings.
        :param location: Location of the job postings.
        """
        for _ in range(num_records):
            date_posted = datetime.now() - timedelta(days=days_old)
            id = generate()
            query = """
                INSERT INTO jobs (job_url, site, title, company, location, job_type, date_posted)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, [
                f"http://example.com/job/{id}", "ExampleSite", job_title, "ExampleCompany", location, "Full-Time", date_posted
            ])
    
    @staticmethod
    def seed_default(cursor):
        """
        Seeds the database with default data

        :param cursor: A database cursor.
        """
        DatabaseHelpers.seed_job_postings(cursor, 5, days_old=40) 
        DatabaseHelpers.seed_job_postings(cursor, 15, days_old=20, location="British Columbia", job_title="Software Engineer")  
        DatabaseHelpers.seed_job_postings(cursor, 10, days_old=30, location="Ontario", job_title="Software Developer Intern")
        cursor.connection.commit()

    @staticmethod
    def clean_up_job_posts(cursor):
        """
        Cleans up the job posts from the database.

        :param cursor: A database cursor.
        """
        cursor.execute("DELETE FROM jobs")


@pytest.fixture(scope="class")
def db():
    """
    Pytest fixture to provide a database connection and cursor.
    Seeds and cleans up data before and after each TEST CLASS.
    Example:
        @pytest.mark.usefixtures("db")
        class TestExample:
            def test_some_db_functionality(self):
                ...
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Seed data before the test class
    DatabaseHelpers.clean_up_job_posts(cursor)  # Clean up any existing data
    DatabaseHelpers.seed_default(cursor)
    conn.commit()

    yield cursor

    # Clean up data after the test class
    DatabaseHelpers.clean_up_job_posts(cursor)
    conn.commit()

    cursor.close()
    conn.close()


@pytest.fixture()
def database_helper():
    """
    Example:
        def test_specific_database_operation(database_helper):
            # Seed specific data for this test
            database_helper.seed_job_postings(db_cursor, num_records=3, days_old=5)
            
            # Perform test operations...

            # Clean up data specific to this test
            database_helper.clean_up_job_posts(db_cursor)
    """
    return DatabaseHelpers