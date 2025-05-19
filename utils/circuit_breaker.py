"""
Circuit Breaker Implementation for The HigherSelf Network Server.

This module provides a standalone circuit breaker pattern implementation for
external service calls, featuring:
1. State management (CLOSED, OPEN, HALF_OPEN)
2. Automatic recovery mechanism
3. Configurable thresholds and timeouts
4. Detailed logging of circuit state changes

Usage example:
    # Create a circuit breaker
    breaker = CircuitBreaker("payment_service", failure_threshold=3)

    # Use with async functions
    async def call_payment_api():
        try:
            result = await breaker.execute(
                payment_service.process_payment, amount=100)
            return result
        except CircuitOpenException as e:
            # Handle circuit open case (e.g., fallback or user-friendly error)
            return {
                "success": False,
                "message": "Service temporarily unavailable"
            }
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type

from utils.error_handling import ServiceException


class CircuitState(str, Enum):
    """
    States for the circuit breaker.

    CLOSED: Normal operation - requests go through
    OPEN: Circuit is open - requests fail fast
    HALF_OPEN: Testing if service is back
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenException(ServiceException):
    """Exception raised when a circuit is open."""

    def __init__(self, service_name: str, remaining_seconds: float):
        super().__init__(
            message=f"Circuit for {service_name} is OPEN",
            service_name=service_name,
            details={
                "circuit_state": CircuitState.OPEN,
                "remaining_seconds": round(remaining_seconds, 1),
            },
        )


class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls.

    This pattern prevents cascading failures by failing fast when
    a service is experiencing issues.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        timeout: float = 10.0,
        exclude_exceptions: Optional[List[Type[Exception]]] = None,
        half_open_max_calls: int = 1,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize a circuit breaker.

        Args:
            name: Name of the service protected by this circuit breaker
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Seconds to wait before allowing requests in
                HALF_OPEN state
            timeout: Request timeout in seconds
            exclude_exceptions: List of exception types to not count as
                failures
            half_open_max_calls: Max number of calls to allow in HALF_OPEN
                state
            logger: Optional logger instance
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.timeout = timeout
        self.exclude_exceptions = exclude_exceptions or []
        self.half_open_max_calls = half_open_max_calls

        # Internal state
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED
        self.half_open_calls = 0
        self.consecutive_successes = 0

        # Metrics
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.rejected_calls = 0  # Due to open circuit
        self.timeouts = 0
        self.state_changes: List[Dict[str, Any]] = []

        self.logger = logger or logging.getLogger(f"circuit_breaker.{name}")
        self.logger.info(
            f"Circuit breaker {name} initialized with "
            f"threshold={failure_threshold}, timeout={timeout}s, "
            f"recovery={recovery_timeout}s"
        )

    async def execute(
        self, func: Callable[..., Awaitable[Any]], *args, **kwargs
    ) -> Any:
        """
        Execute a function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Any: The result of the function call

        Raises:
            CircuitOpenException: If the circuit is open
            Exception: Any exception raised by the function
        """
        self.total_calls += 1

        # Check circuit state
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            elapsed = time.time() - self.last_failure_time
            if elapsed > self.recovery_timeout:
                self._transition_to_half_open()
            else:
                self.rejected_calls += 1
                remaining = self.recovery_timeout - elapsed
                self.logger.debug(
                    f"Circuit {self.name} is OPEN. "
                    f"Failing fast. Retry after {remaining:.1f}s"
                )
                raise CircuitOpenException(
                    service_name=self.name, remaining_seconds=remaining
                )

        # For HALF_OPEN state, limit the number of test calls
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                self.rejected_calls += 1
                self.logger.debug(
                    f"Circuit {self.name} is HALF_OPEN but reached max test "
                    f"calls. Failing fast."
                )
                elapsed = time.time() - self.last_failure_time
                remaining = max(0, self.recovery_timeout - elapsed)
                raise CircuitOpenException(
                    service_name=self.name, remaining_seconds=remaining
                )

            self.half_open_calls += 1

        # Execute with timeout
        try:
            # Set timeout for the call
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout)

            # Success handling
            self.successful_calls += 1

            if self.state == CircuitState.HALF_OPEN:
                self.consecutive_successes += 1
                self.logger.info(
                    f"Successful test call to {self.name} in HALF_OPEN state "
                    f"({self.consecutive_successes}/{self.failure_threshold} "
                    f"successes required to close)"
                )

                # If we've had enough consecutive successes, close the circuit
                if self.consecutive_successes >= self.failure_threshold:
                    self._transition_to_closed()

            # Reset failure count for CLOSED state
            if self.state == CircuitState.CLOSED and self.failure_count > 0:
                self.failure_count = 0
                self.logger.debug(f"Reset failure count for {self.name} after success")

            return result

        except asyncio.TimeoutError:
            self.timeouts += 1
            self.logger.warning(f"Timeout calling {self.name} after {self.timeout}s")
            self._handle_failure()
            raise ServiceException(
                message=f"Request to {self.name} timed out after {self.timeout}s",
                service_name=self.name,
                details={"timeout": self.timeout},
            )

        except Exception as e:
            self.failed_calls += 1

            # Check if this exception type should be excluded
            is_excluded = any(
                isinstance(e, exc_type) for exc_type in self.exclude_exceptions
            )

            if not is_excluded:
                self._handle_failure()
            else:
                self.logger.debug(
                    f"Excluded exception {type(e).__name__} not counted as a "
                    f"failure for {self.name}"
                )

            # Re-raise the original exception
            raise

    def _handle_failure(self):
        """Handle a failure, potentially tripping the circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        # Determine whether to trip the circuit open
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to_open("Failed during HALF_OPEN test")

        elif (
            self.state == CircuitState.CLOSED
            and self.failure_count >= self.failure_threshold
        ):
            self._transition_to_open(
                f"Reached failure threshold "
                f"({self.failure_count}/{self.failure_threshold})"
            )

    def _transition_to_open(self, reason: str):
        """Transition to the open state."""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.last_failure_time = time.time()
        self.state_changes.append(
            {
                "timestamp": time.time(),
                "from_state": old_state,
                "to_state": CircuitState.OPEN,
                "reason": reason,
            }
        )
        self.logger.warning(f"Circuit {self.name} OPENED: {reason}")

    def _transition_to_half_open(self):
        """Transition to the half-open state."""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self.consecutive_successes = 0
        self.state_changes.append(
            {
                "timestamp": time.time(),
                "from_state": old_state,
                "to_state": CircuitState.HALF_OPEN,
                "reason": f"Recovery timeout elapsed ({self.recovery_timeout}s)",
            }
        )
        self.logger.info(
            f"Circuit {self.name} HALF-OPEN: recovery timeout elapsed "
            f"({self.recovery_timeout}s)"
        )

    def _transition_to_closed(self):
        """Transition to the closed state."""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_calls = 0
        self.consecutive_successes = 0
        self.state_changes.append(
            {
                "timestamp": time.time(),
                "from_state": old_state,
                "to_state": CircuitState.CLOSED,
                "reason": (
                    f"Consecutive successes threshold reached "
                    f"({self.failure_threshold})"
                ),
            }
        )
        self.logger.info(
            f"Circuit {self.name} CLOSED: " f"consecutive successes threshold reached"
        )

    def reset(self):
        """
        Manually reset the circuit breaker to closed state.

        This can be used for testing or administrative purposes.
        """
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_calls = 0
        self.consecutive_successes = 0
        self.state_changes.append(
            {
                "timestamp": time.time(),
                "from_state": old_state,
                "to_state": CircuitState.CLOSED,
                "reason": "Manual reset",
            }
        )
        self.logger.info(f"Circuit {self.name} manually reset to CLOSED")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get circuit breaker metrics.

        Returns:
            Dict: Circuit breaker metrics and state
        """
        success_rate = (
            (self.successful_calls / self.total_calls) * 100
            if self.total_calls > 0
            else 0
        )

        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self.last_failure_time,
            "metrics": {
                "total_calls": self.total_calls,
                "successful_calls": self.successful_calls,
                "failed_calls": self.failed_calls,
                "rejected_calls": self.rejected_calls,
                "timeouts": self.timeouts,
                "success_rate": f"{success_rate:.1f}%",
            },
            "state_changes": self.state_changes[-10:],  # Last 10 state changes
        }


