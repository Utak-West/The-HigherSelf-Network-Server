"""
MongoDB Repository for The HigherSelf Network Server.

This module provides repository classes for MongoDB collections, abstracting
the data access layer and providing a clean interface for CRUD operations.
"""

from typing import Dict, List, Optional, Type, Any, Generic, TypeVar
from datetime import datetime

from loguru import logger

from models.mongodb_models import (
    MongoBaseModel, AgentDocument, WorkflowDocument, WorkflowInstanceDocument,
    TaskDocument, AgentCommunicationDocument, ApiIntegrationDocument, SystemHealthDocument
)
from services.mongodb_service import mongo_service

# Type variable for repository generic type
T = TypeVar('T', bound=MongoBaseModel)


class MongoRepository(Generic[T]):
    """Base repository class for MongoDB collections."""
    
    def __init__(self, collection_name: str, model_class: Type[T]):
        """Initialize the repository with collection name and model class."""
        self.collection_name = collection_name
        self.model_class = model_class
    
    def save(self, model: T) -> str:
        """Save a model to the collection."""
        return mongo_service.save_model(self.collection_name, model)
    
    async def async_save(self, model: T) -> str:
        """Save a model to the collection asynchronously."""
        return await mongo_service.async_save_model(self.collection_name, model)
    
    def find_by_id(self, model_id: str) -> Optional[T]:
        """Find a model by ID."""
        return mongo_service.find_model_by_id(self.collection_name, model_id, self.model_class)
    
    async def async_find_by_id(self, model_id: str) -> Optional[T]:
        """Find a model by ID asynchronously."""
        return await mongo_service.async_find_model_by_id(self.collection_name, model_id, self.model_class)
    
    def find_all(self, limit: int = 0, skip: int = 0) -> List[T]:
        """Find all models in the collection."""
        return mongo_service.find_models(self.collection_name, {}, self.model_class, limit, skip)
    
    async def async_find_all(self, limit: int = 0, skip: int = 0) -> List[T]:
        """Find all models in the collection asynchronously."""
        return await mongo_service.async_find_models(self.collection_name, {}, self.model_class, limit, skip)
    
    def find_by_filter(self, filter_dict: Dict[str, Any], limit: int = 0, skip: int = 0) -> List[T]:
        """Find models matching a filter."""
        return mongo_service.find_models(self.collection_name, filter_dict, self.model_class, limit, skip)
    
    async def async_find_by_filter(self, filter_dict: Dict[str, Any], limit: int = 0, skip: int = 0) -> List[T]:
        """Find models matching a filter asynchronously."""
        return await mongo_service.async_find_models(self.collection_name, filter_dict, self.model_class, limit, skip)
    
    def delete_by_id(self, model_id: str) -> int:
        """Delete a model by ID."""
        return mongo_service.delete_one(self.collection_name, {"id": model_id})
    
    async def async_delete_by_id(self, model_id: str) -> int:
        """Delete a model by ID asynchronously."""
        return await mongo_service.async_delete_one(self.collection_name, {"id": model_id})


class AgentRepository(MongoRepository[AgentDocument]):
    """Repository for Agent documents."""
    
    def __init__(self):
        """Initialize the repository with the agents collection."""
        super().__init__("agents", AgentDocument)
    
    def find_by_name(self, name: str) -> Optional[AgentDocument]:
        """Find an agent by name."""
        agents = self.find_by_filter({"name": name}, limit=1)
        return agents[0] if agents else None
    
    async def async_find_by_name(self, name: str) -> Optional[AgentDocument]:
        """Find an agent by name asynchronously."""
        agents = await self.async_find_by_filter({"name": name}, limit=1)
        return agents[0] if agents else None
    
    def find_by_status(self, status: str) -> List[AgentDocument]:
        """Find agents by status."""
        return self.find_by_filter({"status": status})
    
    async def async_find_by_status(self, status: str) -> List[AgentDocument]:
        """Find agents by status asynchronously."""
        return await self.async_find_by_filter({"status": status})


class WorkflowRepository(MongoRepository[WorkflowDocument]):
    """Repository for Workflow documents."""
    
    def __init__(self):
        """Initialize the repository with the workflows collection."""
        super().__init__("workflows", WorkflowDocument)
    
    def find_by_name(self, name: str) -> Optional[WorkflowDocument]:
        """Find a workflow by name."""
        workflows = self.find_by_filter({"name": name}, limit=1)
        return workflows[0] if workflows else None
    
    async def async_find_by_name(self, name: str) -> Optional[WorkflowDocument]:
        """Find a workflow by name asynchronously."""
        workflows = await self.async_find_by_filter({"name": name}, limit=1)
        return workflows[0] if workflows else None
    
    def find_by_type(self, workflow_type: str) -> List[WorkflowDocument]:
        """Find workflows by type."""
        return self.find_by_filter({"workflow_type": workflow_type})
    
    async def async_find_by_type(self, workflow_type: str) -> List[WorkflowDocument]:
        """Find workflows by type asynchronously."""
        return await self.async_find_by_filter({"workflow_type": workflow_type})


