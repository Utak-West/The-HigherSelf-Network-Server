"""
Optimization Integration Service for HigherSelf Network Server.

This module provides a centralized way to initialize, configure, and manage
all performance optimizations implemented in the server.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from loguru import logger
from fastapi import FastAPI

# Import all optimization services
from services.enhanced_cache_service import CacheService, CacheType
from services.optimized_query_service import OptimizedQueryService
from services.performance_monitoring_service import PerformanceMonitoringService
from services.optimized_agent_communication import OptimizedAgentCommunication
from services.async_optimization_service import AsyncOptimizationService
from api.middleware.response_optimization import create_response_optimization_middleware


class OptimizationManager:
    """
    Central manager for all performance optimizations.
    
    Provides unified initialization, configuration, and monitoring
    of all optimization services.
    """
    
    def __init__(self):
        # Initialize all optimization services
        self.cache_service = CacheService()
        self.query_service = OptimizedQueryService()
        self.performance_monitor = PerformanceMonitoringService()
        self.agent_communication = OptimizedAgentCommunication()
        self.async_optimizer = AsyncOptimizationService()
        
        # Track initialization status
        self.initialized = False
        self.startup_time: Optional[datetime] = None
        
        # Service health status
        self.service_health: Dict[str, bool] = {
            "cache_service": False,
            "query_service": False,
            "performance_monitor": False,
            "agent_communication": False,
            "async_optimizer": False
        }
    
    async def initialize(self) -> bool:
        """
        Initialize all optimization services.
        
        Returns:
            True if all services initialized successfully, False otherwise
        """
        if self.initialized:
            logger.warning("Optimization services already initialized")
            return True
        
        logger.info("Initializing HigherSelf Network Server optimizations...")
        self.startup_time = datetime.now()
        
        try:
            # Initialize services in order of dependency
            
            # 1. Performance monitoring (needed for metrics collection)
            logger.info("Starting performance monitoring service...")
            await self.performance_monitor.start_monitoring()
            self.service_health["performance_monitor"] = True
            
            # 2. Async optimization (needed for connection pooling)
            logger.info("Starting async optimization service...")
            await self.async_optimizer.start()
            self.service_health["async_optimizer"] = True
            
            # 3. Cache service (depends on Redis)
            logger.info("Initializing enhanced cache service...")
            cache_health = await self.cache_service.check_health()
            self.service_health["cache_service"] = cache_health
            if not cache_health:
                logger.warning("Cache service health check failed, but continuing...")
            
            # 4. Query service (depends on cache service)
            logger.info("Initializing optimized query service...")
            # Query service doesn't need explicit initialization
            self.service_health["query_service"] = True
            
            # 5. Agent communication (depends on Redis)
            logger.info("Starting agent communication service...")
            await self.agent_communication.start()
            self.service_health["agent_communication"] = True
            
            self.initialized = True
            
            # Log initialization summary
            healthy_services = sum(self.service_health.values())
            total_services = len(self.service_health)
            
            logger.info(
                f"Optimization services initialized: {healthy_services}/{total_services} healthy"
            )
            
            # Record initialization metrics
            self.performance_monitor.record_metric(
                "optimization_services_initialized",
                healthy_services,
                {"total_services": str(total_services)}
            )
            
            return healthy_services == total_services
            
        except Exception as e:
            logger.error(f"Failed to initialize optimization services: {e}")
            self.initialized = False
            return False
    
    async def shutdown(self) -> bool:
        """
        Shutdown all optimization services gracefully.
        
        Returns:
            True if all services shutdown successfully, False otherwise
        """
        if not self.initialized:
            logger.warning("Optimization services not initialized, nothing to shutdown")
            return True
        
        logger.info("Shutting down HigherSelf Network Server optimizations...")
        
        shutdown_success = True
        
        try:
            # Shutdown services in reverse order
            
            # 1. Agent communication
            logger.info("Stopping agent communication service...")
            await self.agent_communication.stop()
            
            # 2. Async optimization
            logger.info("Stopping async optimization service...")
            await self.async_optimizer.stop()
            
            # 3. Performance monitoring (last, to capture shutdown metrics)
            logger.info("Stopping performance monitoring service...")
            await self.performance_monitor.stop_monitoring()
            
            # Reset status
            self.initialized = False
            for service in self.service_health:
                self.service_health[service] = False
            
            logger.info("All optimization services shutdown successfully")
            
        except Exception as e:
            logger.error(f"Error during optimization services shutdown: {e}")
            shutdown_success = False
        
        return shutdown_success
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of all optimization services.
        
        Returns:
            Dictionary containing health status of all services
        """
        health_status = {
            "overall_status": "unknown",
            "initialized": self.initialized,
            "startup_time": self.startup_time.isoformat() if self.startup_time else None,
            "services": {},
            "metrics": {},
            "timestamp": datetime.now().isoformat()
        }
        
        if not self.initialized:
            health_status["overall_status"] = "not_initialized"
            return health_status
        
        try:
            # Check individual service health
            health_status["services"]["cache_service"] = await self.cache_service.check_health()
            health_status["services"]["performance_monitor"] = True  # Always healthy if running
            health_status["services"]["agent_communication"] = True  # Always healthy if running
            health_status["services"]["async_optimizer"] = True  # Always healthy if running
            health_status["services"]["query_service"] = True  # Always healthy if running
            
            # Get service metrics
            health_status["metrics"]["cache_stats"] = await self.cache_service.get_stats()
            health_status["metrics"]["query_metrics"] = self.query_service.get_metrics()
            health_status["metrics"]["agent_metrics"] = await self.agent_communication.get_metrics()
            health_status["metrics"]["async_metrics"] = self.async_optimizer.get_metrics()
            health_status["metrics"]["performance_metrics"] = await self.performance_monitor.get_performance_metrics()
            
            # Determine overall status
            healthy_services = sum(health_status["services"].values())
            total_services = len(health_status["services"])
            
            if healthy_services == total_services:
                health_status["overall_status"] = "healthy"
            elif healthy_services > total_services * 0.5:
                health_status["overall_status"] = "degraded"
            else:
                health_status["overall_status"] = "unhealthy"
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["overall_status"] = "error"
            health_status["error"] = str(e)
        
        return health_status
    
    async def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all optimization performance improvements.
        
        Returns:
            Dictionary containing optimization performance summary
        """
        if not self.initialized:
            return {"status": "not_initialized"}
        
        try:
            # Collect metrics from all services
            cache_stats = await self.cache_service.get_stats()
            query_metrics = self.query_service.get_metrics()
            agent_metrics = await self.agent_communication.get_metrics()
            async_metrics = self.async_optimizer.get_metrics()
            system_health = await self.performance_monitor.get_system_health()
            
            return {
                "status": "active",
                "startup_time": self.startup_time.isoformat() if self.startup_time else None,
                "uptime_seconds": (
                    (datetime.now() - self.startup_time).total_seconds()
                    if self.startup_time else 0
                ),
                "performance_summary": {
                    "cache_hit_rate": self._extract_cache_hit_rate(cache_stats),
                    "query_performance": {
                        "total_queries": query_metrics.get("total_queries", 0),
                        "cache_hit_rate": query_metrics.get("cache_hit_rate", 0),
                        "avg_latency_ms": query_metrics.get("avg_latency_ms", 0)
                    },
                    "agent_communication": {
                        "total_messages": agent_metrics.get("total_messages", 0),
                        "success_rate": agent_metrics.get("success_rate", 0),
                        "avg_processing_time_ms": agent_metrics.get("avg_processing_time_ms", 0)
                    },
                    "async_operations": {
                        "total_operations": async_metrics.get("total_operations", 0),
                        "success_rate": async_metrics.get("success_rate", 0),
                        "max_concurrent": async_metrics.get("max_concurrent_operations", 0)
                    },
                    "system_health": {
                        "status": system_health.status,
                        "cpu_usage": system_health.cpu_usage,
                        "memory_usage": system_health.memory_usage,
                        "response_time_p95": system_health.response_time_p95,
                        "error_rate": system_health.error_rate
                    }
                },
                "optimization_recommendations": await self.performance_monitor.get_optimization_recommendations()
            }
            
        except Exception as e:
            logger.error(f"Failed to get optimization summary: {e}")
            return {"status": "error", "error": str(e)}
    
    def _extract_cache_hit_rate(self, cache_stats: Any) -> float:
        """Extract cache hit rate from cache stats."""
        if isinstance(cache_stats, dict) and "types" in cache_stats:
            # Calculate overall hit rate across all cache types
            total_hits = 0
            total_requests = 0
            
            for cache_type_stats in cache_stats["types"].values():
                if isinstance(cache_type_stats, dict):
                    hits = cache_type_stats.get("hits", 0)
                    requests = cache_type_stats.get("requests", 0)
                    total_hits += hits
                    total_requests += requests
            
            return (total_hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return 0.0
    
    def configure_fastapi_app(self, app: FastAPI) -> None:
        """
        Configure FastAPI app with optimization middleware and event handlers.
        
        Args:
            app: FastAPI application instance
        """
        # Add response optimization middleware
        app.add_middleware(create_response_optimization_middleware(
            compress_responses=True,
            min_compression_size=1024,
            enable_caching=True,
            default_cache_ttl=300
        ))
        
        # Add startup and shutdown event handlers
        @app.on_event("startup")
        async def startup_optimizations():
            success = await self.initialize()
            if not success:
                logger.warning("Some optimization services failed to initialize")
        
        @app.on_event("shutdown")
        async def shutdown_optimizations():
            await self.shutdown()
        
        logger.info("FastAPI app configured with optimization middleware and event handlers")


# Global optimization manager instance
optimization_manager = OptimizationManager()


@asynccontextmanager
async def optimized_server_lifespan(app: FastAPI):
    """
    Async context manager for server lifespan with optimizations.
    
    Usage:
        app = FastAPI(lifespan=optimized_server_lifespan)
    """
    # Startup
    logger.info("Starting HigherSelf Network Server with optimizations...")
    success = await optimization_manager.initialize()
    
    if success:
        logger.info("✅ All optimization services started successfully")
    else:
        logger.warning("⚠️ Some optimization services failed to start")
    
    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down HigherSelf Network Server optimizations...")
        await optimization_manager.shutdown()
        logger.info("✅ All optimization services stopped successfully")


# Convenience functions for easy integration
async def initialize_optimizations() -> bool:
    """Initialize all optimization services."""
    return await optimization_manager.initialize()


async def shutdown_optimizations() -> bool:
    """Shutdown all optimization services."""
    return await optimization_manager.shutdown()


async def get_optimization_health() -> Dict[str, Any]:
    """Get health status of all optimization services."""
    return await optimization_manager.health_check()


async def get_optimization_summary() -> Dict[str, Any]:
    """Get performance summary of all optimizations."""
    return await optimization_manager.get_optimization_summary()
