"""
MCP Tools Registry for Higher Self Network Server.
Provides registration, discovery, and management of MCP tools.
"""

import asyncio
import json
import os
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar

from loguru import logger
from pydantic import BaseModel, Field

from services.analytics_service import agent_analytics
from services.cache_service import CacheLevel, CacheType, multi_level_cache
from services.consul_service import consul_service

# Type for tool handlers
T = TypeVar("T")
ToolHandler = Callable[[Dict[str, Any], str], Any]
AsyncToolHandler = Callable[[Dict[str, Any], str], Any]


class ToolCapability(str, Enum):
    """Capabilities that MCP tools can provide."""

    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    SEARCH = "search"
    WEB_BROWSING = "web_browsing"
    MEMORY = "memory"
    REASONING = "reasoning"
    CODE = "code"
    VISION = "vision"
    AUDIO = "audio"
    PLANNING = "planning"
    DATA_ANALYSIS = "data_analysis"


class ToolMetadata(BaseModel):
    """Metadata for MCP tools."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    version: str = Field(..., description="Tool version")
    capabilities: List[ToolCapability] = Field(
        default_factory=list, description="Tool capabilities"
    )
    parameters_schema: Dict[str, Any] = Field(
        default_factory=dict, description="JSON schema for tool parameters"
    )
    response_schema: Optional[Dict[str, Any]] = Field(
        None, description="JSON schema for tool response"
    )
    requires_api_key: bool = Field(
        False, description="Whether the tool requires an API key"
    )
    rate_limit: Optional[int] = Field(
        None, description="Rate limit in requests per minute"
    )
    pricing_tier: Optional[str] = Field(None, description="Pricing tier for the tool")
    tags: List[str] = Field(
        default_factory=list, description="Tags for categorizing the tool"
    )
    examples: List[Dict[str, Any]] = Field(
        default_factory=list, description="Example usages of the tool"
    )


class MCPTool(Generic[T]):
    """
    Representation of an MCP tool with its metadata and handler.
    """

    def __init__(
        self,
        metadata: ToolMetadata,
        handler: T,
        is_async: bool = True,
        env_var_name: Optional[str] = None,
    ):
        """
        Initialize an MCP tool.

        Args:
            metadata: Tool metadata
            handler: Function to handle tool calls
            is_async: Whether the handler is async
            env_var_name: Name of the environment variable containing the API key
        """
        self.metadata = metadata
        self.handler = handler
        self.is_async = is_async
        self.env_var_name = env_var_name
        self.available = True

        # Check if API key is required and available
        if metadata.requires_api_key and env_var_name:
            if not os.environ.get(env_var_name):
                logger.warning(
                    f"API key for {metadata.name} not found in environment variable {env_var_name}"
                )
                self.available = False

    @property
    def name(self) -> str:
        """Get the tool name."""
        return self.metadata.name


class MCPToolsRegistry:
    """
    Registry for MCP tools.
    Manages tool registration, discovery, and execution.
    """

    def __init__(self):
        """Initialize the MCP tools registry."""
        self._tools: Dict[str, MCPTool] = {}
        self._tool_map_by_capability: Dict[ToolCapability, List[str]] = {
            cap: [] for cap in ToolCapability
        }
        logger.info("MCP Tools Registry initialized")

    def register_tool(self, tool: MCPTool) -> bool:
        """
        Register an MCP tool with the registry.

        Args:
            tool: The tool to register

        Returns:
            True if registration was successful, False otherwise
        """
        try:
            # Check if tool is already registered
            if tool.name in self._tools:
                logger.warning(f"Tool {tool.name} is already registered, updating")

            # Register tool
            self._tools[tool.name] = tool

            # Update capability map
            for capability in tool.metadata.capabilities:
                if tool.name not in self._tool_map_by_capability[capability]:
                    self._tool_map_by_capability[capability].append(tool.name)

            # Register with Consul if tool is available
            if tool.available:
                consul_service.register_mcp_tool_service(tool.name)
                logger.info(
                    f"Registered tool {tool.name} with capabilities: {tool.metadata.capabilities}"
                )
            else:
                logger.warning(f"Tool {tool.name} is registered but not available")

            return True
        except Exception as e:
            logger.error(f"Failed to register tool {tool.name}: {e}")
            return False

    def unregister_tool(self, tool_name: str) -> bool:
        """
        Unregister an MCP tool from the registry.

        Args:
            tool_name: The name of the tool to unregister

        Returns:
            True if unregistration was successful, False otherwise
        """
        try:
            # Check if tool exists
            if tool_name not in self._tools:
                logger.warning(f"Tool {tool_name} is not registered")
                return False

            # Get tool
            tool = self._tools[tool_name]

            # Remove from capability map
            for capability in tool.metadata.capabilities:
                if tool_name in self._tool_map_by_capability[capability]:
                    self._tool_map_by_capability[capability].remove(tool_name)

            # Deregister from Consul
            consul_service.deregister_service(f"mcp-tool-{tool_name}")

            # Remove from registry
            del self._tools[tool_name]

            logger.info(f"Unregistered tool {tool_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to unregister tool {tool_name}: {e}")
            return False

    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """
        Get an MCP tool by name.

        Args:
            tool_name: The name of the tool

        Returns:
            The tool if found, None otherwise
        """
        return self._tools.get(tool_name)

    def get_tools_by_capability(self, capability: ToolCapability) -> List[MCPTool]:
        """
        Get MCP tools by capability.

        Args:
            capability: The capability to filter by

        Returns:
            List of tools with the specified capability
        """
        tool_names = self._tool_map_by_capability.get(capability, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def list_tools(self, available_only: bool = True) -> List[str]:
        """
        List all registered MCP tools.

        Args:
            available_only: Whether to list only available tools

        Returns:
            List of tool names
        """
        if available_only:
            return [name for name, tool in self._tools.items() if tool.available]
        return list(self._tools.keys())

    def list_tools_with_metadata(
        self, available_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all registered MCP tools with their metadata.

        Args:
            available_only: Whether to list only available tools

        Returns:
            List of tool metadata dictionaries
        """
        result = []

        for name, tool in self._tools.items():
            if available_only and not tool.available:
                continue

            result.append(
                {
                    "name": tool.name,
                    "metadata": tool.metadata.dict(),
                    "available": tool.available,
                }
            )

        return result

    def get_capabilities(self) -> Dict[str, List[str]]:
        """
        Get all capabilities and their associated tools.

        Returns:
            Dictionary mapping capabilities to tool names
        """
        result = {}

        for capability, tool_names in self._tool_map_by_capability.items():
            available_tools = [
                name
                for name in tool_names
                if name in self._tools and self._tools[name].available
            ]

            if available_tools:
                result[capability] = available_tools

        return result

    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        agent_id: str,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute an MCP tool.

        Args:
            tool_name: The name of the tool to execute
            parameters: The parameters for the tool
            agent_id: The ID of the agent executing the tool
            use_cache: Whether to use cached results if available
            cache_ttl: Optional TTL for cache in seconds

        Returns:
            The tool execution result
        """
        start_time = asyncio.get_event_loop().time()
        cache_hit = False

        try:
            # Check if tool exists and is available
            tool = self.get_tool(tool_name)
            if not tool:
                return {"error": f"Tool {tool_name} not found", "success": False}

            if not tool.available:
                return {"error": f"Tool {tool_name} is not available", "success": False}

            # Generate cache key
            cache_key = self._generate_cache_key(tool_name, parameters)

            # Check cache if enabled
            if use_cache:
                cached_result = await multi_level_cache.get(cache_key, CacheType.MCP)

                if cached_result is not None:
                    cache_hit = True
                    duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000

                    # Record analytics
                    await agent_analytics.record_mcp_tool_usage(
                        tool_name=tool_name,
                        agent_id=agent_id,
                        operation="execute",
                        parameters=parameters,
                        duration_ms=duration_ms,
                        outcome="success_cached",
                        result_summary="Retrieved from cache",
                    )

                    return {**cached_result, "from_cache": True}

            # Execute tool
            if tool.is_async:
                result = await tool.handler(parameters, agent_id)
            else:
                # Run synchronous handler in thread pool
                result = await asyncio.get_event_loop().run_in_executor(
                    None, tool.handler, parameters, agent_id
                )

            # Format result
            formatted_result = {
                "result": result,
                "success": True,
                "tool_name": tool_name,
                "from_cache": False,
            }

            # Cache result if enabled
            if use_cache:
                await multi_level_cache.set(
                    cache_key, formatted_result, CacheType.MCP, ttl_override=cache_ttl
                )

            # Record duration and analytics
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            await agent_analytics.record_mcp_tool_usage(
                tool_name=tool_name,
                agent_id=agent_id,
                operation="execute",
                parameters=parameters,
                duration_ms=duration_ms,
                outcome="success",
                result_summary=str(result)[:100],  # Truncate for summary
            )

            return formatted_result
        except Exception as e:
            # Record error and analytics
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            await agent_analytics.record_mcp_tool_usage(
                tool_name=tool_name,
                agent_id=agent_id,
                operation="execute",
                parameters=parameters,
                duration_ms=duration_ms,
                outcome="error",
                result_summary=str(e),
            )

            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "error": str(e),
                "success": False,
                "tool_name": tool_name,
                "from_cache": False,
            }

    async def bulk_execute_tools(
        self,
        executions: List[Dict[str, Any]],
        agent_id: str,
        use_cache: bool = True,
        parallel: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple MCP tools in parallel or sequentially.

        Args:
            executions: List of dictionaries with tool_name and parameters
            agent_id: The ID of the agent executing the tools
            use_cache: Whether to use cached results if available
            parallel: Whether to execute tools in parallel or sequentially

        Returns:
            List of tool execution results
        """
        try:
            if parallel:
                # Execute tools in parallel
                tasks = [
                    self.execute_tool(
                        execution["tool_name"],
                        execution["parameters"],
                        agent_id,
                        use_cache,
                        execution.get("cache_ttl"),
                    )
                    for execution in executions
                ]

                return await asyncio.gather(*tasks)
            else:
                # Execute tools sequentially
                results = []
                for execution in executions:
                    result = await self.execute_tool(
                        execution["tool_name"],
                        execution["parameters"],
                        agent_id,
                        use_cache,
                        execution.get("cache_ttl"),
                    )
                    results.append(result)

                return results
        except Exception as e:
            logger.error(f"Error in bulk execute tools: {e}")
            return [
                {"error": str(e), "success": False, "from_cache": False}
                for _ in executions
            ]

    def _generate_cache_key(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """
        Generate a cache key for tool execution.

        Args:
            tool_name: The name of the tool
            parameters: The parameters for the tool

        Returns:
            Cache key string
        """
        # Sort parameters for consistent keys
        sorted_params = json.dumps(parameters, sort_keys=True)
        return f"{tool_name}:{sorted_params}"


# Create a singleton instance
mcp_tools_registry = MCPToolsRegistry()
