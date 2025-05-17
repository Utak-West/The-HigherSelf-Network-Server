"""
Tool initialization module for MCP tools.
Imports and initializes all MCP tools for Higher Self Network Server.
"""

# Import tool registrations
from .memory_tool import memory_tool
from .web_browser_tool import web_browser_tool
from .perplexity_tool import perplexity_tool

# List of all available tools
available_tools = [
    memory_tool,
    web_browser_tool,
    perplexity_tool
]

__all__ = [
    "memory_tool", 
    "web_browser_tool", 
    "perplexity_tool",
    "available_tools"
]
