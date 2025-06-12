"""
Reddit MCP Tool for Higher Self Network Server.
Provides integration with Reddit for social media monitoring and content discovery.
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


class RedditTool:
    """
    MCP Tool for integrating with Reddit API.
    
    This tool allows agents to:
    - Monitor subreddits for relevant discussions
    - Search for posts and comments
    - Analyze community sentiment
    - Track trending topics
    """

    def __init__(self):
        """Initialize the Reddit tool."""
        self.metadata = ToolMetadata(
            name="reddit",
            description="Monitor Reddit for discussions and trends",
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
                        "enum": ["subreddit_posts", "search", "post_details", "trending"],
                        "description": "Type of operation to perform"
                    },
                    "subreddit": {
                        "type": "string",
                        "description": "Subreddit name (without r/)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["hot", "new", "top", "rising"],
                        "default": "hot"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Number of posts to retrieve"
                    },
                    "time_filter": {
                        "type": "string",
                        "enum": ["hour", "day", "week", "month", "year", "all"],
                        "default": "day"
                    }
                },
                "required": ["operation"]
            },
            requires_api_key=False,
            rate_limit=20,
            pricing_tier="free",
            tags=["social", "reddit", "discussions", "trends"],
            examples=[
                {
                    "operation": "subreddit_posts",
                    "subreddit": "MachineLearning",
                    "sort": "hot",
                    "limit": 5
                },
                {
                    "operation": "search",
                    "query": "art therapy wellness",
                    "limit": 10
                }
            ]
        )

    async def execute(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Execute Reddit operations."""
        operation = params.get("operation")
        
        try:
            if operation == "subreddit_posts":
                return await self._get_subreddit_posts(params, agent_id)
            elif operation == "search":
                return await self._search_posts(params, agent_id)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Error in Reddit operation: {e}")
            return {"success": False, "error": str(e)}

    async def _get_subreddit_posts(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Get posts from a specific subreddit."""
        subreddit = params.get("subreddit")
        if not subreddit:
            return {"success": False, "error": "Subreddit is required"}
            
        sort = params.get("sort", "hot")
        limit = params.get("limit", 10)
        
        async with httpx.AsyncClient() as client:
            url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
            response = await client.get(url, headers={"User-Agent": "HigherSelf-Network-Bot/1.0"})
            data = response.json()
            
            posts = []
            for post_data in data.get("data", {}).get("children", []):
                post = post_data.get("data", {})
                posts.append({
                    "id": post.get("id"),
                    "title": post.get("title"),
                    "url": post.get("url"),
                    "score": post.get("score"),
                    "author": post.get("author"),
                    "created_utc": post.get("created_utc"),
                    "num_comments": post.get("num_comments"),
                    "subreddit": post.get("subreddit"),
                    "selftext": post.get("selftext", "")[:500]  # Truncate long text
                })
            
            return {
                "success": True,
                "operation": "subreddit_posts",
                "subreddit": subreddit,
                "sort": sort,
                "posts": posts,
                "count": len(posts)
            }

    async def _search_posts(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Search Reddit posts."""
        query = params.get("query")
        if not query:
            return {"success": False, "error": "Query is required for search"}
            
        limit = params.get("limit", 10)
        sort = params.get("sort", "relevance")
        time_filter = params.get("time_filter", "week")
        
        async with httpx.AsyncClient() as client:
            url = f"https://www.reddit.com/search.json?q={query}&sort={sort}&t={time_filter}&limit={limit}"
            response = await client.get(url, headers={"User-Agent": "HigherSelf-Network-Bot/1.0"})
            data = response.json()
            
            posts = []
            for post_data in data.get("data", {}).get("children", []):
                post = post_data.get("data", {})
                posts.append({
                    "id": post.get("id"),
                    "title": post.get("title"),
                    "url": post.get("url"),
                    "score": post.get("score"),
                    "author": post.get("author"),
                    "subreddit": post.get("subreddit"),
                    "created_utc": post.get("created_utc"),
                    "num_comments": post.get("num_comments"),
                    "selftext": post.get("selftext", "")[:300]
                })
            
            return {
                "success": True,
                "operation": "search",
                "query": query,
                "posts": posts,
                "count": len(posts)
            }


reddit_tool = RedditTool()

mcp_tool = MCPTool(
    metadata=reddit_tool.metadata,
    handler=reddit_tool.execute,
    is_async=True
)

mcp_tools_registry.register_tool(mcp_tool)
