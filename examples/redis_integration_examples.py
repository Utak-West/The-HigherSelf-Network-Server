"""
Redis Integration Examples for HigherSelf Network Server.

This module demonstrates practical Redis usage patterns
for the HigherSelf Network's specific use cases.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger

from services.redis_service import redis_service


class HigherSelfRedisExamples:
    """Examples of Redis integration patterns for HigherSelf Network."""

    def __init__(self):
        self.redis = redis_service

    # ================================================================
    # 1. API RESPONSE CACHING
    # ================================================================

    def cache_notion_response(
        self, database_id: str, response_data: Dict[str, Any], ttl: int = 300
    ):
        """
        Cache Notion API response for faster subsequent requests.

        Args:
            database_id: Notion database identifier
            response_data: API response to cache
            ttl: Time to live in seconds (default: 5 minutes)
        """
        cache_key = f"notion:database:{database_id}"

        # Add metadata to cached response
        cached_data = {
            "data": response_data,
            "cached_at": datetime.now().isoformat(),
            "ttl": ttl,
        }

        self.redis.set(cache_key, cached_data, ex=ttl)
        logger.info(f"Cached Notion response for database {database_id}")

    def get_cached_notion_response(self, database_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached Notion API response.

        Args:
            database_id: Notion database identifier

        Returns:
            Cached response data or None if not found/expired
        """
        cache_key = f"notion:database:{database_id}"
        cached_data = self.redis.get(cache_key, as_json=True)

        if cached_data:
            logger.info(f"Cache hit for Notion database {database_id}")
            return cached_data["data"]

        logger.info(f"Cache miss for Notion database {database_id}")
        return None

    def cache_business_entity(self, entity_id: str, entity_data: Dict[str, Any]):
        """
        Cache business entity data with hierarchical keys.

        Args:
            entity_id: Business entity identifier
            entity_data: Entity data to cache
        """
        # Cache full entity data
        entity_key = f"business_entity:{entity_id}"
        self.redis.hset(entity_key, "data", entity_data)
        self.redis.hset(entity_key, "last_updated", datetime.now().isoformat())
        self.redis.expire(entity_key, 3600)  # 1 hour

        # Cache searchable fields
        if "name" in entity_data:
            name_key = f"business_entity:name:{entity_data['name'].lower()}"
            self.redis.set(name_key, entity_id, ex=3600)

        if "type" in entity_data:
            type_key = f"business_entity:type:{entity_data['type']}"
            self.redis.sadd(type_key, entity_id)
            self.redis.expire(type_key, 3600)

    # ================================================================
    # 2. AGENT COMMUNICATION
    # ================================================================

    async def send_agent_message(
        self, from_agent: str, to_agent: str, message_type: str, payload: Dict[str, Any]
    ):
        """
        Send message between named agents using Redis pub/sub.

        Args:
            from_agent: Source agent identifier
            to_agent: Target agent identifier (or "all" for broadcast)
            message_type: Type of message
            payload: Message payload
        """
        message = {
            "id": f"msg_{datetime.now().timestamp()}",
            "from": from_agent,
            "to": to_agent,
            "type": message_type,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
        }

        # Determine channel based on target
        if to_agent == "all":
            channel = "higherself:agents:broadcast"
        else:
            channel = f"higherself:agents:{to_agent}"

        # Publish message
        subscribers = await self.redis.async_publish(channel, message)
        logger.info(
            f"Sent {message_type} from {from_agent} to {to_agent} ({subscribers} subscribers)"
        )

        # Store message history
        history_key = f"agent_messages:{from_agent}:{to_agent}"
        self.redis.lpush(history_key, message)
        self.redis.ltrim(history_key, 0, 99)  # Keep last 100 messages
        self.redis.expire(history_key, 86400)  # 24 hours

    async def listen_for_agent_messages(self, agent_id: str, callback):
        """
        Listen for messages directed to a specific agent.

        Args:
            agent_id: Agent identifier to listen for
            callback: Function to handle received messages
        """
        channels = [f"higherself:agents:{agent_id}", "higherself:agents:broadcast"]

        for channel in channels:
            pubsub = await self.redis.subscribe(channel)
            asyncio.create_task(self.redis.listen(pubsub, callback))
            logger.info(f"Agent {agent_id} listening on channel {channel}")

    def get_agent_message_history(
        self, from_agent: str, to_agent: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve message history between agents.

        Args:
            from_agent: Source agent identifier
            to_agent: Target agent identifier
            limit: Maximum number of messages to retrieve

        Returns:
            List of messages
        """
        history_key = f"agent_messages:{from_agent}:{to_agent}"
        messages = self.redis.lrange(history_key, 0, limit - 1)

        return [json.loads(msg) if isinstance(msg, str) else msg for msg in messages]

    # ================================================================
    # 3. SESSION MANAGEMENT
    # ================================================================

    def create_user_session(
        self, user_id: str, session_data: Dict[str, Any], ttl: int = 3600
    ):
        """
        Create and store user session data.

        Args:
            user_id: User identifier
            session_data: Session data to store
            ttl: Session timeout in seconds (default: 1 hour)
        """
        session_id = f"sess_{user_id}_{datetime.now().timestamp()}"
        session_key = f"session:{session_id}"

        # Store session data
        full_session_data = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            **session_data,
        }

        self.redis.hset(session_key, "data", full_session_data)
        self.redis.expire(session_key, ttl)

        # Index by user ID
        user_sessions_key = f"user_sessions:{user_id}"
        self.redis.sadd(user_sessions_key, session_id)
        self.redis.expire(user_sessions_key, ttl)

        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id

    def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user session data.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found/expired
        """
        session_key = f"session:{session_id}"
        session_data = self.redis.hget(session_key, "data", as_json=True)

        if session_data:
            # Update last activity
            session_data["last_activity"] = datetime.now().isoformat()
            self.redis.hset(session_key, "data", session_data)

        return session_data

    def invalidate_user_session(self, session_id: str):
        """
        Invalidate a user session.

        Args:
            session_id: Session identifier to invalidate
        """
        session_key = f"session:{session_id}"

        # Get user ID before deletion
        session_data = self.redis.hget(session_key, "data", as_json=True)
        if session_data and "user_id" in session_data:
            user_sessions_key = f"user_sessions:{session_data['user_id']}"
            self.redis.srem(user_sessions_key, session_id)

        # Delete session
        self.redis.delete(session_key)
        logger.info(f"Invalidated session {session_id}")

    # ================================================================
    # 4. RATE LIMITING
    # ================================================================

    def check_rate_limit(
        self, identifier: str, limit: int, window: int = 3600
    ) -> Dict[str, Any]:
        """
        Check and enforce rate limiting.

        Args:
            identifier: Unique identifier (user_id, IP, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds (default: 1 hour)

        Returns:
            Rate limit status information
        """
        rate_key = f"rate_limit:{identifier}"

        # Get current count
        current_count = self.redis.get(rate_key)
        if current_count is None:
            current_count = 0
        else:
            current_count = int(current_count)

        # Check if limit exceeded
        if current_count >= limit:
            ttl = self.redis.ttl(rate_key)
            return {
                "allowed": False,
                "current_count": current_count,
                "limit": limit,
                "reset_in": ttl,
                "retry_after": ttl,
            }

        # Increment counter
        new_count = self.redis.incr(rate_key)
        if new_count == 1:
            self.redis.expire(rate_key, window)

        return {
            "allowed": True,
            "current_count": new_count,
            "limit": limit,
            "remaining": limit - new_count,
            "reset_in": self.redis.ttl(rate_key),
        }

    # ================================================================
    # 5. TASK QUEUES AND WORKFLOWS
    # ================================================================

    def queue_background_task(
        self, task_type: str, parameters: Dict[str, Any], priority: str = "normal"
    ):
        """
        Queue a background task for processing.

        Args:
            task_type: Type of task to execute
            parameters: Task parameters
            priority: Task priority (high, normal, low)
        """
        task_data = {
            "id": f"task_{datetime.now().timestamp()}",
            "type": task_type,
            "parameters": parameters,
            "priority": priority,
            "queued_at": datetime.now().isoformat(),
            "status": "queued",
        }

        # Queue based on priority
        queue_name = f"queue:tasks:{priority}"
        self.redis.lpush(queue_name, task_data)

        # Track task
        task_key = f"task:{task_data['id']}"
        self.redis.hset(task_key, "data", task_data)
        self.redis.expire(task_key, 86400)  # 24 hours

        logger.info(f"Queued {task_type} task with priority {priority}")
        return task_data["id"]

    def get_next_task(
        self, priority: str = "normal", timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Get next task from queue.

        Args:
            priority: Queue priority to check
            timeout: Blocking timeout in seconds

        Returns:
            Task data or None if timeout
        """
        queue_name = f"queue:tasks:{priority}"
        result = self.redis.brpop(queue_name, timeout=timeout)

        if result:
            _, task_json = result
            task_data = (
                json.loads(task_json) if isinstance(task_json, str) else task_json
            )

            # Update task status
            task_key = f"task:{task_data['id']}"
            task_data["status"] = "processing"
            task_data["started_at"] = datetime.now().isoformat()
            self.redis.hset(task_key, "data", task_data)

            return task_data

        return None

    def complete_task(self, task_id: str, result: Dict[str, Any]):
        """
        Mark task as completed with result.

        Args:
            task_id: Task identifier
            result: Task execution result
        """
        task_key = f"task:{task_id}"
        task_data = self.redis.hget(task_key, "data", as_json=True)

        if task_data:
            task_data["status"] = "completed"
            task_data["completed_at"] = datetime.now().isoformat()
            task_data["result"] = result

            self.redis.hset(task_key, "data", task_data)
            logger.info(f"Completed task {task_id}")

    # ================================================================
    # 6. REAL-TIME NOTIFICATIONS
    # ================================================================

    async def send_notification(
        self, user_id: str, notification_type: str, data: Dict[str, Any]
    ):
        """
        Send real-time notification to user.

        Args:
            user_id: Target user identifier
            notification_type: Type of notification
            data: Notification data
        """
        notification = {
            "id": f"notif_{datetime.now().timestamp()}",
            "user_id": user_id,
            "type": notification_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        # Send via pub/sub
        channel = f"notifications:{user_id}"
        await self.redis.async_publish(channel, notification)

        # Store for offline retrieval
        notifications_key = f"user_notifications:{user_id}"
        self.redis.lpush(notifications_key, notification)
        self.redis.ltrim(notifications_key, 0, 49)  # Keep last 50
        self.redis.expire(notifications_key, 604800)  # 7 days

    def get_user_notifications(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get user notifications.

        Args:
            user_id: User identifier
            limit: Maximum notifications to retrieve

        Returns:
            List of notifications
        """
        notifications_key = f"user_notifications:{user_id}"
        notifications = self.redis.lrange(notifications_key, 0, limit - 1)

        return [
            json.loads(notif) if isinstance(notif, str) else notif
            for notif in notifications
        ]


# ================================================================
# USAGE EXAMPLES
# ================================================================


async def main():
    """Demonstrate Redis integration examples."""
    examples = HigherSelfRedisExamples()

    # Example 1: Cache business entity
    entity_data = {
        "id": "entity_123",
        "name": "Adiya Wellness",
        "type": "wellness_center",
        "status": "active",
    }
    examples.cache_business_entity("entity_123", entity_data)

    # Example 2: Agent communication
    await examples.send_agent_message(
        from_agent="grace_fields",
        to_agent="all",
        message_type="training_update",
        payload={"topic": "redis_integration", "status": "completed"},
    )

    # Example 3: Rate limiting
    rate_status = examples.check_rate_limit("user_123", limit=100, window=3600)
    print(f"Rate limit status: {rate_status}")

    # Example 4: Queue background task
    task_id = examples.queue_background_task(
        task_type="sync_notion_data",
        parameters={"database_id": "notion_db_123"},
        priority="high",
    )
    print(f"Queued task: {task_id}")


if __name__ == "__main__":
    asyncio.run(main())
