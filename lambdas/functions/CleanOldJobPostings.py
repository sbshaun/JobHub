import datetime
import json
from typing import Dict, Any, Optional
import psycopg2
import psycopg2.extras

# Configure environment-specific settings
try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    from DbConnection import get_db_connection  # Database Connection Layer
    from DbConfig import DB_CONFIG  # Database Configuration Layer
    from logger import error, success  # Logger Layer
else:
    # This else block runs if no exception was raised in the try block
    # Import absolute path for local development
    import sys
    import os
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sys.path.insert(0, project_root)
    from lambdas.layers.dbConnectionLayer.python.DbConnection import get_db_connection
    from lambdas.layers.dbConfigLayer.python.DbConfig import DB_CONFIG
    from lambdas.layers.loggerLayer.python.logger import error, success
    

FUNCTION_NAME = 'CleanOldJobPostings'

def get_date_days_ago(days: str) -> str:
    """
    :param days: A string representing the number of days.
    :return: A date string in 'YYYY-MM-DD' format representing the past date.
    :raises ValueError: If 'days' is not a valid integer or is negative.
    """
    try:
        days_ago = int(days)
        target_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        return target_date.strftime('%Y-%m-%d')
    except ValueError as e:
        error(FUNCTION_NAME, "get_date_days_ago", e)
        raise

def build_delete_query() -> str:
    """
    :param days_ago: The age threshold in days for deleting job postings.
    :return: An SQL delete query.
    """
    query = "DELETE FROM jobs WHERE date_posted < %s"
    return query

def execute_delete_query(cursor: psycopg2.extensions.cursor, query: str, days_ago: str) -> int:
    """
    :param cursor: A database cursor to execute the query.
    :param query: The SQL query string.
    :param days_ago: The date threshold parameter for the query.
    :return: The number of rows deleted.
    :raises Exception: If the database operation fails.
    """
    try:
        cutoff_date = get_date_days_ago(days_ago)
        cursor.execute(query, [cutoff_date])
        return cursor.rowcount
    except Exception as e:
        error(FUNCTION_NAME, "execute_delete_query", e)
        raise


def count_job_postings(cursor: psycopg2.extensions.cursor) -> int:
    """
    :param cursor: A database cursor.
    :return: The count of remaining records.
    """
    cursor.execute("SELECT COUNT(*) FROM jobs;")
    result = cursor.fetchone()
    return result[0]

def lambda_handler(event: Optional[Dict[str, Any]], context: Optional[Any]) -> Dict[str, Any]:
    """
    AWS Lambda handler function for deleting old job postings.

    :param event: The event triggering this Lambda function, containing 'daysAgo' parameter.
    :param context: Runtime information provided by AWS Lambda.
    :return: A dictionary with status code and operational details.
    """
    days_ago = event.get('daysAgo', '30')
    try:
        with get_db_connection(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                delete_query = build_delete_query()
                deleted_count = execute_delete_query(cursor, delete_query, days_ago)

                remaining_records = count_job_postings(cursor)
                conn.commit()

                success(FUNCTION_NAME, f"Successfully deleted {deleted_count} records.")
                return {
                    'statusCode': 200,
                    'records_deleted': deleted_count,
                    'records_remaining': remaining_records
                }
    except Exception as e:
        error(FUNCTION_NAME, "lambda_handler", e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

# Local development testing
if __name__ == "__main__":
    """
    WARNING: Ensure that this script is run against a Development database.
    The re-insertion logic is meant for testing purposes only and should not be used on a production database.
    """
    # Define a mock event for testing
    mock_event = {'daysAgo': '25'}
    days_ago = mock_event['daysAgo']
    target_date = get_date_days_ago(days_ago)

    # Connect to the database and fetch records that will be deleted
    with get_db_connection(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            print(f"Initial records: {count_job_postings(cursor=cursor)}")
            
            cursor.execute("SELECT * FROM jobs WHERE date_posted < %s", [target_date])
            records_to_delete = cursor.fetchall()

            # Execute lambda_handler to delete the records
            result = lambda_handler(mock_event, None)
            print(f"Lambda Function Response:\n{result}")
            # Re-insert the deleted records
            print(f"Re-inserting deleted records...")
            if records_to_delete:
                reinsert_query = """
                                    INSERT INTO jobs (
                                        id, job_url, site, title, company, company_url, location, job_type, 
                                        date_posted, date_fetched, interval, min_amount, max_amount, currency, 
                                        is_remote, num_urgent_words, benefits, emails, description, city
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """
                cursor.executemany(reinsert_query, records_to_delete)
                conn.commit()
                print(f"Re-inserted {len(records_to_delete)} records back into the database.")
            else:
                print(f"No deleted records found.")


            total_records = count_job_postings(cursor=cursor)
            print(f"Total records in the database after re-insertion: {total_records}")