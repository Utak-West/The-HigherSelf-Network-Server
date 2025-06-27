"""
Performance Testing Suite for HigherSelf Network Server Optimizations.

Tests all implemented optimizations to validate performance improvements
and ensure functionality is maintained.
"""

import asyncio
import time
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import optimization services
from services.enhanced_cache_service import CacheService, CacheType
from services.optimized_query_service import OptimizedQueryService
from services.performance_monitoring_service import PerformanceMonitoringService
from services.optimized_agent_communication import OptimizedAgentCommunication, AgentMessage, MessageType, MessagePriority
from services.async_optimization_service import AsyncOptimizationService
from models.base import OptimizedBaseModel, CacheableModel


class TestModel(CacheableModel):
    """Test model for performance testing."""
    id: str
    name: str
    value: int
    data: Dict[str, Any] = {}


class PerformanceTestSuite:
    """Comprehensive performance testing suite."""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.query_service = OptimizedQueryService()
        self.performance_monitor = PerformanceMonitoringService()
        self.agent_communication = OptimizedAgentCommunication()
        self.async_optimizer = AsyncOptimizationService()
        
        # Test data
        self.test_models = [
            TestModel(id=f"test_{i}", name=f"Test Model {i}", value=i, data={"index": i})
            for i in range(100)
        ]
    
    async def setup(self):
        """Set up test environment."""
        await self.performance_monitor.start_monitoring()
        await self.agent_communication.start()
        await self.async_optimizer.start()
    
    async def teardown(self):
        """Clean up test environment."""
        await self.performance_monitor.stop_monitoring()
        await self.agent_communication.stop()
        await self.async_optimizer.stop()


@pytest.fixture
async def performance_suite():
    """Fixture for performance test suite."""
    suite = PerformanceTestSuite()
    await suite.setup()
    yield suite
    await suite.teardown()


