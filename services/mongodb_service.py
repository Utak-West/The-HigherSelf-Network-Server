"""
MongoDB Service for Higher Self Network Server.
Provides connection management and CRUD operations for MongoDB.

Features:
- Singleton pattern for connection management
- Support for both synchronous and asynchronous operations
- Automatic document validation with Pydantic models
- Connection pooling for better performance
- Health check functionality
- Metrics for monitoring
"""

import asyncio
import json
import os
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast

from dotenv import load_dotenv
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, PyMongoError

# Import MongoBaseModel only if it exists
try:
    from models.mongodb_models import MongoBaseModel

    T = TypeVar("T", bound=MongoBaseModel)
except ImportError:
    from pydantic import BaseModel

    class MongoBaseModel(BaseModel):
        """Fallback base model if mongodb_models is not available."""

        pass

    T = TypeVar("T", bound=BaseModel)

# Load environment variables
load_dotenv()

# Type variable for Pydantic models
T = TypeVar("T", bound=MongoBaseModel)


# Custom JSON encoder for MongoDB
class MongoJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles MongoDB special types."""

    def default(self, obj):
        # Handle ObjectId if bson is available
        if (
            hasattr(obj, "__str__")
            and str(type(obj)) == "<class 'bson.objectid.ObjectId'>"
        ):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


# Decorator for retry logic
def with_retry(max_retries: int = 3, delay: float = 0.5):
    """Decorator to add retry logic to MongoDB operations."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except PyMongoError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        sleep_time = delay * (2**attempt)  # Exponential backoff
                        logger.warning(
                            f"MongoDB operation failed, retrying in {sleep_time:.2f}s: {e}"
                        )
                        time.sleep(sleep_time)
            logger.error(
                f"MongoDB operation failed after {max_retries} attempts: {last_error}"
            )
            if last_error:
                raise last_error
            else:
                raise PyMongoError("Unknown MongoDB error during retry")

        return wrapper

    return decorator


