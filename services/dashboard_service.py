"""
Dashboard Service for HigherSelf Operations Dashboard
Handles business logic for dashboard operations and integrations
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from services.base_service import BaseService
from services.redis_service import RedisService
from services.mongodb_service import MongoDBService
from services.notion_service import NotionService
from models.base import ApiPlatform

logger = logging.getLogger(__name__)


class DashboardService(BaseService):
    """Service for managing dashboard operations and data aggregation"""
    
    def __init__(self):
        super().__init__()
        self.redis_service = RedisService()
        self.mongodb_service = MongoDBService()
        self.notion_service = NotionService()
        self.cache_ttl = 300  # 5 minutes default cache
        
    async def get_organization_metrics(self, org_id: str) -> Dict[str, Any]:
        """Get metrics for a specific organization"""
        try:
            cache_key = f"dashboard:org_metrics:{org_id}"
            cached_data = await self.redis_service.get(cache_key)
            
            if cached_data:
                return cached_data
            
            # Generate fresh metrics based on organization
            metrics = await self._calculate_org_metrics(org_id)
            
            # Cache the results
            await self.redis_service.setex(cache_key, self.cache_ttl, metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get organization metrics for {org_id}: {e}")
            return {}
    
    async def get_agent_performance_data(self) -> List[Dict[str, Any]]:
        """Get performance data for all agents"""
        try:
            cache_key = "dashboard:agent_performance"
            cached_data = await self.redis_service.get(cache_key)
            
            if cached_data:
                return cached_data
            
            # Get agent data from MongoDB
            agents_collection = self.mongodb_service.get_collection("agents")
            agents = await agents_collection.find({}).to_list(length=None)
            
            # Enhance with performance metrics
            performance_data = []
            for agent in agents:
                agent_perf = await self._calculate_agent_performance(agent)
                performance_data.append(agent_perf)
            
            # Cache the results
            await self.redis_service.setex(cache_key, 60, performance_data)  # 1 minute cache
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Failed to get agent performance data: {e}")
            return []
    
    async def get_real_time_system_status(self) -> Dict[str, Any]:
        """Get real-time system status and health metrics"""
        try:
            # Check all critical services
            services_status = await asyncio.gather(
                self._check_redis_status(),
                self._check_mongodb_status(),
                self._check_notion_status(),
                return_exceptions=True
            )
            
            redis_status, mongo_status, notion_status = services_status
            
            # Calculate overall system health
            healthy_services = sum([
                1 for status in [redis_status, mongo_status, notion_status]
                if isinstance(status, dict) and status.get("healthy", False)
            ])
            
            total_services = 3
            health_percentage = (healthy_services / total_services) * 100
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_health": health_percentage,
                "status": "healthy" if health_percentage >= 80 else "degraded" if health_percentage >= 50 else "critical",
                "services": {
                    "redis": redis_status if isinstance(redis_status, dict) else {"healthy": False, "error": str(redis_status)},
                    "mongodb": mongo_status if isinstance(mongo_status, dict) else {"healthy": False, "error": str(mongo_status)},
                    "notion": notion_status if isinstance(notion_status, dict) else {"healthy": False, "error": str(notion_status)}
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_health": 0,
                "status": "critical",
                "error": str(e)
            }
    
    async def update_agent_status(self, agent_name: str, status_data: Dict[str, Any]) -> bool:
        """Update real-time status for an agent"""
        try:
            status_key = f"agent:status:{agent_name.lower().replace(' ', '_')}"
            
            # Add timestamp to status data
            status_data["last_updated"] = datetime.utcnow().isoformat()
            
            # Store in Redis with 10 minute expiry
            await self.redis_service.setex(status_key, 600, status_data)
            
            # Also log to MongoDB for historical tracking
            await self._log_agent_status_change(agent_name, status_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent status for {agent_name}: {e}")
            return False
    
    async def get_dashboard_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        """Get notifications for dashboard user"""
        try:
            # Get recent system alerts
            alerts = await self._get_system_alerts()
            
            # Get agent notifications
            agent_notifications = await self._get_agent_notifications()
            
            # Get business notifications
            business_notifications = await self._get_business_notifications()
            
            # Combine and sort by priority/timestamp
            all_notifications = alerts + agent_notifications + business_notifications
            all_notifications.sort(key=lambda x: (x.get("priority", 0), x.get("timestamp", "")), reverse=True)
            
            return all_notifications[:20]  # Return top 20 notifications
            
        except Exception as e:
            logger.error(f"Failed to get dashboard notifications: {e}")
            return []
    
    async def _calculate_org_metrics(self, org_id: str) -> Dict[str, Any]:
        """Calculate metrics for a specific organization"""
        # Mock implementation - replace with actual business logic
        org_configs = {
            "am-consulting": {
                "active_practitioners": 12,
                "appointments_today": 34,
                "revenue_today": 4500.00,
                "client_satisfaction": 94.2
            },
            "seven-space": {
                "active_events": 5,
                "visitors_today": 127,
                "bookings_this_week": 89,
                "space_utilization": 78.5
            },
            "higherself-network": {
                "active_users": 2847,
                "community_posts": 156,
                "platform_uptime": 99.8,
                "engagement_rate": 67.3
            }
        }
        
        return org_configs.get(org_id, {})
    
    async def _calculate_agent_performance(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics for an agent"""
        agent_name = agent.get("name", "Unknown")
        
        # Mock performance calculation - replace with actual metrics
        return {
            "name": agent_name,
            "id": agent.get("id", ""),
            "status": "active",
            "tasks_completed": 45,
            "success_rate": 92.5,
            "average_response_time": 1.8,
            "last_activity": datetime.utcnow().isoformat(),
            "performance_score": 88.7,
            "level": 15,
            "experience_points": 2340
        }
    
    async def _check_redis_status(self) -> Dict[str, Any]:
        """Check Redis service status"""
        try:
            ping_result = await self.redis_service.ping()
            return {
                "healthy": ping_result,
                "response_time": 0.05,  # Mock response time
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_mongodb_status(self) -> Dict[str, Any]:
        """Check MongoDB service status"""
        try:
            health_check = await self.mongodb_service.health_check()
            return {
                "healthy": health_check,
                "response_time": 0.12,  # Mock response time
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_notion_status(self) -> Dict[str, Any]:
        """Check Notion service status"""
        try:
            # Simple check - try to get user info
            user_info = await self.notion_service.get_user_info()
            return {
                "healthy": bool(user_info),
                "response_time": 0.25,  # Mock response time
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _log_agent_status_change(self, agent_name: str, status_data: Dict[str, Any]):
        """Log agent status change to MongoDB for historical tracking"""
        try:
            status_log_collection = self.mongodb_service.get_collection("agent_status_log")
            log_entry = {
                "agent_name": agent_name,
                "status_data": status_data,
                "timestamp": datetime.utcnow()
            }
            await status_log_collection.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Failed to log agent status change: {e}")
    
    async def _get_system_alerts(self) -> List[Dict[str, Any]]:
        """Get system-level alerts"""
        # Mock implementation
        return [
            {
                "id": "alert_001",
                "type": "system",
                "priority": 2,
                "title": "High CPU Usage",
                "message": "System CPU usage is at 85%",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    
    async def _get_agent_notifications(self) -> List[Dict[str, Any]]:
        """Get agent-related notifications"""
        # Mock implementation
        return [
            {
                "id": "agent_001",
                "type": "agent",
                "priority": 1,
                "title": "Agent Performance",
                "message": "Grace Fields achieved 100% success rate today",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    
    async def _get_business_notifications(self) -> List[Dict[str, Any]]:
        """Get business-related notifications"""
        # Mock implementation
        return [
            {
                "id": "business_001",
                "type": "business",
                "priority": 1,
                "title": "Revenue Milestone",
                "message": "Monthly revenue target achieved",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]


# Global instance
dashboard_service = DashboardService()