class WorkflowInstanceRepository(MongoRepository[WorkflowInstanceDocument]):
    """Repository for WorkflowInstance documents."""
    
    def __init__(self):
        """Initialize the repository with the workflow_instances collection."""
        super().__init__("workflow_instances", WorkflowInstanceDocument)
    
    def find_by_workflow_id(self, workflow_id: str) -> List[WorkflowInstanceDocument]:
        """Find workflow instances by workflow ID."""
        return self.find_by_filter({"workflow_id": workflow_id})
    
    async def async_find_by_workflow_id(self, workflow_id: str) -> List[WorkflowInstanceDocument]:
        """Find workflow instances by workflow ID asynchronously."""
        return await self.async_find_by_filter({"workflow_id": workflow_id})
    
    def find_by_status(self, status: str) -> List[WorkflowInstanceDocument]:
        """Find workflow instances by status."""
        return self.find_by_filter({"status": status})
    
    async def async_find_by_status(self, status: str) -> List[WorkflowInstanceDocument]:
        """Find workflow instances by status asynchronously."""
        return await self.async_find_by_filter({"status": status})


class TaskRepository(MongoRepository[TaskDocument]):
    """Repository for Task documents."""
    
    def __init__(self):
        """Initialize the repository with the tasks collection."""
        super().__init__("tasks", TaskDocument)
    
    def find_by_status(self, status: str) -> List[TaskDocument]:
        """Find tasks by status."""
        return self.find_by_filter({"status": status})
    
    async def async_find_by_status(self, status: str) -> List[TaskDocument]:
        """Find tasks by status asynchronously."""
        return await self.async_find_by_filter({"status": status})
    
    def find_by_assigned_to(self, assigned_to: str) -> List[TaskDocument]:
        """Find tasks by assignee."""
        return self.find_by_filter({"assigned_to": assigned_to})
    
    async def async_find_by_assigned_to(self, assigned_to: str) -> List[TaskDocument]:
        """Find tasks by assignee asynchronously."""
        return await self.async_find_by_filter({"assigned_to": assigned_to})
    
    def find_by_workflow_instance_id(self, workflow_instance_id: str) -> List[TaskDocument]:
        """Find tasks by workflow instance ID."""
        return self.find_by_filter({"workflow_instance_id": workflow_instance_id})
    
    async def async_find_by_workflow_instance_id(self, workflow_instance_id: str) -> List[TaskDocument]:
        """Find tasks by workflow instance ID asynchronously."""
        return await self.async_find_by_filter({"workflow_instance_id": workflow_instance_id})


class AgentCommunicationRepository(MongoRepository[AgentCommunicationDocument]):
    """Repository for AgentCommunication documents."""
    
    def __init__(self):
        """Initialize the repository with the agent_communication collection."""
        super().__init__("agent_communication", AgentCommunicationDocument)
    
    def find_by_source_agent_id(self, source_agent_id: str) -> List[AgentCommunicationDocument]:
        """Find communication patterns by source agent ID."""
        return self.find_by_filter({"source_agent_id": source_agent_id})
    
    async def async_find_by_source_agent_id(self, source_agent_id: str) -> List[AgentCommunicationDocument]:
        """Find communication patterns by source agent ID asynchronously."""
        return await self.async_find_by_filter({"source_agent_id": source_agent_id})
    
    def find_by_target_agent_id(self, target_agent_id: str) -> List[AgentCommunicationDocument]:
        """Find communication patterns by target agent ID."""
        return self.find_by_filter({"target_agent_id": target_agent_id})
    
    async def async_find_by_target_agent_id(self, target_agent_id: str) -> List[AgentCommunicationDocument]:
        """Find communication patterns by target agent ID asynchronously."""
        return await self.async_find_by_filter({"target_agent_id": target_agent_id})


class ApiIntegrationRepository(MongoRepository[ApiIntegrationDocument]):
    """Repository for ApiIntegration documents."""
    
    def __init__(self):
        """Initialize the repository with the api_integrations collection."""
        super().__init__("api_integrations", ApiIntegrationDocument)
    
    def find_by_platform(self, platform: str) -> List[ApiIntegrationDocument]:
        """Find API integrations by platform."""
        return self.find_by_filter({"platform": platform})
    
    async def async_find_by_platform(self, platform: str) -> List[ApiIntegrationDocument]:
        """Find API integrations by platform asynchronously."""
        return await self.async_find_by_filter({"platform": platform})
    
    def find_by_status(self, status: str) -> List[ApiIntegrationDocument]:
        """Find API integrations by status."""
        return self.find_by_filter({"status": status})
    
    async def async_find_by_status(self, status: str) -> List[ApiIntegrationDocument]:
        """Find API integrations by status asynchronously."""
        return await self.async_find_by_filter({"status": status})


class SystemHealthRepository(MongoRepository[SystemHealthDocument]):
    """Repository for SystemHealth documents."""
    
    def __init__(self):
        """Initialize the repository with the system_health collection."""
        super().__init__("system_health", SystemHealthDocument)
    
    def find_latest(self) -> Optional[SystemHealthDocument]:
        """Find the latest system health record."""
        records = self.find_by_filter({}, limit=1, skip=0)
        return records[0] if records else None
    
    async def async_find_latest(self) -> Optional[SystemHealthDocument]:
        """Find the latest system health record asynchronously."""
        records = await self.async_find_by_filter({}, limit=1, skip=0)
        return records[0] if records else None
    
    def find_by_time_range(self, start_time: datetime, end_time: datetime) -> List[SystemHealthDocument]:
        """Find system health records within a time range."""
        return self.find_by_filter({
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        })
    
    async def async_find_by_time_range(self, start_time: datetime, end_time: datetime) -> List[SystemHealthDocument]:
        """Find system health records within a time range asynchronously."""
        return await self.async_find_by_filter({
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        })
