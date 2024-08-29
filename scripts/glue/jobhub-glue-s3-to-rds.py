import os
import sys
import boto3
import logging
import psycopg2 
import pandas as pd
from io import BytesIO, StringIO
from argparse import ArgumentParser
from datetime import datetime, timedelta

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_environment_variables():
    try:
        # if this is run in glue, use the AWS Glue provided env variables
        # for reference: https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api-crawler-pyspark-extensions-get-resolved-options.html
        from awsglue.utils import getResolvedOptions
        args = getResolvedOptions(sys.argv, ['S3_PATH', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD'])
        return args
    except Exception:
        # if run locally, use the .env file 
        from dotenv import load_dotenv
        load_dotenv()  # Fallback to .env file if not running on AWS Glue
        return {
            'DB_HOST': os.getenv('DB_HOST'),
            'DB_PORT': os.getenv('DB_PORT'),
            'DB_NAME': os.getenv('DB_NAME'),
            'DB_USER': os.getenv('DB_USER'),
            'DB_PASSWORD': os.getenv('DB_PASSWORD')
        }

def is_s3_path(file_path):
    return file_path.startswith('s3://')

def read_csv(file_path):
    logging.info("Reading data from %s", file_path)
    try:
        if is_s3_path(file_path):
            s3 = boto3.client('s3')
            bucket_name = file_path.split('/')[2]
            s3_path = '/'.join(file_path.split('/')[3:])
            obj = s3.get_object(Bucket=bucket_name, Key=s3_path)
            df = pd.read_csv(BytesIO(obj['Body'].read()))
        else:
            df = pd.read_csv(file_path)
    except Exception as e:
        logging.error("Error reading CSV file: %s", e)
        sys.exit(1)

    # Remove the 'Unnamed: 0' column if it exists
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])

    return df

def process_data(df):
    # Convert 'date_posted' from string to datetime
    df['date_posted'] = pd.to_datetime(df['date_posted'], format='%Y-%m-%d', errors='coerce')

    # Calculate the cutoff date for one month ago
    one_month_ago = datetime.now() - timedelta(days=30)

    # Filter for the last month's data
    df = df[df['date_posted'] >= one_month_ago]

    # Sort by 'date_posted'
    df = df.sort_values(by='date_posted', ascending=False)
    
    # Filtering for Jobs in Canada and creating an explicit copy to avoid SettingWithCopyWarning
    df_canada = df[df['location'].str.contains("Canada", na=False)].copy()

    # Cleaning 'location' Column
    # Extracting city from the 'location' column
    df_canada['city'] = df_canada['location'].apply(lambda x: x.split(',')[0].strip())

    # Add current date to the DataFrame
    df['date_fetched'] = datetime.now().date()
    
    return df_canada

def load_to_postgres(df, db_config):
    logging.info("Loading data into PostgreSQL...")
    try:
        with psycopg2.connect(host=db_config["DB_HOST"], port=db_config["DB_PORT"], 
                                dbname=db_config["DB_NAME"], user=db_config["DB_USER"], 
                                password=db_config["DB_PASSWORD"]) as conn:
            with conn.cursor() as cursor:
                insert_columns = ', '.join([f'"{col}"' for col in df.columns])  # Ensure columns are properly quoted
                placeholders = ', '.join(['%s'] * len(df.columns))
                insert_sql = f'INSERT INTO jobs ({insert_columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'
                for row in df.itertuples(index=False, name=None):
                    cursor.execute(insert_sql, row)
    except Exception as e:
        logging.error("Error loading data into PostgreSQL: %s", e)
        sys.exit(1)
    else:
        logging.info("Data loaded successfully into the 'jobs' table.")



def main(file_path):
    db_config = load_environment_variables()
    df = read_csv(file_path)
    df_processed = process_data(df) 
    # process data: filter for 
    # 1. only the last month's data and 
    # 2. jobs in Canada
    load_to_postgres(df_processed, db_config)

if __name__ == "__main__":
    db_config = load_environment_variables()
    # Use the S3 path from the environment variables if available, otherwise default to the local file 'jobs.csv'
    file_path = db_config.get('S3_PATH', '/Users/markvu/code/projects/Jobhub/scripts/glue/aggregated_jobs.csv')

    main(file_path)
