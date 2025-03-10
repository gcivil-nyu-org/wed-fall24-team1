#!/usr/bin/env python3
import boto3
from datetime import datetime

def update_reviews(table_name):
    # Connect to DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table(table_name)

    # Scan the table for all items
    response = table.scan()
    items = response.get("Items", [])

    # Handle pagination if necessary
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    for item in items:
        # Retrieve the ResponseText attribute
        response_text = item.get("ResponseText")
        
        # Only update if ResponseText is None (i.e., null in DynamoDB). If it's an empty string, do nothing.
        if response_text is None or response_text == "null":
            today_date = datetime.now().isoformat()  # You can customize the date format as needed.
            table.update_item(
                Key={"ReviewId": item["ReviewId"]},  # Adjust this if your primary key is different
                UpdateExpression="SET ResponseText = :text, RespondedAt = :date",
                ExpressionAttributeValues={
                    ":text": "Thank you for your review",
                    ":date": today_date
                }
            )
            print(f"Updated item with Id {item['ReviewId']}")
        else:
            print(f"Skipping item with Id {item['ReviewId']} (ResponseText is not null).")

def main():
    table_name = "reviewTable"  # Replace with your table name if different
    update_reviews(table_name)

if __name__ == "__main__":
    main()
