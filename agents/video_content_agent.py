"""
Video Content Agent extension for Elan (Content Choreographer).
Integrates with MoneyPrinterTurbo to generate high-quality short videos.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from models.base import AgentCapability, ApiPlatform
from models.content_models import ContentPlatform, ContentStage, ContentType
from models.notion_db_models import WorkflowInstance
from models.video_models import (VideoContent, VideoGenerationConfig,
                                 VideoResolution, VideoStatus)
from services.notion_service import NotionService
from services.video_generation_service import (VideoGenerationRequest,
                                               VideoGenerationService)


class VideoContentAgent:
    """
    Extension for Elan (Content Choreographer) to handle video content generation.
    Uses MoneyPrinterTurbo for video generation while maintaining Notion as the central hub.
    """

    def __init__(self, notion_service: Optional[NotionService] = None):
        """
        Initialize the Video Content Agent extension.

        Args:
            notion_service: NotionService instance for data storage
        """
        self.logger = logger.bind(agent="VideoContentAgent")
        self._notion_service = notion_service
        self.video_service = VideoGenerationService()
        self.logger.info("Video Content Agent extension initialized")

    @property
    async def notion_service(self) -> NotionService:
        """Get or create the Notion service."""
        if self._notion_service is None:
            self._notion_service = NotionService.from_env()
        return self._notion_service

    async def generate_video(
        self, config: VideoGenerationConfig, business_entity_id: str
    ) -> Dict[str, Any]:
        """
        Generate a video using MoneyPrinterTurbo.

        Args:
            config: VideoGenerationConfig with generation parameters
            business_entity_id: Business entity ID for tracking

        Returns:
            Dict containing processing results and video content ID
        """
        self.logger.info(f"Generating video for topic: {config.topic}")

        # Create video content record in Notion (central hub)
        notion_svc = await self.notion_service

        video_content = VideoContent(
            title=f"Video: {config.topic}",
            description=f"AI-generated video about {config.topic}",
            content_type=ContentType.VIDEO.value,
            stage=ContentStage.DRAFT.value,
            business_entity_id=business_entity_id,
            topic=config.topic,
            resolution=config.resolution,
            video_status=VideoStatus.PENDING.value,
            created_by="Elan",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=[config.topic.lower()],
            platforms=["Instagram", "YouTube"],
            voice_name=config.voice_name,
            subtitle_settings={
                "font": config.subtitle_font,
                "position": config.subtitle_position,
                "color": config.subtitle_color,
                "size": config.subtitle_size,
                "stroke_width": config.subtitle_stroke_width,
            },
        )

        # Store in Notion as the central hub
        content_id = await notion_svc.create_page(video_content)

        if not content_id:
            return {
                "status": "error",
                "message": "Failed to create video content record in Notion",
            }

        # Prepare request for MoneyPrinterTurbo
        video_request = VideoGenerationRequest(
            topic=config.topic,
            language=config.language,
            voice_name=config.voice_name,
            video_resolution=config.resolution,
            clip_duration=config.clip_duration,
            subtitle_font=config.subtitle_font,
            subtitle_position=config.subtitle_position,
            subtitle_color=config.subtitle_color,
            subtitle_size=config.subtitle_size,
            subtitle_stroke_width=config.subtitle_stroke_width,
            background_music_volume=config.background_music_volume,
            custom_script=config.custom_script,
            business_entity_id=business_entity_id,
        )

        # Send request to MoneyPrinterTurbo
        response = await self.video_service.generate_video(video_request)

        if response.status != "pending":
            # Update Notion with error status
            await notion_svc.update_page(
                VideoContent, content_id, {"video_status": VideoStatus.FAILED.value}
            )

            return {
                "status": "error",
                "message": response.message,
                "content_id": content_id,
            }

        # Update Notion with task ID
        await notion_svc.update_page(
            VideoContent,
            content_id,
            {
                "task_id": response.task_id,
                "video_status": VideoStatus.GENERATING_SCRIPT.value,
            },
        )

        # Start background task to monitor video generation
        asyncio.create_task(
            self._monitor_video_generation(content_id, response.task_id)
        )

        return {
            "status": "success",
            "message": "Video generation started",
            "content_id": content_id,
            "task_id": response.task_id,
        }

    async def _monitor_video_generation(self, content_id: str, task_id: str) -> None:
        """
        Monitor the status of a video generation task.
        Updates Notion (central hub) with current status.

        Args:
            content_id: Notion page ID for the video content
            task_id: MoneyPrinterTurbo task ID
        """
        notion_svc = await self.notion_service
        completed = False

        while not completed:
            try:
                # Check task status
                status = await self.video_service.get_task_status(task_id)

                # Map status to VideoStatus enum
                video_status = VideoStatus.PENDING.value
                if status.status == "processing":
                    # Determine more specific status based on progress
                    if status.progress and status.progress < 25:
                        video_status = VideoStatus.GENERATING_SCRIPT.value
                    elif status.progress and status.progress < 50:
                        video_status = VideoStatus.COLLECTING_MEDIA.value
                    elif status.progress and status.progress < 75:
                        video_status = VideoStatus.GENERATING_AUDIO.value
                    else:
                        video_status = VideoStatus.RENDERING.value
                elif status.status == "completed":
                    video_status = VideoStatus.COMPLETED.value
                    completed = True
                elif status.status == "failed":
                    video_status = VideoStatus.FAILED.value
                    completed = True

                # Update Notion with current status
                update_data = {"video_status": video_status}

                # If completed, add video URL
                if completed and status.video_url:
                    update_data["video_url"] = status.video_url
                    update_data["stage"] = ContentStage.READY.value

                await notion_svc.update_page(VideoContent, content_id, update_data)

                if completed:
                    self.logger.info(
                        f"Video generation completed for content ID: {content_id}"
                    )
                    break

                # Wait before checking again
                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"Error monitoring video generation: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def get_video_status(self, content_id: str) -> Dict[str, Any]:
        """
        Get the status of a video generation task.

        Args:
            content_id: Notion page ID for the video content

        Returns:
            Dict containing status information
        """
        notion_svc = await self.notion_service

        # Get video content from Notion (central hub)
        video_content = await notion_svc.get_page(VideoContent, content_id)

        if not video_content:
            return {
                "status": "error",
                "message": f"Video content not found: {content_id}",
            }

        # If we have a task ID, get the latest status from MoneyPrinterTurbo
        if video_content.task_id:
            try:
                task_status = await self.video_service.get_task_status(
                    video_content.task_id
                )

                return {
                    "status": "success",
                    "content_id": content_id,
                    "task_id": video_content.task_id,
                    "video_status": video_content.video_status,
                    "video_url": video_content.video_url,
                    "task_status": task_status.dict(),
                }
            except Exception as e:
                self.logger.error(f"Error getting task status: {e}")

        # Return basic status from Notion
        return {
            "status": "success",
            "content_id": content_id,
            "task_id": video_content.task_id,
            "video_status": video_content.video_status,
            "video_url": video_content.video_url,
        }
