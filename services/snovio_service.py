"""
SnovIO integration service for The HigherSelf Network Server.
This service handles lead data enrichment through the SnovIO API.
"""

import os
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from pydantic import BaseModel


class SnovIOConfig(BaseModel):
    """Configuration for SnovIO API integration."""

    client_id: str
    client_secret: str

    class Config:
        env_prefix = "SNOVIO_"


class SnovIOService:
    """
    Service for interacting with the SnovIO API for lead enrichment.
    Data from this service is processed and stored in Notion as the central hub.
    """

    def __init__(self, client_id: str = None, client_secret: str = None):
        """
        Initialize the SnovIO service.

        Args:
            client_id: SnovIO client ID
            client_secret: SnovIO client secret
        """
        self.client_id = client_id or os.environ.get("SNOVIO_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("SNOVIO_CLIENT_SECRET")
        self.base_url = "https://api.snov.io/v1"
        self.access_token = None

        if not self.client_id or not self.client_secret:
            logger.warning("SnovIO credentials not fully configured.")

    async def _get_access_token(self) -> Optional[str]:
        """
        Get an access token from the SnovIO API.

        Returns:
            Access token if successful, None otherwise
        """
        if self.access_token:
            return self.access_token

        url = f"{self.base_url}/oauth/access_token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get("access_token")
            return self.access_token
        except Exception as e:
            logger.error(f"Error getting SnovIO access token: {e}")
            return None

    async def enrich_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Enrich a lead by email address.

        Args:
            email: Email address to enrich

        Returns:
            Enriched lead data if successful, None otherwise
        """
        token = await self._get_access_token()
        if not token:
            logger.error("Failed to get SnovIO access token")
            return None

        url = f"{self.base_url}/get-profile-by-email"
        params = {"access_token": token, "email": email}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                logger.info(f"Successfully enriched lead data for {email}")
                return data.get("data", {})
            else:
                logger.warning(f"No data found for email {email}")
                return None
        except Exception as e:
            logger.error(f"Error enriching lead data: {e}")
            return None

    async def find_emails_by_domain(
        self, domain: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find email addresses by domain.

        Args:
            domain: Domain to search
            limit: Maximum number of results to return

        Returns:
            List of found email addresses
        """
        token = await self._get_access_token()
        if not token:
            logger.error("Failed to get SnovIO access token")
            return []

        url = f"{self.base_url}/domain-emails-with-info"
        params = {"access_token": token, "domain": domain, "limit": limit}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                logger.info(
                    f"Found {len(data.get('emails', []))} emails for domain {domain}"
                )
                return data.get("emails", [])
            else:
                logger.warning(f"No emails found for domain {domain}")
                return []
        except Exception as e:
            logger.error(f"Error finding emails by domain: {e}")
            return []

    async def add_leads_to_list(self, list_id: str, emails: List[str]) -> bool:
        """
        Add leads to a SnovIO list.

        Args:
            list_id: ID of the list
            emails: List of email addresses to add

        Returns:
            True if successful, False otherwise
        """
        token = await self._get_access_token()
        if not token:
            logger.error("Failed to get SnovIO access token")
            return False

        url = f"{self.base_url}/add-leads-to-list"
        payload = {"access_token": token, "listId": list_id, "emails": emails}

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                logger.info(f"Added {len(emails)} leads to list {list_id}")
                return True
            else:
                logger.warning(f"Failed to add leads to list {list_id}")
                return False
        except Exception as e:
            logger.error(f"Error adding leads to list: {e}")
            return False
