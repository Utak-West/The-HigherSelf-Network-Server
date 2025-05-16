"""
CapCut integration models for The HigherSelf Network Server.
These models define the data structures for interacting with the CapCut API.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

from models.base import ApiPlatform
from models.content_models import ContentType, ContentStage


class CapCutVideoFormat(str, Enum):
    """Video format options from CapCut."""
    MP4 = "mp4"
    MOV = "mov"
    AVI = "avi"
    WEBM = "webm"


class CapCutVideoQuality(str, Enum):
    """Video quality options from CapCut."""
    SD = "sd"  # Standard Definition
    HD = "hd"  # High Definition (720p)
    FULL_HD = "full_hd"  # Full HD (1080p)
    ULTRA_HD = "ultra_hd"  # Ultra HD (4K)


class CapCutExportStatus(str, Enum):
    """Status of a video export from CapCut."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CapCutVideoMetadata(BaseModel):
    """Metadata for a video exported from CapCut."""
    title: str = Field(..., description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    duration: float = Field(..., description="Video duration in seconds")
    width: int = Field(..., description="Video width in pixels")
    height: int = Field(..., description="Video height in pixels")
    format: CapCutVideoFormat = Field(..., description="Video format")
    quality: CapCutVideoQuality = Field(..., description="Video quality")
    frame_rate: float = Field(..., description="Video frame rate")
    size_bytes: int = Field(..., description="Video file size in bytes")
    created_at: datetime = Field(..., description="Creation timestamp")
    tags: List[str] = Field(default_factory=list, description="Video tags")
    effects: List[str] = Field(default_factory=list, description="Applied effects")
    audio_tracks: List[str] = Field(default_factory=list, description="Audio tracks used")
    custom_properties: Optional[Dict[str, Any]] = Field(None, description="Custom properties")


class CapCutExportRequest(BaseModel):
    """Request model for exporting a video from CapCut."""
    project_id: str = Field(..., description="CapCut project ID")
    format: CapCutVideoFormat = Field(CapCutVideoFormat.MP4, description="Export format")
    quality: CapCutVideoQuality = Field(CapCutVideoQuality.FULL_HD, description="Export quality")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook callback URL")
    business_entity_id: str = Field(..., description="Business entity ID for tracking")
    include_metadata: bool = Field(True, description="Whether to include metadata")
    watermark: bool = Field(False, description="Whether to include watermark")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "project_id": "cc-proj-123456789",
                "format": "mp4",
                "quality": "full_hd",
                "callback_url": "https://api.thehigherself.network/api/capcut/webhook",
                "business_entity_id": "the_connection_practice",
                "include_metadata": True,
                "watermark": False
            }
        }


class CapCutExportResponse(BaseModel):
    """Response model for a CapCut export request."""
    status: str = Field(..., description="Status of the request (success or error)")
    message: str = Field(..., description="Message describing the result")
    export_id: Optional[str] = Field(None, description="ID of the export task")
    content_id: Optional[str] = Field(None, description="ID of the created video content in Notion")
    estimated_completion_time: Optional[datetime] = Field(None, description="Estimated completion time")


class CapCutExportStatusResponse(BaseModel):
    """Response model for checking the status of a CapCut export."""
    status: str = Field(..., description="Status of the request (success or error)")
    export_id: str = Field(..., description="ID of the export task")
    export_status: CapCutExportStatus = Field(..., description="Status of the export")
    content_id: Optional[str] = Field(None, description="ID of the video content in Notion")
    video_url: Optional[HttpUrl] = Field(None, description="URL to the exported video if completed")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Additional message about the status")
    metadata: Optional[CapCutVideoMetadata] = Field(None, description="Video metadata if available")


class CapCutWebhookPayload(BaseModel):
    """Webhook payload from CapCut for export status updates."""
    export_id: str = Field(..., description="ID of the export task")
    project_id: str = Field(..., description="CapCut project ID")
    status: CapCutExportStatus = Field(..., description="Status of the export")
    video_url: Optional[HttpUrl] = Field(None, description="URL to the exported video if completed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[CapCutVideoMetadata] = Field(None, description="Video metadata if available")
    timestamp: datetime = Field(..., description="Timestamp of the webhook event")
