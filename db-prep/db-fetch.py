import boto3
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Convert Decimal to float for JSON encoding
        return super(DecimalEncoder, self).default(obj)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace with your region
table_name = 'ServiceTable'  # Replace with your table name
table = dynamodb.Table(table_name)

def fetch_table_contents(table):
    response = table.scan()  # Scan the table to get all items
    items = response.get('Items', [])  # Get the 'Items' field from the response
    
    if items:
        for item in items:
            print(json.dumps(item, indent=4, cls=DecimalEncoder))  # Pretty print each item using DecimalEncoder
    else:
        print(f"No items found in the table {table_name}.")

fetch_table_contents(table)