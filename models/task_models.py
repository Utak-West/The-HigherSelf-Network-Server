"""
Task management data models for The HigherSelf Network.

These models support the TaskManagementAgent and maintain
Notion as the central hub for all task data.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class TaskPriority(str, Enum):
    """Task priority levels."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TaskStatus(str, Enum):
    """Task status states."""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    WAITING = "Waiting"
    COMPLETED = "Completed"
    CANCELED = "Canceled"


class TaskSource(str, Enum):
    """Sources that can generate tasks."""
    LEAD_CAPTURE = "Lead Capture"
    BOOKING = "Booking"
    CONTENT = "Content"
    CUSTOMER_SERVICE = "Customer Service"
    MARKETING = "Marketing"
    MANUAL = "Manual"
    SCHEDULED = "Scheduled"


class TaskCategory(str, Enum):
    """Categories of tasks."""
    FOLLOW_UP = "Follow Up"
    CONTENT_CREATION = "Content Creation"
    ADMIN = "Admin"
    FINANCIAL = "Financial"
    MARKETING = "Marketing"
    CUSTOMER_SERVICE = "Customer Service"
    EVENT_PREP = "Event Preparation"
    TECHNICAL = "Technical"


class TaskTemplate(BaseModel):
    """Model for a task template."""
    name: str
    description: str
    category: TaskCategory
    estimated_minutes: int = 30
    priority: TaskPriority = TaskPriority.MEDIUM
    checklist_items: List[str] = Field(default_factory=list)
    default_assignee: Optional[str] = None
    due_date_offset_days: Optional[int] = None
    reminder_days_before: Optional[int] = None
    source: TaskSource = TaskSource.MANUAL
    business_entity_id: str
    workflow_id: Optional[str] = None
    additional_data: Dict[str, Any] = Field(default_factory=dict)


class TaskReminder(BaseModel):
    """Model for a task reminder."""
    task_id: str
    remind_at: datetime
    reminded: bool = False
    channel: str  # email, slack, notion
    recipient: str
    message: Optional[str] = None