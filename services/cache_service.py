"""
Cache Service for Higher Self Network Server.
Implements a multi-level caching strategy using Redis.
"""

import json
import hashlib
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum
from functools import wraps
from loguru import logger
from datetime import datetime, timedelta

from services.redis_service import redis_service
from prometheus_client import Counter, Histogram, Gauge

# Metrics for monitoring cache performance
CACHE_HITS = Counter(
    'cache_hits_total',
    'Cache hit count',
    ['cache_level', 'cache_type']
)
CACHE_MISSES = Counter(
    'cache_misses_total',
    'Cache miss count',
    ['cache_level', 'cache_type']
)
CACHE_SIZE = Gauge(
    'cache_size',
    'Current number of items in cache',
    ['cache_level', 'cache_type']
)
CACHE_LATENCY = Histogram(
    'cache_operation_latency_seconds',
    'Latency for cache operations in seconds',
    ['operation', 'cache_level', 'cache_type']
)


class CacheLevel(Enum):
    """Cache levels with different TTL values."""
    L1 = "l1"  # Very hot data
    L2 = "l2"  # Warm data
    L3 = "l3"  # Cold data
    PERMANENT = "permanent"  # Long-term data


class CacheType(Enum):
    """Types of cached data."""
    NOTION = "notion"  # Notion database results
    AGENT = "agent"    # Agent state and context
    VECTOR = "vector"  # Vector embeddings
    API = "api"        # External API results
    MCP = "mcp"        # MCP tool results
    WORKFLOW = "workflow"  # Workflow state and context


