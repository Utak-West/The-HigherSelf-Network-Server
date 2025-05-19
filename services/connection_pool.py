"""
Connection Pool Implementation for The HigherSelf Network Server.

This module provides pooling for external API and database connections, featuring:
1. Connection reuse for better performance
2. Health checking
3. Automatic retry with backoff logic
4. Request timeout handling
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector

from utils.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry
from utils.error_handling import ServiceException


class ConnectionStatus(str, Enum):
    """Connection status enum."""

    IDLE = "idle"
    BUSY = "busy"
    CLOSED = "closed"
    ERROR = "error"


class APIConnectionPool:
    """
    Connection pool for external API services.

    This implementation:
    1. Maintains a pool of connections for reuse
    2. Includes connection health checking
    3. Supports automatic retry with backoff
    4. Implements request timeout handling
    """

    def __init__(
        self,
        base_url: str,
        max_connections: int = 10,
        timeout: float = 30.0,
        retry_attempts: int = 3,
        circuit_breaker: Optional[CircuitBreaker] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the connection pool.

        Args:
            base_url: Base URL for API requests
            max_connections: Maximum number of connections to maintain
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
            circuit_breaker: Optional circuit breaker instance
            logger: Optional logger instance
        """
        self.base_url = base_url.rstrip("/")
        self.max_connections = max_connections
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.session = None
        self.logger = logger or logging.getLogger("api.connection_pool")

        # Circuit breaker integration
        service_name = (
            base_url.replace("https://", "").replace("http://", "").split("/")[0]
        )
        self.circuit_breaker = (
            circuit_breaker
            or CircuitBreakerRegistry().get_or_create(
                name=f"api_{service_name}",
                failure_threshold=3,
                recovery_timeout=30,
                timeout=timeout,
            )
        )

        # Metrics tracking
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retried_requests": 0,
            "timed_out_requests": 0,
            "active_connections": 0,
            "total_connection_time": 0.0,
            "status": "initialized",
        }

    async def initialize(self):
        """Initialize the connection pool."""
        if self.session is None:
            # Create connection pool with TCPConnector
            connector = TCPConnector(
                limit=self.max_connections,
                enable_cleanup_closed=True,
                force_close=False,
                ssl=None,  # Set to appropriate SSL context if needed
            )

            # Set default request timeout
            timeout = ClientTimeout(total=self.timeout)

            # Create client session
            self.session = ClientSession(
                connector=connector,
                timeout=timeout,
                raise_for_status=False,  # Don't raise exceptions for HTTP status codes
            )

            self._metrics["status"] = "connected"
            self.logger.info(
                f"Initialized connection pool for {self.base_url} "
                f"with {self.max_connections} connections"
            )

    async def close(self):
        """Close the connection pool."""
        if self.session:
            await self.session.close()
            self.session = None
            self._metrics["status"] = "closed"
            self.logger.info(f"Closed connection pool for {self.base_url}")

    async def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: Optional[float] = None,
        raise_for_status: bool = True,
        retry_codes: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API with retry and circuit breaker.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            headers: HTTP headers
            params: Query parameters
            json_data: JSON body data
            data: Form data
            timeout: Request timeout (overrides default)
            raise_for_status: Whether to raise for error status codes
            retry_codes: Status codes to retry (in addition to 5xx and 429)

        Returns:
            Dict with keys:
                - data: Response data (JSON or text)
                - status: HTTP status code
                - headers: Response headers
                - url: Final URL after redirects

        Raises:
            ServiceException: If the request fails after all retries
        """
        # Ensure we have a session
        await self.initialize()

        # Prepare the URL
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Set default retry codes if not provided
        if retry_codes is None:
            retry_codes = [429, 500, 502, 503, 504]

        # Use circuit breaker
        try:
            # Execute with circuit breaker
            return await self.circuit_breaker.execute(
                self._execute_request,
                method=method,
                url=url,
                headers=headers,
                params=params,
                json_data=json_data,
                data=data,
                timeout=timeout,
                raise_for_status=raise_for_status,
                retry_codes=retry_codes,
            )
        except Exception as e:
            # Wrap exception in ServiceException if needed
            if not isinstance(e, ServiceException):
                raise ServiceException(
                    message=f"API request failed: {str(e)}",
                    service_name=self.base_url,
                    details={"method": method, "endpoint": endpoint},
                )
            raise

    async def _execute_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: Optional[float] = None,
        raise_for_status: bool = True,
        retry_codes: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a request with retry logic.

        Note: This function is called by the circuit breaker.
        """
        self._metrics["total_requests"] += 1
        self._metrics["active_connections"] += 1

        attempt = 0
        last_error = None
        request_timeout = ClientTimeout(total=timeout) if timeout else None
        start_time = time.time()

        while attempt < self.retry_attempts:
            try:
                # Exponential backoff for retries
                if attempt > 0:
                    wait_time = 0.5 * (2**attempt)
                    self.logger.warning(
                        f"Retry {attempt}/{self.retry_attempts} for {method} {url} "
                        f"after {wait_time:.2f}s"
                    )
                    self._metrics["retried_requests"] += 1
                    await asyncio.sleep(wait_time)

                # Make the request
                async with self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    data=data,
                    timeout=request_timeout,
                    ssl=None,  # Set to appropriate SSL context if needed
                ) as response:
                    # Parse response
                    content_type = response.headers.get("Content-Type", "")

                    if "application/json" in content_type:
                        data = await response.json()
                    else:
                        data = await response.text()

                    # Check for error status
                    if response.status >= 400:
                        error_msg = f"API error: {response.status}"
                        details = {
                            "status_code": response.status,
                            "url": str(response.url),
                            "method": method,
                        }

                        if isinstance(data, dict) and "error" in data:
                            error_msg = f"{error_msg} - {data.get('error')}"
                            details["error"] = data.get("error")

                        # Only retry on certain status codes
                        if response.status in retry_codes:
                            self.logger.warning(
                                f"Received {response.status} from {method} {url} - will retry"
                            )
                            last_error = error_msg
                            attempt += 1
                            continue
                        elif raise_for_status:
                            # Don't retry but raise an exception
                            self._metrics["failed_requests"] += 1
                            self._metrics["active_connections"] -= 1
                            self._metrics["total_connection_time"] += (
                                time.time() - start_time
                            )

                            raise ServiceException(
                                message=error_msg,
                                service_name=self.base_url,
                                details=details,
                            )

                    # Success - return response data
                    self._metrics["successful_requests"] += 1
                    self._metrics["active_connections"] -= 1
                    self._metrics["total_connection_time"] += time.time() - start_time

                    return {
                        "data": data,
                        "status": response.status,
                        "headers": dict(response.headers),
                        "url": str(response.url),
                    }

            except asyncio.TimeoutError:
                timeout_value = timeout or self.timeout
                last_error = f"Request timeout after {timeout_value}s"
                self.logger.warning(f"Timeout for {method} {url}")
                self._metrics["timed_out_requests"] += 1
                attempt += 1

            except aiohttp.ClientError as e:
                last_error = f"Connection error: {str(e)}"
                self.logger.warning(f"Connection error for {method} {url}: {str(e)}")
                attempt += 1

            except Exception as e:
                # Unexpected error - don't retry
                self._metrics["failed_requests"] += 1
                self._metrics["active_connections"] -= 1
                self._metrics["total_connection_time"] += time.time() - start_time

                raise ServiceException(
                    message=f"Unexpected error: {str(e)}",
                    service_name=self.base_url,
                    details={"url": url, "method": method},
                )

        # All retries failed
        self._metrics["failed_requests"] += 1
        self._metrics["active_connections"] -= 1
        self._metrics["total_connection_time"] += time.time() - start_time

        raise ServiceException(
            message=f"Request failed after {attempt} attempts: {last_error}",
            service_name=self.base_url,
            details={"url": url, "method": method, "attempts": attempt},
        )

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the connection pool.

        Returns:
            Dict with health status information
        """
        health = {
            "service": self.base_url,
            "status": "unknown",
            "timestamp": time.time(),
            "metrics": self._metrics.copy(),
            "circuit_breaker": self.circuit_breaker.get_metrics(),
            "error": None,
        }

        try:
            # Simple health check - send a request to a health endpoint
            # This can be customized based on the actual API
            response = await self.request(
                method="GET", endpoint="/", timeout=5.0, raise_for_status=False
            )

            if response["status"] < 500:
                health["status"] = "healthy"
            else:
                health["status"] = "unhealthy"
                health["error"] = f"Received status {response['status']}"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)

        return health

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the connection pool.

        Returns:
            Dict with metrics information
        """
        metrics = self._metrics.copy()

        # Add calculated metrics
        if metrics["total_requests"] > 0:
            metrics["success_rate"] = (
                metrics["successful_requests"] / metrics["total_requests"]
            ) * 100
            metrics["failure_rate"] = (
                metrics["failed_requests"] / metrics["total_requests"]
            ) * 100
            metrics["retry_rate"] = (
                metrics["retried_requests"] / metrics["total_requests"]
            ) * 100
            metrics["timeout_rate"] = (
                metrics["timed_out_requests"] / metrics["total_requests"]
            ) * 100
        else:
            metrics["success_rate"] = 0
            metrics["failure_rate"] = 0
            metrics["retry_rate"] = 0
            metrics["timeout_rate"] = 0

        # Add average connection time
        if metrics["successful_requests"] > 0:
            total_time = metrics["total_connection_time"]
            success_count = metrics["successful_requests"]
            metrics["average_connection_time"] = total_time / success_count
        else:
            metrics["average_connection_time"] = 0

        # Add circuit breaker metrics
        metrics["circuit_breaker"] = self.circuit_breaker.get_metrics()

        return metrics