class CircuitBreakerRegistry:
    """
    Registry for circuit breakers to provide a central point of access.

    This singleton class manages all circuit breakers in the application.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if not hasattr(self, "initialized"):
            self.circuit_breakers = {}
            self.logger = logging.getLogger("circuit_breaker.registry")
            self.initialized = True

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        timeout: float = 10.0,
        exclude_exceptions: Optional[List[Type[Exception]]] = None,
    ) -> CircuitBreaker:
        """
        Get an existing circuit breaker or create a new one.

        Args:
            name: Name of the service
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Seconds to wait before allowing requests in
                HALF_OPEN state
            timeout: Request timeout in seconds
            exclude_exceptions: List of exception types to not count as
                failures

        Returns:
            CircuitBreaker: The circuit breaker instance
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                timeout=timeout,
                exclude_exceptions=exclude_exceptions,
            )
            self.logger.info(f"Created new circuit breaker: {name}")

        return self.circuit_breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """
        Get an existing circuit breaker by name.

        Args:
            name: Name of the service

        Returns:
            Optional[CircuitBreaker]: The circuit breaker instance or None
                if not found
        """
        return self.circuit_breakers.get(name)

    def get_all(self) -> Dict[str, CircuitBreaker]:
        """
        Get all circuit breakers.

        Returns:
            Dict[str, CircuitBreaker]: Dictionary of all circuit breakers
        """
        return self.circuit_breakers

    def reset_all(self):
        """Reset all circuit breakers to closed state."""
        for name, breaker in self.circuit_breakers.items():
            breaker.reset()

        self.logger.info(f"Reset all circuit breakers ({len(self.circuit_breakers)})")

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics for all circuit breakers.

        Returns:
            Dict: Dictionary of circuit breaker metrics by name
        """
        return {
            name: breaker.get_metrics()
            for name, breaker in self.circuit_breakers.items()
        }


# Create a global registry instance for convenience
registry = CircuitBreakerRegistry()


# Decorator for applying circuit breaker to functions
def with_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 30,
    timeout: float = 10.0,
    exclude_exceptions: Optional[List[Type[Exception]]] = None,
    fallback: Optional[Callable] = None,
):
    """
    Decorator to apply circuit breaker to a function.

    Args:
        name: Name of the service
        failure_threshold: Number of failures before opening the circuit
        recovery_timeout: Seconds to wait before allowing requests in
            HALF_OPEN state
        timeout: Request timeout in seconds
        exclude_exceptions: List of exception types to not count as failures
        fallback: Optional fallback function to call when the circuit is open

    Returns:
        Callable: Decorated function
    """

    def decorator(func):
        breaker = registry.get_or_create(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            timeout=timeout,
            exclude_exceptions=exclude_exceptions,
        )

        async def wrapper(*args, **kwargs):
            try:
                return await breaker.execute(func, *args, **kwargs)
            except CircuitOpenException:
                if fallback:
                    return fallback(*args, **kwargs)
                raise

        return wrapper

    return decorator
