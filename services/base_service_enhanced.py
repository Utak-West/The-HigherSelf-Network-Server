"""
Enhanced base service for The HigherSelf Network Server.

This module provides a more robust service layer that decouples external API
interactions with standardized service responses, built-in retry logic,
improved error handling, and connection validation.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

import aiohttp
from pydantic import BaseModel, Field

# Define type variables
T = TypeVar("T")
R = TypeVar("R")


class ServiceResult(BaseModel):
    """Standard result format for all service operations."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ConnectionStats(BaseModel):
    """Statistics about service connection and usage."""

    created_at: datetime = Field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    request_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    average_response_time_ms: float = 0
    total_response_time_ms: float = 0


class BaseService(ABC):
    """
    Enhanced base service with improved error handling and retry logic.

    This implementation:
    1. Standardizes service responses
    2. Adds built-in retry logic
    3. Improves error handling
    4. Provides connection validation
    """

    def __init__(self, service_name: str, config: Dict[str, Any] = None):
        """
        Initialize the service with configuration.

        Args:
            service_name: Name of the service
            config: Optional configuration dictionary
        """
        self.service_name = service_name
        self.config = config or {}
        self.logger = logging.getLogger(f"service.{service_name}")
        self.session: Optional[aiohttp.ClientSession] = None
        self.stats = ConnectionStats()

        # Retry configuration with defaults that can be overridden
        self.max_retries = self.config.get("max_retries", 3)
        self.base_retry_delay = self.config.get("base_retry_delay", 1.0)
        self.max_retry_delay = self.config.get("max_retry_delay", 60.0)
        self.timeout = self.config.get("timeout", 30.0)

        # Optional configuration for circuit breaker pattern
        self.circuit_breaker_enabled = self.config.get("circuit_breaker_enabled", False)
        self.failure_threshold = self.config.get("failure_threshold", 5)
        self.recovery_timeout = self.config.get("recovery_timeout", 30)

        # Circuit state
        self._circuit_open = False
        self._last_failure_time = 0
        self._consecutive_failures = 0

    async def initialize(self) -> ServiceResult:
        """
        Initialize the service and create HTTP session if needed.

        Returns:
            ServiceResult: Result of the initialization
        """
        try:
            if self.session is None:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                )

            # Validate connection to ensure service is accessible
            validation_result = await self.validate_connection()

            if not validation_result.success:
                return validation_result

            self.logger.info(f"{self.service_name} service initialized successfully")
            return ServiceResult(
                success=True,
                data={"service_name": self.service_name},
                meta={"initialized_at": datetime.now().isoformat()},
            )

        except Exception as e:
            self.logger.error(f"Error initializing {self.service_name}: {str(e)}")
            return ServiceResult(
                success=False, error=f"Initialization failed: {str(e)}"
            )

    async def close(self) -> None:
        """Close any open resources."""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.debug(f"Closed aiohttp session for {self.service_name}")

    @abstractmethod
    async def validate_connection(self) -> ServiceResult:
        """
        Validate the connection to the service.

        This method should be implemented by subclasses to perform
        service-specific validation like API key verification or
        checking service health endpoints.

        Returns:
            ServiceResult: Result of the validation
        """
        pass

    async def execute_with_retry(
        self, operation, max_retries=None, **kwargs
    ) -> ServiceResult:
        """
        Execute an operation with retry logic.

        Args:
            operation: Async function to execute
            max_retries: Maximum number of retries (defaults to self.max_retries)
            **kwargs: Arguments to pass to the operation

        Returns:
            ServiceResult: Result of the operation
        """
        retries = 0
        last_error = None
        start_time = datetime.now()

        # Use instance default if not specified
        if max_retries is None:
            max_retries = self.max_retries

        # Check circuit breaker if enabled
        if self.circuit_breaker_enabled and self._circuit_open:
            # Check if recovery timeout has elapsed
            now = datetime.now().timestamp()
            if now - self._last_failure_time > self.recovery_timeout:
                # Try again - circuit is half-open
                self.logger.info(
                    f"Circuit for {self.service_name} is half-open, "
                    f"allowing test request"
                )
            else:
                # Circuit is open - fail fast
                recovery_after = self._last_failure_time + self.recovery_timeout - now
                self.logger.warning(
                    f"Circuit for {self.service_name} is open, "
                    f"failing fast (retry after {recovery_after:.1f}s)"
                )
                return ServiceResult(
                    success=False,
                    error="Service temporarily unavailable (circuit open)",
                    meta={"circuit_open": True, "retry_after_seconds": recovery_after},
                )

        while retries <= max_retries:
            try:
                if retries > 0:
                    self.logger.info(
                        f"Retry attempt {retries}/{max_retries} for "
                        f"{self.service_name}.{operation.__name__}"
                    )

                # Update stats
                self.stats.request_count += 1
                self.stats.last_used_at = datetime.now()

                # Execute the operation
                result = await operation(**kwargs)

                # Calculate response time
                response_time_ms = (datetime.now() - start_time).total_seconds() * 1000

                # Update stats with response time
                self.stats.total_response_time_ms += response_time_ms
                self.stats.average_response_time_ms = (
                    self.stats.total_response_time_ms / self.stats.request_count
                )

                # Reset circuit breaker on success
                if self.circuit_breaker_enabled and self._consecutive_failures > 0:
                    self._consecutive_failures = 0
                    if self._circuit_open:
                        self._circuit_open = False
                        self.logger.info(
                            f"Circuit for {self.service_name} closed after success"
                        )

                return ServiceResult(success=True, data=result)

            except Exception as e:
                last_error = str(e)
                self.stats.error_count += 1
                self.stats.last_error = last_error
                self.stats.last_error_at = datetime.now()

                # Update circuit breaker state
                if self.circuit_breaker_enabled:
                    self._consecutive_failures += 1
                    self._last_failure_time = datetime.now().timestamp()

                    # Trip circuit breaker if threshold exceeded
                    if (
                        self._consecutive_failures >= self.failure_threshold
                        and not self._circuit_open
                    ):
                        self._circuit_open = True
                        self.logger.warning(
                            f"Circuit tripped open for {self.service_name} after "
                            f"{self._consecutive_failures} consecutive failures"
                        )

                self.logger.warning(
                    f"Operation {operation.__name__} failed "
                    f"(attempt {retries+1}/{max_retries+1}): {last_error}"
                )

                retries += 1

                # Only retry if we haven't reached max_retries
                if retries <= max_retries:
                    # Exponential backoff with jitter
                    wait_time = min(
                        self.max_retry_delay,
                        self.base_retry_delay
                        * (2 ** (retries - 1))
                        * (0.75 + 0.5 * (asyncio.get_event_loop().time() % 1.0)),
                    )
                    self.logger.debug(f"Waiting {wait_time:.2f}s before retry")
                    await asyncio.sleep(wait_time)

        # All retries failed
        self.logger.error(
            f"Operation {operation.__name__} failed after " f"{max_retries+1} attempts"
        )

        return ServiceResult(
            success=False,
            error=last_error,
            meta={
                "retries": retries,
                "service": self.service_name,
                "operation": operation.__name__,
                "circuit_open": (
                    self._circuit_open if self.circuit_breaker_enabled else False
                ),
            },
        )

    async def ensure_session(self) -> aiohttp.ClientSession:
        """
        Ensure an aiohttp session exists, creating one if needed.

        Returns:
            aiohttp.ClientSession: The active session
        """
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            self.logger.debug(f"Created new aiohttp session for {self.service_name}")
        return self.session

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ServiceResult:
        """
        Make a GET request with automatic retry.

        Args:
            url: URL to request
            params: Optional query parameters
            headers: Optional headers
            **kwargs: Additional arguments for the request

        Returns:
            ServiceResult: Result of the request
        """
        session = await self.ensure_session()

        async def _execute_request():
            async with session.get(
                url, params=params, headers=headers, **kwargs
            ) as response:
                response.raise_for_status()
                return await response.json()

        return await self.execute_with_retry(_execute_request)

    async def post(
        self,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ServiceResult:
        """
        Make a POST request with automatic retry.

        Args:
            url: URL to request
            data: Optional form data
            json: Optional JSON data
            headers: Optional headers
            **kwargs: Additional arguments for the request

        Returns:
            ServiceResult: Result of the request
        """
        session = await self.ensure_session()

        async def _execute_request():
            async with session.post(
                url, data=data, json=json, headers=headers, **kwargs
            ) as response:
                response.raise_for_status()
                return await response.json()

        return await self.execute_with_retry(_execute_request)

    async def put(
        self,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ServiceResult:
        """
        Make a PUT request with automatic retry.

        Args:
            url: URL to request
            data: Optional form data
            json: Optional JSON data
            headers: Optional headers
            **kwargs: Additional arguments for the request

        Returns:
            ServiceResult: Result of the request
        """
        session = await self.ensure_session()

        async def _execute_request():
            async with session.put(
                url, data=data, json=json, headers=headers, **kwargs
            ) as response:
                response.raise_for_status()
                return await response.json()

        return await self.execute_with_retry(_execute_request)

    async def delete(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ServiceResult:
        """
        Make a DELETE request with automatic retry.

        Args:
            url: URL to request
            params: Optional query parameters
            headers: Optional headers
            **kwargs: Additional arguments for the request

        Returns:
            ServiceResult: Result of the request
        """
        session = await self.ensure_session()

        async def _execute_request():
            async with session.delete(
                url, params=params, headers=headers, **kwargs
            ) as response:
                response.raise_for_status()
                return await response.json()

        return await self.execute_with_retry(_execute_request)

    async def patch(
        self,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ServiceResult:
        """
        Make a PATCH request with automatic retry.

        Args:
            url: URL to request
            data: Optional form data
            json: Optional JSON data
            headers: Optional headers
            **kwargs: Additional arguments for the request

        Returns:
            ServiceResult: Result of the request
        """
        session = await self.ensure_session()

        async def _execute_request():
            async with session.patch(
                url, data=data, json=json, headers=headers, **kwargs
            ) as response:
                response.raise_for_status()
                return await response.json()

        return await self.execute_with_retry(_execute_request)

    def reset_circuit_breaker(self) -> None:
        """Reset the circuit breaker to closed state."""
        if self.circuit_breaker_enabled:
            self._circuit_open = False
            self._consecutive_failures = 0
            self.logger.info(f"Circuit breaker for {self.service_name} manually reset")

    def get_health_check(self) -> Dict[str, Any]:
        """
        Get service health information.

        Returns:
            Dict: Health check information
        """
        return {
            "service_name": self.service_name,
            "status": "operational" if not self._circuit_open else "degraded",
            "circuit_breaker": {
                "enabled": self.circuit_breaker_enabled,
                "state": "open" if self._circuit_open else "closed",
                "consecutive_failures": self._consecutive_failures,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
            },
            "stats": {
                "request_count": self.stats.request_count,
                "error_count": self.stats.error_count,
                "error_rate": (
                    self.stats.error_count / self.stats.request_count
                    if self.stats.request_count > 0
                    else 0
                ),
                "average_response_time_ms": self.stats.average_response_time_ms,
                "last_used_at": (
                    self.stats.last_used_at.isoformat()
                    if self.stats.last_used_at
                    else None
                ),
                "last_error": self.stats.last_error,
                "last_error_at": (
                    self.stats.last_error_at.isoformat()
                    if self.stats.last_error_at
                    else None
                ),
            },
        }


# Optional API provider-specific service implementations can extend this class
class ApiService(BaseService):
    """
    Base class for API-based services with authentication management.
    """

    def __init__(
        self,
        service_name: str,
        api_base_url: str,
        api_key: Optional[str] = None,
        auth_header: str = "Authorization",
        config: Dict[str, Any] = None,
    ):
        """
        Initialize the API service.

        Args:
            service_name: Name of the service
            api_base_url: Base URL for the API
            api_key: Optional API key
            auth_header: Header name for authentication
            config: Additional configuration
        """
        super().__init__(service_name, config)
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.auth_header = auth_header

    def get_default_headers(self) -> Dict[str, str]:
        """
        Get default headers for API requests.

        Returns:
            Dict: Default headers including authentication
        """
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        if self.api_key:
            headers[self.auth_header] = f"Bearer {self.api_key}"

        return headers

    async def validate_connection(self) -> ServiceResult:
        """
        Validate API connection by checking authentication.

        Returns:
            ServiceResult: Result of the validation
        """
        # This is a basic implementation; override in subclasses to call
        # the specific API's authentication check or health endpoint
        if not self.api_key:
            return ServiceResult(success=False, error="API key not provided")

        return ServiceResult(success=True, data={"message": "API key is set"})

    async def make_api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ServiceResult:
        """
        Make an API request with method resolution.

        Args:
            method: HTTP method (get, post, put, delete, patch)
            endpoint: API endpoint (will be joined with base URL)
            params: Optional query parameters
            data: Optional form data
            json_data: Optional JSON data
            headers: Optional headers (will be merged with defaults)
            **kwargs: Additional arguments for the request

        Returns:
            ServiceResult: Result of the request
        """
        # Combine base URL and endpoint
        url = f"{self.api_base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # Merge headers
        request_headers = self.get_default_headers()
        if headers:
            request_headers.update(headers)

        # Call appropriate method based on the HTTP method
        method = method.lower()
        if method == "get":
            return await self.get(url, params, request_headers, **kwargs)
        elif method == "post":
            return await self.post(url, data, json_data, request_headers, **kwargs)
        elif method == "put":
            return await self.put(url, data, json_data, request_headers, **kwargs)
        elif method == "delete":
            return await self.delete(url, params, request_headers, **kwargs)
        elif method == "patch":
            return await self.patch(url, data, json_data, request_headers, **kwargs)
        else:
            return ServiceResult(
                success=False, error=f"Unsupported HTTP method: {method}"
            )
