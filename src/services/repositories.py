#!/usr/bin/env python3

import logging
from typing import Optional
from bson import ObjectId
from django.conf import settings
from pymongo.collection import Collection
from config.db_config import get_collection
from services.models import ServiceDTO
from datetime import datetime

log = logging.getLogger(__name__)

class ServiceRepository:
    def __init__(self):
        """Initialize ServiceRepository with MongoDB collection."""
        self.collection: Collection = get_collection(settings.MONGODB_COLLECTIONS['SERVICES'])

    def create_service(self, service_dto: ServiceDTO) -> Optional[ServiceDTO]:
        """Create a new service in MongoDB."""
        try:
            # Convert DTO to document format
            service_doc = service_dto.to_dynamodb_item()  # We'll keep the method name for now

            # MongoDB will create its own _id, so we'll use the Id field as a custom identifier
            if 'Id' not in service_doc:
                service_doc['Id'] = str(ObjectId())

            # Insert the document
            result = self.collection.insert_one(service_doc)

            if result.inserted_id:
                # Retrieve the inserted document to return
                inserted_doc = self.collection.find_one({'_id': result.inserted_id})
                return ServiceDTO.from_dynamodb_item(inserted_doc) if inserted_doc else None

            return None

        except Exception as e:
            log.error(f"Error creating service: {str(e)}")
            return None

    def get_services_by_provider(self, provider_id: int) -> list[ServiceDTO]:
        """Retrieve all services for a specific provider."""
        try:
            # Convert provider_id to string to match stored format
            provider_id_str = str(provider_id)

            # Query MongoDB for services
            cursor = self.collection.find({'ProviderId': provider_id_str})

            # Convert documents to DTOs
            services = [ServiceDTO.from_dynamodb_item(doc) for doc in cursor]

            log.debug(f"Fetched {len(services)} services for provider {provider_id}")
            return services

        except Exception as e:
            log.error(f"Error fetching services: {str(e)}")
            return []

    def get_service(self, service_id: str) -> Optional[ServiceDTO]:
        """Retrieve a specific service by ID."""
        try:
            # Query MongoDB for the service
            service_doc = self.collection.find_one({'Id': service_id})

            if service_doc:
                return ServiceDTO.from_dynamodb_item(service_doc)
            return None

        except Exception as e:
            log.error(f"Error fetching service {service_id}: {str(e)}")
            return None

    def get_pending_approval_services(self) -> list[ServiceDTO]:
        """Retrieve all services pending approval."""
        try:
            # Query MongoDB for pending services
            cursor = self.collection.find({'ServiceStatus': 'PENDING_APPROVAL'})

            # Convert documents to DTOs
            return [ServiceDTO.from_dynamodb_item(doc) for doc in cursor]

        except Exception as e:
            log.error(f"Error fetching pending approval services: {str(e)}")
            return []

    def update_service(self, service_dto: ServiceDTO) -> Optional[ServiceDTO]:
        """Update an existing service."""
        try:
            # Convert DTO to document format
            service_doc = service_dto.to_dynamodb_item()

            # Update the document in MongoDB
            result = self.collection.replace_one(
                {'Id': service_doc['Id']},
                service_doc
            )

            if result.modified_count > 0:
                # Retrieve and return the updated document
                updated_doc = self.collection.find_one({'Id': service_doc['Id']})
                return ServiceDTO.from_dynamodb_item(updated_doc) if updated_doc else None

            return None

        except Exception as e:
            log.error(f"Error updating service: {str(e)}")
            return None

    def delete_service(self, service_id: str) -> bool:
        """Delete a service by ID."""
        try:
            result = self.collection.delete_one({'Id': service_id})
            return result.deleted_count > 0

        except Exception as e:
            log.error(f"Error deleting service {service_id}: {str(e)}")
            return False

    def update_service_status(self, service_id: str, new_status: str) -> bool:
        """Update the status of a service."""
        try:
            service_id_str = str(service_id)

            # Update the service status in MongoDB
            result = self.collection.update_one(
                {'Id': service_id_str},
                {'$set': {
                    'ServiceStatus': new_status,
                    'StatusUpdatedAt': datetime.utcnow().isoformat()
                }}
            )

            success = result.modified_count > 0
            if success:
                log.info(f"Updated ServiceStatus for service ID {service_id} to {new_status}")
            else:
                log.error(f"Service ID {service_id} not found or status not updated")

            return success

        except Exception as e:
            log.error(f"Error updating service status for ID {service_id}: {str(e)}")
            return False
