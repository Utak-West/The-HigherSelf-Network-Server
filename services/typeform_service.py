"""
TypeForm integration service for The HigherSelf Network Server.
This service handles integration with TypeForm while maintaining Notion as the central hub.
"""

import hashlib
import hmac
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from pydantic import BaseModel, Field


class TypeFormConfig(BaseModel):
    """Configuration for TypeForm API integration."""

    personal_token: str
    webhook_secret: str

    class Config:
        env_prefix = "TYPEFORM_"


class TypeFormResponse(BaseModel):
    """Model representing a TypeForm form response."""

    response_id: str
    form_id: str
    form_title: str
    submitted_at: datetime
    answers: Dict[str, Any] = Field(default_factory=dict)
    hidden_fields: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    calculated_score: Optional[int] = None
    landing_id: Optional[str] = None
    notion_page_id: Optional[str] = None


class TypeFormService:
    """
    Service for interacting with TypeForm.
    Ensures all form data is properly synchronized with Notion as the central hub.
    """

    def __init__(self, personal_token: str = None, webhook_secret: str = None):
        """
        Initialize the TypeForm service.

        Args:
            personal_token: TypeForm Personal Access Token
            webhook_secret: TypeForm Webhook Secret for signature verification
        """
        self.personal_token = personal_token or os.environ.get(
            "TYPEFORM_PERSONAL_TOKEN"
        )
        self.webhook_secret = webhook_secret or os.environ.get(
            "TYPEFORM_WEBHOOK_SECRET"
        )
        self.base_url = "https://api.typeform.com"

        if not self.personal_token:
            logger.warning("TypeForm Personal Access Token not configured")

    async def validate_credentials(self) -> bool:
        """
        Validate the TypeForm API credentials.

        Returns:
            True if credentials are valid, False otherwise
        """
        if not self.personal_token:
            logger.error("TypeForm credentials not configured")
            return False

        try:
            url = f"{self.base_url}/me"
            headers = {"Authorization": f"Bearer {self.personal_token}"}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            logger.info("TypeForm credentials validated successfully")
            return True
        except Exception as e:
            logger.error(f"Invalid TypeForm credentials: {e}")
            return False

    async def get_forms(self) -> List[Dict[str, Any]]:
        """
        Get all forms for the current account.

        Returns:
            List of form dictionaries
        """
        if not self.personal_token:
            logger.error("TypeForm credentials not configured")
            return []

        try:
            url = f"{self.base_url}/forms"
            headers = {"Authorization": f"Bearer {self.personal_token}"}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            forms = data.get("items", [])

            logger.info(f"Retrieved {len(forms)} forms from TypeForm")
            return forms
        except Exception as e:
            logger.error(f"Error getting TypeForm forms: {e}")
            return []

    async def get_form_details(self, form_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific form.

        Args:
            form_id: TypeForm form ID

        Returns:
            Form details dictionary if found, None otherwise
        """
        if not self.personal_token:
            logger.error("TypeForm credentials not configured")
            return None

        try:
            url = f"{self.base_url}/forms/{form_id}"
            headers = {"Authorization": f"Bearer {self.personal_token}"}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            form_details = response.json()
            logger.info(f"Retrieved details for form {form_id}")
            return form_details
        except Exception as e:
            logger.error(f"Error getting form details for {form_id}: {e}")
            return None

    async def get_form_responses(
        self, form_id: str, page_size: int = 25, since: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get responses for a specific form.

        Args:
            form_id: TypeForm form ID
            page_size: Number of responses to retrieve per page
            since: Optional ISO timestamp to get responses submitted after this time

        Returns:
            List of response dictionaries
        """
        if not self.personal_token:
            logger.error("TypeForm credentials not configured")
            return []

        try:
            url = f"{self.base_url}/forms/{form_id}/responses"
            headers = {"Authorization": f"Bearer {self.personal_token}"}

            params = {
                "page_size": page_size,
            }

            if since:
                params["since"] = since

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            responses = data.get("items", [])

            logger.info(f"Retrieved {len(responses)} responses for form {form_id}")
            return responses
        except Exception as e:
            logger.error(f"Error getting responses for form {form_id}: {e}")
            return []

    async def get_response(
        self, form_id: str, response_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific response by ID.

        Args:
            form_id: TypeForm form ID
            response_id: TypeForm response ID

        Returns:
            Response dictionary if found, None otherwise
        """
        if not self.personal_token:
            logger.error("TypeForm credentials not configured")
            return None

        try:
            url = f"{self.base_url}/forms/{form_id}/responses"
            headers = {"Authorization": f"Bearer {self.personal_token}"}

            # Unfortunately, TypeForm API doesn't provide a direct endpoint to get a specific response
            # We need to get all responses and filter for the one we want
            responses = await self.get_form_responses(form_id, page_size=1000)

            for response in responses:
                if response.get("response_id") == response_id:
                    logger.info(f"Retrieved response {response_id} for form {form_id}")
                    return response

            logger.warning(f"Response {response_id} not found for form {form_id}")
            return None
        except Exception as e:
            logger.error(
                f"Error getting response {response_id} for form {form_id}: {e}"
            )
            return None

    async def process_webhook_payload(
        self, payload: Dict[str, Any]
    ) -> Optional[TypeFormResponse]:
        """
        Process a webhook payload from TypeForm.

        Args:
            payload: Webhook payload data

        Returns:
            TypeFormResponse if valid, None otherwise
        """
        try:
            # Extract form response data
            form_response = payload.get("form_response", {})
            if not form_response:
                logger.error("Invalid TypeForm webhook payload: missing form_response")
                return None

            # Basic payload validation
            if "token" not in form_response or "form_id" not in form_response:
                logger.error(
                    "Invalid TypeForm webhook payload: missing required fields"
                )
                return None

            # Extract key information
            response_id = form_response.get("token")
            form_id = form_response.get("form_id")
            form_title = form_response.get("definition", {}).get(
                "title", "Unknown Form"
            )
            submitted_at = datetime.fromisoformat(
                form_response.get("submitted_at").replace("Z", "+00:00")
            )

            # Process and organize form answers into a structured dictionary
            answers = {}
            for answer in form_response.get("answers", []):
                # Get the question ID and field type
                field_id = answer.get("field", {}).get("id")
                field_type = answer.get("field", {}).get("type")
                field_title = answer.get("field", {}).get("title", "")

                # Extract answer based on field type
                answer_value = None
                if field_type in [
                    "short_text",
                    "long_text",
                    "email",
                    "website",
                    "phone_number",
                ]:
                    answer_value = answer.get("text", "")
                elif field_type == "number":
                    answer_value = answer.get("number", 0)
                elif field_type == "multiple_choice":
                    answer_value = answer.get("choice", {}).get("label", "")
                elif field_type == "picture_choice":
                    answer_value = answer.get("choice", {}).get("label", "")
                elif field_type == "yes_no":
                    answer_value = answer.get("boolean", False)
                elif field_type == "file_upload":
                    answer_value = answer.get("file_url", "")
                elif field_type == "rating":
                    answer_value = answer.get("number", 0)
                elif field_type == "opinion_scale":
                    answer_value = answer.get("number", 0)
                elif field_type == "dropdown":
                    answer_value = answer.get("choice", {}).get("label", "")
                elif field_type == "date":
                    answer_value = answer.get("date", "")
                elif field_type == "payment":
                    answer_value = answer.get("payment", {})
                elif field_type == "matrix":
                    answers_matrix = {}
                    for row in answer.get("choices", {}):
                        row_id = row.get("row_id", "")
                        answers_matrix[row_id] = row.get("choice", {}).get("label", "")
                    answer_value = answers_matrix

                # Add to answers dictionary
                if field_title:
                    # Use field title as the key for readability
                    answers[field_title] = answer_value
                else:
                    # Fall back to field ID if title not available
                    answers[field_id] = answer_value

            # Extract hidden fields if present
            hidden_fields = {}
            if "hidden" in form_response:
                hidden_fields = form_response.get("hidden", {})

            # Extract metadata if present
            metadata = {}
            if "metadata" in form_response:
                metadata = form_response.get("metadata", {})

            # Calculate score if present
            calculated_score = form_response.get("calculated", {}).get("score")

            # Extract landing ID if present
            landing_id = form_response.get("landing_id")

            # Look for Notion page ID in hidden fields
            notion_page_id = None
            if "notion_page_id" in hidden_fields:
                notion_page_id = hidden_fields.get("notion_page_id")

            # Create TypeFormResponse
            response = TypeFormResponse(
                response_id=response_id,
                form_id=form_id,
                form_title=form_title,
                submitted_at=submitted_at,
                answers=answers,
                hidden_fields=hidden_fields,
                metadata=metadata,
                calculated_score=calculated_score,
                landing_id=landing_id,
                notion_page_id=notion_page_id,
            )

            logger.info(
                f"Processed TypeForm webhook for response {response_id} from form {form_title}"
            )
            return response
        except Exception as e:
            logger.error(f"Error processing TypeForm webhook: {e}")
            return None

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify the signature of a TypeForm webhook.

        Args:
            payload: Raw webhook payload bytes
            signature: Signature from the webhook request headers

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.error("TypeForm webhook secret not configured")
            return False

        try:
            # Compute HMAC signature
            computed_signature = hmac.new(
                self.webhook_secret.encode(), payload, hashlib.sha256
            ).hexdigest()

            # Compare signatures
            return hmac.compare_digest(computed_signature, signature)
        except Exception as e:
            logger.error(f"Error verifying TypeForm webhook signature: {e}")
            return False

    async def create_webhook(
        self, form_id: str, webhook_url: str, enabled: bool = True
    ) -> Optional[str]:
        """
        Create a webhook for a specific form.

        Args:
            form_id: TypeForm form ID
            webhook_url: URL to send webhook notifications to
            enabled: Whether the webhook should be enabled

        Returns:
            Webhook tag if successful, None otherwise
        """
        if not self.personal_token:
            logger.error("TypeForm credentials not configured")
            return None

        try:
            url = f"{self.base_url}/forms/{form_id}/webhooks"
            headers = {
                "Authorization": f"Bearer {self.personal_token}",
                "Content-Type": "application/json",
            }

            # Generate a unique tag for the webhook
            tag = f"notion-integration-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            payload = {
                "url": webhook_url,
                "enabled": enabled,
                "tag": tag,
                "verify_ssl": True,
            }

            # Add webhook secret if available
            if self.webhook_secret:
                payload["secret"] = self.webhook_secret

            response = requests.put(url, headers=headers, json=payload)
            response.raise_for_status()

            logger.info(f"Created TypeForm webhook for form {form_id}")
            return tag
        except Exception as e:
            logger.error(f"Error creating TypeForm webhook: {e}")
            return None

    async def update_response_with_notion_id(
        self, form_id: str, response_id: str, notion_page_id: str
    ) -> bool:
        """
        Update TypeForm response metadata with Notion page ID.
        Unfortunately, TypeForm API doesn't allow updating response data directly.
        This method is a placeholder for potential future implementation using hidden fields in follow-up forms.

        Args:
            form_id: TypeForm form ID
            response_id: TypeForm response ID
            notion_page_id: Notion page ID to associate with the response

        Returns:
            True if update successful, False otherwise
        """
        # TypeForm doesn't directly support updating response data through the API
        # For now, we'll log this limitation
        logger.warning(
            "TypeForm API doesn't support updating responses. Store mapping in Notion instead."
        )
        return False
