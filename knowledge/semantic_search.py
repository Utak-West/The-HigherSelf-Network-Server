"""
Semantic search functionality for the Knowledge Hub.

This module provides high-level functions for semantic search using vector embeddings.
It handles the text chunking, embedding generation, and search capabilities.
"""

import asyncio
import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

import nltk
from loguru import logger
from nltk.tokenize import sent_tokenize

from .models import EmbeddingMeta, SearchQuery, SearchResult
from .providers import provider_registry
from .vector_store import get_vector_store

# Try to download nltk data, but don't fail if it's not available
try:
    nltk.download("punkt", quiet=True)
except:
    logger.warning(
        "Failed to download NLTK data. Sentence splitting may be less accurate."
    )


class SemanticSearch:
    """High-level semantic search functionality."""

    def __init__(self):
        """Initialize the semantic search service."""
        self.vector_store = None
        self._initialized = False

    async def initialize(self):
        """Initialize the semantic search service."""
        if self._initialized:
            return

        # Initialize vector store
        from .vector_store import get_vector_store

        self.vector_store = await get_vector_store()

        # Initialize provider registry
        await provider_registry.initialize()

        self._initialized = True

    def _chunk_text(
        self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[str]:
        """
        Split text into chunks for embedding.

        Args:
            text: Text to split
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters

        Returns:
            List of text chunks
        """
        if not text:
            return []

        # First, try to split by newlines to preserve paragraph structure
        paragraphs = [p for p in text.split("\n") if p.strip()]

        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            # If paragraph is longer than chunk_size, split it into sentences
            if len(para) > chunk_size:
                sentences = sent_tokenize(para)
                for sentence in sentences:
                    if current_size + len(sentence) <= chunk_size:
                        current_chunk.append(sentence)
                        current_size += len(sentence)
                    else:
                        # Current chunk is full, save it
                        if current_chunk:
                            chunks.append(" ".join(current_chunk))
                        # Start a new chunk with overlap
                        if len(current_chunk) > 0:
                            # Calculate how many items to keep for overlap
                            overlap_size = 0
                            overlap_items = []

                            for item in reversed(current_chunk):
                                if overlap_size + len(item) <= chunk_overlap:
                                    overlap_items.insert(0, item)
                                    overlap_size += len(item)
                                else:
                                    break

                            current_chunk = overlap_items
                            current_size = overlap_size
                        else:
                            current_chunk = []
                            current_size = 0

                        # Add the current sentence if it fits
                        if len(sentence) <= chunk_size:
                            current_chunk.append(sentence)
                            current_size += len(sentence)
                        else:
                            # The sentence itself is too long, split it
                            words = sentence.split()
                            current_sentence = []
                            current_sentence_size = 0

                            for word in words:
                                if current_sentence_size + len(word) + 1 <= chunk_size:
                                    current_sentence.append(word)
                                    current_sentence_size += len(word) + 1
                                else:
                                    # Add the current sentence part to the chunk
                                    if current_sentence:
                                        sentence_part = " ".join(current_sentence)
                                        current_chunk.append(sentence_part)
                                        current_size += len(sentence_part)

                                    # Check if the chunk is full
                                    if current_size > chunk_size:
                                        chunks.append(" ".join(current_chunk))
                                        current_chunk = []
                                        current_size = 0

                                    # Start a new sentence part
                                    current_sentence = [word]
                                    current_sentence_size = len(word)

                            # Add any remaining sentence part
                            if current_sentence:
                                sentence_part = " ".join(current_sentence)
                                current_chunk.append(sentence_part)
                                current_size += len(sentence_part)
            else:
                # Paragraph fits in a chunk, add it
                if current_size + len(para) <= chunk_size:
                    current_chunk.append(para)
                    current_size += len(para)
                else:
                    # Current chunk is full, save it
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))

                    # Start a new chunk with overlap
                    if len(current_chunk) > 0:
                        # Calculate how many items to keep for overlap
                        overlap_size = 0
                        overlap_items = []

                        for item in reversed(current_chunk):
                            if overlap_size + len(item) <= chunk_overlap:
                                overlap_items.insert(0, item)
                                overlap_size += len(item)
                            else:
                                break

                        current_chunk = overlap_items
                        current_size = overlap_size
                    else:
                        current_chunk = []
                        current_size = 0

                    current_chunk.append(para)
                    current_size += len(para)

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    async def store_and_embed_text(
        self,
        text: str,
        content_type: str,
        metadata: EmbeddingMeta,
        notion_page_id: Optional[str] = None,
        notion_database_id: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Optional[UUID]:
        """
        Store and embed text in the vector store.

        Args:
            text: Text to embed
            content_type: Type of content (e.g., 'page', 'database', 'chunk')
            metadata: Additional metadata about the content
            notion_page_id: Optional Notion page ID
            notion_database_id: Optional Notion database ID
            chunk_size: Size of chunks to split text into
            chunk_overlap: Overlap between chunks

        Returns:
            UUID of the stored embedding record or None if failed
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Get embedding for the full text
            result = await provider_registry.get_embedding(text)

            if not result["success"]:
                logger.error("Failed to generate embedding")
                return None

            # Store the full text embedding
            embedding_id = await self.vector_store.store_embedding(
                content=text,
                embedding=result["embedding"],
                content_type=content_type,
                metadata=metadata,
                provider_name=result["provider"],
                notion_page_id=notion_page_id,
                notion_database_id=notion_database_id,
            )

            if not embedding_id:
                logger.error("Failed to store embedding")
                return None

            # Split text into chunks if it's long
            if len(text) > chunk_size:
                chunks = self._chunk_text(text, chunk_size, chunk_overlap)

                if chunks:
                    # Get embeddings for chunks
                    chunks_result = await provider_registry.get_embeddings(chunks)

                    if chunks_result["success"]:
                        # Store chunk embeddings
                        chunk_ids = await self.vector_store.store_text_chunks(
                            embedding_id=embedding_id,
                            chunks=chunks,
                            chunk_embeddings=chunks_result["embeddings"],
                            metadata=metadata.dict(),
                        )

                        logger.info(
                            f"Stored {len(chunk_ids)} chunks for embedding {embedding_id}"
                        )

            return embedding_id

        except Exception as e:
            logger.error(f"Error storing and embedding text: {e}")
            return None

    async def search(
        self,
        query: str,
        content_types: Optional[List[str]] = None,
        notion_database_id: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7,
        search_chunks: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Perform a semantic search.

        Args:
            query: Query text
            content_types: Optional filter for content types
            notion_database_id: Optional filter for Notion database ID
            limit: Maximum number of results
            threshold: Similarity threshold (0-1, higher is more similar)
            search_chunks: Whether to search in chunks as well as full documents

        Returns:
            List of search results with metadata
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Get embedding for query
            result = await provider_registry.get_embedding(query)

            if not result["success"]:
                logger.error("Failed to generate query embedding")
                return []

            query_embedding = result["embedding"]

            # Search for similar embeddings
            search_results = await self.vector_store.search_embeddings(
                query_embedding=query_embedding,
                content_types=content_types,
                notion_database_id=notion_database_id,
                limit=limit,
                threshold=threshold,
            )

            # Also search in chunks if requested
            chunk_results = []
            if search_chunks:
                chunk_results = await self.vector_store.search_chunks(
                    query_embedding=query_embedding, limit=limit, threshold=threshold
                )

            # Combine and format results
            formatted_results = []

            # Process main document results
            for result in search_results:
                record = result.record
                formatted = {
                    "id": str(record.id),
                    "type": "document",
                    "content_type": record.content_type,
                    "notion_page_id": record.notion_page_id,
                    "notion_database_id": record.notion_database_id,
                    "metadata": record.metadata.dict(),
                    "score": result.score,
                    "distance": result.distance,
                    "source": record.metadata.source,
                    "tags": record.metadata.tags,
                }
                formatted_results.append(formatted)

            # Process chunk results
            for result in chunk_results:
                chunk = result.record
                if isinstance(chunk, list):
                    continue  # Skip if record is somehow a list

                # Get the parent embedding
                embedding = await self.vector_store.get_embedding(chunk.embedding_id)

                formatted = {
                    "id": str(chunk.id),
                    "type": "chunk",
                    "parent_id": str(chunk.embedding_id),
                    "chunk_index": chunk.chunk_index,
                    "chunk_text": chunk.chunk_text,
                    "notion_page_id": embedding.notion_page_id if embedding else None,
                    "notion_database_id": embedding.notion_database_id
                    if embedding
                    else None,
                    "metadata": chunk.metadata,
                    "score": result.score,
                    "distance": result.distance,
                    "source": embedding.metadata.source if embedding else None,
                    "tags": embedding.metadata.tags if embedding else [],
                }
                formatted_results.append(formatted)

            # Sort combined results by score
            formatted_results.sort(key=lambda x: x["score"], reverse=True)

            # Return the top results
            return formatted_results[:limit]

        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            return []


# Singleton instance
_semantic_search_instance = None


async def get_semantic_search() -> SemanticSearch:
    """Get or create the semantic search singleton."""
    global _semantic_search_instance
    if _semantic_search_instance is None:
        _semantic_search_instance = SemanticSearch()
        await _semantic_search_instance.initialize()
    return _semantic_search_instance
