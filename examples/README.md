# Examples

This directory contains example scripts demonstrating how to use various features of The HigherSelf Network Server.

## RAG Demo

The `rag_demo.py` script demonstrates how to use the Retrieval Augmented Generation (RAG) capabilities of the system. It shows how to:

1. Crawl websites using Crawl4AI
2. Store the content in the vector store
3. Generate responses using the RAG pipeline

### Running the RAG Demo

```bash
python examples/rag_demo.py
```

This will:
1. Crawl the Crawl4AI website
2. Store the content in the vector store
3. Generate responses to questions about Crawl4AI

### Code Explanation

The RAG demo consists of three main functions:

#### 1. `crawl_and_store_website()`

This function demonstrates how to crawl a single website and store its content in the vector store:

```python
async def crawl_and_store_website():
    """Crawl a website and store its content in the vector store."""
    logger.info("Initializing Crawl4AI service...")
    crawl_service = await get_crawl4ai_service()

    # Configure the crawl
    config = CrawlConfig(
        url="https://crawl4ai.com",
        tags=["crawl4ai", "documentation"],
        max_pages=5,
        cache_mode="enabled",
        metadata={
            "source_type": "website",
            "importance": "high"
        }
    )

    try:
        # Crawl and store the website
        logger.info(f"Crawling website: {config.url}")
        result = await crawl_service.crawl_and_store(config)

        if result and result.get("success"):
            logger.info(f"Successfully crawled and stored {config.url}: {result.get('embedding_id')}")
        else:
            logger.error(f"Failed to crawl {config.url}: {result.get('error')}")
    except Exception as e:
        logger.error(f"Failed to crawl {config.url}: {e}")
```

#### 2. `deep_crawl_website()`

This function demonstrates how to perform a deep crawl of a website, following links to a specified depth:

```python
async def deep_crawl_website():
    """Perform a deep crawl of a website and store its content."""
    logger.info("Initializing Crawl4AI service...")
    crawl_service = await get_crawl4ai_service()

    # Configure the deep crawl
    config = DeepCrawlConfig(
        url="https://docs.crawl4ai.com",
        tags=["crawl4ai", "documentation"],
        max_depth=2,
        max_pages=10,
        cache_mode="enabled",
        follow_external_links=False,
        metadata={
            "source_type": "documentation",
            "importance": "high"
        }
    )

    try:
        # Deep crawl and store the website
        logger.info(f"Deep crawling website: {config.url}")
        result = await crawl_service.deep_crawl_and_store(config)

        if result and result.get("success"):
            logger.info(f"Successfully deep crawled and stored {config.url}")
            logger.info(f"Pages crawled: {len(result.get('pages', []))}")
        else:
            logger.error(f"Failed to deep crawl {config.url}: {result.get('error')}")
    except Exception as e:
        logger.error(f"Failed to deep crawl {config.url}: {e}")
```

#### 3. `generate_rag_completion()`

This function demonstrates how to generate responses using the RAG pipeline:

```python
async def generate_rag_completion():
    """Generate a completion using the RAG pipeline."""
    logger.info("Initializing RAG pipeline...")

    # Get the AI router
    ai_router = AIRouter()
    await ai_router.initialize()

    # Get the RAG pipeline
    rag_pipeline = await get_rag_pipeline(ai_router)

    # Define some example queries
    queries = [
        "What is Crawl4AI and what are its main features?",
        "How can I use Crawl4AI for RAG applications?",
        "What are the advantages of using Crawl4AI over other web crawlers?"
    ]

    # Generate completions for each query
    for query in queries:
        try:
            logger.info(f"Generating RAG completion for query: {query}")

            response = await rag_pipeline.generate(
                query=query,
                content_types=["web_page"],
                search_limit=5,
                include_sources=True
            )

            logger.info("Successfully generated RAG completion")
            logger.info(f"Sources used: {len(response.sources)}")

            print("\n" + "=" * 50)
            print(f"Query: {query}")
            print("=" * 50)
            print(response.text)
            print("=" * 50 + "\n")

        except Exception as e:
            logger.error(f"Failed to generate RAG completion: {e}")
```

## Other Examples

More examples will be added in the future, including:

- Using the agent system
- Integrating with Notion
- Setting up workflows
- Custom embedding providers
- Advanced RAG techniques
