import psycopg2
import pandas as pd
import streamlit as st
import os
import boto3

# Function to get the schema
@st.cache_data
def get_schema():
    connection = None
    try:
        print("Connecting to the database...")
        connection = psycopg2.connect(os.getenv("CONNECTION_STRING"))
        cursor = connection.cursor()
        
        # Execute a query to get the schema
        print("Executing schema query...")
        query = """
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public'
        ORDER BY table_name, column_name
        """
        cursor.execute(query)
        schema_info = cursor.fetchall()
        print("Schema query executed successfully!")

        # Create a DataFrame to display the schema
        schema_df = pd.DataFrame(schema_info, columns=['Table Name', 'Column Name', 'Data Type'])
        print("Schema DataFrame created successfully!")
        return schema_df

    except Exception as error:
        print(f"Error retrieving schema: {error}")
        st.error(f"Error retrieving schema: {error}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed.")

def format_schema(schema_df):
    schema_str = ""
    for index, row in schema_df.iterrows():
        schema_str += f"Table: {row['Table Name']}, Column: {row['Column Name']}, Type: {row['Data Type']}\n"
    return schema_str

def generate_sql_from_chatgpt(schema_str, instruction):
    bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
    modelId="anthropic.claude-3-sonnet-20240229-v1:0"
    
    prompt = f"""
    Your task is to generate SQL based on the my postgreSQL database schema and my instruction.
    only generate the SQL itself, no any markdown like "```sql" or "```" or any other formatting.

    here is my database schema:
    {schema_str}

    here is the instruction:
    {instruction}
    """

    messages = [
        {"role": "user", "content": [{"text": prompt}]}
    ]
    inferenceConfig = ({"maxTokens": 300,"temperature": 0.0})


    print("Sending request to Bedrock...")
    try:
        response = bedrock.converse(modelId=modelId, messages=messages, inferenceConfig=inferenceConfig)
        print("Received response from Bedrock.")
    except Exception as e:
        print(f"Error in Bedrock request: {e}")
        return "", ""

    sql_query = str(response["output"]["message"]["content"][0]["text"])
    print(sql_query)

    explanation_prompt = f"""
    Explain this SQL very concisely (less than 30 words):
    {sql_query}
    """
    try:
        messages = [
            {"role": "user", "content": [{"text": explanation_prompt}]}
        ]
        explanation_completion = bedrock.converse(modelId=modelId, messages=messages, inferenceConfig=inferenceConfig)
        explanation = str(explanation_completion["output"]["message"]["content"][0]["text"])
        print(explanation)
    except Exception as e:
        explanation = f"Error generating explanation: {e}"

    return sql_query, explanation

def execute_sql(sql_query):
    try:
        print("Executing SQL query...")
        connection = psycopg2.connect(os.getenv("CONNECTION_STRING"))
        cursor = connection.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        result_df = pd.DataFrame(result, columns=column_names)
        print("SQL query executed successfully!")
        return result_df
    except Exception as error:
        st.error(f"Error executing SQL: {error}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed.")

def main():
    st.title("Database Query Generator")
    instruction = st.text_area("Instruction:", height=50)
    sql_explanation = ""
    
    # Get the schema once and cache it
    schema_df = get_schema()
    if schema_df is not None:
        schema_str = format_schema(schema_df)
        st.sidebar.title("Database Schema")
        st.sidebar.write(schema_df)
    
    if st.button("Query"):
        print("Query button clicked.")
        if schema_df is not None and instruction:
            generated_sql, sql_explanation = generate_sql_from_chatgpt(schema_str, instruction)
            if generated_sql:
                st.session_state.generated_sql = generated_sql
                st.session_state.sql_explanation = sql_explanation
                result_df = execute_sql(generated_sql)
                st.write(result_df)
            else:
                print("Failed to generate SQL.")
    
    if 'generated_sql' in st.session_state and st.session_state.generated_sql:
        st.info("✨Generated SQL Explanation✨：\n\n" + st.session_state.get('sql_explanation', sql_explanation))
        modified_sql = st.text_area("Modify SQL", value=st.session_state.generated_sql, height=200, key="modified_sql")
        if st.button("Query Again"):
            print("Query Again button clicked.")
            # Update the session state with the modified SQL right before executing it
            st.session_state.generated_sql = st.session_state.modified_sql
            result_df = execute_sql(st.session_state.modified_sql)
            st.write(result_df)

if __name__ == "__main__":
    main()

