# README

This is a Streamlit text-to-SQL application. It takes natural language input, retrieves the database schema, and generates SQL based on the schema and instructions. The app can execute the SQL and provide a natural language explanation of the generated SQL. Users can recognize discrepancies between their intent and the generated SQL, modify the SQL, and re-execute it.

## Prerequisites

- PostgreSQL
- AWS CLI configured
- Amazon Bedrock model access configured

## Setup

Set your environment variable for the database connection string:
```sh
export CONNECTION_STRING=your_connection_string
```

## Running the Application

To start the Streamlit application, run `streamlit run text-to-sql-bedrock.py`
