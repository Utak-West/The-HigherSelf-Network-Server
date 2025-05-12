"""
Vector Store service for interacting with Supabase vector database.

This module provides functionality to store, retrieve, and search vector embeddings
in Supabase using the pgvector extension.
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from uuid import UUID, uuid4
import asyncio
from loguru import logger

from .models import VectorRecord, ChunkRecord, SearchResult, EmbeddingMeta
from .providers import provider_registry
from services.supabase_service import SupabaseService


class VectorStore:
    """Service for interacting with the vector database in Supabase."""
    
    def __init__(self, supabase_service: SupabaseService = None):
        """
        Initialize the vector store service.
        
        Args:
            supabase_service: SupabaseService instance. If not provided,
                              a new instance will be created.
        """
        from services.supabase_service import get_supabase_service
        self.supabase = supabase_service or get_supabase_service()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the vector store."""
        if self._initialized:
            return
        
        # Initialize provider registry if not already initialized
        await provider_registry.initialize()
        
        self._initialized = True
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the vector store.
        
        Returns:
            Health check results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Check if we can connect to Supabase
            result = await self.supabase.execute_sql(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'embeddings')")
            
            table_exists = result[0]['exists'] if result else False
            
            if not table_exists:
                return {
                    "healthy": False,
                    "error": "Embeddings table does not exist in Supabase",
                    "component": "vector_store"
                }
            
            return {
                "healthy": True,
                "tables": ["embeddings", "vector_chunks"],
                "component": "vector_store"
            }
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "component": "vector_store"
            }
    
    def _compute_content_hash(self, content: str) -> str:
        """
        Compute a hash for content to detect changes.
        
        Args:
            content: The content to hash
            
        Returns:
            Content hash as a hexadecimal string
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def store_embedding(
        self,
        content: str,
        embedding: List[float],
        content_type: str,
        metadata: EmbeddingMeta,
        provider_name: str,
        notion_page_id: Optional[str] = None,
        notion_database_id: Optional[str] = None,
    ) -> Optional[UUID]:
        """
        Store an embedding in the vector database.
        
        Args:
            content: The text content that was embedded
            embedding: The embedding vector
            content_type: Type of content (e.g., 'page', 'database', 'chunk')
            metadata: Additional metadata about the content
            provider_name: Name of the provider that generated the embedding
            notion_page_id: Optional Notion page ID
            notion_database_id: Optional Notion database ID
            
        Returns:
            UUID of the stored embedding record or None if failed
        """
        if not self._initialized:
            await self.initialize()
        
        # Compute content hash for deduplication and change detection
        content_hash = self._compute_content_hash(content)
        
        try:
            # Check if this content is already embedded by this provider
            existing = await self.supabase.execute_sql(
                """
                SELECT id::text FROM embeddings 
                WHERE content_hash = $1 AND embedding_provider = $2
                """,
                [content_hash, provider_name]
            )
            
            if existing:
                # Content exists, update it
                embedding_id = UUID(existing[0]['id'])
                
                # Update the embedding
                await self.supabase.execute_sql(
                    """
                    UPDATE embeddings 
                    SET embedding_vector = $1::vector, 
                        metadata = $2::jsonb,
                        updated_at = NOW()
                    WHERE id = $3::uuid
                    """,
                    [embedding, json.dumps(metadata.dict()), str(embedding_id)]
                )
                
                logger.info(f"Updated existing embedding: {embedding_id}")
                return embedding_id
            
            # Insert new embedding
            embedding_id = uuid4()
            
            await self.supabase.execute_sql(
                """
                INSERT INTO embeddings (
                    id, notion_page_id, notion_database_id, content_type,
                    content_hash, embedding_vector, metadata, embedding_provider
                ) VALUES (
                    $1::uuid, $2, $3, $4, $5, $6::vector, $7::jsonb, $8
                )
                """,
                [
                    str(embedding_id), notion_page_id, notion_database_id, content_type,
                    content_hash, embedding, json.dumps(metadata.dict()), provider_name
                ]
            )
            
            logger.info(f"Stored new embedding: {embedding_id}")
            return embedding_id
            
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
            return None
    
    async def store_text_chunks(
        self,
        embedding_id: UUID,
        chunks: List[str],
        chunk_embeddings: List[List[float]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[UUID]:
        """
        Store text chunks with their embeddings.
        
        Args:
            embedding_id: UUID of the parent embedding record
            chunks: List of text chunks
            chunk_embeddings: List of embedding vectors for each chunk
            metadata: Optional metadata to store with each chunk
            
        Returns:
            List of UUIDs of the stored chunk records
        """
        if not self._initialized:
            await self.initialize()
        
        # Validate input
        if len(chunks) != len(chunk_embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        chunk_ids = []
        metadata = metadata or {}
        
        try:
            # First, delete any existing chunks for this embedding
            await self.supabase.execute_sql(
                "DELETE FROM vector_chunks WHERE embedding_id = $1::uuid",
                [str(embedding_id)]
            )
            
            # Insert new chunks
            for i, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
                chunk_id = uuid4()
                chunk_metadata = {
                    **metadata,
                    "chunk_index": i,
                    "chunk_count": len(chunks)
                }
                
                await self.supabase.execute_sql(
                    """
                    INSERT INTO vector_chunks (
                        id, embedding_id, chunk_index, chunk_text,
                        chunk_embedding, metadata
                    ) VALUES (
                        $1::uuid, $2::uuid, $3, $4, $5::vector, $6::jsonb
                    )
                    """,
                    [
                        str(chunk_id), str(embedding_id), i, chunk,
                        embedding, json.dumps(chunk_metadata)
                    ]
                )
                
                chunk_ids.append(chunk_id)
            
            logger.info(f"Stored {len(chunk_ids)} chunks for embedding {embedding_id}")
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Error storing chunks: {e}")
            return []
    
    async def get_embedding(self, embedding_id: UUID) -> Optional[VectorRecord]:
        """
        Get an embedding by ID.
        
        Args:
            embedding_id: UUID of the embedding record
            
        Returns:
            VectorRecord or None if not found
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            result = await self.supabase.execute_sql(
                """
                SELECT 
                    id::text, notion_page_id, notion_database_id, content_type,
                    content_hash, embedding_vector, metadata, 
                    created_at, updated_at, embedding_provider
                FROM embeddings 
                WHERE id = $1::uuid
                """,
                [str(embedding_id)]
            )
            
            if not result:
                return None
            
            row = result[0]
            
            # Parse the metadata
            metadata_dict = row['metadata']
            metadata = EmbeddingMeta.parse_obj(metadata_dict)
            
            # Create the vector record
            record = VectorRecord(
                id=UUID(row['id']),
                notion_page_id=row['notion_page_id'],
                notion_database_id=row['notion_database_id'],
                content_type=row['content_type'],
                content_hash=row['content_hash'],
                embedding_vector=row['embedding_vector'],
                metadata=metadata,
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                embedding_provider=row['embedding_provider']
            )
            
            return record
            
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None
    
    async def get_chunks(self, embedding_id: UUID) -> List[ChunkRecord]:
        """
        Get chunks for an embedding.
        
        Args:
            embedding_id: UUID of the embedding record
            
        Returns:
            List of ChunkRecord objects
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            result = await self.supabase.execute_sql(
                """
                SELECT 
                    id::text, embedding_id::text, chunk_index, chunk_text,
                    chunk_embedding, metadata, created_at
                FROM vector_chunks 
                WHERE embedding_id = $1::uuid
                ORDER BY chunk_index
                """,
                [str(embedding_id)]
            )
            
            if not result:
                return []
            
            chunks = []
            for row in result:
                chunk = ChunkRecord(
                    id=UUID(row['id']),
                    embedding_id=UUID(row['embedding_id']),
                    chunk_index=row['chunk_index'],
                    chunk_text=row['chunk_text'],
                    chunk_embedding=row['chunk_embedding'],
                    metadata=row['metadata'],
                    created_at=row['created_at']
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error getting chunks: {e}")
            return []
    
    async def delete_embedding(self, embedding_id: UUID) -> bool:
        """
        Delete an embedding and its chunks.
        
        Args:
            embedding_id: UUID of the embedding record
            
        Returns:
            True if deletion was successful
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Delete the embedding (cascades to chunks)
            await self.supabase.execute_sql(
                "DELETE FROM embeddings WHERE id = $1::uuid",
                [str(embedding_id)]
            )
            
            logger.info(f"Deleted embedding: {embedding_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting embedding: {e}")
            return False
    
    async def search_embeddings(
        self,
        query_embedding: List[float],
        content_types: Optional[List[str]] = None,
        notion_database_id: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[SearchResult]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: Embedding vector to search with
            content_types: Optional filter for content types
            notion_database_id: Optional filter for Notion database ID
            limit: Maximum number of results
            threshold: Similarity threshold (0-1, higher is more similar)
            
        Returns:
            List of SearchResult objects
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Build the SQL query with filters
            sql = """
                SELECT 
                    id::text, notion_page_id, notion_database_id, content_type,
                    content_hash, metadata, created_at, updated_at,
                    embedding_provider,
                    1 - (embedding_vector <=> $1::vector) as similarity
                FROM embeddings
                WHERE 1 = 1
            """
            params = [query_embedding]
            
            if content_types:
                placeholders = ', '.join([f"${i+2}" for i in range(len(content_types))])
                sql += f" AND content_type IN ({placeholders})"
                params.extend(content_types)
            
            if notion_database_id:
                sql += f" AND notion_database_id = ${len(params) + 1}"
                params.append(notion_database_id)
            
            sql += f" AND 1 - (embedding_vector <=> $1::vector) > {threshold}"
            sql += " ORDER BY similarity DESC"
            sql += f" LIMIT {limit}"
            
            result = await self.supabase.execute_sql(sql, params)
            
            # Process results
            search_results = []
            for row in result:
                # Parse the metadata
                metadata_dict = row['metadata']
                metadata = EmbeddingMeta.parse_obj(metadata_dict)
                
                # Create the vector record
                record = VectorRecord(
                    id=UUID(row['id']),
                    notion_page_id=row['notion_page_id'],
                    notion_database_id=row['notion_database_id'],
                    content_type=row['content_type'],
                    content_hash=row['content_hash'],
                    embedding_vector=[], # We don't need the full vector in search results
                    metadata=metadata,
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    embedding_provider=row['embedding_provider']
                )
                
                # Create search result
                search_result = SearchResult(
                    record=record,
                    score=row['similarity'],
                    distance=1.0 - row['similarity']
                )
                
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching embeddings: {e}")
            return []
    
    async def search_chunks(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[SearchResult]:
        """
        Search for similar text chunks.
        
        Args:
            query_embedding: Embedding vector to search with
            limit: Maximum number of results
            threshold: Similarity threshold (0-1, higher is more similar)
            
        Returns:
            List of SearchResult objects with chunks
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            sql = """
                SELECT 
                    vc.id::text, vc.embedding_id::text, vc.chunk_index, 
                    vc.chunk_text, vc.metadata, vc.created_at,
                    1 - (vc.chunk_embedding <=> $1::vector) as similarity
                FROM vector_chunks vc
                WHERE 1 - (vc.chunk_embedding <=> $1::vector) > $2
                ORDER BY similarity DESC
                LIMIT $3
            """
            
            result = await self.supabase.execute_sql(sql, [
                query_embedding, threshold, limit
            ])
            
            # Process results
            search_results = []
            for row in result:
                # Create the chunk record
                chunk = ChunkRecord(
                    id=UUID(row['id']),
                    embedding_id=UUID(row['embedding_id']),
                    chunk_index=row['chunk_index'],
                    chunk_text=row['chunk_text'],
                    chunk_embedding=[], # We don't need the full vector in search results
                    metadata=row['metadata'],
                    created_at=row['created_at']
                )
                
                # Create search result
                search_result = SearchResult(
                    record=chunk,
                    score=row['similarity'],
                    distance=1.0 - row['similarity']
                )
                
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
            return []


# Singleton instance
_vector_store_instance = None

def get_vector_store() -> VectorStore:
    """Get the singleton VectorStore instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance