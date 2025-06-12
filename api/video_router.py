"""
Video generation API router for The HigherSelf Network Server.
Provides endpoints for generating and managing videos using MoneyPrinterTurbo.
"""

import os
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from agents import Elan
from models.video_models import (VideoContent, VideoGenerationConfig,
                                 VideoStatus)


# API Models
class VideoGenerationRequest(BaseModel):
    """Request model for video generation."""

    topic: str = Field(..., description="The main topic or keyword for the video")
    language: str = Field("en", description="Language for the video (en or zh)")
    voice_name: Optional[str] = Field(None, description="Voice to use for narration")
    resolution: str = Field(
        "1080x1920",
        description="Video resolution (1080x1920 for portrait, 1920x1080 for landscape)",
    )
    clip_duration: int = Field(5, description="Duration of each video clip in seconds")
    subtitle_font: Optional[str] = Field(None, description="Font to use for subtitles")
    subtitle_position: str = Field(
        "bottom", description="Position of subtitles (top, middle, bottom)"
    )
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
        None, description="Custom script for the video (if not using AI generation)"
    )
    business_entity_id: str = Field(
        "the_connection_practice", description="Business entity ID for tracking"
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
                "business_entity_id": "the_connection_practice",
            }
        }


class VideoGenerationResponse(BaseModel):
    """Response model for video generation."""

    status: str = Field(..., description="Status of the request (success or error)")
    message: str = Field(..., description="Message describing the result")
    content_id: Optional[str] = Field(
        None, description="ID of the created video content in Notion"
    )
    task_id: Optional[str] = Field(None, description="ID of the video generation task")


class VideoStatusResponse(BaseModel):
    """Response model for video status."""

    status: str = Field(..., description="Status of the request (success or error)")
    content_id: str = Field(..., description="ID of the video content in Notion")
    video_status: str = Field(..., description="Status of the video generation")
    video_url: Optional[str] = Field(
        None, description="URL to the generated video if completed"
    )
    task_id: Optional[str] = Field(None, description="ID of the video generation task")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    message: Optional[str] = Field(
        None, description="Additional message about the status"
    )


# Create router
router = APIRouter(
    prefix="/api/videos",
    tags=["videos"],
    responses={404: {"description": "Not found"}},
)


# Authentication middleware
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key for protected endpoints."""
    api_key = os.environ.get("API_KEY")
    if not api_key:
        logger.warning("API_KEY environment variable not set")
        return

    if not x_api_key or x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


# Initialize Elan agent for video generation
elan_agent = None


async def get_elan_agent():
    """Get or initialize the Elan agent."""
    global elan_agent
    if elan_agent is None:
        elan_agent = Elan()
    return elan_agent


@router.post(
    "/generate",
    response_model=VideoGenerationResponse,
    dependencies=[Depends(verify_api_key)],
)
async def generate_video(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
    elan: Elan = Depends(get_elan_agent),
):
    """
    Generate a video using MoneyPrinterTurbo.

    This endpoint triggers the video generation process and returns immediately.
    The actual generation happens asynchronously in the background.
    """
    logger.info(f"Received video generation request for topic: {request.topic}")

    try:
        # Convert request to VideoGenerationConfig
        config = VideoGenerationConfig(
            topic=request.topic,
            language=request.language,
            voice_name=request.voice_name,
            resolution=request.resolution,
            clip_duration=request.clip_duration,
            subtitle_font=request.subtitle_font,
            subtitle_position=request.subtitle_position,
            subtitle_color=request.subtitle_color,
            subtitle_size=request.subtitle_size,
            subtitle_stroke_width=request.subtitle_stroke_width,
            background_music_volume=request.background_music_volume,
            custom_script=request.custom_script,
        )

        # Process in the background to avoid timeout
        result = await elan.process_event(
            event_type="generate_video",
            event_data={**request.dict(), "config": config.dict()},
        )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Unknown error")
            )

        return VideoGenerationResponse(
            status="success",
            message="Video generation started successfully",
            content_id=result.get("content_id"),
            task_id=result.get("task_id"),
        )
    except Exception as e:
        logger.error(f"Error generating video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{content_id}/status",
    response_model=VideoStatusResponse,
    dependencies=[Depends(verify_api_key)],
)
async def get_video_status(content_id: str, elan: Elan = Depends(get_elan_agent)):
    """
    Get the status of a video generation task.

    Args:
        content_id: ID of the video content in Notion
    """
    logger.info(f"Checking status of video content: {content_id}")

    try:
        result = await elan.process_event(
            event_type="get_video_status", event_data={"content_id": content_id}
        )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=404, detail=result.get("message", "Video content not found")
            )

        # Extract task status if available
        task_status = result.get("task_status", {})

        return VideoStatusResponse(
            status="success",
            content_id=content_id,
            video_status=result.get("video_status"),
            video_url=result.get("video_url"),
            task_id=result.get("task_id"),
            progress=task_status.get("progress"),
            message=task_status.get("error"),
        )
    except Exception as e:
        logger.error(f"Error getting video status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
