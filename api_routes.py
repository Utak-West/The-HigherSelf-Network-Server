"""
API routes for The HigherSelf Network Server.
This module defines the FastAPI routes for the server.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger

from config.settings import settings
from services.redis_service import redis_service

# Create router
router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to The HigherSelf Network Server API",
        "version": "1.0.0",
        "status": "running",
    }


@router.get("/health")
async def health_check():
    """Health check endpoint with detailed component status."""
    health_status = {"status": "healthy", "components": {}}

    # Check Redis health if enabled
    if settings.integrations.enable_redis:
        try:
            redis_health = redis_service.health_check()
            health_status["components"]["redis"] = redis_health

            # If Redis is unhealthy, mark the overall status as degraded
            if redis_health["status"] != "healthy":
                health_status["status"] = "degraded"
                health_status["message"] = "Redis service is unhealthy"
        except Exception as e:
            health_status["components"]["redis"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["status"] = "degraded"
            health_status["message"] = "Redis service check failed"

    return health_status


@router.get("/redis/metrics")
async def redis_metrics():
    """Get Redis metrics."""
    if not settings.integrations.enable_redis:
        raise HTTPException(status_code=404, detail="Redis is not enabled")

    try:
        metrics = redis_service.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get Redis metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get Redis metrics: {str(e)}"
        )


@router.post("/redis/flush")
async def redis_flush():
    """Flush all Redis data (for testing/development only)."""
    if not settings.debug:
        raise HTTPException(
            status_code=403, detail="This endpoint is only available in debug mode"
        )

    if not settings.integrations.enable_redis:
        raise HTTPException(status_code=404, detail="Redis is not enabled")

    try:
        # Use with caution - this will delete all data in Redis
        result = redis_service._sync_client.flushdb()
        return {
            "status": "success",
            "message": "Redis database flushed",
            "result": result,
        }
    except Exception as e:
        logger.error(f"Failed to flush Redis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to flush Redis: {str(e)}")
