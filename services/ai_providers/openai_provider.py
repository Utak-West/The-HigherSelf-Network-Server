"""
OpenAI provider implementation for The HigherSelf Network Server.
This provider integrates with OpenAI's API while maintaining Notion as the central data hub.
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

import openai
from loguru import logger
from pydantic import Field

from .base_provider import (
    AICompletionRequest,
    AICompletionResponse,
    AIProvider,
    AIProviderConfig,
)


class OpenAIConfig(AIProviderConfig):
    """Configuration for OpenAI API integration."""

    provider_name: str = "openai"
    api_key: str
    organization_id: Optional[str] = None
    default_model: str = "gpt-4"

    class Config:
        env_prefix = "OPENAI_"


class OpenAIProvider(AIProvider):
    """
    OpenAI provider implementation.
    Interacts with OpenAI's API while ensuring all relevant data is stored in Notion.
    """

    def __init__(
        self,
        api_key: str = None,
        organization_id: str = None,
        default_model: str = "gpt-4",
    ):
        """
        Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key
            organization_id: OpenAI organization ID (optional)
            default_model: Default model to use (e.g., "gpt-4", "gpt-3.5-turbo")
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.organization_id = organization_id or os.environ.get(
            "OPENAI_ORGANIZATION_ID"
        )
        self.default_model = default_model
        self.client = None
        self.available_models = [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "text-davinci-003",
        ]

    async def initialize(self) -> bool:
        """
        Initialize the OpenAI client.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if not self.api_key:
                logger.error("OpenAI API key not configured")
                return False

            # Initialize the OpenAI client
            openai.api_key = self.api_key
            if self.organization_id:
                openai.organization = self.organization_id

            # Test connection with a simple model list call
            await self.validate_credentials()
            logger.info("OpenAI provider initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing OpenAI provider: {e}")
            return False

    async def get_completion(
        self, request: AICompletionRequest
    ) -> AICompletionResponse:
        """
        Get a completion from OpenAI.

        Args:
            request: AICompletionRequest with prompt and parameters

        Returns:
            AICompletionResponse with generated text and metadata
        """
        try:
            # Use specified model or default
            model = request.model or self.default_model

            # Newer models use chat completion API
            if model.startswith(("gpt-4", "gpt-3.5")):
                response = await openai.ChatCompletion.acreate(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant for The HigherSelf Network.",
                        },
                        {"role": "user", "content": request.prompt},
                    ],
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    stop=request.stop_sequences,
                )

                # Extract response text
                if len(response.choices) > 0:
                    text = response.choices[0].message.content
                else:
                    text = ""

                # Create completion response
                completion = AICompletionResponse(
                    text=text,
                    provider="openai",
                    model=model,
                    tokens_used=(
                        response.usage.total_tokens
                        if hasattr(response, "usage")
                        else None
                    ),
                    finish_reason=(
                        response.choices[0].finish_reason
                        if len(response.choices) > 0
                        else None
                    ),
                    metadata={
                        "completion_id": response.id,
                        "created": response.created,
                        "model": response.model,
                    },
                )
            else:
                # Legacy models use completions API
                response = await openai.Completion.acreate(
                    model=model,
                    prompt=request.prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    stop=request.stop_sequences,
                )

                # Extract response text
                if len(response.choices) > 0:
                    text = response.choices[0].text
                else:
                    text = ""

                # Create completion response
                completion = AICompletionResponse(
                    text=text,
                    provider="openai",
                    model=model,
                    tokens_used=(
                        response.usage.total_tokens
                        if hasattr(response, "usage")
                        else None
                    ),
                    finish_reason=(
                        response.choices[0].finish_reason
                        if len(response.choices) > 0
                        else None
                    ),
                    metadata={
                        "completion_id": response.id,
                        "created": response.created,
                        "model": response.model,
                    },
                )

            logger.info(f"Received completion from OpenAI model {model}")
            return completion
        except Exception as e:
            logger.error(f"Error getting completion from OpenAI: {e}")
            # Return a basic response with error information
            return AICompletionResponse(
                text=f"Error: {str(e)}",
                provider="openai",
                model=request.model or self.default_model,
                metadata={"error": str(e)},
            )

    async def validate_credentials(self) -> bool:
        """
        Validate the OpenAI API credentials.

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            # Make a simple API call to test credentials
            models = await openai.Model.alist()
            return True
        except Exception as e:
            logger.error(f"Invalid OpenAI credentials: {e}")
            return False

    def get_provider_name(self) -> str:
        """
        Get the provider name.

        Returns:
            Provider name string
        """
        return "openai"

    def get_available_models(self) -> List[str]:
        """
        Get a list of available OpenAI models.

        Returns:
            List of model identifiers
        """
        return self.available_models
