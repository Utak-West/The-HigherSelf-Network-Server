"""
Memory MCP Tool for Higher Self Network Server.
Provides a tool for agents to create, retrieve, and manage memories.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from integrations.mcp_tools.mcp_tools_registry import (MCPTool, ToolCapability,
                                                       ToolMetadata,
                                                       mcp_tools_registry)
from services.cache_service import CacheLevel, CacheType, multi_level_cache
from services.mongodb_service import mongo_service

# Collection name for memories
MEMORIES_COLLECTION = "agent_memories"


class MemoryItem(BaseModel):
    """Model for a memory item."""

    memory_id: str = Field(..., description="Unique identifier for the memory")
    agent_id: str = Field(..., description="Agent who owns this memory")
    content: str = Field(..., description="Memory content")
    tags: List[str] = Field(
        default_factory=list, description="Tags for categorizing the memory"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for the memory"
    )
    created_at: str = Field(..., description="Creation timestamp")
    last_accessed_at: str = Field(..., description="Last access timestamp")
    importance: int = Field(
        default=1, description="Importance score (1-10, higher is more important)"
    )


class MemoryTool:
    """
    Implementation of memory management tool for agents.
    Provides operations to create, retrieve, update, and delete memories.
    """

    def __init__(self):
        """Initialize the memory tool."""
        self.enabled = True

        # Register with registry
        self._register()

        logger.info("Memory MCP tool initialized")

    def _register(self):
        """Register this tool with the MCP tools registry."""
        metadata = ToolMetadata(
            name="memory",
            description="Tool for creating and retrieving agent memories",
            version="1.0.0",
            capabilities=[ToolCapability.MEMORY],
            parameters_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["create", "get", "search", "update", "delete", "list"],
                        "description": "The memory operation to perform",
                    },
                    "memory_id": {
                        "type": "string",
                        "description": "ID of the memory (required for get, update, delete)",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content of the memory (required for create, update)",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for the memory",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query (required for search)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of results to return",
                    },
                    "importance": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "Importance score (1-10)",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata for the memory",
                    },
                },
                "required": ["operation"],
            },
            response_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "memory_id": {"type": "string"},
                    "memories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "memory_id": {"type": "string"},
                                "content": {"type": "string"},
                                "tags": {"type": "array", "items": {"type": "string"}},
                                "created_at": {"type": "string"},
                                "importance": {"type": "integer"},
                            },
                        },
                    },
                },
            },
            requires_api_key=False,
            examples=[
                {
                    "operation": "create",
                    "content": "The user prefers dark mode for all interfaces.",
                    "tags": ["preferences", "ui"],
                    "importance": 5,
                },
                {"operation": "search", "query": "user preferences", "limit": 5},
                {"operation": "get", "memory_id": "mem_12345"},
            ],
        )

        # Create and register the tool
        memory_tool = MCPTool(
            metadata=metadata, handler=self.handle_memory_operation, is_async=True
        )

        mcp_tools_registry.register_tool(memory_tool)

    async def handle_memory_operation(
        self, parameters: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """
        Handle memory operations based on parameters.

        Args:
            parameters: Operation parameters
            agent_id: The agent ID

        Returns:
            Operation result
        """
        operation = parameters.get("operation")

        try:
            if operation == "create":
                return await self._create_memory(parameters, agent_id)
            elif operation == "get":
                return await self._get_memory(parameters, agent_id)
            elif operation == "search":
                return await self._search_memories(parameters, agent_id)
            elif operation == "update":
                return await self._update_memory(parameters, agent_id)
            elif operation == "delete":
                return await self._delete_memory(parameters, agent_id)
            elif operation == "list":
                return await self._list_memories(parameters, agent_id)
            else:
                return {"success": False, "message": f"Unknown operation: {operation}"}
        except Exception as e:
            logger.error(f"Error in memory operation {operation}: {e}")
            return {"success": False, "message": f"Error in memory operation: {str(e)}"}

    async def _create_memory(
        self, params: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """Create a new memory."""
        content = params.get("content")
        if not content:
            return {"success": False, "message": "Content is required"}

        # Generate a unique memory ID
        from uuid import uuid4

        memory_id = f"mem_{uuid4().hex[:8]}"

        # Create memory item
        from datetime import datetime

        now = datetime.utcnow().isoformat()

        memory = {
            "memory_id": memory_id,
            "agent_id": agent_id,
            "content": content,
            "tags": params.get("tags", []),
            "metadata": params.get("metadata", {}),
            "created_at": now,
            "last_accessed_at": now,
            "importance": params.get("importance", 1),
        }

        # Store in MongoDB
        await mongo_service.async_insert_one(MEMORIES_COLLECTION, memory)

        # Store in cache
        cache_key = f"memory:{memory_id}"
        await multi_level_cache.set(cache_key, memory, CacheType.AGENT)

        return {
            "success": True,
            "message": "Memory created successfully",
            "memory_id": memory_id,
        }

    async def _get_memory(
        self, params: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """Get a memory by ID."""
        memory_id = params.get("memory_id")
        if not memory_id:
            return {"success": False, "message": "Memory ID is required"}

        # Try to get from cache first
        cache_key = f"memory:{memory_id}"
        memory = await multi_level_cache.get(cache_key, CacheType.AGENT)

        # If not in cache, get from MongoDB
        if not memory:
            memory = await mongo_service.async_find_one(
                MEMORIES_COLLECTION, {"memory_id": memory_id, "agent_id": agent_id}
            )

            # Store in cache if found
            if memory:
                await multi_level_cache.set(cache_key, memory, CacheType.AGENT)

        if not memory:
            return {"success": False, "message": "Memory not found"}

        # Update last accessed time
        from datetime import datetime

        now = datetime.utcnow().isoformat()

        await mongo_service.async_update_one(
            MEMORIES_COLLECTION,
            {"memory_id": memory_id},
            {"$set": {"last_accessed_at": now}},
        )

        # Don't include MongoDB _id in response
        if "_id" in memory:
            del memory["_id"]

        return {"success": True, "memory": memory}

    async def _search_memories(
        self, params: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """Search memories by query."""
        query = params.get("query")
        if not query:
            return {"success": False, "message": "Query is required for search"}

        limit = params.get("limit", 10)

        # First check if we have vector search available
        try:
            # Check if we have a vector search service registered
            vector_search_available = False
            # ... (code to check for vector search)

            if vector_search_available:
                # Use vector search
                pass
            else:
                # Fall back to text search
                mongo_query = {"agent_id": agent_id, "$text": {"$search": query}}

                # If tags specified, add to query
                if "tags" in params:
                    mongo_query["tags"] = {"$all": params["tags"]}

                # Execute search
                results = await mongo_service.async_find_many(
                    MEMORIES_COLLECTION,
                    mongo_query,
                    sort_options=[("importance", -1)],
                    limit=limit,
                )

                # Clean up results
                clean_results = []
                for memory in results:
                    if "_id" in memory:
                        del memory["_id"]
                    clean_results.append(memory)

                return {
                    "success": True,
                    "memories": clean_results,
                    "count": len(clean_results),
                }

        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return {"success": False, "message": f"Search error: {str(e)}"}

    async def _update_memory(
        self, params: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """Update an existing memory."""
        memory_id = params.get("memory_id")
        if not memory_id:
            return {"success": False, "message": "Memory ID is required"}

        # Check if memory exists
        existing = await mongo_service.async_find_one(
            MEMORIES_COLLECTION, {"memory_id": memory_id, "agent_id": agent_id}
        )

        if not existing:
            return {"success": False, "message": "Memory not found"}

        # Prepare updates
        updates = {}
        if "content" in params:
            updates["content"] = params["content"]
        if "tags" in params:
            updates["tags"] = params["tags"]
        if "importance" in params:
            updates["importance"] = params["importance"]
        if "metadata" in params:
            updates["metadata"] = params["metadata"]

        # Update last accessed time
        from datetime import datetime

        updates["last_accessed_at"] = datetime.utcnow().isoformat()

        # Update in MongoDB
        await mongo_service.async_update_one(
            MEMORIES_COLLECTION,
            {"memory_id": memory_id, "agent_id": agent_id},
            {"$set": updates},
        )

        # Update cache
        cache_key = f"memory:{memory_id}"
        await multi_level_cache.delete(cache_key, CacheType.AGENT)

        # Get updated memory
        updated = await mongo_service.async_find_one(
            MEMORIES_COLLECTION, {"memory_id": memory_id}
        )

        if "_id" in updated:
            del updated["_id"]

        # Update cache with new version
        await multi_level_cache.set(cache_key, updated, CacheType.AGENT)

        return {
            "success": True,
            "message": "Memory updated successfully",
            "memory": updated,
        }

    async def _delete_memory(
        self, params: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """Delete a memory by ID."""
        memory_id = params.get("memory_id")
        if not memory_id:
            return {"success": False, "message": "Memory ID is required"}

        # Delete from MongoDB
        result = await mongo_service.async_delete_one(
            MEMORIES_COLLECTION, {"memory_id": memory_id, "agent_id": agent_id}
        )

        # Delete from cache
        cache_key = f"memory:{memory_id}"
        await multi_level_cache.delete(cache_key, CacheType.AGENT)

        if result == 0:
            return {"success": False, "message": "Memory not found or already deleted"}

        return {"success": True, "message": "Memory deleted successfully"}

    async def _list_memories(
        self, params: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """List memories for an agent."""
        limit = params.get("limit", 50)

        # Build query
        query = {"agent_id": agent_id}

        # Add tag filter if specified
        if "tags" in params:
            query["tags"] = {"$all": params["tags"]}

        # Execute query
        results = await mongo_service.async_find_many(
            MEMORIES_COLLECTION,
            query,
            sort_options=[("importance", -1), ("last_accessed_at", -1)],
            limit=limit,
        )

        # Clean up results
        clean_results = []
        for memory in results:
            if "_id" in memory:
                del memory["_id"]
            clean_results.append(memory)

        return {"success": True, "memories": clean_results, "count": len(clean_results)}


# Create a singleton instance
memory_tool = MemoryTool()
