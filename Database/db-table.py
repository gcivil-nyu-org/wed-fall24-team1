#!/usr/bin/env python3

import sys
import boto3


def create_service_table(dynamodb, table_name):
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'Id',  # Partition key
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'Id',  # The Id attribute, used as the partition key
                'AttributeType': 'S'  # 'S' is for string
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    
    # Wait for the table to be created
    table.meta.client.get_waiter('table_exists').wait(TableName='ServiceTable')
    print("Table has been created successfully.")
    return table


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python3 db-table.py <dynamoDB table name>")
        exit(1)
    table_name = sys.argv[1]
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    create_service_table(dynamodb, table_name)


if __name__ == "__main__":
    main()
