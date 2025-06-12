"""
Hugging Face provider implementation for The HigherSelf Network Server.
This provider integrates with Hugging Face's API while maintaining Notion as the central data hub.
"""

import json
import os
from typing import Any, Dict, List, Optional

import requests
from loguru import logger

from models.huggingface_model_registry import model_registry

from .base_provider import (
    AICompletionRequest,
    AICompletionResponse,
    AIProvider,
    AIProviderConfig,
)


class HuggingFaceConfig(AIProviderConfig):
    """Configuration for Hugging Face API integration."""

    provider_name: str = "huggingface"
    api_key: str
    default_model: str = "gpt2"

    class Config:
        env_prefix = "HUGGINGFACE_"


class HuggingFaceProvider(AIProvider):
    """
    Hugging Face provider implementation.
    Interacts with Hugging Face's API while ensuring all relevant data is stored in Notion.
    """

    def __init__(self, api_key: str = None, default_model: str = "gpt2"):
        """
        Initialize the Hugging Face provider.

        Args:
            api_key: Hugging Face API key
            default_model: Default model to use (e.g., "gpt2", "facebook/bart-large-cnn")
        """
        self.api_key = api_key or os.environ.get("HUGGINGFACE_API_KEY")
        self.default_model = default_model
        self.api_url = "https://api-inference.huggingface.co/models/"
        self.initialized = False

    def get_provider_name(self) -> str:
        """
        Get the name of the AI provider.

        Returns:
            Provider name string
        """
        return "huggingface"

    async def validate_credentials(self) -> bool:
        """
        Validate the provider credentials.

        Returns:
            True if credentials are valid, False otherwise
        """
        if not self.api_key:
            logger.error("Hugging Face API key not provided")
            return False

        try:
            # Make a simple API call to validate credentials
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                f"{self.api_url}{self.default_model}", headers=headers
            )

            if response.status_code == 200:
                return True
            elif response.status_code == 401 or response.status_code == 403:
                logger.error(
                    f"Hugging Face API authentication failed: {response.status_code}"
                )
                return False
            else:
                # Other errors might not be related to authentication
                logger.warning(
                    f"Hugging Face API returned status code: {response.status_code}"
                )
                return True

        except Exception as e:
            logger.error(f"Error validating Hugging Face credentials: {e}")
            return False

    async def initialize(self) -> bool:
        """
        Initialize the provider.

        Returns:
            True if initialization successful, False otherwise
        """
        if self.initialized:
            return True

        if not self.api_key:
            logger.error("Hugging Face API key not provided")
            return False

        valid_credentials = await self.validate_credentials()
        if not valid_credentials:
            logger.error("Failed to validate Hugging Face credentials")
            return False

        self.initialized = True
        logger.info("Hugging Face provider initialized successfully")
        return True

    def get_available_models(self) -> List[str]:
        """
        Get a list of available models from this provider.

        Returns:
            List of model identifiers
        """
        return model_registry.get_all_model_ids()

    async def get_completion(
        self, request: AICompletionRequest
    ) -> AICompletionResponse:
        """
        Get a completion from the Hugging Face provider.

        Args:
            request: AICompletionRequest with prompt and parameters

        Returns:
            AICompletionResponse with generated text and metadata
        """
        if not self.initialized:
            success = await self.initialize()
            if not success:
                return AICompletionResponse(
                    text="Error: Hugging Face provider initialization failed.",
                    provider=self.get_provider_name(),
                    model=request.model or self.default_model,
                    metadata={"error": "Initialization failed"},
                )

        model = request.model or self.default_model

        # Prepare parameters
        params = {
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_length": request.max_tokens,
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        try:
            # Make API request
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {"inputs": request.prompt, **params}

            response = requests.post(
                f"{self.api_url}{model}", headers=headers, json=payload
            )

            response.raise_for_status()
            result = response.json()

            # Format the response based on model type
            generated_text = self._format_response(result, model)

            # Create response
            return AICompletionResponse(
                text=generated_text,
                provider=self.get_provider_name(),
                model=model,
                metadata={"raw_response": result, "parameters": params},
            )

        except Exception as e:
            error_message = f"Error getting completion from Hugging Face: {str(e)}"
            logger.error(error_message)

            return AICompletionResponse(
                text=f"Error: {error_message}",
                provider=self.get_provider_name(),
                model=model,
                metadata={"error": str(e)},
            )

    def _format_response(self, response: Any, model: str) -> str:
        """Format the response based on the model type."""
        try:
            # Get model metadata from registry
            model_metadata = model_registry.get_model_metadata(model)

            # If we have metadata, use the task type for formatting
            if model_metadata:
                task = model_metadata.task

                # Format based on task type
                if task == "text-generation":
                    if isinstance(response, list) and len(response) > 0:
                        return response[0].get("generated_text", str(response))

                elif task == "summarization":
                    if isinstance(response, list) and len(response) > 0:
                        return response[0].get("summary_text", str(response))

                elif task == "question-answering":
                    if isinstance(response, dict):
                        return response.get("answer", str(response))

                elif task == "translation":
                    if isinstance(response, list) and len(response) > 0:
                        return response[0].get("translation_text", str(response))

                elif task == "sentiment-analysis":
                    if isinstance(response, list) and len(response) > 0:
                        result = response[0]
                        return f"Label: {result.get('label', 'Unknown')}, Score: {result.get('score', 'Unknown')}"

            # Fallback to the old string-based detection if model not in registry
            else:
                # Text generation models like GPT-2
                if "gpt" in model.lower() or "neo" in model.lower():
                    if isinstance(response, list) and len(response) > 0:
                        return response[0].get("generated_text", str(response))

                # Summarization models like BART
                elif "bart" in model.lower() and "cnn" in model.lower():
                    if isinstance(response, list) and len(response) > 0:
                        return response[0].get("summary_text", str(response))

                # Question answering models
                elif "squad" in model.lower() or "roberta" in model.lower():
                    if isinstance(response, dict):
                        return response.get("answer", str(response))

                # Translation models
                elif "opus-mt" in model.lower():
                    if isinstance(response, list) and len(response) > 0:
                        return response[0].get("translation_text", str(response))

                # Sentiment analysis models
                elif "sentiment" in model.lower() or "sst" in model.lower():
                    if isinstance(response, list) and len(response) > 0:
                        result = response[0]
                        return f"Label: {result.get('label', 'Unknown')}, Score: {result.get('score', 'Unknown')}"

            # Default fallback - try to extract text or return as string
            if isinstance(response, list) and len(response) > 0:
                if isinstance(response[0], dict) and "generated_text" in response[0]:
                    return response[0]["generated_text"]

            # Last resort - convert to string
            return json.dumps(response)

        except Exception as e:
            logger.error(f"Error formatting Hugging Face response: {e}")
            return str(response)
