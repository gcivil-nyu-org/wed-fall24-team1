from django.shortcuts import render
import boto3
from decimal import Decimal
from django.core.paginator import Paginator
import json

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace with your region
table_name = 'ServiceTable'  # Replace with your table name
table = dynamodb.Table(table_name)

# Custom JSON encoder to handle Decimal objects
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Convert Decimal to float for JSON encoding
        return super(DecimalEncoder, self).default(obj)

# Function to fetch data from DynamoDB and paginate it
def fetch_dynamodb_data(request):
    # Scan the DynamoDB table to get all items
    response = table.scan()
    items = response.get('Items', [])

    # Exclude the Description field from the items
    filtered_items = [
        {key: value for key, value in item.items() if key != 'Description'}
        for item in items
    ]

    # Paginate the items (10 items per page)
    paginator = Paginator(filtered_items, 10)  # Show 10 items per page

    page_number = request.GET.get('page', 1)  # Get the page number from the request (default to 1)
    page_obj = paginator.get_page(page_number)

    # Calculate the base index for the current page
    base_index = paginator.per_page * (page_obj.number - 1)

    # Render the template with the paginated data and base index
    return render(request, 'dynamodb_table.html', {'page_obj': page_obj, 'base_index': base_index})
