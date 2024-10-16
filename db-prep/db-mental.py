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


def insert_mental_data_to_dynamodb(df, table, name):
    for index, row in df.iterrows():
        street_2 = row["street_2"] if pd.notna(row["street_2"]) else ""
        address = (
            f"{row['street_1']} {street_2.strip()} {row['city']} {row['zip']}".strip()
        )

        description_json = {
            "Branch": row["Branch"],
            "Phone": row["phone"],
            "Website": row["website"],
            "Filter_Military": row.get("filter_military"),
            "Filter_Inpatient_SVC": row.get("filter_inpatient_svc"),
            "Filter_Residential_PGM": row.get("filter_residential_pgm"),
        }

        description_json = {
            key: convert_to_decimal(value) for key, value in description_json.items()
        }

        item = {
            "Id": str(uuid.uuid4()),
            "Name": row["Organization"],
            "Address": address,
            "Lat": convert_to_decimal(row["latitude"]),
            "Log": convert_to_decimal(row["longitude"]),
            "Ratings": "NoRatings",
            "Description": description_json,
            "Category": "MENTAL",
        }

        table.put_item(Item=item)

    print(f"Successfully inserted all records into {name}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 db-mental.py /path/to/csv <dynamoDB table name>")
        exit(1)

    mental_file = sys.argv[1]
    dynamodb = boto3.resource(
        "dynamodb", region_name="us-east-1"
    )  # Replace with your actual region
    table_name = sys.argv[2]
    table = dynamodb.Table(table_name)

    df = pd.read_csv(mental_file)
    insert_mental_data_to_dynamodb(df, table, table_name)


if __name__ == "__main__":
    main()
