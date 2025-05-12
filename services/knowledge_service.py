"""
Knowledge Service for coordination between Notion and the vector store.

This service provides bidirectional synchronization between Notion databases
and the vector store, allowing for semantic search of Notion content.
"""

import os
import json
import hashlib
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from loguru import logger

from services.notion_service import NotionService
from knowledge.vector_store import get_vector_store
from knowledge.semantic_search import get_semantic_search
from knowledge.models import EmbeddingMeta
from knowledge.providers import provider_registry


class KnowledgeService:
    """Service for coordinating between Notion and the vector store."""
    
    def __init__(self, notion_service: NotionService = None):
        """
        Initialize the knowledge service.
        
        Args:
            notion_service: NotionService instance. If not provided,
                           a new instance will be created.
        """
        from services.notion_service import get_notion_service
        self.notion_service = notion_service or get_notion_service()
        self.vector_store = get_vector_store()
        self.semantic_search = get_semantic_search()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the knowledge service."""
        if self._initialized:
            return
        
        # Initialize dependencies
        await self.vector_store.initialize()
        await self.semantic_search.initialize()
        await provider_registry.initialize()
        
        self._initialized = True
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the knowledge service.
        
        Returns:
            Health check results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Check vector store
            vector_health = await self.vector_store.health_check()
            
            # Check embedding providers
            provider_health = await provider_registry.get_embeddings(["health check"])
            
            # Check Notion connection
            notion_health = await self.notion_service.health_check()
            
            return {
                "healthy": vector_health["healthy"] and provider_health["success"] and notion_health["healthy"],
                "vector_store": vector_health,
                "providers": {
                    "success": provider_health["success"],
                    "provider": provider_health.get("provider")
                },
                "notion": notion_health,
                "component": "knowledge_service"
            }
        except Exception as e:
            logger.error(f"Knowledge service health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "component": "knowledge_service"
            }
    
    async def sync_notion_page_to_vector(self, page_id: str, force_update: bool = False) -> Optional[UUID]:
        """
        Sync a Notion page to the vector store.
        
        Args:
            page_id: Notion page ID
            force_update: Whether to force an update even if the content hasn't changed
            
        Returns:
            UUID of the stored embedding record or None if failed
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get the page from Notion
            page = await self.notion_service.get_page(page_id)
            if not page:
                logger.error(f"Page {page_id} not found in Notion")
                return None
            
            # Extract the page content
            page_content = await self.notion_service.get_page_content(page_id)
            if not page_content:
                logger.warning(f"Page {page_id} has no content")
                page_content = ""
            
            # Include the page title in the content
            title = page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "")
            full_content = f"{title}\n\n{page_content}"
            
            # Compute content hash
            content_hash = hashlib.sha256(full_content.encode('utf-8')).hexdigest()
            
            # Check if content already exists with the same hash
            existing = await self.vector_store.supabase.execute_sql(
                """
                SELECT id::text FROM embeddings 
                WHERE notion_page_id = $1 AND content_hash = $2
                """,
                [page_id, content_hash]
            )
            
            if existing and not force_update:
                logger.info(f"Page {page_id} already exists in vector store with the same content")
                return UUID(existing[0]['id'])
            
            # Extract metadata
            database_id = page.get("parent", {}).get("database_id")
            tags = []
            
            # Extract tags from page properties
            for prop_name, prop_value in page.get("properties", {}).items():
                prop_type = prop_value.get("type")
                
                if prop_type == "multi_select":
                    # Add multi-select values as tags
                    tags.extend([option.get("name") for option in prop_value.get("multi_select", [])])
                elif prop_type == "select":
                    # Add select value as tag
                    select_value = prop_value.get("select", {})
                    if select_value and select_value.get("name"):
                        tags.append(select_value.get("name"))
            
            # Create metadata
            metadata = EmbeddingMeta(
                content_type="notion_page",
                source=f"notion_page:{page_id}",
                notion_reference=page_id,
                tags=tags,
                additional_meta={
                    "title": title,
                    "database_id": database_id,
                    "last_edited_time": page.get("last_edited_time"),
                    "created_time": page.get("created_time")
                }
            )
            
            # Store and embed the page content
            embedding_id = await self.semantic_search.store_and_embed_text(
                text=full_content,
                content_type="notion_page",
                metadata=metadata,
                notion_page_id=page_id,
                notion_database_id=database_id
            )
            
            if embedding_id:
                logger.info(f"Successfully synced page {page_id} to vector store: {embedding_id}")
            else:
                logger.error(f"Failed to sync page {page_id} to vector store")
            
            return embedding_id
            
        except Exception as e:
            logger.error(f"Error syncing Notion page to vector: {e}")
            return None
    
    async def sync_notion_database_to_vector(
        self,
        database_id: str,
        modified_since: Optional[datetime] = None,
        force_update: bool = False
    ) -> List[UUID]:
        """
        Sync a Notion database to the vector store.
        
        Args:
            database_id: Notion database ID
            modified_since: Only sync pages modified since this time
            force_update: Whether to force an update even if the content hasn't changed
            
        Returns:
            List of UUIDs of the stored embedding records
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Query the database
            filter_params = {}
            if modified_since:
                filter_params = {
                    "filter": {
                        "property": "last_edited_time",
                        "date": {
                            "on_or_after": modified_since.isoformat()
                        }
                    }
                }
            
            pages = await self.notion_service.query_database(database_id, filter_params)
            
            # Sync each page
            embedding_ids = []
            for page in pages:
                page_id = page.get("id")
                embedding_id = await self.sync_notion_page_to_vector(page_id, force_update)
                if embedding_id:
                    embedding_ids.append(embedding_id)
            
            logger.info(f"Synced {len(embedding_ids)} pages from database {database_id}")
            return embedding_ids
            
        except Exception as e:
            logger.error(f"Error syncing Notion database to vector: {e}")
            return []
    
    async def sync_all_notion_databases_to_vector(
        self,
        modified_since: Optional[datetime] = None,
        force_update: bool = False
    ) -> Dict[str, List[UUID]]:
        """
        Sync all configured Notion databases to the vector store.
        
        Args:
            modified_since: Only sync pages modified since this time
            force_update: Whether to force an update even if the content hasn't changed
            
        Returns:
            Dictionary mapping database IDs to lists of embedding IDs
        """
        if not self._initialized:
            await self.initialize()
        
        # Import the Notion database mapping
        from config.notion_databases import NOTION_DATABASES
        
        results = {}
        
        # Sync each database
        for db_name, db_info in NOTION_DATABASES.items():
            db_id = db_info.get("id")
            if not db_id:
                continue
            
            logger.info(f"Syncing Notion database: {db_name} ({db_id})")
            embedding_ids = await self.sync_notion_database_to_vector(
                db_id, modified_since, force_update)
            
            results[db_id] = embedding_ids
        
        return results
    
    async def semantic_search_notion(
        self,
        query: str,
        database_ids: Optional[List[str]] = None,
        content_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on Notion content.
        
        Args:
            query: Search query
            database_ids: Optional list of database IDs to search in
            content_types: Optional list of content types to search for
            limit: Maximum number of results
            
        Returns:
            List of search results with Notion metadata
        """
        if not self._initialized:
            await self.initialize()
        
        content_types = content_types or ["notion_page"]
        results = []
        
        if database_ids:
            # Search in each specified database
            for db_id in database_ids:
                db_results = await self.semantic_search.search(
                    query=query,
                    content_types=content_types,
                    notion_database_id=db_id,
                    limit=limit
                )
                results.extend(db_results)
        else:
            # Search across all databases
            results = await self.semantic_search.search(
                query=query,
                content_types=content_types,
                limit=limit
            )
        
        # Sort results by score and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:limit]
        
        # Enhance results with additional Notion metadata if needed
        enhanced_results = []
        for result in results:
            notion_page_id = result.get("notion_page_id")
            
            # Only enhance results with Notion page IDs
            if notion_page_id:
                # Get the page title and other basic info without full content
                try:
                    page_info = await self.notion_service.get_page_basic_info(notion_page_id)
                    
                    if page_info:
                        result["notion_title"] = page_info.get("title", "")
                        result["notion_url"] = page_info.get("url", "")
                        result["notion_created_time"] = page_info.get("created_time")
                        result["notion_last_edited_time"] = page_info.get("last_edited_time")
                except Exception as e:
                    logger.warning(f"Error enhancing result with Notion metadata: {e}")
            
            enhanced_results.append(result)
        
        return enhanced_results


# Singleton instance
_knowledge_service_instance = None

def get_knowledge_service() -> KnowledgeService:
    """Get the singleton KnowledgeService instance."""
    global _knowledge_service_instance
    if _knowledge_service_instance is None:
        _knowledge_service_instance = KnowledgeService()
    return _knowledge_service_instance