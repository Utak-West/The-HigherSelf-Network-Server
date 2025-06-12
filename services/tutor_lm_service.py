"""
TutorLM service integration for The HigherSelf Network Server.
This service handles AI tutoring functionalities while maintaining Notion as the central hub.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from pydantic import BaseModel, Field, field_validator

# Import base service
from services.base_service import BaseService, ServiceCredentials


class TutorLMCredentials(ServiceCredentials):
    """Credentials for TutorLM service."""
    api_key: str
    organization_id: Optional[str] = None

    class Config:
        env_prefix = "TUTOR_LM_"

@field_validator('api_key', mode='before')
    def validate_required_fields(cls, v):
        if not v:
            raise ValueError("API key is required")
        return v


class TutorSession(BaseModel):
    """Model representing a tutoring session."""
    id: Optional[str] = None
    student_id: Optional[str] = None
    student_email: Optional[str] = None
    topic: str
    subject_area: str
    difficulty_level: str = "intermediate"  # beginner, intermediate, advanced, expert
    duration_minutes: int = 30
    session_date: Optional[datetime] = None
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    session_notes: Optional[str] = None
    tutor_feedback: Optional[str] = None
    student_feedback: Optional[str] = None
    notion_page_id: Optional[str] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)

@field_validator('topic', 'subject_area', mode='before')
    def validate_required_text(cls, v, values, **kwargs):
        if not v:
            field_name = kwargs.get('field', 'This field')
            raise ValueError(f"{field_name} is required")
        return v

@field_validator('difficulty_level', mode='before')
    def validate_difficulty(cls, v):
        valid_levels = ["beginner", "intermediate", "advanced", "expert"]
        if v not in valid_levels:
            raise ValueError(f"Difficulty level must be one of: {', '.join(valid_levels)}")
        return v

@field_validator('duration_minutes', mode='before')
    def validate_duration(cls, v):
        if v < 15 or v > 120:
            raise ValueError("Duration must be between 15 and 120 minutes")
        return v

@field_validator('status', mode='before')
    def validate_status(cls, v):
        valid_statuses = ["scheduled", "in_progress", "completed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class TutorLMService(BaseService):
    """
    Service for interacting with TutorLM AI tutoring platform.
    Ensures all data is synchronized with Notion as the central hub.
    """

    def __init__(self, api_key: str = None, organization_id: str = None):
        """
        Initialize the TutorLM service.

        Args:
            api_key: API key for TutorLM
            organization_id: Organization ID for TutorLM (optional)
        """
        # Get credentials from environment if not provided
        api_key = api_key or os.environ.get("TUTOR_LM_API_KEY")
        organization_id = organization_id or os.environ.get("TUTOR_LM_ORGANIZATION_ID")

        # Create credentials object
        credentials = None
        if api_key:
            credentials = TutorLMCredentials(
                service_name="tutor_lm",
                api_key=api_key,
                organization_id=organization_id
            )

        # Initialize base service
        super().__init__(service_name="tutor_lm", credentials=credentials)

        # Specific properties
        self.api_key = api_key
        self.organization_id = organization_id
        self.base_url = os.environ.get("TUTOR_LM_API_URL", "https://api.tutorlm.example.com")

        if not self.api_key:
            logger.warning("TutorLM API key not configured")

    async def validate_connection(self) -> bool:
        """
        Validate the TutorLM API connection.

        Returns:
            True if connection is valid, False otherwise
        """
        if not self.api_key:
            logger.error("TutorLM API key not configured")
            return False

        try:
            # Create authorization headers
            headers = self._get_headers()

            # Test connection with a simple API call
            response = await self.async_get(f"{self.base_url}/api/status", headers=headers)

            # Update credentials verification timestamp
            if self.credentials:
                self.credentials.last_verified = datetime.now()

            logger.info("TutorLM connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"Error validating TutorLM connection: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for TutorLM API requests.

        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if self.organization_id:
            headers["X-Organization-ID"] = self.organization_id

        return headers

    async def create_session(self, session: TutorSession) -> Optional[str]:
        """
        Create a new tutoring session.

        Args:
            session: TutorSession model with session details

        Returns:
            Session ID if successful, None otherwise
        """
        if not self.api_key:
            logger.error("TutorLM API key not configured")
            return None

        try:
            # Validate session data
            self.validate_model(session)

            # Set session date if not provided
            if not session.session_date:
                session.session_date = datetime.now()

            # Prepare session data
            session_data = session.dict(exclude={"notion_page_id"})

            # Convert datetime to ISO format string for API
            if session.session_date:
                session_data["session_date"] = session.session_date.isoformat()

            # Create session
            headers = self._get_headers()

            response = await self.async_post(
                f"{self.base_url}/api/sessions",
                headers=headers,
                json=session_data
            )

            # Extract session ID
            session_id = response.get("id")

            if session_id:
                logger.info(f"Successfully created tutoring session: {session_id}")

                # If Notion integration is enabled, update TutorLM record
                if session.notion_page_id:
                    # Add metadata indicating this is managed by Notion
                    session.meta_data["notion_managed"] = True
                    session.meta_data["notion_sync_time"] = datetime.now().isoformat()

                    # Update session with Notion page ID
                    update_data = {
                        "meta_data": session.meta_data,
                        "notion_page_id": session.notion_page_id
                    }

                    await self.async_patch(
                        f"{self.base_url}/api/sessions/{session_id}",
                        headers=headers,
                        json=update_data
                    )

                    logger.info(f"Updated session {session_id} with Notion page ID")

                return session_id
            else:
                logger.error("Failed to create tutoring session: No ID returned")
                return None
        except ValueError as e:
            # Handle validation errors
            logger.error(f"Validation error creating tutoring session: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating tutoring session: {e}")
            return None

    async def get_session(self, session_id: str) -> Optional[TutorSession]:
        """
        Get a tutoring session by ID.

        Args:
            session_id: ID of the session to retrieve

        Returns:
            TutorSession if found, None otherwise
        """
        if not self.api_key:
            logger.error("TutorLM API key not configured")
            return None

        try:
            headers = self._get_headers()
            response = await self.async_get(f"{self.base_url}/api/sessions/{session_id}", headers=headers)

            # Extract Notion page ID if it exists
            notion_page_id = None
            if response.get("meta_data") and "notion_page_id" in response["meta_data"]:
                notion_page_id = response["meta_data"]["notion_page_id"]

            # Parse session date if it exists
            session_date = None
            if response.get("session_date"):
                try:
                    session_date = datetime.fromisoformat(response["session_date"].replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse session_date from session {session_id}")

            session = TutorSession(
                id=response.get("id"),
                student_id=response.get("student_id"),
                student_email=response.get("student_email"),
                topic=response.get("topic", ""),
                subject_area=response.get("subject_area", ""),
                difficulty_level=response.get("difficulty_level", "intermediate"),
                duration_minutes=response.get("duration_minutes", 30),
                session_date=session_date,
                status=response.get("status", "scheduled"),
                session_notes=response.get("session_notes"),
                tutor_feedback=response.get("tutor_feedback"),
                student_feedback=response.get("student_feedback"),
                meta_data=response.get("meta_data", {}),
                notion_page_id=notion_page_id
            )

            return session
        except Exception as e:
            logger.error(f"Error getting tutoring session {session_id}: {e}")
            return None

    async def update_session_status(self, session_id: str, status: str, notes: Optional[str] = None) -> bool:
        """
        Update a tutoring session status.

        Args:
            session_id: ID of the session to update
            status: New status (scheduled, in_progress, completed, cancelled)
            notes: Optional session notes

        Returns:
            True if updated successfully, False otherwise
        """
        if not self.api_key:
            logger.error("TutorLM API key not configured")
            return False

        try:
            # Validate status
            valid_statuses = ["scheduled", "in_progress", "completed", "cancelled"]
            if status not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

            # Prepare update data
            update_data = {"status": status}
            if notes:
                update_data["session_notes"] = notes

            # Update session
            headers = self._get_headers()

            await self.async_patch(
                f"{self.base_url}/api/sessions/{session_id}",
                headers=headers,
                json=update_data
            )

            logger.info(f"Updated session {session_id} status to {status}")
            return True
        except ValueError as e:
            # Handle validation errors
            logger.error(f"Validation error updating session status: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating session status: {e}")
            return False

    async def list_sessions(self,
                           student_id: Optional[str] = None,
                           status: Optional[str] = None,
                           from_date: Optional[datetime] = None,
                           to_date: Optional[datetime] = None,
                           limit: int = 100) -> List[TutorSession]:
        """
        List tutoring sessions with optional filters.

        Args:
            student_id: Filter by student ID
            status: Filter by status
            from_date: Filter by sessions after this date
            to_date: Filter by sessions before this date
            limit: Maximum number of sessions to return

        Returns:
            List of TutorSession objects
        """
        if not self.api_key:
            logger.error("TutorLM API key not configured")
            return []

        try:
            # Build query params
            params = {"limit": limit}

            if student_id:
                params["student_id"] = student_id

            if status:
                params["status"] = status

            if from_date:
                params["from_date"] = from_date.isoformat()

            if to_date:
                params["to_date"] = to_date.isoformat()

            # Make API request
            headers = self._get_headers()
            response = await self.async_get(
                f"{self.base_url}/api/sessions",
                headers=headers,
                params=params
            )

            # Process response
            sessions = []
            for session_data in response.get("sessions", []):
                # Extract Notion page ID if it exists
                notion_page_id = None
                if session_data.get("meta_data") and "notion_page_id" in session_data["meta_data"]:
                    notion_page_id = session_data["meta_data"]["notion_page_id"]

                # Parse session date if it exists
                session_date = None
                if session_data.get("session_date"):
                    try:
                        session_date = datetime.fromisoformat(session_data["session_date"].replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse session_date from session {session_data.get('id')}")

                session = TutorSession(
                    id=session_data.get("id"),
                    student_id=session_data.get("student_id"),
                    student_email=session_data.get("student_email"),
                    topic=session_data.get("topic", ""),
                    subject_area=session_data.get("subject_area", ""),
                    difficulty_level=session_data.get("difficulty_level", "intermediate"),
                    duration_minutes=session_data.get("duration_minutes", 30),
                    session_date=session_date,
                    status=session_data.get("status", "scheduled"),
                    session_notes=session_data.get("session_notes"),
                    tutor_feedback=session_data.get("tutor_feedback"),
                    student_feedback=session_data.get("student_feedback"),
                    meta_data=session_data.get("meta_data", {}),
                    notion_page_id=notion_page_id
                )

                sessions.append(session)

            return sessions
        except Exception as e:
            logger.error(f"Error listing tutoring sessions: {e}")
            return []

    async def add_tutor_feedback(self, session_id: str, feedback: str) -> bool:
        """
        Add tutor feedback to a session.

        Args:
            session_id: ID of the session
            feedback: Tutor feedback

        Returns:
            True if added successfully, False otherwise
        """
        if not self.api_key:
            logger.error("TutorLM API key not configured")
            return False

        try:
            if not feedback:
                raise ValueError("Feedback cannot be empty")

            # Prepare update data
            update_data = {
                "tutor_feedback": feedback,
                "meta_data": {
                    "feedback_added_at": datetime.now().isoformat()
                }
            }

            # Update session
            headers = self._get_headers()

            await self.async_patch(
                f"{self.base_url}/api/sessions/{session_id}",
                headers=headers,
                json=update_data
            )

            logger.info(f"Added tutor feedback to session {session_id}")
            return True
        except ValueError as e:
            # Handle validation errors
            logger.error(f"Validation error adding tutor feedback: {e}")
            return False
        except Exception as e:
            logger.error(f"Error adding tutor feedback: {e}")
            return False
