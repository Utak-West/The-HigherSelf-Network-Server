"""
RAG Router for The HigherSelf Network Server.

This module provides API endpoints for RAG (Retrieval-Augmented Generation)
functionality, enhancing AI completions with relevant context.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from knowledge.rag_pipeline import (RAGPipeline, RAGRequest, RAGResponse,
                                    SourceReference, get_rag_pipeline)
from services.ai_router import AIRouter


# Models
class RAGCompletionRequest(BaseModel):
    """Request for RAG-enhanced AI completion."""

    query: str = Field(..., description="User query or prompt")
    max_tokens: int = Field(1000, description="Maximum number of tokens to generate")
    temperature: float = Field(0.7, description="Temperature for sampling")
    content_types: Optional[List[str]] = Field(
        None, description="Optional filter for content types"
    )
    notion_database_ids: Optional[List[str]] = Field(
        None, description="Optional filter for Notion database IDs"
    )
    search_limit: int = Field(5, description="Maximum number of search results to use")
    similarity_threshold: float = Field(
        0.7, description="Similarity threshold for search results"
    )
    system_message: Optional[str] = Field(
        None, description="Optional system message for the AI"
    )
    include_sources: bool = Field(
        True, description="Whether to include sources in the response"
    )


class RAGCompletionResponse(BaseModel):
    """Response for RAG-enhanced AI completion."""

    text: str = Field(..., description="Generated text")
    sources: List[SourceReference] = Field(
        [], description="Sources used for generation"
    )
    success: bool = Field(..., description="Whether the generation was successful")
    error: Optional[str] = Field(None, description="Error message if generation failed")


# Router
router = APIRouter(
    prefix="/rag",
    tags=["rag"],
    responses={404: {"description": "Not found"}},
)


# Dependencies
async def get_rag_service(ai_router: AIRouter = Depends()) -> RAGPipeline:
    """Get the RAG pipeline."""
    return await get_rag_pipeline(ai_router)


# Endpoints
@router.post("/complete", response_model=RAGCompletionResponse)
async def rag_completion(
    request: RAGCompletionRequest, rag_service: RAGPipeline = Depends(get_rag_service)
) -> RAGCompletionResponse:
    """
    Generate a RAG-enhanced completion.

    Args:
        request: RAG completion request
        rag_service: RAG pipeline

    Returns:
        RAG completion response
    """
    try:
        # Create RAG request
        rag_request = RAGRequest(
            query=request.query,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            content_types=request.content_types,
            notion_database_ids=request.notion_database_ids,
            search_limit=request.search_limit,
            similarity_threshold=request.similarity_threshold,
            system_message=request.system_message,
            include_sources=request.include_sources,
        )

        # Generate completion
        result = await rag_service.generate(rag_request)

        # Convert to response model
        return RAGCompletionResponse(
            text=result.text,
            sources=result.sources,
            success=result.success,
            error=result.error,
        )

    except Exception as e:
        logger.error(f"Error generating RAG completion: {e}")
        return RAGCompletionResponse(text="", sources=[], success=False, error=str(e))


@router.post("/search", response_model=List[SourceReference])
async def semantic_search(
    query: str,
    content_types: Optional[List[str]] = None,
    notion_database_ids: Optional[List[str]] = None,
    limit: int = 5,
    threshold: float = 0.7,
    rag_service: RAGPipeline = Depends(get_rag_service),
) -> List[SourceReference]:
    """
    Perform a semantic search without generating a completion.

    Args:
        query: Search query
        content_types: Optional filter for content types
        notion_database_ids: Optional filter for Notion database IDs
        limit: Maximum number of results
        threshold: Similarity threshold
        rag_service: RAG pipeline

    Returns:
        List of search results
    """
    try:
        # Retrieve context
        search_results = await rag_service._retrieve_context(
            query=query,
            content_types=content_types,
            notion_database_ids=notion_database_ids,
            limit=limit,
            threshold=threshold,
        )

        # Convert to source references
        sources = []
        for result in search_results:
            source_ref = SourceReference(
                id=result["id"],
                content_type=result["content_type"],
                title=result.get("title"),
                url=rag_service._extract_url(result),
                source=result["source"],
                similarity=result["score"],
            )
            sources.append(source_ref)

        return sources

    except Exception as e:
        logger.error(f"Error performing semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))
