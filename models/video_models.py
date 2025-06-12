"""
Video content models for The HigherSelf Network Server.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from models.content_models import ContentStage, ContentType


class VideoResolution(str, Enum):
    """Video resolution options."""

    PORTRAIT = "1080x1920"  # 9:16 aspect ratio for mobile/social
    LANDSCAPE = "1920x1080"  # 16:9 aspect ratio for YouTube/web


class VideoStatus(str, Enum):
    """Status of a video in the generation process."""

    PENDING = "pending"
    GENERATING_SCRIPT = "generating_script"
    COLLECTING_MEDIA = "collecting_media"
    GENERATING_AUDIO = "generating_audio"
    GENERATING_SUBTITLES = "generating_subtitles"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoContent(BaseModel):
    """Model for video content in Notion."""

    id: Optional[str] = Field(None, description="Notion page ID")
    title: str = Field(..., description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    content_type: str = Field(
        ContentType.VIDEO.value, description="Content type (always VIDEO)"
    )
    stage: str = Field(
        ContentStage.IDEA.value, description="Current stage in the content lifecycle"
    )
    business_entity_id: str = Field(..., description="Business entity ID")
    topic: str = Field(..., description="Main topic or keyword for the video")
    script: Optional[str] = Field(None, description="Video script/narration")
    resolution: str = Field(
        VideoResolution.PORTRAIT.value, description="Video resolution"
    )
    duration: Optional[float] = Field(None, description="Video duration in seconds")
    video_status: str = Field(
        VideoStatus.PENDING.value, description="Status of video generation"
    )
    task_id: Optional[str] = Field(None, description="MoneyPrinterTurbo task ID")
    video_url: Optional[str] = Field(None, description="URL to the generated video")
    thumbnail_url: Optional[str] = Field(None, description="URL to the video thumbnail")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator (agent or user)")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    platforms: List[str] = Field(
        default_factory=list, description="Target platforms for distribution"
    )
    voice_name: Optional[str] = Field(None, description="Voice used for narration")
    subtitle_settings: Optional[Dict[str, Any]] = Field(
        None, description="Subtitle configuration"
    )
    background_music: Optional[str] = Field(None, description="Background music used")

    class Config:
        """Pydantic configuration."""

        schema_extra = {
            "example": {
                "title": "Mindfulness Meditation Techniques",
                "description": "A short video explaining basic mindfulness meditation techniques",
                "content_type": "VIDEO",
                "stage": "IDEA",
                "business_entity_id": "the_connection_practice",
                "topic": "mindfulness meditation",
                "resolution": "1080x1920",
                "video_status": "PENDING",
                "created_by": "Elan",
                "tags": ["meditation", "mindfulness", "wellness"],
                "platforms": ["Instagram", "YouTube"],
            }
        }


class VideoGenerationConfig(BaseModel):
    """Configuration for video generation."""

    topic: str = Field(..., description="Main topic or keyword for the video")
    language: str = Field("en", description="Language for the video (en or zh)")
    voice_name: Optional[str] = Field(None, description="Voice to use for narration")
    resolution: str = Field(
        VideoResolution.PORTRAIT.value, description="Video resolution"
    )
    clip_duration: int = Field(5, description="Duration of each video clip in seconds")
    subtitle_font: Optional[str] = Field(None, description="Font to use for subtitles")
    subtitle_position: str = Field("bottom", description="Position of subtitles")
    subtitle_color: str = Field(
        "#FFFFFF", description="Color of subtitles in hex format"
    )
    subtitle_size: int = Field(40, description="Size of subtitle text")
    subtitle_stroke_width: float = Field(
        1.5, description="Width of subtitle text stroke/outline"
    )
    background_music_volume: float = Field(
        0.1, description="Volume of background music (0.0-1.0)"
    )
    custom_script: Optional[str] = Field(
        None, description="Custom script for the video"
    )

    class Config:
        """Pydantic configuration."""

        schema_extra = {
            "example": {
                "topic": "mindfulness meditation",
                "language": "en",
                "voice_name": "en-US-JennyNeural",
                "resolution": "1080x1920",
                "clip_duration": 5,
                "subtitle_position": "bottom",
                "subtitle_color": "#FFFFFF",
                "subtitle_size": 40,
                "subtitle_stroke_width": 1.5,
                "background_music_volume": 0.1,
            }
        }
