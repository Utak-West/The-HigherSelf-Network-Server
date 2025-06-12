"""
Audience segmentation data models for The HigherSelf Network.

These models support the AudienceSegmentationAgent and maintain
Notion as the central hub for all audience data.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, EmailStr, Field


class InteractionType(str, Enum):
    """Types of customer interactions."""

    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"
    FORM_SUBMISSION = "form_submission"
    PURCHASE = "purchase"
    BOOKING = "booking"
    CONTENT_VIEW = "content_view"
    COURSE_ENROLLMENT = "course_enrollment"
    EVENT_SIGNUP = "event_signup"
    DOWNLOAD = "download"
    SOCIAL_ENGAGEMENT = "social_engagement"


class SegmentCriteria(BaseModel):
    """Criteria for defining audience segments."""

    field: str
    operator: str  # e.g., equals, contains, greater_than
    value: Any
    data_source: Optional[str] = None


class AudienceSegment(BaseModel):
    """Model for an audience segment."""

    name: str
    description: str
    criteria: List[SegmentCriteria] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    platform_ids: Dict[str, str] = Field(
        default_factory=dict
    )  # maps platform to segment ID
    member_count: int = 0
    is_active: bool = True
    business_entity_id: str
    tags: List[str] = Field(default_factory=list)


class CustomerProfile(BaseModel):
    """Model for a unified customer profile."""

    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    segments: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    purchase_history: List[Dict[str, Any]] = Field(default_factory=list)
    event_history: List[Dict[str, Any]] = Field(default_factory=list)
    form_submissions: List[Dict[str, Any]] = Field(default_factory=list)
    course_enrollments: List[Dict[str, Any]] = Field(default_factory=list)
    content_interactions: List[Dict[str, Any]] = Field(default_factory=list)
    external_ids: Dict[str, str] = Field(
        default_factory=dict
    )  # maps platform to user ID
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class SegmentSyncResult(BaseModel):
    """Result of syncing a segment to an external platform."""

    segment_id: str
    platform: str
    external_id: Optional[str] = None
    status: str
    member_count: int
    sync_time: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = None