class MultiLevelCache:
    """
    Multi-level caching strategy implementation using Redis.
    
    Provides different cache levels with varying TTLs:
    - L1: Very hot data, 60s TTL
    - L2: Warm data, 5m TTL
    - L3: Cold data, 1h TTL
    - Permanent: Long-term data, 24h TTL
    
    Also supports cache namespaces for different types of data.
    """
    
    def __init__(self):
        """Initialize the cache with TTL values for each level."""
        self.ttl_map = {
            CacheLevel.L1: 60,  # 1 minute
            CacheLevel.L2: 300,  # 5 minutes
            CacheLevel.L3: 3600,  # 1 hour
            CacheLevel.PERMANENT: 86400,  # 24 hours
        }
        
        # Default TTLs by cache type
        self.default_level_map = {
            CacheType.NOTION: CacheLevel.L2,
            CacheType.AGENT: CacheLevel.L1,
            CacheType.VECTOR: CacheLevel.L3,
            CacheType.API: CacheLevel.L2,
            CacheType.MCP: CacheLevel.L2,
            CacheType.WORKFLOW: CacheLevel.L2,
        }
        
        # Max size per cache type (to prevent memory issues)
        self.max_size_map = {
            CacheType.NOTION: 1000,
            CacheType.AGENT: 500,
            CacheType.VECTOR: 10000,
            CacheType.API: 1000,
            CacheType.MCP: 2000,
            CacheType.WORKFLOW: 500,
        }
        
        logger.info("Multi-level cache initialized")
    
    def _get_key(self, key: str, cache_type: CacheType) -> str:
        """
        Generate a namespaced cache key.
        
        Args:
            key: The base cache key
            cache_type: The type of cache
            
        Returns:
            Namespaced cache key
        """
        return f"cache:{cache_type.value}:{key}"
    
    def _get_index_key(self, cache_type: CacheType, cache_level: CacheLevel) -> str:
        """
        Generate a key for the cache index (keeping track of all keys in a level).
        
        Args:
            cache_type: The type of cache
            cache_level: The cache level
            
        Returns:
            Cache index key
        """
        return f"cache:index:{cache_type.value}:{cache_level.value}"
    
    async def get(
        self, 
        key: str, 
        cache_type: CacheType, 
        cache_level: Optional[CacheLevel] = None,
        as_json: bool = True
    ) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            cache_type: The type of cache
            cache_level: Optional cache level to override default
            as_json: Whether to parse the result as JSON
            
        Returns:
            The cached value or None if not found
        """
        start_time = time.time()
        
        level = cache_level or self.default_level_map.get(cache_type, CacheLevel.L2)
        cache_key = self._get_key(key, cache_type)
        
        try:
            # Try to get from cache
            cached_value = await redis_service.async_get(cache_key, as_json=as_json)
            
            # Record metrics
            duration = time.time() - start_time
            CACHE_LATENCY.labels(
                operation="get",
                cache_level=level.value,
                cache_type=cache_type.value
            ).observe(duration)
            
            if cached_value is not None:
                CACHE_HITS.labels(
                    cache_level=level.value,
                    cache_type=cache_type.value
                ).inc()
                return cached_value
                
            CACHE_MISSES.labels(
                cache_level=level.value,
                cache_type=cache_type.value
            ).inc()
            return None
        except Exception as e:
            logger.warning(f"Error getting from cache: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        cache_type: CacheType,
        cache_level: Optional[CacheLevel] = None,
        ttl_override: Optional[int] = None
    ) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to store
            cache_type: The type of cache
            cache_level: Optional cache level to override default
            ttl_override: Optional TTL in seconds to override the level's default TTL
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        level = cache_level or self.default_level_map.get(cache_type, CacheLevel.L2)
        cache_key = self._get_key(key, cache_type)
        index_key = self._get_index_key(cache_type, level)
        
        try:
            # Set the TTL based on cache level or override
            ttl = ttl_override if ttl_override is not None else self.ttl_map.get(level, 300)
            
            # Handle max size
            max_size = self.max_size_map.get(cache_type, 1000)
            
            # Maintain the cache index
            await redis_service.async_sadd(index_key, cache_key)
            
            # Check cache size and possibly evict
            index_size = await redis_service.async_scard(index_key)
            if index_size > max_size:
                await self._evict_oldest(index_key, max_size // 10)  # Evict 10% of the cache
            
            # Store in Redis
            success = await redis_service.async_set(cache_key, value, ex=ttl)
            
            # Record metrics
            duration = time.time() - start_time
            CACHE_LATENCY.labels(
                operation="set",
                cache_level=level.value,
                cache_type=cache_type.value
            ).observe(duration)
            
            # Update cache size metric
            index_size = await redis_service.async_scard(index_key)
            CACHE_SIZE.labels(
                cache_level=level.value,
                cache_type=cache_type.value
            ).set(index_size)
            
            return success
        except Exception as e:
            logger.warning(f"Error setting cache: {e}")
            return False
    
    async def delete(self, key: str, cache_type: CacheType) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            cache_type: The type of cache
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        cache_key = self._get_key(key, cache_type)
        
        try:
            # Delete from Redis
            success = await redis_service.async_delete(cache_key) > 0
            
            # Record metrics
            duration = time.time() - start_time
            CACHE_LATENCY.labels(
                operation="delete",
                cache_level="any",
                cache_type=cache_type.value
            ).observe(duration)
            
            # Remove from indices
            for level in CacheLevel:
                index_key = self._get_index_key(cache_type, level)
                await redis_service.async_srem(index_key, cache_key)
            
            return success
        except Exception as e:
            logger.warning(f"Error deleting from cache: {e}")
            return False
    
    async def exists(self, key: str, cache_type: CacheType) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: The cache key
            cache_type: The type of cache
            
        Returns:
            True if key exists, False otherwise
        """
        start_time = time.time()
        
        cache_key = self._get_key(key, cache_type)
        
        try:
            # Check if key exists in Redis
            result = await redis_service.async_exists(cache_key)
            
            # Record metrics
            duration = time.time() - start_time
            CACHE_LATENCY.labels(
                operation="exists",
                cache_level="any",
                cache_type=cache_type.value
            ).observe(duration)
            
            return result
        except Exception as e:
            logger.warning(f"Error checking cache existence: {e}")
            return False
    
    async def clear_type(self, cache_type: CacheType) -> int:
        """
        Clear all keys for a specific cache type.
        
        Args:
            cache_type: The type of cache to clear
            
        Returns:
            Number of keys cleared
        """
        start_time = time.time()
        
        try:
            # Get keys pattern
            pattern = f"cache:{cache_type.value}:*"
            
            # Find matching keys
            keys = await redis_service.async_keys(pattern)
            
            # Delete all matching keys
            count = 0
            for key in keys:
                await redis_service.async_delete(key)
                count += 1
            
            # Clear indices
            for level in CacheLevel:
                index_key = self._get_index_key(cache_type, level)
                await redis_service.async_delete(index_key)
            
            # Record metrics
            duration = time.time() - start_time
            CACHE_LATENCY.labels(
                operation="clear_type",
                cache_level="all",
                cache_type=cache_type.value
            ).observe(duration)
            
            # Update cache size metric
            for level in CacheLevel:
                CACHE_SIZE.labels(
                    cache_level=level.value,
                    cache_type=cache_type.value
                ).set(0)
            
            return count
        except Exception as e:
            logger.warning(f"Error clearing cache type {cache_type.value}: {e}")
            return 0
    
    async def _evict_oldest(self, index_key: str, count: int) -> int:
        """
        Evict the oldest entries from a cache level.
        
        Args:
            index_key: The cache index key
            count: Number of entries to evict
            
        Returns:
            Number of entries evicted
        """
        try:
            # Get all keys in the index
            all_keys = await redis_service.async_smembers(index_key)
            
            # Get TTLs for each key to find the ones expiring soonest
            key_ttls = []
            for key in all_keys:
                ttl = await redis_service.async_ttl(key)
                key_ttls.append((key, ttl))
            
            # Sort by TTL (ascending)
            key_ttls.sort(key=lambda x: x[1])
            
            # Evict the oldest (those with lowest TTL)
            evicted = 0
            for key, _ in key_ttls[:count]:
                await redis_service.async_delete(key)
                await redis_service.async_srem(index_key, key)
                evicted += 1
            
            return evicted
        except Exception as e:
            logger.warning(f"Error evicting cache entries: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "levels": {},
            "types": {}
        }
        
        try:
            # Gather stats by level
            for level in CacheLevel:
                level_stats = {
                    "ttl": self.ttl_map.get(level, 0),
                    "types": {}
                }
                
                for cache_type in CacheType:
                    index_key = self._get_index_key(cache_type, level)
                    count = await redis_service.async_scard(index_key)
                    level_stats["types"][cache_type.value] = count
                
                stats["levels"][level.value] = level_stats
            
            # Gather stats by type
            for cache_type in CacheType:
                type_stats = {
                    "default_level": self.default_level_map.get(cache_type, CacheLevel.L2).value,
                    "max_size": self.max_size_map.get(cache_type, 1000),
                    "levels": {}
                }
                
                for level in CacheLevel:
                    index_key = self._get_index_key(cache_type, level)
                    count = await redis_service.async_scard(index_key)
                    type_stats["levels"][level.value] = count
                
                stats["types"][cache_type.value] = type_stats
            
            return stats
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {
                "error": str(e),
                "levels": {},
                "types": {}
            }


