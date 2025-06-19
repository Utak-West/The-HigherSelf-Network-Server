"""
Enhanced health check endpoints for The HigherSelf Network Server.
Comprehensive health monitoring for all services and components.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel

from config.settings import settings

# Create router for health endpoints
router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    """Health status model."""
    status: str  # healthy, degraded, unhealthy
    timestamp: str
    response_time_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ServiceHealth(BaseModel):
    """Service health model."""
    service: str
    status: str
    checks: List[HealthStatus]
    overall_response_time_ms: Optional[float] = None


class OverallHealth(BaseModel):
    """Overall system health model."""
    status: str
    timestamp: str
    version: str
    environment: str
    services: Dict[str, ServiceHealth]
    summary: Dict[str, int]


async def check_database_connectivity() -> HealthStatus:
    """Check database connectivity."""
    start_time = time.time()
    
    try:
        # Check MongoDB connectivity
        if settings.integrations.enable_mongodb:
            from services.mongodb_service import mongodb_service
            
            # Perform a simple ping operation
            result = await mongodb_service.ping()
            if result:
                response_time = (time.time() - start_time) * 1000
                return HealthStatus(
                    status="healthy",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=response_time,
                    details={"database": "mongodb", "ping_result": result}
                )
            else:
                return HealthStatus(
                    status="unhealthy",
                    timestamp=datetime.now().isoformat(),
                    error="MongoDB ping failed"
                )
        else:
            return HealthStatus(
                status="disabled",
                timestamp=datetime.now().isoformat(),
                details={"database": "mongodb", "enabled": False}
            )
    
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return HealthStatus(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


async def check_cache_connectivity() -> HealthStatus:
    """Check cache (Redis) connectivity."""
    start_time = time.time()
    
    try:
        if settings.integrations.enable_redis:
            from services.redis_service import redis_service
            
            # Perform Redis health check
            health_result = redis_service.health_check()
            response_time = (time.time() - start_time) * 1000
            
            if health_result.get("status") == "healthy":
                return HealthStatus(
                    status="healthy",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=response_time,
                    details=health_result
                )
            else:
                return HealthStatus(
                    status="unhealthy",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=response_time,
                    error=health_result.get("error", "Redis health check failed")
                )
        else:
            return HealthStatus(
                status="disabled",
                timestamp=datetime.now().isoformat(),
                details={"cache": "redis", "enabled": False}
            )
    
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return HealthStatus(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


async def check_external_services() -> HealthStatus:
    """Check external service connectivity."""
    start_time = time.time()
    external_checks = {}
    
    try:
        # Check Notion API
        if hasattr(settings, 'notion') and settings.notion.api_token:
            try:
                from services.notion_service import notion_service
                notion_health = await notion_service.health_check()
                external_checks["notion"] = notion_health
            except Exception as e:
                external_checks["notion"] = {"status": "unhealthy", "error": str(e)}
        
        # Check OpenAI API
        if hasattr(settings, 'openai') and settings.openai.api_key:
            try:
                from services.openai_service import openai_service
                openai_health = await openai_service.health_check()
                external_checks["openai"] = openai_health
            except Exception as e:
                external_checks["openai"] = {"status": "unhealthy", "error": str(e)}
        
        # Check HuggingFace API
        if hasattr(settings, 'huggingface') and settings.huggingface.api_key:
            try:
                from services.huggingface_service import huggingface_service
                hf_health = await huggingface_service.health_check()
                external_checks["huggingface"] = hf_health
            except Exception as e:
                external_checks["huggingface"] = {"status": "unhealthy", "error": str(e)}
        
        response_time = (time.time() - start_time) * 1000
        
        # Determine overall external services status
        if not external_checks:
            status = "disabled"
        elif all(check.get("status") == "healthy" for check in external_checks.values()):
            status = "healthy"
        elif any(check.get("status") == "healthy" for check in external_checks.values()):
            status = "degraded"
        else:
            status = "unhealthy"
        
        return HealthStatus(
            status=status,
            timestamp=datetime.now().isoformat(),
            response_time_ms=response_time,
            details=external_checks
        )
    
    except Exception as e:
        logger.error(f"External services health check failed: {e}")
        return HealthStatus(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


async def check_business_entities() -> HealthStatus:
    """Check business entity configurations."""
    start_time = time.time()
    
    try:
        entity_checks = {}
        
        # Check The 7 Space configuration
        if getattr(settings, 'THE_7_SPACE_ENABLED', True):
            entity_checks["the_7_space"] = {
                "enabled": True,
                "contact_count": getattr(settings, 'THE_7_SPACE_CONTACT_COUNT', 191),
                "notion_workspace": getattr(settings, 'THE_7_SPACE_NOTION_WORKSPACE', None),
                "status": "configured" if getattr(settings, 'THE_7_SPACE_NOTION_WORKSPACE', None) else "missing_config"
            }
        
        # Check A.M. Consulting configuration
        if getattr(settings, 'AM_CONSULTING_ENABLED', True):
            entity_checks["am_consulting"] = {
                "enabled": True,
                "contact_count": getattr(settings, 'AM_CONSULTING_CONTACT_COUNT', 1300),
                "notion_workspace": getattr(settings, 'AM_CONSULTING_NOTION_WORKSPACE', None),
                "status": "configured" if getattr(settings, 'AM_CONSULTING_NOTION_WORKSPACE', None) else "missing_config"
            }
        
        # Check HigherSelf Core configuration
        if getattr(settings, 'HIGHERSELF_CORE_ENABLED', True):
            entity_checks["higherself_core"] = {
                "enabled": True,
                "contact_count": getattr(settings, 'HIGHERSELF_CORE_CONTACT_COUNT', 1300),
                "notion_workspace": getattr(settings, 'HIGHERSELF_CORE_NOTION_WORKSPACE', None),
                "status": "configured" if getattr(settings, 'HIGHERSELF_CORE_NOTION_WORKSPACE', None) else "missing_config"
            }
        
        response_time = (time.time() - start_time) * 1000
        
        # Determine overall status
        configured_entities = sum(1 for entity in entity_checks.values() if entity["status"] == "configured")
        total_entities = len(entity_checks)
        
        if configured_entities == total_entities:
            status = "healthy"
        elif configured_entities > 0:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return HealthStatus(
            status=status,
            timestamp=datetime.now().isoformat(),
            response_time_ms=response_time,
            details={
                "entities": entity_checks,
                "configured_count": configured_entities,
                "total_count": total_entities
            }
        )
    
    except Exception as e:
        logger.error(f"Business entities health check failed: {e}")
        return HealthStatus(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


@router.get("/", response_model=OverallHealth)
async def overall_health_check(request: Request):
    """
    Comprehensive health check endpoint.
    Returns overall system health with detailed component status.
    """
    start_time = time.time()
    
    # Perform all health checks concurrently
    health_checks = await asyncio.gather(
        check_database_connectivity(),
        check_cache_connectivity(),
        check_external_services(),
        check_business_entities(),
        return_exceptions=True
    )
    
    # Process results
    services = {
        "database": ServiceHealth(
            service="database",
            status=health_checks[0].status if isinstance(health_checks[0], HealthStatus) else "error",
            checks=[health_checks[0] if isinstance(health_checks[0], HealthStatus) else HealthStatus(
                status="error",
                timestamp=datetime.now().isoformat(),
                error=str(health_checks[0])
            )],
            overall_response_time_ms=health_checks[0].response_time_ms if isinstance(health_checks[0], HealthStatus) else None
        ),
        "cache": ServiceHealth(
            service="cache",
            status=health_checks[1].status if isinstance(health_checks[1], HealthStatus) else "error",
            checks=[health_checks[1] if isinstance(health_checks[1], HealthStatus) else HealthStatus(
                status="error",
                timestamp=datetime.now().isoformat(),
                error=str(health_checks[1])
            )],
            overall_response_time_ms=health_checks[1].response_time_ms if isinstance(health_checks[1], HealthStatus) else None
        ),
        "external_services": ServiceHealth(
            service="external_services",
            status=health_checks[2].status if isinstance(health_checks[2], HealthStatus) else "error",
            checks=[health_checks[2] if isinstance(health_checks[2], HealthStatus) else HealthStatus(
                status="error",
                timestamp=datetime.now().isoformat(),
                error=str(health_checks[2])
            )],
            overall_response_time_ms=health_checks[2].response_time_ms if isinstance(health_checks[2], HealthStatus) else None
        ),
        "business_entities": ServiceHealth(
            service="business_entities",
            status=health_checks[3].status if isinstance(health_checks[3], HealthStatus) else "error",
            checks=[health_checks[3] if isinstance(health_checks[3], HealthStatus) else HealthStatus(
                status="error",
                timestamp=datetime.now().isoformat(),
                error=str(health_checks[3])
            )],
            overall_response_time_ms=health_checks[3].response_time_ms if isinstance(health_checks[3], HealthStatus) else None
        )
    }
    
    # Calculate overall status
    service_statuses = [service.status for service in services.values()]
    
    if all(status in ["healthy", "disabled"] for status in service_statuses):
        overall_status = "healthy"
    elif any(status == "unhealthy" for status in service_statuses):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"
    
    # Calculate summary
    summary = {
        "healthy": sum(1 for status in service_statuses if status == "healthy"),
        "degraded": sum(1 for status in service_statuses if status == "degraded"),
        "unhealthy": sum(1 for status in service_statuses if status == "unhealthy"),
        "disabled": sum(1 for status in service_statuses if status == "disabled"),
        "error": sum(1 for status in service_statuses if status == "error")
    }
    
    return OverallHealth(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        version=getattr(settings, 'version', '1.0.0'),
        environment=getattr(settings, 'environment', 'development'),
        services=services,
        summary=summary
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe endpoint.
    Returns 200 if the application is ready to serve requests.
    """
    try:
        # Check critical dependencies
        critical_checks = await asyncio.gather(
            check_database_connectivity(),
            check_cache_connectivity(),
            return_exceptions=True
        )
        
        # If any critical service is unhealthy, we're not ready
        for check in critical_checks:
            if isinstance(check, HealthStatus) and check.status == "unhealthy":
                raise HTTPException(status_code=503, detail="Service not ready")
            elif not isinstance(check, HealthStatus):
                raise HTTPException(status_code=503, detail="Health check failed")
        
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check():
    """
    Liveness probe endpoint.
    Returns 200 if the application is alive (basic functionality works).
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time() - getattr(liveness_check, 'start_time', time.time())
    }


@router.get("/database")
async def database_health():
    """Database-specific health check."""
    health = await check_database_connectivity()
    
    if health.status == "unhealthy":
        raise HTTPException(status_code=503, detail=health.error)
    
    return health


@router.get("/external")
async def external_services_health():
    """External services health check."""
    health = await check_external_services()
    
    if health.status == "unhealthy":
        raise HTTPException(status_code=503, detail=health.error)
    
    return health


@router.get("/entities")
async def business_entities_health():
    """Business entities configuration health check."""
    health = await check_business_entities()
    
    if health.status == "unhealthy":
        raise HTTPException(status_code=503, detail=health.error)
    
    return health


# Initialize start time for uptime calculation
liveness_check.start_time = time.time()
