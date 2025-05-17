"""
Registry for MCP Tools integration.
Handles registration, validation, and execution of MCP tools.
"""

import asyncio
import time
import json
import httpx
from typing import Any, Dict, List, Optional, Set, Union, Callable
from loguru import logger
from .config import mcp_config, MCPToolConfig
from models.agent_models import Agent
from services.redis_service import redis_service

class MCPRateLimiter:
    """Rate limiter for MCP tool calls."""
    
    def __init__(self, tool_name: str, calls_per_minute: int):
        self.tool_name = tool_name
        self.calls_per_minute = calls_per_minute
        self.window_size = 60  # seconds
        self.key_prefix = f"mcp_ratelimit:{tool_name}:"
    
    async def can_execute(self, agent_id: str) -> bool:
        """Check if the agent can execute the tool within rate limits."""
        if not self.calls_per_minute:
            return True
        
        now = int(time.time())
        window_start = now - self.window_size
        key = f"{self.key_prefix}{agent_id}"
        
        # Get recent calls within window
        async def get_calls():
            calls = await redis_service.async_get(key, as_json=True)
            return calls if calls else []
        
        calls = await get_calls()
        
        # Filter calls within current window
        recent_calls = [call for call in calls if call > window_start]
        
        # Check if under limit
        return len(recent_calls) < self.calls_per_minute
    
    async def record_call(self, agent_id: str):
        """Record a call for rate limiting purposes."""
        if not self.calls_per_minute:
            return
        
        now = int(time.time())
        key = f"{self.key_prefix}{agent_id}"
        
        # Get existing calls
        async def get_calls():
            calls = await redis_service.async_get(key, as_json=True)
            return calls if calls else []
        
        calls = await get_calls()
        
        # Add current call and remove old ones
        window_start = now - self.window_size
        calls = [call for call in calls if call > window_start]
        calls.append(now)
        
        # Save updated calls
        await redis_service.async_set(key, calls, ex=self.window_size * 2)


