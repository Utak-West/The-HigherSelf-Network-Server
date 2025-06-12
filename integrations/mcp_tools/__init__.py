"""
MCP Tools integration for Higher Self Network Server.
This package provides access to Model Context Protocol (MCP) tools that agents can use at their discretion.
"""

# Import registry and tool metadata
from .mcp_tools_registry import (MCPTool, ToolCapability, ToolMetadata,
                                 mcp_tools_registry)
# Import individual tools
from .tools import (available_tools, memory_tool, perplexity_tool,
                    tesseract_tool, web_browser_tool)

# Legacy imports maintained for backward compatibility
try:
    from .config import MCPConfig
    from .registry import MCPToolRegistry
except ImportError:
    pass

__all__ = [
    "mcp_tools_registry",
    "MCPTool",
    "ToolMetadata",
    "ToolCapability",
    "memory_tool",
    "web_browser_tool",
    "perplexity_tool",
    "tesseract_tool",
    "available_tools",
]
