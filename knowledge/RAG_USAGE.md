# RAG (Retrieval Augmented Generation) Usage Guide

This guide explains how to use the RAG functionality in The HigherSelf Network Server.

## Overview

The RAG system enhances AI completions with relevant context from various sources:

1. **Notion databases and pages**
2. **Web content crawled with Crawl4AI**
3. **Voice commands processed with Aqua Voice**

## Setup

### 1. Environment Variables

Set the following environment variables:

```bash
# Notion API
NOTION_TOKEN=your_notion_token
NOTION_BUSINESS_ENTITIES_DB=your_business_entities_db_id
NOTION_AGENT_REGISTRY_DB=your_agent_registry_db_id
# ... other Notion database IDs

# Crawl4AI
CRAWL4AI_API_KEY=your_crawl4ai_api_key  # Optional

# Aqua Voice
AQUA_API_KEY=your_aqua_api_key
AQUA_API_URL=https://api.withaqua.com/v1  # Default

# AI Provider (OpenAI or Anthropic)
OPENAI_API_KEY=your_openai_api_key
# or
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### 1. Syncing Notion to Vector Store

To sync Notion databases to the vector store for semantic search:

```bash
python tools/sync_notion_to_vector.py
```

Options:
- `--databases`: Specific database names to sync
- `--since`: Only sync pages modified since this time (ISO format or relative like '1d', '12h')
- `--force`: Force update even if content hasn't changed

### 2. Crawling Web Content

Use the Crawl4AI service to crawl and store web content:

```python
from services.crawl4ai_service import get_crawl4ai_service, CrawlConfig

# Initialize the service
crawl_service = await get_crawl4ai_service()

# Crawl a single URL
result = await crawl_service.crawl_and_store(
    CrawlConfig(
        url="https://example.com",
        tags=["example", "documentation"],
        max_pages=10
    )
)

# Deep crawl a website
result = await crawl_service.deep_crawl_and_store(
    CrawlConfig(
        url="https://example.com",
        max_depth=2,
        max_pages=20,
        tags=["example", "documentation"]
    )
)
```

### 3. Voice Processing

Use the Aqua Voice service for voice transcription and command processing:

```python
from services.aqua_voice_service import get_aqua_voice_service, VoiceTranscriptionRequest
from services.ai_router import AIRouter

# Initialize the services
ai_router = AIRouter()
await ai_router.initialize()
voice_service = await get_aqua_voice_service(ai_router)

# Transcribe audio
result = await voice_service.transcribe(
    VoiceTranscriptionRequest(
        audio_data=base64_encoded_audio,
        content_type="audio/wav"
    )
)

# Process a command
result = await voice_service.process_command(
    VoiceCommandRequest(
        text="Search for information about retrieval augmented generation"
    )
)
```

### 4. RAG Completions

Use the RAG pipeline to generate completions enhanced with relevant context:

```python
from services.ai_router import AIRouter
from knowledge.rag_pipeline import get_rag_pipeline, RAGRequest

# Initialize the services
ai_router = AIRouter()
await ai_router.initialize()
rag_pipeline = await get_rag_pipeline(ai_router)

# Generate a RAG completion
result = await rag_pipeline.generate(
    RAGRequest(
        query="What is Retrieval Augmented Generation?",
        content_types=["web_page", "notion_page"],
        search_limit=5,
        include_sources=True
    )
)

print(result.text)
for source in result.sources:
    print(f"Source: {source.title} ({source.similarity})")
```

## API Endpoints

The server provides the following API endpoints for RAG functionality:

### Crawl Endpoints

- `POST /crawl/url`: Crawl a single URL
- `POST /crawl/deep`: Deep crawl a website
- `POST /crawl/background`: Start a background crawl task

### Voice Endpoints

- `POST /voice/transcribe`: Transcribe audio to text
- `POST /voice/command`: Process a voice command
- `POST /voice/transcribe-and-command`: Transcribe audio and process as a command

### RAG Endpoints

- `POST /rag/complete`: Generate a RAG-enhanced completion
- `POST /rag/search`: Perform a semantic search without generating a completion

## Testing

Run the test scripts to verify the RAG functionality:

```bash
# Test RAG with Notion integration
python tests/test_rag_notion_integration.py

# Test Aqua Voice service
python tests/test_aqua_voice.py
```

## Troubleshooting

- **Vector store initialization fails**: Check that Supabase is properly configured and the pgvector extension is enabled.
- **Notion sync fails**: Verify your Notion API token and database IDs.
- **Crawl4AI fails**: Check your internet connection and the URL being crawled.
- **Aqua Voice fails**: Verify your Aqua API key and the audio format.
- **RAG completion fails**: Check that the vector store has content and the AI provider is properly configured.
