"""
Performance Monitoring Service for HigherSelf Network Server.

Provides comprehensive performance tracking, metrics collection,
and optimization recommendations for the entire system.
"""

import asyncio
import time
import psutil
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

from loguru import logger
from pydantic import BaseModel

from services.enhanced_cache_service import CacheService, CacheType
from services.redis_service import redis_service


@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""
    
    timestamp: datetime
    metric_name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """System health status."""
    
    status: str  # healthy, degraded, unhealthy
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    redis_status: str
    notion_api_status: str
    mongodb_status: str
    active_connections: int
    response_time_p95: float
    error_rate: float
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceMonitoringService:
    """
    Comprehensive performance monitoring service.
    
    Features:
    - Real-time metrics collection
    - System health monitoring
    - Performance trend analysis
    - Automatic optimization recommendations
    - Alert generation for performance issues
    """
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()
        
        # Metrics storage (in-memory with Redis backup)
        self.metrics_buffer: deque = deque(maxlen=10000)  # Last 10k metrics
        self.aggregated_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Performance thresholds
        self.thresholds = {
            'cpu_usage': 80.0,          # 80% CPU usage
            'memory_usage': 85.0,       # 85% memory usage
            'disk_usage': 90.0,         # 90% disk usage
            'response_time_p95': 2000,  # 2 seconds
            'error_rate': 5.0,          # 5% error rate
            'cache_hit_rate': 70.0,     # 70% cache hit rate
        }
        
        # Monitoring intervals
        self.system_monitor_interval = 30  # seconds
        self.metrics_flush_interval = 60   # seconds
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._flush_task: Optional[asyncio.Task] = None
        
        # Performance counters
        self.request_count = 0
        self.error_count = 0
        self.response_times: deque = deque(maxlen=1000)
        
    async def start_monitoring(self):
        """Start background monitoring tasks."""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._system_monitor_loop())
            
        if self._flush_task is None or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._metrics_flush_loop())
            
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop background monitoring tasks."""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            
        logger.info("Performance monitoring stopped")
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a performance metric."""
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name=metric_name,
            value=value,
            tags=tags or {},
            metadata=metadata or {}
        )
        
        self.metrics_buffer.append(metric)
        self.aggregated_metrics[metric_name].append(value)
    
    def record_request(self, response_time: float, success: bool = True):
        """Record API request metrics."""
        self.request_count += 1
        self.response_times.append(response_time)
        
        if not success:
            self.error_count += 1
        
        # Record detailed metrics
        self.record_metric("api_response_time", response_time, {"success": str(success)})
        self.record_metric("api_request_count", 1, {"success": str(success)})
    
    async def get_system_health(self) -> SystemHealth:
        """Get current system health status."""
        try:
            # System metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Service health checks
            redis_health = await self._check_redis_health()
            notion_health = await self._check_notion_health()
            mongodb_health = await self._check_mongodb_health()
            
            # Performance metrics
            response_time_p95 = self._calculate_percentile(list(self.response_times), 95)
            error_rate = (self.error_count / max(self.request_count, 1)) * 100
            
            # Determine overall status
            status = self._determine_health_status(
                cpu_usage, memory.percent, disk.percent,
                response_time_p95, error_rate
            )
            
            return SystemHealth(
                status=status,
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                redis_status=redis_health,
                notion_api_status=notion_health,
                mongodb_status=mongodb_health,
                active_connections=len(psutil.net_connections()),
                response_time_p95=response_time_p95,
                error_rate=error_rate
            )
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return SystemHealth(
                status="error",
                cpu_usage=0,
                memory_usage=0,
                disk_usage=0,
                redis_status="unknown",
                notion_api_status="unknown",
                mongodb_status="unknown",
                active_connections=0,
                response_time_p95=0,
                error_rate=100
            )
    
    async def get_performance_metrics(
        self,
        metric_name: Optional[str] = None,
        time_range: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get performance metrics with optional filtering."""
        time_range = time_range or timedelta(hours=1)
        cutoff_time = datetime.now() - time_range
        
        if metric_name:
            # Get specific metric
            values = [
                metric.value for metric in self.metrics_buffer
                if metric.metric_name == metric_name and metric.timestamp >= cutoff_time
            ]
            
            if not values:
                return {"metric_name": metric_name, "values": [], "stats": {}}
            
            return {
                "metric_name": metric_name,
                "values": values,
                "stats": {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": statistics.mean(values),
                    "median": statistics.median(values),
                    "p95": self._calculate_percentile(values, 95),
                    "p99": self._calculate_percentile(values, 99)
                }
            }
        else:
            # Get all metrics summary
            metrics_summary = {}
            
            for name, values in self.aggregated_metrics.items():
                if values:
                    recent_values = list(values)[-100:]  # Last 100 values
                    metrics_summary[name] = {
                        "count": len(recent_values),
                        "avg": statistics.mean(recent_values),
                        "min": min(recent_values),
                        "max": max(recent_values),
                        "latest": recent_values[-1] if recent_values else 0
                    }
            
            return {
                "summary": metrics_summary,
                "system_health": (await self.get_system_health()).__dict__,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on current metrics."""
        recommendations = []
        health = await self.get_system_health()
        
        # CPU optimization
        if health.cpu_usage > self.thresholds['cpu_usage']:
            recommendations.append({
                "type": "cpu_optimization",
                "priority": "high",
                "message": f"CPU usage is {health.cpu_usage:.1f}%, consider scaling or optimizing CPU-intensive operations",
                "suggestions": [
                    "Enable async processing for heavy operations",
                    "Implement request queuing",
                    "Consider horizontal scaling"
                ]
            })
        
        # Memory optimization
        if health.memory_usage > self.thresholds['memory_usage']:
            recommendations.append({
                "type": "memory_optimization",
                "priority": "high",
                "message": f"Memory usage is {health.memory_usage:.1f}%, implement memory optimization",
                "suggestions": [
                    "Increase cache TTL to reduce memory pressure",
                    "Implement memory-efficient data structures",
                    "Add memory monitoring and cleanup"
                ]
            })
        
        # Response time optimization
        if health.response_time_p95 > self.thresholds['response_time_p95']:
            recommendations.append({
                "type": "response_time_optimization",
                "priority": "medium",
                "message": f"95th percentile response time is {health.response_time_p95:.0f}ms",
                "suggestions": [
                    "Implement more aggressive caching",
                    "Optimize database queries",
                    "Add connection pooling"
                ]
            })
        
        # Error rate optimization
        if health.error_rate > self.thresholds['error_rate']:
            recommendations.append({
                "type": "error_rate_optimization",
                "priority": "high",
                "message": f"Error rate is {health.error_rate:.1f}%",
                "suggestions": [
                    "Implement circuit breakers",
                    "Add retry mechanisms",
                    "Improve error handling"
                ]
            })
        
        # Cache optimization
        cache_stats = await self.cache_service.get_stats()
        if isinstance(cache_stats, dict) and 'types' in cache_stats:
            for cache_type, stats in cache_stats['types'].items():
                if stats.get('hit_rate', 0) < self.thresholds['cache_hit_rate']:
                    recommendations.append({
                        "type": "cache_optimization",
                        "priority": "medium",
                        "message": f"Cache hit rate for {cache_type} is low",
                        "suggestions": [
                            "Increase cache TTL",
                            "Implement cache warming",
                            "Review cache key strategies"
                        ]
                    })
        
        return recommendations
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _determine_health_status(
        self,
        cpu_usage: float,
        memory_usage: float,
        disk_usage: float,
        response_time_p95: float,
        error_rate: float
    ) -> str:
        """Determine overall system health status."""
        critical_issues = 0
        warning_issues = 0
        
        # Check critical thresholds
        if cpu_usage > 90 or memory_usage > 95 or disk_usage > 95:
            critical_issues += 1
        elif cpu_usage > 80 or memory_usage > 85 or disk_usage > 90:
            warning_issues += 1
        
        if error_rate > 10:
            critical_issues += 1
        elif error_rate > 5:
            warning_issues += 1
        
        if response_time_p95 > 5000:  # 5 seconds
            critical_issues += 1
        elif response_time_p95 > 2000:  # 2 seconds
            warning_issues += 1
        
        if critical_issues > 0:
            return "unhealthy"
        elif warning_issues > 0:
            return "degraded"
        else:
            return "healthy"
    
    async def _check_redis_health(self) -> str:
        """Check Redis service health."""
        try:
            health = await redis_service.async_health_check()
            return health.get("status", "unknown")
        except Exception:
            return "unhealthy"
    
    async def _check_notion_health(self) -> str:
        """Check Notion API health."""
        # This would need to be implemented based on your Notion service
        return "healthy"  # Placeholder
    
    async def _check_mongodb_health(self) -> str:
        """Check MongoDB health."""
        # This would need to be implemented based on your MongoDB service
        return "healthy"  # Placeholder
    
    async def _system_monitor_loop(self):
        """Background task for system monitoring."""
        while True:
            try:
                health = await self.get_system_health()
                
                # Record system metrics
                self.record_metric("cpu_usage", health.cpu_usage)
                self.record_metric("memory_usage", health.memory_usage)
                self.record_metric("disk_usage", health.disk_usage)
                self.record_metric("active_connections", health.active_connections)
                self.record_metric("error_rate", health.error_rate)
                
                await asyncio.sleep(self.system_monitor_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(self.system_monitor_interval)
    
    async def _metrics_flush_loop(self):
        """Background task for flushing metrics to Redis."""
        while True:
            try:
                # Flush metrics to Redis for persistence
                if self.metrics_buffer:
                    metrics_data = [
                        {
                            "timestamp": metric.timestamp.isoformat(),
                            "metric_name": metric.metric_name,
                            "value": metric.value,
                            "tags": metric.tags,
                            "metadata": metric.metadata
                        }
                        for metric in list(self.metrics_buffer)
                    ]
                    
                    await self.cache_service.set(
                        "performance_metrics",
                        metrics_data,
                        ttl=3600,  # 1 hour
                        cache_type=CacheType.CONFIG
                    )
                
                await asyncio.sleep(self.metrics_flush_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics flush error: {e}")
                await asyncio.sleep(self.metrics_flush_interval)


# Global performance monitoring service instance
performance_monitor = PerformanceMonitoringService()
