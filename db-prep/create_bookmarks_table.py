#!/usr/bin/env python3

import sys
import boto3

def create_bookmarks_table(dynamodb, table_name):
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'BookmarkId', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'BookmarkId', 'AttributeType': 'S'},
            {'AttributeName': 'UserId', 'AttributeType': 'S'},
            {'AttributeName': 'ServiceId', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'UserBookmarksIndex',
                'KeySchema': [
                    {'AttributeName': 'UserId', 'KeyType': 'HASH'},
                    {'AttributeName': 'ServiceId', 'KeyType': 'RANGE'}
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # Wait for the table to be created
    table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
    print("Bookmarks table has been created successfully.")
    return table

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 create_bookmarks_table.py <dynamoDB table name>")
        exit(1)
    table_name = sys.argv[1]
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    create_bookmarks_table(dynamodb, table_name)

if __name__ == "__main__":
    main()
