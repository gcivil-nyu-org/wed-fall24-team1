from urllib.parse import quote

from django.shortcuts import render
import boto3
from django.core.paginator import Paginator
import json
from django.conf import settings


def get_services_table():
    """
    Helper function to initialize and return the DynamoDB table object.
    """
    dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
    return dynamodb.Table(settings.DYNAMODB_TABLE_SERVICES)


# Function to fetch data from DynamoDB and paginate it
def home_view(request):
    # Get search query from request
    search_query = request.GET.get("search", "")

    # Prepare scan parameters
    scan_kwargs = {}
    if search_query:
        from boto3.dynamodb.conditions import Attr

        scan_kwargs["FilterExpression"] = Attr("Name").contains(search_query)

    table = get_services_table()
    # Scan the DynamoDB table to get items
    response = table.scan(**scan_kwargs)

    items = response.get("Items", [])

    # Exclude the Description field from the items

    processed_items = []
    for item in items:
        address = item.get("Address", "N/A")
        map_link = (
            f"https://www.google.com/maps/dir/?api=1&destination={quote(address)}"
        )
        processed_item = {
            key: value for key, value in item.items() if key != "Description"
        }
        processed_item["MapLink"] = map_link
        processed_items.append(processed_item)

    # Paginate the items (10 items per page)
    paginator = Paginator(processed_items, 10)  # Show 10 items per page

    page_number = request.GET.get(
        "page", 1
    )  # Get the page number from the request (default to 1)
    page_obj = paginator.get_page(page_number)

    # Calculate the base index for the current page
    base_index = paginator.per_page * (page_obj.number - 1)

    # Serialize current page's items to JSON for the map
    serialized_items = [
        {
            "Name": item.get("Name", "No Name"),
            "Address": item.get("Address", "N/A"),
            "Lat": float(item.get("Lat")) if item.get("Lat") else None,
            "Log": float(item.get("Log")) if item.get("Log") else None,
            "Ratings": (
                str(item.get("Ratings")) if item.get("Ratings") else "No ratings"
            ),
            "Category": str(item.get("Category")),
            "MapLink": item.get("MapLink", "#"),
        }
        for item in page_obj
    ]

    return render(
        request,
        "home.html",
        {
            "page_obj": page_obj,
            "base_index": base_index,
            "search_query": search_query,
            "serialized_items": json.dumps(serialized_items),  # Pass serialized data
        },
    )
