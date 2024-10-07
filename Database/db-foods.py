import pandas as pd
import boto3
import json
from decimal import Decimal
import uuid

# Custom JSON encoder for Decimal objects
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Convert Decimal to string for JSON encoding
        return super(DecimalEncoder, self).default(obj)

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace with your actual region
table_name = 'ServiceTable'  # Replace with your actual table name
table = dynamodb.Table(table_name)

# Load the dataset from CSV
foods_file = 'foods.csv'  # Replace with the path to your foods dataset
df = pd.read_csv(foods_file)

# Function to convert any value to Decimal if it's a float or handle NaN/Infinity
def convert_to_decimal(value):
    if pd.isna(value):  # Check for NaN
        return None
    if isinstance(value, float):
        return Decimal(str(value))  # Convert float to Decimal
    return value

# Function to handle fields like Phone and Email, converting to string
def convert_to_string(value):
    if pd.isna(value):  # Handle NaN
        return None
    return str(value)  # Convert to string

# Function to insert food provider data into DynamoDB
def insert_food_data_to_dynamodb(df, table):
    for index, row in df.iterrows():
        # Skip rows where 'Provider' is NaN
        if pd.isna(row['Provider']):
            continue  # Skip this record

        # Create JSON fields for Description (all other fields except Name, Address, Lat, and Log)
        description_json = {
            "Borough": convert_to_string(row['Borough']),
            "Contact_Name": convert_to_string(row['Contact Name']),
            "Phone": convert_to_string(row['Phone']),
            "Email_Website": convert_to_string(row['Email/Website'])
        }

        # Define the item to insert into DynamoDB
        item = {
            'Id': str(uuid.uuid4()),  # Auto-generate a unique ID
            'Name': row['Provider'],  # Provider name
            'Address': row['Address'],  # Address
            'Lat': convert_to_decimal(row["Latitude"]),
            'Log': convert_to_decimal(row["longitude"]),
            'Ratings': "NoRatings",  # Default value for Ratings
            'Description': description_json  # JSON object with all other fields
        }

        # Insert the item into DynamoDB
        table.put_item(Item=item)

    # Final success message after all records are inserted
    print(f"Successfully inserted all food provider records into {table_name}.")

# Example usage
insert_food_data_to_dynamodb(df, table)
