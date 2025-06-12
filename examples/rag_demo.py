#!/usr/bin/env python3
"""
RAG Demo for The HigherSelf Network Server.

This example demonstrates how to use the RAG (Retrieval-Augmented Generation)
capabilities of the server to crawl websites, store content, and generate
AI completions enhanced with relevant context.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add parent directory to path to allow importing from the server codebase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from loguru import logger

from knowledge.rag_pipeline import RAGRequest, get_rag_pipeline
from services.ai_router import AIRouter
from services.crawl4ai_service import CrawlConfig, get_crawl4ai_service


async def crawl_and_store_website():
    """Crawl a website and store its content in the vector database."""
    logger.info("Initializing Crawl4AI service...")
    crawl_service = await get_crawl4ai_service()

    # Define the website to crawl
    url = "https://crawl4ai.com"

    # Create crawl configuration
    config = CrawlConfig(
        url=url,
        cache_mode="enabled",
        headless=True,
        content_filter_threshold=0.48,
        tags=["crawl4ai", "documentation", "web_crawler"],
        metadata={"source": "rag_demo", "crawl_time": datetime.now().isoformat()},
    )

    # Crawl and store the website
    logger.info(f"Crawling website: {url}")
    result = await crawl_service.crawl_and_store(config)

    if result["success"]:
        logger.info(f"Successfully crawled and stored {url}")
        logger.info(f"Embedding ID: {result['embedding_id']}")
        logger.info(f"Content length: {result['content_length']} characters")
    else:
        logger.error(f"Failed to crawl {url}: {result.get('error')}")

    return result


async def deep_crawl_website():
    """Perform a deep crawl of a website and store all pages."""
    logger.info("Initializing Crawl4AI service...")
    crawl_service = await get_crawl4ai_service()

    # Define the website to crawl
    url = "https://docs.crawl4ai.com"

    # Create crawl configuration
    config = CrawlConfig(
        url=url,
        cache_mode="enabled",
        headless=True,
        max_depth=2,
        max_pages=10,
        content_filter_threshold=0.48,
        tags=["crawl4ai", "documentation", "web_crawler"],
        metadata={"source": "rag_demo", "crawl_time": datetime.now().isoformat()},
    )

    # Deep crawl and store the website
    logger.info(f"Deep crawling website: {url}")
    result = await crawl_service.deep_crawl_and_store(config)

    if result["success"]:
        logger.info(f"Successfully deep crawled {url}")
        logger.info(f"Pages crawled: {result['pages_crawled']}")
        logger.info(f"Pages stored: {result['pages_stored']}")
        logger.info(f"Embedding IDs: {result['embedding_ids']}")
    else:
        logger.error(f"Failed to deep crawl {url}: {result.get('error')}")

    return result


async def generate_rag_completion(query: str):
    """Generate a RAG-enhanced completion for a query."""
    logger.info("Initializing RAG pipeline...")
    ai_router = AIRouter()
    rag_pipeline = await get_rag_pipeline(ai_router)

    # Create RAG request
    request = RAGRequest(
        query=query,
        max_tokens=1000,
        temperature=0.7,
        content_types=["web_page"],
        search_limit=5,
        similarity_threshold=0.7,
        include_sources=True,
    )

    # Generate completion
    logger.info(f"Generating RAG completion for query: {query}")
    result = await rag_pipeline.generate(request)

    if result.success:
        logger.info("Successfully generated RAG completion")
        logger.info(f"Sources used: {len(result.sources)}")

        # Print the completion
        print("\n" + "=" * 50)
        print(f"Query: {query}")
        print("=" * 50)
        print(result.text)
        print("=" * 50 + "\n")
    else:
        logger.error(f"Failed to generate RAG completion: {result.error}")

    return result


async def main():
    """Run the RAG demo."""
    # Set up logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    # Crawl and store a website
    await crawl_and_store_website()

    # Deep crawl a website
    await deep_crawl_website()

    # Generate RAG completions
    queries = [
        "What is Crawl4AI and what are its main features?",
        "How can I use Crawl4AI for RAG applications?",
        "What are the advantages of using Crawl4AI over other web crawlers?",
    ]

    for query in queries:
        await generate_rag_completion(query)


if __name__ == "__main__":
    asyncio.run(main())
