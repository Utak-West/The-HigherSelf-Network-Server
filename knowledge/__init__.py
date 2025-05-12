"""
Knowledge Hub module for The HigherSelf Network Server.

This module provides vector database capabilities for semantic search
and embedding storage integration with Supabase.
"""

from .vector_store import get_vector_store, VectorStore
from .semantic_search import get_semantic_search, SemanticSearch
from .models import (
    EmbeddingMeta,
    VectorRecord,
    ChunkRecord,
    SearchResult,
    SearchQuery,
    EmbeddingRequest
)
from .providers import provider_registry

# Convenience function to get initialized instances
async def initialize_knowledge_hub():
    """Initialize all knowledge hub components."""
    vector_store = get_vector_store()
    await vector_store.initialize()
    
    semantic_search = get_semantic_search()
    await semantic_search.initialize()
    
    await provider_registry.initialize()
    
    return {
        "vector_store": vector_store,
        "semantic_search": semantic_search,
        "provider_registry": provider_registry
    }