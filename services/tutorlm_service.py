"""
TutorLM integration service for The HigherSelf Network Server.
This service manages integration with TutorLM AI tutoring platform while maintaining Notion as the central data hub.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from pydantic import BaseModel, Field


class TutorSession(BaseModel):
    """Model representing a TutorLM tutoring session."""

    id: Optional[str] = None
    student_id: str
    student_name: str
    subject: str
    topic: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: str = "scheduled"  # scheduled, in-progress, completed, cancelled
    session_transcript: Optional[str] = None
    ai_tutor_model: str = "advanced"
    feedback_score: Optional[int] = None
    feedback_comments: Optional[str] = None
    follow_up_actions: Optional[List[str]] = None
    notion_page_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TutorLMConfig(BaseModel):
    """Configuration for TutorLM API integration."""

    api_key: str
    api_base_url: str = "https://api.tutorlm.com/v1"
    default_tutor_model: str = "advanced"

    class Config:
        env_prefix = "TUTORLM_"


class TutorLMService:
    """
    Service for interacting with the TutorLM AI tutoring platform.
    Ensures all tutoring data is properly synchronized with Notion as the central hub.
    """

    def __init__(self, api_key: str = None, api_base_url: str = None):
        """
        Initialize the TutorLM service.

        Args:
            api_key: TutorLM API key
            api_base_url: TutorLM API base URL
        """
        self.api_key = api_key or os.environ.get("TUTORLM_API_KEY")
        self.api_base_url = api_base_url or os.environ.get(
            "TUTORLM_API_BASE_URL", "https://api.tutorlm.com/v1"
        )

        if not self.api_key:
            logger.warning("TutorLM API key not configured")

    async def create_tutoring_session(self, session: TutorSession) -> Optional[str]:
        """
        Create a new tutoring session in TutorLM.

        Args:
            session: TutorSession model with session details

        Returns:
            Session ID if successful, None otherwise
        """
        if not self.api_key:
            logger.error("TutorLM API key not configured")
            return None

        url = f"{self.api_base_url}/sessions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "student_id": session.student_id,
            "student_name": session.student_name,
            "subject": session.subject,
            "topic": session.topic,
            "start_time": session.start_time.isoformat(),
            "ai_tutor_model": session.ai_tutor_model,
            "metadata": session.metadata,
        }

        if session.end_time:
            payload["end_time"] = session.end_time.isoformat()

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            session_id = data.get("id")
            logger.info(f"Created TutorLM session: {session_id}")
            return session_id
        except Exception as e:
            logger.error(f"Error creating TutorLM session: {e}")
            return None

    async def get_session(self, session_id: str) -> Optional[TutorSession]:
        """
        Get details of a specific tutoring session.

        Args:
            session_id: ID of the session to retrieve

        Returns:
            TutorSession model if found, None otherwise
        """
        if not self.api_key:
            logger.error("TutorLM API key not configured")
            return None

        url = f"{self.api_base_url}/sessions/{session_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            session = TutorSession(
                id=data.get("id"),
                student_id=data.get("student_id"),
                student_name=data.get("student_name"),
                subject=data.get("subject"),
                topic=data.get("topic"),
                start_time=datetime.fromisoformat(data.get("start_time")),
                status=data.get("status", "scheduled"),
                ai_tutor_model=data.get("ai_tutor_model", "advanced"),
                metadata=data.get("metadata", {}),
            )

            # Add optional fields if present
            if data.get("end_time"):
                session.end_time = datetime.fromisoformat(data.get("end_time"))

            if data.get("duration_minutes"):
                session.duration_minutes = data.get("duration_minutes")

            if data.get("session_transcript"):
                session.session_transcript = data.get("session_transcript")

            if data.get("feedback_score") is not None:
                session.feedback_score = data.get("feedback_score")

            if data.get("feedback_comments"):
                session.feedback_comments = data.get("feedback_comments")

            if data.get("follow_up_actions"):
                session.follow_up_actions = data.get("follow_up_actions")

            if data.get("notion_page_id"):
                session.notion_page_id = data.get("notion_page_id")

            return session
        except Exception as e:
            logger.error(f"Error getting TutorLM session {session_id}: {e}")
            return None

    async def update_session(
        self, session_id: str, update_data: Dict[str, Any]
    ) -> bool:
        """
        Update a tutoring session in TutorLM.

        Args:
            session_id: ID of the session to update
            update_data: Dictionary of fields to update

        Returns:
            True if update successful, False otherwise
        """
        if not self.api_key:
            logger.error("TutorLM API key not configured")
            return False

        url = f"{self.api_base_url}/sessions/{session_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Format datetime objects if present
        if "start_time" in update_data and isinstance(
            update_data["start_time"], datetime
        ):
            update_data["start_time"] = update_data["start_time"].isoformat()

        if "end_time" in update_data and isinstance(update_data["end_time"], datetime):
            update_data["end_time"] = update_data["end_time"].isoformat()

        try:
            response = requests.patch(url, headers=headers, json=update_data)
            response.raise_for_status()
            logger.info(f"Updated TutorLM session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating TutorLM session {session_id}: {e}")
            return False

    async def cancel_session(self, session_id: str, reason: str = None) -> bool:
        """
        Cancel a scheduled tutoring session.

        Args:
            session_id: ID of the session to cancel
            reason: Optional reason for cancellation

        Returns:
            True if cancellation successful, False otherwise
        """
        update_data = {"status": "cancelled"}

        if reason:
            update_data["metadata"] = {"cancellation_reason": reason}

        return await self.update_session(session_id, update_data)

    async def get_session_transcript(self, session_id: str) -> Optional[str]:
        """
        Get the transcript for a completed tutoring session.

        Args:
            session_id: ID of the session

        Returns:
            Transcript text if available, None otherwise
        """
        if not self.api_key:
            logger.error("TutorLM API key not configured")
            return None

        url = f"{self.api_base_url}/sessions/{session_id}/transcript"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("transcript")
        except Exception as e:
            logger.error(f"Error getting transcript for session {session_id}: {e}")
            return None

    async def list_student_sessions(
        self, student_id: str, limit: int = 10
    ) -> List[TutorSession]:
        """
        List tutoring sessions for a specific student.

        Args:
            student_id: ID of the student
            limit: Maximum number of sessions to return

        Returns:
            List of TutorSession objects
        """
        if not self.api_key:
            logger.error("TutorLM API key not configured")
            return []

        url = f"{self.api_base_url}/students/{student_id}/sessions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"limit": limit}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            sessions = []
            for item in data.get("sessions", []):
                try:
                    session = TutorSession(
                        id=item.get("id"),
                        student_id=item.get("student_id"),
                        student_name=item.get("student_name"),
                        subject=item.get("subject"),
                        topic=item.get("topic"),
                        start_time=datetime.fromisoformat(item.get("start_time")),
                        status=item.get("status", "scheduled"),
                        ai_tutor_model=item.get("ai_tutor_model", "advanced"),
                        metadata=item.get("metadata", {}),
                    )

                    # Add optional fields if present
                    if item.get("end_time"):
                        session.end_time = datetime.fromisoformat(item.get("end_time"))

                    if item.get("duration_minutes"):
                        session.duration_minutes = item.get("duration_minutes")

                    if item.get("feedback_score") is not None:
                        session.feedback_score = item.get("feedback_score")

                    if item.get("notion_page_id"):
                        session.notion_page_id = item.get("notion_page_id")

                    sessions.append(session)
                except Exception as e:
                    logger.error(f"Error parsing session data: {e}")

            return sessions
        except Exception as e:
            logger.error(f"Error listing sessions for student {student_id}: {e}")
            return []

    async def add_session_feedback(
        self, session_id: str, score: int, comments: str = None
    ) -> bool:
        """
        Add student feedback for a completed tutoring session.

        Args:
            session_id: ID of the session
            score: Feedback score (1-5)
            comments: Optional feedback comments

        Returns:
            True if feedback added successfully, False otherwise
        """
        update_data = {"feedback_score": score}

        if comments:
            update_data["feedback_comments"] = comments

        return await self.update_session(session_id, update_data)

    async def sync_session_to_notion(
        self, session_id: str, notion_page_id: str
    ) -> bool:
        """
        Update the TutorLM session with the associated Notion page ID.
        This allows for bi-directional tracking between TutorLM and Notion.

        Args:
            session_id: ID of the TutorLM session
            notion_page_id: ID of the Notion page

        Returns:
            True if update successful, False otherwise
        """
        update_data = {
            "notion_page_id": notion_page_id,
            "metadata": {
                "synced_to_notion": True,
                "notion_sync_time": datetime.now().isoformat(),
            },
        }

        return await self.update_session(session_id, update_data)

    async def get_available_tutors(self, subject: str = None) -> List[Dict[str, Any]]:
        """
        Get a list of available AI tutors, optionally filtered by subject.

        Args:
            subject: Optional subject filter

        Returns:
            List of tutor information dictionaries
        """
        if not self.api_key:
            logger.error("TutorLM API key not configured")
            return []

        url = f"{self.api_base_url}/tutors"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {}

        if subject:
            params["subject"] = subject

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("tutors", [])
        except Exception as e:
            logger.error(f"Error getting available tutors: {e}")
            return []
