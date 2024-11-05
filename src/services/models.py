# from django.db import models

# Create your models here.
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Any
import uuid

from public_service_finder.utils.enums.service_status import ServiceStatus


@dataclass
class ServiceDTO:
    """Data Transfer Object for Service"""

    id: str
    name: str
    address: str
    latitude: Decimal
    longitude: Decimal
    ratings: Decimal
    description: Dict[str, Any]
    category: str
    provider_id: str
    service_status: str
    service_created_timestamp: str
    service_approved_timestamp: str

    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> "ServiceDTO":
        """Create ServiceDTO from DynamoDB item"""
        service_status = item.get("ServiceStatus", "PENDING_APPROVAL")
        if service_status.startswith("ServiceStatus."):
            service_status = service_status.split(".")[1]
        return cls(
            id=item["Id"],
            name=item["Name"],
            address=item["Address"],
            latitude=Decimal(str(item["Lat"])),
            longitude=Decimal(str(item["Log"])),
            ratings=item["Ratings"],
            description=item["Description"],
            category=item["Category"],
            provider_id=item["ProviderId"],
            service_status=ServiceStatus(service_status).value,
            service_created_timestamp=item.get("CreatedTimestamp", "NONE"),
            service_approved_timestamp=item.get("ApprovedTimestamp", "NONE"),
        )

    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format"""
        return {
            "Id": self.id or str(uuid.uuid4()),
            "Name": self.name,
            "Address": self.address,
            "Lat": self.latitude,
            "Log": self.longitude,
            "Ratings": self.ratings or Decimal("0"),
            "Description": self.description,
            "Category": self.category,
            "ProviderId": self.provider_id,
            "ServiceStatus": self.service_status,
            "CreatedTimestamp": self.service_created_timestamp,
            "ApprovedTimestamp": self.service_approved_timestamp,
        }

@dataclass
class ReviewDTO:
    """Data Transfer Object for Review"""
    review_id: str
    service_id: str
    user_id: str
    username: str
    rating_stars: int
    rating_message: str
    timestamp: str
    response: str = field(default="")
    responded_at: str = field(default="")

    @classmethod
    def from_dynamodb_item(cls, review_data: Dict[str, Any]) -> "ReviewDTO":
        """Create ReviewDTO from review data in DynamoDB item"""
        return cls(
            review_id=review_data["ReviewId"],
            service_id=review_data["ServiceId"],
            user_id=review_data["UserId"],
            username=review_data["Username"],
            rating_stars=int(review_data["RatingStars"]),
            rating_message=review_data["RatingMessage"],
            timestamp=review_data["Timestamp"],
            response=review_data.get("Response", "NULL"),
            responded_at=review_data.get("RespondedAt", "NULL")
        )

    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB review data format"""
        item = {
            "ReviewId": self.review_id or str(uuid.uuid4()),
            "ServiceId": self.service_id,
            "UserId": self.user_id,
            "Username": self.username,
            "RatingStars": str(self.rating_stars),
            "RatingMessage": self.rating_message,
            "Timestamp": self.timestamp
        }
        if self.response:
            item["Response"] = self.response
        if self.responded_at:
            item["RespondedAt"] = self.responded_at
        return item