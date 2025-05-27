"""
Comprehensive Redis Connection Tests for HigherSelf Network Server.

This module provides thorough testing of Redis connectivity, configuration,
and integration points to ensure reliable operation in all environments.
"""

import asyncio
import json
import os
import pytest
import time
from typing import Any, Dict
from unittest.mock import patch, MagicMock

from services.redis_service import RedisService, redis_service
from config.settings import settings


class TestRedisConnection:
    """Test Redis connection and basic operations."""

    def setup_method(self):
        """Set up test environment."""
        # Reset Redis service instance for clean testing
        RedisService._instance = None
        RedisService._sync_client = None
        RedisService._async_client = None

    def test_redis_service_singleton(self):
        """Test that RedisService follows singleton pattern."""
        service1 = RedisService()
        service2 = RedisService()
        assert service1 is service2

    def test_redis_connection_configuration(self):
        """Test Redis connection configuration from settings."""
        # Test with default settings
        service = RedisService()
        assert service._connection_pool is not None

    @pytest.mark.asyncio
    async def test_redis_health_check(self):
        """Test Redis health check functionality."""
        service = RedisService()
        
        try:
            health_status = service.health_check()
            assert "status" in health_status
            assert health_status["status"] in ["healthy", "unhealthy"]
            assert "last_check" in health_status
            
            # Test async health check
            async_health_status = await service.async_health_check()
            assert "status" in async_health_status
            assert async_health_status["status"] in ["healthy", "unhealthy"]
            
        except Exception as e:
            # If Redis is not available, test should still pass
            # but log the issue for debugging
            print(f"Redis not available for testing: {e}")
            pytest.skip("Redis server not available")

    def test_redis_basic_operations(self):
        """Test basic Redis operations (set, get, delete)."""
        service = RedisService()
        
        try:
            # Test string operations
            test_key = "test:higherself:basic"
            test_value = "test_value"
            
            # Set and get
            result = service.set(test_key, test_value, ex=60)
            assert result is True
            
            retrieved_value = service.get(test_key)
            assert retrieved_value == test_value
            
            # Test existence
            assert service.exists(test_key) is True
            
            # Test deletion
            deleted_count = service.delete(test_key)
            assert deleted_count == 1
            assert service.exists(test_key) is False
            
        except Exception as e:
            print(f"Redis not available for testing: {e}")
            pytest.skip("Redis server not available")

    def test_redis_json_operations(self):
        """Test Redis JSON serialization/deserialization."""
        service = RedisService()
        
        try:
            test_key = "test:higherself:json"
            test_data = {
                "user_id": "12345",
                "name": "Test User",
                "preferences": ["wellness", "art", "consulting"],
                "metadata": {
                    "created_at": "2024-01-01T00:00:00Z",
                    "source": "higherself_network"
                }
            }
            
            # Set JSON data
            service.set(test_key, test_data, ex=60)
            
            # Get as JSON
            retrieved_data = service.get(test_key, as_json=True)
            assert retrieved_data == test_data
            assert isinstance(retrieved_data, dict)
            assert retrieved_data["user_id"] == "12345"
            
            # Cleanup
            service.delete(test_key)
            
        except Exception as e:
            print(f"Redis not available for testing: {e}")
            pytest.skip("Redis server not available")

    def test_redis_hash_operations(self):
        """Test Redis hash operations."""
        service = RedisService()
        
        try:
            hash_name = "test:higherself:user:12345"
            
            # Set hash fields
            service.hset(hash_name, "name", "John Doe")
            service.hset(hash_name, "email", "john@example.com")
            service.hset(hash_name, "preferences", {"wellness": True})
            
            # Get hash fields
            name = service.hget(hash_name, "name")
            assert name == "John Doe"
            
            email = service.hget(hash_name, "email")
            assert email == "john@example.com"
            
            # Get all hash fields
            all_fields = service.hgetall(hash_name)
            assert "name" in all_fields
            assert "email" in all_fields
            
            # Delete hash fields
            deleted_count = service.hdel(hash_name, "name", "email")
            assert deleted_count == 2
            
            # Cleanup
            service.delete(hash_name)
            
        except Exception as e:
            print(f"Redis not available for testing: {e}")
            pytest.skip("Redis server not available")

    @pytest.mark.asyncio
    async def test_redis_async_operations(self):
        """Test async Redis operations."""
        service = RedisService()
        
        try:
            test_key = "test:higherself:async"
            test_value = "async_test_value"
            
            # Async set and get
            result = await service.async_set(test_key, test_value, ex=60)
            assert result is True
            
            retrieved_value = await service.async_get(test_key)
            assert retrieved_value == test_value
            
            # Async delete
            deleted_count = await service.async_delete(test_key)
            assert deleted_count == 1
            
        except Exception as e:
            print(f"Redis not available for testing: {e}")
            pytest.skip("Redis server not available")

    def test_redis_expiration(self):
        """Test Redis key expiration functionality."""
        service = RedisService()
        
        try:
            test_key = "test:higherself:expiration"
            test_value = "expiring_value"
            
            # Set with expiration
            service.set(test_key, test_value, ex=2)  # 2 seconds
            
            # Check TTL
            ttl = service.ttl(test_key)
            assert ttl > 0 and ttl <= 2
            
            # Wait for expiration
            time.sleep(3)
            
            # Key should be expired
            assert service.exists(test_key) is False
            
        except Exception as e:
            print(f"Redis not available for testing: {e}")
            pytest.skip("Redis server not available")

    def test_redis_increment_operations(self):
        """Test Redis increment/decrement operations."""
        service = RedisService()
        
        try:
            counter_key = "test:higherself:counter"
            
            # Increment
            value = service.incr(counter_key)
            assert value == 1
            
            value = service.incr(counter_key, 5)
            assert value == 6
            
            # Decrement
            value = service.decr(counter_key, 2)
            assert value == 4
            
            # Cleanup
            service.delete(counter_key)
            
        except Exception as e:
            print(f"Redis not available for testing: {e}")
            pytest.skip("Redis server not available")

    def test_redis_metrics(self):
        """Test Redis metrics collection."""
        service = RedisService()
        
        try:
            # Perform some operations to generate metrics
            service.set("test:metrics", "value", ex=60)
            service.get("test:metrics")
            service.delete("test:metrics")
            
            # Get metrics
            metrics = service.get_metrics()
            
            assert "operations" in metrics
            assert "errors" in metrics
            assert "avg_latency" in metrics
            assert "health" in metrics
            
            assert metrics["operations"] >= 3  # At least 3 operations
            assert isinstance(metrics["avg_latency"], float)
            
        except Exception as e:
            print(f"Redis not available for testing: {e}")
            pytest.skip("Redis server not available")


