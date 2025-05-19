# HigherSelf RAG Engineer

## Description
Specialized mode for enhancing Retrieval Augmented Generation capabilities

## Instructions
- Focus on improving vector embedding strategies
- Optimize retrieval mechanisms for context relevance
- Implement chunking strategies for document processing
- Ensure proper handling of multiple embedding providers
- Design fallback mechanisms for embedding services
- Implement caching for frequently accessed embeddings
- Optimize query construction for semantic search

## Capabilities
- Analyze existing RAG implementation
- Generate optimized embedding code
- Implement retrieval mechanisms
- Design caching strategies
- Create evaluation metrics for retrieval quality

## RAG Implementation Template

```python
"""
Enhanced RAG implementation for The HigherSelf Network Server.

This module provides advanced Retrieval Augmented Generation capabilities
with optimized embedding strategies and context-aware retrieval.
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
import numpy as np
from pydantic import BaseModel, Field

from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define Pydantic models for RAG components

class Document(BaseModel):
    """Represents a document in the knowledge base."""
    id: str = Field(..., description="Unique identifier")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    
class Query(BaseModel):
    """Represents a query to the RAG system."""
    text: str = Field(..., description="Query text")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Query filters")
    top_k: int = Field(5, description="Number of results to return")
    
class RetrievalResult(BaseModel):
    """Represents a retrieval result."""
    document: Document
    score: float = Field(..., description="Relevance score")
    
class RAGResponse(BaseModel):
    """Represents a response from the RAG system."""
    query: str = Field(..., description="Original query")
    results: List[RetrievalResult] = Field(default_factory=list, description="Retrieval results")
    generated_response: Optional[str] = Field(None, description="Generated response")
    processing_time: float = Field(..., description="Processing time in seconds")

# Embedding provider interface

class EmbeddingProvider:
    """Interface for embedding providers."""
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text.
        
        Args:
            text: Text to embed
            
        Returns:
            Vector embedding
        """
        raise NotImplementedError("Embedding providers must implement generate_embedding")
        
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of vector embeddings
        """
        raise NotImplementedError("Embedding providers must implement generate_embeddings")

# Document chunking strategies

def chunk_by_tokens(text: str, max_tokens: int = 512, overlap: int = 50) -> List[str]:
    """
    Chunk text by token count with overlap.
    
    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk
        overlap: Number of tokens to overlap between chunks
        
    Returns:
        List of text chunks
    """
    # Implementation depends on tokenizer
    pass

def chunk_by_sentences(text: str, max_sentences: int = 10, overlap: int = 2) -> List[str]:
    """
    Chunk text by sentence count with overlap.
    
    Args:
        text: Text to chunk
        max_sentences: Maximum sentences per chunk
        overlap: Number of sentences to overlap between chunks
        
    Returns:
        List of text chunks
    """
    # Implementation depends on sentence tokenizer
    pass

# Vector similarity functions

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    return np.dot(vec1_np, vec2_np) / (np.linalg.norm(vec1_np) * np.linalg.norm(vec2_np))

# RAG Pipeline

class RAGPipeline:
    """
    Enhanced RAG pipeline with optimized retrieval and response generation.
    """
    
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: Any,  # Vector store interface
        llm_provider: Any,  # LLM provider interface
        cache_enabled: bool = True,
        cache_ttl: int = 3600  # 1 hour
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            embedding_provider: Provider for generating embeddings
            vector_store: Vector store for document storage and retrieval
            llm_provider: LLM provider for response generation
            cache_enabled: Whether to enable caching
            cache_ttl: Cache time-to-live in seconds
        """
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.llm_provider = llm_provider
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.embedding_cache = {}  # Simple in-memory cache
        
    async def process_query(self, query: Query) -> RAGResponse:
        """
        Process a query through the RAG pipeline.
        
        Args:
            query: Query to process
            
        Returns:
            RAG response with retrieval results and generated response
        """
        start_time = datetime.now()
        
        # Generate query embedding
        if not query.embedding:
            query.embedding = await self.embedding_provider.generate_embedding(query.text)
        
        # Retrieve relevant documents
        results = await self.retrieve_documents(query)
        
        # Generate response
        context = self.prepare_context(results)
        response = await self.generate_response(query.text, context)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return RAGResponse(
            query=query.text,
            results=results,
            generated_response=response,
            processing_time=processing_time
        )
        
    async def retrieve_documents(self, query: Query) -> List[RetrievalResult]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Query with embedding
            
        Returns:
            List of retrieval results
        """
        # Implement vector store retrieval
        pass
        
    def prepare_context(self, results: List[RetrievalResult]) -> str:
        """
        Prepare context from retrieval results for response generation.
        
        Args:
            results: Retrieval results
            
        Returns:
            Formatted context string
        """
        # Format retrieved documents into context
        pass
        
    async def generate_response(self, query: str, context: str) -> str:
        """
        Generate a response using the LLM provider.
        
        Args:
            query: Original query text
            context: Context from retrieved documents
            
        Returns:
            Generated response
        """
        # Implement LLM response generation
        pass
```
