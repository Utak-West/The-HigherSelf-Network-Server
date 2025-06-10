# RAG Agent Guide

## Introduction to Atlas - Knowledge Retrieval Specialist

Atlas is the dedicated RAG (Retrieval Augmented Generation) agent in The HigherSelf Network Server. As the Knowledge Retrieval Specialist, Atlas enhances the capabilities of all other agents by providing contextually relevant information from various sources.

## Key Capabilities

Atlas offers several powerful capabilities:

1. **RAG-Enhanced Completions**: Generate AI responses enhanced with relevant context from the knowledge base
2. **Semantic Search**: Find information based on meaning rather than exact keyword matches
3. **Web Crawling & Indexing**: Automatically extract and index content from websites
4. **Cross-Agent Knowledge Sharing**: Provide contextual information to other agents on request
5. **Knowledge Base Management**: Maintain and organize the system's knowledge repository

## Integration with Other Agents

Atlas is designed to work seamlessly with all other agents in the system:

- **Nyra** (Lead Capture Specialist): Atlas provides relevant information about leads, helping Nyra personalize interactions
- **Solari** (Booking & Order Manager): Atlas retrieves product details and booking information to assist Solari
- **Ruvo** (Task Orchestrator): Atlas provides context for task creation and prioritization
- **Liora** (Marketing Strategist): Atlas retrieves market trends and campaign performance data
- **Sage** (Community Curator): Atlas finds relevant content to share with the community
- **Elan** (Content Choreographer): Atlas provides research and reference material for content creation
- **Zevi** (Audience Analyst): Atlas retrieves historical data and trends for audience analysis

## Using Atlas in Your Workflows

### RAG-Enhanced Completions

To generate a completion enhanced with relevant context:

```python
from agents import Atlas

# Initialize Atlas
atlas = Atlas(notion_client=notion_service, ai_router=ai_router)

# Generate a RAG-enhanced completion
result = await atlas.generate_rag_completion(
    query="What are the key features of our new wellness program?",
    content_types=["notion_page", "web_page"],
    search_limit=5,
    include_sources=True
)

# Access the result
print(result["text"])
for source in result["sources"]:
    print(f"Source: {source.title} ({source.similarity})")
```

### Semantic Search

To search for information semantically:

```python
# Perform a semantic search
search_results = await atlas.semantic_search(
    query="wellness retreat pricing",
    content_types=["notion_page"],
    limit=10,
    threshold=0.7
)

# Process the results
for result in search_results["results"]:
    print(f"Content: {result['content'][:100]}...")
    print(f"Source: {result['source']}")
    print(f"Similarity: {result['score']}")
```

### Web Crawling & Indexing

To crawl and index a website:

```python
# Crawl and index a website
crawl_result = await atlas.crawl_and_index(
    url="https://example.com/blog",
    max_pages=20,
    max_depth=2,
    tags=["blog", "wellness"]
)

print(f"Crawled {crawl_result['pages_crawled']} pages")
print(f"Embedding ID: {crawl_result['embedding_id']}")
```

### Cross-Agent Knowledge Requests

Other agents can request knowledge from Atlas:

```python
# From another agent (e.g., Elan)
knowledge_request = {
    "query": "What content has performed best in our wellness category?",
    "requesting_agent": "Elan",
    "request_id": "content-research-123",
    "content_types": ["notion_page", "web_page"],
    "max_tokens": 500
}

# Send the request to Atlas
knowledge_response = await atlas.handle_knowledge_request(knowledge_request)

# Use the knowledge in the agent's workflow
print(knowledge_response["text"])
```

## Event Types

Atlas responds to the following event types:

1. **rag_completion**: Generate a RAG-enhanced completion
2. **semantic_search**: Perform a semantic search
3. **crawl_and_index**: Crawl and index a website
4. **knowledge_request**: Handle a knowledge request from another agent

## Configuration

Atlas can be configured through environment variables:

```
# OpenAI API for embeddings and completions
OPENAI_API_KEY=your_openai_api_key

# Anthropic API for Claude models
ANTHROPIC_API_KEY=your_anthropic_api_key

# Supabase for vector storage
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Crawl4AI for web crawling
CRAWL4AI_API_KEY=your_crawl4ai_api_key

# Local embedding model (optional)
LOCAL_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Best Practices

1. **Provide Specific Queries**: More specific queries yield better results
2. **Use Content Type Filters**: Limit searches to relevant content types
3. **Adjust Search Limits**: Increase for broader searches, decrease for focused results
4. **Include Sources**: Enable source citations to track information provenance
5. **Tag Content**: Use consistent tags when adding content to improve retrieval
6. **Regular Indexing**: Schedule regular crawling of important websites
7. **Combine with Other Agents**: Use Atlas in conjunction with other agents for powerful workflows

## Troubleshooting

### Common Issues

1. **No Results Found**: Try broadening your query or reducing the similarity threshold
2. **Slow Response Times**: Reduce the search limit or narrow content type filters
3. **Irrelevant Results**: Make your query more specific or increase the similarity threshold
4. **Crawling Failures**: Check website robots.txt and ensure proper access permissions

### Health Check

To check Atlas's health status:

```python
health_status = await atlas.check_health()
print(f"Status: {health_status['status']}")
for component, status in health_status["components"].items():
    print(f"{component}: {status}")
```

## Advanced Usage

### Custom System Messages

You can provide custom system messages for RAG completions:

```python
result = await atlas.generate_rag_completion(
    query="Summarize our wellness retreat options",
    system_message="You are a wellness expert helping clients find the perfect retreat. Provide a concise summary of options based on the context."
)
```

### Notion Database Integration

Atlas can search specific Notion databases:

```python
result = await atlas.generate_rag_completion(
    query="What are our current marketing campaigns?",
    notion_database_ids=["your_notion_database_id"],
    search_limit=10
)
```

## Conclusion

Atlas, the Knowledge Retrieval Specialist, brings powerful RAG capabilities to The HigherSelf Network Server. By integrating Atlas with your other agents, you can create more intelligent, context-aware automation workflows that leverage your organization's collective knowledge.
