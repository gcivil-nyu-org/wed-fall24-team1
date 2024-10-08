#!/usr/bin/env python3
import sys
import pandas as pd
import boto3
import json
from decimal import Decimal
import uuid
import math


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Convert Decimal to string for JSON encoding
        return super(DecimalEncoder, self).default(obj)


def convert_to_decimal(value):
    if pd.isna(value):  # Check for NaN
        return None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None  # Handle NaN and Infinity
        else:
            return Decimal(str(value))  # Convert float to Decimal
    return value


def insert_restroom_data_to_dynamodb(df, table, name):
    for index, row in df.iterrows():
        if pd.isna(row['Facility Name']) or pd.isna(row["Address"]) or (
                pd.isna(row["Latitude"]) and pd.isna(row["Longitude"])):
            continue

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

        description_json = {key: convert_to_decimal(value) for key, value in description_json.items()}

        item = {
            'Id': str(uuid.uuid4()),  # Auto-generate a unique ID
            'Name': row['Facility Name'],  # Facility name
            'Address': row["Address"],
            'Lat': convert_to_decimal(row['Latitude']),  # Convert latitude to Decimal or handle NaN
            'Log': convert_to_decimal(row['Longitude']),  # Convert longitude to Decimal or handle NaN
            'Ratings': "NoRatings",  # Default value for Ratings
            'Description': description_json,  # JSON object with all other fields
            'Category': 'RESTROOM'
        }

        # Insert the item into DynamoDB
        table.put_item(Item=item)

    print(f"Successfully inserted all records into {name}")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: python3 db-restrooms.py /path/to/csv <dynamoDB table name>")
        exit(1)

    restroom_file = sys.argv[1]
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace with your actual region
    table_name = sys.argv[2]  # Replace with your actual table name
    table = dynamodb.Table(table_name)

    # Load the dataset from CSV
    df = pd.read_csv(restroom_file)
    insert_restroom_data_to_dynamodb(df, table, table_name)


if __name__ == "__main__":
    main()
