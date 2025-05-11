"""
Message bus for agent communication in The HigherSelf Network Server.

This module provides a simple message bus for inter-agent communication,
with support for Notion as the central hub for message storage and tracing.
"""

import asyncio
import uuid
from typing import Dict, Any, List, Callable, Optional, Set
from datetime import datetime
from collections import defaultdict

from pydantic import BaseModel, Field
from loguru import logger

from models.notion_db_models import AgentCommunication


class AgentMessage(BaseModel):
    """
    Message format for agent communication.
    All agent messages are stored in Notion for traceability.
    """
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    priority: str = "normal"  # Options: low, normal, high, critical
    requires_response: bool = False
    response_to: Optional[str] = None  # message_id this is responding to
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MessageBus:
    """
    Simple message bus for agent communication.
    Ensures all agent communications are synchronized with Notion as the central hub.
    """
    
    def __init__(self, notion_service=None):
        """
        Initialize the message bus.
        
        Args:
            notion_service: Optional NotionService instance for message persistence
        """
        self.subscribers = defaultdict(list)
        self.message_history: List[AgentMessage] = []
        self.notion_service = notion_service
        self.active_topics: Set[str] = set()
        
        # Initialize logger
        self.logger = logger.bind(component="MessageBus")
        self.logger.info("Message bus initialized")
    
    async def publish(self, message: AgentMessage) -> str:
        """
        Publish a message to subscribers.
        
        Args:
            message: The message to publish
            
        Returns:
            The message ID
        """
        # Add to message history
        self.message_history.append(message)
        
        # Log the message
        self.logger.info(
            f"Message published: {message.message_type} from {message.sender} to {message.recipient}"
        )
        
        # Store in Notion for traceability if notion_service is available
        if self.notion_service:
            await self.store_in_notion(message)
        
        # Deliver to specific recipient
        if message.recipient in self.subscribers:
            delivery_tasks = []
            for callback in self.subscribers[message.recipient]:
                delivery_tasks.append(self._safe_deliver(callback, message))
            
            if delivery_tasks:
                await asyncio.gather(*delivery_tasks)
        
        # Also deliver to "all" subscribers
        all_delivery_tasks = []
        for callback in self.subscribers.get("all", []):
            all_delivery_tasks.append(self._safe_deliver(callback, message))
        
        if all_delivery_tasks:
            await asyncio.gather(*all_delivery_tasks)
        
        return message.message_id
    
    async def _safe_deliver(self, callback: Callable, message: AgentMessage):
        """
        Safely deliver a message to a callback, catching exceptions.
        
        Args:
            callback: The callback function to call
            message: The message to deliver
        """
        try:
            await callback(message)
        except Exception as e:
            self.logger.error(f"Error delivering message to subscriber: {e}")
    
    def subscribe(self, agent_id: str, callback: Callable):
        """
        Subscribe to messages for a specific agent.
        
        Args:
            agent_id: The agent ID to subscribe to
            callback: Async callback function that takes an AgentMessage
        """
        self.subscribers[agent_id].append(callback)
        self.logger.info(f"Agent {agent_id} subscribed to message bus")
    
    def unsubscribe(self, agent_id: str, callback: Optional[Callable] = None):
        """
        Unsubscribe from messages.
        
        Args:
            agent_id: The agent ID to unsubscribe
            callback: Specific callback to remove, or None to remove all
        """
        if callback is None:
            # Remove all callbacks for this agent
            self.subscribers[agent_id] = []
            self.logger.info(f"Agent {agent_id} unsubscribed from all messages")
        else:
            # Remove specific callback
            if agent_id in self.subscribers:
                try:
                    self.subscribers[agent_id].remove(callback)
                    self.logger.info(f"Agent {agent_id} unsubscribed specific callback")
                except ValueError:
                    self.logger.warning(f"Callback not found for agent {agent_id}")
    
    async def store_in_notion(self, message: AgentMessage):
        """
        Store message in Notion for traceability.
        
        Args:
            message: The message to store
        """
        try:
            # Convert to AgentCommunication model
            agent_comm = AgentCommunication(
                message_id=message.message_id,
                sender=message.sender,
                recipient=message.recipient,
                message_type=message.message_type,
                content=message.payload,
                timestamp=message.timestamp,
                priority=message.priority,
                requires_response=message.requires_response,
                response_to=message.response_to
            )
            
            # Create page in Notion
            await self.notion_service.create_page(agent_comm)
            
            self.logger.debug(f"Message {message.message_id} stored in Notion")
        except Exception as e:
            self.logger.error(f"Error storing message in Notion: {e}")
    
    def get_message_history(self, limit: int = 100) -> List[AgentMessage]:
        """
        Get recent message history.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of recent messages
        """
        return self.message_history[-limit:]
    
    async def request_response(
        self, 
        sender: str,
        recipient: str,
        message_type: str,
        payload: Dict[str, Any],
        timeout: float = 30.0
    ) -> Optional[AgentMessage]:
        """
        Send a message and wait for a response.
        
        Args:
            sender: Sender agent ID
            recipient: Recipient agent ID
            message_type: Type of message
            payload: Message payload
            timeout: Timeout in seconds
            
        Returns:
            Response message or None if timed out
        """
        # Create a future to wait for the response
        response_future = asyncio.Future()
        
        # Create the message
        message = AgentMessage(
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            requires_response=True
        )
        
        # Create a callback to handle the response
        async def response_handler(response_msg: AgentMessage):
            if response_msg.response_to == message.message_id:
                if not response_future.done():
                    response_future.set_result(response_msg)
        
        # Subscribe to responses
        self.subscribe(sender, response_handler)
        
        try:
            # Publish the message
            await self.publish(message)
            
            # Wait for response with timeout
            return await asyncio.wait_for(response_future, timeout)
        except asyncio.TimeoutError:
            self.logger.warning(
                f"Timeout waiting for response to message {message.message_id}"
            )
            return None
        finally:
            # Unsubscribe the response handler
            self.unsubscribe(sender, response_handler)
