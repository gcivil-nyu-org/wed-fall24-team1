import pandas as pd
import boto3
import json
from decimal import Decimal
import uuid
import math

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
restroom_file = 'restrooms.csv'  # Replace with the path to your restroom dataset
df = pd.read_csv(restroom_file)

# Function to convert any value to Decimal if it's a float or handle NaN/Infinity
def convert_to_decimal(value):
    if pd.isna(value):  # Check for NaN
        return None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None  # Handle NaN and Infinity
        else:
            return Decimal(str(value))  # Convert float to Decimal
    return value

# Function to insert restroom data into DynamoDB
def insert_restroom_data_to_dynamodb(df, table):
    for index, row in df.iterrows():
        # Skip rows where 'Facility Name' is NaN
        if pd.isna(row['Facility Name']):
            continue  # Skip this record

        # Create JSON fields for Description (all other fields)
        description_json = {
            "Location_Type": row['Location Type'],
            "Operator": row['Operator'],
            "Open": row['Open'],
            "Hours_of_Operation": row['Hours of Operation'],
            "Accessibility": row['Accessibility'],
            "Restroom_Type": row['Restroom Type'],
            "Changing_Stations": row['Changing Stations'],
            "Additional_Notes": row['Additional Notes'],
            "Website": row['Website']
        }

        # Convert all fields in the description to Decimal or handle NaN
        description_json = {key: convert_to_decimal(value) for key, value in description_json.items()}

        # Define the item to insert into DynamoDB
        item = {
            'Id': str(uuid.uuid4()),  # Auto-generate a unique ID
            'Name': row['Facility Name'],  # Facility name
            'Address': "NA",  # Address is NA for now
            'Lat': convert_to_decimal(row['Latitude']),  # Convert latitude to Decimal or handle NaN
            'Log': convert_to_decimal(row['Longitude']),  # Convert longitude to Decimal or handle NaN
            'Ratings': "NoRatings",  # Default value for Ratings
            'Description': description_json  # JSON object with all other fields
        }

        # Insert the item into DynamoDB
        table.put_item(Item=item)

    # Final success message after all records are inserted
    print(f"Successfully inserted all records into {table_name}.")

# Example usage
insert_restroom_data_to_dynamodb(df, table)
