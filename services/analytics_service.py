"""
Analytics Service for Higher Self Network Server.
Tracks agent performance, workflow execution, and MCP tool usage.
"""

import time
import uuid
from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge

from services.mongodb_service import mongo_service
from services.redis_service import redis_service

# Metrics for monitoring agent and MCP tool performance
AGENT_ACTION_COUNTER = Counter(
    'agent_actions_total',
    'Total count of agent actions',
    ['agent_id', 'action_type', 'outcome']
)
MCP_TOOL_USAGE = Counter(
    'mcp_tool_usage_total',
    'Total count of MCP tool usage',
    ['tool_name', 'agent_id', 'operation', 'outcome']
)
WORKFLOW_TRANSITIONS = Counter(
    'workflow_transitions_total',
    'Total count of workflow state transitions',
    ['workflow_id', 'from_state', 'to_state', 'agent_id']
)
AGENT_LATENCY = Histogram(
    'agent_action_duration_seconds',
    'Duration of agent actions in seconds',
    ['agent_id', 'action_type']
)
MCP_TOOL_LATENCY = Histogram(
    'mcp_tool_operation_duration_seconds',
    'Duration of MCP tool operations in seconds',
    ['tool_name', 'operation']
)
WORKFLOW_STAGE_DURATION = Histogram(
    'workflow_stage_duration_seconds',
    'Duration of workflow stages in seconds',
    ['workflow_id', 'state']
)

