"""API retry utilities for The HigherSelf Network Server.

This module provides retry mechanisms for API calls to handle transient failures
and improve the resilience of the system. It includes decorators and utility functions
for implementing exponential backoff, configurable retry policies, and exception handling
for both synchronous and asynchronous API calls.
"""

import asyncio
import functools
from datetime import datetime, timedelta
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

# Setup logger with fallback to standard logging if loguru is not available
try:
    from loguru import logger
except ImportError:
    import logging

    # Create a compatible logger that mimics loguru's interface
    class CompatLogger:
        def __init__(self, name):
            self._logger = logging.getLogger(name)

        def info(self, message):
            self._logger.info(message)

        def warning(self, message):
            self._logger.warning(message)

        def error(self, message):
            self._logger.error(message)

        def debug(self, message):
            self._logger.debug(message)

    logger = CompatLogger(__name__)

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_BACKOFF = 1.0  # seconds
DEFAULT_MAX_BACKOFF = 30.0  # seconds
DEFAULT_BACKOFF_FACTOR = 2.0  # exponential backoff


# Type variables for better type hinting with async functions
T = TypeVar("T")

# Better type for async callables
AsyncCallable = Callable[..., Awaitable[Any]]


class RetryConfig:
    """Configuration for retry behavior with exponential backoff.

    This class encapsulates all settings related to retry behavior, including
    the number of retries, backoff timing, and exception handling policies.
    """

    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_backoff: float = DEFAULT_INITIAL_BACKOFF,
        max_backoff: float = DEFAULT_MAX_BACKOFF,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        retry_exceptions: Optional[List[Type[Exception]]] = None,
        no_retry_exceptions: Optional[List[Type[Exception]]] = None,
    ):
        """Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
            max_backoff: Maximum backoff time in seconds
            backoff_factor: Multiplier for backoff time after each retry (exponential growth)
            retry_exceptions: List of exception types that should trigger a retry.
                Defaults to [ConnectionError, TimeoutError, asyncio.TimeoutError]
            no_retry_exceptions: List of exception types that should never trigger a retry.
                Defaults to [ValueError, TypeError, KeyError, AttributeError]
        """
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_factor = backoff_factor

        # Default retry exceptions if none provided
        self.retry_exceptions = retry_exceptions or [
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        ]

        # Default no-retry exceptions if none provided
        self.no_retry_exceptions = no_retry_exceptions or [
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ]


def with_retry(
    config: Optional[RetryConfig] = None,
) -> Callable:
    """Decorator for retrying async functions with exponential backoff.

    Wraps an async function to automatically retry on specified exceptions,
    with configurable backoff timing between attempts.

    Args:
        config: Retry configuration object with retry policies and timing settings.
            If None, uses default RetryConfig values.

    Returns:
        Callable: A decorator function that wraps the target async function with retry logic
    """
    # Use default config if none provided
    if config is None:
        config = RetryConfig()

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get function name for logging
            func_name = func.__qualname__

            # Initialize retry counter and backoff time
            retry_count = 0
            backoff_time = config.initial_backoff

            # Keep track of last exception for logging
            last_exception = None

            # Try the function with retries
            while True:
                try:
                    # Attempt to call the function
                    return await func(*args, **kwargs)

                except Exception as e:
                    # Check if we should retry this exception
                    should_retry = any(
                        isinstance(e, exc_type) for exc_type in config.retry_exceptions
                    ) and not any(
                        isinstance(e, exc_type)
                        for exc_type in config.no_retry_exceptions
                    )

                    # If we shouldn't retry or we've reached max retries, raise the exception
                    if not should_retry or retry_count >= config.max_retries:
                        if retry_count > 0:
                            logger.warning(
                                f"Function {func_name} failed after {retry_count} retries: {str(e)}"
                            )
                        raise

                    # Increment retry counter
                    retry_count += 1

                    # Log the retry
                    logger.warning(
                        f"Retry {retry_count}/{config.max_retries} for {func_name} after error: {str(e)}"
                    )

                    # Store the exception for later
                    last_exception = e

                    # Wait before retrying
                    await asyncio.sleep(backoff_time)

                    # Increase backoff time for next retry, up to max_backoff
                    backoff_time = min(
                        backoff_time * config.backoff_factor, config.max_backoff
                    )

        return wrapper

    return decorator


# Convenience function for common retry patterns
async def retry_api_call(
    api_call: Callable,
    *args: Any,
    max_retries: int = DEFAULT_MAX_RETRIES,
    **kwargs: Any,
) -> Any:
    """Retry an API call with exponential backoff.

    Utility function that applies retry logic to a single async function call
    without requiring the full decorator syntax. This is useful for one-off
    API calls that need retry handling.

    Args:
        api_call: Async function to call
        *args: Positional arguments for the function
        max_retries: Maximum number of retries
        **kwargs: Keyword arguments for the function

    Returns:
        Any: Result of the API call

    Raises:
        Exception: If all retries fail, the last exception encountered is raised
    """
    # Create a retry config
    config = RetryConfig(max_retries=max_retries)

    # Create a temporary wrapped function
    @with_retry(config)
    async def _wrapped_call():
        return await api_call(*args, **kwargs)

    # Call the wrapped function
    return await _wrapped_call()
