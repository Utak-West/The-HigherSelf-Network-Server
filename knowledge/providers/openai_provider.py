"""
OpenAI embedding provider implementation.

This module provides an implementation of the embedding provider interface
for OpenAI's API.
"""

import asyncio
import json
import os
from typing import Any, Dict, List

import httpx
from loguru import logger

from .base_provider import BaseEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider implementation."""

    def __init__(self):
        """Initialize the OpenAI embedding provider."""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com")
        self.embedding_model = os.environ.get(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"
        )
        self.timeout = int(os.environ.get("OPENAI_TIMEOUT", "30"))

        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            timeout=self.timeout,
        )

    @property
    def provider_name(self) -> str:
        """Get the name of this provider."""
        return "openai"

    @property
    def embedding_dimensions(self) -> int:
        """Get the dimensions of embeddings from this provider."""
        # Map model names to their dimensions
        dimensions = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536,
        }
        return dimensions.get(self.embedding_model, 1536)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            response = await self.client.post(
                "/v1/embeddings",
                json={
                    "model": self.embedding_model,
                    "input": texts,
                    "encoding_format": "float",
                },
            )

            response.raise_for_status()
            data = response.json()

            # Sort embeddings by index to ensure order matches input texts
            sorted_embeddings = sorted(data["data"], key=lambda x: x["index"])
            embeddings = [item["embedding"] for item in sorted_embeddings]

            return embeddings

        except Exception as e:
            logger.error(f"Error getting embeddings from OpenAI: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of this provider.

        Returns:
            Health check results
        """
        try:
            # Try to get an embedding for a simple text
            response = await self.client.post(
                "/v1/embeddings",
                json={
                    "model": self.embedding_model,
                    "input": "health check",
                    "encoding_format": "float",
                },
            )

            response.raise_for_status()

            return {
                "healthy": True,
                "status_code": response.status_code,
                "model": self.embedding_model,
                "provider": self.provider_name,
            }
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return {"healthy": False, "error": str(e), "provider": self.provider_name}

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
