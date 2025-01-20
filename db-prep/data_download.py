#!/usr/bin/env python3

import sys
import boto3
import pandas as pd
from decimal import Decimal
import json
import argparse

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def flatten_dict(d, parent_key='', sep='_'):
    """
    Flatten a nested dictionary for CSV export.
    For example: {'a': {'b': 1}} becomes {'a_b': 1}
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def export_dynamodb_to_csv(table_name, output_file, region='us-east-1'):
    """
    Export DynamoDB table data to a CSV file.
    
    Args:
        table_name (str): Name of the DynamoDB table
        output_file (str): Name of the output CSV file
        region (str): AWS region name
    """
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name=region)
        table = dynamodb.Table(table_name)
        
        print(f"Scanning table {table_name}...")
        
        # Scan the table
        items = []
        scan_kwargs = {}
        done = False
        start_key = None
        
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = table.scan(**scan_kwargs)
            items.extend(response.get('Items', []))
            
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None
            
            print(f"Scanned {len(items)} items so far...")
        
        if not items:
            print("No items found in the table.")
            return
        
        print("Processing items...")
        
        # Flatten nested dictionaries and convert Decimal to float
        processed_items = []
        for item in items:
            # Convert Decimal to float and flatten nested structures
            flattened_item = flatten_dict(json.loads(
                json.dumps(item, cls=DecimalEncoder)
            ))
            processed_items.append(flattened_item)
        
        # Convert to DataFrame and export to CSV
        df = pd.DataFrame(processed_items)
        df.to_csv(output_file, index=False)
        print(f"Successfully exported {len(items)} items to {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Export DynamoDB table to CSV')
    parser.add_argument('table_name', help='Name of the DynamoDB table')
    parser.add_argument('output_file', help='Name of the output CSV file')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    
    args = parser.parse_args()
    
    export_dynamodb_to_csv(args.table_name, args.output_file, args.region)

if __name__ == "__main__":
    main()
