"""Message bus for agent communication in The HigherSelf Network Server.

This module provides a simple message bus for inter-agent communication,
with support for Notion as the central hub for message storage and tracing.
Features include pub/sub messaging, request-response patterns, message
history tracking, and asynchronous delivery with error handling.
"""

import asyncio
import uuid
from collections import defaultdict
from datetime import datetime
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    TypeVar,
    Union,
)

from pydantic import BaseModel, Field

# Try to import loguru, but provide a fallback if not available
try:
    from loguru import logger
except ImportError:
    import logging

    # Create a compatible logger that mimics loguru's interface
    class CompatLogger:
        def __init__(self, name):
            self._logger = logging.getLogger(name)

        def info(self, message):
            self._logger.info(message)

        def warning(self, message):
            self._logger.warning(message)

        def error(self, message):
            self._logger.error(message)

        def debug(self, message):
            self._logger.debug(message)

        def bind(self, **kwargs):
            """Create a logger with bound context values."""
            return self

    logger = CompatLogger(__name__)

from models.notion_db_models import AgentCommunication

# Type definition for message callback functions
MessageCallback = Callable[[Any], Awaitable[None]]
T = TypeVar("T")


class AgentMessage(BaseModel):
    """Message format for agent communication.

    Standardized message format for all agent communications within the system.
    Messages are structured to support traceability, request-response patterns,
    and priority-based handling.

    Attributes:
        message_id: Unique identifier for the message
        sender: ID of the sending agent
        recipient: ID of the receiving agent (or "broadcast" for all)
        message_type: Type of message (e.g., "task", "notification", "query")
        payload: Dictionary containing the actual message content
        timestamp: When the message was created
        priority: Message priority (low, normal, high, critical)
        requires_response: Whether this message expects a response
        response_to: ID of the message this is responding to (if applicable)
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
        """Pydantic configuration for the AgentMessage model."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class MessageBus:
    """Simple message bus for agent communication.

    Provides a centralized communication system for agents to exchange messages
    using a publish-subscribe pattern. All communications can be synchronized
    with Notion as the central hub for traceability and persistence.

    Features:
    - Asynchronous publish-subscribe messaging
    - Request-response pattern with timeout
    - Message history tracking
    - Notion integration for persistent message storage
    - Error handling for delivery failures
    """

    def __init__(self, notion_service=None):
        """Initialize the message bus.

        Args:
            notion_service: Optional NotionService instance for message persistence.
                If provided, all messages will be stored in Notion.
        """
        self.subscribers: Dict[str, List[MessageCallback]] = defaultdict(list)
        self.message_history: List[AgentMessage] = []
        self.notion_service = notion_service
        self.active_topics: Set[str] = set()

        # Initialize logger
        self.logger = logger.bind(component="MessageBus")
        self.logger.info("Message bus initialized")

    async def publish(self, message: AgentMessage) -> str:
        """Publish a message to subscribers.

        Sends a message to the appropriate subscribers based on the recipient.
        If the message is addressed to "broadcast", it will be sent to all
        subscribers. The message is also stored in the message history and
        optionally in Notion for traceability.

        Args:
            message: The message to publish containing sender, recipient,
                    message type, and payload

        Returns:
            str: The message ID for tracking and referencing
        """
        # Add to message history
        self.message_history.append(message)

        # Log the message
        self.logger.info(
            f"Message published: {message.message_type} from {message.sender} to {message.recipient}"
        )

        # Store in Notion for traceability if notion_service is available
        if self.notion_service:
            try:
                await self.store_in_notion(message)
            except Exception as e:
                self.logger.error(f"Failed to store message in Notion: {e}")
                # Continue with delivery even if Notion storage fails

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

    async def _safe_deliver(
        self, callback: MessageCallback, message: AgentMessage
    ) -> None:
        """Safely deliver a message to a callback, catching exceptions.

        Executes the subscriber's callback function with the message,
        catching and logging any exceptions that occur during delivery.
        This ensures that failures in one subscriber don't affect others.

        Args:
            callback: The callback function to call with the message
            message: The message to deliver to the subscriber
        """
        try:
            await callback(message)
        except Exception as e:
            self.logger.error(f"Error delivering message to subscriber: {e}")

    def subscribe(self, agent_id: str, callback: MessageCallback) -> None:
        """Subscribe to messages for a specific agent.

        Registers a callback function to be called when messages are
        published for the specified agent ID. Use "all" as the agent_id
        to receive all messages regardless of recipient.

        Args:
            agent_id: The agent ID to subscribe to, or "all" for all messages
            callback: Async callback function that takes an AgentMessage parameter
        """
        self.subscribers[agent_id].append(callback)
        self.logger.info(f"Agent {agent_id} subscribed to message bus")

    def unsubscribe(
        self, agent_id: str, callback: Optional[MessageCallback] = None
    ) -> None:
        """Unsubscribe from messages.

        Removes a callback function from the list of subscribers for the
        specified agent ID. If no callback is provided, all subscriptions
        for that agent ID are removed.

        Args:
            agent_id: The agent ID to unsubscribe from
            callback: Specific callback to remove, or None to remove all
                     subscriptions for this agent
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

    async def store_in_notion(self, message: AgentMessage) -> None:
        """Store message in Notion for traceability.

        Converts the AgentMessage to a Notion-compatible AgentCommunication model
        and creates a record in the appropriate Notion database. This provides
        a persistent, auditable log of all agent communications.

        Args:
            message: The AgentMessage to store in Notion

        Raises:
            Exception: If storing in Notion fails (e.g., API error)
        """
        # Verify notion_service is available
        if not self.notion_service:
            self.logger.warning("Cannot store message: Notion service not configured")
            return

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
                response_to=message.response_to,
            )

            # Create page in Notion
            await self.notion_service.create_page(agent_comm)

            self.logger.debug(f"Message {message.message_id} stored in Notion")
        except Exception as e:
            self.logger.error(f"Error storing message in Notion: {e}")

    def get_message_history(
        self,
        limit: int = 100,
        agent_id: Optional[str] = None,
        message_type: Optional[str] = None,
    ) -> List[AgentMessage]:
        """Get recent message history with optional filtering.

        Retrieves recent messages from the in-memory history, with options
        to filter by agent ID and/or message type. Returns the most recent
        messages first, up to the specified limit.

        Args:
            limit: Maximum number of messages to return
            agent_id: Optional agent ID to filter by (as sender or recipient)
            message_type: Optional message type to filter by

        Returns:
            List[AgentMessage]: List of matching messages, newest first
        """
        # Start with complete message history
        messages = self.message_history

        # Apply filters if provided
        if agent_id:
            messages = [
                m for m in messages if m.sender == agent_id or m.recipient == agent_id
            ]

        if message_type:
            messages = [m for m in messages if m.message_type == message_type]

        # Return the most recent messages up to the limit
        return self.message_history[-limit:]

    async def request_response(
        self,
        sender: str,
        recipient: str,
        message_type: str,
        payload: Dict[str, Any],
        timeout: float = 30.0,
        priority: str = "normal",
    ) -> Optional[AgentMessage]:
        """Send a message and wait for a response.

        Implements a request-response pattern by sending a message that requires
        a response and waiting for that response with a timeout. This is useful
        for synchronous interactions between agents.

        Args:
            sender: Sender agent ID
            recipient: Recipient agent ID
            message_type: Type of message (e.g., "query", "command")
            payload: Message payload containing the request data
            timeout: Maximum time to wait for response in seconds
            priority: Message priority (low, normal, high, critical)

        Returns:
            Optional[AgentMessage]: Response message if received within timeout,
                                  None if timed out
        """
        # Create a future to wait for the response
        response_future = asyncio.Future()

        # Create the message
        message = AgentMessage(
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            requires_response=True,
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
