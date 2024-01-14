import json
import logging
from typing import List, Dict, Any, Optional

import psycopg2

try:
    # for local development, load environment variables from .env file
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    # In production
    from DbConnection import get_db_connection # dbConnectionLayer
    from DbConfig import DB_CONFIG # dbConfig file

FUNCTION_NAME = "FetchJobsDataLimited" 

def fetch_data_limited(cursor: psycopg2.extensions.cursor, limit: int = 25) -> List[Dict[str, Any]]:
    """
    Executes a query to fetch job data and returns the results as a list of dictionaries.

    :param cursor: Database cursor for executing queries.
    :param limit: Limit for number of rows fetched.
    :return: A list of dictionaries where each dictionary represents a row of job data.
    :raises: Propagates exceptions that occur during query execution.
    """
    try:
        query = f"SELECT id, title, city, location, company, job_type, date_posted, job_url FROM jobs ORDER BY date_posted DESC LIMIT {limit}"
        cursor.execute(query)
        colnames = [desc[0] for desc in cursor.description]
        return [dict(zip(colnames, row)) for row in cursor.fetchall()]
    except Exception as e:
        sub_function_name = "fetch_data_limited()"
        logging.error("[%s - %s]: Query execution failed. Exception: %s", FUNCTION_NAME, sub_function_name, e)
        raise
    
def lambda_handler(event: Optional[Dict[str, Any]], context: Optional[Any]) -> Dict[str, Any]:
    """
    AWS Lambda handler function to fetch job data and return it as JSON.

    :param event: The event triggering this Lambda function.
    :param context: Runtime information provided by AWS Lambda.
    :return: A dictionary with statusCode, body, and records_fetched.
    """
    default_limit = 25 
    max_limit = 100
    sub_function_name = "lambda_handler"
    
    try:
        limit = int(event.get('limit', default_limit))
        if limit < 1 or limit > max_limit:
            logging.error("[%s - %s]: Limit out of range (> 1 and < %d) (%d). Using default limit.", FUNCTION_NAME, sub_function_name, max_limit, limit)
            limit = default_limit
    except (ValueError, TypeError) as e:
        logging.error("[%s - %s]: Invalid limit value. Using default limit. Exception: %s", FUNCTION_NAME, sub_function_name, e)
        limit = default_limit
    
    with get_db_connection(**DB_CONFIG) as conn, conn.cursor() as cursor:
        rows = fetch_data_limited(cursor, limit)
        json_rows = json.dumps(rows, default=str)

    return {
        'statusCode': 200,
        'body': json_rows,
        'records_fetched': len(rows)
    }
    
if __name__ == "__main__":
    import os
    import sys
    
    # Import 
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sys.path.insert(0, project_root)
    from lambdas.layers.dbConnectionLayer.python.DbConnection import get_db_connection
    from lambdas.layers.dbConfigLayer.python.DbConfig import DB_CONFIG
    
    logging.basicConfig(level=logging.INFO)
    result = lambda_handler(None, None)

    # Extracting the statusCode, body, and records_fetched from the result
    status_code = result['statusCode']
    records_fetched = result['records_fetched']
    body = json.loads(result['body'])

    # Print statusCode, one example from body (if available), and records_fetched
    print(f"Status Code: {status_code}")
    print(f"Example Record: {body[0] if body else 'No records found'}")
    print(f"Total Records Fetched: {records_fetched}")
