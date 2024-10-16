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


def insert_shelter_data_to_dynamodb(df, table, name):
    for index, row in df.iterrows():
        if pd.isna(row["Center Name"]):
            continue

        description_json = {
            "Borough": row["Borough"],
            "Hours_of_Operation": row["Hours_of_Operation"],
            "Community_Board": row["Community Board"],
            "Council_District": row["Council District"],
            "Census_Tract": row["Census Tract"],
        }

        description_json = {
            key: convert_to_decimal(value) for key, value in description_json.items()
        }

        item = {
            "Id": str(uuid.uuid4()),
            "Name": row["Center Name"],
            "Address": row["Address"],
            "Lat": convert_to_decimal(row["Latitude"]),
            "Log": convert_to_decimal(row["Longitude"]),
            "Ratings": "NoRatings",
            "Description": description_json,
            "Category": "SHELTER",
        }

        table.put_item(Item=item)

    print(f"Successfully inserted all records into {name}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 db-shelters.py /path/to/csv <dynamoDB table name>")
        exit(1)

    shelter_file = sys.argv[1]
    dynamodb = boto3.resource(
        "dynamodb", region_name="us-east-1"
    )  # Replace with your actual region
    table_name = sys.argv[2]
    table = dynamodb.Table(table_name)

    df = pd.read_csv(shelter_file)
    insert_shelter_data_to_dynamodb(df, table, table_name)


if __name__ == "__main__":
    main()
