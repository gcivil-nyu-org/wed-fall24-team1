import boto3
from urllib.parse import quote
from boto3.dynamodb.conditions import Attr, And
from django.conf import settings


class HomeRepository:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.table = self.dynamodb.Table(settings.DYNAMODB_TABLE_SERVICES)

    def fetch_items_with_filter(self, search_query, category_filter):
        filter_expression = None

        if search_query and category_filter:
            filter_expression = And(
                Attr("Name").contains(search_query),
                Attr("Category").contains(category_filter)
            )
        elif search_query:
            filter_expression = Attr("Name").contains(search_query)
        elif category_filter:
            filter_expression = Attr("Category").contains(category_filter)

        scan_kwargs = {}
        if filter_expression:
            scan_kwargs["FilterExpression"] = filter_expression

        response = self.table.scan(**scan_kwargs)
        return response.get("Items", [])

    def process_items(self, items):
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
        return processed_items
