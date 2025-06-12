"""
Knowledge base search tool for the RAG AI agent.
"""

import os
import sys
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Add parent directory to path to allow relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.setup import SupabaseClient
from document_processing.embeddings import EmbeddingGenerator


# Define the search parameters model
class KnowledgeBaseSearchParams(BaseModel):
    """
    Parameters for the knowledge base search tool.
    """

    query: str = Field(
        ...,
        description="The search query to find relevant information in the knowledge base",
    )
    max_results: int = Field(
        5, description="Maximum number of results to return (default: 5)"
    )
    source_filter: Optional[str] = Field(
        None, description="Optional filter to search only within a specific source"
    )


# Define the search result model
class KnowledgeBaseSearchResult(BaseModel):
    """
    Result from the knowledge base search.
    """

    content: str = Field(..., description="Content of the document chunk")
    source: str = Field(..., description="Source of the document chunk")
    source_type: str = Field(..., description="Type of source (e.g., 'pdf', 'text')")
    similarity: float = Field(
        ..., description="Similarity score between the query and the document"
    )
    metadata: Dict[str, Any] = Field(
        {}, description="Additional metadata about the document"
    )


class KnowledgeBaseSearchTool:
    """
    Tool for searching the knowledge base using vector embeddings.
    """

    def __init__(
        self,
        supabase_client: SupabaseClient = None,
        embedding_generator: EmbeddingGenerator = None,
    ):
        """
        Initialize the knowledge base search tool.

        Args:
            supabase_client: Optional SupabaseClient instance
            embedding_generator: Optional EmbeddingGenerator instance
        """
        self.supabase_client = supabase_client or SupabaseClient()
        self.embedding_generator = embedding_generator or EmbeddingGenerator()

    async def search(
        self, params: KnowledgeBaseSearchParams
    ) -> List[KnowledgeBaseSearchResult]:
        """
        Search the knowledge base for relevant information.

        Args:
            params: Search parameters

        Returns:
            List of search results
        """
        # Generate embedding for the query
        query_embedding = await self.embedding_generator.generate_embedding(
            params.query
        )

        # Prepare search filters
        filters = {}
        if params.source_filter:
            filters["source"] = params.source_filter

        # Search the vector database
        results = await self.supabase_client.search_vectors(
            embedding=query_embedding, limit=params.max_results, filters=filters
        )

        # Format results
        search_results = []
        for result in results:
            search_results.append(
                KnowledgeBaseSearchResult(
                    content=result["content"],
                    source=result["source"],
                    source_type=result["source_type"],
                    similarity=result["similarity"],
                    metadata=result.get("metadata", {}),
                )
            )

        return search_results

    async def add_to_knowledge_base(
        self,
        content: str,
        source: str,
        source_type: str,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Add content to the knowledge base.

        Args:
            content: Content to add
            source: Source of the content
            source_type: Type of source
            metadata: Additional metadata

        Returns:
            ID of the added content
        """
        # Generate embedding for the content
        content_embedding = await self.embedding_generator.generate_embedding(content)

        # Add to vector database
        content_id = await self.supabase_client.insert_vector(
            content=content,
            embedding=content_embedding,
            source=source,
            source_type=source_type,
            metadata=metadata or {},
        )

        return content_id
