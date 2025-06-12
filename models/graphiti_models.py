"""
Pydantic models for Graphiti integration in The HigherSelf Network Server.

These models provide type safety and validation for Graphiti temporal knowledge
graph operations, ensuring consistent data handling across all AI agents.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class GraphitiEpisodeType(str, Enum):
    """Episode types for Graphiti knowledge graph."""

    TEXT = "text"
    JSON = "json"


class GraphitiBusinessContext(str, Enum):
    """Business contexts for The HigherSelf Network."""

    ART_GALLERY = "art_gallery"
    WELLNESS_CENTER = "wellness_center"
    CONSULTANCY = "consultancy"
    INTERIOR_DESIGN = "interior_design"
    LUXURY_RENOVATIONS = "luxury_renovations"
    EXECUTIVE_WELLNESS = "executive_wellness"
    CORPORATE_WELLNESS = "corporate_wellness"


class GraphitiAgentName(str, Enum):
    """AI agent names in The HigherSelf Network."""

    GRACE = "Grace"  # GraceOrchestrator
    NYRA = "Nyra"  # Lead Capture Specialist
    SOLARI = "Solari"  # Booking & Order Manager
    RUVO = "Ruvo"  # Task Orchestrator
    LIORA = "Liora"  # Marketing Strategist
    SAGE = "Sage"  # Community Curator
    ELAN = "Elan"  # Content Choreographer
    ZEVI = "Zevi"  # Audience Analyst
    ATLAS = "Atlas"  # Knowledge Retrieval Specialist


class GraphitiEpisodeRequest(BaseModel):
    """Request model for adding episodes to Graphiti."""

    name: str = Field(..., description="Name/title of the episode")
    episode_body: str = Field(..., description="Content of the episode")
    source: GraphitiEpisodeType = Field(
        default=GraphitiEpisodeType.TEXT, description="Type of episode content"
    )
    source_description: str = Field(
        default="agent_interaction", description="Description of the episode source"
    )
    reference_time: Optional[datetime] = Field(
        default=None, description="When the episode occurred"
    )
    group_id: Optional[str] = Field(
        default=None, description="Optional group identifier"
    )
    agent_name: Optional[GraphitiAgentName] = Field(
        default=None, description="Name of the agent adding the episode"
    )
    business_context: Optional[GraphitiBusinessContext] = Field(
        default=None, description="Business context for the episode"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @validator("reference_time", pre=True, always=True)
    def set_reference_time(cls, v):
        """Set reference time to current UTC if not provided."""
        return v or datetime.now(timezone.utc)


class GraphitiEpisodeResponse(BaseModel):
    """Response model for episode creation."""

    uuid: str = Field(..., description="Unique identifier for the episode")
    name: str = Field(..., description="Name of the episode")
    agent_name: Optional[str] = Field(
        default=None, description="Agent that created the episode"
    )
    business_context: Optional[str] = Field(
        default=None, description="Business context"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the episode was created",
    )
    success: bool = Field(default=True, description="Whether creation succeeded")


class GraphitiSearchRequest(BaseModel):
    """Request model for searching Graphiti knowledge graph."""

    query: str = Field(..., description="Search query string")
    center_node_uuid: Optional[str] = Field(
        default=None, description="Optional center node for reranking results"
    )
    limit: int = Field(
        default=10, ge=1, le=100, description="Maximum number of results"
    )
    agent_name: Optional[GraphitiAgentName] = Field(
        default=None, description="Filter by agent name"
    )
    business_context: Optional[GraphitiBusinessContext] = Field(
        default=None, description="Filter by business context"
    )


class GraphitiSearchResult(BaseModel):
    """Individual search result from Graphiti."""

    uuid: str = Field(..., description="Unique identifier for the result")
    fact: str = Field(..., description="The fact/relationship found")
    source_node_uuid: str = Field(..., description="UUID of the source node")
    target_node_uuid: str = Field(..., description="UUID of the target node")
    valid_at: Optional[datetime] = Field(
        default=None, description="When this fact became valid"
    )
    invalid_at: Optional[datetime] = Field(
        default=None, description="When this fact became invalid"
    )
    score: Optional[float] = Field(
        default=None, description="Relevance score for the result"
    )


class GraphitiSearchResponse(BaseModel):
    """Response model for search operations."""

    query: str = Field(..., description="Original search query")
    results: List[GraphitiSearchResult] = Field(
        default_factory=list, description="List of search results"
    )
    total_results: int = Field(default=0, description="Total number of results found")
    search_time_ms: Optional[float] = Field(
        default=None, description="Time taken for search in milliseconds"
    )
    cached: bool = Field(
        default=False, description="Whether results were served from cache"
    )


class GraphitiAgentContext(BaseModel):
    """Context information for a specific agent."""

    agent_name: GraphitiAgentName = Field(..., description="Name of the agent")
    business_context: Optional[GraphitiBusinessContext] = Field(
        default=None, description="Business context filter"
    )
    search_results: List[GraphitiSearchResult] = Field(
        default_factory=list, description="Recent search results for this agent"
    )
    recent_episodes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Recent episodes created by this agent"
    )
    context_retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this context was retrieved",
    )
    total_episodes: int = Field(
        default=0, description="Total number of episodes for this agent"
    )


class GraphitiHealthStatus(BaseModel):
    """Health status of the Graphiti service."""

    service_name: str = Field(default="graphiti", description="Service name")
    status: str = Field(..., description="Current status")
    initialized_at: Optional[datetime] = Field(
        default=None, description="When the service was initialized"
    )
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    neo4j_uri: Optional[str] = Field(default=None, description="Neo4j connection URI")
    connection_test: Optional[str] = Field(
        default=None, description="Result of connection test"
    )
    last_check: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this status was last checked",
    )
    error: Optional[str] = Field(default=None, description="Error message if any")


class GraphitiMemoryUpdate(BaseModel):
    """Model for updating agent memory with Graphiti."""

    agent_name: GraphitiAgentName = Field(..., description="Agent updating memory")
    interaction_type: str = Field(..., description="Type of interaction")
    content: str = Field(..., description="Content to add to memory")
    business_context: Optional[GraphitiBusinessContext] = Field(
        default=None, description="Business context"
    )
    entities: List[str] = Field(
        default_factory=list, description="Entities mentioned in the interaction"
    )
    relationships: List[str] = Field(
        default_factory=list, description="Relationships identified"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the interaction occurred",
    )


class GraphitiCacheOperation(BaseModel):
    """Model for cache operations."""

    operation: str = Field(..., description="Cache operation type")
    pattern: str = Field(default="graphiti:*", description="Redis key pattern")
    success: bool = Field(default=False, description="Operation success")
    message: Optional[str] = Field(default=None, description="Operation message")
