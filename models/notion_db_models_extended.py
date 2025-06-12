"""
Extended Pydantic models that represent the complete 16-database Notion structure for The HigherSelf Network.
These models enable comprehensive automation flows and data management through Notion as the central hub.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, validator

from models.base import (ApiPlatform, ContentReviewStatus, EntityType,
                         NotificationChannel, TaskStatus)


class ContactProfile(BaseModel):
    """
    Represents a contact in the Contacts & Profiles DB.
    This is a core operational database for all contact information.
    """

    contact_id: str = Field(
        default_factory=lambda: f"CTCT-{uuid4().hex[:8]}",
        description="Unique contact ID",
    )
    full_name: str = Field(..., description="Contact's full name")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    contact_type: str = Field(
        "Lead", description="Contact type (Lead, Client, Partner, etc.)"
    )
    lead_source: Optional[str] = Field(None, description="Source of the lead")
    status: str = Field("Active Lead", description="Contact status")
    date_added: datetime = Field(default_factory=datetime.now, description="Date added")
    last_contacted_date: Optional[datetime] = Field(
        None, description="Last contacted date"
    )
    marketing_segments: List[str] = Field(
        default_factory=list, description="Marketing segments for targeting"
    )
    notes: Optional[str] = Field(None, description="Notes about the contact")
    communication_preferences: Dict[str, bool] = Field(
        default_factory=dict, description="Communication preferences"
    )
    related_business_entity: Optional[str] = Field(
        None, description="Related business entity ID"
    )
    engagement_score: Optional[int] = Field(
        None, description="Engagement score (0-100)"
    )

    # Additional fields for comprehensive contact tracking
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    address: Optional[str] = Field(None, description="Physical address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    country: Optional[str] = Field(None, description="Country")
    postal_code: Optional[str] = Field(None, description="Postal/ZIP code")
    company: Optional[str] = Field(None, description="Company name")
    job_title: Optional[str] = Field(None, description="Job title")

    # Notion-specific field
    page_id: Optional[str] = Field(None, description="Notion page ID")


class CommunityMember(BaseModel):
    """
    Represents a member in the Community Hub DB.
    This tracks community engagement and membership details.
    """

    member_id: str = Field(
        default_factory=lambda: f"MEMBER-{uuid4().hex[:8]}",
        description="Unique member ID",
    )
    member_name: str = Field(..., description="Member's name")
    member_email: str = Field(..., description="Member's email")
    join_date: datetime = Field(default_factory=datetime.now, description="Date joined")
    membership_level: str = Field("Standard", description="Membership level")
    membership_status: str = Field("Active", description="Active, Inactive, Pending")
    primary_platform: str = Field("Circle.so", description="Primary community platform")
    interest_groups: List[str] = Field(
        default_factory=list, description="Interest groups joined"
    )
    last_engagement_date: Optional[datetime] = Field(
        None, description="Last engagement date"
    )
    engagement_type: Optional[str] = Field(
        None, description="Last engagement type (post, comment, etc.)"
    )
    engagement_score: Optional[int] = Field(
        None, description="Engagement score (0-100)"
    )
    events_attended: List[str] = Field(
        default_factory=list, description="List of attended events"
    )
    profile_link: Optional[str] = Field(None, description="Link to member profile")
    notes: Optional[str] = Field(None, description="Notes about this member")
    related_contact: Optional[str] = Field(
        None, description="Related record in Contacts & Profiles DB"
    )

    # Notion-specific field
    page_id: Optional[str] = Field(None, description="Notion page ID")


class ProductService(BaseModel):
    """
    Represents a product or service in the Products & Services DB.
    This is the catalog database for all offerings.
    """

    product_id: str = Field(
        default_factory=lambda: f"PROD-{uuid4().hex[:8]}",
        description="Unique product/service ID",
    )
    name: str = Field(..., description="Product/service name")
    type: str = Field(
        ..., description="Type (e.g., Course, Retreat, Art, Consultation)"
    )
    description: str = Field(..., description="Detailed description")
    price: float = Field(..., description="Price in USD")
    status: str = Field("Active", description="Status (Active, Inactive, Coming Soon)")
    inventory_count: Optional[int] = Field(
        None, description="Inventory count for physical products"
    )
    business_entity: str = Field(..., description="Related business entity ID")
    integration_system: Optional[str] = Field(
        None, description="Integration system (Amelia, WooCommerce, etc.)"
    )
    external_id: Optional[str] = Field(None, description="ID in external system")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    booking_link: Optional[str] = Field(
        None, description="Direct link to book/purchase"
    )
    duration_minutes: Optional[int] = Field(
        None, description="Duration in minutes (for services)"
    )
    categories: List[str] = Field(
        default_factory=list, description="Categories for filtering"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for filtering")
    featured: bool = Field(
        False, description="Whether this is a featured product/service"
    )

    # Notion-specific field
    page_id: Optional[str] = Field(None, description="Notion page ID")


class MarketingCampaign(BaseModel):
    """
    Represents a marketing campaign in the Marketing Campaigns DB.
    This tracks all marketing initiatives and results.
    """

    campaign_id: str = Field(
        default_factory=lambda: f"CAMP-{uuid4().hex[:8]}",
        description="Unique campaign ID",
    )
    name: str = Field(..., description="Campaign name")
    description: str = Field(..., description="Campaign description and goals")
    type: str = Field(..., description="Type (Email, Social Media, Event, etc.)")
    status: str = Field(
        "Planning", description="Status (Planning, Active, Completed, Cancelled)"
    )
    business_entity: str = Field(..., description="Related business entity ID")
    target_contacts: Dict[str, Any] = Field(
        ..., description="Target segments definition"
    )
    channels: List[str] = Field(..., description="Marketing channels used")
    start_date: datetime = Field(..., description="Campaign start date")
    end_date: Optional[datetime] = Field(None, description="Campaign end date")
    budget: Optional[float] = Field(None, description="Campaign budget")
    actual_spend: Optional[float] = Field(None, description="Actual amount spent")
    leads_generated: Optional[int] = Field(
        None, description="Number of leads generated"
    )
    conversions: Optional[int] = Field(None, description="Number of conversions")
    related_notification_templates: List[str] = Field(
        default_factory=list, description="Related notification templates"
    )
    results_summary: Optional[str] = Field(
        None, description="Summary of campaign results"
    )
    url_parameters: Optional[str] = Field(
        None, description="UTM parameters for tracking"
    )

    # Notion-specific field
    page_id: Optional[str] = Field(None, description="Notion page ID")


class FeedbackSurvey(BaseModel):
    """
    Represents a feedback item in the Feedback & Surveys DB.
    This captures all customer feedback and survey responses.
    """

    feedback_id: str = Field(
        default_factory=lambda: f"FDBK-{uuid4().hex[:8]}",
        description="Unique feedback ID",
    )
    source: str = Field(..., description="Source (Userfeedback, Email, Survey, etc.)")
    contact: Optional[str] = Field(None, description="Related contact ID")
    related_product_service: Optional[str] = Field(
        None, description="Related product/service ID"
    )
    related_workflow_instance: Optional[str] = Field(
        None, description="Related workflow instance ID"
    )
    date_received: datetime = Field(
        default_factory=datetime.now, description="Date received"
    )
    feedback_content: str = Field(..., description="Full text of feedback")
    rating: Optional[int] = Field(None, description="Numerical rating (e.g., 1-5)")
    sentiment: Optional[str] = Field(
        None, description="Sentiment analysis (Positive, Neutral, Negative)"
    )
    status: str = Field("New", description="Processing status")
    response_required: bool = Field(False, description="Whether a response is required")
    response_content: Optional[str] = Field(None, description="Response content")
    responded_by: Optional[str] = Field(None, description="Who responded")
    response_date: Optional[datetime] = Field(None, description="Date responded")
    action_items: List[str] = Field(
        default_factory=list, description="Action items from feedback"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

    # Notion-specific field
    page_id: Optional[str] = Field(None, description="Notion page ID")


class RewardBounty(BaseModel):
    """
    Represents an item in the Rewards & Bounties DB.
    This tracks customer rewards, referral bounties, and partner commissions.
    """

    reward_id: str = Field(
        default_factory=lambda: f"RWD-{uuid4().hex[:8]}", description="Unique reward ID"
    )
    name: str = Field(..., description="Reward name")
    type: str = Field(
        ..., description="Type (Referral, Commission, Loyalty Reward, etc.)"
    )
    status: str = Field("Active", description="Status (Active, Claimed, Expired)")
    recipient: Optional[str] = Field(None, description="Recipient contact ID")
    business_entity: str = Field(..., description="Related business entity ID")
    amount: Optional[float] = Field(None, description="Monetary value (if applicable)")
    description: str = Field(..., description="Reward description")
    qualifying_action: str = Field(
        ..., description="Action that qualifies for the reward"
    )
    expiration_date: Optional[datetime] = Field(None, description="Expiration date")
    claimed_date: Optional[datetime] = Field(None, description="Date claimed")
    related_transaction: Optional[str] = Field(
        None, description="Related transaction ID"
    )
    related_product_service: Optional[str] = Field(
        None, description="Related product/service ID"
    )
    notes: Optional[str] = Field(None, description="Additional notes")

    # Notion-specific field
    page_id: Optional[str] = Field(None, description="Notion page ID")
