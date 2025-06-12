"""
WebSocket router for real-time agent communications.
Implements secure, bidirectional communication between agents and clients.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Cookie, Depends, Query, WebSocket, WebSocketDisconnect
from loguru import logger
from starlette.websockets import WebSocketState

from models.agent_models import Agent
from services.mongodb_service import mongo_service
from services.redis_service import redis_service

router = APIRouter(prefix="/ws", tags=["WebSockets"])


class ConnectionManager:
    """
    WebSocket connection manager for agent communications.
    Follows the Agent Communication Security rules by enforcing
    authorized communication patterns.
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_connections: Dict[str, List[str]] = {}
        self.connection_info: Dict[str, Dict[str, Any]] = {}

    async def connect(
        self, websocket: WebSocket, client_id: str, agent_id: Optional[str] = None
    ):
        """
        Connect a client websocket.

        Args:
            websocket: The WebSocket connection
            client_id: Unique identifier for the client
            agent_id: Optional agent ID if this connection is associated with an agent
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket

        # Record connection info for monitoring
        self.connection_info[client_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "client_ip": websocket.client.host,
            "agent_id": agent_id,
            "last_activity": datetime.utcnow().isoformat(),
        }

        # Add to agent connections if associated with an agent
        if agent_id:
            if agent_id not in self.agent_connections:
                self.agent_connections[agent_id] = []
            self.agent_connections[agent_id].append(client_id)

            # Log for audit trail
            await mongo_service.async_insert_one(
                "agent_websocket_connections",
                {
                    "agent_id": agent_id,
                    "client_id": client_id,
                    "client_ip": websocket.client.host,
                    "connected_at": datetime.utcnow().isoformat(),
                },
            )

        logger.info(f"WebSocket connected: {client_id} (Agent: {agent_id})")

    async def disconnect(self, client_id: str):
        """
        Disconnect a client websocket.

        Args:
            client_id: The client ID to disconnect
        """
        if client_id in self.active_connections:
            # Cleanup agent connections
            for agent_id, connections in self.agent_connections.items():
                if client_id in connections:
                    connections.remove(client_id)

                    # Log disconnection for audit trail
                    await mongo_service.async_insert_one(
                        "agent_websocket_disconnections",
                        {
                            "agent_id": agent_id,
                            "client_id": client_id,
                            "connected_at": self.connection_info.get(client_id, {}).get(
                                "connected_at"
                            ),
                            "disconnected_at": datetime.utcnow().isoformat(),
                            "duration_seconds": (
                                datetime.utcnow()
                                - datetime.fromisoformat(
                                    self.connection_info.get(client_id, {}).get(
                                        "connected_at", datetime.utcnow().isoformat()
                                    )
                                )
                            ).total_seconds()
                            if self.connection_info.get(client_id, {}).get(
                                "connected_at"
                            )
                            else 0,
                        },
                    )

            # Remove from active connections
            del self.active_connections[client_id]
            if client_id in self.connection_info:
                del self.connection_info[client_id]

            logger.info(f"WebSocket disconnected: {client_id}")

    async def send_json(self, client_id: str, message: Dict[str, Any]):
        """
        Send a JSON message to a specific client.

        Args:
            client_id: The client ID to send to
            message: The message to send (will be serialized to JSON)

        Returns:
            True if sent successfully, False otherwise
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    # Update last activity
                    if client_id in self.connection_info:
                        self.connection_info[client_id][
                            "last_activity"
                        ] = datetime.utcnow().isoformat()

                    # Send the message
                    await websocket.send_json(message)
                    return True
                except Exception as e:
                    logger.error(f"Error sending WebSocket message to {client_id}: {e}")

        return False

    async def broadcast_to_agent(self, agent_id: str, message: Dict[str, Any]):
        """
        Broadcast a message to all clients connected to an agent.

        Args:
            agent_id: The agent to broadcast to
            message: The message to broadcast (will be serialized to JSON)

        Returns:
            Number of clients the message was sent to
        """
        if agent_id not in self.agent_connections:
            return 0

        sent_count = 0
        for client_id in self.agent_connections[agent_id]:
            if await self.send_json(client_id, message):
                sent_count += 1

        return sent_count

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast (will be serialized to JSON)

        Returns:
            Number of clients the message was sent to
        """
        sent_count = 0
        for client_id in list(self.active_connections.keys()):
            if await self.send_json(client_id, message):
                sent_count += 1

        return sent_count

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

    def get_agent_connection_count(self, agent_id: str) -> int:
        """Get the number of connections for a specific agent."""
        return len(self.agent_connections.get(agent_id, []))

    def get_all_connection_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all active connections."""
        return self.connection_info


