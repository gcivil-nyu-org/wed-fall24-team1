#!/usr/bin/env python3

import sys
import boto3
from botocore.exceptions import ClientError

def create_reviews_table(dynamodb, table_name):
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    "AttributeName": "ReviewId",  # Primary key
                    "KeyType": "HASH"  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    "AttributeName": "ReviewId",
                    "AttributeType": "S"  # 'S' for string
                }
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        )

        # Wait until the table exists.
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"Table '{table_name}' has been created successfully.")
        return table

    except ClientError as e:
        print(f"Failed to create table: {e.response['Error']['Message']}")
        sys.exit(1)

def main():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace with your region
    create_reviews_table(dynamodb, "reviews")

if __name__ == "__main__":
    main()
