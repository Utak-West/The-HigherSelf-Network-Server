"""
Pydantic models that represent the Notion database structures for The HigherSelf Network.
These models are used for data validation, serialization/deserialization, and
structured interaction with the Notion API.
"""

# NotionIntegrationConfig - Used for webhook handling and API configurations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, validator

from models.base import (
    AgentCapability,
    AgentStatus,
    ApiPlatform,
    ContentReviewStatus,
    EntityType,
    InstanceStatus,
    IntegrationStatus,
    NotificationChannel,
    RuntimeEnvironment,
    TaskStatus,
    WorkflowStatus,
)


class NotionSetupConfig(BaseModel):
    """
    Configuration model for Notion initial setup, parent page, and webhooks.
    """

    api_token: str = Field(..., description="Notion API token")
    parent_page_id: Optional[str] = Field(
        None, description="Parent page ID for database creation"
    )
    webhook_secret: Optional[str] = Field(
        None, description="Secret for webhook verification"
    )

    @validator("api_token")
    def validate_token(cls, v):
        if not v:
            raise ValueError("Notion API token is required")
        return v

    @classmethod
    def from_env(cls) -> "NotionSetupConfig":
        """
        Create a configuration instance from environment variables.

        Returns:
            NotionSetupConfig: Configuration instance
        """
        return cls(
            api_token=os.environ.get("NOTION_API_TOKEN", ""),
            parent_page_id=os.environ.get("NOTION_PARENT_PAGE_ID"),
            webhook_secret=os.environ.get("WEBHOOK_SECRET"),
        )


class BusinessEntity(BaseModel):
    """
    Represents a business entity in the Business Entities Registry database.
    """

    name: str = Field(..., description="Business entity name")
    entity_type: EntityType = Field(..., description="Type of business entity")
    api_keys_reference: str = Field(
        ..., description="Secure reference to API credentials"
    )
    primary_workflows: List[str] = Field(
        default_factory=list, description="IDs of primary workflows"
    )
    active_agents: List[str] = Field(
        default_factory=list, description="IDs of active agents"
    )
    integration_status: str = Field("Active", description="Integration status")

    # Notion-specific fields
    page_id: Optional[str] = Field(None, description="Notion page ID")


class Agent(BaseModel):
    """
    Represents an agent in the Agent Registry database.
    """

    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    description: str = Field(..., description="Agent purpose and responsibilities")
    version: str = Field(..., description="Agent version")
    status: AgentStatus = Field(AgentStatus.DEVELOPMENT, description="Agent status")
    business_entity_association: List[str] = Field(
        default_factory=list, description="Associated business entities"
    )
    capabilities: List[AgentCapability] = Field(
        default_factory=list, description="Agent capabilities"
    )
    primary_apis_utilized: List[ApiPlatform] = Field(
        default_factory=list, description="Primary APIs used"
    )
    supported_workflows: List[str] = Field(
        default_factory=list, description="Supported workflow IDs"
    )
    primary_data_sources: List[str] = Field(
        default_factory=list, description="Primary data sources"
    )
    primary_data_sinks: List[str] = Field(
        default_factory=list, description="Primary data sinks"
    )
    runtime_environment: RuntimeEnvironment = Field(
        RuntimeEnvironment.DOCKER, description="Runtime environment"
    )
    source_code_location: Optional[str] = Field(None, description="Link to source code")

    # Notion-specific fields
    page_id: Optional[str] = Field(None, description="Notion page ID")


class Workflow(BaseModel):
    """
    Represents a workflow in the Workflows Library database.
    """

    workflow_id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Human-readable workflow name")
    description: str = Field(..., description="Workflow purpose")
    version: str = Field("1.0", description="Workflow version")
    business_entity: str = Field(..., description="Associated business entity ID")
    initial_state: str = Field(..., description="Initial workflow state")
    states: Dict[str, Dict[str, Any]] = Field(
        ..., description="State machine definition"
    )
    transitions: List[Dict[str, Any]] = Field(..., description="State transitions")
    required_agents: List[str] = Field(
        default_factory=list, description="Required agent IDs"
    )
    visualization_url: Optional[str] = Field(
        None, description="URL to state machine diagram"
    )
    status: WorkflowStatus = Field(WorkflowStatus.DRAFT, description="Workflow status")

    # Notion-specific fields
    page_id: Optional[str] = Field(None, description="Notion page ID")


