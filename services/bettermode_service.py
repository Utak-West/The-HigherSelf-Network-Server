"""
BetterMode integration service for The HigherSelf Network Server.
This service handles integration with BetterMode while maintaining Notion as the central hub.
"""

import asyncio
import hashlib
import hmac
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
from loguru import logger
from pydantic import ValidationError

from config.testing_mode import TestingMode, is_api_disabled
from models.base import ApiPlatform
from models.bettermode_models import (
    BetterModeComment,
    BetterModeEvent,
    BetterModeIntegrationConfig,
    BetterModeMember,
    BetterModePost,
    BetterModeReaction,
    BetterModeSpace,
    BetterModeWebhookPayload,
)
from services.base_service import BaseService, ServiceCredentials


class BetterModeService(BaseService):
    """
    Service for interacting with BetterMode API.
    Handles authentication, API calls, and webhook verification.
    """

    def __init__(self, config: Optional[BetterModeIntegrationConfig] = None):
        """Initialize the BetterMode service."""
        super().__init__(
            service_name="bettermode",
            api_platform=ApiPlatform.BETTERMODE,
            description="BetterMode community platform integration",
        )

        self.config = config or self._load_config_from_env()
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info("BetterMode service initialized")

    def _load_config_from_env(self) -> BetterModeIntegrationConfig:
        """Load configuration from environment variables."""
        return BetterModeIntegrationConfig(
            api_token=os.getenv("BETTERMODE_API_TOKEN", ""),
            network_id=os.getenv("BETTERMODE_NETWORK_ID", ""),
            webhook_secret=os.getenv("BETTERMODE_WEBHOOK_SECRET", ""),
            api_url=os.getenv(
                "BETTERMODE_API_URL", "https://app.bettermode.com/api/graphql"
            ),
        )

    async def validate_connection(self) -> bool:
        """Validate the connection to BetterMode API."""
        try:
            # Check if in testing mode
            if is_api_disabled("bettermode"):
                TestingMode.log_attempted_api_call(
                    api_name="bettermode",
                    endpoint="graphql",
                    method="POST",
                    params={"query": "{ network { id name } }"},
                )
                logger.info(
                    "[TESTING MODE] Simulated BetterMode API connection validation"
                )
                return True

            # Simple query to check if API token is valid
            query = """
            query {
                network {
                    id
                    name
                }
            }
            """

            result = await self._execute_graphql(query)
            return (
                "network" in result
                and result["network"]["id"] == self.config.network_id
            )
        except Exception as e:
            logger.error(f"Error validating BetterMode connection: {str(e)}")
            return False

    async def _execute_graphql(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a GraphQL query against the BetterMode API."""
        if is_api_disabled("bettermode"):
            TestingMode.log_attempted_api_call(
                api_name="bettermode",
                endpoint="graphql",
                method="POST",
                params={"query": query, "variables": variables},
            )
            logger.info(
                f"[TESTING MODE] Simulated BetterMode GraphQL query: {query[:50]}..."
            )
            return {"data": {}}

        headers = {
            "Authorization": f"Bearer {self.config.api_token}",
            "Content-Type": "application/json",
        }

        payload = {"query": query, "variables": variables or {}}

        response = await self.client.post(
            self.config.api_url, headers=headers, json=payload
        )

        if response.status_code != 200:
            logger.error(
                f"BetterMode API error: {response.status_code} - {response.text}"
            )
            raise Exception(f"BetterMode API error: {response.status_code}")

        result = response.json()

        if "errors" in result:
            logger.error(f"BetterMode GraphQL error: {result['errors']}")
            raise Exception(f"BetterMode GraphQL error: {result['errors']}")

        return result.get("data", {})

    def verify_webhook_signature(self, signature: str, body: bytes) -> bool:
        """
        Verify the webhook signature from BetterMode.

        Args:
            signature: The signature from the X-Bettermode-Signature header
            body: The raw request body

        Returns:
            True if the signature is valid, False otherwise
        """
        if not self.config.webhook_secret:
            logger.warning(
                "No webhook secret configured, skipping signature verification"
            )
            return True

        # Calculate expected signature
        expected_signature = hmac.new(
            self.config.webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()

        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)

    async def get_member(self, member_id: str) -> Optional[BetterModeMember]:
        """
        Get a member by ID.

        Args:
            member_id: BetterMode member ID

        Returns:
            BetterModeMember if found, None otherwise
        """
        query = """
        query GetMember($id: ID!) {
            member(id: $id) {
                id
                name
                email
                role
                joinedAt
                profilePicture
                customFields
            }
        }
        """

        variables = {"id": member_id}

        try:
            result = await self._execute_graphql(query, variables)

            if not result.get("member"):
                return None

            member_data = result["member"]
            return BetterModeMember(
                id=member_data["id"],
                name=member_data["name"],
                email=member_data["email"],
                role=member_data["role"],
                joined_at=datetime.fromisoformat(
                    member_data["joinedAt"].replace("Z", "+00:00")
                ),
                profile_picture=member_data.get("profilePicture"),
                custom_fields=member_data.get("customFields", {}),
            )
        except Exception as e:
            logger.error(f"Error getting BetterMode member {member_id}: {str(e)}")
            return None

    async def get_member_by_email(self, email: str) -> Optional[BetterModeMember]:
        """
        Get a member by email.

        Args:
            email: Member's email address

        Returns:
            BetterModeMember if found, None otherwise
        """
        query = """
        query GetMemberByEmail($email: String!) {
            members(filter: { email: { eq: $email } }, first: 1) {
                nodes {
                    id
                    name
                    email
                    role
                    joinedAt
                    profilePicture
                    customFields
                }
            }
        }
        """

        variables = {"email": email}

        try:
            result = await self._execute_graphql(query, variables)

            members = result.get("members", {}).get("nodes", [])
            if not members:
                return None

            member_data = members[0]
            return BetterModeMember(
                id=member_data["id"],
                name=member_data["name"],
                email=member_data["email"],
                role=member_data["role"],
                joined_at=datetime.fromisoformat(
                    member_data["joinedAt"].replace("Z", "+00:00")
                ),
                profile_picture=member_data.get("profilePicture"),
                custom_fields=member_data.get("customFields", {}),
            )
        except Exception as e:
            logger.error(f"Error getting BetterMode member by email {email}: {str(e)}")
            return None

    async def send_direct_message(self, recipient_id: str, message: str) -> bool:
        """
        Send a direct message to a member.

        Args:
            recipient_id: BetterMode member ID
            message: Message content

        Returns:
            True if successful, False otherwise
        """
        query = """
        mutation SendDirectMessage($input: SendDirectMessageInput!) {
            sendDirectMessage(input: $input) {
                message {
                    id
                }
            }
        }
        """

        variables = {"input": {"recipientId": recipient_id, "content": message}}

        try:
            result = await self._execute_graphql(query, variables)
            return (
                "sendDirectMessage" in result
                and result["sendDirectMessage"]["message"]["id"]
            )
        except Exception as e:
            logger.error(
                f"Error sending BetterMode direct message to {recipient_id}: {str(e)}"
            )
            return False

    async def create_post(
        self,
        space_id: str,
        content: str,
        title: Optional[str] = None,
        author_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a post in a space.

        Args:
            space_id: BetterMode space ID
            content: Post content
            title: Post title (optional)
            author_id: Author's BetterMode member ID (optional, uses API token user if not provided)

        Returns:
            Post ID if successful, None otherwise
        """
        query = """
        mutation CreatePost($input: CreatePostInput!) {
            createPost(input: $input) {
                post {
                    id
                }
            }
        }
        """

        variables = {
            "input": {"spaceId": space_id, "content": content, "published": True}
        }

        if title:
            variables["input"]["title"] = title

        if author_id:
            variables["input"]["authorId"] = author_id

        try:
            result = await self._execute_graphql(query, variables)
            return result.get("createPost", {}).get("post", {}).get("id")
        except Exception as e:
            logger.error(
                f"Error creating BetterMode post in space {space_id}: {str(e)}"
            )
            return None


# Singleton instance
_bettermode_service = None


async def get_bettermode_service() -> BetterModeService:
    """Get or create the BetterMode service singleton."""
    global _bettermode_service

    if _bettermode_service is None:
        _bettermode_service = BetterModeService()

    return _bettermode_service
