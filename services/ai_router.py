"""
AI Router Service for The HigherSelf Network Server.
This service routes AI requests to the appropriate provider while maintaining Notion as the central hub.
"""

import os
from typing import Dict, List, Any, Optional
from loguru import logger
from pydantic import BaseModel

from services.ai_providers import (
    AIProvider,
    AICompletionRequest,
    AICompletionResponse,
    OpenAIProvider,
    AnthropicProvider
)

# Import mock provider for testing
try:
    from services.ai_providers.mock_provider import MockAIProvider
except ImportError:
    # Mock provider not available
    MockAIProvider = None


class AIRouterConfig(BaseModel):
    """Configuration for the AI Router."""
    default_provider: str = "openai"
    default_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    class Config:
        env_prefix = "AI_ROUTER_"


class AIRouter:
    """
    Router service for AI providers.
    Dynamically selects the appropriate provider based on request requirements.
    Ensures all data is processed and stored in Notion as the central hub.
    """

    def __init__(self):
        """Initialize the AI Router."""
        self.providers: Dict[str, AIProvider] = {}
        self.default_provider = os.environ.get("AI_ROUTER_DEFAULT_PROVIDER", "openai")
        self.default_model = os.environ.get("AI_ROUTER_DEFAULT_MODEL")
        self.initialized = False

    async def initialize(self) -> bool:
        """
        Initialize all AI providers.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize OpenAI provider
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if openai_api_key:
                openai_provider = OpenAIProvider(api_key=openai_api_key)
                if await openai_provider.initialize():
                    self.providers["openai"] = openai_provider
                    logger.info("OpenAI provider initialized")

            # Initialize Anthropic provider
            anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
            if anthropic_api_key:
                anthropic_provider = AnthropicProvider(api_key=anthropic_api_key)
                if await anthropic_provider.initialize():
                    self.providers["anthropic"] = anthropic_provider
                    logger.info("Anthropic provider initialized")

            # Check if at least one provider is available
            if not self.providers:
                logger.warning("No AI providers could be initialized. Using mock provider for testing.")

                # Use mock provider as fallback
                if MockAIProvider:
                    mock_provider = MockAIProvider()
                    if await mock_provider.initialize():
                        self.providers["mock"] = mock_provider
                        self.default_provider = "mock"
                        logger.info("Mock provider initialized as fallback")
                    else:
                        logger.error("Failed to initialize mock provider")
                        return False
                else:
                    logger.error("No AI providers could be initialized and mock provider is not available.")
                    return False

            # Ensure default provider is available
            if self.default_provider not in self.providers:
                self.default_provider = next(iter(self.providers.keys()))
                logger.warning(f"Default provider not available. Using {self.default_provider} instead.")

            self.initialized = True
            logger.info(f"AI Router initialized with providers: {', '.join(self.providers.keys())}")
            return True
        except Exception as e:
            logger.error(f"Error initializing AI Router: {e}")
            return False

    async def get_completion(self,
                           request: AICompletionRequest,
                           provider_name: Optional[str] = None) -> AICompletionResponse:
        """
        Get a completion from the appropriate AI provider.

        Args:
            request: AICompletionRequest with prompt and parameters
            provider_name: Optional name of provider to use (defaults to router's default)

        Returns:
            AICompletionResponse with generated text and metadata
        """
        if not self.initialized:
            success = await self.initialize()
            if not success:
                return AICompletionResponse(
                    text="Error: AI Router initialization failed. Check your API keys and configuration.",
                    provider="none",
                    model="none",
                    metadata={"error": "Initialization failed"}
                )

        # Determine which provider to use
        provider_name = provider_name or self.default_provider

        # Check if any providers are available
        if not self.providers:
            logger.error("No AI providers available")
            return AICompletionResponse(
                text="Error: No AI providers available. Check your API keys and configuration.",
                provider="none",
                model="none",
                metadata={"error": "No providers available"}
            )

        if provider_name not in self.providers:
            logger.warning(f"Requested provider {provider_name} not available. Using {self.default_provider}.")
            provider_name = self.default_provider

            # If default provider is also not available, use the first available provider
            if provider_name not in self.providers:
                provider_name = next(iter(self.providers.keys()))
                logger.warning(f"Default provider not available. Using {provider_name} instead.")

        provider = self.providers[provider_name]

        # Use default model if not specified
        if not request.model and self.default_model:
            request.model = self.default_model

        # Get completion from the selected provider
        try:
            logger.info(f"Routing completion request to {provider_name} provider")
            response = await provider.get_completion(request)
            return response
        except Exception as e:
            logger.error(f"Error getting completion from {provider_name}: {e}")

            # Try fallback to default provider if different from requested
            if provider_name != self.default_provider:
                try:
                    fallback_provider = self.providers[self.default_provider]
                    logger.info(f"Falling back to {self.default_provider} provider")
                    return await fallback_provider.get_completion(request)
                except Exception as fallback_error:
                    logger.error(f"Fallback to {self.default_provider} also failed: {fallback_error}")

            # Return error response
            return AICompletionResponse(
                text=f"Error: {str(e)}",
                provider=provider_name,
                model=request.model or "unknown",
                metadata={"error": str(e)}
            )

    def get_available_providers(self) -> List[str]:
        """
        Get a list of available provider names.

        Returns:
            List of provider names
        """
        return list(self.providers.keys())

    def get_available_models(self, provider_name: Optional[str] = None) -> List[str]:
        """
        Get a list of available models for a specific provider or all providers.

        Args:
            provider_name: Optional name of provider to get models for

        Returns:
            List of model identifiers
        """
        if provider_name and provider_name in self.providers:
            return self.providers[provider_name].get_available_models()

        # If no provider specified or not found, return all models from all providers
        all_models = []
        for provider in self.providers.values():
            all_models.extend(provider.get_available_models())

        return all_models

    def select_provider_for_task(self, request: AICompletionRequest) -> str:
        """
        Intelligently select the best provider for a given task based on the request.

        Args:
            request: AICompletionRequest with prompt and parameters

        Returns:
            Provider name string
        """
        # This method could be enhanced with more sophisticated routing logic
        # based on task requirements, prompt complexity, cost considerations, etc.

        # For now, use a simple approach based on token length and model availability
        try:
            # Estimate token count (very rough approximation)
            estimated_tokens = len(request.prompt.split()) * 1.3

            # For very long prompts, prefer models with larger context windows
            if estimated_tokens > 8000 and "openai" in self.providers:
                return "openai"  # GPT models have large context windows

            # For complex reasoning tasks, prefer Claude
            complex_keywords = ["analyze", "explain", "compare", "evaluate", "synthesize"]
            if any(keyword in request.prompt.lower() for keyword in complex_keywords) and "anthropic" in self.providers:
                return "anthropic"  # Claude excels at complex reasoning

            # Default to the router's default provider
            return self.default_provider
        except Exception as e:
            logger.error(f"Error in provider selection: {e}")
            return self.default_provider
