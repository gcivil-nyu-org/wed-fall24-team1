import boto3

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace with your actual region


def create_service_table():
    table = dynamodb.create_table(
        TableName='ServiceTable',
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

create_service_table()