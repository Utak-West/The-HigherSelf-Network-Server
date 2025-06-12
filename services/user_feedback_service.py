"""
UserFeedback service integration for The HigherSelf Network Server.
This service handles user feedback collection and processing while maintaining Notion as the central hub.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from pydantic import BaseModel, Field, field_validator

# Import base service
from services.base_service import BaseService, ServiceCredentials


class UserFeedbackCredentials(ServiceCredentials):
    """Credentials for UserFeedback service."""
    api_key: str
    webhook_secret: Optional[str] = None

    class Config:
        env_prefix = "USER_FEEDBACK_"

@field_validator('api_key', mode='before')
    def validate_required_fields(cls, v):
        if not v:
            raise ValueError("API key is required")
        return v


class UserFeedbackItem(BaseModel):
    """Model representing user feedback."""
    id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    feedback_type: str  # "suggestion", "bug", "comment", "rating"
    content: str
    rating: Optional[int] = None  # 1-5 if feedback_type is "rating"
    category: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    notion_page_id: Optional[str] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)

@field_validator('feedback_type', mode='before')
    def validate_feedback_type(cls, v):
        valid_types = ["suggestion", "bug", "comment", "rating"]
        if v not in valid_types:
            raise ValueError(f"Feedback type must be one of: {', '.join(valid_types)}")
        return v

@field_validator('rating', mode='before')
    def validate_rating(cls, v, values):
        if values.get('feedback_type') == "rating" and (v is None or not 1 <= v <= 5):
            raise ValueError("Rating must be between 1 and 5 for rating feedback type")
        return v

@field_validator('content', mode='before')
    def validate_content(cls, v):
        if not v:
            raise ValueError("Feedback content is required")
        if len(v) < 3:
            raise ValueError("Feedback content must be at least 3 characters")
        return v


class UserFeedbackService(BaseService):
    """
    Service for handling user feedback.
    Ensures all feedback data is synchronized with Notion as the central hub.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the UserFeedback service.

        Args:
            api_key: API key for UserFeedback service
        """
        # Get credentials from environment if not provided
        api_key = api_key or os.environ.get("USER_FEEDBACK_API_KEY")
        webhook_secret = os.environ.get("USER_FEEDBACK_WEBHOOK_SECRET")

        # Create credentials object
        credentials = None
        if api_key:
            credentials = UserFeedbackCredentials(
                service_name="user_feedback",
                api_key=api_key,
                webhook_secret=webhook_secret
            )

        # Initialize base service
        super().__init__(service_name="user_feedback", credentials=credentials)

        # Specific properties
        self.api_key = api_key
        self.base_url = os.environ.get("USER_FEEDBACK_API_URL", "https://api.userfeedback.example.com")

        if not self.api_key:
            logger.warning("UserFeedback API key not configured")

    async def validate_connection(self) -> bool:
        """
        Validate the UserFeedback API connection.

        Returns:
            True if connection is valid, False otherwise
        """
        if not self.api_key:
            logger.error("UserFeedback API key not configured")
            return False

        try:
            # Simple API call to validate connection
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await self.async_get(f"{self.base_url}/api/status", headers=headers)

            # Update credentials verification timestamp
            if self.credentials:
                self.credentials.last_verified = datetime.now()

            logger.info("UserFeedback connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"Error validating UserFeedback connection: {e}")
            return False

    async def submit_feedback(self, feedback: UserFeedbackItem) -> Optional[str]:
        """
        Submit user feedback to the service and create a Notion record.

        Args:
            feedback: UserFeedbackItem containing feedback details

        Returns:
            Feedback ID if successful, None otherwise
        """
        if not self.api_key:
            logger.error("UserFeedback API key not configured")
            return None

        try:
            # Validate feedback data
            self.validate_model(feedback)

            # Set creation timestamp if not provided
            if not feedback.created_at:
                feedback.created_at = datetime.now()

            # Prepare feedback data for API
            feedback_data = feedback.dict(exclude={"notion_page_id"})

            # Convert datetime to ISO format string for API
            if feedback.created_at:
                feedback_data["created_at"] = feedback.created_at.isoformat()

            # Submit feedback
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = await self.async_post(
                f"{self.base_url}/api/feedback",
                headers=headers,
                json=feedback_data
            )

            # Extract feedback ID
            feedback_id = response.get("id")

            if feedback_id:
                logger.info(f"Successfully submitted feedback: {feedback_id}")

                # If Notion integration is enabled, create Notion record
                if feedback.notion_page_id:
                    # Add metadata indicating this is managed by Notion
                    feedback.meta_data["notion_managed"] = True
                    feedback.meta_data["notion_sync_time"] = datetime.now().isoformat()

                    # Update feedback record with Notion ID
                    update_data = {
                        "meta_data": feedback.meta_data,
                        "notion_page_id": feedback.notion_page_id
                    }

                    await self.async_patch(
                        f"{self.base_url}/api/feedback/{feedback_id}",
                        headers=headers,
                        json=update_data
                    )

                    logger.info(f"Updated feedback {feedback_id} with Notion page ID")

                return feedback_id
            else:
                logger.error("Failed to submit feedback: No ID returned")
                return None
        except ValueError as e:
            # Handle validation errors
            logger.error(f"Validation error submitting feedback: {e}")
            return None
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return None

    async def get_feedback(self, feedback_id: str) -> Optional[UserFeedbackItem]:
        """
        Get feedback by ID.

        Args:
            feedback_id: ID of the feedback to retrieve

        Returns:
            UserFeedbackItem if found, None otherwise
        """
        if not self.api_key:
            logger.error("UserFeedback API key not configured")
            return None

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await self.async_get(f"{self.base_url}/api/feedback/{feedback_id}", headers=headers)

            # Extract Notion page ID if it exists
            notion_page_id = None
            if response.get("meta_data") and "notion_page_id" in response["meta_data"]:
                notion_page_id = response["meta_data"]["notion_page_id"]

            # Parse created_at if it exists
            created_at = None
            if response.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(response["created_at"].replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse created_at from feedback {feedback_id}")

            feedback = UserFeedbackItem(
                id=response.get("id"),
                user_id=response.get("user_id"),
                user_email=response.get("user_email"),
                feedback_type=response.get("feedback_type", "comment"),
                content=response.get("content", ""),
                rating=response.get("rating"),
                category=response.get("category"),
                source=response.get("source"),
                created_at=created_at,
                meta_data=response.get("meta_data", {}),
                notion_page_id=notion_page_id
            )

            return feedback
        except Exception as e:
            logger.error(f"Error getting feedback {feedback_id}: {e}")
            return None

    async def process_webhook(self, payload: Dict[str, Any], signature: Optional[str] = None) -> bool:
        """
        Process incoming webhook from UserFeedback service.

        Args:
            payload: Webhook payload
            signature: Webhook signature for verification

        Returns:
            True if processed successfully, False otherwise
        """
        try:
            # Verify webhook signature if provided and configured
            if signature and self.credentials and self.credentials.webhook_secret:
                if not self._verify_webhook_signature(payload, signature, self.credentials.webhook_secret):
                    logger.error("Invalid webhook signature")
                    return False

            event_type = payload.get("event")
            if not event_type:
                logger.error("Missing event type in webhook payload")
                return False

            data = payload.get("data", {})

            if event_type == "feedback.created":
                # Process new feedback
                feedback_id = data.get("id")
                if feedback_id:
                    logger.info(f"Processing new feedback: {feedback_id}")

                    # Get full feedback details
                    feedback = await self.get_feedback(feedback_id)
                    if feedback:
                        # Create Notion record for the feedback
                        notion_page_id = await self._create_notion_feedback_record(feedback)
                        if notion_page_id:
                            # Update feedback with Notion page ID
                            feedback.notion_page_id = notion_page_id
                            await self._update_feedback_with_notion_id(feedback_id, notion_page_id)
                            logger.info(f"Processed new feedback: {feedback_id}, Notion page: {notion_page_id}")
                            return True
                        else:
                            logger.warning(f"Failed to create Notion record for feedback: {feedback_id}")
                            return False

            elif event_type == "feedback.updated":
                # Process updated feedback
                feedback_id = data.get("id")
                if feedback_id:
                    logger.info(f"Processing updated feedback: {feedback_id}")

                    # Get full feedback details
                    feedback = await self.get_feedback(feedback_id)
                    if feedback:
                        # Check if we have a Notion page ID
                        if feedback.notion_page_id:
                            # Update the existing Notion record
                            success = await self._update_notion_feedback_record(feedback)
                            if success:
                                logger.info(f"Updated Notion record for feedback: {feedback_id}")
                                return True
                            else:
                                logger.warning(f"Failed to update Notion record for feedback: {feedback_id}")
                                return False
                        else:
                            # Create a new Notion record
                            notion_page_id = await self._create_notion_feedback_record(feedback)
                            if notion_page_id:
                                # Update feedback with Notion page ID
                                feedback.notion_page_id = notion_page_id
                                await self._update_feedback_with_notion_id(feedback_id, notion_page_id)
                                logger.info(f"Created Notion record for updated feedback: {feedback_id}")
                                return True
                            else:
                                logger.warning(f"Failed to create Notion record for updated feedback: {feedback_id}")
                                return False

            logger.warning(f"Unhandled webhook event type: {event_type}")
            return False
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return False

    def _verify_webhook_signature(self, payload: Dict[str, Any], signature: str, secret: str) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Webhook payload
            signature: Webhook signature
            secret: Webhook secret

        Returns:
            True if signature is valid, False otherwise
        """
        import hashlib
        import hmac

        # Convert payload to JSON string
        payload_str = json.dumps(payload, separators=(',', ':'))

        # Calculate expected signature
        expected_signature = hmac.new(
            key=secret.encode(),
            msg=payload_str.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)

    async def _create_notion_feedback_record(self, feedback: UserFeedbackItem) -> Optional[str]:
        """
        Create a new feedback record in Notion.

        Args:
            feedback: UserFeedbackItem to create in Notion

        Returns:
            Notion page ID if successful, None otherwise
        """
        try:
            from models.notion_db_models import FeedbackSurvey
            from services.notion_service import NotionService

            # Create Notion service
            notion_service = NotionService.from_env()

            # Create feedback survey record
            feedback_record = FeedbackSurvey(
                title=f"Feedback: {feedback.feedback_type.capitalize()}",
                feedback_type=feedback.feedback_type,
                content=feedback.content,
                rating=feedback.rating,
                category=feedback.category or "General",
                source=feedback.source or "UserFeedback API",
                user_email=feedback.user_email,
                user_id=feedback.user_id,
                external_id=feedback.id,
                status="New",
                created_at=feedback.created_at or datetime.now(),
                meta_data=feedback.meta_data
            )

            # Create page in Notion
            page_id = await notion_service.create_page(feedback_record)
            logger.info(f"Created Notion feedback record with page ID: {page_id}")

            return page_id
        except Exception as e:
            logger.error(f"Error creating Notion feedback record: {e}")
            return None

    async def _update_notion_feedback_record(self, feedback: UserFeedbackItem) -> bool:
        """
        Update an existing feedback record in Notion.

        Args:
            feedback: UserFeedbackItem to update in Notion

        Returns:
            True if successful, False otherwise
        """
        try:
            from models.notion_db_models import FeedbackSurvey
            from services.notion_service import NotionService

            if not feedback.notion_page_id:
                logger.warning("Cannot update Notion record: No notion_page_id provided")
                return False

            # Create Notion service
            notion_service = NotionService.from_env()

            # Get existing record
            existing_records = await notion_service.get_page(
                model_class=FeedbackSurvey,
                page_id=feedback.notion_page_id
            )

            if not existing_records:
                logger.warning(f"Notion page not found: {feedback.notion_page_id}")
                return False

            existing_record = existing_records

            # Update fields
            existing_record.feedback_type = feedback.feedback_type
            existing_record.content = feedback.content
            existing_record.rating = feedback.rating
            existing_record.category = feedback.category or existing_record.category
            existing_record.user_email = feedback.user_email or existing_record.user_email
            existing_record.meta_data = feedback.meta_data or existing_record.meta_data

            # Update page in Notion
            success = await notion_service.update_page(existing_record)
            if success:
                logger.info(f"Updated Notion feedback record: {feedback.notion_page_id}")
            else:
                logger.warning(f"Failed to update Notion feedback record: {feedback.notion_page_id}")

            return success
        except Exception as e:
            logger.error(f"Error updating Notion feedback record: {e}")
            return False

    async def _update_feedback_with_notion_id(self, feedback_id: str, notion_page_id: str) -> bool:
        """
        Update a feedback record with its Notion page ID.

        Args:
            feedback_id: ID of the feedback to update
            notion_page_id: Notion page ID to associate

        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare update data
            update_data = {
                "meta_data": {
                    "notion_managed": True,
                    "notion_page_id": notion_page_id,
                    "notion_sync_time": datetime.now().isoformat()
                }
            }

            # Update feedback record
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = await self.async_patch(
                f"{self.base_url}/api/feedback/{feedback_id}",
                headers=headers,
                json=update_data
            )

            if response and response.get("id") == feedback_id:
                logger.info(f"Updated feedback {feedback_id} with Notion page ID: {notion_page_id}")
                return True
            else:
                logger.warning(f"Failed to update feedback {feedback_id} with Notion page ID")
                return False
        except Exception as e:
            logger.error(f"Error updating feedback with Notion ID: {e}")
            return False