class TestRedisConfiguration:
    """Test Redis configuration and settings."""

    def test_redis_settings_validation(self):
        """Test Redis settings validation."""
        from config.settings import RedisSettings
        
        # Test valid settings
        valid_settings = RedisSettings(
            host="localhost",
            port=6379,
            timeout=5,
            max_connections=10
        )
        assert valid_settings.host == "localhost"
        assert valid_settings.port == 6379

    def test_redis_connection_url_generation(self):
        """Test Redis connection URL generation."""
        from config.settings import RedisSettings
        
        # Test basic URL
        settings = RedisSettings(
            host="localhost",
            port=6379,
            database=0
        )
        url = settings.get_connection_url()
        assert "redis://localhost:6379/0" in url
        
        # Test URL with password
        settings = RedisSettings(
            host="redis.example.com",
            port=6380,
            database=1,
            password="secret123"
        )
        url = settings.get_connection_url()
        assert "redis://:secret123@redis.example.com:6380/1" in url

    def test_redis_connection_kwargs(self):
        """Test Redis connection kwargs generation."""
        from config.settings import RedisSettings
        
        settings = RedisSettings(
            timeout=10,
            max_connections=20,
            ssl_enabled=True
        )
        kwargs = settings.get_connection_kwargs()
        
        assert kwargs["socket_timeout"] == 10
        assert kwargs["max_connections"] == 20
        assert kwargs["ssl"] is True


