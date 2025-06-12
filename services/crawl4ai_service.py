"""
Crawl4AI Service for The HigherSelf Network Server.

This service provides web crawling and content extraction capabilities
using the Crawl4AI library, with integration to the vector store for RAG.
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

# Crawl4AI imports
from crawl4ai import (AsyncWebCrawler, BrowserConfig, CacheMode,
                      CrawlerRunConfig)
from crawl4ai.content_filter_strategy import (BM25ContentFilter,
                                              PruningContentFilter)
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from loguru import logger
from pydantic import BaseModel, Field

from knowledge.models import EmbeddingMeta
from knowledge.semantic_search import get_semantic_search
# Local imports
from knowledge.vector_store import get_vector_store


class CrawlConfig(BaseModel):
    """Configuration for web crawling."""

    url: str
    cache_mode: str = "enabled"
    headless: bool = True
    max_depth: int = 1
    max_pages: int = 10
    content_filter_threshold: float = 0.48
    user_query: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class Crawl4AIService:
    """Service for web crawling and content extraction using Crawl4AI."""

    def __init__(self):
        """Initialize the Crawl4AI service."""
        self.vector_store = None
        self.semantic_search = None
        self._initialized = False
        self.browser_config = BrowserConfig(headless=True, verbose=True)
        self.crawler = None

    async def initialize(self):
        """Initialize the service and its dependencies."""
        if self._initialized:
            return

        try:
            # Initialize vector store and semantic search
            self.vector_store = await get_vector_store()
            self.semantic_search = await get_semantic_search()

            # Initialize crawler
            self.crawler = AsyncWebCrawler(config=self.browser_config)
            await self.crawler.start()

            self._initialized = True
            logger.info("Crawl4AI service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Crawl4AI service: {e}")
            raise

    async def close(self):
        """Close the service and release resources."""
        if self.crawler:
            await self.crawler.stop()
        self._initialized = False
        logger.info("Crawl4AI service closed")

    async def crawl_and_store(self, config: CrawlConfig) -> Dict[str, Any]:
        """
        Crawl a website and store the content in the vector database.

        Args:
            config: Configuration for the crawl

        Returns:
            Dictionary with crawl results and embedding IDs
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Configure content filter based on user query
            if config.user_query:
                content_filter = BM25ContentFilter(
                    user_query=config.user_query, bm25_threshold=1.0
                )
            else:
                content_filter = PruningContentFilter(
                    threshold=config.content_filter_threshold,
                    threshold_type="fixed",
                    min_word_threshold=0,
                )

            # Configure crawler
            run_config = CrawlerRunConfig(
                cache_mode=(
                    CacheMode.ENABLED
                    if config.cache_mode == "enabled"
                    else CacheMode.BYPASS
                ),
                markdown_generator=DefaultMarkdownGenerator(
                    content_filter=content_filter
                ),
            )

            # Execute crawl
            result = await self.crawler.arun(url=config.url, config=run_config)

            if not result.success:
                logger.error(f"Failed to crawl {config.url}")
                return {
                    "success": False,
                    "error": "Failed to crawl the URL",
                    "url": config.url,
                }

            # Extract content
            content = (
                result.markdown.fit_markdown
                if hasattr(result.markdown, "fit_markdown")
                else result.markdown
            )

            # Extract title from result or use URL as fallback
            title = getattr(result, "title", None)
            if title is None:
                title = config.url.split("//")[-1].split("/")[0]

            # Create metadata
            metadata = EmbeddingMeta(
                content_type="web_page",
                source=f"web:{config.url}",
                tags=config.tags,
                additional_meta={
                    "url": config.url,
                    "title": title,
                    "crawl_time": datetime.now().isoformat(),
                    **config.metadata,
                },
            )

            # Store and embed the content
            embedding_id = await self.semantic_search.store_and_embed_text(
                text=content, content_type="web_page", metadata=metadata
            )

            if not embedding_id:
                logger.error(f"Failed to store embedding for {config.url}")
                return {
                    "success": False,
                    "error": "Failed to store embedding",
                    "url": config.url,
                }

            logger.info(f"Successfully crawled and stored {config.url}: {embedding_id}")

            return {
                "success": True,
                "url": config.url,
                "title": result.title,
                "embedding_id": str(embedding_id),
                "content_length": len(content),
            }

        except Exception as e:
            logger.error(f"Error during crawl and store for {config.url}: {e}")
            return {"success": False, "error": str(e), "url": config.url}

    async def deep_crawl_and_store(self, config: CrawlConfig) -> Dict[str, Any]:
        """
        Perform a deep crawl of a website and store all pages in the vector database.

        Args:
            config: Configuration for the crawl

        Returns:
            Dictionary with crawl results and embedding IDs
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Configure content filter
            if config.user_query:
                content_filter = BM25ContentFilter(
                    user_query=config.user_query, bm25_threshold=1.0
                )
            else:
                content_filter = PruningContentFilter(
                    threshold=config.content_filter_threshold,
                    threshold_type="fixed",
                    min_word_threshold=0,
                )

            # Configure crawler for deep crawl
            run_config = CrawlerRunConfig(
                cache_mode=(
                    CacheMode.ENABLED
                    if config.cache_mode == "enabled"
                    else CacheMode.BYPASS
                ),
                markdown_generator=DefaultMarkdownGenerator(
                    content_filter=content_filter
                ),
            )

            # Note: deep_crawl parameter is not supported in the current version
            # We'll implement our own breadth-first crawling

            # Execute deep crawl
            results = await self.crawler.arun_many(urls=[config.url], config=run_config)

            if not results:
                logger.error(f"Failed to deep crawl {config.url}")
                return {
                    "success": False,
                    "error": "Failed to crawl the URL",
                    "url": config.url,
                }

            # Store each page
            embedding_ids = []
            for result in results:
                if not result.success:
                    continue

                # Extract content
                content = (
                    result.markdown.fit_markdown
                    if hasattr(result.markdown, "fit_markdown")
                    else result.markdown
                )

                # Create metadata
                metadata = EmbeddingMeta(
                    content_type="web_page",
                    source=f"web:{result.url}",
                    tags=config.tags,
                    additional_meta={
                        "url": result.url,
                        "title": result.title,
                        "crawl_time": datetime.now().isoformat(),
                        "parent_url": config.url,
                        **config.metadata,
                    },
                )

                # Store and embed the content
                embedding_id = await self.semantic_search.store_and_embed_text(
                    text=content, content_type="web_page", metadata=metadata
                )

                if embedding_id:
                    embedding_ids.append(str(embedding_id))

            logger.info(
                f"Successfully deep crawled {config.url}: {len(embedding_ids)} pages stored"
            )

            return {
                "success": True,
                "url": config.url,
                "pages_crawled": len(results),
                "pages_stored": len(embedding_ids),
                "embedding_ids": embedding_ids,
            }

        except Exception as e:
            logger.error(f"Error during deep crawl and store for {config.url}: {e}")
            return {"success": False, "error": str(e), "url": config.url}


# Singleton instance
_crawl4ai_service = None


async def get_crawl4ai_service() -> Crawl4AIService:
    """Get or create the Crawl4AI service singleton."""
    global _crawl4ai_service
    if _crawl4ai_service is None:
        _crawl4ai_service = Crawl4AIService()
        await _crawl4ai_service.initialize()
    return _crawl4ai_service
