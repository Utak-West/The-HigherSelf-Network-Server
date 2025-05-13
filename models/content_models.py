"""
Content data models for The HigherSelf Network.

These models support the ContentLifecycleAgent and maintain
Notion as the central hub for all content data.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Types of content handled by the ContentLifecycleAgent."""
    BLOG_POST = "blog_post"
    SOCIAL_MEDIA = "social_media"
    EMAIL_NEWSLETTER = "email_newsletter"
    VIDEO_SCRIPT = "video_script"
    PODCAST_SCRIPT = "podcast_script"
    COURSE_MATERIAL = "course_material"
    WORKSHOP_MATERIAL = "workshop_material"
    VIDEO = "video"


class ContentStage(str, Enum):
    """Stages in the content lifecycle workflow."""
    IDEA = "idea"
    RESEARCH = "research"
    DRAFT = "draft"
    REVIEW = "review"
    MEDIA_CREATION = "media_creation"
    FINAL = "final"
    READY = "ready"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentPlatform(str, Enum):
    """Distribution platforms for content."""
    WORDPRESS = "wordpress"
    BEEHIIV = "beehiiv"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    TUTORM = "tutorm"


class ContentRequest(BaseModel):
    """Model for a content creation request."""
    title: str
    content_type: ContentType
    brief: str
    audience: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    target_platforms: List[ContentPlatform] = Field(default_factory=list)
    required_media: bool = False
    target_completion_date: Optional[datetime] = None
    references: List[str] = Field(default_factory=list)
    additional_data: Dict[str, Any] = Field(default_factory=dict)


class ResearchData(BaseModel):
    """Model for content research data."""
    summary: str
    key_points: List[str] = Field(default_factory=list)
    sources: List[Dict[str, str]] = Field(default_factory=list)
    additional_data: Dict[str, Any] = Field(default_factory=dict)


class DistributionResult(BaseModel):
    """Model for content distribution results."""
    platform: ContentPlatform
    status: str
    url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContentPlanFrequency(BaseModel):
    """Model for content plan frequency settings."""
    blog_posts: int = 0
    social_media: int = 0
    email_newsletters: int = 0
    videos: int = 0
    podcasts: int = 0