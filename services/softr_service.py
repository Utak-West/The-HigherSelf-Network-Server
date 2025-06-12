"""
Softr Service

This module provides integration with Softr for staff interfaces to agents.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from pydantic import BaseModel

from models.base import ApiPlatform
from models.softr_models import (AgentInteraction, AgentRequest, AgentResponse,
                                 StaffUser)
from services.base_service import BaseService


class SoftrServiceConfig(BaseModel):
    """Configuration for Softr service."""

    api_key: str
    app_id: str
    api_url: str = "https://api.softr.io/v1"


class SoftrService(BaseService):
    """Service for interacting with Softr API to enable staff-agent interfaces"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        app_id: Optional[str] = None,
        api_url: Optional[str] = None,
        credentials: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the Softr service.

        Args:
            api_key: Softr API key (optional, can be provided in credentials)
            app_id: Softr App ID (optional, can be provided in credentials)
            api_url: Softr API URL (optional, defaults to standard URL)
            credentials: Dictionary containing credentials (optional)
        """
        # Initialize base service
        super().__init__(service_name="softr", credentials=credentials)

        # Get credentials from parameters or environment
        self.api_key = api_key or credentials.get("api_key") if credentials else None
        if not self.api_key:
            self.api_key = os.getenv("SOFTR_API_KEY")

        self.app_id = app_id or credentials.get("app_id") if credentials else None
        if not self.app_id:
            self.app_id = os.getenv("SOFTR_APP_ID")

        self.api_url = api_url or credentials.get("api_url") if credentials else None
        if not self.api_url:
            self.api_url = os.getenv("SOFTR_API_URL", "https://api.softr.io/v1")

        # Log warning if credentials are missing
        if not self.api_key or not self.app_id:
            logger.warning("Softr credentials not fully configured")

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Softr API requests.

        Returns:
            Dictionary of headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Softr-Api-Key": self.api_key,
            "Softr-App-Id": self.app_id,
            "Content-Type": "application/json",
        }

    async def validate_staff_user(
        self, user_id: str, api_key: str
    ) -> Optional[StaffUser]:
        """
        Validate that a staff user exists and has appropriate permissions.

        Args:
            user_id: The staff user ID
            api_key: The staff user's API key

        Returns:
            StaffUser object if valid, None otherwise
        """
        try:
            # In a real implementation, this would check against Softr's user database
            # For now, we'll use a simplified approach
            response = requests.get(
                f"{self.api_url}/users/{user_id}", headers=self._get_headers()
            )

            if response.status_code != 200:
                logger.warning(
                    f"Failed to validate staff user {user_id}: {response.status_code}"
                )
                return None

            user_data = response.json()

            # Check if the user has the staff role
            if "staff" not in user_data.get("roles", []):
                logger.warning(f"User {user_id} does not have staff role")
                return None

            # Validate the API key (in a real implementation, this would be more secure)
            # This is a simplified example
            if user_data.get("api_key") != api_key:
                logger.warning(f"Invalid API key for user {user_id}")
                return None

            return StaffUser(
                id=user_data.get("id"),
                name=user_data.get("name"),
                email=user_data.get("email"),
                roles=user_data.get("roles", []),
            )

        except Exception as e:
            logger.error(f"Error validating staff user: {str(e)}")
            return None

    async def record_agent_interaction(self, interaction: AgentInteraction) -> bool:
        """
        Record an agent interaction in Softr.

        Args:
            interaction: The agent interaction to record

        Returns:
            True if successful, False otherwise
        """
        try:
            # In a real implementation, this would create a record in Softr's database
            response = requests.post(
                f"{self.api_url}/records/agent_interactions",
                headers=self._get_headers(),
                json=interaction.model_dump(),
            )

            if response.status_code not in (200, 201):
                logger.warning(
                    f"Failed to record agent interaction: {response.status_code}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error recording agent interaction: {str(e)}")
            return False

    async def get_staff_agent_history(
        self, staff_id: str, agent_id: Optional[str] = None
    ) -> List[AgentInteraction]:
        """
        Get the history of interactions between a staff member and agents.

        Args:
            staff_id: The staff user ID
            agent_id: Optional agent ID to filter by

        Returns:
            List of agent interactions
        """
        try:
            # Build query parameters
            params = {"staff_id": staff_id}
            if agent_id:
                params["agent_id"] = agent_id

            # In a real implementation, this would query Softr's database
            response = requests.get(
                f"{self.api_url}/records/agent_interactions",
                headers=self._get_headers(),
                params=params,
            )

            if response.status_code != 200:
                logger.warning(
                    f"Failed to get agent interaction history: {response.status_code}"
                )
                return []

            interactions_data = response.json().get("data", [])
            return [
                AgentInteraction(**interaction) for interaction in interactions_data
            ]

        except Exception as e:
            logger.error(f"Error getting agent interaction history: {str(e)}")
            return []

    async def get_available_agents(self) -> List[Dict[str, Any]]:
        """
        Get a list of available agents that staff can interact with.

        Returns:
            List of agent information dictionaries
        """
        try:
            # In a real implementation, this would query the agent registry
            # For now, we'll return a static list of example agents
            return [
                {
                    "id": "lead_capture_agent",
                    "name": "Lead Capture Agent",
                    "description": "Processes leads from various sources",
                    "status": "active",
                    "capabilities": ["lead_processing", "data_enrichment"],
                },
                {
                    "id": "booking_agent",
                    "name": "Booking Agent",
                    "description": "Handles bookings and scheduling",
                    "status": "active",
                    "capabilities": ["scheduling", "reminders", "calendar_management"],
                },
                {
                    "id": "content_lifecycle_agent",
                    "name": "Content Lifecycle Agent",
                    "description": "Manages content creation and distribution",
                    "status": "active",
                    "capabilities": ["content_creation", "distribution", "analytics"],
                },
            ]
        except Exception as e:
            logger.error(f"Error getting available agents: {str(e)}")
            return []
