import logging
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from django.conf import settings
from django.utils import timezone
from boto3.dynamodb.conditions import Key
from typing import List

from services.models import ReviewDTO, ServiceDTO


log = logging.getLogger(__name__)


class ServiceRepository:
    def __init__(self):
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=settings.AWS_REGION,
        )
        self.table = self.dynamodb.Table(settings.DYNAMODB_TABLE_SERVICES)

    def create_service(self, service_dto: ServiceDTO):
        try:
            item = service_dto.to_dynamodb_item()
            self.table.put_item(Item=item)
            log.info(f"Persisted service: {item} to DynamoDB")
            return service_dto
        except ClientError as e:
            log.error(f"Error creating service: {e.responseText['Error']['Message']}")
            return None

    def get_services_by_provider(self, provider_id: int) -> list[ServiceDTO]:
        try:
            response = self.table.scan(
                FilterExpression="ProviderId = :pid",
                ExpressionAttributeValues={":pid": str(provider_id)},
            )
            services = [
                ServiceDTO.from_dynamodb_item(item)
                for item in response.get("Items", [])
            ]
            log.debug(f"Fetched {len(services)} services for provider {provider_id}")
            return services
        except ClientError as e:
            log.error(f"Error fetching services: {e.responseText['Error']['Message']}")
            return []

    def get_service(self, service_id: str) -> ServiceDTO | None:
        try:
            response = self.table.get_item(Key={"Id": service_id})
            item = response.get("Item")
            if item:
                log.debug(f"Fetched service {service_id}")
            return ServiceDTO.from_dynamodb_item(item) if item else None
        except ClientError as e:
            log.error(
                f"Error fetching service {service_id}: {e.responseText['Error']['Message']}"
            )
            return None

    def get_pending_approval_or_editRequested_services(self) -> list[ServiceDTO]:
        try:
            filter_expression = Attr("ServiceStatus").eq("PENDING_APPROVAL") | Attr("ServiceStatus").eq("EDIT_REQUESTED")
            response = self.table.scan(
                FilterExpression=filter_expression
            )
            return [
                ServiceDTO.from_dynamodb_item(item)
                for item in response.get("Items", [])
            ]
        except ClientError as e:
            log.error(
                f"Error fetching pending approval services: {e.response['Error']['Message']}"
            )
            return []



    def save_pending_update(self, service_id: str, pending_update_data: dict) -> bool:
        try:
            # Update the DynamoDB item to add a "pending_update" attribute
            response = self.table.update_item(
                Key={"Id": service_id},
                UpdateExpression="SET pending_update = :pending_update",
                ExpressionAttributeValues={":pending_update": pending_update_data},
            )
            return response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except ClientError as e:
            print(e.response["Error"]["Message"])
            return False

    def update_service(self, service_dto: ServiceDTO) -> ServiceDTO | None:
        try:
            item = service_dto.to_dynamodb_item()
            response = self.table.put_item(Item=item)
            return service_dto if response else None
        except ClientError as e:
            print(e.response["Error"]["Message"])
            return None

    def delete_service(self, service_id: str) -> bool:
        try:
            self.table.delete_item(Key={"Id": service_id})
            return True
        except ClientError as e:
            print(e.response["Error"]["Message"])
            return False

    def update_service_status(self, service_id: str, new_status: str) -> bool:
        try:
            # Update service status
            service_id_str = str(service_id)
            response = self.table.update_item(
                Key={"Id": service_id_str},
                UpdateExpression="SET ServiceStatus = :new_status",
                ExpressionAttributeValues={":new_status": new_status},
                ConditionExpression="attribute_exists(Id)",  # Ensure item exists
                ReturnValues="UPDATED_NEW",
            )
            print("response: " + response)

            # Logging successful update
            log.info(
                f"Updated ServiceStatus for service ID {service_id} to {new_status}"
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                log.error(f"Service ID {service_id} does not exist.")
            else:
                log.error(
                    f"Error updating service status for ID {service_id}: {e.response['Error']['Message']}"
                )

            return False

        except Exception as e:
            log.error(
                f"Unexpected error updating service status for ID {service_id}, exception: {e}"
            )
            return False


class ReviewRepository:
    def __init__(self):
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=settings.AWS_REGION,
        )
        self.table = self.dynamodb.Table(settings.DYNAMODB_TABLE_REVIEWS)

    def get_review(self, review_id: str) -> ReviewDTO | None:
        """Retrieve a single review by its ID."""
        try:
            response = self.table.get_item(Key={"ReviewId": review_id})
            item = response.get("Item")
            return ReviewDTO.from_dynamodb_item(item) if item else None
        except ClientError as e:
            log.error(
                f"Error fetching review {review_id}: {e.responseText['Error']['Message']}"
            )
            return None

    def respond_to_review(self, review_id: str, response_text: str) -> bool:
        """Update a review's responseText field."""
        try:
            current_time = timezone.now().isoformat()
            log.debug(
                "Updating DynamoDB with responseText: %s, respondedAt: %s",
                response_text,
                current_time,
            )
            self.table.update_item(
                Key={"ReviewId": review_id},
                UpdateExpression="SET #response_text = :responseText, RespondedAt = :responded_at",
                ExpressionAttributeNames={
                    "#response_text": "ResponseText"
                },  # Alias for reserved keyword
                ExpressionAttributeValues={
                    ":responseText": response_text,
                    ":responded_at": current_time,
                },
            )
            log.info(f"Updated review {review_id} with response")
            return True
        except ClientError as e:
            log.error(
                f"Error responding to review {review_id}: {e.response['Error']['Message']}"
            )
            return False

    def get_reviews_for_service(self, service_id: str) -> List[ReviewDTO]:
        """Retrieve all reviews for a given service ID."""
        try:
            response = self.table.query(
                IndexName="ServiceIdIndex",  # Ensure this index exists in your DynamoDB table
                KeyConditionExpression=Key("ServiceId").eq(service_id),
            )
            items = response.get("Items", [])
            return [ReviewDTO.from_dynamodb_item(item) for item in items]
        except ClientError as e:
            log.error(
                f"Error fetching reviews for service {service_id}: {e.response['Error']['Message']}"
            )
            return []
