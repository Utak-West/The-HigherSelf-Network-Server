"""
MCP Tools integration for Higher Self Network Server.
This package provides access to Model Context Protocol (MCP) tools that agents can use at their discretion.
"""

# Import registry and tool metadata
from .mcp_tools_registry import mcp_tools_registry, MCPTool, ToolMetadata, ToolCapability

# Import individual tools
from .tools import memory_tool, web_browser_tool, perplexity_tool, available_tools

# Legacy imports maintained for backward compatibility
try:
    from .registry import MCPToolRegistry
    from .config import MCPConfig
except ImportError:
    pass

__all__ = [
    'mcp_tools_registry',
    'MCPTool',
    'ToolMetadata',
    'ToolCapability',
    'memory_tool',
    'web_browser_tool',
    'perplexity_tool',
    'available_tools'
]
