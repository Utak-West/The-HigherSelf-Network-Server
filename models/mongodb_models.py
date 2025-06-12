"""
MongoDB models for The HigherSelf Network Server.

This module contains Pydantic models that represent the MongoDB collections
used throughout the system, aligned with the existing Notion database structure.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from models.base import (AgentCapability, AgentStatus, ApiPlatform,
                         ContentReviewStatus, EntityType, InstanceStatus,
                         IntegrationStatus, NotificationChannel,
                         RuntimeEnvironment, TaskStatus, WorkflowStatus)


class MongoBaseModel(BaseModel):
    """Base model for all MongoDB documents."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    notion_page_id: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            UUID: lambda uuid: str(uuid),
        }


class AgentDocument(MongoBaseModel):
    """MongoDB document for Agent collection."""

    name: str
    description: Optional[str] = None
    agent_type: str
    capabilities: List[AgentCapability] = []
    status: AgentStatus = AgentStatus.INACTIVE
    runtime_environment: RuntimeEnvironment = RuntimeEnvironment.DOCKER
    configuration: Dict[str, Any] = Field(default_factory=dict)
    api_keys: Dict[str, str] = Field(default_factory=dict)
    last_active: Optional[datetime] = None
    version: str = "1.0.0"

    @field_validator("name", mode="before")
    @classmethod
    def name_must_not_be_empty(cls, v):
        """Validate that name is not empty."""
        if not v or not v.strip():
            raise ValueError("Name must not be empty")
        return v


class WorkflowDocument(MongoBaseModel):
    """MongoDB document for Workflow collection."""

    name: str
    description: Optional[str] = None
    workflow_type: str
    version: str = "1.0.0"
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    triggers: List[Dict[str, Any]] = Field(default_factory=list)
    required_agents: List[str] = Field(default_factory=list)
    required_integrations: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

    @field_validator("name", mode="before")
    @classmethod
    def name_must_not_be_empty(cls, v):
        """Validate that name is not empty."""
        if not v or not v.strip():
            raise ValueError("Name must not be empty")
        return v


class WorkflowInstanceDocument(MongoBaseModel):
    """MongoDB document for WorkflowInstance collection."""

    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.DRAFT
    current_step: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    error_message: Optional[str] = None
    assigned_agents: List[str] = Field(default_factory=list)

    @field_validator("workflow_id", mode="before")
    @classmethod
    def workflow_id_must_not_be_empty(cls, v):
        """Validate that workflow_id is not empty."""
        if not v or not v.strip():
            raise ValueError("Workflow ID must not be empty")
        return v


class TaskDocument(MongoBaseModel):
    """MongoDB document for Task collection."""

    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TO_DO
    priority: int = 1
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    workflow_instance_id: Optional[str] = None
    business_entity_id: Optional[str] = None
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    @field_validator("title", mode="before")
    @classmethod
    def title_must_not_be_empty(cls, v):
        """Validate that title is not empty."""
        if not v or not v.strip():
            raise ValueError("Title must not be empty")
        return v


class AgentCommunicationDocument(MongoBaseModel):
    """MongoDB document for AgentCommunication collection."""

    pattern_name: str
    description: Optional[str] = None
    source_agent_id: str
    target_agent_id: str
    message_format: Dict[str, Any] = Field(default_factory=dict)
    required_fields: List[str] = Field(default_factory=list)
    optional_fields: List[str] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("pattern_name", mode="before")
    @classmethod
    def pattern_name_must_not_be_empty(cls, v):
        """Validate that pattern_name is not empty."""
        if not v or not v.strip():
            raise ValueError("Pattern name must not be empty")
        return v


class ApiIntegrationDocument(MongoBaseModel):
    """MongoDB document for ApiIntegration collection."""

    name: str
    description: Optional[str] = None
    platform: ApiPlatform
    api_url: str
    auth_type: str
    status: IntegrationStatus = IntegrationStatus.PLANNED
    configuration: Dict[str, Any] = Field(default_factory=dict)
    credentials: Dict[str, str] = Field(default_factory=dict)
    rate_limits: Optional[Dict[str, Any]] = None

    @field_validator("name", mode="before")
    @classmethod
    def name_must_not_be_empty(cls, v):
        """Validate that name is not empty."""
        if not v or not v.strip():
            raise ValueError("Name must not be empty")
        return v


class SystemHealthDocument(MongoBaseModel):
    """MongoDB document for SystemHealth collection."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_agents: int
    active_workflows: int
    pending_tasks: int
    api_response_times: Dict[str, float] = Field(default_factory=dict)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
