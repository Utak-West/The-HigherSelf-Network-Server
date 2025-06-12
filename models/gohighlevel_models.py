"""
GoHighLevel CRM models for The HigherSelf Network Server.

This module provides Pydantic models for GoHighLevel API integration,
supporting multi-business portfolio management and cross-business automation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class BusinessType(str, Enum):
    """Enumeration of supported business types."""

    ART_GALLERY = "art_gallery"
    WELLNESS_CENTER = "wellness_center"
    CONSULTANCY = "consultancy"
    INTERIOR_DESIGN = "interior_design"
    LUXURY_RENOVATIONS = "luxury_renovations"
    EXECUTIVE_WELLNESS = "executive_wellness"
    CORPORATE_WELLNESS = "corporate_wellness"


class ContactSource(str, Enum):
    """Enumeration of contact sources."""

    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    ADVERTISING = "advertising"
    EVENT = "event"
    CROSS_BUSINESS = "cross_business"


class OpportunityStage(str, Enum):
    """Enumeration of opportunity stages."""

    INITIAL_INQUIRY = "initial_inquiry"
    CONSULTATION_SCHEDULED = "consultation_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class SubAccountType(str, Enum):
    """Enumeration of GoHighLevel sub-account types."""

    CORE_BUSINESS = "core_business"
    HOME_SERVICES = "home_services"
    EXTENDED_WELLNESS = "extended_wellness"
    DEVELOPMENT = "development"
    ANALYTICS = "analytics"


class GHLContact(BaseModel):
    """GoHighLevel contact model with cross-business support."""

    id: Optional[str] = Field(None, description="GoHighLevel contact ID")
    first_name: str = Field(..., description="Contact first name")
    last_name: str = Field(..., description="Contact last name")
    email: str = Field(..., description="Contact email address")
    phone: Optional[str] = Field(None, description="Contact phone number")

    # Business context
    primary_business: BusinessType = Field(..., description="Primary business interest")
    source: ContactSource = Field(ContactSource.WEBSITE, description="Lead source")
    sub_account: SubAccountType = Field(..., description="GoHighLevel sub-account")

    # Cross-business tracking
    business_interests: List[BusinessType] = Field(
        default_factory=list, description="All business interests"
    )
    cross_sell_potential: Dict[BusinessType, float] = Field(
        default_factory=dict, description="Cross-sell scores"
    )

    # Custom fields by business type
    art_gallery_fields: Optional[Dict[str, Any]] = Field(
        None, description="Art gallery specific fields"
    )
    wellness_fields: Optional[Dict[str, Any]] = Field(
        None, description="Wellness specific fields"
    )
    consultancy_fields: Optional[Dict[str, Any]] = Field(
        None, description="Consultancy specific fields"
    )
    home_services_fields: Optional[Dict[str, Any]] = Field(
        None, description="Home services specific fields"
    )

    # Tags and categories
    tags: List[str] = Field(default_factory=list, description="Contact tags")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Additional custom fields"
    )

    # Integration tracking
    notion_page_id: Optional[str] = Field(None, description="Notion page ID for sync")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    @validator("email")
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not v or "@" not in v:
            raise ValueError("Valid email address is required")
        return v.lower().strip()

    @validator("business_interests")
    def validate_business_interests(
        cls, v: List[BusinessType], values: Dict[str, Any]
    ) -> List[BusinessType]:
        """Ensure primary business is included in interests."""
        primary_business = values.get("primary_business")
        if primary_business and primary_business not in v:
            v.append(primary_business)
        return v


class GHLOpportunity(BaseModel):
    """GoHighLevel opportunity model with pipeline management."""

    id: Optional[str] = Field(None, description="GoHighLevel opportunity ID")
    name: str = Field(..., description="Opportunity name")
    contact_id: str = Field(..., description="Associated contact ID")
    pipeline_id: str = Field(..., description="Pipeline ID")
    stage_id: str = Field(..., description="Current stage ID")
    stage: OpportunityStage = Field(..., description="Current stage")

    # Financial details
    monetary_value: Optional[float] = Field(None, description="Opportunity value")
    currency: str = Field("USD", description="Currency code")

    # Business context
    business_type: BusinessType = Field(
        ..., description="Business type for this opportunity"
    )
    sub_account: SubAccountType = Field(..., description="GoHighLevel sub-account")

    # Tracking
    status: str = Field("open", description="Opportunity status")
    source: Optional[str] = Field(None, description="Opportunity source")
    close_date: Optional[datetime] = Field(None, description="Expected close date")

    # Custom fields
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom fields"
    )

    # Integration tracking
    notion_page_id: Optional[str] = Field(None, description="Notion page ID for sync")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    @validator("monetary_value")
    def validate_monetary_value(cls, v: Optional[float]) -> Optional[float]:
        """Validate monetary value is positive."""
        if v is not None and v < 0:
            raise ValueError("Monetary value must be positive")
        return v


class GHLCampaign(BaseModel):
    """GoHighLevel campaign model for marketing automation."""

    id: Optional[str] = Field(None, description="GoHighLevel campaign ID")
    name: str = Field(..., description="Campaign name")
    type: str = Field(..., description="Campaign type (email, sms, workflow)")
    status: str = Field("draft", description="Campaign status")

    # Business context
    business_types: List[BusinessType] = Field(..., description="Target business types")
    sub_account: SubAccountType = Field(..., description="GoHighLevel sub-account")

    # Campaign details
    description: Optional[str] = Field(None, description="Campaign description")
    start_date: Optional[datetime] = Field(None, description="Campaign start date")
    end_date: Optional[datetime] = Field(None, description="Campaign end date")

    # Performance metrics
    stats: Dict[str, Any] = Field(
        default_factory=dict, description="Campaign statistics"
    )
    target_contacts: List[str] = Field(
        default_factory=list, description="Target contact IDs"
    )

    # Integration tracking
    notion_page_id: Optional[str] = Field(None, description="Notion page ID for sync")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class GHLAppointment(BaseModel):
    """GoHighLevel appointment model for calendar management."""

    id: Optional[str] = Field(None, description="GoHighLevel appointment ID")
    title: str = Field(..., description="Appointment title")
    contact_id: str = Field(..., description="Associated contact ID")
    calendar_id: str = Field(..., description="Calendar ID")

    # Scheduling details
    start_time: datetime = Field(..., description="Appointment start time")
    end_time: datetime = Field(..., description="Appointment end time")
    timezone: str = Field("UTC", description="Timezone")

    # Business context
    business_type: BusinessType = Field(
        ..., description="Business type for this appointment"
    )
    sub_account: SubAccountType = Field(..., description="GoHighLevel sub-account")
    appointment_type: str = Field(..., description="Type of appointment")

    # Details
    description: Optional[str] = Field(None, description="Appointment description")
    location: Optional[str] = Field(None, description="Appointment location")
    status: str = Field("scheduled", description="Appointment status")

    # Integration tracking
    notion_page_id: Optional[str] = Field(None, description="Notion page ID for sync")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class GHLWebhookEvent(BaseModel):
    """GoHighLevel webhook event model."""

    id: str = Field(..., description="Event ID")
    type: str = Field(..., description="Event type")
    timestamp: datetime = Field(..., description="Event timestamp")
    location_id: str = Field(..., description="Location ID")

    # Event data
    data: Dict[str, Any] = Field(..., description="Event data payload")

    # Processing tracking
    processed: bool = Field(False, description="Whether event has been processed")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    error_message: Optional[str] = Field(
        None, description="Error message if processing failed"
    )


class GHLPipeline(BaseModel):
    """GoHighLevel pipeline configuration model."""

    id: Optional[str] = Field(None, description="Pipeline ID")
    name: str = Field(..., description="Pipeline name")
    business_type: BusinessType = Field(..., description="Associated business type")
    sub_account: SubAccountType = Field(..., description="GoHighLevel sub-account")

    # Pipeline configuration
    stages: List[Dict[str, Any]] = Field(..., description="Pipeline stages")
    custom_fields: List[Dict[str, Any]] = Field(
        default_factory=list, description="Custom fields"
    )

    # Integration tracking
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class GHLSyncStatus(BaseModel):
    """Model for tracking synchronization status between GoHighLevel and Notion."""

    entity_type: str = Field(
        ..., description="Type of entity (contact, opportunity, etc.)"
    )
    entity_id: str = Field(..., description="Entity ID")
    ghl_id: Optional[str] = Field(None, description="GoHighLevel ID")
    notion_id: Optional[str] = Field(None, description="Notion page ID")

    # Sync status
    last_sync: Optional[datetime] = Field(None, description="Last sync timestamp")
    sync_direction: str = Field(
        ..., description="Sync direction (ghl_to_notion, notion_to_ghl, bidirectional)"
    )
    sync_status: str = Field(
        "pending", description="Sync status (pending, success, error)"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if sync failed"
    )

    # Conflict resolution
    conflict_detected: bool = Field(
        False, description="Whether a sync conflict was detected"
    )
    conflict_resolution: Optional[str] = Field(
        None, description="How conflict was resolved"
    )
