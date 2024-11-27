# home/repositories.py
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import decimal
import logging
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

        # search_query = search_query.lower() if search_query else None
        # Create filter based on search query and category
        if search_query and category_filter:
            filter_expression = And(
                Attr("Name").contains(
                    search_query
                ),  # Assuming data is stored in lowercase in "NormalizedName"
                Attr("Category").contains(
                    category_filter
                ),  # Assuming data is stored in lowercase in "NormalizedCategory"
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
            processed_item["Announcement"] = item.get("Announcement", "")
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
            updated_ratings = round(updated_ratings, 2)
            updated_rating_count = rating_count + 1

            updated_ratings = Decimal(updated_ratings).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

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

    def get_bookmarks_for_service(self, service_id):
        """Get all bookmarks for a specific service."""
        try:
            response = self.bookmarks_table.scan(
                FilterExpression=Attr("ServiceId").eq(service_id)
            )
            return response.get("Items", [])
        except ClientError as e:
            print(
                f"Failed to get bookmarks for service: {e.response['Error']['Message']}"
            )
            return []

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

    def get_bookmarks_for_services(self, service_ids):
        try:
            response = self.bookmarks_table.scan(
                FilterExpression=Attr("ServiceId").is_in(service_ids)
            )
            return response.get("Items", [])
        except ClientError as e:
            print(
                f"Failed to get bookmarks for services: {e.response['Error']['Message']}"
            )
            return []

    def get_reviews_for_services(self, service_ids):
        try:
            response = self.reviews_table.scan(
                FilterExpression=Attr("ServiceId").is_in(service_ids)
            )
            return response.get("Items", [])
        except ClientError as e:
            print(
                f"Failed to get reviews for services: {e.response['Error']['Message']}"
            )
            return []

    def compute_user_metrics(self, user_id):
        from services.repositories import ServiceRepository

        service_repo = ServiceRepository()
        total_ratings = Decimal("0")
        total_services_with_metrics = 0
        total_bookmarks = 0
        total_reviews = 0

        # Get services owned by the user
        services = service_repo.get_services_by_provider(user_id)
        service_ids = [service.id for service in services]

        # Get bookmarks and reviews for user's services
        bookmarks = self.get_bookmarks_for_services(service_ids)
        reviews = self.get_reviews_for_services(service_ids)

        # Build mappings
        bookmark_counts = {}
        for bookmark in bookmarks:
            service_id = bookmark["ServiceId"]
            bookmark_counts[service_id] = bookmark_counts.get(service_id, 0) + 1

        review_counts = {}
        for review in reviews:
            service_id = review["ServiceId"]
            review_counts[service_id] = review_counts.get(service_id, 0) + 1

        # Process each service
        for service in services:
            service_id = service.id
            rating_value = service.ratings

            # Convert rating to Decimal
            try:
                if rating_value is None or rating_value == "":
                    rating_decimal = Decimal("0")
                else:
                    rating_decimal = Decimal(str(rating_value))
            except decimal.InvalidOperation:
                logging.error(
                    f"Invalid rating value '{rating_value}' for service ID {service_id}"
                )
                rating_decimal = Decimal("0")

            num_bookmarks = bookmark_counts.get(service_id, 0)
            num_reviews = review_counts.get(service_id, 0)

            # Skip services with zero ratings, zero bookmarks, and zero reviews
            if rating_decimal == 0 and num_bookmarks == 0 and num_reviews == 0:
                continue

            # Include in totals
            total_ratings += rating_decimal
            total_services_with_metrics += 1
            total_bookmarks += num_bookmarks
            total_reviews += num_reviews

        # Calculate averages
        if total_services_with_metrics > 0:
            average_rating = total_ratings / total_services_with_metrics
        else:
            average_rating = Decimal("0")

        return {
            "average_rating": float(average_rating),
            "total_bookmarks": total_bookmarks,
            "total_reviews": total_reviews,
            "total_services": total_services_with_metrics,
        }

    def delete_review(self, review_id):
        try:
            # Retrieve the review item before deletion to get necessary details for rating update
            response = self.reviews_table.get_item(Key={"ReviewId": review_id})
            review = response.get("Item")

            if not review:
                raise ValueError("Review not found")

            # Delete the review from the table
            self.reviews_table.delete_item(Key={"ReviewId": review_id})

            return review  # Return the review details for further processing
        except ClientError as e:
            print(f"Failed to delete review: {e.response['Error']['Message']}")
            raise e

    def edit_review(self, review_id, new_rating, new_message):
        try:
            # Fetch the original review
            original_review = self.reviews_table.get_item(
                Key={"ReviewId": review_id}
            ).get("Item")

            if not original_review:
                raise ValueError("Review not found")

            # Update the review in the database
            self.reviews_table.update_item(
                Key={"ReviewId": review_id},
                UpdateExpression="SET RatingStars = :r, RatingMessage = :m",
                ExpressionAttributeValues={
                    ":r": new_rating,
                    ":m": new_message,
                },
            )
            return {
                "success": True,
                "message": "Review updated successfully.",
                "original_review": original_review,
            }

        except ClientError as e:
            print(f"Failed to edit review: {e.response['Error']['Message']}")
            raise e
        except ValueError as ve:
            return {"error": str(ve)}