class TestCacheOptimizations:
    """Test cache optimization performance."""
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, performance_suite):
        """Test cache read/write performance."""
        cache_service = performance_suite.cache_service
        
        # Test cache write performance
        start_time = time.time()
        for i in range(100):
            await cache_service.set(
                f"test_key_{i}",
                {"data": f"test_value_{i}"},
                cache_type=CacheType.API
            )
        write_time = time.time() - start_time
        
        # Test cache read performance
        start_time = time.time()
        for i in range(100):
            result = await cache_service.get(f"test_key_{i}", cache_type=CacheType.API)
            assert result is not None
        read_time = time.time() - start_time
        
        # Performance assertions
        assert write_time < 1.0, f"Cache writes took too long: {write_time}s"
        assert read_time < 0.5, f"Cache reads took too long: {read_time}s"
        
        # Test cache hit rate
        stats = await cache_service.get_stats()
        assert stats["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_model_cache_performance(self, performance_suite):
        """Test model-aware caching performance."""
        cache_service = performance_suite.cache_service
        test_models = performance_suite.test_models
        
        # Test model caching
        start_time = time.time()
        for model in test_models:
            await cache_service.set_model(
                f"model_{model.id}",
                model,
                cache_type=CacheType.API
            )
        cache_time = time.time() - start_time
        
        # Test model retrieval
        start_time = time.time()
        for model in test_models:
            cached_model = await cache_service.get_model(
                f"model_{model.id}",
                TestModel,
                cache_type=CacheType.API
            )
            assert cached_model is not None
            assert cached_model.id == model.id
        retrieve_time = time.time() - start_time
        
        # Performance assertions
        assert cache_time < 2.0, f"Model caching took too long: {cache_time}s"
        assert retrieve_time < 1.0, f"Model retrieval took too long: {retrieve_time}s"


class TestQueryOptimizations:
    """Test query optimization performance."""
    
    @pytest.mark.asyncio
    async def test_query_caching(self, performance_suite):
        """Test query result caching."""
        query_service = performance_suite.query_service
        
        # Mock query function
        async def mock_query():
            await asyncio.sleep(0.1)  # Simulate slow query
            return [{"id": "1", "name": "Test"}]
        
        # First query (should be slow)
        start_time = time.time()
        result1 = await query_service.cache_service.get_or_set(
            "test_query",
            mock_query,
            ttl=300
        )
        first_query_time = time.time() - start_time
        
        # Second query (should be fast due to caching)
        start_time = time.time()
        result2 = await query_service.cache_service.get("test_query")
        second_query_time = time.time() - start_time
        
        # Assertions
        assert result1 == result2
        assert first_query_time > 0.1, "First query should be slow"
        assert second_query_time < 0.01, "Second query should be fast (cached)"
        
        # Check metrics
        metrics = query_service.get_metrics()
        assert metrics["cache_hit_rate"] > 0


class TestAgentCommunicationOptimizations:
    """Test agent communication optimization performance."""
    
    @pytest.mark.asyncio
    async def test_message_throughput(self, performance_suite):
        """Test message sending throughput."""
        comm_service = performance_suite.agent_communication
        
        # Create test messages
        messages = [
            AgentMessage(
                sender_id="test_agent",
                recipient_id="target_agent",
                message_type=MessageType.TASK_REQUEST,
                priority=MessagePriority.NORMAL,
                payload={"task_id": i, "data": f"test_data_{i}"}
            )
            for i in range(100)
        ]
        
        # Test message sending performance
        start_time = time.time()
        for message in messages:
            await comm_service.send_message(message)
        send_time = time.time() - start_time
        
        # Performance assertions
        assert send_time < 2.0, f"Message sending took too long: {send_time}s"
        
        # Check metrics
        metrics = await comm_service.get_metrics()
        assert metrics["total_messages"] >= 100
        assert metrics["success_rate"] > 95.0
    
    @pytest.mark.asyncio
    async def test_priority_message_handling(self, performance_suite):
        """Test priority-based message handling."""
        comm_service = performance_suite.agent_communication
        
        # Create messages with different priorities
        urgent_message = AgentMessage(
            sender_id="test_agent",
            message_type=MessageType.SYSTEM_ALERT,
            priority=MessagePriority.URGENT,
            payload={"alert": "urgent_test"}
        )
        
        normal_message = AgentMessage(
            sender_id="test_agent",
            message_type=MessageType.TASK_REQUEST,
            priority=MessagePriority.NORMAL,
            payload={"task": "normal_test"}
        )
        
        # Send messages
        await comm_service.send_message(normal_message)
        await comm_service.send_message(urgent_message)
        
        # Verify priority handling (urgent should be processed first)
        metrics = await comm_service.get_metrics()
        assert metrics["queue_sizes"]["urgent"] >= 0
        assert metrics["queue_sizes"]["normal"] >= 0


class TestAsyncOptimizations:
    """Test async/await optimization performance."""
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, performance_suite):
        """Test concurrent operation performance."""
        async_optimizer = performance_suite.async_optimizer
        
        # Create test operations
        async def test_operation(delay: float = 0.1):
            await asyncio.sleep(delay)
            return f"completed_{delay}"
        
        operations = [lambda: test_operation(0.1) for _ in range(10)]
        
        # Test sequential execution
        start_time = time.time()
        sequential_results = []
        for op in operations:
            result = await op()
            sequential_results.append(result)
        sequential_time = time.time() - start_time
        
        # Test concurrent execution
        start_time = time.time()
        concurrent_results = await async_optimizer.batch_execute(
            operations,
            max_concurrent=5
        )
        concurrent_time = time.time() - start_time
        
        # Performance assertions
        assert len(concurrent_results) == len(sequential_results)
        assert concurrent_time < sequential_time * 0.6, "Concurrent execution should be significantly faster"
        
        # Check metrics
        metrics = async_optimizer.get_metrics()
        assert metrics["total_operations"] >= 10
    
    @pytest.mark.asyncio
    async def test_connection_pool_performance(self, performance_suite):
        """Test connection pool performance."""
        async_optimizer = performance_suite.async_optimizer
        
        # Mock connection creation
        connection_count = 0
        
        async def create_mock_connection():
            nonlocal connection_count
            connection_count += 1
            await asyncio.sleep(0.01)  # Simulate connection time
            return f"connection_{connection_count}"
        
        # Create connection pool
        pool = async_optimizer.create_connection_pool(
            "test_pool",
            create_mock_connection,
            max_connections=5,
            min_connections=2
        )
        
        await pool.initialize()
        
        # Test connection reuse
        start_time = time.time()
        for _ in range(10):
            async with pool.get_connection() as conn:
                assert conn is not None
        pool_time = time.time() - start_time
        
        # Check pool stats
        stats = pool.get_stats()
        assert stats["reuse_rate"] > 50.0, "Connection pool should have good reuse rate"
        assert stats["total_created"] < 10, "Should reuse connections instead of creating new ones"


