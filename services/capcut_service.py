"""
CapCut integration service for The HigherSelf Network Server.
This service handles integration with CapCut while maintaining Notion as the central hub.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import httpx
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from models.base import ApiPlatform
from models.capcut_models import (
    CapCutExportRequest,
    CapCutExportResponse,
    CapCutExportStatus,
    CapCutExportStatusResponse,
    CapCutVideoMetadata,
    CapCutWebhookPayload,
)
from models.video_models import VideoContent, VideoStatus
from services.base_service import BaseService, ServiceCredentials
from services.notion_service import NotionService
from utils.api_decorators import handle_async_api_errors


class CapCutConfig(BaseModel):
    """Configuration for CapCut API integration."""

    api_key: str
    api_secret: str
    base_url: str = "https://api.capcut.com/v1"
    webhook_secret: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        env_prefix = "CAPCUT_"


class CapCutService(BaseService):
    """
    Service for interacting with the CapCut API.
    Handles video export and status checking while maintaining Notion as the central hub.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        notion_service: Optional[NotionService] = None,
    ):
        """
        Initialize the CapCut service.

        Args:
            api_key: CapCut API key
            api_secret: CapCut API secret
            base_url: CapCut API base URL
            webhook_secret: Secret for validating CapCut webhooks
            notion_service: NotionService instance for data persistence
        """
        # Load config from environment if not provided
        self.api_key = api_key or os.environ.get("CAPCUT_API_KEY")
        self.api_secret = api_secret or os.environ.get("CAPCUT_API_SECRET")
        self.base_url = base_url or os.environ.get(
            "CAPCUT_BASE_URL", "https://api.capcut.com/v1"
        )
        self.webhook_secret = webhook_secret or os.environ.get("CAPCUT_WEBHOOK_SECRET")

        # Create credentials object
        credentials = ServiceCredentials(
            api_key=self.api_key,
            api_secret=self.api_secret,
            additional_params={
                "base_url": self.base_url,
                "webhook_secret": self.webhook_secret,
            },
        )

        # Initialize base service
        super().__init__(service_name="capcut", credentials=credentials)

        # Store NotionService instance
        self.notion_service = notion_service

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        if not self.api_key or not self.api_secret:
            logger.warning("CapCut API credentials not fully configured")
        else:
            logger.info("CapCut service initialized successfully")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    @handle_async_api_errors(api_name="capcut")
    async def export_video(self, request: CapCutExportRequest) -> CapCutExportResponse:
        """
        Export a video from CapCut.

        Args:
            request: Export request parameters

        Returns:
            Export response with status and export ID
        """
        logger.info(f"Exporting video from CapCut project: {request.project_id}")

        try:
            # Prepare request payload
            payload = {
                "project_id": request.project_id,
                "format": request.format,
                "quality": request.quality,
                "include_metadata": request.include_metadata,
                "watermark": request.watermark,
            }

            # Add callback URL if provided
            if request.callback_url:
                payload["callback_url"] = str(request.callback_url)

            # Make API request
            response = await self.client.post("/projects/export", json=payload)
            response.raise_for_status()
            data = response.json()

            # Create video content in Notion if NotionService is available
            content_id = None
            if self.notion_service:
                # Create a VideoContent object
                video_content = VideoContent(
                    title=f"CapCut Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    description=f"Video exported from CapCut project {request.project_id}",
                    content_type="VIDEO",
                    stage="IDEA",
                    business_entity_id=request.business_entity_id,
                    topic="CapCut Export",
                    resolution="1920x1080",  # Default, will be updated when export completes
                    video_status=VideoStatus.PENDING.value,
                    task_id=data.get("export_id"),
                    created_by="CapCut Integration",
                    platforms=["CapCut"],
                )

                # Save to Notion
                content_id = await self.notion_service.create_video_content(
                    video_content
                )
                logger.info(f"Created video content in Notion with ID: {content_id}")

            # Return response
            return CapCutExportResponse(
                status="success",
                message="Video export started successfully",
                export_id=data.get("export_id"),
                content_id=content_id,
                estimated_completion_time=datetime.fromisoformat(
                    data.get("estimated_completion_time")
                )
                if data.get("estimated_completion_time")
                else None,
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error exporting video: {e.response.status_code} - {e.response.text}"
            )
            return CapCutExportResponse(
                status="error",
                message=f"HTTP error: {e.response.status_code} - {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Error exporting video: {str(e)}")
            return CapCutExportResponse(status="error", message=f"Error: {str(e)}")

    @handle_async_api_errors(api_name="capcut")
    async def get_export_status(self, export_id: str) -> CapCutExportStatusResponse:
        """
        Check the status of a video export.

        Args:
            export_id: ID of the export task

        Returns:
            Export status response
        """
        logger.info(f"Checking status of CapCut export: {export_id}")

        try:
            # Make API request
            response = await self.client.get(f"/exports/{export_id}")
            response.raise_for_status()
            data = response.json()

            # Extract metadata if available
            metadata = None
            if data.get("metadata"):
                try:
                    metadata = CapCutVideoMetadata(**data.get("metadata"))
                except ValidationError as e:
                    logger.warning(f"Error parsing video metadata: {e}")

            # Get content ID from Notion if NotionService is available
            content_id = None
            if self.notion_service:
                # Query Notion for video content with this export ID as task_id
                content = await self.notion_service.find_video_content_by_task_id(
                    export_id
                )
                if content:
                    content_id = content.id

                    # Update video content if export is completed
                    if data.get(
                        "status"
                    ) == CapCutExportStatus.COMPLETED.value and data.get("video_url"):
                        # Update with video URL and metadata
                        updates = {
                            "video_url": data.get("video_url"),
                            "video_status": VideoStatus.COMPLETED.value,
                        }

                        # Add metadata if available
                        if metadata:
                            updates["title"] = (
                                metadata.title if metadata.title else content.title
                            )
                            updates["description"] = (
                                metadata.description
                                if metadata.description
                                else content.description
                            )
                            updates["duration"] = metadata.duration
                            updates[
                                "resolution"
                            ] = f"{metadata.width}x{metadata.height}"
                            updates["tags"] = metadata.tags

                        # Save updates to Notion
                        await self.notion_service.update_video_content(
                            content_id, updates
                        )
                        logger.info(
                            f"Updated video content in Notion with export results: {content_id}"
                        )

            # Return response
            return CapCutExportStatusResponse(
                status="success",
                export_id=export_id,
                export_status=CapCutExportStatus(data.get("status", "pending")),
                content_id=content_id,
                video_url=data.get("video_url"),
                progress=data.get("progress"),
                message=data.get("message"),
                metadata=metadata,
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error checking export status: {e.response.status_code} - {e.response.text}"
            )
            return CapCutExportStatusResponse(
                status="error",
                export_id=export_id,
                export_status=CapCutExportStatus.FAILED,
                message=f"HTTP error: {e.response.status_code} - {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Error checking export status: {str(e)}")
            return CapCutExportStatusResponse(
                status="error",
                export_id=export_id,
                export_status=CapCutExportStatus.FAILED,
                message=f"Error: {str(e)}",
            )

    async def process_webhook(
        self, payload: Dict[str, Any], signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a webhook from CapCut.

        Args:
            payload: Webhook payload
            signature: Webhook signature for verification

        Returns:
            Processed webhook data
        """
        logger.info(f"Processing CapCut webhook for export: {payload.get('export_id')}")

        try:
            # Verify signature if webhook_secret is configured
            if self.webhook_secret and signature:
                # Implement signature verification logic here
                pass

            # Parse webhook payload
            webhook_data = CapCutWebhookPayload(**payload)

            # Update video content in Notion if NotionService is available
            if self.notion_service:
                # Query Notion for video content with this export ID as task_id
                content = await self.notion_service.find_video_content_by_task_id(
                    webhook_data.export_id
                )
                if content:
                    # Update with video URL and status
                    updates = {
                        "video_status": VideoStatus.COMPLETED.value
                        if webhook_data.status == CapCutExportStatus.COMPLETED
                        else VideoStatus.FAILED.value
                    }

                    # Add video URL if available
                    if webhook_data.video_url:
                        updates["video_url"] = str(webhook_data.video_url)

                    # Add metadata if available
                    if webhook_data.metadata:
                        updates["title"] = (
                            webhook_data.metadata.title
                            if webhook_data.metadata.title
                            else content.title
                        )
                        updates["description"] = (
                            webhook_data.metadata.description
                            if webhook_data.metadata.description
                            else content.description
                        )
                        updates["duration"] = webhook_data.metadata.duration
                        updates[
                            "resolution"
                        ] = f"{webhook_data.metadata.width}x{webhook_data.metadata.height}"
                        updates["tags"] = webhook_data.metadata.tags

                    # Save updates to Notion
                    await self.notion_service.update_video_content(content.id, updates)
                    logger.info(
                        f"Updated video content in Notion from webhook: {content.id}"
                    )

            return {
                "status": "success",
                "message": "Webhook processed successfully",
                "export_id": webhook_data.export_id,
                "project_id": webhook_data.project_id,
                "export_status": webhook_data.status,
            }

        except ValidationError as e:
            logger.error(f"Error validating webhook payload: {e}")
            return {"status": "error", "message": f"Validation error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {"status": "error", "message": f"Error: {str(e)}"}
