import logging
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from django.conf import settings
from django.utils import timezone

from .models import ServiceDTO, ReviewDTO
from .models import ServiceDTO

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
            log.info(f"Persisted item: {item} to dynamoDB")
            return service_dto
        except ClientError as e:
            print(e.response["Error"]["Message"])
            return None

    def get_services_by_provider(self, provider_id: str) -> list[ServiceDTO]:
        try:
            response = self.table.scan(
                FilterExpression="ProviderId = :pid",
                ExpressionAttributeValues={":pid": str(provider_id)},
            )
            return [
                ServiceDTO.from_dynamodb_item(item)
                for item in response.get("Items", [])
            ]
        except ClientError as e:
            print(e.response["Error"]["Message"])
            return []

    def get_service(self, service_id: str) -> ServiceDTO | None:
        try:
            response = self.table.get_item(Key={"Id": service_id})
            item = response.get("Item")
            return ServiceDTO.from_dynamodb_item(item) if item else None
        except ClientError as e:
            print(e.response["Error"]["Message"])
            return None

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

    def get_pending_approval_services(self) -> list[ServiceDTO]:
        try:
            response = self.table.scan(
                FilterExpression=Attr("ServiceStatus").eq("PENDING_APPROVAL")
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
        self.table = self.dynamodb.Table(settings.DYNAMODB_TABLE_SERVICES)

    def get_reviews_for_service(self, service_id: str) -> list:
        """Retrieve all reviews for a specific service."""
        try:
            response = self.table.scan(
                FilterExpression="ServiceId = :sid",
                ExpressionAttributeValues={":sid": service_id},
            )
            return [
                ReviewDTO.from_dynamodb_item(item)
                for item in response.get("Items", [])
            ]
        except Exception as e:
            print(f"Error retrieving reviews: {e}")
            return []

    def respond_to_review(self, service_id: str, review_id: str, response_text: str) -> bool:
        """Add a response to a specific review."""
        try:
            current_time = timezone.now().isoformat()

            # First get the service to find the review in the reviews array
            response = self.table.get_item(Key={"Id": service_id})
            service_item = response.get("Item", {})
            reviews = service_item.get("reviews", [])

            # Find and update the specific review
            updated = False
            for review in reviews:
                if review["ReviewId"] == review_id:
                    review["Response"] = response_text
                    review["RespondedAt"] = current_time
                    updated = True
                    break

            if not updated:
                log.error(f"Review {review_id} not found in service {service_id}")
                return False

            # Update the entire service item with the modified reviews
            self.table.update_item(
                Key={"Id": service_id},
                UpdateExpression="SET reviews = :reviews",
                ExpressionAttributeValues={
                    ":reviews": reviews
                }
            )

            log.info(f"Updated review {review_id} with response")
            return True
        except ClientError as e:
            log.error(f"Error responding to review {review_id}: {e.response['Error']['Message']}")
            return False
