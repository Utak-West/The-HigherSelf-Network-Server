"""
Redis Health Monitoring API Routes for HigherSelf Network Server.

This module provides comprehensive Redis health monitoring endpoints
for operational visibility and troubleshooting.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from loguru import logger
from pydantic import BaseModel

from services.redis_service import redis_service
from config.settings import settings


# Create router for Redis health endpoints
router = APIRouter(prefix="/redis", tags=["Redis Health"])


class RedisHealthResponse(BaseModel):
    """Redis health check response model."""
    status: str
    timestamp: datetime
    latency_ms: Optional[float] = None
    connection_info: Dict[str, Any]
    errors: List[str] = []


class RedisMetricsResponse(BaseModel):
    """Redis metrics response model."""
    operations: int
    errors: int
    avg_latency_ms: float
    health_status: str
    redis_info: Dict[str, Any]
    connection_pool_info: Dict[str, Any]


class RedisConfigResponse(BaseModel):
    """Redis configuration response model."""
    connection_settings: Dict[str, Any]
    feature_flags: Dict[str, bool]
    performance_settings: Dict[str, Any]


@router.get("/health", response_model=RedisHealthResponse)
async def get_redis_health():
    """
    Get comprehensive Redis health status.
    
    Returns detailed information about Redis connectivity,
    performance, and operational status.
    """
    try:
        # Perform health check
        health_status = redis_service.health_check()
        
        # Get connection info
        connection_info = {
            "host": settings.redis.host,
            "port": settings.redis.port,
            "database": settings.redis.database,
            "ssl_enabled": settings.redis.ssl_enabled,
            "max_connections": settings.redis.max_connections,
            "timeout": settings.redis.timeout
        }
        
        # Convert latency to milliseconds if available
        latency_ms = None
        if "latency" in health_status:
            latency_ms = health_status["latency"] * 1000
        
        return RedisHealthResponse(
            status=health_status["status"],
            timestamp=datetime.now(),
            latency_ms=latency_ms,
            connection_info=connection_info,
            errors=health_status.get("errors", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to get Redis health status: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Redis health check failed: {str(e)}"
        )


@router.get("/health/async", response_model=RedisHealthResponse)
async def get_redis_health_async():
    """
    Get Redis health status using async client.
    
    Provides health check using the asynchronous Redis client
    for better performance in async contexts.
    """
    try:
        # Perform async health check
        health_status = await redis_service.async_health_check()
        
        # Get connection info
        connection_info = {
            "host": settings.redis.host,
            "port": settings.redis.port,
            "database": settings.redis.database,
            "ssl_enabled": settings.redis.ssl_enabled,
            "max_connections": settings.redis.max_connections,
            "timeout": settings.redis.timeout,
            "client_type": "async"
        }
        
        # Convert latency to milliseconds if available
        latency_ms = None
        if "latency" in health_status:
            latency_ms = health_status["latency"] * 1000
        
        return RedisHealthResponse(
            status=health_status["status"],
            timestamp=datetime.now(),
            latency_ms=latency_ms,
            connection_info=connection_info,
            errors=health_status.get("errors", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to get async Redis health status: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Async Redis health check failed: {str(e)}"
        )


@router.get("/metrics", response_model=RedisMetricsResponse)
async def get_redis_metrics():
    """
    Get comprehensive Redis performance metrics.
    
    Returns detailed metrics about Redis operations,
    performance, and server information.
    """
    try:
        # Get metrics from Redis service
        metrics = redis_service.get_metrics()
        
        # Convert latency to milliseconds
        avg_latency_ms = metrics.get("avg_latency", 0) * 1000
        
        # Get connection pool information
        connection_pool_info = {
            "max_connections": settings.redis.max_connections,
            "current_connections": "N/A",  # Would need pool inspection
            "connection_pool_class": str(type(redis_service._connection_pool))
        }
        
        return RedisMetricsResponse(
            operations=metrics.get("operations", 0),
            errors=metrics.get("errors", 0),
            avg_latency_ms=avg_latency_ms,
            health_status=metrics.get("health", {}).get("status", "unknown"),
            redis_info=metrics.get("redis_info", {}),
            connection_pool_info=connection_pool_info
        )
        
    except Exception as e:
        logger.error(f"Failed to get Redis metrics: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Redis metrics collection failed: {str(e)}"
        )


@router.get("/config", response_model=RedisConfigResponse)
async def get_redis_config():
    """
    Get Redis configuration information.
    
    Returns current Redis configuration settings,
    feature flags, and performance parameters.
    """
    try:
        # Get connection settings (without sensitive data)
        connection_settings = {
            "host": settings.redis.host,
            "port": settings.redis.port,
            "database": settings.redis.database,
            "ssl_enabled": settings.redis.ssl_enabled,
            "username": settings.redis.username,
            "password_configured": bool(settings.redis.password),
            "connection_url_configured": bool(settings.redis.uri)
        }
        
        # Get feature flags
        feature_flags = {
            "cache_enabled": settings.redis.cache_enabled,
            "pubsub_enabled": settings.redis.pubsub_enabled,
            "session_store_enabled": settings.redis.session_store_enabled,
            "rate_limiting_enabled": settings.redis.rate_limiting_enabled,
            "metrics_enabled": settings.redis.metrics_enabled
        }
        
        # Get performance settings
        performance_settings = {
            "max_connections": settings.redis.max_connections,
            "timeout": settings.redis.timeout,
            "socket_connect_timeout": settings.redis.socket_connect_timeout,
            "socket_timeout": settings.redis.socket_timeout,
            "health_check_interval": settings.redis.health_check_interval,
            "retry_on_timeout": settings.redis.retry_on_timeout,
            "retry_on_error": settings.redis.retry_on_error,
            "max_retries": settings.redis.max_retries,
            "retry_delay": settings.redis.retry_delay,
            "slow_query_threshold": settings.redis.slow_query_threshold
        }
        
        return RedisConfigResponse(
            connection_settings=connection_settings,
            feature_flags=feature_flags,
            performance_settings=performance_settings
        )
        
    except Exception as e:
        logger.error(f"Failed to get Redis configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Redis configuration retrieval failed: {str(e)}"
        )


@router.post("/test-connection")
async def test_redis_connection():
    """
    Test Redis connection with a simple operation.
    
    Performs a basic set/get/delete operation to verify
    Redis connectivity and basic functionality.
    """
    try:
        test_key = "higherself:health:test"
        test_value = f"test_{datetime.now().isoformat()}"
        
        # Test synchronous operations
        redis_service.set(test_key, test_value, ex=60)
        retrieved_value = redis_service.get(test_key)
        redis_service.delete(test_key)
        
        # Verify operation
        if retrieved_value != test_value:
            raise Exception("Value mismatch in test operation")
        
        return {
            "status": "success",
            "message": "Redis connection test passed",
            "test_performed": "set/get/delete operation",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Redis connection test failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Redis connection test failed: {str(e)}"
        )


@router.post("/test-async-connection")
async def test_redis_async_connection():
    """
    Test Redis async connection with a simple operation.
    
    Performs a basic async set/get/delete operation to verify
    async Redis connectivity and functionality.
    """
    try:
        test_key = "higherself:health:async_test"
        test_value = f"async_test_{datetime.now().isoformat()}"
        
        # Test asynchronous operations
        await redis_service.async_set(test_key, test_value, ex=60)
        retrieved_value = await redis_service.async_get(test_key)
        await redis_service.async_delete(test_key)
        
        # Verify operation
        if retrieved_value != test_value:
            raise Exception("Value mismatch in async test operation")
        
        return {
            "status": "success",
            "message": "Redis async connection test passed",
            "test_performed": "async set/get/delete operation",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Redis async connection test failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Redis async connection test failed: {str(e)}"
        )


@router.get("/info/{section}")
async def get_redis_info(
    section: str = Query(..., description="Redis INFO section (e.g., server, memory, stats)")
):
    """
    Get specific Redis INFO section.
    
    Retrieves detailed information from Redis INFO command
    for specific sections like server, memory, stats, etc.
    """
    try:
        # Get Redis info
        if hasattr(redis_service._sync_client, 'info'):
            info = redis_service._sync_client.info(section)
        else:
            raise Exception("Redis client not available")
        
        return {
            "section": section,
            "info": info,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to get Redis info for section '{section}': {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Redis info retrieval failed: {str(e)}"
        )


@router.get("/keys/pattern/{pattern}")
async def get_redis_keys_by_pattern(
    pattern: str,
    limit: int = Query(100, description="Maximum number of keys to return")
):
    """
    Get Redis keys matching a pattern.
    
    WARNING: Use with caution in production as KEYS command
    can be expensive on large datasets.
    """
    try:
        # Get keys matching pattern (limited for safety)
        if hasattr(redis_service._sync_client, 'scan_iter'):
            keys = list(redis_service._sync_client.scan_iter(
                match=pattern, 
                count=limit
            ))[:limit]
        else:
            raise Exception("Redis client not available")
        
        return {
            "pattern": pattern,
            "keys": keys,
            "count": len(keys),
            "limit": limit,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to get Redis keys for pattern '{pattern}': {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Redis keys retrieval failed: {str(e)}"
        )
