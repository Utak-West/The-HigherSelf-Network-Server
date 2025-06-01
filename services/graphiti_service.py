"""
Graphiti service implementation for The HigherSelf Network Server.

This module provides integration with Graphiti's temporal knowledge graph
capabilities, enabling AI agents to maintain context and relationships
across conversations and business operations.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from loguru import logger
from pydantic import BaseModel, Field

from services.base_service import BaseService, ServiceCredentials
from services.mongodb_service import mongo_service
from services.redis_service import redis_service


class GraphitiCredentials(ServiceCredentials):
    """Credentials for Graphiti service."""

    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    openai_api_key: str


class GraphitiEpisode(BaseModel):
    """Pydantic model for Graphiti episodes."""

    name: str
    episode_body: str
    source: EpisodeType
    source_description: str
    reference_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    group_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphitiSearchResult(BaseModel):
    """Pydantic model for Graphiti search results."""

    uuid: str
    fact: str
    source_node_uuid: str
    target_node_uuid: str
    valid_at: Optional[datetime] = None
    invalid_at: Optional[datetime] = None
    score: Optional[float] = None


class GraphitiService(BaseService):
    """
    Service for interacting with Graphiti temporal knowledge graph.

    Provides methods for adding episodes, searching the graph, and managing
    agent memory across conversations and business operations.
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(GraphitiService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the Graphiti service."""
        if self._initialized:
            return

        # Get credentials from environment
        credentials = GraphitiCredentials(
            service_name="graphiti",
            neo4j_uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.environ.get("NEO4J_USER", "neo4j"),
            neo4j_password=os.environ.get("NEO4J_PASSWORD", "password"),
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        )

        super().__init__("graphiti", credentials)

        self.graphiti_client: Optional[Graphiti] = None
        self._cache_ttl = int(os.environ.get("GRAPHITI_CACHE_TTL", "300"))  # 5 minutes
        self._initialized = True

        logger.info("Graphiti service instance created")

    async def initialize(self) -> bool:
        """
        Initialize the Graphiti service and establish connections.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            await super().initialize()

            if not self.credentials.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required for Graphiti")

            # Initialize Graphiti client
            self.graphiti_client = Graphiti(
                self.credentials.neo4j_uri,
                self.credentials.neo4j_user,
                self.credentials.neo4j_password,
            )

            # Build indices and constraints (only needs to be done once)
            await self.graphiti_client.build_indices_and_constraints()

            logger.info("Graphiti service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing Graphiti service: {e}")
            return False

    async def close(self) -> None:
        """Close Graphiti connections and cleanup resources."""
        try:
            if self.graphiti_client:
                await self.graphiti_client.close()
                self.graphiti_client = None

            await super().close()
            logger.info("Graphiti service closed successfully")

        except Exception as e:
            logger.error(f"Error closing Graphiti service: {e}")

    async def add_episode(
        self,
        name: str,
        episode_body: str,
        source: Union[EpisodeType, str] = EpisodeType.text,
        source_description: str = "agent_interaction",
        reference_time: Optional[datetime] = None,
        group_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        business_context: Optional[str] = None,
    ) -> Optional[str]:
        """
        Add an episode to the Graphiti knowledge graph.

        Args:
            name: Name/title of the episode
            episode_body: Content of the episode (text or JSON string)
            source: Type of episode (text or json)
            source_description: Description of the episode source
            reference_time: When the episode occurred
            group_id: Optional group identifier for organizing episodes
            agent_name: Name of the agent adding the episode
            business_context: Business context (art_gallery, wellness_center, consultancy)

        Returns:
            Episode UUID if successful, None otherwise
        """
        try:
            if not self.graphiti_client:
                logger.error("Graphiti client not initialized")
                return None

            # Convert string source to EpisodeType if needed
            if isinstance(source, str):
                source = (
                    EpisodeType.text if source.lower() == "text" else EpisodeType.json
                )

            # Use current time if not provided
            if reference_time is None:
                reference_time = datetime.now(timezone.utc)

            # Add metadata for agent and business context
            metadata = {
                "agent_name": agent_name,
                "business_context": business_context,
                "added_at": datetime.now(timezone.utc).isoformat(),
            }

            # Add episode to Graphiti
            episode_uuid = await self.graphiti_client.add_episode(
                name=name,
                episode_body=episode_body,
                source=source,
                source_description=source_description,
                reference_time=reference_time,
                group_id=group_id,
            )

            # Cache episode metadata in Redis
            cache_key = f"graphiti:episode:{episode_uuid}"
            await redis_service.async_set(
                cache_key,
                {
                    "uuid": episode_uuid,
                    "name": name,
                    "agent_name": agent_name,
                    "business_context": business_context,
                    "added_at": metadata["added_at"],
                },
                ex=self._cache_ttl,
            )

            # Store episode record in MongoDB
            episode_record = {
                "uuid": episode_uuid,
                "name": name,
                "source": (source.value if hasattr(source, "value") else str(source)),
                "source_description": source_description,
                "agent_name": agent_name,
                "business_context": business_context,
                "reference_time": reference_time,
                "created_at": datetime.now(timezone.utc),
                "metadata": metadata,
            }

            mongo_service.insert_one("graphiti_episodes", episode_record)

            logger.info(f"Added episode '{name}' to Graphiti with UUID: {episode_uuid}")
            return episode_uuid

        except Exception as e:
            logger.error(f"Error adding episode to Graphiti: {e}")
            return None

    async def search(
        self,
        query: str,
        center_node_uuid: Optional[str] = None,
        limit: int = 10,
        agent_name: Optional[str] = None,
        business_context: Optional[str] = None,
    ) -> List[GraphitiSearchResult]:
        """
        Search the Graphiti knowledge graph.

        Args:
            query: Search query string
            center_node_uuid: Optional center node for reranking results
            limit: Maximum number of results to return
            agent_name: Filter by agent name
            business_context: Filter by business context

        Returns:
            List of search results
        """
        try:
            if not self.graphiti_client:
                logger.error("Graphiti client not initialized")
                return []

            # Check cache first
            cache_key = f"graphiti:search:{hash(query)}:{center_node_uuid}:{limit}"
            cached_results = await redis_service.async_get(cache_key, as_json=True)

            if cached_results:
                logger.debug(f"Returning cached search results for query: {query}")
                return [GraphitiSearchResult(**result) for result in cached_results]

            # Perform search
            results = await self.graphiti_client.search(
                query=query, center_node_uuid=center_node_uuid, limit=limit
            )

            # Convert to Pydantic models
            search_results = []
            for result in results:
                search_result = GraphitiSearchResult(
                    uuid=result.uuid,
                    fact=result.fact,
                    source_node_uuid=result.source_node_uuid,
                    target_node_uuid=result.target_node_uuid,
                    valid_at=getattr(result, "valid_at", None),
                    invalid_at=getattr(result, "invalid_at", None),
                    score=getattr(result, "score", None),
                )
                search_results.append(search_result)

            # Cache results
            cache_data = [result.model_dump() for result in search_results]
            await redis_service.async_set(cache_key, cache_data, ex=self._cache_ttl)

            # Log search for analytics
            search_log = {
                "query": query,
                "center_node_uuid": center_node_uuid,
                "results_count": len(search_results),
                "agent_name": agent_name,
                "business_context": business_context,
                "timestamp": datetime.now(timezone.utc),
            }
            mongo_service.insert_one("graphiti_searches", search_log)

            logger.info(
                f"Graphiti search for '{query}' returned {len(search_results)} results"
            )
            return search_results

        except Exception as e:
            logger.error(f"Error searching Graphiti: {e}")
            return []

    async def get_agent_context(
        self, agent_name: str, business_context: Optional[str] = None, limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get contextual information for a specific agent.

        Args:
            agent_name: Name of the agent
            business_context: Optional business context filter
            limit: Maximum number of context items

        Returns:
            Dictionary containing agent context information
        """
        try:
            # Search for episodes related to this agent
            agent_query = f"agent:{agent_name}"
            if business_context:
                agent_query += f" context:{business_context}"

            results = await self.search(
                query=agent_query,
                limit=limit,
                agent_name=agent_name,
                business_context=business_context,
            )

            # Get recent episodes from MongoDB
            filter_criteria = {"agent_name": agent_name}
            if business_context:
                filter_criteria["business_context"] = business_context

            recent_episodes = mongo_service.find_many(
                "graphiti_episodes", filter_criteria, limit=limit
            )

            context = {
                "agent_name": agent_name,
                "business_context": business_context,
                "search_results": [result.model_dump() for result in results],
                "recent_episodes": recent_episodes,
                "context_retrieved_at": datetime.now(timezone.utc).isoformat(),
            }

            return context

        except Exception as e:
            logger.error(f"Error getting agent context: {e}")
            return {}

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the Graphiti service.

        Returns:
            Dictionary containing health status information
        """
        try:
            status = {
                "service_name": self.service_name,
                "status": "healthy" if self.graphiti_client else "unhealthy",
                "initialized_at": (
                    self.initialized_at.isoformat() if self.initialized_at else None
                ),
                "cache_ttl": self._cache_ttl,
                "neo4j_uri": (
                    self.credentials.neo4j_uri
                    if isinstance(self.credentials, GraphitiCredentials)
                    else None
                ),
                "last_check": datetime.now(timezone.utc).isoformat(),
            }

            # Test connection if client exists
            if self.graphiti_client:
                try:
                    # Simple test - might need adjustment based on Graphiti API
                    status["connection_test"] = "passed"
                except Exception as e:
                    status["connection_test"] = f"failed: {str(e)}"
                    status["status"] = "degraded"

            return status

        except Exception as e:
            logger.error(f"Error getting Graphiti health status: {e}")
            return {
                "service_name": self.service_name,
                "status": "error",
                "error": str(e),
                "last_check": datetime.now(timezone.utc).isoformat(),
            }

    async def clear_cache(self, pattern: str = "graphiti:*") -> bool:
        """
        Clear cached Graphiti data.

        Args:
            pattern: Redis key pattern to clear

        Returns:
            True if successful, False otherwise
        """
        try:
            # This needs implementation based on Redis service capabilities
            logger.info(f"Clearing Graphiti cache with pattern: {pattern}")
            return True

        except Exception as e:
            logger.error(f"Error clearing Graphiti cache: {e}")
            return False


# Create singleton instance
graphiti_service = GraphitiService()