class WorkflowInstance(BaseModel):
    """
    Represents an active workflow instance in the Active Workflow Instances database.
    This is a central operational database tracking currently running workflows.
    """

    instance_id: str = Field(
        default_factory=lambda: f"INST-{uuid4().hex[:8]}",
        description="Unique instance ID",
    )
    workflow_id: str = Field(..., description="Associated workflow ID")
    business_entity: str = Field(..., description="Business entity ID")
    current_state: str = Field(..., description="Current workflow state")
    client_lead_email: Optional[str] = Field(None, description="Client or lead email")
    client_lead_name: Optional[str] = Field(None, description="Client or lead name")
    client_lead_phone: Optional[str] = Field(None, description="Client or lead phone")
    start_date: datetime = Field(
        default_factory=datetime.now, description="Workflow start time"
    )
    last_transition_date: datetime = Field(
        default_factory=datetime.now, description="Last state transition time"
    )
    status: InstanceStatus = Field(InstanceStatus.ACTIVE, description="Instance status")
    error_message: Optional[str] = Field(
        None, description="Error message if status is Error"
    )
    assigned_to: Optional[str] = Field(
        None, description="User assigned to this instance"
    )
    priority: str = Field("Medium", description="Priority level")
    tags: List[str] = Field(default_factory=list, description="Tags for filtering")
    source_system: Optional[str] = Field(
        None, description="Source system (e.g., Amelia, WooCommerce)"
    )
    source_record_id: Optional[str] = Field(
        None, description="Record ID in source system"
    )
    hubspot_contact_id: Optional[str] = Field(
        None, description="HubSpot contact ID if synced"
    )
    airtable_record_id: Optional[str] = Field(
        None, description="Airtable record ID if synced"
    )
    key_data_payload: Optional[Dict[str, Any]] = Field(
        None, description="Critical data in JSON format"
    )
    history_log: List[Dict[str, Any]] = Field(
        default_factory=list, description="Append-only log of state transitions"
    )

    # Notion-specific fields
    page_id: Optional[str] = Field(None, description="Notion page ID")

    def add_history_entry(self, action: str, details: Dict[str, Any] = None) -> None:
        """Add an entry to the history log."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details or {},
        }
        self.history_log.append(entry)
        self.last_transition_date = datetime.now()


class ApiIntegration(BaseModel):
    """
    Represents an API integration in the API Integrations Catalog database.
    """

    platform: str = Field(..., description="Platform name (e.g., 'Amelia API v2.3')")
    description: str = Field(..., description="Integration description")
    base_url: str = Field(..., description="Base URL for API")
    authentication_type: str = Field(
        ..., description="Auth type (e.g., OAuth, API Key)"
    )
    credential_reference: str = Field(
        ..., description="Secure reference to credentials"
    )
    primary_endpoints: List[str] = Field(
        default_factory=list, description="Main endpoints used"
    )
    documentation_url: Optional[str] = Field(
        None, description="Link to API documentation"
    )
    business_entities: List[str] = Field(
        default_factory=list, description="Associated business entity IDs"
    )
    version: str = Field("1.0", description="API version")
    status: IntegrationStatus = Field(
        IntegrationStatus.ACTIVE, description="Integration status"
    )

    # Notion-specific fields
    page_id: Optional[str] = Field(None, description="Notion page ID")


class DataTransformation(BaseModel):
    """
    Represents a data transformation in the Data Transformations Registry database.
    """

    transformation_name: str = Field(..., description="Transformation name")
    description: str = Field(..., description="Transformation description")
    source_format: str = Field(..., description="Source data format")
    target_format: str = Field(..., description="Target data format")
    transformation_logic: str = Field(
        ..., description="Logic as Python code or pseudo-code"
    )
    sample_input: Dict[str, Any] = Field(..., description="Sample input JSON")
    sample_output: Dict[str, Any] = Field(..., description="Sample output JSON")
    used_by_workflows: List[str] = Field(
        default_factory=list, description="Workflow IDs using this transformation"
    )

    # Notion-specific fields
    page_id: Optional[str] = Field(None, description="Notion page ID")


class UseCase(BaseModel):
    """
    Represents a business use case in the Use Cases Library database.
    """

    use_case_id: str = Field(..., description="Unique use case ID")
    title: str = Field(..., description="Concise title")
    description: str = Field(..., description="Detailed description")
    business_entities: List[str] = Field(
        default_factory=list, description="Business entity IDs"
    )
    implemented_by_workflows: List[str] = Field(
        default_factory=list, description="Implementing workflow IDs"
    )
    user_stories: List[str] = Field(default_factory=list, description="User stories")
    acceptance_criteria: List[str] = Field(
        default_factory=list, description="Acceptance criteria"
    )
    implementation_status: str = Field("Planned", description="Implementation status")
    notion_dashboard_link: Optional[str] = Field(
        None, description="Link to Notion dashboard"
    )

    # Notion-specific fields
    page_id: Optional[str] = Field(None, description="Notion page ID")


class NotificationTemplate(BaseModel):
    """
    Represents a notification template in the Notifications Templates database.
    """

    template_id: str = Field(..., description="Unique template ID")
    description: str = Field(..., description="Template description")
    channel: NotificationChannel = Field(..., description="Notification channel")
    content_template: str = Field(..., description="Template content with placeholders")
    subject_template: Optional[str] = Field(
        None, description="Subject line for email templates"
    )
    supported_placeholders: List[str] = Field(
        default_factory=list, description="Valid placeholder names"
    )
    business_entities: List[str] = Field(
        default_factory=list, description="Business entity IDs"
    )
    creator: str = Field(..., description="Template creator")
    created_date: datetime = Field(
        default_factory=datetime.now, description="Creation date"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update date"
    )

    # Notion-specific fields
    page_id: Optional[str] = Field(None, description="Notion page ID")


class AgentCommunication(BaseModel):
    """
    Represents an agent communication pattern in the Agent Communication Patterns database.
    """

    pattern_name: str = Field(..., description="Pattern name")
    description: str = Field(..., description="Pattern description")
    source_agent: str = Field(..., description="Source agent ID")
    target_agent: str = Field(..., description="Target agent ID")
    message_format: str = Field(..., description="Message format/structure")
    communication_protocol: str = Field(
        "HTTP", description="Protocol (HTTP, Message Queue, etc.)"
    )
    sample_payload: Dict[str, Any] = Field(..., description="Sample message payload")
    active_workflows_using: List[str] = Field(
        default_factory=list, description="Workflow IDs using this pattern"
    )

    # Notion-specific fields
    page_id: Optional[str] = Field(None, description="Notion page ID")


class Task(BaseModel):
    """
    Represents a task in the Master Tasks Database.
    """

    task_id: str = Field(
        default_factory=lambda: f"TASK-{uuid4().hex[:8]}", description="Unique task ID"
    )
    task_name: str = Field(..., description="Task name")
    status: TaskStatus = Field(TaskStatus.TO_DO, description="Task status")
    description: str = Field(..., description="Task description")
    priority: str = Field("Medium", description="Priority level")
    due_date: Optional[datetime] = Field(None, description="Due date")
    assigned_to: Optional[str] = Field(None, description="Assignee")
    related_workflow_instance: Optional[str] = Field(
        None, description="Related workflow instance ID"
    )
    related_business_entity: Optional[str] = Field(
        None, description="Related business entity ID"
    )
    created_by: str = Field(..., description="Creator (user or agent ID)")
    created_date: datetime = Field(
        default_factory=datetime.now, description="Creation date"
    )
    last_edited_date: datetime = Field(
        default_factory=datetime.now, description="Last edit date"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for filtering")

    # Notion-specific fields
    page_id: Optional[str] = Field(None, description="Notion page ID")


class AIContentReview(BaseModel):
    """
    Represents an AI content review item in the AI Content Review database.
    Used for reviewing and refining AI-generated content.
    """

    content_title: str = Field(..., description="Content title")
    source_ai_tool: str = Field(
        ..., description="Source AI tool (e.g., Plaud, TutorLM)"
    )
    raw_output: str = Field(..., description="Original AI output")
    reviewed_output: Optional[str] = Field(None, description="Reviewed/edited content")
    status: ContentReviewStatus = Field(
        ContentReviewStatus.PENDING_REVIEW, description="Review status"
    )
    reviewer: Optional[str] = Field(None, description="Assigned reviewer")
    review_date: Optional[datetime] = Field(None, description="Date of review")
    notes: Optional[str] = Field(None, description="Review notes")
    related_business_entity: Optional[str] = Field(
        None, description="Related business entity ID"
    )

    # Notion-specific fields
    page_id: Optional[str] = Field(None, description="Notion page ID")


class ContentItem(BaseModel):
    """
    Represents a content item in the content management system.
    Used for tracking content through its lifecycle.
    """

    content_id: str = Field(
        default_factory=lambda: f"CONTENT-{uuid4().hex[:8]}",
        description="Unique content ID",
    )
    title: str = Field(..., description="Content title")
    content_type: str = Field(
        ..., description="Type of content (blog, social, email, etc.)"
    )
    stage: str = Field("idea", description="Current lifecycle stage")
    description: str = Field(..., description="Content description or brief")
    created_date: datetime = Field(
        default_factory=datetime.now, description="Creation date"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update date"
    )
    author: Optional[str] = Field(None, description="Content author")
    associated_business_entity: Optional[str] = Field(
        None, description="Associated business entity ID"
    )
    target_platforms: List[str] = Field(
        default_factory=list, description="Target distribution platforms"
    )
    keywords: List[str] = Field(default_factory=list, description="Content keywords")
    scheduled_publish_date: Optional[datetime] = Field(
        None, description="Scheduled publication date"
    )
    actual_publish_date: Optional[datetime] = Field(
        None, description="Actual publication date"
    )
    published_urls: List[str] = Field(
        default_factory=list, description="Published content URLs"
    )
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Performance metrics"
    )

    # Notion-specific field
    page_id: Optional[str] = Field(None, description="Notion page ID")


class ContentPlan(BaseModel):
    """
    Represents a content plan in the content management system.
    Used for planning and scheduling content creation and distribution.
    """

    plan_id: str = Field(
        default_factory=lambda: f"PLAN-{uuid4().hex[:8]}", description="Unique plan ID"
    )
    name: str = Field(..., description="Plan name")
    description: str = Field(..., description="Plan description")
    start_date: datetime = Field(default_factory=datetime.now, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    content_types: List[str] = Field(
        default_factory=list, description="Content types included in plan"
    )
    frequency: Dict[str, int] = Field(
        default_factory=dict, description="Publishing frequency by content type"
    )
    target_platforms: List[str] = Field(
        default_factory=list, description="Target platforms"
    )
    business_entity: Optional[str] = Field(
        None, description="Associated business entity ID"
    )
    themes: List[str] = Field(default_factory=list, description="Content themes")
    status: str = Field("Active", description="Plan status")
    owner: Optional[str] = Field(None, description="Plan owner")
    content_items: List[str] = Field(
        default_factory=list, description="Associated content item IDs"
    )

    # Notion-specific field
    page_id: Optional[str] = Field(None, description="Notion page ID")
