"""
Base Pydantic models for The HigherSelf Network Server's Notion integration.

These models are aligned with The HigherSelf Network's central data management approach.
Optimized with Pydantic v2 patterns for enhanced performance and validation.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# Performance-optimized base model configuration
class OptimizedBaseModel(BaseModel):
    """
    Base model with performance optimizations for HigherSelf Network Server.

    Features:
    - Frozen models for immutability and performance
    - Validation alias generation for flexible field names
    - Extra field handling for API compatibility
    - Optimized serialization settings
    """

    model_config = ConfigDict(
        # Performance optimizations
        frozen=True,  # Immutable models for better performance and caching
        validate_assignment=True,  # Validate on assignment
        use_enum_values=True,  # Use enum values in serialization

        # API compatibility
        extra='forbid',  # Strict validation - no extra fields allowed
        populate_by_name=True,  # Allow field population by alias or name

        # Serialization optimizations
        ser_json_bytes=True,  # Optimize JSON serialization
        validate_default=True,  # Validate default values

        # String handling
        str_strip_whitespace=True,  # Strip whitespace from strings
        str_to_lower=False,  # Don't auto-lowercase (preserve case)

        # Performance settings
        arbitrary_types_allowed=False,  # Strict type checking
        use_list=True,  # Use list instead of set for better performance
    )


class CacheableModel(OptimizedBaseModel):
    """
    Base model for cacheable entities with TTL and cache key generation.
    """

    # Cache metadata (not serialized to API responses)
    _cache_ttl: Optional[int] = Field(default=300, exclude=True)  # 5 minutes default
    _cache_key_prefix: Optional[str] = Field(default=None, exclude=True)
    _last_cached: Optional[datetime] = Field(default=None, exclude=True)

    def get_cache_key(self, suffix: Optional[str] = None) -> str:
        """Generate cache key for this model instance."""
        prefix = self._cache_key_prefix or self.__class__.__name__.lower()
        base_key = f"{prefix}:{hash(self.model_dump_json())}"
        return f"{base_key}:{suffix}" if suffix else base_key

    def is_cache_valid(self) -> bool:
        """Check if cached data is still valid based on TTL."""
        if not self._last_cached or not self._cache_ttl:
            return False

        elapsed = (datetime.now() - self._last_cached).total_seconds()
        return elapsed < self._cache_ttl


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


class NotionPage(CacheableModel):
    """
    Represents a record in a Notion database.

    Used for constructing API requests and parsing responses.
    Optimized with caching support for better performance.
    """

    page_id: Optional[str] = Field(
        None, description="Notion page ID when record exists"
    )
    database_id: str = Field(..., description="Notion database ID")
    properties: Dict[str, Any] = Field(..., description="Notion page properties")

    # Cache configuration
    _cache_ttl: Optional[int] = Field(default=600, exclude=True)  # 10 minutes for Notion pages
    _cache_key_prefix: Optional[str] = Field(default="notion_page", exclude=True)

    @field_validator('database_id')
    @classmethod
    def validate_database_id(cls, v: str) -> str:
        """Validate database ID format."""
        if not v or len(v) < 32:
            raise ValueError("Database ID must be at least 32 characters")
        return v.replace('-', '')  # Normalize database ID format

    @classmethod
    def from_pydantic(cls, model: BaseModel, database_id: str) -> "NotionPage":
        """Convert any Pydantic model to a Notion page structure."""
        # Use model_dump instead of deprecated dict() method
        model_data = model.model_dump() if hasattr(model, 'model_dump') else model.dict()
        properties = cls._convert_to_notion_properties(model_data)

        return cls(database_id=database_id, properties=properties, page_id=None)

    @staticmethod
    def _convert_to_notion_properties(model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert model data to Notion properties format."""
        properties = {}

        for field_name, field_value in model_data.items():
            if field_value is None:
                continue

            # Use type-specific converters for better performance
            notion_property = NotionPage._convert_field_to_notion_property(field_value)
            if notion_property:
                properties[field_name] = notion_property

        return properties

    @staticmethod
    def _convert_field_to_notion_property(field_value: Any) -> Optional[Dict[str, Any]]:
        """Convert a single field value to Notion property format."""
        if isinstance(field_value, str):
            return {"rich_text": [{"text": {"content": field_value}}]}
        elif isinstance(field_value, (int, float)):
            return {"number": field_value}
        elif isinstance(field_value, bool):
            return {"checkbox": field_value}
        elif isinstance(field_value, datetime):
            return {"date": {"start": field_value.isoformat()}}
        elif isinstance(field_value, list):
            return NotionPage._convert_list_to_notion_property(field_value)
        elif isinstance(field_value, dict):
            return {"rich_text": [{"text": {"content": json.dumps(field_value)}}]}
        elif isinstance(field_value, Enum):
            return {"select": {"name": field_value.value}}

        return None

    @staticmethod
    def _convert_list_to_notion_property(field_value: List[Any]) -> Optional[Dict[str, Any]]:
        """Convert list field to appropriate Notion property."""
        if not field_value:
            return None

        # Multi-select for string lists
        if all(isinstance(item, str) for item in field_value):
            return {"multi_select": [{"name": item} for item in field_value]}
        # Relation for ID lists
        elif all(isinstance(item, (str, UUID)) for item in field_value):
            return {"relation": [{"id": str(item)} for item in field_value]}

        return None


class NotionIntegrationConfig(CacheableModel):
    """Configuration for Notion integration with caching support."""

    token: str = Field(..., description="Notion API token")
    database_mappings: Dict[str, str] = Field(
        ..., description="Model to database ID mappings"
    )
    last_sync: Optional[datetime] = Field(
        None, description="Last synchronization timestamp"
    )
    sync_frequency: int = Field(3600, description="Sync frequency in seconds")

    # Cache configuration for integration config
    _cache_ttl: Optional[int] = Field(default=1800, exclude=True)  # 30 minutes
    _cache_key_prefix: Optional[str] = Field(default="notion_config", exclude=True)

    @field_validator('sync_frequency')
    @classmethod
    def validate_sync_frequency(cls, v: int) -> int:
        """Validate sync frequency is reasonable."""
        if v < 60:  # Minimum 1 minute
            raise ValueError("Sync frequency must be at least 60 seconds")
        if v > 86400:  # Maximum 24 hours
            raise ValueError("Sync frequency must not exceed 86400 seconds (24 hours)")
        return v


class AgentPersonality(str, Enum):
    """Named agent personalities in the HigherSelf Network."""

    NYRA = "nyra"
    SOLARI = "solari"
    RUVO = "ruvo"
    LIORA = "liora"
    SAGE = "sage"
    ELAN = "elan"
    ZEVI = "zevi"
    ATLAS = "atlas"
    GRACE_FIELDS = "grace_fields"


class AgentRole(str, Enum):
    """Functional roles that agents can perform in the system."""

    LEAD_CAPTURE = "lead_capture"
    BOOKING_MANAGER = "booking_manager"
    TASK_ORCHESTRATOR = "task_orchestrator"
    MARKETING_STRATEGIST = "marketing_strategist"
    COMMUNITY_CURATOR = "community_curator"
    CONTENT_CHOREOGRAPHER = "content_choreographer"
    AUDIENCE_ANALYST = "audience_analyst"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    MASTER_ORCHESTRATOR = "master_orchestrator"