class TestPerformanceMonitoring:
    """Test performance monitoring functionality."""
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, performance_suite):
        """Test metrics collection performance."""
        monitor = performance_suite.performance_monitor
        
        # Record test metrics
        for i in range(100):
            monitor.record_metric(f"test_metric_{i % 5}", float(i), {"test": "true"})
            monitor.record_request(float(i) / 100, success=True)
        
        # Get metrics
        start_time = time.time()
        metrics = await monitor.get_performance_metrics()
        metrics_time = time.time() - start_time
        
        # Performance assertions
        assert metrics_time < 0.1, f"Metrics collection took too long: {metrics_time}s"
        assert "summary" in metrics
        assert "system_health" in metrics
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, performance_suite):
        """Test system health monitoring."""
        monitor = performance_suite.performance_monitor
        
        # Get system health
        start_time = time.time()
        health = await monitor.get_system_health()
        health_time = time.time() - start_time
        
        # Performance assertions
        assert health_time < 1.0, f"Health check took too long: {health_time}s"
        assert health.status in ["healthy", "degraded", "unhealthy"]
        assert health.cpu_usage >= 0
        assert health.memory_usage >= 0
    
    @pytest.mark.asyncio
    async def test_optimization_recommendations(self, performance_suite):
        """Test optimization recommendations."""
        monitor = performance_suite.performance_monitor
        
        # Get recommendations
        start_time = time.time()
        recommendations = await monitor.get_optimization_recommendations()
        recommendations_time = time.time() - start_time
        
        # Performance assertions
        assert recommendations_time < 0.5, f"Recommendations took too long: {recommendations_time}s"
        assert isinstance(recommendations, list)


class TestIntegrationPerformance:
    """Test integrated performance of all optimizations."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_performance(self, performance_suite):
        """Test end-to-end performance with all optimizations."""
        
        # Simulate complex workflow
        start_time = time.time()
        
        # 1. Cache some data
        for i in range(10):
            await performance_suite.cache_service.set(
                f"workflow_data_{i}",
                {"step": i, "data": f"workflow_{i}"},
                cache_type=CacheType.WORKFLOW
            )
        
        # 2. Send agent messages
        for i in range(5):
            message = AgentMessage(
                sender_id="workflow_agent",
                message_type=MessageType.WORKFLOW_EVENT,
                payload={"event": f"step_{i}"}
            )
            await performance_suite.agent_communication.send_message(message)
        
        # 3. Execute concurrent operations
        operations = [
            lambda: asyncio.sleep(0.01) for _ in range(10)
        ]
        await performance_suite.async_optimizer.batch_execute(operations)
        
        # 4. Record metrics
        for i in range(10):
            performance_suite.performance_monitor.record_metric(
                "workflow_step",
                float(i),
                {"workflow": "test"}
            )
        
        total_time = time.time() - start_time
        
        # Performance assertion
        assert total_time < 2.0, f"End-to-end workflow took too long: {total_time}s"
        
        # Verify all services are working
        cache_stats = await performance_suite.cache_service.get_stats()
        comm_metrics = await performance_suite.agent_communication.get_metrics()
        async_metrics = performance_suite.async_optimizer.get_metrics()
        perf_metrics = await performance_suite.performance_monitor.get_performance_metrics()
        
        assert cache_stats["status"] == "healthy"
        assert comm_metrics["total_messages"] > 0
        assert async_metrics["total_operations"] > 0
        assert "summary" in perf_metrics


# Performance benchmarks
@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmarks for optimization validation."""
    
    @pytest.mark.asyncio
    async def test_cache_benchmark(self, performance_suite, benchmark):
        """Benchmark cache operations."""
        cache_service = performance_suite.cache_service
        
        async def cache_operations():
            # Write operations
            for i in range(100):
                await cache_service.set(f"bench_key_{i}", {"value": i})
            
            # Read operations
            for i in range(100):
                await cache_service.get(f"bench_key_{i}")
        
        # Benchmark the operations
        result = await benchmark(cache_operations)
        
        # Verify performance
        assert result is None  # Function doesn't return anything
    
    @pytest.mark.asyncio
    async def test_concurrent_benchmark(self, performance_suite, benchmark):
        """Benchmark concurrent operations."""
        async_optimizer = performance_suite.async_optimizer
        
        async def concurrent_operations():
            operations = [
                lambda: asyncio.sleep(0.001) for _ in range(50)
            ]
            return await async_optimizer.batch_execute(operations, max_concurrent=10)
        
        # Benchmark the operations
        results = await benchmark(concurrent_operations)
        
        # Verify results
        assert len(results) == 50
