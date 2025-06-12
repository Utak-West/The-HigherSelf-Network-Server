"""
Utility functions for Graphiti integration in The HigherSelf Network Server.

These utilities provide helper functions for common Graphiti operations,
data transformation, and integration with existing agent workflows.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from models.graphiti_models import (GraphitiAgentName, GraphitiBusinessContext,
                                    GraphitiEpisodeRequest,
                                    GraphitiEpisodeType, GraphitiMemoryUpdate,
                                    GraphitiSearchRequest)


def create_episode_from_agent_interaction(
    agent_name: str,
    interaction_content: str,
    business_context: Optional[str] = None,
    interaction_type: str = "conversation",
    metadata: Optional[Dict[str, Any]] = None,
) -> GraphitiEpisodeRequest:
    """
    Create a Graphiti episode from an agent interaction.

    Args:
        agent_name: Name of the agent
        interaction_content: Content of the interaction
        business_context: Business context for the interaction
        interaction_type: Type of interaction
        metadata: Additional metadata

    Returns:
        GraphitiEpisodeRequest ready for submission
    """
    try:
        # Convert string agent name to enum if possible
        try:
            agent_enum = GraphitiAgentName(agent_name)
        except ValueError:
            agent_enum = None
            logger.warning(f"Unknown agent name: {agent_name}")

        # Convert string business context to enum if possible
        business_enum = None
        if business_context:
            try:
                business_enum = GraphitiBusinessContext(business_context)
            except ValueError:
                logger.warning(f"Unknown business context: {business_context}")

        # Create episode name
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        episode_name = f"{agent_name}_{interaction_type}_{timestamp}"

        # Prepare metadata
        episode_metadata = {
            "interaction_type": interaction_type,
            "created_by": "graphiti_utils",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if metadata:
            episode_metadata.update(metadata)

        return GraphitiEpisodeRequest(
            name=episode_name,
            episode_body=interaction_content,
            source=GraphitiEpisodeType.TEXT,
            source_description=f"{agent_name} {interaction_type}",
            agent_name=agent_enum,
            business_context=business_enum,
            metadata=episode_metadata,
        )

    except Exception as e:
        logger.error(f"Error creating episode from agent interaction: {e}")
        raise


def create_structured_episode(
    agent_name: str,
    data: Dict[str, Any],
    business_context: Optional[str] = None,
    episode_type: str = "structured_data",
    metadata: Optional[Dict[str, Any]] = None,
) -> GraphitiEpisodeRequest:
    """
    Create a Graphiti episode from structured data.

    Args:
        agent_name: Name of the agent
        data: Structured data to store
        business_context: Business context
        episode_type: Type of structured data
        metadata: Additional metadata

    Returns:
        GraphitiEpisodeRequest ready for submission
    """
    try:
        # Convert to enum if possible
        try:
            agent_enum = GraphitiAgentName(agent_name)
        except ValueError:
            agent_enum = None

        business_enum = None
        if business_context:
            try:
                business_enum = GraphitiBusinessContext(business_context)
            except ValueError:
                pass

        # Create episode name
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        episode_name = f"{agent_name}_{episode_type}_{timestamp}"

        # Convert data to JSON string
        episode_body = json.dumps(data, default=str, indent=2)

        # Prepare metadata
        episode_metadata = {
            "episode_type": episode_type,
            "data_keys": list(data.keys()),
            "created_by": "graphiti_utils",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if metadata:
            episode_metadata.update(metadata)

        return GraphitiEpisodeRequest(
            name=episode_name,
            episode_body=episode_body,
            source=GraphitiEpisodeType.JSON,
            source_description=f"{agent_name} {episode_type}",
            agent_name=agent_enum,
            business_context=business_enum,
            metadata=episode_metadata,
        )

    except Exception as e:
        logger.error(f"Error creating structured episode: {e}")
        raise


def create_search_request(
    query: str,
    agent_name: Optional[str] = None,
    business_context: Optional[str] = None,
    limit: int = 10,
    center_node_uuid: Optional[str] = None,
) -> GraphitiSearchRequest:
    """
    Create a Graphiti search request.

    Args:
        query: Search query string
        agent_name: Optional agent name filter
        business_context: Optional business context filter
        limit: Maximum number of results
        center_node_uuid: Optional center node for reranking

    Returns:
        GraphitiSearchRequest ready for submission
    """
    try:
        # Convert to enums if possible
        agent_enum = None
        if agent_name:
            try:
                agent_enum = GraphitiAgentName(agent_name)
            except ValueError:
                pass

        business_enum = None
        if business_context:
            try:
                business_enum = GraphitiBusinessContext(business_context)
            except ValueError:
                pass

        return GraphitiSearchRequest(
            query=query,
            center_node_uuid=center_node_uuid,
            limit=limit,
            agent_name=agent_enum,
            business_context=business_enum,
        )

    except Exception as e:
        logger.error(f"Error creating search request: {e}")
        raise


def extract_entities_from_text(text: str) -> List[str]:
    """
    Extract potential entities from text for Graphiti processing.

    This is a simple implementation that can be enhanced with NLP libraries.

    Args:
        text: Text to extract entities from

    Returns:
        List of potential entities
    """
    try:
        # Simple entity extraction - can be enhanced with spaCy, NLTK, etc.
        import re

        # Extract capitalized words (potential proper nouns)
        entities = re.findall(r"\b[A-Z][a-z]+\b", text)

        # Extract email addresses
        emails = re.findall(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
        )
        entities.extend(emails)

        # Extract phone numbers (simple pattern)
        phones = re.findall(r"\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s*\d{3}-\d{4}\b", text)
        entities.extend(phones)

        # Remove duplicates and return
        return list(set(entities))

    except Exception as e:
        logger.error(f"Error extracting entities from text: {e}")
        return []


def format_search_results_for_agent(
    results: List[Dict[str, Any]], agent_name: str, max_results: int = 5
) -> str:
    """
    Format search results for agent consumption.

    Args:
        results: List of search results
        agent_name: Name of the requesting agent
        max_results: Maximum number of results to include

    Returns:
        Formatted string for agent use
    """
    try:
        if not results:
            return f"No relevant information found for {agent_name}'s query."

        formatted_results = []
        for i, result in enumerate(results[:max_results], 1):
            fact = result.get("fact", "Unknown fact")
            score = result.get("score", 0)

            formatted_result = f"{i}. {fact}"
            if score:
                formatted_result += f" (relevance: {score:.2f})"

            formatted_results.append(formatted_result)

        header = f"Found {len(results)} relevant facts for {agent_name}:"
        if len(results) > max_results:
            header += f" (showing top {max_results})"

        return header + "\n\n" + "\n".join(formatted_results)

    except Exception as e:
        logger.error(f"Error formatting search results: {e}")
        return f"Error formatting search results for {agent_name}"


def create_memory_update(
    agent_name: str,
    interaction_type: str,
    content: str,
    business_context: Optional[str] = None,
    entities: Optional[List[str]] = None,
    relationships: Optional[List[str]] = None,
) -> GraphitiMemoryUpdate:
    """
    Create a memory update for Graphiti.

    Args:
        agent_name: Name of the agent
        interaction_type: Type of interaction
        content: Content to remember
        business_context: Business context
        entities: Entities mentioned
        relationships: Relationships identified

    Returns:
        GraphitiMemoryUpdate ready for processing
    """
    try:
        # Convert to enums if possible
        try:
            agent_enum = GraphitiAgentName(agent_name)
        except ValueError:
            agent_enum = agent_name  # Keep as string if not in enum

        business_enum = None
        if business_context:
            try:
                business_enum = GraphitiBusinessContext(business_context)
            except ValueError:
                pass

        # Extract entities if not provided
        if entities is None:
            entities = extract_entities_from_text(content)

        return GraphitiMemoryUpdate(
            agent_name=agent_enum,
            interaction_type=interaction_type,
            content=content,
            business_context=business_enum,
            entities=entities or [],
            relationships=relationships or [],
        )

    except Exception as e:
        logger.error(f"Error creating memory update: {e}")
        raise


def validate_graphiti_config() -> Dict[str, Any]:
    """
    Validate Graphiti configuration and environment variables.

    Returns:
        Dictionary with validation results
    """
    import os

    validation_results = {"valid": True, "errors": [], "warnings": [], "config": {}}

    try:
        # Check required environment variables
        required_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "OPENAI_API_KEY"]

        for var in required_vars:
            value = os.environ.get(var)
            if not value:
                validation_results["errors"].append(
                    f"Missing required environment variable: {var}"
                )
                validation_results["valid"] = False
            else:
                # Mask sensitive values
                if "PASSWORD" in var or "KEY" in var:
                    validation_results["config"][var] = "***masked***"
                else:
                    validation_results["config"][var] = value

        # Check optional variables
        optional_vars = {"GRAPHITI_CACHE_TTL": "300", "NEO4J_DATABASE": "neo4j"}

        for var, default in optional_vars.items():
            value = os.environ.get(var, default)
            validation_results["config"][var] = value

        # Validate Neo4j URI format
        neo4j_uri = os.environ.get("NEO4J_URI", "")
        if neo4j_uri and not neo4j_uri.startswith(
            ("bolt://", "neo4j://", "neo4j+s://", "bolt+s://")
        ):
            validation_results["warnings"].append(
                "Neo4j URI should start with bolt:// or neo4j://"
            )

        return validation_results

    except Exception as e:
        logger.error(f"Error validating Graphiti config: {e}")
        validation_results["valid"] = False
        validation_results["errors"].append(f"Configuration validation error: {str(e)}")
        return validation_results
