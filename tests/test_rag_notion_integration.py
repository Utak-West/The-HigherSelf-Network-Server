#!/usr/bin/env python3
"""
Test script for RAG functionality with Notion integration.

This script tests the RAG (Retrieval Augmented Generation) functionality
with Notion database integration, Crawl4AI, and Aqua Voice services.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add parent directory to path to allow importing from the server codebase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

from knowledge.rag_pipeline import RAGRequest, get_rag_pipeline
from services.ai_router import AIRouter
from services.aqua_voice_service import (
    VoiceTranscriptionRequest,
    get_aqua_voice_service,
)
from services.crawl4ai_service import CrawlConfig, get_crawl4ai_service
from services.knowledge_service import KnowledgeService

# Import required services
from services.notion_service import NotionService


async def test_notion_integration():
    """Test Notion integration with the RAG system."""
    print("\n=== Testing Notion Integration ===\n")

    # Initialize Notion service
    notion_service = NotionService.from_env()

    # Initialize Knowledge service
    knowledge_service = KnowledgeService()
    await knowledge_service.initialize()

    # Get a list of Notion databases
    print("Fetching Notion databases...")
    db_mappings = notion_service.db_mappings

    if not db_mappings:
        print("❌ No Notion database mappings found. Check your environment variables.")
        return False

    print(f"✅ Found {len(db_mappings)} Notion database mappings:")
    for db_name, db_id in db_mappings.items():
        if db_id:
            print(f"  - {db_name}: {db_id}")

    # Test syncing a database to vector store
    print("\nTesting database sync to vector store...")

    # Choose a database to test
    test_db_name = next((name for name, id in db_mappings.items() if id), None)
    if not test_db_name:
        print("❌ No valid database ID found for testing.")
        return False

    test_db_id = db_mappings[test_db_name]
    print(f"Using database '{test_db_name}' with ID: {test_db_id}")

    # Sync the database
    embedding_ids = await knowledge_service.sync_notion_database_to_vector(
        test_db_id, modified_since=None, force_update=False
    )

    if embedding_ids:
        print(
            f"✅ Successfully synced {len(embedding_ids)} pages from '{test_db_name}' database"
        )
        return True
    else:
        print(f"❌ Failed to sync pages from '{test_db_name}' database")
        return False


async def test_crawl4ai():
    """Test Crawl4AI functionality."""
    print("\n=== Testing Crawl4AI Integration ===\n")

    # Initialize Crawl4AI service
    crawl_service = await get_crawl4ai_service()

    # Test URL to crawl
    test_url = "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"

    print(f"Crawling URL: {test_url}")

    # Create crawl config
    config = CrawlConfig(
        url=test_url,
        cache_mode="enabled",
        headless=True,
        content_filter_threshold=0.48,
        tags=["test", "rag"],
        metadata={"test": True},
    )

    # Crawl and store
    result = await crawl_service.crawl_and_store(config)

    if result.get("success", False):
        print(f"✅ Successfully crawled and stored: {test_url}")
        print(f"  - Embedding ID: {result.get('embedding_id')}")
        print(f"  - Content length: {result.get('content_length')} characters")
        return True
    else:
        print(f"❌ Failed to crawl and store: {test_url}")
        print(f"  - Error: {result.get('error')}")
        return False


async def test_rag_pipeline():
    """Test RAG pipeline functionality."""
    print("\n=== Testing RAG Pipeline ===\n")

    # Initialize AI router
    ai_router = AIRouter()
    await ai_router.initialize()

    # Initialize RAG pipeline
    rag_pipeline = await get_rag_pipeline(ai_router)

    # Test query
    test_query = "What is Retrieval Augmented Generation?"

    print(f"Testing RAG query: '{test_query}'")

    # Create RAG request
    request = RAGRequest(
        query=test_query,
        max_tokens=500,
        temperature=0.7,
        content_types=["web_page", "notion_page"],
        search_limit=3,
        similarity_threshold=0.7,
        include_sources=True,
    )

    # Generate completion
    result = await rag_pipeline.generate(request)

    if result.success:
        print(f"✅ Successfully generated RAG completion")
        print(f"\nQuery: {test_query}")
        print(f"\nResponse: {result.text[:200]}...")

        if result.sources:
            print(f"\nSources used ({len(result.sources)}):")
            for i, source in enumerate(result.sources):
                print(
                    f"  {i+1}. {source.title or source.source} (similarity: {source.similarity:.2f})"
                )

        return True
    else:
        print(f"❌ Failed to generate RAG completion")
        print(f"  - Error: {result.error}")
        return False


async def main():
    """Main function to run all tests."""
    print("\n=== RAG Notion Integration Test ===\n")

    # Run tests
    notion_success = await test_notion_integration()
    crawl_success = await test_crawl4ai()
    rag_success = await test_rag_pipeline()

    # Print summary
    print("\n=== Test Summary ===\n")
    print(f"Notion Integration: {'✅ PASSED' if notion_success else '❌ FAILED'}")
    print(f"Crawl4AI Integration: {'✅ PASSED' if crawl_success else '❌ FAILED'}")
    print(f"RAG Pipeline: {'✅ PASSED' if rag_success else '❌ FAILED'}")

    overall_success = notion_success and crawl_success and rag_success
    print(f"\nOverall: {'✅ PASSED' if overall_success else '❌ FAILED'}")

    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
