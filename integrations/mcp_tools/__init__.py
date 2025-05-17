"""
MCP Tools integration for Higher Self Network Server.
This package provides access to Model Context Protocol (MCP) tools that agents can use at their discretion.
"""

from .registry import MCPToolRegistry
from .config import MCPConfig

__all__ = ['MCPToolRegistry', 'MCPConfig']
