"""
Optimized Query Service for HigherSelf Network Server.

Provides optimized database query patterns with caching, connection pooling,
and performance monitoring for both Notion API and MongoDB operations.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Callable
from functools import wraps
import hashlib

from loguru import logger
from pydantic import BaseModel

from models.base import CacheableModel, OptimizedBaseModel
from services.enhanced_cache_service import CacheService, CacheType
from services.notion_service import NotionService
from services.mongodb_service import MongoDBService
from services.redis_service import redis_service

T = TypeVar('T', bound=BaseModel)


class QueryMetrics:
    """Query performance metrics tracking."""
    
    def __init__(self):
        self.total_queries = 0
        self.cached_queries = 0
        self.failed_queries = 0
        self.total_latency = 0.0
        self.notion_queries = 0
        self.mongodb_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total) if total > 0 else 0.0
    
    @property
    def avg_latency(self) -> float:
        """Calculate average query latency."""
        return (self.total_latency / self.total_queries) if self.total_queries > 0 else 0.0


class OptimizedQueryService:
    """
    Optimized query service with caching and performance monitoring.
    
    Features:
    - Automatic query result caching
    - Connection pooling optimization
    - Query performance monitoring
    - Batch query support
    - Intelligent cache invalidation
    """
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()
        self.notion_service = NotionService()
        self.mongodb_service = MongoDBService()
        self.metrics = QueryMetrics()
        
        # Query optimization settings
        self.default_cache_ttl = 300  # 5 minutes
        self.batch_size = 100
        self.max_concurrent_queries = 10
        
        # Cache TTL by query type
        self.cache_ttl_mapping = {
            'notion_database_query': 600,  # 10 minutes
            'notion_page_get': 300,        # 5 minutes
            'mongodb_find': 300,           # 5 minutes
            'mongodb_aggregate': 600,      # 10 minutes
        }
    
    def _generate_query_cache_key(self, query_type: str, **params) -> str:
        """Generate cache key for query parameters."""
        # Create deterministic hash of parameters
        param_string = "|".join(f"{k}:{v}" for k, v in sorted(params.items()))
        param_hash = hashlib.md5(param_string.encode()).hexdigest()
        return f"query:{query_type}:{param_hash}"
    
    def _track_query_metrics(self, query_type: str, latency: float, cached: bool, success: bool):
        """Track query performance metrics."""
        self.metrics.total_queries += 1
        self.metrics.total_latency += latency
        
        if cached:
            self.metrics.cached_queries += 1
            self.metrics.cache_hits += 1
        else:
            self.metrics.cache_misses += 1
        
        if not success:
            self.metrics.failed_queries += 1
        
        if 'notion' in query_type:
            self.metrics.notion_queries += 1
        elif 'mongodb' in query_type:
            self.metrics.mongodb_queries += 1
    
    async def query_notion_database(
        self,
        database_id: str,
        model_class: Type[T],
        filter_conditions: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None
    ) -> List[T]:
        """
        Query Notion database with caching and optimization.
        
        Args:
            database_id: Notion database ID
            model_class: Pydantic model class for results
            filter_conditions: Notion API filter conditions
            sorts: Notion API sort conditions
            use_cache: Whether to use caching
            cache_ttl: Cache TTL override
            
        Returns:
            List of model instances
        """
        start_time = time.time()
        query_type = 'notion_database_query'
        
        # Generate cache key
        cache_key = self._generate_query_cache_key(
            query_type,
            database_id=database_id,
            filter_conditions=filter_conditions,
            sorts=sorts,
            model_class=model_class.__name__
        )
        
        try:
            # Try cache first if enabled
            if use_cache:
                cached_results = await self.cache_service.get(
                    cache_key, 
                    cache_type=CacheType.NOTION
                )
                if cached_results is not None:
                    latency = time.time() - start_time
                    self._track_query_metrics(query_type, latency, True, True)
                    
                    # Deserialize cached results
                    return [model_class(**item) for item in cached_results]
            
            # Execute query
            results = await self.notion_service.query_database(
                database_id=database_id,
                model_class=model_class,
                filter_conditions=filter_conditions,
                sorts=sorts
            )
            
            # Cache results if enabled
            if use_cache and results:
                ttl = cache_ttl or self.cache_ttl_mapping.get(query_type, self.default_cache_ttl)
                serialized_results = [
                    result.model_dump() if hasattr(result, 'model_dump') else result.dict()
                    for result in results
                ]
                await self.cache_service.set(
                    cache_key,
                    serialized_results,
                    ttl=ttl,
                    cache_type=CacheType.NOTION
                )
            
            latency = time.time() - start_time
            self._track_query_metrics(query_type, latency, False, True)
            
            return results
            
        except Exception as e:
            latency = time.time() - start_time
            self._track_query_metrics(query_type, latency, False, False)
            logger.error(f"Notion database query failed: {e}")
            raise
    
    async def get_notion_page(
        self,
        page_id: str,
        model_class: Type[T],
        use_cache: bool = True,
        cache_ttl: Optional[int] = None
    ) -> Optional[T]:
        """
        Get Notion page with caching.
        
        Args:
            page_id: Notion page ID
            model_class: Pydantic model class
            use_cache: Whether to use caching
            cache_ttl: Cache TTL override
            
        Returns:
            Model instance or None
        """
        start_time = time.time()
        query_type = 'notion_page_get'
        
        cache_key = self._generate_query_cache_key(
            query_type,
            page_id=page_id,
            model_class=model_class.__name__
        )
        
        try:
            # Try cache first
            if use_cache:
                cached_result = await self.cache_service.get_model(
                    cache_key,
                    model_class,
                    cache_type=CacheType.NOTION
                )
                if cached_result is not None:
                    latency = time.time() - start_time
                    self._track_query_metrics(query_type, latency, True, True)
                    return cached_result
            
            # Execute query
            result = await self.notion_service.get_page(page_id, model_class)
            
            # Cache result
            if use_cache and result:
                ttl = cache_ttl or self.cache_ttl_mapping.get(query_type, self.default_cache_ttl)
                await self.cache_service.set_model(
                    cache_key,
                    result,
                    ttl=ttl,
                    cache_type=CacheType.NOTION
                )
            
            latency = time.time() - start_time
            self._track_query_metrics(query_type, latency, False, True)
            
            return result
            
        except Exception as e:
            latency = time.time() - start_time
            self._track_query_metrics(query_type, latency, False, False)
            logger.error(f"Notion page get failed: {e}")
            raise
    
    async def batch_query_notion_pages(
        self,
        page_ids: List[str],
        model_class: Type[T],
        use_cache: bool = True,
        max_concurrent: Optional[int] = None
    ) -> List[Optional[T]]:
        """
        Batch query multiple Notion pages with concurrency control.
        
        Args:
            page_ids: List of Notion page IDs
            model_class: Pydantic model class
            use_cache: Whether to use caching
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of model instances (None for failed queries)
        """
        max_concurrent = max_concurrent or self.max_concurrent_queries
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def get_page_with_semaphore(page_id: str) -> Optional[T]:
            async with semaphore:
                try:
                    return await self.get_notion_page(page_id, model_class, use_cache)
                except Exception as e:
                    logger.warning(f"Failed to get page {page_id}: {e}")
                    return None
        
        # Execute batch queries
        tasks = [get_page_with_semaphore(page_id) for page_id in page_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return results
        return [result if not isinstance(result, Exception) else None for result in results]
    
    async def invalidate_cache(
        self,
        pattern: Optional[str] = None,
        cache_type: Optional[CacheType] = None
    ) -> int:
        """
        Invalidate cached queries by pattern or type.
        
        Args:
            pattern: Cache key pattern to match
            cache_type: Cache type to invalidate
            
        Returns:
            Number of invalidated entries
        """
        try:
            if pattern:
                # Invalidate by pattern
                return await self.cache_service.delete_pattern(pattern, cache_type)
            elif cache_type:
                # Invalidate entire cache type
                return await self.cache_service.clear(cache_type)
            else:
                # Invalidate all query caches
                return await self.cache_service.delete_pattern("query:*")
                
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get query performance metrics."""
        return {
            "total_queries": self.metrics.total_queries,
            "cached_queries": self.metrics.cached_queries,
            "failed_queries": self.metrics.failed_queries,
            "cache_hit_rate": self.metrics.cache_hit_rate,
            "avg_latency_ms": self.metrics.avg_latency * 1000,
            "notion_queries": self.metrics.notion_queries,
            "mongodb_queries": self.metrics.mongodb_queries,
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses
        }


# Global optimized query service instance
optimized_query_service = OptimizedQueryService()
