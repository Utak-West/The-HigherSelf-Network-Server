"""
Context7 RAG integration for Higher Self Network Server.
Provides advanced RAG capabilities through the Context7 MCP service.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Set, Union

import httpx
from loguru import logger

from models.agent_models import Agent
from services.redis_service import redis_service

from .config import mcp_config


class Context7RAG:
    """Context7 RAG service integration."""

    def __init__(self):
        """Initialize Context7 RAG service."""
        self.config = mcp_config.get_config("context7")
        if not self.config or not self.config.enabled:
            logger.warning("Context7 RAG tool is not enabled or missing configuration")
            self.enabled = False
        else:
            self.enabled = True
            self.base_url = self.config.server_url
            self.headers = {"Content-Type": "application/json"}
            if self.config.auth_type == "api_key" and self.config.api_key:
                self.headers["Authorization"] = f"Bearer {self.config.api_key}"

    async def query(
        self,
        query_text: str,
        collection_name: str = "default",
        filters: Dict[str, Any] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Query the Context7 RAG system.

        Args:
            query_text: The query text to search for
            collection_name: Optional name of the collection to search in
            filters: Optional filters to apply to the search
            top_k: Number of results to return

        Returns:
            Dict containing query results
        """
        if not self.enabled:
            return {"error": "Context7 RAG is not enabled"}

        try:
            payload = {
                "query": query_text,
                "collection": collection_name,
                "top_k": top_k,
            }

            if filters:
                payload["filters"] = filters

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/query", json=payload, headers=self.headers
                )

                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error querying Context7 RAG: {e}")
            return {"error": str(e)}

    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any] = None,
        doc_id: str = None,
        collection_name: str = "default",
    ) -> Dict[str, Any]:
        """
        Add a document to the Context7 RAG system.

        Args:
            content: The document content
            metadata: Optional metadata for the document
            doc_id: Optional document ID
            collection_name: Optional collection name

        Returns:
            Dict containing document ID and status
        """
        if not self.enabled:
            return {"error": "Context7 RAG is not enabled"}

        try:
            payload = {"content": content, "collection": collection_name}

            if metadata:
                payload["metadata"] = metadata

            if doc_id:
                payload["id"] = doc_id

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/documents", json=payload, headers=self.headers
                )

                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error adding document to Context7 RAG: {e}")
            return {"error": str(e)}

    async def search_documents(
        self,
        search_text: str,
        collection_name: str = "default",
        filters: Dict[str, Any] = None,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Search for documents in the Context7 RAG system.

        Args:
            search_text: The text to search for
            collection_name: Optional name of the collection to search in
            filters: Optional filters to apply to the search
            top_k: Number of results to return

        Returns:
            Dict containing search results
        """
        if not self.enabled:
            return {"error": "Context7 RAG is not enabled"}

        try:
            payload = {
                "query": search_text,
                "collection": collection_name,
                "top_k": top_k,
            }

            if filters:
                payload["filters"] = filters

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/search", json=payload, headers=self.headers
                )

                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error searching documents in Context7 RAG: {e}")
            return {"error": str(e)}

    async def delete_document(
        self, doc_id: str, collection_name: str = "default"
    ) -> Dict[str, Any]:
        """
        Delete a document from the Context7 RAG system.

        Args:
            doc_id: The document ID to delete
            collection_name: Optional collection name

        Returns:
            Dict containing status of deletion
        """
        if not self.enabled:
            return {"error": "Context7 RAG is not enabled"}

        try:
            payload = {"id": doc_id, "collection": collection_name}

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/documents/{doc_id}",
                    params={"collection": collection_name},
                    headers=self.headers,
                )

                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error deleting document from Context7 RAG: {e}")
            return {"error": str(e)}

    async def update_document(
        self,
        doc_id: str,
        content: str = None,
        metadata: Dict[str, Any] = None,
        collection_name: str = "default",
    ) -> Dict[str, Any]:
        """
        Update a document in the Context7 RAG system.

        Args:
            doc_id: The document ID to update
            content: Optional new content for the document
            metadata: Optional metadata to update
            collection_name: Optional collection name

        Returns:
            Dict containing status of update
        """
        if not self.enabled:
            return {"error": "Context7 RAG is not enabled"}

        try:
            payload = {"id": doc_id, "collection": collection_name}

            if content is not None:
                payload["content"] = content

            if metadata is not None:
                payload["metadata"] = metadata

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.patch(
                    f"{self.base_url}/documents/{doc_id}",
                    json=payload,
                    headers=self.headers,
                )

                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error updating document in Context7 RAG: {e}")
            return {"error": str(e)}

    async def get_collections(self) -> Dict[str, Any]:
        """
        Get list of available collections.

        Returns:
            Dict containing list of collections
        """
        if not self.enabled:
            return {"error": "Context7 RAG is not enabled"}

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/collections", headers=self.headers
                )

                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting collections from Context7 RAG: {e}")
            return {"error": str(e)}

    async def create_collection(
        self, name: str, description: str = None
    ) -> Dict[str, Any]:
        """
        Create a new collection.

        Args:
            name: Name of the collection
            description: Optional description

        Returns:
            Dict containing status of creation
        """
        if not self.enabled:
            return {"error": "Context7 RAG is not enabled"}

        try:
            payload = {"name": name}

            if description:
                payload["description"] = description

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/collections", json=payload, headers=self.headers
                )

                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error creating collection in Context7 RAG: {e}")
            return {"error": str(e)}


# Create a singleton instance
context7_rag = Context7RAG()
