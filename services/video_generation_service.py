"""
Video Generation Service for The HigherSelf Network Server.
Integrates with MoneyPrinterTurbo to generate high-quality short videos.
"""

import os
import json
import asyncio
import httpx
from typing import Dict, Any, List, Optional, Union
from loguru import logger
from pydantic import BaseModel, Field

from models.base import ApiPlatform


class VideoGenerationRequest(BaseModel):
    """Request model for video generation."""
    topic: str = Field(..., description="The main topic or keyword for the video")
    language: str = Field("en", description="Language for the video (en or zh)")
    voice_name: Optional[str] = Field(None, description="Voice to use for narration")
    video_resolution: str = Field("1080x1920", description="Video resolution (1080x1920 for portrait, 1920x1080 for landscape)")
    clip_duration: int = Field(5, description="Duration of each video clip in seconds")
    subtitle_font: Optional[str] = Field(None, description="Font to use for subtitles")
    subtitle_position: str = Field("bottom", description="Position of subtitles (top, middle, bottom)")
    subtitle_color: str = Field("#FFFFFF", description="Color of subtitles in hex format")
    subtitle_size: int = Field(40, description="Size of subtitle text")
    subtitle_stroke_width: float = Field(1.5, description="Width of subtitle text stroke/outline")
    background_music_volume: float = Field(0.1, description="Volume of background music (0.0-1.0)")
    custom_script: Optional[str] = Field(None, description="Custom script for the video (if not using AI generation)")
    business_entity_id: Optional[str] = Field(None, description="Business entity ID for tracking")


class VideoGenerationResponse(BaseModel):
    """Response model for video generation."""
    task_id: str = Field(..., description="ID of the video generation task")
    status: str = Field(..., description="Status of the video generation task")
    message: Optional[str] = Field(None, description="Additional message about the task")


class VideoTaskStatus(BaseModel):
    """Status model for video generation task."""
    task_id: str = Field(..., description="ID of the video generation task")
    status: str = Field(..., description="Status of the task (pending, processing, completed, failed)")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    video_url: Optional[str] = Field(None, description="URL to the generated video if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[str] = Field(None, description="Timestamp when the task was created")
    completed_at: Optional[str] = Field(None, description="Timestamp when the task was completed")


class VideoGenerationService:
    """
    Service for generating videos using MoneyPrinterTurbo.
    Maintains Notion as the central hub for all data and workflows.
    """
    
    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize the Video Generation Service.
        
        Args:
            api_url: URL of the MoneyPrinterTurbo API (defaults to environment variable)
        """
        self.api_url = api_url or os.environ.get("MONEYPRINTER_API_URL", "http://localhost:8080/api/v1")
        self.logger = logger.bind(service="VideoGenerationService")
        self.logger.info(f"Video Generation Service initialized with API URL: {self.api_url}")
    
    async def generate_video(self, request: VideoGenerationRequest) -> VideoGenerationResponse:
        """
        Generate a video using MoneyPrinterTurbo.
        
        Args:
            request: VideoGenerationRequest with video parameters
            
        Returns:
            VideoGenerationResponse with task ID and status
        """
        self.logger.info(f"Generating video for topic: {request.topic}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.api_url}/generate",
                    json=request.dict(exclude_none=True)
                )
                
                if response.status_code != 200:
                    self.logger.error(f"Error generating video: {response.text}")
                    return VideoGenerationResponse(
                        task_id="error",
                        status="failed",
                        message=f"API error: {response.text}"
                    )
                
                result = response.json()
                self.logger.info(f"Video generation task created: {result.get('task_id')}")
                
                return VideoGenerationResponse(
                    task_id=result.get("task_id"),
                    status="pending",
                    message="Video generation task created successfully"
                )
        except Exception as e:
            self.logger.error(f"Error generating video: {e}")
            return VideoGenerationResponse(
                task_id="error",
                status="failed",
                message=f"Service error: {str(e)}"
            )
    
    async def get_task_status(self, task_id: str) -> VideoTaskStatus:
        """
        Get the status of a video generation task.
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            VideoTaskStatus with current status and progress
        """
        self.logger.info(f"Checking status of video task: {task_id}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.api_url}/tasks/{task_id}/status")
                
                if response.status_code != 200:
                    self.logger.error(f"Error checking task status: {response.text}")
                    return VideoTaskStatus(
                        task_id=task_id,
                        status="error",
                        error=f"API error: {response.text}"
                    )
                
                result = response.json()
                
                return VideoTaskStatus(
                    task_id=task_id,
                    status=result.get("status", "unknown"),
                    progress=result.get("progress"),
                    video_url=result.get("video_url"),
                    error=result.get("error"),
                    created_at=result.get("created_at"),
                    completed_at=result.get("completed_at")
                )
        except Exception as e:
            self.logger.error(f"Error checking task status: {e}")
            return VideoTaskStatus(
                task_id=task_id,
                status="error",
                error=f"Service error: {str(e)}"
            )
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get a list of available voices for video narration.
        
        Returns:
            List of voice objects with name, language, and gender
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.api_url}/voices")
                
                if response.status_code != 200:
                    self.logger.error(f"Error getting available voices: {response.text}")
                    return []
                
                return response.json()
        except Exception as e:
            self.logger.error(f"Error getting available voices: {e}")
            return []
