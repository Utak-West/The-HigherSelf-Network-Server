"""
API Router for MCP Tools integration.
Provides endpoints for agents to discover and execute MCP tools.
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import json

from models.agent_models import Agent
from api.auth import get_current_agent
from integrations.mcp_tools import MCPToolRegistry, mcp_config
from integrations.mcp_tools.registry import mcp_tool_registry
from services.redis_service import redis_service

router = APIRouter(prefix="/api/mcp_tools", tags=["MCP Tools"])

class ToolExecuteRequest(BaseModel):
    """Request model for tool execution."""
    tool_name: str
    operation: str
    parameters: Dict[str, Any]

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
    return mcp_tool_registry.list_available_tools(agent)

@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    request: ToolExecuteRequest,
    agent: Agent = Depends(get_current_agent)
):
    """
    Execute an MCP tool operation.
    
    Args:
        request: The tool execution request
        agent: The authenticated agent
        
    Returns:
        Result of the tool execution
    """
    result = await mcp_tool_registry.execute_tool(
        agent, request.tool_name, request.operation, request.parameters
    )
    
    if "error" in result:
        return ToolExecuteResponse(
            result=result,
            success=False,
            error=result["error"]
        )
    
    return ToolExecuteResponse(
        result=result,
        success=True
    )

@router.get("/config/{tool_name}", response_model=Dict[str, Any])
async def get_tool_config(
    tool_name: str = Path(..., description="Name of the MCP tool"),
    agent: Agent = Depends(get_current_agent)
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
    config = mcp_config.get_config(tool_name)
    if not config:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
    
    # Convert to dict and redact sensitive information
    config_dict = config.dict()
    if "api_key" in config_dict and config_dict["api_key"]:
        config_dict["api_key"] = "***REDACTED***"
    
    return config_dict

@router.get("/context7/collections", response_model=Dict[str, Any])
async def get_context7_collections(agent: Agent = Depends(get_current_agent)):
    """
    Get list of available Context7 RAG collections.
    
    Args:
        agent: The authenticated agent
        
    Returns:
        List of available collections
    """
    from integrations.mcp_tools.context7_rag import context7_rag
    
    if not context7_rag.enabled:
        raise HTTPException(status_code=400, detail="Context7 RAG is not enabled")
    
    result = await context7_rag.get_collections()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/context7/query", response_model=Dict[str, Any])
async def query_context7(
    query: str = Body(..., embed=True),
    collection: str = Body("default", embed=True),
    top_k: int = Body(5, embed=True),
    filters: Dict[str, Any] = Body(None, embed=True),
    agent: Agent = Depends(get_current_agent)
):
    """
    Query the Context7 RAG system.
    
    Args:
        query: The query text
        collection: Name of the collection to search in
        top_k: Number of results to return
        filters: Optional filters to apply
        agent: The authenticated agent
        
    Returns:
        Query results
    """
    from integrations.mcp_tools.context7_rag import context7_rag
    
    if not context7_rag.enabled:
        raise HTTPException(status_code=400, detail="Context7 RAG is not enabled")
    
    result = await context7_rag.query(query, collection, filters, top_k)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result