# Connection pool registry for easy access
_connection_pools = {}


async def get_connection_pool(
    base_url: str,
    max_connections: int = 10,
    timeout: float = 30.0,
    retry_attempts: int = 3,
) -> APIConnectionPool:
    """
    Get or create a connection pool for a specific base URL.

    Args:
        base_url: Base URL for API requests
        max_connections: Maximum number of connections to maintain
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts for failed requests

    Returns:
        APIConnectionPool: The connection pool instance
    """
    global _connection_pools

    if base_url not in _connection_pools:
        pool = APIConnectionPool(
            base_url=base_url,
            max_connections=max_connections,
            timeout=timeout,
            retry_attempts=retry_attempts,
        )
        await pool.initialize()
        _connection_pools[base_url] = pool

    return _connection_pools[base_url]


async def close_all_pools():
    """Close all connection pools."""
    global _connection_pools

    for url, pool in _connection_pools.items():
        await pool.close()

    _connection_pools = {}


# Decorator for API requests with connection pooling
def with_connection_pool(
    base_url: str,
    max_connections: int = 10,
    timeout: float = 30.0,
    retry_attempts: int = 3,
):
    """
    Decorator to use a connection pool for API requests.

    Usage:
    @with_connection_pool("https://api.example.com")
    async def fetch_data(endpoint, params):
        # Will use a connection pool for this request
        return await pool.request("GET", endpoint, params=params)

    Args:
        base_url: Base URL for API requests
        max_connections: Maximum number of connections to maintain
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts for failed requests

    Returns:
        Decorator function
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get connection pool
            pool = await get_connection_pool(
                base_url=base_url,
                max_connections=max_connections,
                timeout=timeout,
                retry_attempts=retry_attempts,
            )

            # Add pool to kwargs
            kwargs["pool"] = pool

            # Call the function
            return await func(*args, **kwargs)

        return wrapper

    return decorator
