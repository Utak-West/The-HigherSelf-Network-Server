"""
Anthropic provider implementation for The HigherSelf Network Server.
This provider integrates with Anthropic's API while maintaining Notion as the central data hub.
"""

import json
import os
from typing import Any, Dict, List, Optional

import requests
from loguru import logger

from .base_provider import (
    AICompletionRequest,
    AICompletionResponse,
    AIProvider,
    AIProviderConfig,
)


class AnthropicConfig(AIProviderConfig):
    """Configuration for Anthropic API integration."""

    provider_name: str = "anthropic"
    api_key: str
    default_model: str = "claude-2"

    class Config:
        env_prefix = "ANTHROPIC_"


class AnthropicProvider(AIProvider):
    """
    Anthropic provider implementation for Claude models.
    Interacts with Anthropic's API while ensuring all relevant data is stored in Notion.
    """

    def __init__(self, api_key: str = None, default_model: str = "claude-2"):
        """
        Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key
            default_model: Default model to use (e.g., "claude-2", "claude-instant-1")
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.default_model = default_model
        self.base_url = "https://api.anthropic.com/v1"
        self.available_models = ["claude-2", "claude-instant-1", "claude-2.1"]

    async def initialize(self) -> bool:
        """
        Initialize the Anthropic client.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if not self.api_key:
                logger.error("Anthropic API key not configured")
                return False

            # Test API key with a simple validation call
            valid = await self.validate_credentials()
            if valid:
                logger.info("Anthropic provider initialized successfully")
                return True
            else:
                logger.error(
                    "Failed to initialize Anthropic provider: invalid credentials"
                )
                return False
        except Exception as e:
            logger.error(f"Error initializing Anthropic provider: {e}")
            return False

    async def get_completion(
        self, request: AICompletionRequest
    ) -> AICompletionResponse:
        """
        Get a completion from Anthropic's Claude.

        Args:
            request: AICompletionRequest with prompt and parameters

        Returns:
            AICompletionResponse with generated text and metadata
        """
        try:
            # Use specified model or default
            model = request.model or self.default_model

            # Anthropic requires a specific format for the prompts with \n\nHuman: and \n\nAssistant:
            prompt = f"\\n\\nHuman: {request.prompt}\\n\\nAssistant:"

            url = f"{self.base_url}/complete"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "anthropic-version": "2023-06-01",
            }

            payload = {
                "prompt": prompt,
                "model": model,
                "max_tokens_to_sample": request.max_tokens or 1000,
                "temperature": request.temperature or 0.7,
                "top_p": request.top_p or 1.0,
            }

            if request.stop_sequences:
                payload["stop_sequences"] = request.stop_sequences

            # Make the API request
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            # Extract completion text
            completion_text = data.get("completion", "")

            # Create the response object
            completion = AICompletionResponse(
                text=completion_text,
                provider="anthropic",
                model=model,
                tokens_used=None,  # Anthropic doesn't provide token count in the response
                finish_reason=data.get("stop_reason"),
                metadata={
                    "stop": data.get("stop"),
                    "stop_reason": data.get("stop_reason"),
                    "model": model,
                },
            )

            logger.info(f"Received completion from Anthropic model {model}")
            return completion
        except Exception as e:
            logger.error(f"Error getting completion from Anthropic: {e}")
            # Return a basic response with error information
            return AICompletionResponse(
                text=f"Error: {str(e)}",
                provider="anthropic",
                model=request.model or self.default_model,
                metadata={"error": str(e)},
            )

    async def validate_credentials(self) -> bool:
        """
        Validate the Anthropic API credentials.

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            # Make a minimal API call to validate credentials
            url = f"{self.base_url}/complete"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "anthropic-version": "2023-06-01",
            }

            # Minimal payload to test credentials
            payload = {
                "prompt": "\\n\\nHuman: Hi\\n\\nAssistant:",
                "model": self.default_model,
                "max_tokens_to_sample": 1,
                "temperature": 0,
            }

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            return True
        except Exception as e:
            logger.error(f"Invalid Anthropic credentials: {e}")
            return False

    def get_provider_name(self) -> str:
        """
        Get the provider name.

        Returns:
            Provider name string
        """
        return "anthropic"

    def get_available_models(self) -> List[str]:
        """
        Get a list of available Anthropic models.

        Returns:
            List of model identifiers
        """
        return self.available_models
