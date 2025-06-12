"""
GoHighLevel service implementation for The HigherSelf Network Server.

This module provides comprehensive integration with GoHighLevel CRM API,
supporting multi-business portfolio management and cross-business automation.
"""

import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import aiohttp
from loguru import logger
from pydantic import BaseModel, Field, validator

from config.settings import settings
from models.gohighlevel_models import (BusinessType, ContactSource,
                                       GHLAppointment, GHLCampaign, GHLContact,
                                       GHLOpportunity, GHLPipeline,
                                       GHLSyncStatus, GHLWebhookEvent,
                                       OpportunityStage, SubAccountType)
from services.base_service import BaseService, ServiceCredentials


class GoHighLevelCredentials(ServiceCredentials):
    """Credentials for GoHighLevel API integration."""

    client_id: str = Field(..., description="GoHighLevel OAuth client ID")
    client_secret: str = Field(..., description="GoHighLevel OAuth client secret")
    access_token: Optional[str] = Field(None, description="Current access token")
    refresh_token: Optional[str] = Field(
        None, description="Refresh token for token renewal"
    )
    location_id: str = Field(..., description="GoHighLevel location/sub-account ID")
    webhook_secret: str = Field(
        ..., description="Webhook signature verification secret"
    )

    class Config:
        env_prefix = "GOHIGHLEVEL_"

    @validator("client_id", "client_secret", "location_id", "webhook_secret")
    def validate_required_fields(cls, v: str) -> str:
        """Validate that required fields are not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError("This field is required and cannot be empty")
        return v.strip()


class GoHighLevelError(Exception):
    """Base exception for GoHighLevel API errors."""

    pass


class GoHighLevelAuthError(GoHighLevelError):
    """Authentication/authorization errors."""

    pass


class GoHighLevelRateLimitError(GoHighLevelError):
    """Rate limit exceeded errors."""

    pass


class GoHighLevelValidationError(GoHighLevelError):
    """Data validation errors."""

    pass


class RateLimiter:
    """Rate limiter for GoHighLevel API compliance."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 10):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[datetime] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Acquire permission to make an API request.

        Blocks if rate limit would be exceeded.
        """
        async with self._lock:
            now = datetime.now()

            # Remove requests outside the current window
            cutoff = now - timedelta(seconds=self.window_seconds)
            self.requests = [
                req_time for req_time in self.requests if req_time > cutoff
            ]

            # Check if we can make another request
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = min(self.requests)
                wait_time = (
                    oldest_request + timedelta(seconds=self.window_seconds) - now
                ).total_seconds()

                if wait_time > 0:
                    logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time)
                    return await self.acquire()  # Recursive call after waiting

            # Record this request
            self.requests.append(now)


class GoHighLevelService(BaseService):
    """
    Service for interacting with GoHighLevel CRM API.

    Provides comprehensive CRM functionality including contacts, opportunities,
    campaigns, and appointments management across multiple business sub-accounts.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        location_id: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        """
        Initialize GoHighLevel service.

        Args:
            client_id: OAuth client ID (defaults to environment variable)
            client_secret: OAuth client secret (defaults to environment variable)
            location_id: GoHighLevel location ID (defaults to environment variable)
            webhook_secret: Webhook verification secret (defaults to environment variable)
        """
        # Get credentials from environment if not provided
        client_id = client_id or getattr(
            settings.integrations, "gohighlevel_client_id", None
        )
        client_secret = client_secret or getattr(
            settings.integrations, "gohighlevel_client_secret", None
        )
        location_id = location_id or getattr(
            settings.integrations, "gohighlevel_location_id", None
        )
        webhook_secret = webhook_secret or getattr(
            settings.integrations, "gohighlevel_webhook_secret", None
        )

        # Create credentials object
        credentials = None
        if all([client_id, client_secret, location_id, webhook_secret]):
            credentials = GoHighLevelCredentials(
                service_name="gohighlevel",
                client_id=client_id,
                client_secret=client_secret,
                location_id=location_id,
                webhook_secret=webhook_secret,
            )

        # Initialize base service
        super().__init__(service_name="gohighlevel", credentials=credentials)

        # GoHighLevel specific configuration
        self.api_base_url = "https://services.leadconnectorhq.com"
        self.api_version = "v1"
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=10)

        # Sub-account mapping
        self.sub_account_tokens = {
            SubAccountType.CORE_BUSINESS: getattr(
                settings.integrations, "gohighlevel_core_business_token", None
            ),
            SubAccountType.HOME_SERVICES: getattr(
                settings.integrations, "gohighlevel_home_services_token", None
            ),
            SubAccountType.EXTENDED_WELLNESS: getattr(
                settings.integrations, "gohighlevel_extended_wellness_token", None
            ),
            SubAccountType.DEVELOPMENT: getattr(
                settings.integrations, "gohighlevel_development_token", None
            ),
            SubAccountType.ANALYTICS: getattr(
                settings.integrations, "gohighlevel_analytics_token", None
            ),
        }

        self.sub_account_locations = {
            SubAccountType.CORE_BUSINESS: getattr(
                settings.integrations, "gohighlevel_core_business_location", None
            ),
            SubAccountType.HOME_SERVICES: getattr(
                settings.integrations, "gohighlevel_home_services_location", None
            ),
            SubAccountType.EXTENDED_WELLNESS: getattr(
                settings.integrations, "gohighlevel_extended_wellness_location", None
            ),
            SubAccountType.DEVELOPMENT: getattr(
                settings.integrations, "gohighlevel_development_location", None
            ),
            SubAccountType.ANALYTICS: getattr(
                settings.integrations, "gohighlevel_analytics_location", None
            ),
        }

        if not credentials:
            logger.warning("GoHighLevel credentials not fully configured")

    async def validate_credentials(self) -> bool:
        """
        Validate GoHighLevel API credentials.

        Returns:
            True if credentials are valid, False otherwise
        """
        if not self.credentials:
            logger.error("GoHighLevel credentials not configured")
            return False

        try:
            # Test API access with location info endpoint
            url = f"{self.api_base_url}/{self.api_version}/locations/{self.credentials.location_id}"
            headers = await self._get_auth_headers()

            response = await self.async_get(url, headers=headers)

            # Update credentials verification timestamp
            self.credentials.last_verified = datetime.now()

            logger.info("GoHighLevel credentials validated successfully")
            return True

        except Exception as e:
            logger.error(f"Invalid GoHighLevel credentials: {e}")
            return False

    async def _get_auth_headers(
        self, sub_account: Optional[SubAccountType] = None
    ) -> Dict[str, str]:
        """
        Get authentication headers for API requests.

        Args:
            sub_account: Sub-account to get token for

        Returns:
            Dictionary of headers including authorization
        """
        # Use sub-account specific token if provided
        if sub_account and sub_account in self.sub_account_tokens:
            token = self.sub_account_tokens[sub_account]
        else:
            token = self.credentials.access_token if self.credentials else None

        if not token:
            raise GoHighLevelAuthError("No access token available")

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _handle_api_response(
        self, response: aiohttp.ClientResponse
    ) -> Dict[str, Any]:
        """
        Handle GoHighLevel API response with comprehensive error handling.

        Args:
            response: aiohttp response object

        Returns:
            Parsed JSON response data

        Raises:
            GoHighLevelAuthError: For authentication failures
            GoHighLevelRateLimitError: For rate limit violations
            GoHighLevelValidationError: For validation errors
            GoHighLevelError: For other API errors
        """
        try:
            if response.status == 200:
                return await response.json()

            elif response.status == 401:
                error_data = await response.json()
                logger.error(f"GoHighLevel authentication error: {error_data}")
                raise GoHighLevelAuthError(
                    f"Authentication failed: {error_data.get('message', 'Unknown error')}"
                )

            elif response.status == 429:
                retry_after = response.headers.get("Retry-After", "60")
                logger.warning(
                    f"GoHighLevel rate limit exceeded. Retry after {retry_after} seconds"
                )
                raise GoHighLevelRateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds"
                )

            elif response.status == 422:
                error_data = await response.json()
                logger.error(f"GoHighLevel validation error: {error_data}")
                raise GoHighLevelValidationError(
                    f"Validation failed: {error_data.get('message', 'Unknown error')}"
                )

            else:
                error_text = await response.text()
                logger.error(f"GoHighLevel API error {response.status}: {error_text}")
                raise GoHighLevelError(f"API error {response.status}: {error_text}")

        except aiohttp.ClientError as e:
            logger.error(f"GoHighLevel client error: {e}")
            raise GoHighLevelError(f"Client error: {e}")

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature from GoHighLevel.

        Args:
            payload: Raw webhook payload
            signature: Signature from webhook headers

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.credentials or not self.credentials.webhook_secret:
            logger.error("Webhook secret not configured")
            return False

        try:
            # GoHighLevel uses HMAC-SHA256
            expected_signature = hmac.new(
                self.credentials.webhook_secret.encode(), payload, hashlib.sha256
            ).hexdigest()

            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False

    # Contact Management Methods

    async def create_contact(self, contact_data: GHLContact) -> Optional[str]:
        """
        Create a new contact in GoHighLevel.

        Args:
            contact_data: Contact information

        Returns:
            Contact ID if successful, None otherwise
        """
        await self.rate_limiter.acquire()

        try:
            # Get location ID for sub-account
            location_id = self.sub_account_locations.get(contact_data.sub_account)
            if not location_id:
                raise GoHighLevelError(
                    f"No location ID configured for sub-account: {contact_data.sub_account}"
                )

            url = f"{self.api_base_url}/{self.api_version}/contacts/"
            headers = await self._get_auth_headers(contact_data.sub_account)

            # Prepare contact payload
            payload = {
                "firstName": contact_data.first_name,
                "lastName": contact_data.last_name,
                "email": contact_data.email,
                "locationId": location_id,
                "source": contact_data.source.value,
                "tags": contact_data.tags,
                "customFields": contact_data.custom_fields,
            }

            if contact_data.phone:
                payload["phone"] = contact_data.phone

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    result = await self._handle_api_response(response)

                    contact_id = result.get("contact", {}).get("id")
                    if contact_id:
                        logger.info(f"Created GoHighLevel contact: {contact_id}")
                        return contact_id
                    else:
                        logger.error(f"Failed to create contact: {result}")
                        return None

        except GoHighLevelRateLimitError:
            # Retry with exponential backoff
            await asyncio.sleep(2)
            return await self.create_contact(contact_data)
        except Exception as e:
            logger.error(f"Error creating GoHighLevel contact: {e}")
            return None

    async def get_contact(
        self, contact_id: str, sub_account: SubAccountType
    ) -> Optional[GHLContact]:
        """
        Retrieve a contact from GoHighLevel.

        Args:
            contact_id: GoHighLevel contact ID
            sub_account: Sub-account type

        Returns:
            Contact data if found, None otherwise
        """
        await self.rate_limiter.acquire()

        try:
            url = f"{self.api_base_url}/{self.api_version}/contacts/{contact_id}"
            headers = await self._get_auth_headers(sub_account)

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    result = await self._handle_api_response(response)

                    contact_data = result.get("contact", {})
                    if contact_data:
                        # Convert to GHLContact model
                        return GHLContact(
                            id=contact_data.get("id"),
                            first_name=contact_data.get("firstName", ""),
                            last_name=contact_data.get("lastName", ""),
                            email=contact_data.get("email", ""),
                            phone=contact_data.get("phone"),
                            primary_business=BusinessType.ART_GALLERY,  # Default, should be determined from tags
                            source=ContactSource.WEBSITE,  # Default, should be from contact data
                            sub_account=sub_account,
                            tags=contact_data.get("tags", []),
                            custom_fields=contact_data.get("customFields", {}),
                            created_at=(
                                datetime.fromisoformat(
                                    contact_data.get("dateAdded", "").replace(
                                        "Z", "+00:00"
                                    )
                                )
                                if contact_data.get("dateAdded")
                                else None
                            ),
                            updated_at=(
                                datetime.fromisoformat(
                                    contact_data.get("dateUpdated", "").replace(
                                        "Z", "+00:00"
                                    )
                                )
                                if contact_data.get("dateUpdated")
                                else None
                            ),
                        )
                    return None

        except Exception as e:
            logger.error(f"Error retrieving GoHighLevel contact {contact_id}: {e}")
            return None

    async def update_contact(self, contact_id: str, contact_data: GHLContact) -> bool:
        """
        Update an existing contact in GoHighLevel.

        Args:
            contact_id: GoHighLevel contact ID
            contact_data: Updated contact information

        Returns:
            True if successful, False otherwise
        """
        await self.rate_limiter.acquire()

        try:
            url = f"{self.api_base_url}/{self.api_version}/contacts/{contact_id}"
            headers = await self._get_auth_headers(contact_data.sub_account)

            # Prepare update payload
            payload = {
                "firstName": contact_data.first_name,
                "lastName": contact_data.last_name,
                "email": contact_data.email,
                "tags": contact_data.tags,
                "customFields": contact_data.custom_fields,
            }

            if contact_data.phone:
                payload["phone"] = contact_data.phone

            async with aiohttp.ClientSession() as session:
                async with session.put(url, headers=headers, json=payload) as response:
                    await self._handle_api_response(response)
                    logger.info(f"Updated GoHighLevel contact: {contact_id}")
                    return True

        except Exception as e:
            logger.error(f"Error updating GoHighLevel contact {contact_id}: {e}")
            return False

    async def search_contacts(
        self, query: str, sub_account: SubAccountType, limit: int = 20
    ) -> List[GHLContact]:
        """
        Search for contacts in GoHighLevel.

        Args:
            query: Search query
            sub_account: Sub-account type
            limit: Maximum number of results

        Returns:
            List of matching contacts
        """
        await self.rate_limiter.acquire()

        try:
            location_id = self.sub_account_locations.get(sub_account)
            if not location_id:
                raise GoHighLevelError(
                    f"No location ID configured for sub-account: {sub_account}"
                )

            url = f"{self.api_base_url}/{self.api_version}/contacts/"
            headers = await self._get_auth_headers(sub_account)

            params = {"locationId": location_id, "query": query, "limit": limit}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    result = await self._handle_api_response(response)

                    contacts = []
                    for contact_data in result.get("contacts", []):
                        contact = GHLContact(
                            id=contact_data.get("id"),
                            first_name=contact_data.get("firstName", ""),
                            last_name=contact_data.get("lastName", ""),
                            email=contact_data.get("email", ""),
                            phone=contact_data.get("phone"),
                            primary_business=BusinessType.ART_GALLERY,  # Default
                            source=ContactSource.WEBSITE,  # Default
                            sub_account=sub_account,
                            tags=contact_data.get("tags", []),
                            custom_fields=contact_data.get("customFields", {}),
                            created_at=(
                                datetime.fromisoformat(
                                    contact_data.get("dateAdded", "").replace(
                                        "Z", "+00:00"
                                    )
                                )
                                if contact_data.get("dateAdded")
                                else None
                            ),
                        )
                        contacts.append(contact)

                    return contacts

        except Exception as e:
            logger.error(f"Error searching GoHighLevel contacts: {e}")
            return []
