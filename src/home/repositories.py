# home/repositories.py
from datetime import datetime
from decimal import Decimal
import boto3
from urllib.parse import quote
from boto3.dynamodb.conditions import Attr, And, Key
from django.conf import settings
from botocore.exceptions import ClientError
from . import utils


class HomeRepository:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.services_table = self.dynamodb.Table(settings.DYNAMODB_TABLE_SERVICES)
        self.reviews_table = self.dynamodb.Table(
            settings.DYNAMODB_TABLE_REVIEWS
        )  # Ensure this is set in settings

    def fetch_items_with_filter(
        self, search_query, category_filter, radius, ulat, ulon
    ):
        filter_expression = None

        if search_query and category_filter:
            filter_expression = And(
                Attr("Name").contains(search_query),
                Attr("Category").contains(category_filter),
            )
        elif search_query:
            filter_expression = Attr("Name").contains(search_query)
        elif category_filter:
            filter_expression = Attr("Category").contains(category_filter)

        scan_kwargs = {}
        if filter_expression:
            scan_kwargs["FilterExpression"] = filter_expression

        response = self.services_table.scan(**scan_kwargs)
        items = response.get("Items", [])

        if radius and ulat and ulon:
            filtered_items = []
            for item in items:
                item_lat = item.get("Lat", "0")
                item_lon = item.get("Log", "0")
                if item_lat and item_lon:
                    distance = utils.calculate_distance(
                        float(ulat), float(ulon), float(item_lat), float(item_lon)
                    )
                    if distance <= float(radius):
                        filtered_items.append(item)

            return filtered_items

        return items

    @staticmethod
    def process_items(items):
        processed_items = []
        for item in items:
            address = item.get("Address", "N/A")
            map_link = (
                f"https://www.google.com/maps/dir/?api=1&destination={quote(address)}"
            )
            processed_item = {
                key: value for key, value in item.items() if key != "Description"
            }
            processed_item["Description"] = item.get("Description", {})
            processed_item["MapLink"] = map_link
            processed_items.append(processed_item)
        return processed_items

    def add_review(
        self, review_id, service_id, user_id, rating_stars, rating_message, username
    ):
        try:
            # Generate current timestamp in ISO 8601 format
            timestamp = datetime.utcnow().isoformat()

            self.reviews_table.put_item(
                Item={
                    "ReviewId": review_id,
                    "ServiceId": service_id,
                    "UserId": user_id,
                    "Username": username,  # Optional: to display the user's name
                    "RatingStars": rating_stars,
                    "RatingMessage": rating_message,
                    "Timestamp": timestamp,  # New timestamp field
                }
            )
        except ClientError as e:
            print(f"Failed to add review: {e.response['Error']['Message']}")
            raise e

    def update_service_rating(self, service_id, new_rating):
        try:
            # Retrieve the current ratings and rating count
            response = self.services_table.get_item(
                Key={"Id": service_id}, ProjectionExpression="Ratings, rating_count"
            )
            item = response.get("Item", {})
            current_ratings = Decimal(item.get("Ratings", 0))
            rating_count = int(item.get("rating_count", 0))

            # Calculate the new ratings
            updated_ratings = (current_ratings * rating_count + new_rating) / (
                rating_count + 1
            )
            updated_rating_count = rating_count + 1

            # Update the table
            self.services_table.update_item(
                Key={"Id": service_id},
                UpdateExpression="SET Ratings = :r, rating_count = :c",
                ExpressionAttributeValues={
                    ":r": updated_ratings,
                    ":c": updated_rating_count,
                },
            )
        except ClientError as e:
            print(f"Failed to update service rating: {e.response['Error']['Message']}")
            raise e

    def fetch_reviews_for_service(self, service_id):
        try:
            # Query to get all reviews with matching ServiceId
            response = self.reviews_table.scan(
                FilterExpression=Key("ServiceId").eq(service_id)
            )
            reviews = response.get("Items", [])

            # Sort reviews by Timestamp in descending order (latest first)
            reviews.sort(key=lambda x: x["Timestamp"], reverse=True)

            return reviews
        except ClientError as e:
            print(f"Error fetching reviews: {e.response['Error']['Message']}")
            return []
