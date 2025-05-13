"""
Models for The HigherSelf Network Server.

This package contains Pydantic models that represent the data structures
used throughout the system, aligned with the 16-database Notion structure.
"""

# Base models and enums
from models.base import (
    EntityType, ApiPlatform, AgentCapability, AgentStatus, RuntimeEnvironment,
    WorkflowStatus, InstanceStatus, IntegrationStatus, NotificationChannel,
    TaskStatus, ContentReviewStatus, NotionPage, NotionIntegrationConfig
)

# Core Notion database models
from models.notion_db_models import (
    BusinessEntity, Agent, Workflow, WorkflowInstance,
    ApiIntegration, DataTransformation, UseCase,
    NotificationTemplate, AgentCommunication, Task,
    AIContentReview
)

# Extended Notion database models for all 16 databases
from models.notion_db_models_extended import *

# Task management models
from models.task_models import *

# Content models
from models.content_models import *

# Audience segmentation models
from models.audience_models import *

# Video models
from models.video_models import *

__all__ = [
    'EntityType', 'ApiPlatform', 'AgentCapability', 'AgentStatus',
    'RuntimeEnvironment', 'WorkflowStatus', 'InstanceStatus',
    'IntegrationStatus', 'NotificationChannel', 'TaskStatus',
    'ContentReviewStatus', 'NotionPage', 'NotionIntegrationConfig',
    'BusinessEntity', 'Agent', 'Workflow', 'WorkflowInstance',
    'ApiIntegration', 'DataTransformation', 'UseCase',
    'NotificationTemplate', 'AgentCommunication', 'Task',
    'AIContentReview'
]
