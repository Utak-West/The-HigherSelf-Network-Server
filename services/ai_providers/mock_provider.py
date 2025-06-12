"""
Mock AI Provider for The HigherSelf Network Server.

This module provides a mock AI provider for testing purposes.
"""

import os
import random
from typing import Any, Dict, List, Optional

from loguru import logger

from .base_provider import (AICompletionRequest, AICompletionResponse,
                            AIProvider)


class MockAIProvider(AIProvider):
    """Mock AI provider for testing purposes."""

    def __init__(self, name: str = "mock"):
        """
        Initialize the mock AI provider.

        Args:
            name: Name of the provider
        """
        self.name = name
        self.models = ["mock-gpt", "mock-claude"]
        self.default_model = "mock-gpt"
        self.initialized = False

    def get_provider_name(self) -> str:
        """
        Get the name of the AI provider.

        Returns:
            Provider name string
        """
        return self.name

    async def validate_credentials(self) -> bool:
        """
        Validate the provider credentials.

        Returns:
            True if credentials are valid, False otherwise
        """
        # Mock provider always has valid credentials
        return True

    async def initialize(self) -> bool:
        """
        Initialize the provider.

        Returns:
            True if initialization successful, False otherwise
        """
        self.initialized = True
        logger.info(f"Mock AI provider '{self.name}' initialized")
        return True

    async def get_completion(
        self, request: AICompletionRequest
    ) -> AICompletionResponse:
        """
        Get a completion from the mock AI provider.

        Args:
            request: AICompletionRequest with prompt and parameters

        Returns:
            AICompletionResponse with generated text and metadata
        """
        if not self.initialized:
            success = await self.initialize()
            if not success:
                return AICompletionResponse(
                    text="Error: Mock AI provider initialization failed.",
                    provider=self.name,
                    model=request.model or self.default_model,
                    metadata={"error": "Initialization failed"},
                )

        # Use the specified model or default
        model = request.model or self.default_model

        # Generate a mock response based on the prompt
        response_text = self._generate_mock_response(
            prompt=request.prompt, system_message=request.system_message, model=model
        )

        return AICompletionResponse(
            text=response_text,
            provider=self.name,
            model=model,
            metadata={
                "mock": True,
                "tokens": len(response_text.split()),
                "prompt_tokens": len(request.prompt.split()),
            },
        )

    def _generate_mock_response(
        self, prompt: str, system_message: Optional[str] = None, model: str = "mock-gpt"
    ) -> str:
        """
        Generate a mock response based on the prompt.

        Args:
            prompt: User prompt
            system_message: Optional system message
            model: Model to use

        Returns:
            Generated text
        """
        # Simple responses based on keywords in the prompt
        prompt_lower = prompt.lower()

        # Check for question patterns
        if "what is" in prompt_lower or "tell me about" in prompt_lower:
            return f"This is a mock response about {prompt.split()[-1]}. In a real implementation, this would provide information about the topic."

        if "how to" in prompt_lower or "how do" in prompt_lower:
            return f"Here's a mock explanation of how to {prompt.split()[-1]}:\n1. First step\n2. Second step\n3. Final step"

        if "why" in prompt_lower:
            return f"This is a mock explanation of why {prompt.split()[-1]}. There are several factors to consider..."

        if "when" in prompt_lower:
            return f"The timing for {prompt.split()[-1]} depends on various factors. This is a mock response."

        if "where" in prompt_lower:
            return (
                f"This is a mock response about the location of {prompt.split()[-1]}."
            )

        if "who" in prompt_lower:
            return f"This is a mock response about the person or entity {prompt.split()[-1]}."

        if "list" in prompt_lower or "examples" in prompt_lower:
            return f"Here's a mock list related to {prompt.split()[-1]}:\n- First item\n- Second item\n- Third item"

        if "compare" in prompt_lower:
            return f"This is a mock comparison between different aspects of {prompt.split()[-1]}."

        if "summarize" in prompt_lower or "summary" in prompt_lower:
            return (
                f"This is a mock summary of {prompt.split()[-1]}. The key points are..."
            )

        # Default response
        return f"This is a mock response to your query about {prompt.split()[-1]}. In a real implementation, this would be generated by an AI model."

    async def validate_credentials(self) -> bool:
        """
        Validate the provider credentials.

        Returns:
            True if credentials are valid, False otherwise
        """
        # Mock provider always has valid credentials
        return True

    def get_available_models(self) -> List[str]:
        """
        Get a list of available models.

        Returns:
            List of model identifiers
        """
        return self.models