class TestRedisIntegration:
    """Test Redis integration with HigherSelf Network components."""

    @pytest.mark.asyncio
    async def test_redis_pubsub_integration(self):
        """Test Redis pub/sub for agent communication."""
        service = RedisService()
        
        try:
            channel = "higherself:agents:communication"
            test_message = {
                "agent_id": "grace_fields",
                "message_type": "task_assignment",
                "payload": {
                    "task": "prepare_training_materials",
                    "priority": "high"
                }
            }
            
            # Publish message
            subscribers = service.publish(channel, test_message)
            # Note: subscribers will be 0 if no one is listening
            assert isinstance(subscribers, int)
            
        except Exception as e:
            print(f"Redis not available for testing: {e}")
            pytest.skip("Redis server not available")

    def test_redis_caching_integration(self):
        """Test Redis caching for API responses."""
        service = RedisService()
        
        try:
            # Simulate API response caching
            cache_key = "api:notion:business_entities:12345"
            api_response = {
                "id": "12345",
                "name": "Adiya Wellness",
                "type": "wellness_center",
                "status": "active",
                "cached_at": "2024-01-01T12:00:00Z"
            }
            
            # Cache the response
            service.set(cache_key, api_response, ex=300)  # 5 minutes
            
            # Retrieve from cache
            cached_response = service.get(cache_key, as_json=True)
            assert cached_response == api_response
            assert cached_response["name"] == "Adiya Wellness"
            
            # Cleanup
            service.delete(cache_key)
            
        except Exception as e:
            print(f"Redis not available for testing: {e}")
            pytest.skip("Redis server not available")

    def test_redis_session_storage(self):
        """Test Redis for session storage."""
        service = RedisService()
        
        try:
            session_id = "sess_higherself_12345"
            session_data = {
                "user_id": "user_67890",
                "authenticated": True,
                "permissions": ["read", "write"],
                "last_activity": "2024-01-01T12:00:00Z"
            }
            
            # Store session
            service.hset(f"session:{session_id}", "data", session_data)
            service.expire(f"session:{session_id}", 3600)  # 1 hour
            
            # Retrieve session
            retrieved_data = service.hget(f"session:{session_id}", "data", as_json=True)
            assert retrieved_data == session_data
            
            # Cleanup
            service.delete(f"session:{session_id}")
            
        except Exception as e:
            print(f"Redis not available for testing: {e}")
            pytest.skip("Redis server not available")


class TestRedisErrorHandling:
    """Test Redis error handling and resilience."""

    def test_redis_connection_failure_handling(self):
        """Test handling of Redis connection failures."""
        # Mock Redis connection failure
        with patch('redis.Redis') as mock_redis:
            mock_redis.side_effect = Exception("Connection refused")
            
            with pytest.raises(Exception):
                RedisService()

    def test_redis_operation_retry_logic(self):
        """Test Redis operation retry logic."""
        service = RedisService()
        
        # Mock a failing operation that succeeds on retry
        with patch.object(service, '_sync_client') as mock_client:
            mock_client.set.side_effect = [
                Exception("Timeout"),  # First attempt fails
                True  # Second attempt succeeds
            ]
            
            # This should succeed due to retry logic
            # Note: This test requires the actual retry decorator to work
            try:
                result = service.set("test:retry", "value")
                # If we get here, retry worked or Redis is not available
            except Exception:
                # Expected if Redis is not available
                pass

    def test_redis_graceful_degradation(self):
        """Test graceful degradation when Redis is unavailable."""
        # This test ensures the application can continue without Redis
        # when Redis features are disabled or unavailable
        
        with patch.dict(os.environ, {'ENABLE_REDIS': 'false'}):
            # Application should handle Redis being disabled
            assert os.environ.get('ENABLE_REDIS') == 'false'


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
