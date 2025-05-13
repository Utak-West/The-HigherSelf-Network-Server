"""
Embedding providers for The HigherSelf Network Server.

This module provides a registry of embedding providers and implementations
for different embedding models.
"""

import os
import json
import random
from typing import List, Dict, Any, Optional, Union
import asyncio
from loguru import logger

import numpy as np


class EmbeddingProvider:
    """Base class for embedding providers."""

    def __init__(self, name: str):
        """
        Initialize the embedding provider.

        Args:
            name: Name of the provider
        """
        self.name = name
        self._initialized = False

    async def initialize(self):
        """Initialize the provider."""
        self._initialized = True

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        raise NotImplementedError("Subclasses must implement generate_embedding")


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing."""

    def __init__(self, name: str = "mock", dimension: int = 1536):
        """
        Initialize the mock embedding provider.

        Args:
            name: Name of the provider
            dimension: Dimension of the embedding vectors
        """
        super().__init__(name)
        self.dimension = dimension

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a mock embedding for text.

        Args:
            text: Text to embed

        Returns:
            Mock embedding vector
        """
        if not self._initialized:
            await self.initialize()

        # Generate a deterministic embedding based on the text
        # This ensures the same text always gets the same embedding
        random.seed(hash(text) % 2**32)
        embedding = [random.uniform(-1, 1) for _ in range(self.dimension)]

        # Normalize the embedding
        norm = sum(x**2 for x in embedding) ** 0.5
        embedding = [x / norm for x in embedding]

        return embedding


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(self, name: str = "openai", model: str = "text-embedding-3-small"):
        """
        Initialize the OpenAI embedding provider.

        Args:
            name: Name of the provider
            model: OpenAI model to use
        """
        super().__init__(name)
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")

    async def initialize(self):
        """Initialize the provider."""
        if not self.api_key:
            logger.warning("OpenAI API key not found, using mock provider")
            self.mock_provider = MockEmbeddingProvider(f"{self.name}_mock")
            await self.mock_provider.initialize()

        self._initialized = True

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding using OpenAI.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if not self._initialized:
            await self.initialize()

        # If no API key, use mock provider
        if not self.api_key:
            return await self.mock_provider.generate_embedding(text)

        try:
            import openai

            # Create client
            client = openai.OpenAI(api_key=self.api_key)

            # Generate embedding
            response = client.embeddings.create(
                input=text,
                model=self.model
            )

            # Extract embedding
            embedding = response.data[0].embedding

            return embedding

        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}")

            # Fall back to mock provider
            mock_provider = MockEmbeddingProvider(f"{self.name}_mock")
            await mock_provider.initialize()
            return await mock_provider.generate_embedding(text)


class ProviderRegistry:
    """Registry of embedding providers."""

    def __init__(self):
        """Initialize the provider registry."""
        self.providers = {}
        self._initialized = False

    async def initialize(self):
        """Initialize the provider registry."""
        if self._initialized:
            return

        # Try to initialize primary embedding provider (Anthropic)
        try:
            from knowledge.providers.local_provider import LocalEmbeddingProvider
            local_provider = LocalEmbeddingProvider()
            await self.register_provider(local_provider)
        except Exception as e:
            logger.warning(f"Failed to initialize primary embedding provider: {e}")

        # Try to initialize secondary embedding provider (OpenAI)
        try:
            await self.register_provider(OpenAIEmbeddingProvider())
        except Exception as e:
            logger.warning(f"Failed to initialize secondary embedding provider: {e}")

        # Always register mock provider as fallback
        await self.register_provider(MockEmbeddingProvider())

        self._initialized = True

    async def register_provider(self, provider: EmbeddingProvider):
        """
        Register an embedding provider.

        Args:
            provider: EmbeddingProvider instance
        """
        if not provider._initialized:
            await provider.initialize()

        self.providers[provider.name] = provider
        logger.info(f"Registered embedding provider: {provider.name}")

    def get_provider(self, name: str) -> Optional[EmbeddingProvider]:
        """
        Get an embedding provider by name.

        Args:
            name: Name of the provider

        Returns:
            EmbeddingProvider instance or None if not found
        """
        return self.providers.get(name)

    async def get_embedding(self, text: str, provider_name: str = "openai") -> Dict[str, Any]:
        """
        Generate an embedding for text.

        Args:
            text: Text to embed
            provider_name: Name of the provider to use

        Returns:
            Dictionary with embedding results
        """
        if not self._initialized:
            await self.initialize()

        provider = self.get_provider(provider_name)
        if not provider:
            logger.warning(f"Provider '{provider_name}' not found, using mock provider")
            provider = self.get_provider("mock")
            if not provider:
                # Create and register a mock provider
                provider = MockEmbeddingProvider()
                await self.register_provider(provider)

        try:
            embedding = await provider.generate_embedding(text)

            return {
                "success": True,
                "embedding": embedding,
                "provider": provider.name
            }
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_embeddings(self, texts: List[str], provider_name: str = "openai") -> Dict[str, Any]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            provider_name: Name of the provider to use

        Returns:
            Dictionary with embedding results
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Generate embeddings in parallel
            tasks = [self.get_embedding(text, provider_name) for text in texts]
            results = await asyncio.gather(*tasks)

            # Check if all embeddings were successful
            if all(result["success"] for result in results):
                return {
                    "success": True,
                    "embeddings": [result["embedding"] for result in results],
                    "provider": results[0]["provider"]
                }
            else:
                # Find the first error
                error = next((result["error"] for result in results if not result["success"]), "Unknown error")
                return {
                    "success": False,
                    "error": error
                }
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
provider_registry = ProviderRegistry()