# Create a single connection manager instance
manager = ConnectionManager()


async def get_agent(agent_id: str = Query(...)) -> Optional[Agent]:
    """
    Get an agent by ID for WebSocket authentication.

    Args:
        agent_id: The agent ID to retrieve

    Returns:
        The agent if found, None otherwise
    """
    # Replace this with your actual agent retrieval logic
    try:
        agent_data = await mongo_service.async_find_one(
            "agents", {"agent_id": agent_id}
        )
        if agent_data:
            # Assuming you have a way to construct an Agent model from data
            # This is just a placeholder - adjust for your agent model structure
            return Agent(**agent_data)
    except Exception as e:
        logger.error(f"Error retrieving agent {agent_id}: {e}")

    return None


@router.websocket("/agent/{agent_id}")
async def websocket_agent_endpoint(
    websocket: WebSocket,
    agent_id: str,
    client_id: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for agent communication.

    Args:
        websocket: The WebSocket connection
        agent_id: The agent ID to connect to
        client_id: Optional client identifier
    """
    # Generate a client ID if not provided
    if not client_id:
        client_id = (
            f"{agent_id}-{websocket.client.host}-{datetime.utcnow().timestamp()}"
        )

    # Get the agent (for validation)
    agent = await get_agent(agent_id)
    if not agent:
        await websocket.close(code=4004, reason=f"Agent {agent_id} not found")
        return

    # Connect the WebSocket
    await manager.connect(websocket, client_id, agent_id)

    # Subscribe to agent's Redis pubsub channel
    channel_name = f"agent_channel:{agent_id}"
    pubsub = await redis_service.subscribe(channel_name)

    # Send initial connection status
    await websocket.send_json(
        {
            "type": "connection_status",
            "status": "connected",
            "agent_id": agent_id,
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

    # Run both tasks concurrently - messages from client and from Redis
    try:
        # Listen for messages from the client
        async def receive_from_client():
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    # Validate the message structure
                    if "type" not in message:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "error": "Invalid message format, missing 'type'",
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                        continue

                    # Handle different message types
                    if message["type"] == "ping":
                        await websocket.send_json(
                            {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                        )
                    elif message["type"] == "agent_action":
                        # Process agent action request
                        # You'd typically handle this by publishing to Redis for processing by the agent
                        await redis_service.async_publish(
                            f"agent_actions:{agent_id}",
                            json.dumps(
                                {
                                    "action": message.get("action"),
                                    "params": message.get("params", {}),
                                    "client_id": client_id,
                                    "timestamp": datetime.utcnow().isoformat(),
                                }
                            ),
                        )

                        await websocket.send_json(
                            {
                                "type": "action_received",
                                "action": message.get("action"),
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                    else:
                        # Unknown message type
                        await websocket.send_json(
                            {
                                "type": "error",
                                "error": f"Unknown message type: {message['type']}",
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                except json.JSONDecodeError:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "error": "Invalid JSON format",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                except WebSocketDisconnect:
                    raise
                except Exception as e:
                    logger.error(f"Error receiving WebSocket message: {e}")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "error": "Internal server error",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

        # Forward messages from Redis pubsub to the WebSocket
        async def forward_pubsub_messages():
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        # Parse the message data
                        try:
                            data = json.loads(message["data"])
                            await websocket.send_json(data)
                        except json.JSONDecodeError:
                            # If it's not valid JSON, send as a text message
                            await websocket.send_json(
                                {
                                    "type": "message",
                                    "data": message["data"],
                                    "timestamp": datetime.utcnow().isoformat(),
                                }
                            )
                        except Exception as e:
                            logger.error(f"Error forwarding Redis message: {e}")
            except Exception as e:
                logger.error(f"Redis pubsub error: {e}")

        # Run both coroutines concurrently
        await asyncio.gather(receive_from_client(), forward_pubsub_messages())

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
    finally:
        # Clean up resources
        await manager.disconnect(client_id)
        if pubsub:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()


@router.websocket("/workflow/{workflow_id}")
async def websocket_workflow_endpoint(
    websocket: WebSocket,
    workflow_id: str,
    client_id: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for workflow state updates.

    Args:
        websocket: The WebSocket connection
        workflow_id: The workflow ID to connect to
        client_id: Optional client identifier
    """
    # Generate a client ID if not provided
    if not client_id:
        client_id = f"workflow-{workflow_id}-{websocket.client.host}-{datetime.utcnow().timestamp()}"

    # Verify workflow exists
    workflow = await mongo_service.async_find_one(
        "workflows", {"workflow_id": workflow_id}
    )
    if not workflow:
        await websocket.close(code=4004, reason=f"Workflow {workflow_id} not found")
        return

    # Connect the WebSocket (without agent association)
    await manager.connect(websocket, client_id)

    # Subscribe to workflow's Redis pubsub channel
    channel_name = f"workflow_channel:{workflow_id}"
    pubsub = await redis_service.subscribe(channel_name)

    # Send initial connection status
    await websocket.send_json(
        {
            "type": "connection_status",
            "status": "connected",
            "workflow_id": workflow_id,
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_state": workflow.get("current_state", "unknown"),
        }
    )

    try:
        # Forward messages from Redis pubsub to the WebSocket
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                except json.JSONDecodeError:
                    # If it's not valid JSON, send as a text message
                    await websocket.send_json(
                        {
                            "type": "message",
                            "data": message["data"],
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                except Exception as e:
                    logger.error(f"Error forwarding Redis message: {e}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
    finally:
        # Clean up resources
        await manager.disconnect(client_id)
        if pubsub:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()


@router.websocket("/system")
async def websocket_system_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for system-wide notifications.

    Args:
        websocket: The WebSocket connection
        client_id: Optional client identifier
    """
    # Generate a client ID if not provided
    if not client_id:
        client_id = f"system-{websocket.client.host}-{datetime.utcnow().timestamp()}"

    # Connect the WebSocket (without agent association)
    await manager.connect(websocket, client_id)

    # Subscribe to system notifications channel
    channel_name = "system_notifications"
    pubsub = await redis_service.subscribe(channel_name)

    # Send initial connection status
    await websocket.send_json(
        {
            "type": "connection_status",
            "status": "connected",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

    try:
        # Forward messages from Redis pubsub to the WebSocket
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                except json.JSONDecodeError:
                    # If it's not valid JSON, send as a text message
                    await websocket.send_json(
                        {
                            "type": "message",
                            "data": message["data"],
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                except Exception as e:
                    logger.error(f"Error forwarding Redis message: {e}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
    finally:
        # Clean up resources
        await manager.disconnect(client_id)
        if pubsub:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()


# Administrative endpoints


@router.get("/connections")
async def get_connection_info():
    """Get information about all active WebSocket connections."""
    return {
        "total_connections": manager.get_connection_count(),
        "connections": manager.get_all_connection_info(),
    }


@router.post("/broadcast")
async def broadcast_message(message: Dict[str, Any]):
    """
    Broadcast a message to all connected clients.

    Args:
        message: The message to broadcast
    """
    sent_count = await manager.broadcast_to_all(
        {**message, "timestamp": datetime.utcnow().isoformat(), "broadcast": True}
    )

    return {
        "success": True,
        "sent_to": sent_count,
        "total_connections": manager.get_connection_count(),
    }
