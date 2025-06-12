"""
Knowledge Hub module for The HigherSelf Network Server.

This module provides vector database capabilities for semantic search
and embedding storage integration with Supabase.
"""

from .models import (ChunkRecord, EmbeddingMeta, EmbeddingRequest, SearchQuery,
                     SearchResult, VectorRecord)
from .providers import provider_registry
from .semantic_search import SemanticSearch, get_semantic_search
from .vector_store import VectorStore, get_vector_store


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
        "provider_registry": provider_registry,
    }
