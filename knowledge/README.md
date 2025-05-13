# Knowledge Module

The Knowledge module provides Retrieval Augmented Generation (RAG) capabilities for The HigherSelf Network Server. It enables the system to retrieve relevant information from various sources and use it to generate more accurate and contextually relevant responses.

## Overview

The Knowledge module consists of several components:

1. **Embedding Providers**: Generate vector embeddings for text content
2. **Vector Store**: Store and retrieve vector embeddings
3. **Semantic Search**: Search for semantically similar content
4. **RAG Pipeline**: Combine retrieval and generation for enhanced responses
5. **Web Crawling**: Crawl websites for content using Crawl4AI

## Components

### Embedding Providers

The `providers.py` file implements a registry of embedding providers:

- **MockEmbeddingProvider**: A mock provider for testing
- **OpenAIEmbeddingProvider**: Uses OpenAI's embedding models
- **LocalEmbeddingProvider**: Uses sentence-transformers for local embeddings

The provider registry automatically selects the best available provider based on API keys and falls back to local or mock providers when necessary.

### Vector Store

The vector store is responsible for storing and retrieving vector embeddings. It supports:

- Storing embeddings with metadata
- Retrieving embeddings by ID
- Searching for similar embeddings using cosine similarity
- Filtering by content type, tags, and other metadata

### Semantic Search

The semantic search component enables searching for content based on semantic similarity rather than exact keyword matches. It:

- Converts search queries into vector embeddings
- Finds the most similar content in the vector store
- Returns ranked results with similarity scores

### RAG Pipeline

The RAG pipeline combines retrieval and generation to produce enhanced responses:

1. Retrieves relevant context from the vector store based on a query
2. Formats the context for the AI model
3. Generates a response using the context and query
4. Optionally includes source citations in the response

### Web Crawling with Crawl4AI

The system integrates with Crawl4AI to crawl websites and extract content for RAG:

- Crawls individual pages or entire websites
- Extracts text content and metadata
- Stores content in the vector store for later retrieval
- Supports deep crawling with configurable depth and breadth

## Usage

### Basic RAG Example

```python
from knowledge.rag_pipeline import get_rag_pipeline
from services.ai_router import AIRouter

# Initialize the AI router
ai_router = AIRouter()
await ai_router.initialize()

# Get the RAG pipeline
rag_pipeline = await get_rag_pipeline(ai_router)

# Generate a RAG completion
response = await rag_pipeline.generate(
    query="What is Retrieval Augmented Generation?",
    content_types=["web_page", "notion_page"],
    search_limit=5,
    include_sources=True
)

print(response.text)
```

### Crawling a Website

```python
from services.crawl4ai_service import get_crawl4ai_service

# Get the Crawl4AI service
crawl_service = await get_crawl4ai_service()

# Crawl a website
result = await crawl_service.crawl_and_store(
    url="https://example.com",
    tags=["example", "documentation"],
    max_pages=10
)

print(f"Crawled and stored content with ID: {result['embedding_id']}")
```

## Configuration

The Knowledge module can be configured through environment variables:

- `OPENAI_API_KEY`: API key for OpenAI embeddings
- `ANTHROPIC_API_KEY`: API key for Anthropic embeddings
- `LOCAL_EMBEDDING_MODEL`: Name of the sentence-transformers model to use (default: "all-MiniLM-L6-v2")
- `SUPABASE_URL`: URL for Supabase (for vector storage)
- `SUPABASE_KEY`: API key for Supabase

## Dependencies

- `sentence-transformers`: For local embedding generation
- `openai`: For OpenAI embedding generation
- `crawl4ai`: For web crawling
- `supabase-py`: For vector storage (optional)

## Testing

The module includes mock providers for testing without external API keys. To enable testing mode:

```python
from config.testing_mode import enable_testing_mode

# Enable testing mode with specific APIs disabled
enable_testing_mode(disabled_apis=["openai", "anthropic", "supabase"])
```

This will use mock providers instead of making real API calls.
