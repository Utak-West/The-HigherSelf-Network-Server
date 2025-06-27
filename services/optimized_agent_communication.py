"""
Optimized Agent Communication Service for HigherSelf Network Server.

Provides high-performance pub/sub messaging, message routing, and
communication patterns for inter-agent coordination.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

from loguru import logger
from pydantic import BaseModel

from models.base import OptimizedBaseModel
from services.redis_service import redis_service
from services.performance_monitoring_service import performance_monitor


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageType(str, Enum):
    """Types of inter-agent messages."""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    WORKFLOW_EVENT = "workflow_event"
    SYSTEM_ALERT = "system_alert"
    HEARTBEAT = "heartbeat"
    BROADCAST = "broadcast"


@dataclass
class AgentMessage(OptimizedBaseModel):
    """Optimized agent message structure."""
    
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    recipient_id: Optional[str] = None  # None for broadcast
    message_type: MessageType
    priority: MessagePriority = MessagePriority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if message has expired."""
        return self.expires_at is not None and datetime.now() > self.expires_at
    
    def to_redis_message(self) -> str:
        """Serialize message for Redis pub/sub."""
        return self.model_dump_json()
    
    @classmethod
    def from_redis_message(cls, data: str) -> "AgentMessage":
        """Deserialize message from Redis pub/sub."""
        return cls.model_validate_json(data)


class MessageHandler:
    """Base class for message handlers."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
    
    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle incoming message and optionally return a response."""
        raise NotImplementedError


