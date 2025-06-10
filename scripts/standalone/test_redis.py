#!/usr/bin/env python3
"""
Test script for Redis connection in The HigherSelf Network Server.
This script tests the connection to Redis and performs basic operations.
"""

import json
import os
import sys

from dotenv import load_dotenv
from loguru import logger

# Configure logging
logger.remove()  # Remove default handler
logger.add(sys.stderr, level="INFO")
logger.add("logs/test_redis.log", rotation="10 MB", level="DEBUG")

# Import Redis service
from services.redis_service import redis_service


def test_redis_connection():
    """Test basic Redis connection and operations."""
    try:
        # Test connection
        redis_service._sync_client.ping()
        logger.info("✅ Redis connection successful")

        # Get Redis info
        info = redis_service._sync_client.info()
        logger.info(f"Redis version: {info.get('redis_version', 'unknown')}")
        logger.info(f"Redis mode: {info.get('redis_mode', 'unknown')}")

        # Test basic operations
        test_key = "test:connection"
        test_value = {"timestamp": str(os.times()), "success": True}

        # Set a value
        redis_service.set(test_key, test_value)
        logger.info(f"✅ Set value for key '{test_key}'")

        # Get the value back
        retrieved_value = redis_service.get(test_key, as_json=True)
        logger.info(f"✅ Retrieved value: {json.dumps(retrieved_value, indent=2)}")

        # Test expiration
        expiry_key = "test:expiry"
        redis_service.set(expiry_key, "This will expire", ex=5)
        ttl = redis_service.ttl(expiry_key)
        logger.info(f"✅ Set key '{expiry_key}' with TTL: {ttl} seconds")

        # Test increment/decrement
        counter_key = "test:counter"
        redis_service.set(counter_key, 10)
        incremented = redis_service.incr(counter_key, 5)
        logger.info(f"✅ Incremented counter to {incremented}")
        decremented = redis_service.decr(counter_key, 3)
        logger.info(f"✅ Decremented counter to {decremented}")

        # Test hash operations
        hash_key = "test:hash"
        redis_service.hset(hash_key, "field1", "value1")
        redis_service.hset(hash_key, "field2", {"nested": "value"})
        hash_value = redis_service.hgetall(hash_key)
        logger.info(f"✅ Hash values: {hash_value}")

        # Test health check
        health = redis_service.health_check()
        logger.info(f"✅ Health check: {health}")

        # Test metrics
        metrics = redis_service.get_metrics()
        logger.info(f"✅ Redis metrics: {json.dumps(metrics, indent=2)}")

        # Delete the test keys
        redis_service.delete(test_key)
        redis_service.delete(expiry_key)
        redis_service.delete(counter_key)
        redis_service.delete(hash_key)
        logger.info(f"✅ Deleted test keys")

        # Check if key exists (should be False)
        exists = redis_service.exists(test_key)
        logger.info(f"✅ Key '{test_key}' exists: {exists}")

        # Test pub/sub
        logger.info("Testing pub/sub functionality...")
        channel = "test:channel"
        message = {"event": "test", "data": "Hello Redis!"}
        result = redis_service.publish(channel, message)
        logger.info(
            f"✅ Published message to channel '{channel}', received by {result} subscribers"
        )

        logger.info("All Redis tests completed successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Redis test failed: {e}")
        logger.exception(e)
        return False


def main():
    """Main entry point for the script."""
    # Load environment variables
    load_dotenv()

    # Get Redis URI from environment
    redis_uri = os.environ.get("REDIS_URI", "redis://localhost:6379/0")
    logger.info(f"Testing Redis connection to: {redis_uri}")

    # Run tests
    success = test_redis_connection()

    # Exit with appropriate status code
    if success:
        logger.info("Redis connection test completed successfully")
        sys.exit(0)
    else:
        logger.error("Redis connection test failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
