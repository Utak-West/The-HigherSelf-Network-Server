"""
Registry for embedding providers with fallback capability.

This module provides a registry for managing embedding providers with
priority-based fallback capabilities.
"""

import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from loguru import logger

from .base_provider import BaseEmbeddingProvider


class ProviderPriority(Enum):
    """Priority levels for embedding providers."""

    PRIMARY = 1
    SECONDARY = 2
    FALLBACK = 3


class EmbeddingProviderRegistry:
    """Registry for embedding providers with fallback capability."""

    def __init__(self):
        """Initialize the registry."""
        self.providers: Dict[ProviderPriority, BaseEmbeddingProvider] = {}
        self.initialized = False

    async def initialize(self):
        """Initialize all providers."""
        if self.initialized:
            return

        # Lazy import to avoid circular dependencies
        from .anthropic_provider import AnthropicEmbeddingProvider
        from .local_provider import LocalEmbeddingProvider
        from .openai_provider import OpenAIEmbeddingProvider

        # Set up providers with priority
        try:
            # Primary provider (Anthropic)
            try:
                anthropic_provider = AnthropicEmbeddingProvider()
                self.providers[ProviderPriority.PRIMARY] = anthropic_provider
                logger.info(
                    f"Initialized primary embedding provider: {anthropic_provider.provider_name}"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize primary embedding provider: {e}")

            # Secondary provider (OpenAI)
            try:
                openai_provider = OpenAIEmbeddingProvider()
                self.providers[ProviderPriority.SECONDARY] = openai_provider
                logger.info(
                    f"Initialized secondary embedding provider: {openai_provider.provider_name}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize secondary embedding provider: {e}"
                )

            # Fallback provider (Local)
            try:
                local_provider = LocalEmbeddingProvider()
                self.providers[ProviderPriority.FALLBACK] = local_provider
                logger.info(
                    f"Initialized fallback embedding provider: {local_provider.provider_name}"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize fallback embedding provider: {e}")

            if not self.providers:
                raise RuntimeError("No embedding providers could be initialized")

            self.initialized = True
        except Exception as e:
            logger.error(f"Error initializing embedding providers: {e}")
            raise

    async def get_embeddings(self, texts: List[str]) -> Dict[str, Any]:
        """
        Get embeddings with fallback capability.

        Args:
            texts: List of text strings to embed

        Returns:
            Dict with provider name, embeddings, and success status
        """
        if not self.initialized:
            await self.initialize()

        # Try providers in priority order
        for priority in sorted(ProviderPriority, key=lambda p: p.value):
            provider = self.providers.get(priority)
            if not provider:
                continue

            try:
                # Check provider health first
                health = await provider.health_check()
                if not health.get("healthy", False):
                    logger.warning(
                        f"Provider {provider.provider_name} is not healthy, trying next"
                    )
                    continue

                # Get embeddings from this provider
                embeddings = await provider.get_embeddings(texts)

                return {
                    "provider": provider.provider_name,
                    "embeddings": embeddings,
                    "success": True,
                }
            except Exception as e:
                logger.error(
                    f"Error getting embeddings from {provider.provider_name}: {e}"
                )
                # Continue to next provider

        # All providers failed
        logger.error("All embedding providers failed")
        return {"provider": None, "embeddings": None, "success": False}

    async def get_embedding(self, text: str) -> Dict[str, Any]:
        """
        Get embedding for a single text with fallback capability.

        Args:
            text: Text string to embed

        Returns:
            Dict with provider name, embedding, and success status
        """
        result = await self.get_embeddings([text])

        if result["success"]:
            return {
                "provider": result["provider"],
                "embedding": result["embeddings"][0],
                "success": True,
            }

        return {"provider": None, "embedding": None, "success": False}

    def register_provider(
        self, provider: BaseEmbeddingProvider, priority: ProviderPriority
    ):
        """
        Register a provider with a specified priority.

        Args:
            provider: Provider instance to register
            priority: Priority level for this provider
        """
        self.providers[priority] = provider
        logger.info(
            f"Registered embedding provider: {provider.provider_name} with priority {priority.name}"
        )


# Singleton instance
provider_registry = EmbeddingProviderRegistry()
