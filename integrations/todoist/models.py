"""
Pydantic models for Todoist integration with The HigherSelf Network Server.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class BusinessEntity(str, Enum):
    """Business entities for task categorization."""
    
    SEVEN_SPACE = "7space"
    AM_CONSULTING = "am_consulting"
    HIGHER_SELF_NETWORK = "hsn"


class TaskPriority(int, Enum):
    """Todoist task priority levels."""
    
    NORMAL = 1
    HIGH = 2
    VERY_HIGH = 3
    URGENT = 4


class TaskStatus(str, Enum):
    """Task status for tracking."""
    
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EnergyLevel(str, Enum):
    """Energy level tags for task optimization."""
    
    HIGH = "high_energy"
    MEDIUM = "medium_energy"
    LOW = "low_energy"
    CREATIVE = "creative_energy"


class TimeDuration(str, Enum):
    """Time duration tags for task planning."""
    
    TWO_MINUTES = "2_minutes"
    FIVE_MINUTES = "5_minutes"
    FIFTEEN_MINUTES = "15_minutes"
    THIRTY_MINUTES = "30_minutes"
    ONE_HOUR = "1_hour"
    TWO_HOURS = "2_hours"
    HALF_DAY = "half_day"
    FULL_DAY = "full_day"


class DeviceType(str, Enum):
    """Device type tags for task execution."""
    
    COMPUTER = "computer"
    PHONE = "phone"
    TABLET = "tablet"
    ANY_DEVICE = "any_device"
    OFFLINE = "offline"


class TodoistLabel(BaseModel):
    """Todoist label model."""
    
    id: Optional[str] = None
    name: str
    color: Optional[str] = None
    order: Optional[int] = None
    is_favorite: bool = False


class TodoistProject(BaseModel):
    """Todoist project model."""
    
    id: Optional[str] = None
    name: str
    comment_count: Optional[int] = 0
    order: Optional[int] = None
    color: Optional[str] = None
    is_shared: bool = False
    is_favorite: bool = False
    is_inbox_project: bool = False
    is_team_inbox: bool = False
    view_style: str = "list"
    url: Optional[str] = None
    parent_id: Optional[str] = None
    business_entity: Optional[BusinessEntity] = None


class TodoistTask(BaseModel):
    """Todoist task model with HSN-specific extensions."""
    
    id: Optional[str] = None
    assigner_id: Optional[str] = None
    assignee_id: Optional[str] = None
    project_id: str
    section_id: Optional[str] = None
    parent_id: Optional[str] = None
    order: Optional[int] = None
    content: str
    description: Optional[str] = None
    is_completed: bool = False
    labels: List[str] = Field(default_factory=list)
    priority: TaskPriority = TaskPriority.NORMAL
    comment_count: Optional[int] = 0
    creator_id: Optional[str] = None
    created_at: Optional[datetime] = None
    due: Optional[Dict[str, Any]] = None
    url: Optional[str] = None
    duration: Optional[Dict[str, Any]] = None
    
    # HSN-specific fields
    business_entity: Optional[BusinessEntity] = None
    energy_level: Optional[EnergyLevel] = None
    time_duration: Optional[TimeDuration] = None
    device_type: Optional[DeviceType] = None
    server_event_id: Optional[str] = None
    automation_source: Optional[str] = None
    hsn_metadata: Dict[str, Any] = Field(default_factory=dict)


class TodoistWebhookEvent(BaseModel):
    """Todoist webhook event model."""
    
    event_name: str
    user_id: str
    event_data: Dict[str, Any]
    initiator: Dict[str, Any]
    version: str = "8"


class TaskCreationRequest(BaseModel):
    """Request model for creating tasks."""
    
    content: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    section_id: Optional[str] = None
    parent_id: Optional[str] = None
    order: Optional[int] = None
    labels: List[str] = Field(default_factory=list)
    priority: TaskPriority = TaskPriority.NORMAL
    due_string: Optional[str] = None
    due_date: Optional[str] = None
    due_datetime: Optional[str] = None
    due_lang: Optional[str] = None
    assignee_id: Optional[str] = None
    
    # HSN-specific fields
    business_entity: Optional[BusinessEntity] = None
    energy_level: Optional[EnergyLevel] = None
    time_duration: Optional[TimeDuration] = None
    device_type: Optional[DeviceType] = None
    automation_source: Optional[str] = None
    server_event_id: Optional[str] = None


class ProjectCreationRequest(BaseModel):
    """Request model for creating projects."""
    
    name: str
    parent_id: Optional[str] = None
    order: Optional[int] = None
    color: Optional[str] = None
    is_favorite: bool = False
    view_style: str = "list"
    business_entity: Optional[BusinessEntity] = None


class HSNTaskAutomation(BaseModel):
    """Configuration for HSN task automation."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    business_entity: BusinessEntity
    trigger_type: str  # "server_event", "webhook", "schedule", "manual"
    trigger_config: Dict[str, Any]
    task_template: TaskCreationRequest
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


class TodoistIntegrationConfig(BaseModel):
    """Configuration for Todoist integration."""
    
    api_token: str
    webhook_secret: Optional[str] = None
    default_project_ids: Dict[BusinessEntity, str] = Field(default_factory=dict)
    automation_rules: List[HSNTaskAutomation] = Field(default_factory=list)
    label_mappings: Dict[str, str] = Field(default_factory=dict)
    ifttt_enabled: bool = True
    webhook_url: Optional[str] = None
    sync_interval_minutes: int = 15
    
    class Config:
        use_enum_values = True


class TodoistSyncResponse(BaseModel):
    """Response model for sync operations."""
    
    sync_token: str
    full_sync: bool
    items: List[TodoistTask] = Field(default_factory=list)
    projects: List[TodoistProject] = Field(default_factory=list)
    labels: List[TodoistLabel] = Field(default_factory=list)
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    notes: List[Dict[str, Any]] = Field(default_factory=list)
    project_notes: List[Dict[str, Any]] = Field(default_factory=list)
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    reminders: List[Dict[str, Any]] = Field(default_factory=list)
    locations: List[Dict[str, Any]] = Field(default_factory=list)
    user: Optional[Dict[str, Any]] = None
    live_notifications: List[Dict[str, Any]] = Field(default_factory=list)
    collaborators: List[Dict[str, Any]] = Field(default_factory=list)
    notification_settings: List[Dict[str, Any]] = Field(default_factory=list)


class TaskAnalytics(BaseModel):
    """Analytics model for task performance."""
    
    business_entity: BusinessEntity
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    avg_completion_time_hours: Optional[float] = None
    tasks_by_priority: Dict[str, int] = Field(default_factory=dict)
    tasks_by_energy_level: Dict[str, int] = Field(default_factory=dict)
    tasks_by_duration: Dict[str, int] = Field(default_factory=dict)
    automation_effectiveness: Dict[str, float] = Field(default_factory=dict)
    period_start: datetime
    period_end: datetime
