"""
Base class for embedding providers.

This module defines the base class that all embedding providers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio
import numpy as np
from loguru import logger


class BaseEmbeddingProvider(ABC):
    """Base class for embedding providers."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the name of this provider."""
        pass
    
    @property
    @abstractmethod
    def embedding_dimensions(self) -> int:
        """Get the dimensions of embeddings from this provider."""
        pass
    
    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of this provider.
        
        Returns:
            Health check results with at minimum a 'healthy' boolean field
        """
        pass
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text.
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector
        """
        embeddings = await self.get_embeddings([text])
        return embeddings[0]
    
    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize an embedding vector to unit length.
        
        Args:
            embedding: Embedding vector
            
        Returns:
            Normalized embedding vector
        """
        embedding_array = np.array(embedding)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            normalized = embedding_array / norm
            return normalized.tolist()
        return embedding
    
    async def batch_get_embeddings(
        self, 
        texts: List[str], 
        batch_size: int = 20
    ) -> List[List[float]]:
        """
        Get embeddings for a list of texts in batches.
        
        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embedding vectors
        """
        results = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                batch_embeddings = await self.get_embeddings(batch)
                results.extend(batch_embeddings)
                logger.debug(f"Processed batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                # Fallback to processing one by one if batch fails
                for j, text in enumerate(batch):
                    try:
                        embedding = await self.get_embedding(text)
                        results.append(embedding)
                        logger.debug(f"Processed item {i+j+1}/{len(texts)}")
                    except Exception as e:
                        logger.error(f"Error processing item {i+j+1}: {e}")
                        # Append a zero vector as a fallback
                        results.append([0.0] * self.embedding_dimensions)
        
        return results