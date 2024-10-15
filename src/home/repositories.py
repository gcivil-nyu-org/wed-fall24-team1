import boto3
from urllib.parse import quote
from boto3.dynamodb.conditions import Attr
from django.conf import settings

class HomeRepository:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.table = self.dynamodb.Table(settings.DYNAMODB_TABLE_SERVICES)

    def fetch_items(self, category_filter):
        scan_kwargs = {}
        if category_filter:
            scan_kwargs["FilterExpression"] = Attr("Category").contains(category_filter)
        response = self.table.scan(**scan_kwargs)
        return response.get("Items", [])

    def process_items(self, items):
        processed_items = []
        for item in items:
            address = item.get("Address", "N/A")
            map_link = f"https://www.google.com/maps/dir/?api=1&destination={quote(address)}"
            processed_item = {key: value for key, value in item.items() if key != "Description"}
            processed_item["MapLink"] = map_link
            processed_items.append(processed_item)
        return processed_items
