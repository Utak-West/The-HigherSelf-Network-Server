"""RAG (Retrieval Augmented Generation) Agent for The HigherSelf Network Server.

This agent is responsible for:
1. Managing knowledge retrieval across various sources
2. Enhancing AI responses with relevant context
3. Maintaining the knowledge base through crawling and indexing
4. Integrating with other agents to provide contextual information
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from utils.logging_utils import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

from agents.base_agent import BaseAgent
from knowledge.rag_pipeline import RAGRequest, RAGResponse, get_rag_pipeline
from knowledge.semantic_search import get_semantic_search
from knowledge.vector_store import get_vector_store
from models.base import AgentCapability, ApiPlatform
from services.ai_router import AIRouter
from services.crawl4ai_service import CrawlConfig, get_crawl4ai_service
from services.notion_service import NotionService


class RAGAgent(BaseAgent):
    """RAG Agent - Knowledge Retrieval Specialist

    This agent specializes in retrieving relevant knowledge from various sources
    and enhancing AI responses with contextual information. It manages the knowledge
    base through crawling, indexing, and semantic search capabilities.
    """

    def __init__(
        self,
        agent_id: str = "RAGAgent",
        name: str = "Atlas",
        description: str = "Knowledge Retrieval Specialist",
        version: str = "1.0.0",
        business_entities: Optional[List[str]] = None,
        api_keys: Optional[Dict[str, str]] = None,
        notion_client: Optional[NotionService] = None,
        ai_router: Optional[AIRouter] = None,
    ):
        """Initialize the RAG Agent.

        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name
            description: Agent description and responsibilities
            version: Agent version
            business_entities: List of business entity IDs this agent is associated with
            api_keys: Dictionary of API keys
            notion_client: NotionService instance or None to create from environment
            ai_router: AIRouter instance or None to create a new one
        """
        capabilities = [
            AgentCapability.CONTENT_CREATION,
            AgentCapability.CONTENT_GENERATION,
            AgentCapability.WORKFLOW_MANAGEMENT,
            AgentCapability.AUDIENCE_ANALYSIS,
        ]

        apis_utilized = [
            ApiPlatform.NOTION,
            ApiPlatform.PLAUD,  # Assuming PLAUD is used for AI services
        ]

        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            version=version,
            capabilities=capabilities,
            apis_utilized=apis_utilized,
            business_entities=business_entities,
            notion_service=notion_client,
        )

        # Initialize AI router
        self.ai_router = ai_router

        # RAG components will be initialized lazily
        # Type annotations for better code analysis
        from knowledge.rag_pipeline import RAGPipeline
        from knowledge.semantic_search import SemanticSearch
        from knowledge.vector_store import VectorStore
        from services.crawl4ai_service import Crawl4AIService

        # All components start as None but will be initialized before use
        self.rag_pipeline: Optional[RAGPipeline] = None
        self.semantic_search: Optional[SemanticSearch] = None
        self.vector_store: Optional[VectorStore] = None
        self.crawl_service: Optional[Crawl4AIService] = None

        self.logger.info(f"RAG Agent {self.name} v{self.version} initialized")

    async def _ensure_rag_pipeline(self) -> None:
        """Ensure the RAG pipeline is initialized.

        Lazily initializes the RAG pipeline if it doesn't exist yet.
        Creates an AI router if one wasn't provided to the constructor.

        Raises:
            Exception: If RAG pipeline initialization fails
        """
        if self.rag_pipeline is None:
            if self.ai_router is None:
                self.ai_router = AIRouter()
                await self.ai_router.initialize()

            self.rag_pipeline = await get_rag_pipeline(self.ai_router)
            self.logger.info("RAG pipeline initialized")

    async def _ensure_semantic_search(self) -> None:
        """Ensure the semantic search is initialized.

        Lazily initializes the semantic search component if it doesn't exist yet.

        Raises:
            Exception: If semantic search initialization fails
        """
        if self.semantic_search is None:
            self.semantic_search = await get_semantic_search()
            self.logger.info("Semantic search initialized")

    async def _ensure_vector_store(self) -> None:
        """Ensure the vector store is initialized.

        Lazily initializes the vector store component if it doesn't exist yet.

        Raises:
            Exception: If vector store initialization fails
        """
        if self.vector_store is None:
            self.vector_store = await get_vector_store()
            self.logger.info("Vector store initialized")

    async def _ensure_crawl_service(self) -> None:
        """Ensure the crawl service is initialized.

        Lazily initializes the crawl service component if it doesn't exist yet.

        Raises:
            Exception: If crawl service initialization fails
        """
        if self.crawl_service is None:
            self.crawl_service = await get_crawl4ai_service()
            self.logger.info("Crawl service initialized")

    async def generate_rag_completion(self, query: str, **kwargs) -> Dict[str, Any]:
        """Generate a RAG-enhanced completion.

        Args:
            query: The query to answer
            **kwargs: Additional parameters for the RAG request
                max_tokens: Maximum number of tokens to generate
                temperature: Temperature for generation
                content_types: Types of content to search
                notion_database_ids: Specific Notion databases to search
                search_limit: Maximum number of search results
                similarity_threshold: Minimum similarity threshold
                system_message: Custom system message
                include_sources: Whether to include sources in the response

        Returns:
            Dict[str, Any]: Dictionary with the completion result containing
                status, text, sources (if requested), and the original query
        """
        await self._ensure_rag_pipeline()

        # Create RAG request
        request = RAGRequest(
            query=query,
            max_tokens=kwargs.get("max_tokens", 1000),
            temperature=kwargs.get("temperature", 0.7),
            content_types=kwargs.get("content_types"),
            notion_database_ids=kwargs.get("notion_database_ids"),
            search_limit=kwargs.get("search_limit", 5),
            similarity_threshold=kwargs.get("similarity_threshold", 0.7),
            system_message=kwargs.get("system_message"),
            include_sources=kwargs.get("include_sources", True),
        )

        # Generate completion
        try:
            if self.rag_pipeline is None:
                raise ValueError("RAG pipeline not initialized")

            result = await self.rag_pipeline.generate(request)

            return {
                "status": "success",
                "text": result.text,
                "sources": (
                    [source.model_dump() for source in result.sources]
                    if result.sources
                    else []
                ),
                "query": query,
            }
        except Exception as e:
            error_msg = f"Error generating RAG completion: {e}"
            self.logger.error(error_msg)
            return {"status": "error", "error": error_msg, "query": query}

    async def perform_semantic_search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Perform a semantic search.

        Args:
            query: The search query
            **kwargs: Additional parameters for the search
                content_types: Types of content to search
                notion_database_id: Specific Notion database to search
                limit: Maximum number of search results
                threshold: Minimum similarity threshold

        Returns:
            Dict[str, Any]: Dictionary with the search results containing
                status, results, and the original query
        """
        await self._ensure_semantic_search()

        try:
            # Call search method on the semantic_search instance
            semantic_search_instance = self.semantic_search
            if semantic_search_instance is None:
                raise ValueError("Semantic search not initialized")

            results = await semantic_search_instance.search(
                query=query,
                content_types=kwargs.get("content_types"),
                notion_database_id=kwargs.get("notion_database_id"),
                limit=kwargs.get("limit", 5),
                threshold=kwargs.get("threshold", 0.7),
            )

            return {"status": "success", "results": results, "query": query}
        except Exception as e:
            error_msg = f"Error performing semantic search: {e}"
            self.logger.error(error_msg)
            return {"status": "error", "error": error_msg, "query": query}

    async def crawl_and_index(self, url: str, **kwargs) -> Dict[str, Any]:
        """Crawl a URL and index the content.

        Args:
            url: The URL to crawl
            **kwargs: Additional parameters for the crawl
                max_pages: Maximum number of pages to crawl
                max_depth: Maximum crawl depth
                follow_links: Whether to follow links
                extract_metadata: Whether to extract metadata
                tags: Tags to associate with the crawled content

        Returns:
            Dict[str, Any]: Dictionary with the crawl results containing
                status, embedding_id, url, and pages_crawled
        """
        await self._ensure_crawl_service()

        try:
            # Create crawl config with all parameters
            config = CrawlConfig(
                url=url,  # Set the URL in the config
                max_pages=kwargs.get("max_pages", 10),
                max_depth=kwargs.get("max_depth", 2),
                # These parameters aren't in our CrawlConfig but appear in the method interface
                # We will handle them as metadata
                cache_mode=kwargs.get("cache_mode", "enabled"),
                tags=kwargs.get("tags", []),
                metadata={"extract_metadata": kwargs.get("extract_metadata", True)},
            )

            # Crawl and store
            if self.crawl_service is None:
                raise ValueError("Crawl service not initialized")

            result = await self.crawl_service.crawl_and_store(config=config)

            return {
                "status": "success",
                "embedding_id": result.get("embedding_id"),
                "url": url,
                "pages_crawled": result.get("pages_crawled", 1),
            }
        except Exception as e:
            error_msg = f"Error crawling and indexing URL {url}: {e}"
            self.logger.error(error_msg)
            return {"status": "error", "error": error_msg, "url": url}

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an event received by this agent.

        Handles different types of events including rag_completion,
        semantic_search, crawl_and_index, and knowledge_request.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Dict[str, Any]: Processing result based on the event type
        """
        self.logger.info(f"Processing event: {event_type}")

        # Handle different event types
        if event_type == "rag_completion":
            return await self.generate_rag_completion(
                query=event_data.get("query", ""),
                **{k: v for k, v in event_data.items() if k != "query"},
            )

        elif event_type == "semantic_search":
            return await self.perform_semantic_search(
                query=event_data.get("query", ""),
                **{k: v for k, v in event_data.items() if k != "query"},
            )

        elif event_type == "crawl_and_index":
            return await self.crawl_and_index(
                url=event_data.get("url", ""),
                **{k: v for k, v in event_data.items() if k != "url"},
            )

        elif event_type == "knowledge_request":
            # This event type is used by other agents to request knowledge
            return await self.handle_knowledge_request(event_data)

        else:
            error_msg = f"Unknown event type: {event_type}"
            self.logger.warning(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "event_type": event_type,
                "supported_events": [
                    "rag_completion",
                    "semantic_search",
                    "crawl_and_index",
                    "knowledge_request",
                ],
            }

    async def handle_knowledge_request(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle a knowledge request from another agent.

        Args:
            request_data: Request data including:
                query: The knowledge query
                requesting_agent: ID of the requesting agent
                request_id: Optional request ID for tracking
                max_tokens: Maximum number of tokens to generate
                temperature: Temperature for generation
                content_types: Types of content to search
                notion_database_ids: Specific Notion databases to search
                search_limit: Maximum number of search results
                include_sources: Whether to include sources in response

        Returns:
            Dict[str, Any]: Knowledge response with results and metadata
        """
        query = request_data.get("query", "")
        requesting_agent = request_data.get("requesting_agent", "unknown")

        self.logger.info(f"Knowledge request from {requesting_agent}: {query}")

        # Generate RAG completion
        result = await self.generate_rag_completion(
            query=query,
            max_tokens=request_data.get("max_tokens", 500),
            temperature=request_data.get("temperature", 0.7),
            content_types=request_data.get("content_types"),
            notion_database_ids=request_data.get("notion_database_ids"),
            search_limit=request_data.get("search_limit", 3),
            include_sources=request_data.get("include_sources", True),
        )

        # Add metadata for the requesting agent
        result["requesting_agent"] = requesting_agent
        result["request_id"] = request_data.get("request_id")

        return result

    async def check_health(self) -> Dict[str, Any]:
        """Check the health status of this agent.

        Verifies the health of all dependent components including:
        - RAG pipeline
        - Semantic search
        - Vector store

        Returns:
            Dict[str, Any]: Health check result with component statuses
        """
        health_status = {
            "status": "healthy",
            "name": self.name,
            "agent_id": self.agent_id,
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "components": {},
        }

        # Check RAG pipeline
        try:
            await self._ensure_rag_pipeline()
            health_status["components"]["rag_pipeline"] = "healthy"
        except Exception as e:
            error_msg = f"RAG pipeline error: {str(e)}"
            health_status["components"]["rag_pipeline"] = error_msg
            health_status["status"] = "degraded"
            self.logger.error(error_msg)

        # Check semantic search
        try:
            await self._ensure_semantic_search()
            health_status["components"]["semantic_search"] = "healthy"
        except Exception as e:
            error_msg = f"Semantic search error: {str(e)}"
            health_status["components"]["semantic_search"] = error_msg
            health_status["status"] = "degraded"
            self.logger.error(error_msg)

        # Check vector store
        try:
            await self._ensure_vector_store()
            health_status["components"]["vector_store"] = "healthy"
        except Exception as e:
            error_msg = f"Vector store error: {str(e)}"
            health_status["components"]["vector_store"] = error_msg
            health_status["status"] = "degraded"
            self.logger.error(error_msg)

        return health_status


# Create an alias for the RAG Agent with a personality name
Atlas = RAGAgent
