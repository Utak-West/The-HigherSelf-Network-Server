"""
Dataset Repository for The HigherSelf Network Server.

This module provides repository classes for dataset-related MongoDB collections,
abstracting the data access layer and providing a clean interface for CRUD operations.
"""

from datetime import datetime
from typing import Dict, List, Optional, Type, Any, Generic, TypeVar

from loguru import logger

from models.dataset_models import (
    DatasetMetadata, DatasetVersion, ProcessedDataset, 
    DatasetTrainingConfig, DatasetTrainingResult
)
from services.mongodb_service import mongo_service
from repositories.mongodb_repository import MongoRepository


class DatasetMetadataRepository(MongoRepository[DatasetMetadata]):
    """Repository for dataset metadata."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__("dataset_metadata", DatasetMetadata)
    
    def find_by_openml_id(self, openml_id: str) -> Optional[DatasetMetadata]:
        """Find dataset metadata by OpenML ID."""
        return mongo_service.find_one(
            self.collection_name, 
            {"dataset_id": openml_id}, 
            self.model_class
        )
    
    async def async_find_by_openml_id(self, openml_id: str) -> Optional[DatasetMetadata]:
        """Find dataset metadata by OpenML ID asynchronously."""
        return await mongo_service.async_find_one(
            self.collection_name, 
            {"dataset_id": openml_id}, 
            self.model_class
        )
    
    def find_by_tags(self, tags: List[str], match_all: bool = False) -> List[DatasetMetadata]:
        """
        Find datasets by tags.
        
        Args:
            tags: List of tags to match
            match_all: If True, all tags must match; if False, any tag can match
        
        Returns:
            List of matching datasets
        """
        if match_all:
            # All tags must match
            query = {"tags": {"$all": tags}}
        else:
            # Any tag can match
            query = {"tags": {"$in": tags}}
            
        return mongo_service.find(
            self.collection_name,
            query,
            self.model_class
        )
    
    async def async_find_by_tags(
        self, 
        tags: List[str], 
        match_all: bool = False
    ) -> List[DatasetMetadata]:
        """
        Find datasets by tags asynchronously.
        
        Args:
            tags: List of tags to match
            match_all: If True, all tags must match; if False, any tag can match
        
        Returns:
            List of matching datasets
        """
        if match_all:
            # All tags must match
            query = {"tags": {"$all": tags}}
        else:
            # Any tag can match
            query = {"tags": {"$in": tags}}
            
        return await mongo_service.async_find(
            self.collection_name,
            query,
            self.model_class
        )
    
    def update_usage_stats(self, dataset_id: str) -> bool:
        """
        Update usage statistics for a dataset.
        
        Args:
            dataset_id: OpenML dataset ID
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Find the dataset
            dataset = self.find_by_openml_id(dataset_id)
            if not dataset:
                return False
                
            # Update usage stats
            dataset.last_used = datetime.now()
            dataset.usage_count += 1
            
            # Save the updated dataset
            self.save(dataset)
            return True
            
        except Exception as e:
            logger.error(f"Error updating dataset usage stats: {e}")
            return False
    
    async def async_update_usage_stats(self, dataset_id: str) -> bool:
        """
        Update usage statistics for a dataset asynchronously.
        
        Args:
            dataset_id: OpenML dataset ID
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Find the dataset
            dataset = await self.async_find_by_openml_id(dataset_id)
            if not dataset:
                return False
                
            # Update usage stats
            dataset.last_used = datetime.now()
            dataset.usage_count += 1
            
            # Save the updated dataset
            await self.async_save(dataset)
            return True
            
        except Exception as e:
            logger.error(f"Error updating dataset usage stats: {e}")
            return False


class DatasetVersionRepository(MongoRepository[DatasetVersion]):
    """Repository for dataset versions."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__("dataset_versions", DatasetVersion)
    
    def find_by_version_id(self, version_id: str) -> Optional[DatasetVersion]:
        """Find dataset version by version ID."""
        return mongo_service.find_one(
            self.collection_name, 
            {"version_id": version_id}, 
            self.model_class
        )
    
    async def async_find_by_version_id(self, version_id: str) -> Optional[DatasetVersion]:
        """Find dataset version by version ID asynchronously."""
        return await mongo_service.async_find_one(
            self.collection_name, 
            {"version_id": version_id}, 
            self.model_class
        )
    
    def find_versions_for_dataset(self, dataset_id: str) -> List[DatasetVersion]:
        """Find all versions for a dataset."""
        return mongo_service.find(
            self.collection_name,
            {"dataset_id": dataset_id},
            self.model_class,
            sort=[("created_at", -1)]  # Sort by created_at descending
        )
    
    async def async_find_versions_for_dataset(self, dataset_id: str) -> List[DatasetVersion]:
        """Find all versions for a dataset asynchronously."""
        return await mongo_service.async_find(
            self.collection_name,
            {"dataset_id": dataset_id},
            self.model_class,
            sort=[("created_at", -1)]  # Sort by created_at descending
        )
    
    def get_latest_version(self, dataset_id: str) -> Optional[DatasetVersion]:
        """Get the latest version for a dataset."""
        versions = self.find_versions_for_dataset(dataset_id)
        return versions[0] if versions else None
    
    async def async_get_latest_version(self, dataset_id: str) -> Optional[DatasetVersion]:
        """Get the latest version for a dataset asynchronously."""
        versions = await self.async_find_versions_for_dataset(dataset_id)
        return versions[0] if versions else None


class DatasetTrainingResultRepository(MongoRepository[DatasetTrainingResult]):
    """Repository for dataset training results."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__("dataset_training_results", DatasetTrainingResult)
    
    def find_by_training_id(self, training_id: str) -> Optional[DatasetTrainingResult]:
        """Find training result by training ID."""
        return mongo_service.find_one(
            self.collection_name, 
            {"training_id": training_id}, 
            self.model_class
        )
    
    async def async_find_by_training_id(self, training_id: str) -> Optional[DatasetTrainingResult]:
        """Find training result by training ID asynchronously."""
        return await mongo_service.async_find_one(
            self.collection_name, 
            {"training_id": training_id}, 
            self.model_class
        )
    
    def find_results_for_agent(self, agent_id: str) -> List[DatasetTrainingResult]:
        """Find all training results for an agent."""
        return mongo_service.find(
            self.collection_name,
            {"agent_id": agent_id},
            self.model_class,
            sort=[("completed_at", -1)]  # Sort by completed_at descending
        )
    
    async def async_find_results_for_agent(self, agent_id: str) -> List[DatasetTrainingResult]:
        """Find all training results for an agent asynchronously."""
        return await mongo_service.async_find(
            self.collection_name,
            {"agent_id": agent_id},
            self.model_class,
            sort=[("completed_at", -1)]  # Sort by completed_at descending
        )
    
    def find_results_for_dataset(self, dataset_id: str) -> List[DatasetTrainingResult]:
        """Find all training results for a dataset."""
        return mongo_service.find(
            self.collection_name,
            {"dataset_id": dataset_id},
            self.model_class,
            sort=[("completed_at", -1)]  # Sort by completed_at descending
        )
    
    async def async_find_results_for_dataset(self, dataset_id: str) -> List[DatasetTrainingResult]:
        """Find all training results for a dataset asynchronously."""
        return await mongo_service.async_find(
            self.collection_name,
            {"dataset_id": dataset_id},
            self.model_class,
            sort=[("completed_at", -1)]  # Sort by completed_at descending
        )
