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
shelter_file = 'shelters.csv'  # Replace with the path to your shelter dataset
df = pd.read_csv(shelter_file)

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

# Function to insert shelter data into DynamoDB
def insert_shelter_data_to_dynamodb(df, table):
    for index, row in df.iterrows():
        # Skip rows where 'Center Name' is NaN
        if pd.isna(row['Center Name']):
            continue  # Skip this record

        # Create JSON fields for Description (all other fields except Name, Address, Lat, and Log)
        description_json = {
            "Borough": row['Borough'],
            "Hours_of_Operation": row['Hours_of_Operation'],
            "Community_Board": row['Community Board'],
            "Council_District": row['Council District'],
            "Census_Tract": row['Census Tract']
        }

        # Convert all fields in the description to Decimal or handle NaN
        description_json = {key: convert_to_decimal(value) for key, value in description_json.items()}

        # Define the item to insert into DynamoDB
        item = {
            'Id': str(uuid.uuid4()),  # Auto-generate a unique ID
            'Name': row['Center Name'],  # Center name
            'Address': row['Address'],  # Address
            'Lat': convert_to_decimal(row['Latitude']),  # Convert latitude to Decimal or handle NaN
            'Log': convert_to_decimal(row['Longitude']),  # Convert longitude to Decimal or handle NaN
            'Ratings': "NoRatings",  # Default value for Ratings
            'Description': description_json  # JSON object with all other fields
        }

        # Insert the item into DynamoDB
        table.put_item(Item=item)

    # Final success message after all records are inserted
    print(f"Successfully inserted all shelter records into {table_name}.")

# Example usage
insert_shelter_data_to_dynamodb(df, table)
