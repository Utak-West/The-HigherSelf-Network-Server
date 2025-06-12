"""
Hacker News MCP Tool for Higher Self Network Server.
Provides integration with Hacker News for tech news and discussions.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from integrations.mcp_tools.mcp_tools_registry import (MCPTool, ToolCapability,
                                                       ToolMetadata,
                                                       mcp_tools_registry)


class HackerNewsTool:
    """
    MCP Tool for integrating with Hacker News API.
    
    This tool allows agents to:
    - Fetch top stories from Hacker News
    - Search for specific topics
    - Get story details and comments
    - Monitor tech trends and discussions
    """

    def __init__(self):
        """Initialize the Hacker News tool."""
        self.metadata = ToolMetadata(
            name="hacker_news",
            description="Access Hacker News stories and discussions",
            version="1.0.0",
            capabilities=[
                ToolCapability.SEARCH,
                ToolCapability.RETRIEVAL,
                ToolCapability.DATA_ANALYSIS
            ],
            parameters_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["top_stories", "new_stories", "search", "story_details"],
                        "description": "Type of operation to perform"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for stories"
                    },
                    "story_id": {
                        "type": "integer",
                        "description": "Hacker News story ID"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Number of stories to retrieve"
                    }
                },
                "required": ["operation"]
            },
            requires_api_key=False,
            rate_limit=30,
            pricing_tier="free",
            tags=["news", "tech", "discussions", "trends"],
            examples=[
                {
                    "operation": "top_stories",
                    "limit": 5
                },
                {
                    "operation": "search",
                    "query": "artificial intelligence",
                    "limit": 10
                }
            ]
        )

    async def execute(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Execute Hacker News operations."""
        operation = params.get("operation")
        
        try:
            if operation == "top_stories":
                return await self._get_top_stories(params, agent_id)
            elif operation == "search":
                return await self._search_stories(params, agent_id)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Error in Hacker News operation: {e}")
            return {"success": False, "error": str(e)}

    async def _get_top_stories(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Get top stories from Hacker News."""
        limit = params.get("limit", 10)
        
        async with httpx.AsyncClient() as client:
            response = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
            story_ids = response.json()[:limit]
            
            stories = []
            for story_id in story_ids:
                story_response = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
                story = story_response.json()
                if story:
                    stories.append({
                        "id": story.get("id"),
                        "title": story.get("title"),
                        "url": story.get("url"),
                        "score": story.get("score"),
                        "by": story.get("by"),
                        "time": story.get("time"),
                        "descendants": story.get("descendants", 0)
                    })
            
            return {
                "success": True,
                "operation": "top_stories",
                "stories": stories,
                "count": len(stories)
            }

    async def _search_stories(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Search for stories using Algolia HN Search API."""
        query = params.get("query")
        if not query:
            return {"success": False, "error": "Query is required for search"}
            
        limit = params.get("limit", 10)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://hn.algolia.com/api/v1/search?query={query}&hitsPerPage={limit}"
            )
            data = response.json()
            
            stories = []
            for hit in data.get("hits", []):
                stories.append({
                    "id": hit.get("objectID"),
                    "title": hit.get("title"),
                    "url": hit.get("url"),
                    "points": hit.get("points"),
                    "author": hit.get("author"),
                    "created_at": hit.get("created_at"),
                    "num_comments": hit.get("num_comments", 0)
                })
            
            return {
                "success": True,
                "operation": "search",
                "query": query,
                "stories": stories,
                "count": len(stories)
            }


hacker_news_tool = HackerNewsTool()

mcp_tool = MCPTool(
    metadata=hacker_news_tool.metadata,
    handler=hacker_news_tool.execute,
    is_async=True
)

mcp_tools_registry.register_tool(mcp_tool)
