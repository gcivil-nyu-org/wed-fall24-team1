#!/usr/bin/env python3

import sys
import boto3


def get_first_100_items(dynamodb, table_name):
    table = dynamodb.Table(table_name)
    response = table.scan(Limit=100)  # Retrieve the first 100 items
    items = response.get("Items", [])

    # Print the items
    for item in items:
        print(item)

    print(f"Total items retrieved: {len(items)}")
    return items


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 extract_data.py <dynamoDB table name>")
        exit(1)
    table_name = sys.argv[1]
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    get_first_100_items(dynamodb, table_name)


if __name__ == "__main__":
    main()
