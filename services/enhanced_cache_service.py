"""
Enhanced Cache Service for The HigherSelf Network Server.

This module provides a standardized Redis-based caching mechanism featuring:
1. Simple interface for caching data
2. Support for cache invalidation patterns
3. Cache health monitoring
4. Decorator-based automatic caching
"""

import hashlib
import json
import logging
import time
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Dict, Optional, Callable

from services.redis_service import redis_service
from utils.error_handling import ErrorHandler

# Optional metrics - only use if prometheus_client is available
try:
    from prometheus_client import Counter, Gauge, Histogram
    
    CACHE_HITS = Counter(
        'enhanced_cache_hits',
        'Cache hit count',
        ['cache_type']
    )
    CACHE_MISSES = Counter(
        'enhanced_cache_misses',
        'Cache miss count',
        ['cache_type']
    )
    CACHE_SIZE = Gauge(
        'enhanced_cache_size',
        'Current number of items in cache',
        ['cache_type']
    )
    CACHE_LATENCY = Histogram(
        'enhanced_cache_latency',
        'Latency for cache operations in seconds',
        ['operation', 'cache_type']
    )
    CACHE_ERRORS = Counter(
        'enhanced_cache_errors',
        'Cache operation error count',
        ['operation', 'cache_type']
    )
    CACHE_HEALTH = Gauge(
        'enhanced_cache_health',
        default_ttl: int = 300,  # 5 minutes default
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the cache service.

        Args:
            default_ttl: Default TTL for cached items in seconds
            logger: Optional logger instance
        """
        self.default_ttl = default_ttl
        self.logger = logger or logging.getLogger("cache.service")
        self.error_handler = ErrorHandler()

        # Cache TTL mappings for different types
        self.ttl_mappings = {
            CacheType.NOTION: 600,  # 10 minutes
            CacheType.AGENT: 300,  # 5 minutes
            CacheType.VECTOR: 3600,  # 1 hour
            CacheType.API: 300,  # 5 minutes
            CacheType.MCP: 300,  # 5 minutes
            CacheType.WORKFLOW: 600,  # 10 minutes
            CacheType.CONFIG: 1800,  # 30 minutes
            CacheType.USER: 1800,  # 30 minutes
            CacheType.SESSION: 86400,  # 24 hours
        }

        # Maximum size limits for different cache types
        self.max_size_limits = {
            CacheType.NOTION: 1000,
            CacheType.AGENT: 500,
            CacheType.VECTOR: 10000,
            CacheType.API: 1000,
            CacheType.MCP: 1000,
            CacheType.WORKFLOW: 500,
            CacheType.CONFIG: 100,
            CacheType.USER: 5000,
            CacheType.SESSION: 10000,
        }

        try:
            # Test connection
            redis_service.health_check()
            self.logger.info("Cache service initialized with Redis")
            if METRICS_ENABLED:
                CACHE_HEALTH.labels(cache_type="all").set(1)
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis cache: {e}")
            if METRICS_ENABLED:
                CACHE_HEALTH.labels(cache_type="all").set(0)

    def _get_cache_key(self, key: str, cache_type: Optional[CacheType] = None) -> str:
        """
        Generate a namespaced cache key.

        Args:
            key: Original cache key
            cache_type: Type of cache

        Returns:
            Namespaced cache key
        """
        cache_type_value = cache_type.value if cache_type else "general"
        return f"cache:{cache_type_value}:{key}"

    def _get_index_key(self, cache_type: Optional[CacheType] = None) -> str:
        """
        Generate an index key for tracking keys in a cache type.

        Args:
            cache_type: Type of cache

        Returns:
            Index key for the cache type
        """
        cache_type_value = cache_type.value if cache_type else "general"
        return f"cache:index:{cache_type_value}"

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        cache_type: Optional[CacheType] = None,
    ) -> bool:
        """
        Set a value in the cache with optional TTL in seconds.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            cache_type: Type of cache

        Returns:
            bool: True if successful, False otherwise
        """
        start_time = time.time()
        cache_type_value = cache_type.value if cache_type else "general"
        cache_key = self._get_cache_key(key, cache_type)
        index_key = self._get_index_key(cache_type)

        try:
            # Use appropriate TTL
            if ttl is None:
                if cache_type and cache_type in self.ttl_mappings:
                    ttl = self.ttl_mappings[cache_type]
                else:
                    ttl = self.default_ttl

            # Serialize value to JSON
            if isinstance(value, (dict, list, tuple, set, bool)) or value is None:
                serialized = json.dumps(value)
            else:
                serialized = str(value)

            # Add to index for tracking
            await redis_service.async_sadd(index_key, cache_key)

            # Check if we're exceeding max size
            index_size = await redis_service.async_scard(index_key)
            max_size = (
                self.max_size_limits.get(cache_type, 1000) if cache_type else 1000
            )

            if index_size > max_size:
                # Evict oldest entries (10% of max)
                await self._evict_oldest(cache_type, max_size // 10)

            # Store in Redis
            success = await redis_service.async_set(cache_key, serialized, ex=ttl)

            # Update metrics
            if METRICS_ENABLED:
                CACHE_LATENCY.labels(
                    operation="set", cache_type=cache_type_value
                ).observe(time.time() - start_time)

                index_size = await redis_service.async_scard(index_key)
                CACHE_SIZE.labels(cache_type=cache_type_value).set(index_size)

            return bool(success)
        except Exception as e:
            if METRICS_ENABLED:
                CACHE_ERRORS.labels(operation="set", cache_type=cache_type_value).inc()
            self.logger.warning(f"Cache set failed for key {key}: {str(e)}")
            return False

    async def get(
        self, key: str, cache_type: Optional[CacheType] = None, default: Any = None
    ) -> Optional[Any]:
        """
        Get a value from the cache. Returns default if not found.

        Args:
            key: Cache key
            cache_type: Type of cache
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        start_time = time.time()
        cache_type_value = cache_type.value if cache_type else "general"
        cache_key = self._get_cache_key(key, cache_type)

        try:
            # Get from Redis
            value = await redis_service.async_get(cache_key)

            # Update metrics
            if METRICS_ENABLED:
                CACHE_LATENCY.labels(
                    operation="get", cache_type=cache_type_value
                ).observe(time.time() - start_time)

            if value is None:
                if METRICS_ENABLED:
                    CACHE_MISSES.labels(cache_type=cache_type_value).inc()
                return default

            if METRICS_ENABLED:
                CACHE_HITS.labels(cache_type=cache_type_value).inc()

            # Deserialize from JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # If not valid JSON, return as is
                return value
        except Exception as e:
            if METRICS_ENABLED:
                CACHE_ERRORS.labels(operation="get", cache_type=cache_type_value).inc()
            self.logger.warning(f"Cache get failed for key {key}: {str(e)}")
            return default

    async def delete(self, key: str, cache_type: Optional[CacheType] = None) -> bool:
        """
        Delete a specific key from the cache.

        Args:
            key: Cache key
            cache_type: Type of cache

        Returns:
            bool: True if deleted, False otherwise
        """
        start_time = time.time()
        cache_type_value = cache_type.value if cache_type else "general"
        cache_key = self._get_cache_key(key, cache_type)
        index_key = self._get_index_key(cache_type)

        try:
            # Delete key
            result = bool(await redis_service.async_delete(cache_key))

            # Remove from index
            if result:
                await redis_service.async_srem(index_key, cache_key)

            # Update metrics
            if METRICS_ENABLED:
                CACHE_LATENCY.labels(
                    operation="delete", cache_type=cache_type_value
                ).observe(time.time() - start_time)

            return result
        except Exception as e:
            if METRICS_ENABLED:
                CACHE_ERRORS.labels(
                    operation="delete", cache_type=cache_type_value
                ).inc()
            self.logger.warning(f"Cache delete failed for key {key}: {str(e)}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern (e.g., "user:*").

        Args:
            pattern: Pattern to match keys

        Returns:
            int: Number of keys deleted
        """
        start_time = time.time()

        try:
            # Find matching keys
            keys = await redis_service.async_keys(pattern)
            if not keys:
                return 0

            # Delete all matching keys
            deleted = 0
            for key in keys:
                if await redis_service.async_delete(key):
                    deleted += 1

            # Update metrics
            if METRICS_ENABLED:
                CACHE_LATENCY.labels(
                    operation="delete_pattern", cache_type="all"
                ).observe(time.time() - start_time)

            # Remove from indices
            for cache_type in CacheType:
                index_key = self._get_index_key(cache_type)
                for key in keys:
                    await redis_service.async_srem(index_key, key)

            return deleted
        except Exception as e:
            if METRICS_ENABLED:
                CACHE_ERRORS.labels(operation="delete_pattern", cache_type="all").inc()
            self.logger.warning(f"Cache delete_pattern failed: {str(e)}")
            return 0

    async def _evict_oldest(
        self, cache_type: Optional[CacheType] = None, count: int = 10
    ) -> int:
        """
        Evict oldest entries for a cache type based on TTL.

        Args:
            cache_type: Type of cache
            count: Number of entries to evict

        Returns:
            int: Number of entries evicted
        """
        cache_type_value = cache_type.value if cache_type else "general"
        index_key = self._get_index_key(cache_type)

        try:
            # Get keys from the index
            keys = await redis_service.async_smembers(index_key)
            if not keys:
                return 0

            # Track TTL for each key
            key_ttls = []
            for key in keys:
                ttl = await redis_service.async_ttl(key)
                key_ttls.append((key, ttl))

            # Sort by TTL (lowest first)
            key_ttls.sort(key=lambda x: x[1])

            # Delete oldest entries
            deleted = 0
            for key, _ in key_ttls[:count]:
                if await redis_service.async_delete(key):
                    await redis_service.async_srem(index_key, key)
                    deleted += 1

            self.logger.debug(
                f"Evicted {deleted} entries from {cache_type_value} cache"
            )
            return deleted
        except Exception as e:
            self.logger.warning(f"Failed to evict cache entries: {str(e)}")
            return 0

    async def check_health(self) -> bool:
        """
        Check if the cache connection is healthy.

        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            # Check Redis health
            health_check = await redis_service.async_health_check()
            is_healthy = health_check.get("status") == "healthy"

            # Update metrics
            if METRICS_ENABLED:
                CACHE_HEALTH.labels(cache_type="all").set(1 if is_healthy else 0)

            return is_healthy
        except Exception as e:
            self.logger.error(f"Cache health check failed: {str(e)}")
            if METRICS_ENABLED:
                CACHE_HEALTH.labels(cache_type="all").set(0)
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.

        Returns:
            Dict: Cache statistics
        """
        try:
            # Check health
            is_healthy = await self.check_health()

            stats = {
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "types": {},
            }

            # Get stats for each cache type
            for cache_type in CacheType:
                index_key = self._get_index_key(cache_type)
                key_count = await redis_service.async_scard(index_key)

                stats["types"][cache_type.value] = {
                    "count": key_count,
                    "ttl": self.ttl_mappings.get(cache_type, self.default_ttl),
                    "max_size": self.max_size_limits.get(cache_type, 1000),
                }

            return stats
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# Decorator for automatic caching
def cached(
    ttl: Optional[int] = None,
    cache_type: Optional[CacheType] = None,
    key_prefix: Optional[str] = None,
    key_builder: Optional[Callable] = None,
):
    """
    Decorator to automatically cache function results.

    Usage:
    @cached(ttl=300, cache_type=CacheType.API)
    async def get_user(user_id: str) -> dict:
        # Function implementation...

    Args:
        ttl: Time-to-live in seconds
        cache_type: Type of cache
        key_prefix: Prefix for cache key
        key_builder: Function to build custom cache key

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache service
            cache_service_instance = await get_cache_service()

            # Generate a cache key
            if key_builder:
                # Use custom key builder if provided
                key = key_builder(*args, **kwargs)
            else:
                # Default key builder: function name + args hash
                key_parts = [
                    key_prefix or func.__module__ + "." + func.__name__,
                    *[
                        str(arg) for arg in args if not hasattr(arg, "__dict__")
                    ],  # Skip objects
                    *[f"{k}:{v}" for k, v in sorted(kwargs.items())],
                ]
                key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            # Try to get from cache first
            cached_result = await cache_service_instance.get(key, cache_type=cache_type)
            if cached_result is not None:
                return cached_result

            # Execute the function if not cached
            result = await func(*args, **kwargs)

            # Cache the result
            await cache_service_instance.set(
                key, result, ttl=ttl, cache_type=cache_type
            )

            return result

        return wrapper

    return decorator


# Singleton instance
_cache_service = None


async def get_cache_service() -> CacheService:
    """
    Get or create the singleton cache service instance.

    Returns:
        CacheService: The cache service instance
    """
    global _cache_service

    if _cache_service is None:
        _cache_service = CacheService()

    return _cache_service
