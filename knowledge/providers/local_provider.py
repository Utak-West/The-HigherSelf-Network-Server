"""
Local embedding provider implementation using sentence-transformers.

This module provides a fallback embedding provider that uses locally running
sentence-transformers models instead of an external API.
"""

import os
import asyncio
import threading
from typing import List, Dict, Any, Optional
from loguru import logger
import numpy as np

from .base_provider import BaseEmbeddingProvider


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """Local embedding provider using sentence-transformers."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the local embedding provider.
        
        Args:
            model_name: Optional name of the sentence-transformers model to use.
                        Defaults to 'all-MiniLM-L6-v2' if not specified.
        """
        self.model_name = model_name or os.environ.get(
            "LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model = None
        self.model_lock = threading.Lock()
        self._embedding_dimensions = 384  # Default for all-MiniLM-L6-v2
        
        # Model dimension mapping
        self.model_dimensions = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "paraphrase-multilingual-MiniLM-L12-v2": 384,
            "all-distilroberta-v1": 768
        }
        
        # Set the correct dimensions based on model
        if self.model_name in self.model_dimensions:
            self._embedding_dimensions = self.model_dimensions[self.model_name]
        
        # Load model lazily on first use
    
    @property
    def provider_name(self) -> str:
        """Get the name of this provider."""
        return f"local:{self.model_name}"
    
    @property
    def embedding_dimensions(self) -> int:
        """Get the dimensions of embeddings from this provider."""
        return self._embedding_dimensions
    
    def _load_model(self):
        """Load the sentence-transformers model if not already loaded."""
        if self.model is not None:
            return
        
        with self.model_lock:
            if self.model is not None:
                return
            
            try:
                # Import here to avoid requiring sentence-transformers
                # for users who don't need the local provider
                from sentence_transformers import SentenceTransformer
                
                logger.info(f"Loading sentence-transformers model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                
                # Update dimensions based on actual model
                self._embedding_dimensions = self.model.get_sentence_embedding_dimension()
                logger.info(f"Model loaded with dimension: {self._embedding_dimensions}")
                
            except ImportError:
                logger.error("sentence-transformers not installed. "
                           "Install with: pip install sentence-transformers")
                raise
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                raise
    
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
        
        # Load model if not already loaded
        if self.model is None:
            # Run in a thread to avoid blocking the async event loop
            await asyncio.get_event_loop().run_in_executor(
                None, self._load_model)
        
        try:
            # Run embedding generation in a thread
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.encode(texts, convert_to_numpy=True))
            
            # Convert numpy arrays to lists
            return [embedding.tolist() for embedding in embeddings]
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of this provider.
        
        Returns:
            Health check results
        """
        try:
            if self.model is None:
                # Try to load the model
                await asyncio.get_event_loop().run_in_executor(
                    None, self._load_model)
            
            # Try to generate an embedding for a simple text
            embedding = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.encode("health check", convert_to_numpy=True))
            
            return {
                "healthy": True,
                "model": self.model_name,
                "dimensions": self.embedding_dimensions,
                "provider": self.provider_name
            }
        except Exception as e:
            logger.error(f"Local provider health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "provider": self.provider_name
            }