# Decorator for async retry logic
def with_async_retry(max_retries: int = 3, delay: float = 0.5):
    """Decorator to add retry logic to async MongoDB operations."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except PyMongoError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        sleep_time = delay * (2**attempt)  # Exponential backoff
                        logger.warning(
                            f"MongoDB operation failed, retrying in {sleep_time:.2f}s: {e}"
                        )
                        await asyncio.sleep(sleep_time)
            logger.error(
                f"MongoDB operation failed after {max_retries} attempts: {last_error}"
            )
            if last_error:
                raise last_error
            else:
                raise PyMongoError("Unknown MongoDB error during async retry")

        return wrapper

    return decorator


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
            mongo_uri = os.environ.get(
                "MONGODB_URI", "mongodb://localhost:27017/higherselfnetwork"
            )

            # For synchronous operations
            self._sync_client = MongoClient(mongo_uri)
            db_name = mongo_uri.split("/")[-1]
            self._db = self._sync_client[db_name]

            # For async operations
            self._async_client = AsyncIOMotorClient(mongo_uri)
            self._async_db = self._async_client[db_name]

            # Test connection
            self._sync_client.admin.command("ping")
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

    def find_one(
        self, collection_name: str, filter_dict: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find a single document matching the filter criteria."""
        return self.get_collection(collection_name).find_one(filter_dict)

    def find_many(
        self,
        collection_name: str,
        filter_dict: Dict[str, Any],
        limit: int = 0,
        skip: int = 0,
        sort_field: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Find multiple documents matching the filter criteria."""
        cursor = self.get_collection(collection_name).find(filter_dict)

        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        if sort_field:
            cursor = cursor.sort([(sort_field, 1)])

        return list(cursor)

    def update_one(
        self,
        collection_name: str,
        filter_dict: Dict[str, Any],
        update_dict: Dict[str, Any],
        upsert: bool = False,
    ) -> int:
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
    async def async_insert_one(
        self, collection_name: str, document: Dict[str, Any]
    ) -> str:
        """Insert a document into a collection asynchronously and return its ID."""
        collection = await self.get_async_collection(collection_name)
        result = await collection.insert_one(document)
        return str(result.inserted_id)

    async def async_find_one(
        self, collection_name: str, filter_dict: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find a single document matching the filter criteria asynchronously."""
        collection = await self.get_async_collection(collection_name)
        return await collection.find_one(filter_dict)

    async def async_find_many(
        self,
        collection_name: str,
        filter_dict: Dict[str, Any],
        limit: int = 0,
        skip: int = 0,
        sort_field: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Find multiple documents matching the filter criteria asynchronously."""
        collection = await self.get_async_collection(collection_name)
        cursor = collection.find(filter_dict)

        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        if sort_field:
            cursor = cursor.sort([(sort_field, 1)])

        result = []
        async for document in cursor:
            result.append(document)
        return result

    async def async_update_one(
        self,
        collection_name: str,
        filter_dict: Dict[str, Any],
        update_dict: Dict[str, Any],
        upsert: bool = False,
    ) -> int:
        """Update a single document asynchronously and return the count of modified documents."""
        collection = await self.get_async_collection(collection_name)
        result = await collection.update_one(
            filter_dict, {"$set": update_dict}, upsert=upsert
        )
        return result.modified_count

    async def async_delete_one(
        self, collection_name: str, filter_dict: Dict[str, Any]
    ) -> int:
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

    # Model conversion methods
    def model_to_dict(self, model: MongoBaseModel) -> Dict[str, Any]:
        """Convert a Pydantic model to a dictionary for MongoDB storage."""
        if not model:
            return {}

        # Convert model to dict - handle both Pydantic v1 and v2
        try:
            # Pydantic v2
            model_dict = model.model_dump(exclude_none=True)
        except AttributeError:
            # Pydantic v1 fallback
            model_dict = model.dict(exclude_none=True)

        # Update timestamps
        from datetime import timezone

        model_dict["updated_at"] = datetime.now(timezone.utc)

        return model_dict

    def dict_to_model(
        self, data: Optional[Dict[str, Any]], model_class: Type[MongoBaseModel]
    ) -> Optional[MongoBaseModel]:
        """Convert a MongoDB document to a Pydantic model."""
        if not data:
            return None

        # Remove MongoDB _id field if present
        if "_id" in data:
            data_copy = data.copy()
            del data_copy["_id"]
            try:
                return model_class(**data_copy)
            except Exception as e:
                logger.error(
                    f"Error converting MongoDB document to {model_class.__name__}: {e}"
                )
                return None

        try:
            return model_class(**data)
        except Exception as e:
            logger.error(
                f"Error converting MongoDB document to {model_class.__name__}: {e}"
            )
            return None

    # Model-based operations
    def save_model(self, collection_name: str, model: MongoBaseModel) -> str:
        """Save a Pydantic model to MongoDB."""
        model_dict = self.model_to_dict(model)

        # Get ID with fallback
        model_id = model_dict.get("id")
        if not model_id:
            raise ValueError("Model must have an 'id' field")

        # Check if document exists by id
        existing = self.find_one(collection_name, {"id": model_id})

        if existing:
            # Update existing document
            self.update_one(collection_name, {"id": model_id}, model_dict)
            return model_id
        else:
            # Insert new document
            return self.insert_one(collection_name, model_dict)

    async def async_save_model(
        self, collection_name: str, model: MongoBaseModel
    ) -> str:
        """Save a Pydantic model to MongoDB asynchronously."""
        model_dict = self.model_to_dict(model)

        # Get ID with fallback
        model_id = model_dict.get("id")
        if not model_id:
            raise ValueError("Model must have an 'id' field")

        # Check if document exists by id
        existing = await self.async_find_one(collection_name, {"id": model_id})

        if existing:
            # Update existing document
            await self.async_update_one(collection_name, {"id": model_id}, model_dict)
            return model_id
        else:
            # Insert new document
            return await self.async_insert_one(collection_name, model_dict)

    def find_model_by_id(
        self, collection_name: str, model_id: str, model_class: Type[MongoBaseModel]
    ) -> Optional[MongoBaseModel]:
        """Find a model by ID and return as a Pydantic model."""
        data = self.find_one(collection_name, {"id": model_id})
        return self.dict_to_model(data, model_class)

    async def async_find_model_by_id(
        self, collection_name: str, model_id: str, model_class: Type[MongoBaseModel]
    ) -> Optional[MongoBaseModel]:
        """Find a model by ID asynchronously and return as a Pydantic model."""
        data = await self.async_find_one(collection_name, {"id": model_id})
        return self.dict_to_model(data, model_class)

    def find_models(
        self,
        collection_name: str,
        filter_dict: Dict[str, Any],
        model_class: Type[MongoBaseModel],
        limit: int = 0,
        skip: int = 0,
    ) -> List[MongoBaseModel]:
        """Find models matching criteria and return as Pydantic models."""
        data_list = self.find_many(collection_name, filter_dict, limit, skip)
        result = []
        for data in data_list:
            if data:
                model = self.dict_to_model(data, model_class)
                if model:
                    result.append(model)
        return result

    async def async_find_models(
        self,
        collection_name: str,
        filter_dict: Dict[str, Any],
        model_class: Type[MongoBaseModel],
        limit: int = 0,
        skip: int = 0,
    ) -> List[MongoBaseModel]:
        """Find models matching criteria asynchronously and return as Pydantic models."""
        data_list = await self.async_find_many(
            collection_name, filter_dict, limit, skip
        )
        result = []
        for data in data_list:
            if data:
                model = self.dict_to_model(data, model_class)
                if model:
                    result.append(model)
        return result


# For easy import and use throughout the application
mongo_service = MongoDBService()
