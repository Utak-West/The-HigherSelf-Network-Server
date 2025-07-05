"""
Tool initialization module for MCP tools.
Imports and initializes all MCP tools for Higher Self Network Server.
"""

# Import tool registrations
from .memory_tool import memory_tool
from .perplexity_tool import perplexity_tool
from .tesseract_tool import tesseract_tool
from .web_browser_tool import web_browser_tool

try:
    from .devon_ai_tool import devon_ai_tool
except ImportError:
    devon_ai_tool = None

try:
    from .manus_ai_tool import manus_ai_tool
except ImportError:
    manus_ai_tool = None

# try:
#     from .genspark_tool import genspark_tool
# except ImportError:
genspark_tool = None

try:
    from .augment_code_tool import augment_code_tool
except ImportError:
    augment_code_tool = None

# List of all available tools
available_tools = [
    tool for tool in [
        memory_tool, 
        web_browser_tool, 
        perplexity_tool, 
        tesseract_tool,
        devon_ai_tool,
        manus_ai_tool,
        genspark_tool,
        augment_code_tool
    ] if tool is not None
]

__all__ = [
    "memory_tool",
    "web_browser_tool", 
    "perplexity_tool",
    "tesseract_tool",
    "devon_ai_tool",
    "manus_ai_tool",
    "genspark_tool",
    "augment_code_tool",
    "available_tools",
]
