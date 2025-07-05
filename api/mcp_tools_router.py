"""
API Router for MCP Tools integration.
Provides endpoints for agents to discover and execute MCP tools.
"""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from api.auth import get_current_agent
from integrations.mcp_tools.mcp_tools_registry import ToolCapability, mcp_tools_registry
from models.notion_db_models import Agent
from services.analytics_service import agent_analytics
from services.cache_service import CacheLevel, CacheType, multi_level_cache
from services.redis_service import redis_service

router = APIRouter(prefix="/api/mcp_tools", tags=["MCP Tools"])


class ToolExecuteRequest(BaseModel):
    """Request model for tool execution."""

    tool_name: str
    parameters: Dict[str, Any]
    use_cache: bool = True
    cache_ttl: Optional[int] = None


class ToolExecuteResponse(BaseModel):
    """Response model for tool execution."""

    result: Dict[str, Any]
    success: bool
    error: Optional[str] = None


@router.get("/available", response_model=Dict[str, List[str]])
async def list_available_tools(agent: Agent = Depends(get_current_agent)):
    """
    List available MCP tools and their operations for the current agent.

    Args:
        agent: The authenticated agent

    Returns:
        Dictionary of tool names to list of supported operations
    """
    # Record analytics
    await agent_analytics.record_agent_action(
        agent_id=agent.agent_id,
        action_type="list_mcp_tools",
        context={},
        duration_ms=0,
        outcome="success",
    )

    # Map capabilities to tool names
    return mcp_tools_registry.get_capabilities()


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    request: ToolExecuteRequest, agent: Agent = Depends(get_current_agent)
):
    """
    Execute an MCP tool operation.

    Args:
        request: The tool execution request
        agent: The authenticated agent

    Returns:
        Result of the tool execution
    """
    result = await mcp_tools_registry.execute_tool(
        tool_name=request.tool_name,
        parameters=request.parameters,
        agent_id=agent.agent_id,
        use_cache=request.use_cache,
        cache_ttl=request.cache_ttl,
    )

    if "error" in result:
        return ToolExecuteResponse(result=result, success=False, error=result["error"])

    return ToolExecuteResponse(result=result, success=True)


@router.get("/config/{tool_name}", response_model=Dict[str, Any])
async def get_tool_config(
    tool_name: str = Path(..., description="Name of the MCP tool"),
    agent: Agent = Depends(get_current_agent),
):
    """
    Get configuration information for an MCP tool.
    Sensitive information like API keys will be redacted.

    Args:
        tool_name: Name of the MCP tool
        agent: The authenticated agent

    Returns:
        Tool configuration information (redacted)
    """
    tool = mcp_tools_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

    # Get tool metadata
    metadata = tool.metadata

    # Record analytics
    await agent_analytics.record_agent_action(
        agent_id=agent.agent_id,
        action_type="get_tool_config",
        context={"tool_name": tool_name},
        duration_ms=0,
        outcome="success",
    )

    return {
        "name": metadata.name,
        "description": metadata.description,
        "version": metadata.version,
        "capabilities": [cap for cap in metadata.capabilities],
        "parameters_schema": metadata.parameters_schema,
        "response_schema": metadata.response_schema,
        "requires_api_key": metadata.requires_api_key,
        "available": tool.available,
        "rate_limit": metadata.rate_limit,
        "examples": metadata.examples,
    }


@router.get("/tools/metadata", response_model=List[Dict[str, Any]])
async def get_tools_metadata(agent: Agent = Depends(get_current_agent)):
    """
    Get metadata for all available MCP tools.

    Args:
        agent: The authenticated agent

    Returns:
        List of tool metadata
    """
    # Record analytics
    await agent_analytics.record_agent_action(
        agent_id=agent.agent_id,
        action_type="get_tools_metadata",
        context={},
        duration_ms=0,
        outcome="success",
    )

    return mcp_tools_registry.list_tools_with_metadata()


@router.post("/bulk_execute", response_model=List[ToolExecuteResponse])
async def bulk_execute_tools(
    requests: List[ToolExecuteRequest],
    parallel: bool = Query(True, description="Whether to execute tools in parallel"),
    agent: Agent = Depends(get_current_agent),
):
    """
    Execute multiple MCP tools in a single request.

    Args:
        requests: List of tool execution requests
        parallel: Whether to execute tools in parallel
        agent: The authenticated agent

    Returns:
        List of tool execution results
    """
    executions = [
        {
            "tool_name": req.tool_name,
            "parameters": req.parameters,
            "cache_ttl": req.cache_ttl,
        }
        for req in requests
    ]

    results = await mcp_tools_registry.bulk_execute_tools(
        executions=executions,
        agent_id=agent.agent_id,
        use_cache=all(req.use_cache for req in requests),
        parallel=parallel,
    )

    # Format responses
    responses = []
    for result in results:
        if "error" in result:
            responses.append(
                ToolExecuteResponse(result=result, success=False, error=result["error"])
            )
        else:
            responses.append(ToolExecuteResponse(result=result, success=True))

    return responses
