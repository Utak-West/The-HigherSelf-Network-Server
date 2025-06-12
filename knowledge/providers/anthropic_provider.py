"""
Anthropic embedding provider implementation.

This module provides an implementation of the embedding provider interface
for Anthropic's API.
"""

import asyncio
import json
import os
from typing import Any, Dict, List

import httpx
from loguru import logger

from .base_provider import BaseEmbeddingProvider


class AnthropicEmbeddingProvider(BaseEmbeddingProvider):
    """Anthropic embedding provider implementation."""

    def __init__(self):
        """Initialize the Anthropic embedding provider."""
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.api_base = os.environ.get(
            "ANTHROPIC_API_BASE", "https://api.anthropic.com"
        )
        self.embedding_model = os.environ.get(
            "ANTHROPIC_EMBEDDING_MODEL", "claude-3-haiku-20240307"
        )
        self.timeout = int(os.environ.get("ANTHROPIC_TIMEOUT", "30"))

        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            timeout=self.timeout,
        )

    @property
    def provider_name(self) -> str:
        """Get the name of this provider."""
        return "anthropic"

    @property
    def embedding_dimensions(self) -> int:
        """Get the dimensions of embeddings from this provider."""
        return 1536  # Claude embeddings dimension

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

        embeddings = []
        for text in texts:
            try:
                response = await self.client.post(
                    "/v1/embeddings",
                    json={
                        "model": self.embedding_model,
                        "input": text,
                        "encoding_format": "float",
                    },
                )

                response.raise_for_status()
                data = response.json()

                # Extract embedding from response
                embedding = data["embeddings"][0]["embedding"]
                embeddings.append(embedding)

            except Exception as e:
                logger.error(f"Error getting embedding from Anthropic: {e}")
                raise

        return embeddings

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
            logger.error(f"Anthropic health check failed: {e}")
            return {"healthy": False, "error": str(e), "provider": self.provider_name}

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