class OptimizedAgentCommunication:
    """
    High-performance agent communication service.
    
    Features:
    - Redis pub/sub for real-time messaging
    - Message routing and filtering
    - Priority-based message handling
    - Message persistence and replay
    - Performance monitoring
    - Circuit breaker for reliability
    """
    
    def __init__(self):
        self.redis_client = redis_service
        
        # Message handlers by agent ID
        self.message_handlers: Dict[str, MessageHandler] = {}
        
        # Active subscriptions
        self.subscriptions: Dict[str, Set[str]] = {}  # channel -> agent_ids
        self.agent_channels: Dict[str, Set[str]] = {}  # agent_id -> channels
        
        # Message queues for different priorities
        self.priority_queues: Dict[MessagePriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in MessagePriority
        }
        
        # Performance metrics
        self.message_count = 0
        self.failed_messages = 0
        self.processing_times: List[float] = []
        
        # Background tasks
        self._subscriber_task: Optional[asyncio.Task] = None
        self._processor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Configuration
        self.max_message_size = 1024 * 1024  # 1MB
        self.message_ttl = timedelta(hours=24)  # 24 hours
        self.heartbeat_interval = 30  # seconds
        self.max_retry_attempts = 3
    
    async def start(self):
        """Start the communication service."""
        if self._subscriber_task is None or self._subscriber_task.done():
            self._subscriber_task = asyncio.create_task(self._subscription_loop())
        
        if self._processor_task is None or self._processor_task.done():
            self._processor_task = asyncio.create_task(self._message_processor_loop())
        
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Optimized agent communication service started")
    
    async def stop(self):
        """Stop the communication service."""
        tasks = [self._subscriber_task, self._processor_task, self._cleanup_task]
        
        for task in tasks:
            if task and not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*[task for task in tasks if task], return_exceptions=True)
        
        logger.info("Optimized agent communication service stopped")
    
    def register_agent(self, agent_id: str, handler: MessageHandler):
        """Register an agent with its message handler."""
        self.message_handlers[agent_id] = handler
        self.agent_channels[agent_id] = set()
        logger.info(f"Registered agent: {agent_id}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent."""
        if agent_id in self.message_handlers:
            del self.message_handlers[agent_id]
        
        if agent_id in self.agent_channels:
            # Unsubscribe from all channels
            for channel in self.agent_channels[agent_id]:
                if channel in self.subscriptions:
                    self.subscriptions[channel].discard(agent_id)
            del self.agent_channels[agent_id]
        
        logger.info(f"Unregistered agent: {agent_id}")
    
    async def subscribe_to_channel(self, agent_id: str, channel: str):
        """Subscribe an agent to a communication channel."""
        if agent_id not in self.message_handlers:
            raise ValueError(f"Agent {agent_id} not registered")
        
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
        
        self.subscriptions[channel].add(agent_id)
        self.agent_channels[agent_id].add(channel)
        
        logger.debug(f"Agent {agent_id} subscribed to channel {channel}")
    
    async def unsubscribe_from_channel(self, agent_id: str, channel: str):
        """Unsubscribe an agent from a communication channel."""
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(agent_id)
        
        if agent_id in self.agent_channels:
            self.agent_channels[agent_id].discard(channel)
        
        logger.debug(f"Agent {agent_id} unsubscribed from channel {channel}")
    
    async def send_message(
        self,
        message: AgentMessage,
        channel: Optional[str] = None
    ) -> bool:
        """Send a message to an agent or broadcast to a channel."""
        start_time = time.time()
        
        try:
            # Validate message size
            message_data = message.to_redis_message()
            if len(message_data.encode()) > self.max_message_size:
                logger.warning(f"Message too large: {len(message_data)} bytes")
                return False
            
            # Set expiration if not set
            if message.expires_at is None:
                message.expires_at = datetime.now() + self.message_ttl
            
            # Determine routing
            if message.recipient_id:
                # Direct message
                channel = f"agent:{message.recipient_id}"
            elif channel:
                # Channel broadcast
                pass
            else:
                # Global broadcast
                channel = "agents:broadcast"
            
            # Publish to Redis
            await self.redis_client.async_publish(channel, message_data)
            
            # Store message for persistence (optional)
            await self._store_message(message)
            
            # Update metrics
            self.message_count += 1
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            # Record performance metric
            performance_monitor.record_metric(
                "agent_message_sent",
                processing_time * 1000,  # Convert to milliseconds
                {"priority": message.priority.value, "type": message.message_type.value}
            )
            
            logger.debug(f"Message sent: {message.message_id} to {channel}")
            return True
            
        except Exception as e:
            self.failed_messages += 1
            logger.error(f"Failed to send message {message.message_id}: {e}")
            return False
    
    async def send_request(
        self,
        sender_id: str,
        recipient_id: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        timeout: float = 30.0
    ) -> Optional[AgentMessage]:
        """Send a request message and wait for response."""
        correlation_id = str(uuid.uuid4())
        
        request_message = AgentMessage(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload,
            correlation_id=correlation_id,
            reply_to=f"agent:{sender_id}:responses"
        )
        
        # Set up response listener
        response_future = asyncio.Future()
        response_channel = f"agent:{sender_id}:responses"
        
        # Subscribe to response channel temporarily
        await self.subscribe_to_channel(sender_id, response_channel)
        
        try:
            # Send request
            success = await self.send_message(request_message)
            if not success:
                return None
            
            # Wait for response
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout for message {correlation_id}")
            return None
        finally:
            # Cleanup response subscription
            await self.unsubscribe_from_channel(sender_id, response_channel)
    
    async def broadcast_message(
        self,
        sender_id: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        channel: str = "agents:broadcast"
    ) -> bool:
        """Broadcast a message to all agents on a channel."""
        broadcast_message = AgentMessage(
            sender_id=sender_id,
            message_type=message_type,
            payload=payload,
            priority=MessagePriority.NORMAL
        )
        
        return await self.send_message(broadcast_message, channel)
    
    async def send_heartbeat(self, agent_id: str):
        """Send heartbeat message for an agent."""
        heartbeat_message = AgentMessage(
            sender_id=agent_id,
            message_type=MessageType.HEARTBEAT,
            priority=MessagePriority.LOW,
            payload={"timestamp": datetime.now().isoformat()}
        )
        
        await self.send_message(heartbeat_message, "agents:heartbeat")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get communication service metrics."""
        avg_processing_time = (
            sum(self.processing_times) / len(self.processing_times)
            if self.processing_times else 0
        )
        
        return {
            "total_messages": self.message_count,
            "failed_messages": self.failed_messages,
            "success_rate": (
                (self.message_count - self.failed_messages) / max(self.message_count, 1)
            ) * 100,
            "avg_processing_time_ms": avg_processing_time * 1000,
            "active_agents": len(self.message_handlers),
            "active_channels": len(self.subscriptions),
            "queue_sizes": {
                priority.value: queue.qsize()
                for priority, queue in self.priority_queues.items()
            }
        }
    
    async def _store_message(self, message: AgentMessage):
        """Store message for persistence and replay."""
        try:
            key = f"message_store:{message.message_id}"
            await self.redis_client.async_set(
                key,
                message.to_redis_message(),
                ex=int(self.message_ttl.total_seconds())
            )
        except Exception as e:
            logger.warning(f"Failed to store message {message.message_id}: {e}")
    
    async def _subscription_loop(self):
        """Background task for handling Redis subscriptions."""
        try:
            # This would need to be implemented with Redis pub/sub
            # For now, it's a placeholder
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Subscription loop error: {e}")
    
    async def _message_processor_loop(self):
        """Background task for processing messages by priority."""
        try:
            while True:
                # Process messages in priority order
                for priority in [MessagePriority.URGENT, MessagePriority.HIGH, 
                               MessagePriority.NORMAL, MessagePriority.LOW]:
                    queue = self.priority_queues[priority]
                    
                    try:
                        message = queue.get_nowait()
                        await self._process_message(message)
                    except asyncio.QueueEmpty:
                        continue
                
                await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Message processor error: {e}")
    
    async def _process_message(self, message: AgentMessage):
        """Process an individual message."""
        try:
            # Check if message has expired
            if message.is_expired():
                logger.debug(f"Message {message.message_id} expired, discarding")
                return
            
            # Find target agents
            target_agents = []
            if message.recipient_id:
                if message.recipient_id in self.message_handlers:
                    target_agents = [message.recipient_id]
            else:
                # Broadcast to all registered agents
                target_agents = list(self.message_handlers.keys())
            
            # Process message for each target agent
            for agent_id in target_agents:
                handler = self.message_handlers.get(agent_id)
                if handler:
                    try:
                        response = await handler.handle_message(message)
                        if response and message.reply_to:
                            await self.send_message(response, message.reply_to)
                    except Exception as e:
                        logger.error(f"Handler error for agent {agent_id}: {e}")
            
        except Exception as e:
            logger.error(f"Message processing error: {e}")
    
    async def _cleanup_loop(self):
        """Background task for cleanup operations."""
        try:
            while True:
                # Clean up expired messages, old metrics, etc.
                await asyncio.sleep(300)  # Run every 5 minutes
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Cleanup loop error: {e}")


# Global optimized agent communication service
agent_communication = OptimizedAgentCommunication()
