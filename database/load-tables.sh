#!/bin/bash

# PURPOSE: 
# Loading tables before running a scraper. Assumes that the PostgreSQL 
# container is already running 

# Load the environment variables from the .env file
if [ -f .env ]; then
    export $(cat .env | xargs)
else
    echo ".env file not found"
    exit 1
fi

# Configuration
CONTAINER_NAME="jobhub-postgres"
SQL_FILE="create_tables.sql"  # Replace with the actual SQL file name

# Step 1: Copy the SQL file to the container
echo "Copying SQL file to the container..."
docker cp $SQL_FILE $CONTAINER_NAME:/$SQL_FILE

# Step 2: Execute the SQL file
# Using 'postgres' as the Linux user in the container,
# and '$DB_USER' as the PostgreSQL user
echo "Executing SQL file..."
docker exec -u postgres $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /$SQL_FILE

echo "SQL file executed successfully."
