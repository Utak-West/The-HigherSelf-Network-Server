"""
Redis Service for Higher Self Network Server.
Provides connection management and Redis operations for caching, pub/sub, and more.
"""

import os
import json
from typing import Any, Dict, List, Optional, Union, Callable
import redis.asyncio as aioredis
from redis import Redis
from redis.exceptions import ConnectionError, RedisError
from loguru import logger
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

class RedisService:
    """Service to interact with Redis for caching and messaging."""
    
    _instance = None
    _sync_client = None
    _async_client = None
    _pubsub = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance of the service exists."""
        if cls._instance is None:
            cls._instance = super(RedisService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Redis connections."""
        try:
            redis_uri = os.environ.get("REDIS_URI", "redis://localhost:6379/0")
            
            # For synchronous operations
            self._sync_client = Redis.from_url(redis_uri, decode_responses=True)
            
            # Test connection
            self._sync_client.ping()
            logger.info(f"Connected to Redis at {redis_uri}")
            
            # For async operations (lazy initialized when needed)
            self._async_client = None
        except (ConnectionError, RedisError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def get_async_client(self) -> aioredis.Redis:
        """Get or create async Redis client."""
        if self._async_client is None:
            redis_uri = os.environ.get("REDIS_URI", "redis://localhost:6379/0")
            self._async_client = await aioredis.from_url(
                redis_uri, decode_responses=True
            )
            # Test connection
            await self._async_client.ping()
        return self._async_client
    
    # Synchronous operations
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a key with a value and optional expiration time in seconds."""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return self._sync_client.set(key, value, ex=ex)
    
    def get(self, key: str, as_json: bool = False) -> Any:
        """Get a value by key, with option to parse as JSON."""
        value = self._sync_client.get(key)
        if value and as_json:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse Redis value as JSON: {value}")
                return value
        return value
    
    def delete(self, key: str) -> int:
        """Delete a key and return the number of keys removed."""
        return self._sync_client.delete(key)
    
    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return bool(self._sync_client.exists(key))
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set a key's time to live in seconds."""
        return bool(self._sync_client.expire(key, seconds))
    
    def ttl(self, key: str) -> int:
        """Get the time to live for a key in seconds."""
        return self._sync_client.ttl(key)
    
    def incr(self, key: str, amount: int = 1) -> int:
        """Increment the value of a key by the given amount."""
        return self._sync_client.incr(key, amount)
    
    def decr(self, key: str, amount: int = 1) -> int:
        """Decrement the value of a key by the given amount."""
        return self._sync_client.decr(key, amount)
    
    def hset(self, name: str, key: str, value: Any) -> int:
        """Set a hash field to a value."""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return self._sync_client.hset(name, key, value)
    
    def hget(self, name: str, key: str, as_json: bool = False) -> Any:
        """Get the value of a hash field."""
        value = self._sync_client.hget(name, key)
        if value and as_json:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse Redis hash value as JSON: {value}")
                return value
        return value
    
    def hgetall(self, name: str) -> Dict[str, str]:
        """Get all the fields and values in a hash."""
        return self._sync_client.hgetall(name)
    
    def hdel(self, name: str, *keys) -> int:
        """Delete one or more hash fields."""
        return self._sync_client.hdel(name, *keys)
    
    def publish(self, channel: str, message: Any) -> int:
        """Publish a message to a channel."""
        if isinstance(message, (dict, list)):
            message = json.dumps(message)
        return self._sync_client.publish(channel, message)
    
    # Asynchronous operations
    
    async def async_set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a key with a value and optional expiration time in seconds (async)."""
        client = await self.get_async_client()
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await client.set(key, value, ex=ex)
    
    async def async_get(self, key: str, as_json: bool = False) -> Any:
        """Get a value by key, with option to parse as JSON (async)."""
        client = await self.get_async_client()
        value = await client.get(key)
        if value and as_json:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse Redis value as JSON: {value}")
                return value
        return value
    
    async def async_delete(self, key: str) -> int:
        """Delete a key and return the number of keys removed (async)."""
        client = await self.get_async_client()
        return await client.delete(key)
    
    async def async_publish(self, channel: str, message: Any) -> int:
        """Publish a message to a channel (async)."""
        client = await self.get_async_client()
        if isinstance(message, (dict, list)):
            message = json.dumps(message)
        return await client.publish(channel, message)
    
    async def subscribe(self, channel: str) -> aioredis.client.PubSub:
        """Subscribe to a channel and return a pubsub instance."""
        client = await self.get_async_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub
    
    async def listen(self, pubsub: aioredis.client.PubSub, callback: Callable):
        """Listen for messages on a pubsub channel and call the callback."""
        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = message['data']
                try:
                    # Try to parse as JSON
                    data = json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    pass
                await callback(data)
    
    def close(self):
        """Close Redis connections."""
        if self._sync_client:
            self._sync_client.close()
        logger.info("Redis connections closed")
    
    async def async_close(self):
        """Close async Redis connections."""
        if self._async_client:
            await self._async_client.close()
        logger.info("Async Redis connections closed")

# For easy import and use throughout the application
redis_service = RedisService()