class AgentAnalytics:
    """
    Service for tracking and analyzing agent performance metrics and MCP tool usage.
    Stores results in MongoDB for long-term analysis and Redis for real-time monitoring.
    """
    
    def __init__(self):
        """Initialize the analytics service."""
        self.agent_collection = "agent_analytics"
        self.workflow_collection = "workflow_analytics"
        self.mcp_tool_collection = "mcp_tool_analytics"
        self.realtime_key_prefix = "analytics:realtime"
        self.metric_retention_days = 30  # Days to keep analytics data
        
        logger.info("Agent analytics service initialized")
        
    async def record_agent_action(
        self,
        agent_id: str,
        action_type: str,
        context: Dict[str, Any],
        duration_ms: float,
        outcome: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record an agent action for analytics.
        
        Args:
            agent_id: The ID of the agent
            action_type: The type of action performed
            context: The context of the action
            duration_ms: The duration of the action in milliseconds
            outcome: The outcome of the action (success, failure, etc.)
            metadata: Additional metadata
            
        Returns:
            The ID of the analytics record
        """
        try:
            # Create analytics document
            document = {
                "timestamp": datetime.utcnow(),
                "agent_id": agent_id,
                "action_type": action_type,
                "context": context,
                "duration_ms": duration_ms,
                "outcome": outcome,
                "metadata": metadata or {}
            }
            
            # Record in MongoDB
            record_id = await mongo_service.async_insert_one(
                self.agent_collection, document
            )
            
            # Update Redis for real-time monitoring
            key = f"{self.realtime_key_prefix}:agent:{agent_id}"
            await self._update_realtime_stats(key, action_type, outcome, duration_ms)
            
            # Update Prometheus metrics
            AGENT_ACTION_COUNTER.labels(
                agent_id=agent_id,
                action_type=action_type,
                outcome=outcome
            ).inc()
            
            AGENT_LATENCY.labels(
                agent_id=agent_id,
                action_type=action_type
            ).observe(duration_ms / 1000)  # Convert to seconds
            
            return record_id
        except Exception as e:
            logger.error(f"Failed to record agent action: {e}")
            return str(uuid.uuid4())  # Return a placeholder ID
    
    async def record_mcp_tool_usage(
        self,
        tool_name: str,
        agent_id: str,
        operation: str,
        parameters: Dict[str, Any],
        duration_ms: float,
        outcome: str,
        result_summary: Optional[str] = None
    ) -> str:
        """
        Record MCP tool usage for analytics.
        
        Args:
            tool_name: The name of the MCP tool
            agent_id: The ID of the agent using the tool
            operation: The operation performed
            parameters: The parameters of the operation
            duration_ms: The duration of the operation in milliseconds
            outcome: The outcome of the operation (success, failure, etc.)
            result_summary: Summary of the result
            
        Returns:
            The ID of the analytics record
        """
        try:
            # Create analytics document
            document = {
                "timestamp": datetime.utcnow(),
                "tool_name": tool_name,
                "agent_id": agent_id,
                "operation": operation,
                "parameters": parameters,
                "duration_ms": duration_ms,
                "outcome": outcome,
                "result_summary": result_summary
            }
            
            # Record in MongoDB
            record_id = await mongo_service.async_insert_one(
                self.mcp_tool_collection, document
            )
            
            # Update Redis for real-time monitoring
            key = f"{self.realtime_key_prefix}:mcp_tool:{tool_name}"
            await self._update_realtime_stats(key, operation, outcome, duration_ms)
            
            # Update Prometheus metrics
            MCP_TOOL_USAGE.labels(
                tool_name=tool_name,
                agent_id=agent_id,
                operation=operation,
                outcome=outcome
            ).inc()
            
            MCP_TOOL_LATENCY.labels(
                tool_name=tool_name,
                operation=operation
            ).observe(duration_ms / 1000)  # Convert to seconds
            
            return record_id
        except Exception as e:
            logger.error(f"Failed to record MCP tool usage: {e}")
            return str(uuid.uuid4())  # Return a placeholder ID
    
    async def record_workflow_transition(
        self,
        workflow_id: str,
        from_state: str,
        to_state: str,
        agent_id: str,
        context: Dict[str, Any],
        duration_ms: float
    ) -> str:
        """
        Record a workflow state transition for analytics.
        
        Args:
            workflow_id: The ID of the workflow
            from_state: The previous state
            to_state: The new state
            agent_id: The ID of the agent making the transition
            context: The context of the transition
            duration_ms: The duration of the state in milliseconds
            
        Returns:
            The ID of the analytics record
        """
        try:
            # Create analytics document
            document = {
                "timestamp": datetime.utcnow(),
                "workflow_id": workflow_id,
                "from_state": from_state,
                "to_state": to_state,
                "agent_id": agent_id,
                "context": context,
                "duration_ms": duration_ms
            }
            
            # Record in MongoDB
            record_id = await mongo_service.async_insert_one(
                self.workflow_collection, document
            )
            
            # Update Redis for real-time monitoring
            key = f"{self.realtime_key_prefix}:workflow:{workflow_id}"
            await self._update_realtime_stats(key, from_state, to_state, duration_ms)
            
            # Update Prometheus metrics
            WORKFLOW_TRANSITIONS.labels(
                workflow_id=workflow_id,
                from_state=from_state,
                to_state=to_state,
                agent_id=agent_id
            ).inc()
            
            WORKFLOW_STAGE_DURATION.labels(
                workflow_id=workflow_id,
                state=from_state
            ).observe(duration_ms / 1000)  # Convert to seconds
            
            return record_id
        except Exception as e:
            logger.error(f"Failed to record workflow transition: {e}")
            return str(uuid.uuid4())  # Return a placeholder ID
    
    async def _update_realtime_stats(
        self, 
        key: str, 
        action: str, 
        outcome: str, 
        duration_ms: float
    ):
        """
        Update real-time statistics in Redis.
        
        Args:
            key: The Redis key
            action: The action or operation
            outcome: The outcome
            duration_ms: The duration in milliseconds
        """
        try:
            # Get current stats
            stats = await redis_service.async_get(key, as_json=True)
            if not stats:
                stats = {
                    "actions": {},
                    "outcomes": {},
                    "total_count": 0,
                    "total_duration_ms": 0,
                    "avg_duration_ms": 0,
                    "last_update": datetime.utcnow().isoformat()
                }
            
            # Update action count
            stats["actions"][action] = stats["actions"].get(action, 0) + 1
            
            # Update outcome count
            stats["outcomes"][outcome] = stats["outcomes"].get(outcome, 0) + 1
            
            # Update totals
            stats["total_count"] += 1
            stats["total_duration_ms"] += duration_ms
            stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["total_count"]
            stats["last_update"] = datetime.utcnow().isoformat()
            
            # Store updated stats
            await redis_service.async_set(key, stats, ex=86400)  # 24-hour expiry
        except Exception as e:
            logger.error(f"Failed to update real-time stats: {e}")
    
    async def get_agent_performance(
        self,
        agent_id: str,
        timeframe_days: int = 7,
        action_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for an agent.
        
        Args:
            agent_id: The ID of the agent
            timeframe_days: Number of days to look back
            action_types: Optional filter for specific action types
            
        Returns:
            Performance metrics for the agent
        """
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=timeframe_days)
            
            # Build query
            query = {
                "agent_id": agent_id,
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            }
            
            # Add action_types filter if provided
            if action_types:
                query["action_type"] = {"$in": action_types}
            
            # Query MongoDB
            results = await mongo_service.async_find_many(
                self.agent_collection, query
            )
            
            # Aggregate metrics
            metrics = {
                "total_actions": len(results),
                "action_types": {},
                "outcomes": {},
                "avg_duration_ms": 0,
                "timeframe_days": timeframe_days,
                "agent_id": agent_id
            }
            
            total_duration = 0
            
            for result in results:
                # Count by action type
                action_type = result.get("action_type", "unknown")
                if action_type not in metrics["action_types"]:
                    metrics["action_types"][action_type] = 0
                metrics["action_types"][action_type] += 1
                
                # Count by outcome
                outcome = result.get("outcome", "unknown")
                if outcome not in metrics["outcomes"]:
                    metrics["outcomes"][outcome] = 0
                metrics["outcomes"][outcome] += 1
                
                # Sum duration
                total_duration += result.get("duration_ms", 0)
            
            # Calculate average duration
            if metrics["total_actions"] > 0:
                metrics["avg_duration_ms"] = total_duration / metrics["total_actions"]
            
            return metrics
        except Exception as e:
            logger.error(f"Failed to get agent performance: {e}")
            return {
                "error": str(e),
                "total_actions": 0,
                "agent_id": agent_id,
                "timeframe_days": timeframe_days
            }
    
    async def get_mcp_tool_performance(
        self,
        tool_name: Optional[str] = None,
        agent_id: Optional[str] = None,
        timeframe_days: int = 7,
        operations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for MCP tool usage.
        
        Args:
            tool_name: Optional tool name filter
            agent_id: Optional agent ID filter
            timeframe_days: Number of days to look back
            operations: Optional filter for specific operations
            
        Returns:
            Performance metrics for MCP tool usage
        """
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=timeframe_days)
            
            # Build query
            query = {
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            }
            
            # Add filters if provided
            if tool_name:
                query["tool_name"] = tool_name
            if agent_id:
                query["agent_id"] = agent_id
            if operations:
                query["operation"] = {"$in": operations}
            
            # Query MongoDB
            results = await mongo_service.async_find_many(
                self.mcp_tool_collection, query
            )
            
            # Aggregate metrics
            metrics = {
                "total_operations": len(results),
                "tools": {},
                "operations": {},
                "agents": {},
                "outcomes": {},
                "avg_duration_ms": 0,
                "timeframe_days": timeframe_days,
                "tool_name": tool_name,
                "agent_id": agent_id
            }
            
            total_duration = 0
            
            for result in results:
                # Count by tool
                tool = result.get("tool_name", "unknown")
                if tool not in metrics["tools"]:
                    metrics["tools"][tool] = 0
                metrics["tools"][tool] += 1
                
                # Count by operation
                operation = result.get("operation", "unknown")
                if operation not in metrics["operations"]:
                    metrics["operations"][operation] = 0
                metrics["operations"][operation] += 1
                
                # Count by agent
                agent = result.get("agent_id", "unknown")
                if agent not in metrics["agents"]:
                    metrics["agents"][agent] = 0
                metrics["agents"][agent] += 1
                
                # Count by outcome
                outcome = result.get("outcome", "unknown")
                if outcome not in metrics["outcomes"]:
                    metrics["outcomes"][outcome] = 0
                metrics["outcomes"][outcome] += 1
                
                # Sum duration
                total_duration += result.get("duration_ms", 0)
            
            # Calculate average duration
            if metrics["total_operations"] > 0:
                metrics["avg_duration_ms"] = total_duration / metrics["total_operations"]
            
            return metrics
        except Exception as e:
            logger.error(f"Failed to get MCP tool performance: {e}")
            return {
                "error": str(e),
                "total_operations": 0,
                "timeframe_days": timeframe_days
            }
    
    async def get_workflow_performance(
        self,
        workflow_id: Optional[str] = None,
        timeframe_days: int = 7,
        agent_id: Optional[str] = None,
        states: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for workflow execution.
        
        Args:
            workflow_id: Optional workflow ID filter
            timeframe_days: Number of days to look back
            agent_id: Optional agent ID filter
            states: Optional filter for specific states
            
        Returns:
            Performance metrics for workflow execution
        """
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=timeframe_days)
            
            # Build query
            query = {
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            }
            
            # Add filters if provided
            if workflow_id:
                query["workflow_id"] = workflow_id
            if agent_id:
                query["agent_id"] = agent_id
            if states:
                query["$or"] = [
                    {"from_state": {"$in": states}},
                    {"to_state": {"$in": states}}
                ]
            
            # Query MongoDB
            results = await mongo_service.async_find_many(
                self.workflow_collection, query
            )
            
            # Aggregate metrics
            metrics = {
                "total_transitions": len(results),
                "workflows": {},
                "states": {},
                "agents": {},
                "state_durations": {},
                "avg_duration_ms": 0,
                "timeframe_days": timeframe_days,
                "workflow_id": workflow_id,
                "agent_id": agent_id
            }
            
            total_duration = 0
            state_counts = {}
            
            for result in results:
                # Count by workflow
                workflow = result.get("workflow_id", "unknown")
                if workflow not in metrics["workflows"]:
                    metrics["workflows"][workflow] = 0
                metrics["workflows"][workflow] += 1
                
                # Count by state
                from_state = result.get("from_state", "unknown")
                if from_state not in metrics["states"]:
                    metrics["states"][from_state] = 0
                metrics["states"][from_state] += 1
                
                # Count by agent
                agent = result.get("agent_id", "unknown")
                if agent not in metrics["agents"]:
                    metrics["agents"][agent] = 0
                metrics["agents"][agent] += 1
                
                # Track state durations
                duration = result.get("duration_ms", 0)
                
                if from_state not in metrics["state_durations"]:
                    metrics["state_durations"][from_state] = {
                        "total_ms": 0,
                        "count": 0,
                        "avg_ms": 0
                    }
                
                metrics["state_durations"][from_state]["total_ms"] += duration
                metrics["state_durations"][from_state]["count"] += 1
                
                # Sum duration
                total_duration += duration
            
            # Calculate averages
            for state, data in metrics["state_durations"].items():
                if data["count"] > 0:
                    data["avg_ms"] = data["total_ms"] / data["count"]
            
            # Calculate overall average duration
            if metrics["total_transitions"] > 0:
                metrics["avg_duration_ms"] = total_duration / metrics["total_transitions"]
            
            return metrics
        except Exception as e:
            logger.error(f"Failed to get workflow performance: {e}")
            return {
                "error": str(e),
                "total_transitions": 0,
                "timeframe_days": timeframe_days
            }
    
    async def clean_old_metrics(self, days_to_keep: int = None) -> Dict[str, int]:
        """
        Clean up old metrics data.
        
        Args:
            days_to_keep: Number of days to keep data for (defaults to self.metric_retention_days)
            
        Returns:
            Dictionary with counts of deleted records by collection
        """
        try:
            # Use provided value or default
            retention_days = days_to_keep if days_to_keep is not None else self.metric_retention_days
            
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Delete old records from each collection
            agent_count = await mongo_service.async_delete_many(
                self.agent_collection,
                {"timestamp": {"$lt": cutoff_date}}
            )
            
            workflow_count = await mongo_service.async_delete_many(
                self.workflow_collection,
                {"timestamp": {"$lt": cutoff_date}}
            )
            
            mcp_tool_count = await mongo_service.async_delete_many(
                self.mcp_tool_collection,
                {"timestamp": {"$lt": cutoff_date}}
            )
            
            logger.info(
                f"Cleaned {agent_count} agent analytics, {workflow_count} workflow analytics, "
                f"and {mcp_tool_count} MCP tool analytics records older than {retention_days} days"
            )
            
            return {
                "agent_count": agent_count,
                "workflow_count": workflow_count,
                "mcp_tool_count": mcp_tool_count,
                "cutoff_date": cutoff_date.isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to clean old metrics: {e}")
            return {
                "error": str(e),
                "agent_count": 0,
                "workflow_count": 0,
                "mcp_tool_count": 0
            }


# Create a singleton instance
agent_analytics = AgentAnalytics()
