"""
RAG (Retrieval Augmented Generation) Agent for The HigherSelf Network Server.

This agent is responsible for:
1. Managing knowledge retrieval across various sources
2. Enhancing AI responses with relevant context
3. Maintaining the knowledge base through crawling and indexing
4. Integrating with other agents to provide contextual information
"""

import os
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent
from models.base import AgentCapability, ApiPlatform
from services.notion_service import NotionService
from services.ai_router import AIRouter
from knowledge.rag_pipeline import get_rag_pipeline, RAGRequest, RAGResponse
from knowledge.semantic_search import get_semantic_search
from knowledge.vector_store import get_vector_store
from services.crawl4ai_service import get_crawl4ai_service, CrawlConfig


class RAGAgent(BaseAgent):
    """
    RAG Agent - Knowledge Retrieval Specialist
    
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
        business_entities: List[str] = None,
        api_keys: Dict[str, str] = None,
        notion_client: Optional[NotionService] = None,
        ai_router: Optional[AIRouter] = None
    ):
        """Initialize the RAG Agent."""
        capabilities = [
            AgentCapability.KNOWLEDGE_RETRIEVAL,
            AgentCapability.CONTENT_CREATION,
            AgentCapability.AI_INTEGRATION,
            AgentCapability.ANALYTICS_PROCESSING
        ]
        
        apis_utilized = [
            ApiPlatform.NOTION,
            ApiPlatform.OPENAI,
            ApiPlatform.ANTHROPIC,
            ApiPlatform.HUGGINGFACE
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            version=version,
            capabilities=capabilities,
            apis_utilized=apis_utilized,
            business_entities=business_entities,
            notion_service=notion_client
        )
        
        # Initialize AI router
        self.ai_router = ai_router
        
        # RAG components will be initialized lazily
        self.rag_pipeline = None
        self.semantic_search = None
        self.vector_store = None
        self.crawl_service = None
        
        self.logger.info(f"RAG Agent {name} initialized")
    
    async def _ensure_rag_pipeline(self):
        """Ensure the RAG pipeline is initialized."""
        if self.rag_pipeline is None:
            if self.ai_router is None:
                self.ai_router = AIRouter()
                await self.ai_router.initialize()
            
            self.rag_pipeline = await get_rag_pipeline(self.ai_router)
            self.logger.info("RAG pipeline initialized")
    
    async def _ensure_semantic_search(self):
        """Ensure the semantic search is initialized."""
        if self.semantic_search is None:
            self.semantic_search = await get_semantic_search()
            self.logger.info("Semantic search initialized")
    
    async def _ensure_vector_store(self):
        """Ensure the vector store is initialized."""
        if self.vector_store is None:
            self.vector_store = await get_vector_store()
            self.logger.info("Vector store initialized")
    
    async def _ensure_crawl_service(self):
        """Ensure the crawl service is initialized."""
        if self.crawl_service is None:
            self.crawl_service = await get_crawl4ai_service()
            self.logger.info("Crawl service initialized")
    
    async def generate_rag_completion(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a RAG-enhanced completion.
        
        Args:
            query: The query to answer
            **kwargs: Additional parameters for the RAG request
            
        Returns:
            Dictionary with the completion result
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
            include_sources=kwargs.get("include_sources", True)
        )
        
        # Generate completion
        try:
            result = await self.rag_pipeline.generate(request)
            
            return {
                "status": "success",
                "text": result.text,
                "sources": [source.dict() for source in result.sources] if result.sources else [],
                "query": query
            }
        except Exception as e:
            self.logger.error(f"Error generating RAG completion: {e}")
            return {
                "status": "error",
                "error": str(e),
                "query": query
            }
    
    async def semantic_search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Perform a semantic search.
        
        Args:
            query: The search query
            **kwargs: Additional parameters for the search
            
        Returns:
            Dictionary with the search results
        """
        await self._ensure_semantic_search()
        
        try:
            results = await self.semantic_search.search(
                query=query,
                content_types=kwargs.get("content_types"),
                notion_database_id=kwargs.get("notion_database_id"),
                limit=kwargs.get("limit", 5),
                threshold=kwargs.get("threshold", 0.7)
            )
            
            return {
                "status": "success",
                "results": results,
                "query": query
            }
        except Exception as e:
            self.logger.error(f"Error performing semantic search: {e}")
            return {
                "status": "error",
                "error": str(e),
                "query": query
            }
    
    async def crawl_and_index(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Crawl a URL and index the content.
        
        Args:
            url: The URL to crawl
            **kwargs: Additional parameters for the crawl
            
        Returns:
            Dictionary with the crawl results
        """
        await self._ensure_crawl_service()
        
        try:
            # Create crawl config
            config = CrawlConfig(
                max_pages=kwargs.get("max_pages", 10),
                max_depth=kwargs.get("max_depth", 2),
                follow_links=kwargs.get("follow_links", True),
                extract_metadata=kwargs.get("extract_metadata", True)
            )
            
            # Crawl and store
            result = await self.crawl_service.crawl_and_store(
                url=url,
                tags=kwargs.get("tags", []),
                config=config
            )
            
            return {
                "status": "success",
                "embedding_id": result.get("embedding_id"),
                "url": url,
                "pages_crawled": result.get("pages_crawled", 1)
            }
        except Exception as e:
            self.logger.error(f"Error crawling and indexing URL {url}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "url": url
            }
    
    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an event received by this agent.
        
        Args:
            event_type: Type of event
            event_data: Event data
            
        Returns:
            Processing result
        """
        self.logger.info(f"Processing event: {event_type}")
        
        # Handle different event types
        if event_type == "rag_completion":
            return await self.generate_rag_completion(
                query=event_data.get("query", ""),
                **{k: v for k, v in event_data.items() if k != "query"}
            )
        
        elif event_type == "semantic_search":
            return await self.semantic_search(
                query=event_data.get("query", ""),
                **{k: v for k, v in event_data.items() if k != "query"}
            )
        
        elif event_type == "crawl_and_index":
            return await self.crawl_and_index(
                url=event_data.get("url", ""),
                **{k: v for k, v in event_data.items() if k != "url"}
            )
        
        elif event_type == "knowledge_request":
            # This event type is used by other agents to request knowledge
            return await self.handle_knowledge_request(event_data)
        
        else:
            self.logger.warning(f"Unknown event type: {event_type}")
            return {
                "status": "error",
                "error": f"Unknown event type: {event_type}",
                "event_type": event_type
            }
    
    async def handle_knowledge_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a knowledge request from another agent.
        
        Args:
            request_data: Request data
            
        Returns:
            Knowledge response
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
            include_sources=request_data.get("include_sources", True)
        )
        
        # Add metadata for the requesting agent
        result["requesting_agent"] = requesting_agent
        result["request_id"] = request_data.get("request_id")
        
        return result
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.
        
        Returns:
            Health check result
        """
        health_status = {
            "status": "healthy",
            "name": self.name,
            "agent_id": self.agent_id,
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check RAG pipeline
        try:
            await self._ensure_rag_pipeline()
            health_status["components"]["rag_pipeline"] = "healthy"
        except Exception as e:
            health_status["components"]["rag_pipeline"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check semantic search
        try:
            await self._ensure_semantic_search()
            health_status["components"]["semantic_search"] = "healthy"
        except Exception as e:
            health_status["components"]["semantic_search"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check vector store
        try:
            await self._ensure_vector_store()
            health_status["components"]["vector_store"] = "healthy"
        except Exception as e:
            health_status["components"]["vector_store"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        return health_status


# Create an alias for the RAG Agent with a personality name
Atlas = RAGAgent
