"""
BetterMode integration models for The HigherSelf Network Server.
These models represent the data structures used for BetterMode integration.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class BetterModeIntegrationConfig(BaseModel):
    """Configuration for BetterMode integration."""

    api_token: str = Field(..., description="BetterMode API token")
    network_id: str = Field(..., description="BetterMode network ID")
    webhook_secret: Optional[str] = Field(
        None, description="Webhook secret for signature verification"
    )
    api_url: str = Field(
        "https://app.bettermode.com/api/graphql",
        description="BetterMode GraphQL API URL",
    )

    class Config:
        env_prefix = "BETTERMODE_"


class BetterModeSpaceType(str, Enum):
    """Types of spaces in BetterMode."""

    DISCUSSION = "discussion"
    ARTICLE = "article"
    QUESTION = "question"
    EVENT = "event"
    IDEATION = "ideation"
    REVIEW = "review"
    JOB = "job"
    CUSTOM = "custom"


class BetterModeMemberRole(str, Enum):
    """Member roles in BetterMode."""

    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"
    GUEST = "guest"


class BetterModeWebhookType(str, Enum):
    """Types of webhooks from BetterMode."""

    MEMBER_CREATED = "member.created"
    MEMBER_UPDATED = "member.updated"
    POST_CREATED = "post.created"
    POST_UPDATED = "post.updated"
    COMMENT_CREATED = "comment.created"
    COMMENT_UPDATED = "comment.updated"
    REACTION_CREATED = "reaction.created"
    REACTION_DELETED = "reaction.deleted"
    SPACE_CREATED = "space.created"
    SPACE_UPDATED = "space.updated"


class BetterModeMember(BaseModel):
    """Represents a member in BetterMode."""

    id: str = Field(..., description="BetterMode member ID")
    name: str = Field(..., description="Member's name")
    email: str = Field(..., description="Member's email")
    role: BetterModeMemberRole = Field(
        BetterModeMemberRole.MEMBER, description="Member's role"
    )
    joined_at: datetime = Field(..., description="When the member joined")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom profile fields"
    )

    # Fields for integration with HigherSelf Network
    member_id: str = Field(
        default_factory=lambda: f"MEMBER-{uuid4().hex[:8]}",
        description="HigherSelf Network member ID",
    )
    notion_page_id: Optional[str] = Field(None, description="Notion page ID")

    def to_community_member(self):
        """Convert to CommunityMember model for backward compatibility."""
        from models.notion_db_models_extended import CommunityMember

        return CommunityMember(
            member_id=self.member_id,
            member_name=self.name,
            member_email=self.email,
            join_date=self.joined_at,
            membership_level="Standard",  # Default mapping
            membership_status="Active",
            primary_platform="BetterMode",
            profile_link=f"https://app.bettermode.com/members/{self.id}",
            bettermode_member_id=self.id,
            custom_fields=self.custom_fields,
            notion_page_id=self.notion_page_id,
        )


class BetterModeSpace(BaseModel):
    """Represents a space in BetterMode."""

    id: str = Field(..., description="BetterMode space ID")
    name: str = Field(..., description="Space name")
    slug: str = Field(..., description="Space slug")
    description: Optional[str] = Field(None, description="Space description")
    type: BetterModeSpaceType = Field(..., description="Space type")
    created_at: datetime = Field(..., description="When the space was created")
    updated_at: datetime = Field(..., description="When the space was last updated")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom space fields"
    )


class BetterModePost(BaseModel):
    """Represents a post in BetterMode."""

    id: str = Field(..., description="BetterMode post ID")
    title: Optional[str] = Field(None, description="Post title")
    content: str = Field(..., description="Post content")
    author_id: str = Field(..., description="Author's BetterMode member ID")
    space_id: str = Field(..., description="BetterMode space ID")
    created_at: datetime = Field(..., description="When the post was created")
    updated_at: datetime = Field(..., description="When the post was last updated")
    published: bool = Field(True, description="Whether the post is published")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom post fields"
    )


class BetterModeComment(BaseModel):
    """Represents a comment in BetterMode."""

    id: str = Field(..., description="BetterMode comment ID")
    content: str = Field(..., description="Comment content")
    author_id: str = Field(..., description="Author's BetterMode member ID")
    post_id: str = Field(..., description="BetterMode post ID")
    created_at: datetime = Field(..., description="When the comment was created")
    updated_at: datetime = Field(..., description="When the comment was last updated")


class BetterModeReaction(BaseModel):
    """Represents a reaction in BetterMode."""

    id: str = Field(..., description="BetterMode reaction ID")
    type: str = Field(..., description="Reaction type (e.g., 'like', 'heart')")
    author_id: str = Field(..., description="Author's BetterMode member ID")
    target_id: str = Field(..., description="Target ID (post or comment)")
    target_type: str = Field(..., description="Target type ('Post' or 'Comment')")
    created_at: datetime = Field(..., description="When the reaction was created")


class BetterModeEvent(BaseModel):
    """Represents an event in BetterMode."""

    id: str = Field(..., description="BetterMode event ID")
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_time: datetime = Field(..., description="Event start time")
    end_time: Optional[datetime] = Field(None, description="Event end time")
    timezone: str = Field("UTC", description="Event timezone")
    location: Optional[str] = Field(None, description="Event location")
    organizer_id: str = Field(..., description="Organizer's BetterMode member ID")
    space_id: str = Field(..., description="BetterMode space ID")
    created_at: datetime = Field(..., description="When the event was created")
    updated_at: datetime = Field(..., description="When the event was last updated")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom event fields"
    )


class BetterModeWebhookPayload(BaseModel):
    """Represents a webhook payload from BetterMode."""

    event_type: BetterModeWebhookType = Field(..., description="Webhook event type")
    network_id: str = Field(..., description="BetterMode network ID")
    timestamp: datetime = Field(..., description="Webhook timestamp")
    data: Dict[str, Any] = Field(..., description="Webhook data")

    @validator("timestamp", pre=True)
    def parse_timestamp(cls, value):
        """Parse timestamp from string or int."""
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        elif isinstance(value, int):
            return datetime.fromtimestamp(value / 1000)
        return value
