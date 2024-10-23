#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError


def update_table_items(table):
    try:
        # Scan the entire table to retrieve all items
        response = table.scan()
        items = response.get("Items", [])

        print(f"Found {len(items)} items. Updating...")

        # Loop through each item and update the 'Ratings' and 'RatingCount'
        for item in items:
            item_id = item["Id"]  # Assuming 'Id' is the partition key

            print(f"Updating item with Id: {item_id}")

            # Update the item: set 'Ratings' to 0 and add 'RatingCount' as 0
            table.update_item(
                Key={"Id": item_id},
                UpdateExpression="SET Ratings = :r, rating_count = :c",
                ExpressionAttributeValues={
                    ":r": 0,  # Set Ratings to 0
                    ":c": 0,  # Add RatingCount and set to 0
                },
            )

        print("Successfully updated all items.")

    except ClientError as e:
        print(f"Error updating items: {e.response['Error']['Message']}")


def main():
    # Replace with your actual region and table name
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("services")

    update_table_items(table)


if __name__ == "__main__":
    main()
