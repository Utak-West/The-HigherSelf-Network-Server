"""
Base Pydantic models for The HigherSelf Network Server's Notion integration.
These models are aligned with The HigherSelf Network's central data management approach.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator


class EntityType(str, Enum):
    """Types of business entities supported in the system."""

    CONSULTING_FIRM = "CONSULTING_FIRM"
    ART_GALLERY = "ART_GALLERY"
    WELLNESS_CENTER = "WELLNESS_CENTER"


class ApiPlatform(str, Enum):
    """API platforms integrated with the agent network."""

    NOTION = "NOTION_API"
    HUBSPOT = "HUBSPOT_API"
    TYPEFORM = "TYPEFORM_API"
    AIRTABLE = "AIRTABLE_API"
    AMELIA = "AMELIA_API"
    WOOCOMMERCE = "WOOCOMMERCE_API"
    TUTORLM = "TUTORLM_API"
    STRIPE = "STRIPE_API"
    PLAUD = "PLAUD_API"


class AgentCapability(str, Enum):
    """Capabilities that agents can have."""

    # Original capabilities
    BOOKING_DETECTION = "Booking Detection"
    CLIENT_COMMUNICATION = "Client Communication"
    LEAD_PROCESSING = "Lead Processing"
    CRM_SYNC = "CRM Sync"
    INVENTORY_MANAGEMENT = "Inventory Management"
    TASK_CREATION = "Task Creation"
    WORKFLOW_MANAGEMENT = "Workflow Management"
    NOTIFICATION_DISPATCH = "Notification Dispatch"
    CONTENT_GENERATION = "Content Generation"
    LEARNING_CONTENT = "Learning Content Management"
    TRANSCRIPTION_PROCESSING = "Transcription Processing"

    # Additional capabilities for Grace Fields training
    LEAD_CAPTURE = "Lead Capture"
    BOOKING_MANAGEMENT = "Booking Management"
    TASK_MANAGEMENT = "Task Management"
    MARKETING_CAMPAIGN = "Marketing Campaign"
    COMMUNITY_ENGAGEMENT = "Community Engagement"
    CONTENT_CREATION = "Content Creation"
    CONTENT_DISTRIBUTION = "Content Distribution"
    AUDIENCE_ANALYSIS = "Audience Analysis"
    ERROR_HANDLING = "Error Handling"
    WORKFLOW_ORCHESTRATION = "Workflow Orchestration"


class AgentStatus(str, Enum):
    """Statuses an agent can have."""

    DEPLOYED = "Deployed"
    DEVELOPMENT = "Development"
    INACTIVE = "Inactive"
    DEPRECATED = "Deprecated"


class RuntimeEnvironment(str, Enum):
    """Runtime environments for agents."""

    DOCKER = "Docker (HigherSelf Network Server)"
    SERVERLESS = "Serverless"


class WorkflowStatus(str, Enum):
    """Statuses a workflow can have."""

    DRAFT = "Draft"
    IMPLEMENTED = "Implemented"
    ACTIVE = "Active"


class InstanceStatus(str, Enum):
    """Statuses a workflow instance can have."""

    ACTIVE = "Active"
    COMPLETED = "Completed"
    ERROR = "Error"
    ON_HOLD = "On Hold"


class IntegrationStatus(str, Enum):
    """Statuses for API integrations."""

    ACTIVE = "Active"
    DEPRECATED = "Deprecated"
    PLANNED = "Planned"
    UNDER_TEST = "Under Test"


class NotificationChannel(str, Enum):
    """Channels for sending notifications."""

    EMAIL = "Email"
    SMS = "SMS"
    SLACK = "Slack"
    PUSH_NOTIFICATION = "Push Notification"


class TaskStatus(str, Enum):
    """Statuses a task can have."""

    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    DONE = "Done"
    CANCELLED = "Cancelled"


class ContentReviewStatus(str, Enum):
    """Statuses for content review."""

    PENDING_REVIEW = "Pending Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class NotionPage(BaseModel):
    """
    Represents a record in a Notion database.
    Used for constructing API requests and parsing responses.
    """

    page_id: Optional[str] = Field(
        None, description="Notion page ID when record exists"
    )
    database_id: str = Field(..., description="Notion database ID")
    properties: Dict[str, Any] = Field(..., description="Notion page properties")

    @classmethod
    def from_pydantic(cls, model: BaseModel, database_id: str) -> "NotionPage":
        """Convert any Pydantic model to a Notion page structure."""
        properties = {}
        for field_name, field_value in model.dict().items():
            # Convert to Notion property format based on field type
            if field_value is None:
                continue

            # Handle different field types
            if isinstance(field_value, str):
                properties[field_name] = {
                    "rich_text": [{"text": {"content": field_value}}]
                }
            elif isinstance(field_value, int) or isinstance(field_value, float):
                properties[field_name] = {"number": field_value}
            elif isinstance(field_value, bool):
                properties[field_name] = {"checkbox": field_value}
            elif isinstance(field_value, datetime):
                properties[field_name] = {"date": {"start": field_value.isoformat()}}
            elif isinstance(field_value, list):
                # For multi-select properties
                if all(isinstance(item, str) for item in field_value):
                    properties[field_name] = {
                        "multi_select": [{"name": item} for item in field_value]
                    }
                # For relation properties (assuming list of IDs)
                elif all(isinstance(item, (str, UUID)) for item in field_value):
                    properties[field_name] = {
                        "relation": [{"id": str(item)} for item in field_value]
                    }
            elif isinstance(field_value, dict):
                # For rich text content or other structured data
                properties[field_name] = {
                    "rich_text": [{"text": {"content": json.dumps(field_value)}}]
                }
            elif isinstance(field_value, Enum):
                # For enum values
                properties[field_name] = {"select": {"name": field_value.value}}

        return cls(database_id=database_id, properties=properties)


class NotionIntegrationConfig(BaseModel):
    """Configuration for Notion integration."""

    token: str = Field(..., description="Notion API token")
    database_mappings: Dict[str, str] = Field(
        ..., description="Model to database ID mappings"
    )
    last_sync: Optional[datetime] = Field(
        None, description="Last synchronization timestamp"
    )
    sync_frequency: int = Field(3600, description="Sync frequency in seconds")
