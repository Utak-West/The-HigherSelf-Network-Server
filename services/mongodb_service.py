"""
MongoDB Service for Higher Self Network Server.
Provides connection management and CRUD operations for MongoDB.
"""

import os
from typing import Any, Dict, List, Optional, Union
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from loguru import logger
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoDBService:
    """Service to interact with MongoDB."""
    
    _instance = None
    _async_client = None
    _sync_client = None
    _db = None
    _async_db = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance of the service exists."""
        if cls._instance is None:
            cls._instance = super(MongoDBService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize MongoDB connections."""
        try:
            mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/higherselfnetwork")
            
            # For synchronous operations
            self._sync_client = MongoClient(mongo_uri)
            db_name = mongo_uri.split('/')[-1]
            self._db = self._sync_client[db_name]
            
            # For async operations
            self._async_client = AsyncIOMotorClient(mongo_uri)
            self._async_db = self._async_client[db_name]
            
            # Test connection
            self._sync_client.admin.command('ping')
            logger.info(f"Connected to MongoDB at {mongo_uri}")
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @property
    def db(self) -> Any:
        """Get synchronous database connection."""
        return self._db
    
    @property
    def async_db(self) -> AsyncIOMotorDatabase:
        """Get asynchronous database connection."""
        return self._async_db
    
    def get_collection(self, collection_name: str) -> Any:
        """Get a MongoDB collection by name (synchronous)."""
        return self._db[collection_name]
        
    async def get_async_collection(self, collection_name: str) -> Any:
        """Get a MongoDB collection by name (asynchronous)."""
        return self._async_db[collection_name]
    
    # Synchronous CRUD operations
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a document into a collection and return its ID."""
        result = self.get_collection(collection_name).insert_one(document)
        return str(result.inserted_id)
    
    def find_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching the filter criteria."""
        return self.get_collection(collection_name).find_one(filter_dict)
    
    def find_many(self, collection_name: str, filter_dict: Dict[str, Any], 
                  limit: int = 0, skip: int = 0, sort_field: str = None) -> List[Dict[str, Any]]:
        """Find multiple documents matching the filter criteria."""
        cursor = self.get_collection(collection_name).find(filter_dict)
        
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        if sort_field:
            cursor = cursor.sort(sort_field)
            
        return list(cursor)
    
    def update_one(self, collection_name: str, filter_dict: Dict[str, Any], 
                   update_dict: Dict[str, Any], upsert: bool = False) -> int:
        """Update a single document and return the count of modified documents."""
        result = self.get_collection(collection_name).update_one(
            filter_dict, {"$set": update_dict}, upsert=upsert
        )
        return result.modified_count
    
    def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """Delete a single document and return the count of deleted documents."""
        result = self.get_collection(collection_name).delete_one(filter_dict)
        return result.deleted_count
    
    # Async CRUD operations
    async def async_insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a document into a collection asynchronously and return its ID."""
        collection = await self.get_async_collection(collection_name)
        result = await collection.insert_one(document)
        return str(result.inserted_id)
    
    async def async_find_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching the filter criteria asynchronously."""
        collection = await self.get_async_collection(collection_name)
        return await collection.find_one(filter_dict)
    
    async def async_find_many(self, collection_name: str, filter_dict: Dict[str, Any],
                             limit: int = 0, skip: int = 0, sort_field: str = None) -> List[Dict[str, Any]]:
        """Find multiple documents matching the filter criteria asynchronously."""
        collection = await self.get_async_collection(collection_name)
        cursor = collection.find(filter_dict)
        
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        if sort_field:
            cursor = cursor.sort(sort_field)
            
        result = []
        async for document in cursor:
            result.append(document)
        return result
    
    async def async_update_one(self, collection_name: str, filter_dict: Dict[str, Any],
                              update_dict: Dict[str, Any], upsert: bool = False) -> int:
        """Update a single document asynchronously and return the count of modified documents."""
        collection = await self.get_async_collection(collection_name)
        result = await collection.update_one(
            filter_dict, {"$set": update_dict}, upsert=upsert
        )
        return result.modified_count
    
    async def async_delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """Delete a single document asynchronously and return the count of deleted documents."""
        collection = await self.get_async_collection(collection_name)
        result = await collection.delete_one(filter_dict)
        return result.deleted_count

    def close(self):
        """Close MongoDB connections."""
        if self._sync_client:
            self._sync_client.close()
        if self._async_client:
            self._async_client.close()
        logger.info("MongoDB connections closed")

# For easy import and use throughout the application
mongo_service = MongoDBService()
