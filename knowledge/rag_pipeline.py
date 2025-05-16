"""
RAG (Retrieval-Augmented Generation) Pipeline for The HigherSelf Network Server.

This module provides a complete RAG pipeline for enhancing AI completions
with relevant context from the vector store.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from loguru import logger
from pydantic import BaseModel, Field

# Local imports
from knowledge.semantic_search import get_semantic_search
from knowledge.vector_store import get_vector_store
from services.ai_router import AIRouter


class RAGRequest(BaseModel):
    """Request for RAG-enhanced AI completion."""

    query: str
    max_tokens: int = 1000
    temperature: float = 0.7
    content_types: Optional[List[str]] = None
    notion_database_ids: Optional[List[str]] = None
    search_limit: int = 5
    similarity_threshold: float = 0.7
    system_message: Optional[str] = None
    include_sources: bool = True


class SourceReference(BaseModel):
    """Reference to a source document."""

    id: str
    content_type: str
    title: Optional[str] = None
    url: Optional[str] = None
    source: str
    similarity: float


class RAGResponse(BaseModel):
    """Response from RAG-enhanced AI completion."""

    text: str
    sources: List[SourceReference] = []
    success: bool = True
    error: Optional[str] = None


class RAGPipeline:
    """Pipeline for Retrieval-Augmented Generation."""

    def __init__(self):
        """Initialize the RAG pipeline."""
        self.semantic_search = None
        self.vector_store = None
        self.ai_router = None
        self._initialized = False

    async def initialize(self, ai_router: AIRouter):
        """
        Initialize the pipeline and its dependencies.

        Args:
            ai_router: AIRouter instance for completions
        """
        if self._initialized:
            return

        try:
            # Initialize semantic search and vector store
            self.semantic_search = await get_semantic_search()
            self.vector_store = await get_vector_store()

            # Set AI router
            self.ai_router = ai_router

            self._initialized = True
            logger.info("RAG pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG pipeline: {e}")
            raise

    async def generate(self, request: RAGRequest) -> RAGResponse:
        """
        Generate a RAG-enhanced completion.

        Args:
            request: RAG request

        Returns:
            RAG response with completion and sources
        """
        if not self._initialized:
            return RAGResponse(
                text="", sources=[], success=False, error="RAG pipeline not initialized"
            )

        try:
            # Retrieve relevant context
            search_results = await self._retrieve_context(
                query=request.query,
                content_types=request.content_types,
                notion_database_ids=request.notion_database_ids,
                limit=request.search_limit,
                threshold=request.similarity_threshold,
            )

            if not search_results:
                logger.warning(f"No relevant context found for query: {request.query}")
                # Fall back to standard completion without context
                return await self._generate_without_context(request)

            # Format context for the AI
            context = self._format_context(search_results)

            # Create sources list
            sources = []
            for result in search_results:
                source_ref = SourceReference(
                    id=result["id"],
                    content_type=result["content_type"],
                    title=result.get("title"),
                    url=self._extract_url(result),
                    source=result["source"],
                    similarity=result["score"],
                )
                sources.append(source_ref)

            # Generate completion with context
            completion = await self._generate_with_context(request, context)

            # Process completion response using helper method
            response_result = self._process_completion_response(completion)

            if not response_result["success"]:
                logger.error(f"Error generating completion: {response_result['error']}")
                return RAGResponse(
                    text="",
                    sources=sources,
                    success=False,
                    error=response_result["error"],
                )

            response_text = response_result["text"]

            # Format the response

            # Add sources if requested
            if request.include_sources:
                response_text = self._add_source_citations(response_text, sources)

            return RAGResponse(text=response_text, sources=sources, success=True)

        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            return RAGResponse(text="", sources=[], success=False, error=str(e))

    async def _retrieve_context(
        self,
        query: str,
        content_types: Optional[List[str]] = None,
        notion_database_ids: Optional[List[str]] = None,
        limit: int = 5,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from the vector store.

        Args:
            query: Search query
            content_types: Optional filter for content types
            notion_database_ids: Optional filter for Notion database IDs
            limit: Maximum number of results
            threshold: Similarity threshold

        Returns:
            List of search results
        """
        results = []

        # Search in Notion databases if specified
        if notion_database_ids:
            for db_id in notion_database_ids:
                db_results = await self.semantic_search.search(
                    query=query,
                    content_types=content_types,
                    notion_database_id=db_id,
                    limit=limit,
                    threshold=threshold,
                )
                results.extend(db_results)
        else:
            # Search across all content
            results = await self.semantic_search.search(
                query=query,
                content_types=content_types,
                limit=limit,
                threshold=threshold,
            )

        # Sort by score and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:limit]

        return results

    def _format_context(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Format search results into context for the AI.

        Args:
            search_results: List of search results

        Returns:
            Formatted context string
        """
        if not search_results:
            return ""

        context_parts = []

        for i, result in enumerate(search_results):
            # Extract metadata
            content_type = result.get("content_type", "unknown")
            title = result.get("title", f"Document {i+1}")
            source = result.get("source", "unknown source")

            # Format the context entry
            context_entry = f"[{i+1}] {title} ({content_type})\n{result['content']}\n"
            context_parts.append(context_entry)

        return "\n\n".join(context_parts)

    def _extract_url(self, result: Dict[str, Any]) -> Optional[str]:
        """
        Extract URL from search result.

        Args:
            result: Search result

        Returns:
            URL if available, None otherwise
        """
        # Check for web page URL
        if result.get("content_type") == "web_page":
            metadata = result.get("metadata", {})
            if isinstance(metadata, dict):
                return metadata.get("url")
            elif isinstance(metadata, str):
                try:
                    metadata_dict = json.loads(metadata)
                    return metadata_dict.get("url")
                except:
                    pass

        # Check for Notion page URL
        if result.get("content_type") == "notion_page" and result.get("notion_page_id"):
            return f"https://notion.so/{result['notion_page_id'].replace('-', '')}"

        return None

    async def _generate_with_context(
        self, request: RAGRequest, context: str
    ) -> Dict[str, Any]:
        """
        Generate a completion with context.

        Args:
            request: RAG request
            context: Formatted context

        Returns:
            Completion response
        """
        # Create system message with context
        system_message = (
            request.system_message
            or "You are a helpful assistant that answers questions based on the provided context."
        )
        system_message += "\n\nContext information is below. Use this information to answer the user's question.\n"
        system_message += "If the answer cannot be found in the context, say 'I don't have enough information to answer this question.'\n"
        system_message += (
            "Do not make up information that is not supported by the context.\n\n"
        )
        system_message += context

        # Create completion request
        from services.ai_providers import AICompletionRequest

        completion_request = AICompletionRequest(
            prompt=request.query,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system_message=system_message,
        )

        # Get completion
        return await self.ai_router.get_completion(completion_request)

    async def _generate_without_context(self, request: RAGRequest) -> RAGResponse:
        """
        Generate a completion without context when no relevant context is found.

        Args:
            request: RAG request

        Returns:
            RAG response
        """
        # Create system message
        system_message = (
            request.system_message
            or "You are a helpful assistant that answers questions based on your knowledge."
        )
        system_message += "\n\nIf you don't know the answer, say 'I don't have enough information to answer this question.'"

        # Create completion request
        from services.ai_providers import AICompletionRequest

        completion_request = AICompletionRequest(
            prompt=request.query,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system_message=system_message,
        )

        # Get completion
        completion = await self.ai_router.get_completion(completion_request)

        # Process completion response using helper method
        response_result = self._process_completion_response(completion)

        if not response_result["success"]:
            logger.error(
                f"Error generating completion without context: {response_result['error']}"
            )
            return RAGResponse(
                text="", sources=[], success=False, error=response_result["error"]
            )

        return RAGResponse(text=response_result["text"], sources=[], success=True)

    def _add_source_citations(self, text: str, sources: List[SourceReference]) -> str:
        """
        Add source citations to the response text.

        Args:
            text: Response text
            sources: List of source references

        Returns:
            Text with source citations
        """
        if not sources:
            return text

        # Add sources section
        sources_text = "\n\nSources:\n"
        for i, source in enumerate(sources):
            title = source.title or f"Document {i+1}"
            url_text = f" - {source.url}" if source.url else ""
            sources_text += f"[{i+1}] {title} ({source.content_type}){url_text}\n"

        return text + sources_text

    def _process_completion_response(self, completion):
        """
        Helper method to process completion responses consistently.

        Args:
            completion: The completion response from AI router

        Returns:
            Dict with keys:
                - success: Boolean indicating success
                - text: Response text (empty string if failed)
                - error: Error message (None if successful)
        """
        result = {"success": False, "text": "", "error": None}

        # Handle AICompletionResponse object
        if hasattr(completion, "text"):
            # Check for errors in metadata
            if (
                hasattr(completion, "metadata")
                and completion.metadata
                and completion.metadata.get("error")
            ):
                result["error"] = completion.metadata.get(
                    "error", "Failed to generate completion"
                )
                return result

            # Success case
            result["success"] = True
            result["text"] = completion.text
            return result

        # Handle dictionary response (legacy format)
        elif isinstance(completion, dict):
            if not completion.get("success", False):
                result["error"] = completion.get(
                    "error", "Failed to generate completion"
                )
                return result

            # Success case
            result["success"] = True
            result["text"] = completion.get("text", "")
            return result

        # Unknown response type
        else:
            error_msg = f"Unknown completion response type: {type(completion)}"
            logger.error(error_msg)
            result["error"] = error_msg
            return result


# Singleton instance
_rag_pipeline = None


async def get_rag_pipeline(ai_router: AIRouter) -> RAGPipeline:
    """Get or create the RAG pipeline singleton."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
        await _rag_pipeline.initialize(ai_router)
    return _rag_pipeline
