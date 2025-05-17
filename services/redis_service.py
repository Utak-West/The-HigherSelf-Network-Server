"""
Redis Service for Higher Self Network Server.
Provides connection management and Redis operations for caching, pub/sub, and more.
Features:
- Connection pooling for better performance
- Retry logic for better reliability
- Health check functionality
- SSL/TLS support for secure connections
- Metrics for monitoring
"""

import asyncio
import json
import os
import ssl
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import redis.asyncio as aioredis
from dotenv import load_dotenv
from loguru import logger
from redis import ConnectionPool, Redis
from redis.exceptions import ConnectionError, RedisError, TimeoutError

# Load environment variables
load_dotenv()


# Define retry decorator for Redis operations
def with_retry(max_retries=3, backoff_factor=0.5):
    """Decorator to retry Redis operations with exponential backoff."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    last_exception = e
                    if attempt < max_retries:
                        sleep_time = backoff_factor * (2**attempt)
                        logger.warning(
                            f"Redis operation failed, retrying in {sleep_time:.2f}s: {e}"
                        )
                        time.sleep(sleep_time)
                    else:
                        logger.error(
                            f"Redis operation failed after {max_retries} retries: {e}"
                        )
            raise last_exception

        return wrapper

    return decorator


# Define async retry decorator
def with_async_retry(max_retries=3, backoff_factor=0.5):
    """Decorator to retry async Redis operations with exponential backoff."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    last_exception = e
                    if attempt < max_retries:
                        sleep_time = backoff_factor * (2**attempt)
                        logger.warning(
                            f"Async Redis operation failed, retrying in {sleep_time:.2f}s: {e}"
                        )
                        await asyncio.sleep(sleep_time)
                    else:
                        logger.error(
                            f"Async Redis operation failed after {max_retries} retries: {e}"
                        )
            raise last_exception

        return wrapper

    return decorator


class RedisService:
    """Service to interact with Redis for caching and messaging."""

    _instance = None
    _sync_client = None
    _async_client = None
    _pubsub = None
    _connection_pool = None
    _async_connection_pool = None
    _health_status = {"status": "unknown", "last_check": 0, "errors": []}
    _metrics = {"operations": 0, "errors": 0, "latency_sum": 0, "latency_count": 0}

    def __new__(cls):
        """Singleton pattern to ensure only one instance of the service exists."""
        if cls._instance is None:
            cls._instance = super(RedisService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize Redis connections with connection pooling."""
        try:
            redis_uri = os.environ.get("REDIS_URI", "redis://localhost:6379/0")
            redis_password = os.environ.get("REDIS_PASSWORD", "")
            redis_timeout = int(os.environ.get("REDIS_TIMEOUT", "5"))
            redis_max_connections = int(os.environ.get("REDIS_MAX_CONNECTIONS", "10"))
            redis_ssl = os.environ.get("REDIS_SSL", "false").lower() == "true"

            # Connection options
            connection_kwargs = {
                "decode_responses": True,
                "socket_timeout": redis_timeout,
                "socket_connect_timeout": redis_timeout,
                "max_connections": redis_max_connections,
                "health_check_interval": 30,  # Check connection health every 30 seconds
            }

            # Add password if provided
            if redis_password:
                connection_kwargs["password"] = redis_password
                # Mask part of the password for logging
                masked_password = (
                    f"{redis_password[:2]}***{redis_password[-2:]}"
                    if len(redis_password) > 4
                    else "***"
                )
                logger.info(
                    f"Using Redis with authentication (password: {masked_password})"
                )

            # Add SSL if enabled
            if redis_ssl:
                ssl_context = ssl.create_default_context()
                connection_kwargs["ssl"] = True
                connection_kwargs["ssl_context"] = ssl_context
                logger.info("Using SSL/TLS for Redis connection")

            # Create connection pool for better performance
            self._connection_pool = ConnectionPool.from_url(
                redis_uri, **connection_kwargs
            )
            logger.info(
                f"Created Redis connection pool with max {redis_max_connections} connections"
            )

            # For synchronous operations
            self._sync_client = Redis(connection_pool=self._connection_pool)

            # Test connection
            self._sync_client.ping()
            logger.info(f"Connected to Redis at {redis_uri}")

            # Update health status
            self._health_status = {
                "status": "healthy",
                "last_check": time.time(),
                "errors": [],
            }

            # For async operations (lazy initialized when needed)
            self._async_client = None
            self._async_connection_pool = None
        except (ConnectionError, RedisError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._health_status = {
                "status": "unhealthy",
                "last_check": time.time(),
                "errors": [str(e)],
            }
            raise

    async def get_async_client(self) -> aioredis.Redis:
        """Get or create async Redis client with connection pooling."""
        if self._async_client is None:
            redis_uri = os.environ.get("REDIS_URI", "redis://localhost:6379/0")
            redis_password = os.environ.get("REDIS_PASSWORD", "")
            redis_timeout = int(os.environ.get("REDIS_TIMEOUT", "5"))
            redis_max_connections = int(os.environ.get("REDIS_MAX_CONNECTIONS", "10"))
            redis_ssl = os.environ.get("REDIS_SSL", "false").lower() == "true"

            # Connection options
            connection_kwargs = {
                "decode_responses": True,
                "socket_timeout": redis_timeout,
                "socket_connect_timeout": redis_timeout,
                "max_connections": redis_max_connections,
                "health_check_interval": 30,  # Check connection health every 30 seconds
            }

            # Add password if provided
            if redis_password:
                connection_kwargs["password"] = redis_password

            # Add SSL if enabled
            if redis_ssl:
                ssl_context = ssl.create_default_context()
                connection_kwargs["ssl"] = True
                connection_kwargs["ssl_context"] = ssl_context

            # Create async connection pool
            self._async_client = await aioredis.from_url(redis_uri, **connection_kwargs)

            # Test connection
            await self._async_client.ping()
            logger.info("Async Redis client initialized successfully")
        return self._async_client

    @with_retry(max_retries=3)
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the Redis connection."""
        try:
            start_time = time.time()
            self._sync_client.ping()
            latency = time.time() - start_time

            self._health_status = {
                "status": "healthy",
                "last_check": time.time(),
                "latency": latency,
                "errors": [],
            }
            logger.debug(f"Redis health check successful, latency: {latency:.4f}s")
            return self._health_status
        except Exception as e:
            self._health_status = {
                "status": "unhealthy",
                "last_check": time.time(),
                "errors": [str(e)],
            }
            logger.error(f"Redis health check failed: {e}")
            return self._health_status

    async def async_health_check(self) -> Dict[str, Any]:
        """Perform an async health check on the Redis connection."""
        try:
            client = await self.get_async_client()
            start_time = time.time()
            await client.ping()
            latency = time.time() - start_time

            self._health_status = {
                "status": "healthy",
                "last_check": time.time(),
                "latency": latency,
                "errors": [],
            }
            logger.debug(
                f"Async Redis health check successful, latency: {latency:.4f}s"
            )
            return self._health_status
        except Exception as e:
            self._health_status = {
                "status": "unhealthy",
                "last_check": time.time(),
                "errors": [str(e)],
            }
            logger.error(f"Async Redis health check failed: {e}")
            return self._health_status

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
            if message["type"] == "message":
                data = message["data"]
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
