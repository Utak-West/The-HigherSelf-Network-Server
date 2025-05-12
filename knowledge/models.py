"""
Data models for the Knowledge Hub.

These models define the core data structures used throughout the Knowledge Hub.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from uuid import UUID


class EmbeddingMeta(BaseModel):
    """Metadata for an embedding."""
    content_type: str
    source: str
    notion_reference: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    additional_meta: Dict[str, Any] = Field(default_factory=dict)


class VectorRecord(BaseModel):
    """A record in the vector store."""
    id: UUID
    notion_page_id: Optional[str] = None
    notion_database_id: Optional[str] = None
    content_type: str
    content_hash: str
    embedding_vector: List[float]
    metadata: EmbeddingMeta
    created_at: datetime
    updated_at: datetime
    embedding_provider: str


class ChunkRecord(BaseModel):
    """A text chunk with its embedding."""
    id: UUID
    embedding_id: UUID
    chunk_index: int
    chunk_text: str
    chunk_embedding: List[float]
    metadata: Dict[str, Any]
    created_at: datetime


class SearchResult(BaseModel):
    """A search result from the vector store."""
    record: Union[VectorRecord, ChunkRecord]
    score: float
    distance: float


class SearchQuery(BaseModel):
    """A search query for the vector store."""
    query_text: str
    limit: int = 10
    content_types: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    notion_database_id: Optional[str] = None
    metadata_filters: Optional[Dict[str, Any]] = None


class EmbeddingRequest(BaseModel):
    """A request to generate an embedding."""
    content: str
    content_type: str
    metadata: EmbeddingMeta
    notion_page_id: Optional[str] = None
    notion_database_id: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None