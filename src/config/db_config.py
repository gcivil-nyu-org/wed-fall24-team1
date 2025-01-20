#!/usr/bin/env python3

from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from django.conf import settings

class MongoDBClient:
    _instance: Optional['MongoDBClient'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            # Get MongoDB connection details from Django settings
            mongodb_uri = settings.MONGODB_URI
            database_name = settings.MONGODB_NAME

            # Initialize MongoDB client
            self._client = MongoClient(mongodb_uri)
            self._db = self._client[database_name]

    @property
    def client(self):
        """Get the MongoDB client instance."""
        return self._client

    @property
    def db(self) -> Database:
        """Get the MongoDB database instance."""
        return self._db

    def get_collection(self, collection_name: str):
        """Get a specific collection from the database."""
        return self._db[collection_name]

    def close(self):
        """Close the MongoDB client connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

# Helper function to get a MongoDB collection
def get_collection(collection_name: str):
    """
    Helper function to get a MongoDB collection.

    Args:
        collection_name (str): Name of the collection to retrieve

    Returns:
        pymongo.collection.Collection: MongoDB collection object
    """
    return MongoDBClient().get_collection(collection_name)