class MCPToolRegistry:
    """Registry for MCP Tools integration."""
    
    _instance = None
    _tools = {}
    _rate_limiters = {}
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(MCPToolRegistry, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize MCP tool registry."""
        self._tools = {}
        self._rate_limiters = {}
        
        # Register built-in tool handlers
        self._register_built_in_tools()
    
    def _register_built_in_tools(self):
        """Register built-in MCP tool handlers."""
        # Context 7 RAG tool
        self.register_tool_handler(
            "context7", 
            self._handle_context7_tool,
            ["query", "search_documents", "add_document"]
        )
        
        # Memory tool
        self.register_tool_handler(
            "memory",
            self._handle_memory_tool,
            ["create_memory", "retrieve_memory", "update_memory", "delete_memory"]
        )
        
        # Perplexity tool
        self.register_tool_handler(
            "perplexity",
            self._handle_perplexity_tool,
            ["ask", "web_search"]
        )
        
        # Brave search tool
        self.register_tool_handler(
            "brave_search",
            self._handle_brave_search_tool,
            ["web_search", "local_search"]
        )
        
        # Sequential thinking tool
        self.register_tool_handler(
            "sequential_thinking",
            self._handle_sequential_thinking_tool,
            ["sequentialthinking"]
        )
    
    def register_tool_handler(self, tool_name: str, handler: Callable, operations: List[str] = None):
        """Register a new MCP tool handler."""
        config = mcp_config.get_config(tool_name)
        if not config or not config.enabled:
            logger.warning(f"Cannot register handler for disabled or missing tool: {tool_name}")
            return False
        
        self._tools[tool_name] = {
            "handler": handler,
            "operations": operations or [],
            "config": config
        }
        
        # Create rate limiter if needed
        if config.rate_limit_per_min:
            self._rate_limiters[tool_name] = MCPRateLimiter(tool_name, config.rate_limit_per_min)
        
        logger.info(f"Registered MCP tool handler for {tool_name} with operations: {operations}")
        return True
    
    async def execute_tool(
        self, 
        agent: Agent, 
        tool_name: str, 
        operation: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an MCP tool."""
        # Check if tool exists
        if tool_name not in self._tools:
            return {"error": f"Tool {tool_name} not registered"}
        
        tool = self._tools[tool_name]
        
        # Check if operation is supported
        if operation not in tool["operations"]:
            return {"error": f"Operation {operation} not supported by tool {tool_name}"}
        
        # Check if agent is allowed to use the tool
        agent_id = getattr(agent, "agent_id", str(agent))
        if not mcp_config.is_agent_allowed(tool_name, agent_id):
            return {"error": f"Agent {agent_id} not authorized to use tool {tool_name}"}
        
        # Check rate limits
        if tool_name in self._rate_limiters:
            can_execute = await self._rate_limiters[tool_name].can_execute(agent_id)
            if not can_execute:
                return {"error": f"Rate limit exceeded for tool {tool_name}"}
        
        try:
            # Execute the tool handler
            result = await tool["handler"](agent, operation, params)
            
            # Record the call for rate limiting
            if tool_name in self._rate_limiters:
                await self._rate_limiters[tool_name].record_call(agent_id)
            
            # Log tool execution
            logger.info(f"Agent {agent_id} executed MCP tool {tool_name}.{operation}")
            
            return result
        except Exception as e:
            logger.error(f"Error executing MCP tool {tool_name}.{operation}: {e}")
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def list_available_tools(self, agent: Agent) -> Dict[str, List[str]]:
        """List available tools and operations for an agent."""
        agent_id = getattr(agent, "agent_id", str(agent))
        available_tools = {}
        
        for tool_name, tool in self._tools.items():
            if mcp_config.is_agent_allowed(tool_name, agent_id):
                available_tools[tool_name] = tool["operations"]
        
        return available_tools
    
    # Built-in tool handlers
    
    async def _handle_context7_tool(self, agent: Agent, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Context 7 RAG tool operations."""
        config = mcp_config.get_config("context7")
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            headers = {"Content-Type": "application/json"}
            if config.auth_type == "api_key" and config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"
            
            if operation == "query":
                url = f"{config.server_url}/query"
                response = await client.post(url, json=params, headers=headers)
                return response.json()
            
            elif operation == "search_documents":
                url = f"{config.server_url}/search"
                response = await client.post(url, json=params, headers=headers)
                return response.json()
            
            elif operation == "add_document":
                url = f"{config.server_url}/documents"
                response = await client.post(url, json=params, headers=headers)
                return response.json()
            
            return {"error": f"Unknown operation: {operation}"}
    
    async def _handle_memory_tool(self, agent: Agent, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Memory tool operations."""
        config = mcp_config.get_config("memory")
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            headers = {"Content-Type": "application/json"}
            if config.auth_type == "api_key" and config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"
            
            if operation == "create_memory":
                url = f"{config.server_url}/memories"
                response = await client.post(url, json=params, headers=headers)
                return response.json()
            
            elif operation == "retrieve_memory":
                url = f"{config.server_url}/memories/search"
                response = await client.post(url, json=params, headers=headers)
                return response.json()
            
            elif operation == "update_memory":
                memory_id = params.pop("id", None)
                if not memory_id:
                    return {"error": "Memory ID is required for updates"}
                url = f"{config.server_url}/memories/{memory_id}"
                response = await client.put(url, json=params, headers=headers)
                return response.json()
            
            elif operation == "delete_memory":
                memory_id = params.pop("id", None)
                if not memory_id:
                    return {"error": "Memory ID is required for deletion"}
                url = f"{config.server_url}/memories/{memory_id}"
                response = await client.delete(url, headers=headers)
                return response.json()
            
            return {"error": f"Unknown operation: {operation}"}
    
    async def _handle_perplexity_tool(self, agent: Agent, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Perplexity tool operations."""
        config = mcp_config.get_config("perplexity")
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            headers = {"Content-Type": "application/json"}
            if config.auth_type == "api_key" and config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"
            
            if operation == "ask":
                url = f"{config.server_url}/chat/completions"
                response = await client.post(url, json=params, headers=headers)
                return response.json()
            
            elif operation == "web_search":
                url = f"{config.server_url}/search"
                response = await client.post(url, json=params, headers=headers)
                return response.json()
            
            return {"error": f"Unknown operation: {operation}"}
    
    async def _handle_brave_search_tool(self, agent: Agent, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Brave search tool operations."""
        config = mcp_config.get_config("brave_search")
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            headers = {"Content-Type": "application/json"}
            if config.auth_type == "api_key" and config.api_key:
                headers["X-Subscription-Token"] = config.api_key
            
            if operation == "web_search":
                url = f"{config.server_url}/search"
                response = await client.get(
                    url,
                    params={"q": params.get("query"), "count": params.get("count", 10)},
                    headers=headers
                )
                return response.json()
            
            elif operation == "local_search":
                url = f"{config.server_url}/local"
                response = await client.get(
                    url,
                    params={"q": params.get("query"), "count": params.get("count", 5)},
                    headers=headers
                )
                return response.json()
            
            return {"error": f"Unknown operation: {operation}"}
    
    async def _handle_sequential_thinking_tool(
        self, agent: Agent, operation: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Sequential Thinking tool operations."""
        config = mcp_config.get_config("sequential_thinking")
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            headers = {"Content-Type": "application/json"}
            if config.auth_type == "api_key" and config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"
            
            if operation == "sequentialthinking":
                url = f"{config.server_url}/think"
                response = await client.post(url, json=params, headers=headers)
                return response.json()
            
            return {"error": f"Unknown operation: {operation}"}

# Create a singleton instance
mcp_tool_registry = MCPToolRegistry()
