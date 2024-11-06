# home/repositories.py
from datetime import datetime
from decimal import Decimal
import boto3
from urllib.parse import quote
from boto3.dynamodb.conditions import Attr, And, Key, Or
from django.conf import settings
from botocore.exceptions import ClientError
from geopy import distance as dist


class HomeRepository:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.services_table = self.dynamodb.Table(settings.DYNAMODB_TABLE_SERVICES)
        self.reviews_table = self.dynamodb.Table(
            settings.DYNAMODB_TABLE_REVIEWS
        )  # Ensure this is set in settings
        self.bookmarks_table = self.dynamodb.Table(settings.DYNAMODB_TABLE_BOOKMARKS)

    def fetch_items_with_filter(
        self, search_query, category_filter, radius, ulat, ulon
    ):
        filter_expression = None

        # Create filter based on search query and category
        if search_query and category_filter:
            filter_expression = And(
                Attr("Name").contains(search_query),
                Attr("Category").contains(category_filter),
            )
        elif search_query:
            filter_expression = Attr("Name").contains(search_query)
        elif category_filter:
            filter_expression = Attr("Category").contains(category_filter)

        # Add ServiceStatus filter (if exists, it should be "APPROVED")
        service_status_filter = Or(
            Attr(
                "ServiceStatus"
            ).not_exists(),  # Include items where ServiceStatus does not exist
            Attr("ServiceStatus").eq(
                "APPROVED"
            ),  # Include items where ServiceStatus is "APPROVED"
        )

        # Combine the existing filter expression with the new ServiceStatus filter
        if filter_expression:
            filter_expression = And(filter_expression, service_status_filter)
        else:
            filter_expression = service_status_filter

        # Scan with the combined filter expression
        scan_kwargs = {}
        if filter_expression:
            scan_kwargs["FilterExpression"] = filter_expression

        response = self.services_table.scan(**scan_kwargs)
        items = response.get("Items", [])

        # Filter items based on radius if provided
        if radius and ulat and ulon:
            filtered_items = []
            for item in items:
                item_lat = item.get("Lat", "0")
                item_lon = item.get("Log", "0")
                if item_lat and item_lon and item_lat != "0" and item_lon != "0":
                    distance = dist.distance((item_lat, item_lon), (ulat, ulon)).miles
                    item["Distance"] = distance
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
                    "ResponseText": None,
                    "RespondedAt": None,
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
            current_ratings = float(item.get("Ratings", 0))
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
                    ":r": Decimal(updated_ratings),
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

    def add_bookmark(self, bookmark_id, user_id, service_id):
        try:
            timestamp = datetime.utcnow().isoformat()
            self.bookmarks_table.put_item(
                Item={
                    "BookmarkId": bookmark_id,
                    "UserId": user_id,
                    "ServiceId": service_id,
                    "timestamp": timestamp,
                }
            )
        except ClientError as e:
            print(f"Failed to add bookmark: {e.response['Error']['Message']}")
            raise e

    def remove_bookmark(self, user_id, service_id):
        try:
            response = self.bookmarks_table.query(
                IndexName="UserBookmarksIndex",
                KeyConditionExpression=Key("UserId").eq(user_id)
                & Key("ServiceId").eq(service_id),
            )
            items = response.get("Items", [])
            if items:
                bookmark_id = items[0]["BookmarkId"]
                self.bookmarks_table.delete_item(Key={"BookmarkId": bookmark_id})
        except ClientError as e:
            print(f"Failed to remove bookmark: {e.response['Error']['Message']}")
            raise e

    def is_bookmarked(self, user_id, service_id):
        try:
            response = self.bookmarks_table.query(
                IndexName="UserBookmarksIndex",
                KeyConditionExpression=Key("UserId").eq(user_id)
                & Key("ServiceId").eq(service_id),
            )
            items = response.get("Items", [])
            return len(items) > 0
        except ClientError as e:
            print(f"Failed to check bookmark: {e.response['Error']['Message']}")
            raise e

    def get_user_bookmarks(self, user_id):
        try:
            response = self.bookmarks_table.query(
                IndexName="UserBookmarksIndex",
                KeyConditionExpression=Key("UserId").eq(user_id),
            )
            bookmarks = response.get("Items", [])
            services = []
            for bookmark in bookmarks:
                service_id = bookmark["ServiceId"]
                service = self.services_table.get_item(Key={"Id": service_id}).get(
                    "Item"
                )
                if service:
                    services.append(service)
            return services
        except ClientError as e:
            print(f"Failed to get user bookmarks: {e.response['Error']['Message']}")
            raise e

    def fetch_reviews_by_user(self, user_id):
        try:
            # Since 'UserId' is not the primary key, we need to scan with a filter
            response = self.reviews_table.scan(
                FilterExpression=Attr("UserId").eq(user_id)
            )
            reviews = response.get("Items", [])
            # Sort reviews by Timestamp in descending order
            reviews.sort(key=lambda x: x["Timestamp"], reverse=True)
            return reviews
        except ClientError as e:
            print(f"Error fetching reviews: {e.response['Error']['Message']}")
            return []

    def get_services_by_ids(self, service_ids):
        try:
            services = []
            keys = [{"Id": service_id} for service_id in service_ids]
            # DynamoDB batch_get_item limit is 100 items per batch
            for i in range(0, len(keys), 100):
                batch_keys = keys[i : i + 100]
                response = self.dynamodb.batch_get_item(
                    RequestItems={self.services_table.name: {"Keys": batch_keys}}
                )
                services.extend(
                    response.get("Responses", {}).get(self.services_table.name, [])
                )
            service_map = {service["Id"]: service for service in services}
            return service_map
        except ClientError as e:
            print(f"Error fetching services: {e.response['Error']['Message']}")
            return {}
