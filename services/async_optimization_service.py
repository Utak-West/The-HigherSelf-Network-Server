"""
Async/Await Optimization Service for HigherSelf Network Server.

Provides optimized async patterns, connection pooling, concurrent request handling,
and performance improvements for async operations.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, Awaitable
from functools import wraps
from contextlib import asynccontextmanager
import weakref

from loguru import logger
from pydantic import BaseModel

from services.performance_monitoring_service import performance_monitor

T = TypeVar('T')


class ConnectionPool:
    """Generic async connection pool."""
    
    def __init__(
        self,
        create_connection: Callable[[], Awaitable[Any]],
        max_connections: int = 10,
        min_connections: int = 2,
        max_idle_time: float = 300.0,  # 5 minutes
        connection_timeout: float = 30.0
    ):
        self.create_connection = create_connection
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.max_idle_time = max_idle_time
        self.connection_timeout = connection_timeout
        
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_connections)
        self._active_connections: weakref.WeakSet = weakref.WeakSet()
        self._connection_count = 0
        self._last_cleanup = time.time()
        
        # Metrics
        self.total_connections_created = 0
        self.total_connections_reused = 0
        self.total_connections_closed = 0
    
    async def initialize(self):
        """Initialize the connection pool with minimum connections."""
        for _ in range(self.min_connections):
            connection = await self._create_new_connection()
            await self._pool.put((connection, time.time()))
    
    async def _create_new_connection(self):
        """Create a new connection."""
        try:
            connection = await asyncio.wait_for(
                self.create_connection(),
                timeout=self.connection_timeout
            )
            self._connection_count += 1
            self.total_connections_created += 1
            self._active_connections.add(connection)
            return connection
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        connection = None
        connection_time = None
        
        try:
            # Try to get existing connection
            try:
                connection, connection_time = self._pool.get_nowait()
                
                # Check if connection is still valid and not too old
                if time.time() - connection_time > self.max_idle_time:
                    await self._close_connection(connection)
                    connection = None
                else:
                    self.total_connections_reused += 1
            except asyncio.QueueEmpty:
                pass
            
            # Create new connection if needed
            if connection is None:
                if self._connection_count < self.max_connections:
                    connection = await self._create_new_connection()
                else:
                    # Wait for a connection to become available
                    connection, connection_time = await asyncio.wait_for(
                        self._pool.get(),
                        timeout=self.connection_timeout
                    )
                    
                    # Check if connection is still valid
                    if time.time() - connection_time > self.max_idle_time:
                        await self._close_connection(connection)
                        connection = await self._create_new_connection()
                    else:
                        self.total_connections_reused += 1
            
            yield connection
            
        except Exception as e:
            logger.error(f"Connection pool error: {e}")
            if connection:
                await self._close_connection(connection)
            raise
        finally:
            # Return connection to pool if it's still valid
            if connection and connection in self._active_connections:
                try:
                    self._pool.put_nowait((connection, time.time()))
                except asyncio.QueueFull:
                    # Pool is full, close the connection
                    await self._close_connection(connection)
    
    async def _close_connection(self, connection):
        """Close a connection."""
        try:
            if hasattr(connection, 'close'):
                await connection.close()
            elif hasattr(connection, 'disconnect'):
                await connection.disconnect()
            
            self._active_connections.discard(connection)
            self._connection_count -= 1
            self.total_connections_closed += 1
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
    
    async def cleanup(self):
        """Clean up idle connections."""
        current_time = time.time()
        
        # Only cleanup if enough time has passed
        if current_time - self._last_cleanup < 60:  # Cleanup every minute
            return
        
        self._last_cleanup = current_time
        connections_to_close = []
        
        # Check all connections in pool
        temp_connections = []
        while not self._pool.empty():
            try:
                connection, connection_time = self._pool.get_nowait()
                if current_time - connection_time > self.max_idle_time:
                    connections_to_close.append(connection)
                else:
                    temp_connections.append((connection, connection_time))
            except asyncio.QueueEmpty:
                break
        
        # Put back valid connections
        for connection, connection_time in temp_connections:
            try:
                self._pool.put_nowait((connection, connection_time))
            except asyncio.QueueFull:
                connections_to_close.append(connection)
        
        # Close expired connections
        for connection in connections_to_close:
            await self._close_connection(connection)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            "active_connections": self._connection_count,
            "pool_size": self._pool.qsize(),
            "max_connections": self.max_connections,
            "min_connections": self.min_connections,
            "total_created": self.total_connections_created,
            "total_reused": self.total_connections_reused,
            "total_closed": self.total_connections_closed,
            "reuse_rate": (
                self.total_connections_reused / 
                max(self.total_connections_created + self.total_connections_reused, 1)
            ) * 100
        }


class AsyncOptimizationService:
    """
    Service for optimizing async operations and patterns.
    
    Features:
    - Connection pooling
    - Concurrent request batching
    - Async operation monitoring
    - Circuit breaker patterns
    - Rate limiting
    """
    
    def __init__(self):
        self.connection_pools: Dict[str, ConnectionPool] = {}
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        self.rate_limiters: Dict[str, Dict[str, Any]] = {}
        
        # Performance metrics
        self.concurrent_operations = 0
        self.max_concurrent_operations = 0
        self.total_operations = 0
        self.failed_operations = 0
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the async optimization service."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Async optimization service started")
    
    async def stop(self):
        """Stop the async optimization service."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        
        # Close all connection pools
        for pool in self.connection_pools.values():
            await pool.cleanup()
        
        logger.info("Async optimization service stopped")
    
    def create_connection_pool(
        self,
        name: str,
        create_connection: Callable[[], Awaitable[Any]],
        max_connections: int = 10,
        min_connections: int = 2,
        max_idle_time: float = 300.0
    ) -> ConnectionPool:
        """Create a named connection pool."""
        pool = ConnectionPool(
            create_connection=create_connection,
            max_connections=max_connections,
            min_connections=min_connections,
            max_idle_time=max_idle_time
        )
        
        self.connection_pools[name] = pool
        return pool
    
    def get_connection_pool(self, name: str) -> Optional[ConnectionPool]:
        """Get a connection pool by name."""
        return self.connection_pools.get(name)
    
    def create_semaphore(self, name: str, max_concurrent: int) -> asyncio.Semaphore:
        """Create a named semaphore for concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)
        self.semaphores[name] = semaphore
        return semaphore
    
    def get_semaphore(self, name: str) -> Optional[asyncio.Semaphore]:
        """Get a semaphore by name."""
        return self.semaphores.get(name)
    
    async def batch_execute(
        self,
        operations: List[Callable[[], Awaitable[T]]],
        max_concurrent: int = 10,
        return_exceptions: bool = True
    ) -> List[Union[T, Exception]]:
        """Execute multiple async operations with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(operation: Callable[[], Awaitable[T]]) -> T:
            async with semaphore:
                self.concurrent_operations += 1
                self.max_concurrent_operations = max(
                    self.max_concurrent_operations, 
                    self.concurrent_operations
                )
                
                try:
                    start_time = time.time()
                    result = await operation()
                    
                    # Record metrics
                    execution_time = (time.time() - start_time) * 1000
                    performance_monitor.record_metric(
                        "async_operation_duration",
                        execution_time,
                        {"type": "batch_operation"}
                    )
                    
                    self.total_operations += 1
                    return result
                    
                except Exception as e:
                    self.failed_operations += 1
                    logger.error(f"Batch operation failed: {e}")
                    raise
                finally:
                    self.concurrent_operations -= 1
        
        # Execute all operations concurrently
        tasks = [execute_with_semaphore(op) for op in operations]
        results = await asyncio.gather(*tasks, return_exceptions=return_exceptions)
        
        return results
    
    def rate_limit(
        self,
        name: str,
        max_calls: int,
        time_window: float = 60.0
    ):
        """Decorator for rate limiting async functions."""
        
        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                current_time = time.time()
                
                # Initialize rate limiter if not exists
                if name not in self.rate_limiters:
                    self.rate_limiters[name] = {
                        'calls': [],
                        'max_calls': max_calls,
                        'time_window': time_window
                    }
                
                limiter = self.rate_limiters[name]
                
                # Clean old calls
                limiter['calls'] = [
                    call_time for call_time in limiter['calls']
                    if current_time - call_time < time_window
                ]
                
                # Check rate limit
                if len(limiter['calls']) >= max_calls:
                    wait_time = time_window - (current_time - limiter['calls'][0])
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                        # Clean again after waiting
                        current_time = time.time()
                        limiter['calls'] = [
                            call_time for call_time in limiter['calls']
                            if current_time - call_time < time_window
                        ]
                
                # Record call
                limiter['calls'].append(current_time)
                
                # Execute function
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        """Decorator for circuit breaker pattern."""
        
        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            state = {
                'failures': 0,
                'last_failure_time': None,
                'state': 'closed'  # closed, open, half-open
            }
            
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                current_time = time.time()
                
                # Check if circuit should be half-open
                if (state['state'] == 'open' and 
                    state['last_failure_time'] and
                    current_time - state['last_failure_time'] > recovery_timeout):
                    state['state'] = 'half-open'
                
                # Reject if circuit is open
                if state['state'] == 'open':
                    raise Exception(f"Circuit breaker {name} is open")
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # Reset on success
                    if state['state'] == 'half-open':
                        state['state'] = 'closed'
                        state['failures'] = 0
                        logger.info(f"Circuit breaker {name} recovered")
                    
                    return result
                    
                except expected_exception as e:
                    state['failures'] += 1
                    state['last_failure_time'] = current_time
                    
                    # Open circuit if threshold reached
                    if state['failures'] >= failure_threshold:
                        state['state'] = 'open'
                        logger.warning(f"Circuit breaker {name} opened after {state['failures']} failures")
                    
                    raise
            
            return wrapper
        return decorator
    
    async def timeout_wrapper(
        self,
        operation: Callable[[], Awaitable[T]],
        timeout: float
    ) -> T:
        """Wrap an async operation with timeout."""
        try:
            return await asyncio.wait_for(operation(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout} seconds")
            raise
    
    async def retry_with_backoff(
        self,
        operation: Callable[[], Awaitable[T]],
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ) -> T:
        """Retry an async operation with exponential backoff."""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                last_exception = e
                
                if attempt == max_retries:
                    break
                
                # Calculate delay with exponential backoff
                delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                logger.warning(f"Operation failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get async optimization metrics."""
        pool_stats = {}
        for name, pool in self.connection_pools.items():
            pool_stats[name] = pool.get_stats()
        
        return {
            "concurrent_operations": self.concurrent_operations,
            "max_concurrent_operations": self.max_concurrent_operations,
            "total_operations": self.total_operations,
            "failed_operations": self.failed_operations,
            "success_rate": (
                (self.total_operations - self.failed_operations) / 
                max(self.total_operations, 1)
            ) * 100,
            "connection_pools": pool_stats,
            "active_semaphores": len(self.semaphores),
            "active_rate_limiters": len(self.rate_limiters)
        }
    
    async def _cleanup_loop(self):
        """Background cleanup task."""
        try:
            while True:
                # Cleanup connection pools
                for pool in self.connection_pools.values():
                    await pool.cleanup()
                
                # Cleanup rate limiters
                current_time = time.time()
                for name, limiter in list(self.rate_limiters.items()):
                    limiter['calls'] = [
                        call_time for call_time in limiter['calls']
                        if current_time - call_time < limiter['time_window']
                    ]
                    
                    # Remove empty rate limiters
                    if not limiter['calls']:
                        del self.rate_limiters[name]
                
                await asyncio.sleep(60)  # Cleanup every minute
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Cleanup loop error: {e}")


# Global async optimization service
async_optimizer = AsyncOptimizationService()
