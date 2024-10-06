import pandas as pd
import boto3
import json
from decimal import Decimal
import math
import uuid  # Import uuid to generate unique IDs

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
excel_file = 'mental.csv'  # Replace with the path to your file
df = pd.read_csv(excel_file)

# Function to convert any float values in the DataFrame to Decimal and handle NaN/Infinity
def convert_values_to_compatible(data):
    for key, value in data.items():
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                data[key] = None  # Replace NaN or Infinity with None
            else:
                data[key] = Decimal(str(value))  # Convert float to Decimal
    return data

# Function to insert data into DynamoDB
def insert_service_data_to_dynamodb(df, table):
    for index, row in df.iterrows():
        # Handle street_2 properly by checking if it's not NaN
        street_2 = row['street_2'] if pd.notna(row['street_2']) else ""
        
        # Construct the Address by combining street_1, street_2, city, and zip
        address = f"{row['street_1']} {street_2.strip()} {row['city']} {row['zip']}".strip()
        
        # Create JSON fields for Description (Branch, Phone, Website, and filter columns)
        description_json = {
            "Branch": row['Branch'],
            "Phone": row['phone'],
            "Website": row['website'],
            "Filter_Military": row.get('filter_military'),
            "Filter_Inpatient_SVC": row.get('filter_inpatient_svc'),
            "Filter_Residential_PGM": row.get('filter_residential_pgm')
        }

        # Define the item to insert into DynamoDB
        item = {
            'Id': str(uuid.uuid4()),  # Auto-generate a unique ID
            'Name': row['Organization'],  # Service name
            'Address': address,  # Combined address
            'Lat': Decimal(str(row['latitude'])) if pd.notna(row['latitude']) else None,  # Handle NaN
            'Log': Decimal(str(row['longitude'])) if pd.notna(row['longitude']) else None,  # Handle NaN
            'Ratings': "NoRatings",  # Default value for Ratings
            'Description': convert_values_to_compatible(description_json)  # Convert floats in description to Decimal
        }

        # Insert the item into DynamoDB
        table.put_item(Item=item)

    print(f"Data successfully inserted into {table_name}.")

# Example usage
insert_service_data_to_dynamodb(df, table)
