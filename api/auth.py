"""
Authentication module for API endpoints.

This module provides authentication utilities for API endpoints,
including agent authentication and API key validation.
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException

from models.notion_db_models import Agent


async def get_current_agent(
    x_agent_id: Optional[str] = Header(None, alias="X-Agent-ID")
) -> Agent:
    """
    Get the current agent from the request headers.
    
    This is a simplified implementation that creates a mock agent
    for development purposes. In production, this should validate
    the agent ID against a database or authentication service.
    
    Args:
        x_agent_id: The agent ID from the X-Agent-ID header
        
    Returns:
        Agent: The authenticated agent
        
    Raises:
        HTTPException: If agent ID is missing or invalid
    """
    if not x_agent_id:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Agent-ID header"
        )
    
    # For development, create a mock agent
    # In production, this should validate against a real agent database
    return Agent(
        agent_id=x_agent_id,
        name=f"Agent-{x_agent_id}",
        description="Development agent",
        version="1.0.0"
    )
