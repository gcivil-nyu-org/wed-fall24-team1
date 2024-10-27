# services/repositories.py
import logging

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

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
