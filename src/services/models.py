# from django.db import models

# Create your models here.
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Any
import uuid


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

    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> "ServiceDTO":
        """Create ServiceDTO from DynamoDB item"""
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
        }