def cached(
    cache_type: CacheType, 
    cache_level: Optional[CacheLevel] = None,
    ttl_override: Optional[int] = None,
    key_builder: Optional[Callable] = None
):
    """
    Decorator to cache function results.
    
    Args:
        cache_type: The type of cache
        cache_level: Optional cache level override
        ttl_override: Optional TTL override
        key_builder: Optional function to build the cache key from the function arguments
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                # Default key builder: function name + args hash
                key_parts = [func.__name__]
                
                # Add positional args
                for arg in args:
                    if hasattr(arg, '__dict__'):
                        # For complex objects, use their dict representation
                        key_parts.append(str(arg.__dict__))
                    else:
                        # For simple types
                        key_parts.append(str(arg))
                
                # Add kwargs
                for k, v in sorted(kwargs.items()):
                    if hasattr(v, '__dict__'):
                        key_parts.append(f"{k}:{str(v.__dict__)}")
                    else:
                        key_parts.append(f"{k}:{str(v)}")
                
                # Create a hash
                key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = await multi_level_cache.get(key, cache_type, cache_level)
            if cached_result is not None:
                return cached_result
            
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Cache the result
            await multi_level_cache.set(
                key, result, cache_type, cache_level, ttl_override
            )
            
            return result
        return wrapper
    return decorator


# Create a singleton instance
multi_level_cache = MultiLevelCache()
