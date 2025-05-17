"""
Web Browser MCP Tool for Higher Self Network Server.
Provides a tool for agents to search the web, fetch page content, and perform basic web navigation.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
import httpx
from pydantic import BaseModel, Field
from loguru import logger
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

from integrations.mcp_tools.mcp_tools_registry import (
    mcp_tools_registry,
    MCPTool,
    ToolMetadata,
    ToolCapability
)
from services.cache_service import multi_level_cache, CacheType, CacheLevel


class WebBrowserTool:
    """
    Implementation of web browsing tool for agents.
    Provides operations to search, fetch content, and navigate web pages.
    """

    def __init__(self):
        """Initialize the web browser tool."""
        self.enabled = True
        self.search_api_key = os.environ.get("SEARCH_API_KEY", "")
        self.search_engine_id = os.environ.get("SEARCH_ENGINE_ID", "")
        self.user_agent = "Mozilla/5.0 (compatible; HigherSelfAgent/1.0; +https://higherself.network/bot)"
        
        # Register with registry
        self._register()
        
        logger.info("Web Browser MCP tool initialized")
        
    def _register(self):
        """Register this tool with the MCP tools registry."""
        metadata = ToolMetadata(
            name="web_browser",
            description="Tool for searching the web and retrieving web content",
            version="1.0.0",
            capabilities=[ToolCapability.WEB_BROWSING, ToolCapability.SEARCH],
            parameters_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "search", "get_page", "extract_links", "summarize"
                        ],
                        "description": "The web operation to perform"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query (required for search operation)"
                    },
                    "url": {
                        "type": "string",
                        "description": "URL to fetch (required for get_page, extract_links, summarize)"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of search results to return"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout for HTTP requests in seconds"
                    },
                    "extract_images": {
                        "type": "boolean",
                        "description": "Whether to extract image URLs from the page"
                    },
                    "extract_text_only": {
                        "type": "boolean",
                        "description": "Whether to return only the text content of a page"
                    },
                    "select_element": {
                        "type": "string",
                        "description": "CSS selector to extract specific elements from a page"
                    }
                },
                "required": ["operation"]
            },
            response_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "results": {"type": "array", "items": {"type": "object"}},
                    "content": {"type": "string"},
                    "links": {"type": "array", "items": {"type": "string"}},
                    "title": {"type": "string"},
                    "url": {"type": "string"}
                }
            },
            requires_api_key=True,
            env_var_name="SEARCH_API_KEY",
            rate_limit=60,  # Requests per minute
            examples=[
                {
                    "operation": "search",
                    "query": "artificial intelligence news",
                    "num_results": 5
                },
                {
                    "operation": "get_page",
                    "url": "https://example.com",
                    "extract_text_only": True
                },
                {
                    "operation": "extract_links",
                    "url": "https://example.com"
                }
            ]
        )
        
        # Create and register the tool
        web_browser_tool = MCPTool(
            metadata=metadata,
            handler=self.handle_web_operation,
            is_async=True,
            env_var_name="SEARCH_API_KEY"
        )
        
        mcp_tools_registry.register_tool(web_browser_tool)
    
    async def handle_web_operation(
        self, parameters: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """
        Handle web browsing operations based on parameters.
        
        Args:
            parameters: Operation parameters
            agent_id: The agent ID
            
        Returns:
            Operation result
        """
        operation = parameters.get("operation")
        
        try:
            if operation == "search":
                return await self._search_web(parameters, agent_id)
            elif operation == "get_page":
                return await self._get_page(parameters, agent_id)
            elif operation == "extract_links":
                return await self._extract_links(parameters, agent_id)
            elif operation == "summarize":
                return await self._summarize_page(parameters, agent_id)
            else:
                return {
                    "success": False,
                    "message": f"Unknown operation: {operation}"
                }
        except Exception as e:
            logger.error(f"Error in web operation {operation}: {e}")
            return {
                "success": False,
                "message": f"Error in web operation: {str(e)}"
            }
    
    async def _search_web(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Search the web for a query."""
        query = params.get("query")
        if not query:
            return {"success": False, "message": "Query is required for search"}
        
        num_results = params.get("num_results", 5)
        
        # Generate cache key
        cache_key = f"search:{query}:{num_results}"
        
        # Check cache first
        cached = await multi_level_cache.get(cache_key, CacheType.API)
        if cached:
            return {**cached, "from_cache": True}
        
        try:
            # If using Google Search API
            if self.search_api_key and self.search_engine_id:
                return await self._google_search(query, num_results, agent_id)
            
            # Fallback to a basic search implementation
            return await self._basic_search(query, num_results, agent_id)
            
        except Exception as e:
            logger.error(f"Error searching web: {e}")
            return {"success": False, "message": f"Search error: {str(e)}"}
    
    async def _google_search(self, query: str, num_results: int, agent_id: str) -> Dict[str, Any]:
        """Search using Google Search API."""
        api_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.search_api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10)  # Google API limits to 10 per request
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, params=params, timeout=10)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "message": f"Search API error: {response.status_code}"
                }
            
            data = response.json()
            
            if "items" not in data:
                return {
                    "success": True,
                    "results": [],
                    "total_results": 0,
                    "message": "No results found"
                }
            
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "display_link": item.get("displayLink", "")
                })
            
            result_data = {
                "success": True,
                "results": results,
                "total_results": int(data.get("searchInformation", {}).get("totalResults", 0)),
                "query": query
            }
            
            # Cache the results
            cache_key = f"search:{query}:{num_results}"
            await multi_level_cache.set(cache_key, result_data, CacheType.API)
            
            return result_data
    
    async def _basic_search(self, query: str, num_results: int, agent_id: str) -> Dict[str, Any]:
        """Basic search implementation fallback."""
        # This is a very basic search implementation
        # In a production environment, use a proper search API
        search_url = f"https://www.google.com/search?q={query}"
        
        headers = {"User-Agent": self.user_agent}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, headers=headers, follow_redirects=True, timeout=10)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "message": f"Search error: status code {response.status_code}"
                }
            
            # Parse results
            soup = BeautifulSoup(response.text, "html.parser")
            search_results = []
            
            # Extract search results (this is simplistic and may break with Google layout changes)
            results = soup.select("div.g")[:num_results]
            
            for result in results:
                title_element = result.select_one("h3")
                link_element = result.select_one("a")
                snippet_element = result.select_one("div.VwiC3b")
                
                if title_element and link_element and "href" in link_element.attrs:
                    href = link_element["href"]
                    if href.startswith("/url?q="):
                        href = href[7:].split("&")[0]
                    
                    search_results.append({
                        "title": title_element.get_text(),
                        "link": href,
                        "snippet": snippet_element.get_text() if snippet_element else "",
                        "display_link": urlparse(href).netloc
                    })
            
            result_data = {
                "success": True,
                "results": search_results,
                "total_results": len(search_results),
                "query": query
            }
            
            # Cache the results
            cache_key = f"search:{query}:{num_results}"
            await multi_level_cache.set(cache_key, result_data, CacheType.API)
            
            return result_data
    
    async def _get_page(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Get the content of a web page."""
        url = params.get("url")
        if not url:
            return {"success": False, "message": "URL is required for get_page"}
        
        extract_text_only = params.get("extract_text_only", False)
        extract_images = params.get("extract_images", False)
        timeout = params.get("timeout", 10)
        select_element = params.get("select_element")
        
        # Generate cache key
        cache_options = f"{extract_text_only}:{extract_images}:{select_element}"
        cache_key = f"page:{url}:{cache_options}"
        
        # Check cache first
        cached = await multi_level_cache.get(cache_key, CacheType.API)
        if cached:
            return {**cached, "from_cache": True}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, 
                    headers={"User-Agent": self.user_agent},
                    follow_redirects=True,
                    timeout=timeout
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "message": f"Failed to fetch page: status code {response.status_code}"
                    }
                
                # Process content
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract title
                title = soup.title.string if soup.title else ""
                
                # Extract specific element if requested
                if select_element:
                    selected = soup.select(select_element)
                    if selected:
                        content_html = "".join(str(e) for e in selected)
                        content_text = " ".join(e.get_text(" ", strip=True) for e in selected)
                    else:
                        return {
                            "success": False,
                            "message": f"Element not found: {select_element}"
                        }
                else:
                    # Remove script and style elements
                    for element in soup(["script", "style"]):
                        element.decompose()
                    
                    content_html = str(soup)
                    content_text = soup.get_text(" ", strip=True)
                    # Clean up whitespace
                    content_text = re.sub(r'\s+', ' ', content_text).strip()
                
                result = {
                    "success": True,
                    "url": url,
                    "title": title,
                    "content": content_text if extract_text_only else content_html
                }
                
                # Add images if requested
                if extract_images:
                    image_urls = []
                    for img in soup.find_all("img"):
                        if "src" in img.attrs:
                            img_url = img["src"]
                            if not img_url.startswith(("http://", "https://")):
                                img_url = urljoin(url, img_url)
                            image_urls.append(img_url)
                    
                    result["images"] = image_urls
                
                # Cache the result
                await multi_level_cache.set(cache_key, result, CacheType.API)
                
                return result
                
        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            return {"success": False, "message": f"Error fetching page: {str(e)}"}
    
    async def _extract_links(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Extract links from a web page."""
        url = params.get("url")
        if not url:
            return {"success": False, "message": "URL is required for extract_links"}
        
        # Generate cache key
        cache_key = f"links:{url}"
        
        # Check cache first
        cached = await multi_level_cache.get(cache_key, CacheType.API)
        if cached:
            return {**cached, "from_cache": True}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, 
                    headers={"User-Agent": self.user_agent},
                    follow_redirects=True,
                    timeout=10
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "message": f"Failed to fetch page: status code {response.status_code}"
                    }
                
                # Parse links
                soup = BeautifulSoup(response.text, "html.parser")
                links = []
                
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    link_text = a.get_text(strip=True)
                    
                    # Make relative URLs absolute
                    if not href.startswith(("http://", "https://")):
                        href = urljoin(url, href)
                    
                    # Only include http/https URLs
                    if href.startswith(("http://", "https://")):
                        links.append({
                            "url": href,
                            "text": link_text if link_text else href
                        })
                
                result = {
                    "success": True,
                    "url": url,
                    "links": links,
                    "count": len(links)
                }
                
                # Cache the result
                await multi_level_cache.set(cache_key, result, CacheType.API)
                
                return result
                
        except Exception as e:
            logger.error(f"Error extracting links from {url}: {e}")
            return {"success": False, "message": f"Error extracting links: {str(e)}"}
    
    async def _summarize_page(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """
        Summarize a web page using basic extraction techniques.
        For more advanced summarization, integrate with an LLM API.
        """
        url = params.get("url")
        if not url:
            return {"success": False, "message": "URL is required for summarize"}
        
        # Generate cache key
        cache_key = f"summary:{url}"
        
        # Check cache first
        cached = await multi_level_cache.get(cache_key, CacheType.API)
        if cached:
            return {**cached, "from_cache": True}
        
        try:
            # First get the page content
            page_result = await self._get_page(
                {"url": url, "extract_text_only": True},
                agent_id
            )
            
            if not page_result.get("success", False):
                return page_result
            
            content = page_result.get("content", "")
            title = page_result.get("title", "")
            
            # Simple extractive summarization
            # In a real implementation, use a more sophisticated algorithm or LLM
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 40]
            
            # Select a subset of sentences (simple approach)
            if len(sentences) > 10:
                summary_sentences = sentences[:3] + sentences[len(sentences)//2-1:len(sentences)//2+1] + sentences[-3:]
            else:
                summary_sentences = sentences
            
            summary = ". ".join(summary_sentences)
            
            result = {
                "success": True,
                "url": url,
                "title": title,
                "summary": summary[:1000] + "..." if len(summary) > 1000 else summary,
                "full_text_length": len(content)
            }
            
            # Cache the result
            await multi_level_cache.set(cache_key, result, CacheType.API)
            
            return result
                
        except Exception as e:
            logger.error(f"Error summarizing page {url}: {e}")
            return {"success": False, "message": f"Error summarizing page: {str(e)}"}


# Create a singleton instance
web_browser_tool = WebBrowserTool()
