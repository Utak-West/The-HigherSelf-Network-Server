"""
Models for The HigherSelf Network Server.

This package contains Pydantic models that represent the data structures
used throughout the system, aligned with the 16-database Notion structure.
"""

# Audience segmentation models
from models.audience_models import *

# Barter system models
from models.barter_models import (
    BarterListing,
    BarterMatch,
    BarterProfile,
    BarterRequest,
    BarterStatus,
    BarterTransaction,
    CulturalAdaptation,
    CulturalRegion,
    Location,
    ServiceCategory,
    SkillLevel,
)

# Base models and enums
from models.base import (
    AgentCapability,
    AgentStatus,
    ApiPlatform,
    ContentReviewStatus,
    EntityType,
    InstanceStatus,
    IntegrationStatus,
    NotificationChannel,
    NotionIntegrationConfig,
    NotionPage,
    RuntimeEnvironment,
    TaskStatus,
    WorkflowStatus,
)

# CapCut integration models
from models.capcut_models import *

# Content models
from models.content_models import *

# Core Notion database models
from models.notion_db_models import (
    Agent,
    AgentCommunication,
    AIContentReview,
    ApiIntegration,
    BusinessEntity,
    DataTransformation,
    NotificationTemplate,
    Task,
    UseCase,
    Workflow,
    WorkflowInstance,
)

# Extended Notion database models for all 16 databases
from models.notion_db_models_extended import *

# Pipit payment integration models
from models.pipit_models import *

# Task management models
from models.task_models import *

# Video models
from models.video_models import *

# Video transaction models
from models.video_transaction_models import *

__all__ = [
    "EntityType",
    "ApiPlatform",
    "AgentCapability",
    "AgentStatus",
    "RuntimeEnvironment",
    "WorkflowStatus",
    "InstanceStatus",
    "IntegrationStatus",
    "NotificationChannel",
    "TaskStatus",
    "ContentReviewStatus",
    "NotionPage",
    "NotionIntegrationConfig",
    "BusinessEntity",
    "Agent",
    "Workflow",
    "WorkflowInstance",
    "ApiIntegration",
    "DataTransformation",
    "UseCase",
    "NotificationTemplate",
    "AgentCommunication",
    "Task",
    "AIContentReview",
    # Barter system models
    "ServiceCategory",
    "SkillLevel",
    "BarterStatus",
    "CulturalRegion",
    "Location",
    "CulturalAdaptation",
    "BarterListing",
    "BarterRequest",
    "BarterMatch",
    "BarterTransaction",
    "BarterProfile",
]
