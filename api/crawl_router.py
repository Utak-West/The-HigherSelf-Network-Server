"""
Crawl Router for The HigherSelf Network Server.

This module provides API endpoints for web crawling and content retrieval.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field, HttpUrl

from services.crawl4ai_service import Crawl4AIService, CrawlConfig, get_crawl4ai_service


# Models
class CrawlRequest(BaseModel):
    """Request for crawling a URL."""

    url: str = Field(..., description="URL to crawl")
    cache_mode: str = Field("enabled", description="Cache mode (enabled or bypass)")
    headless: bool = Field(True, description="Whether to run browser in headless mode")
    content_filter_threshold: float = Field(
        0.48, description="Content filter threshold"
    )
    user_query: Optional[str] = Field(None, description="User query for BM25 filtering")
    tags: List[str] = Field([], description="Tags for the crawled content")
    metadata: Dict[str, Any] = Field({}, description="Additional metadata")


class DeepCrawlRequest(CrawlRequest):
    """Request for deep crawling a website."""

    max_depth: int = Field(1, description="Maximum crawl depth")
    max_pages: int = Field(10, description="Maximum number of pages to crawl")


class CrawlResponse(BaseModel):
    """Response for crawl requests."""

    success: bool = Field(..., description="Whether the crawl was successful")
    url: str = Field(..., description="URL that was crawled")
    embedding_id: Optional[str] = Field(None, description="ID of the stored embedding")
    content_length: Optional[int] = Field(
        None, description="Length of the extracted content"
    )
    title: Optional[str] = Field(None, description="Title of the page")
    error: Optional[str] = Field(None, description="Error message if crawl failed")


class DeepCrawlResponse(BaseModel):
    """Response for deep crawl requests."""

    success: bool = Field(..., description="Whether the crawl was successful")
    url: str = Field(..., description="URL that was crawled")
    pages_crawled: Optional[int] = Field(None, description="Number of pages crawled")
    pages_stored: Optional[int] = Field(None, description="Number of pages stored")
    embedding_ids: Optional[List[str]] = Field(
        None, description="IDs of the stored embeddings"
    )
    error: Optional[str] = Field(None, description="Error message if crawl failed")


# Router
router = APIRouter(
    prefix="/crawl",
    tags=["crawl"],
    responses={404: {"description": "Not found"}},
)


# Dependencies
async def get_crawl_service() -> Crawl4AIService:
    """Get the Crawl4AI service."""
    return await get_crawl4ai_service()


# Endpoints
@router.post("/url", response_model=CrawlResponse)
async def crawl_url(
    request: CrawlRequest, crawl_service: Crawl4AIService = Depends(get_crawl_service)
) -> CrawlResponse:
    """
    Crawl a URL and store the content in the vector database.

    Args:
        request: Crawl request
        crawl_service: Crawl4AI service

    Returns:
        Crawl response
    """
    try:
        # Create crawl config
        config = CrawlConfig(
            url=request.url,
            cache_mode=request.cache_mode,
            headless=request.headless,
            content_filter_threshold=request.content_filter_threshold,
            user_query=request.user_query,
            tags=request.tags,
            metadata=request.metadata,
        )

        # Crawl and store
        result = await crawl_service.crawl_and_store(config)

        # Convert to response model
        return CrawlResponse(**result)

    except Exception as e:
        logger.error(f"Error crawling URL {request.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deep", response_model=DeepCrawlResponse)
async def deep_crawl(
    request: DeepCrawlRequest,
    crawl_service: Crawl4AIService = Depends(get_crawl_service),
) -> DeepCrawlResponse:
    """
    Perform a deep crawl of a website and store all pages in the vector database.

    Args:
        request: Deep crawl request
        crawl_service: Crawl4AI service

    Returns:
        Deep crawl response
    """
    try:
        # Create crawl config
        config = CrawlConfig(
            url=request.url,
            cache_mode=request.cache_mode,
            headless=request.headless,
            max_depth=request.max_depth,
            max_pages=request.max_pages,
            content_filter_threshold=request.content_filter_threshold,
            user_query=request.user_query,
            tags=request.tags,
            metadata=request.metadata,
        )

        # Deep crawl and store
        result = await crawl_service.deep_crawl_and_store(config)

        # Convert to response model
        return DeepCrawlResponse(**result)

    except Exception as e:
        logger.error(f"Error deep crawling URL {request.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/background", response_model=Dict[str, Any])
async def background_crawl(
    request: DeepCrawlRequest,
    background_tasks: BackgroundTasks,
    crawl_service: Crawl4AIService = Depends(get_crawl_service),
) -> Dict[str, Any]:
    """
    Start a background crawl task.

    Args:
        request: Deep crawl request
        background_tasks: FastAPI background tasks
        crawl_service: Crawl4AI service

    Returns:
        Task information
    """
    try:
        # Create crawl config
        config = CrawlConfig(
            url=request.url,
            cache_mode=request.cache_mode,
            headless=request.headless,
            max_depth=request.max_depth,
            max_pages=request.max_pages,
            content_filter_threshold=request.content_filter_threshold,
            user_query=request.user_query,
            tags=request.tags,
            metadata=request.metadata,
        )

        # Add task to background
        task_id = str(uuid4())
        background_tasks.add_task(crawl_service.deep_crawl_and_store, config)

        return {
            "task_id": task_id,
            "status": "started",
            "url": request.url,
            "message": f"Background crawl started for {request.url}",
        }

    except Exception as e:
        logger.error(f"Error starting background crawl for {request.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
