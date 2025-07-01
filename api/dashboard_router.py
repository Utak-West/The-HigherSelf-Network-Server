"""
Dashboard API Router for HigherSelf Operations Dashboard
Integrates with existing FastAPI server to provide dashboard endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
import asyncio
import logging
from datetime import datetime, timedelta

from models.base import ApiPlatform
from services.redis_service import RedisService
from services.mongodb_service import MongoDBService
from utils.auth import get_current_user
from utils.error_handling import handle_api_error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Initialize services
redis_service = RedisService()
mongodb_service = MongoDBService()


@router.get("/health")
async def dashboard_health():
    """Health check for dashboard services"""
    try:
        # Check Redis connection
        redis_status = await redis_service.ping()
        
        # Check MongoDB connection
        mongo_status = await mongodb_service.health_check()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "redis": "connected" if redis_status else "disconnected",
                "mongodb": "connected" if mongo_status else "disconnected"
            }
        }
    except Exception as e:
        logger.error(f"Dashboard health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dashboard services unavailable"
        )


@router.get("/metrics")
async def get_dashboard_metrics(current_user: dict = Depends(get_current_user)):
    """Get real-time dashboard metrics"""
    try:
        # Get system metrics
        system_metrics = await _get_system_metrics()
        
        # Get agent metrics
        agent_metrics = await _get_agent_metrics()
        
        # Get business metrics
        business_metrics = await _get_business_metrics()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": system_metrics,
            "agents": agent_metrics,
            "business": business_metrics
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        return handle_api_error(e)


@router.get("/organizations")
async def get_organizations(current_user: dict = Depends(get_current_user)):
    """Get available organizations for multi-tenant dashboard"""
    try:
        organizations = [
            {
                "id": "am-consulting",
                "name": "A.M. Consulting",
                "description": "Conflict management and practitioner services",
                "color": "#31B2E0",
                "active": True
            },
            {
                "id": "seven-space",
                "name": "The 7 Space",
                "description": "Exhibitions, events, and wellness programs",
                "color": "#00ff88",
                "active": True
            },
            {
                "id": "higherself-network",
                "name": "HigherSelf Network",
                "description": "Community management and platform services",
                "color": "#8a2be2",
                "active": True
            }
        ]
        
        return {"organizations": organizations}
    except Exception as e:
        logger.error(f"Failed to get organizations: {e}")
        return handle_api_error(e)


@router.get("/agents")
async def get_agents_status(current_user: dict = Depends(get_current_user)):
    """Get status of all AI agents"""
    try:
        # Get agent data from MongoDB
        agents_collection = mongodb_service.get_collection("agents")
        agents = await agents_collection.find({}).to_list(length=None)
        
        # Enhance with real-time status
        enhanced_agents = []
        for agent in agents:
            agent_status = await _get_agent_real_time_status(agent.get("name", ""))
            enhanced_agents.append({
                **agent,
                "real_time_status": agent_status
            })
        
        return {"agents": enhanced_agents}
    except Exception as e:
        logger.error(f"Failed to get agents status: {e}")
        return handle_api_error(e)


async def _get_system_metrics() -> Dict[str, Any]:
    """Get system-level metrics"""
    try:
        # Get from Redis cache if available
        cached_metrics = await redis_service.get("dashboard:system_metrics")
        if cached_metrics:
            return cached_metrics
        
        # Calculate fresh metrics
        metrics = {
            "cpu_usage": 45.2,  # Mock data - replace with actual system monitoring
            "memory_usage": 67.8,
            "disk_usage": 34.5,
            "network_io": {
                "bytes_sent": 1024000,
                "bytes_received": 2048000
            },
            "active_connections": 156,
            "uptime": "7d 14h 32m"
        }
        
        # Cache for 30 seconds
        await redis_service.setex("dashboard:system_metrics", 30, metrics)
        return metrics
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {}


async def _get_agent_metrics() -> Dict[str, Any]:
    """Get agent performance metrics"""
    try:
        # Mock agent metrics - replace with actual agent monitoring
        metrics = {
            "total_agents": 9,
            "active_agents": 8,
            "tasks_completed_today": 247,
            "average_response_time": 1.2,
            "success_rate": 94.7,
            "top_performers": [
                {"name": "Grace Fields", "score": 98.5},
                {"name": "Nyra", "score": 96.2},
                {"name": "Booking Agent", "score": 94.8}
            ]
        }
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to get agent metrics: {e}")
        return {}


async def _get_business_metrics() -> Dict[str, Any]:
    """Get business-level metrics"""
    try:
        # Mock business metrics - replace with actual business data
        metrics = {
            "revenue": {
                "today": 12450.00,
                "this_month": 345600.00,
                "growth_rate": 15.3
            },
            "customers": {
                "total": 1247,
                "new_today": 23,
                "retention_rate": 87.5
            },
            "bookings": {
                "today": 34,
                "this_week": 189,
                "completion_rate": 92.1
            }
        }
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to get business metrics: {e}")
        return {}


async def _get_agent_real_time_status(agent_name: str) -> Dict[str, Any]:
    """Get real-time status for a specific agent"""
    try:
        # Check Redis for agent status
        status_key = f"agent:status:{agent_name.lower().replace(' ', '_')}"
        status = await redis_service.get(status_key)
        
        if not status:
            # Default status if not found
            status = {
                "online": True,
                "last_activity": datetime.utcnow().isoformat(),
                "current_task": None,
                "performance_score": 85.0
            }
        
        return status
    except Exception as e:
        logger.error(f"Failed to get agent status for {agent_name}: {e}")
        return {"online": False, "error": str(e)}


@router.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket.accept()
    try:
        while True:
            # Send real-time updates every 5 seconds
            metrics = await get_dashboard_metrics()
            await websocket.send_json(metrics)
            await asyncio.sleep(5)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()
