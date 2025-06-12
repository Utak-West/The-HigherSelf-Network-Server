"""
Perplexity MCP Tool for Higher Self Network Server.
Provides a tool for agents to use Perplexity for advanced question-answering with citations.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from integrations.mcp_tools.mcp_tools_registry import (MCPTool, ToolCapability,
                                                       ToolMetadata,
                                                       mcp_tools_registry)
from services.cache_service import CacheLevel, CacheType, multi_level_cache


class PerplexityTool:
    """
    Implementation of Perplexity question-answering tool for agents.
    Provides operations to ask factual questions with web citations.
    """

    def __init__(self):
        """Initialize the Perplexity tool."""
        self.enabled = True
        self.perplexity_api_key = os.environ.get("PERPLEXITY_API_KEY", "")
        self.perplexity_api_url = "https://api.perplexity.ai/chat/completions"

        # Register with registry
        self._register()

        logger.info("Perplexity MCP tool initialized")

    def _register(self):
        """Register this tool with the MCP tools registry."""
        metadata = ToolMetadata(
            name="perplexity",
            description="Tool for advanced question-answering with web citations powered by Perplexity AI",
            version="1.0.0",
            capabilities=[
                ToolCapability.RETRIEVAL,
                ToolCapability.SEARCH,
                ToolCapability.REASONING,
            ],
            parameters_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or query to answer",
                    },
                    "model": {
                        "type": "string",
                        "enum": [
                            "sonar-medium-online",
                            "sonar-small-online",
                            "sonar-small-chat",
                        ],
                        "description": "Perplexity model to use",
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Model temperature (0.0-1.0)",
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens in the response",
                    },
                },
                "required": ["query"],
            },
            response_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "answer": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "object"}},
                    "model": {"type": "string"},
                    "usage": {"type": "object"},
                },
            },
            requires_api_key=True,
            env_var_name="PERPLEXITY_API_KEY",
            rate_limit=60,  # Requests per minute
            examples=[
                {
                    "query": "What are the latest developments in AI governance?",
                    "model": "sonar-medium-online",
                },
                {
                    "query": "Explain the impact of climate change on biodiversity",
                    "model": "sonar-medium-online",
                    "temperature": 0.7,
                },
            ],
        )

        # Create and register the tool
        perplexity_tool = MCPTool(
            metadata=metadata,
            handler=self.handle_perplexity_query,
            is_async=True,
            env_var_name="PERPLEXITY_API_KEY",
        )

        mcp_tools_registry.register_tool(perplexity_tool)

    async def handle_perplexity_query(
        self, parameters: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """
        Handle Perplexity queries based on parameters.

        Args:
            parameters: Query parameters
            agent_id: The agent ID

        Returns:
            Query result with answer and sources
        """
        query = parameters.get("query")
        if not query:
            return {"success": False, "message": "Query is required"}

        model = parameters.get("model", "sonar-medium-online")
        temperature = parameters.get("temperature", 0.7)
        max_tokens = parameters.get("max_tokens", 2048)

        # Generate cache key
        cache_key_parts = [query, model, str(temperature), str(max_tokens)]
        cache_key = f"perplexity:{':'.join(cache_key_parts)}"

        # Check cache first
        cached = await multi_level_cache.get(cache_key, CacheType.API)
        if cached:
            return {**cached, "from_cache": True}

        if not self.perplexity_api_key:
            return {"success": False, "message": "Perplexity API key not configured"}

        try:
            # Prepare the API request
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json",
            }

            # Create a system message for web search
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions accurately with citations to online sources.",
                    },
                    {"role": "user", "content": query},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.perplexity_api_url, headers=headers, json=payload, timeout=60
                )

                if response.status_code != 200:
                    return {
                        "success": False,
                        "message": f"Perplexity API error: {response.status_code}",
                        "details": response.text,
                    }

                data = response.json()

                # Extract the answer and sources
                answer_text = (
                    data.get("choices", [{}])[0].get("message", {}).get("content", "")
                )

                # Parse citations from the text or extract from metadata
                citations = []

                # Process links if present in message metadata
                message = data.get("choices", [{}])[0].get("message", {})
                if "tool_calls" in message and message["tool_calls"]:
                    for tool_call in message["tool_calls"]:
                        if tool_call.get("function", {}).get("name") == "search":
                            try:
                                search_args = json.loads(
                                    tool_call["function"]["arguments"]
                                )
                                if "links" in search_args:
                                    for link in search_args["links"]:
                                        citations.append(
                                            {
                                                "title": link.get("title", ""),
                                                "url": link.get("url", ""),
                                                "snippet": link.get("snippet", ""),
                                            }
                                        )
                            except Exception as e:
                                logger.warning(
                                    f"Error parsing tool call arguments: {e}"
                                )

                # Use regex to extract URLs if no tool calls found
                if not citations:
                    import re

                    # Look for URLs in format [1]: http://example.com
                    url_pattern = r"\[(\d+)\]:\s*(https?://\S+)"
                    for match in re.finditer(url_pattern, answer_text):
                        index = match.group(1)
                        url = match.group(2)
                        citations.append({"index": index, "url": url})

                result = {
                    "success": True,
                    "answer": answer_text,
                    "sources": citations,
                    "model": model,
                    "usage": data.get("usage", {}),
                }

                # Cache the result
                await multi_level_cache.set(
                    cache_key, result, CacheType.API, ttl_override=3600
                )  # 1-hour cache

                return result

        except Exception as e:
            logger.error(f"Error in Perplexity query: {e}")
            return {"success": False, "message": f"Error in Perplexity query: {str(e)}"}

    async def extract_structured_answer(self, raw_answer: str) -> Dict[str, Any]:
        """Extract a structured answer with citations from raw text."""
        # Extract the main answer text and citations
        main_text = raw_answer
        citations = []

        # Try to find citation markers like [1], [2], etc.
        import re

        citation_pattern = r"\[(\d+)\]"
        citation_matches = list(re.finditer(citation_pattern, raw_answer))

        if citation_matches:
            # Find where citations begin
            last_match = citation_matches[-1]
            citation_list_pattern = r"\[\d+\]:\s*.*"
            citation_list_match = re.search(
                citation_list_pattern, raw_answer[last_match.start() :]
            )

            if citation_list_match:
                citation_start = last_match.start() + citation_list_match.start()
                main_text = raw_answer[:citation_start].strip()
                citation_text = raw_answer[citation_start:].strip()

                # Extract individual citations
                citation_items = re.finditer(
                    r"\[(\d+)\]:\s*(.*?)(?=\[\d+\]:|$)", citation_text, re.DOTALL
                )
                for item in citation_items:
                    index = item.group(1)
                    citation = item.group(2).strip()

                    # Try to extract URL from citation
                    url_match = re.search(r"(https?://\S+)", citation)
                    url = url_match.group(1) if url_match else ""

                    citations.append({"index": index, "text": citation, "url": url})

        return {"answer": main_text, "citations": citations}


# Create a singleton instance
perplexity_tool = PerplexityTool()
