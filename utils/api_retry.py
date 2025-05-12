"""
API retry utilities for The HigherSelf Network Server.

This module provides retry mechanisms for API calls to handle transient failures
and improve the resilience of the system.
"""

import asyncio
import functools
# import logging # Unused
from typing import Any, Callable, Dict, Optional, Type, Union, List
from datetime import datetime, timedelta

from loguru import logger

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_BACKOFF = 1.0  # seconds
DEFAULT_MAX_BACKOFF = 30.0  # seconds
DEFAULT_BACKOFF_FACTOR = 2.0  # exponential backoff


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_backoff: float = DEFAULT_INITIAL_BACKOFF,
        max_backoff: float = DEFAULT_MAX_BACKOFF,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        retry_exceptions: List[Type[Exception]] = None,
        no_retry_exceptions: List[Type[Exception]] = None
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
            max_backoff: Maximum backoff time in seconds
            backoff_factor: Multiplier for backoff time after each retry
            retry_exceptions: List of exception types that should trigger a retry
            no_retry_exceptions: List of exception types that should not trigger a retry
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


def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        config: Retry configuration
        
    Returns:
        Decorated function
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
                    should_retry = (
                        any(isinstance(e, exc_type) for exc_type in config.retry_exceptions) and
                        not any(isinstance(e, exc_type) for exc_type in config.no_retry_exceptions)
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
                    backoff_time = min(backoff_time * config.backoff_factor, config.max_backoff)
        
        return wrapper
    
    return decorator


# Convenience function for common retry patterns
async def retry_api_call(
    api_call: Callable,
    *args,
    max_retries: int = DEFAULT_MAX_RETRIES,
    **kwargs
) -> Any:
    """
    Retry an API call with exponential backoff.
    
    Args:
        api_call: Async function to call
        *args: Positional arguments for the function
        max_retries: Maximum number of retries
        **kwargs: Keyword arguments for the function
        
    Returns:
        Result of the API call
        
    Raises:
        Exception: If all retries fail
    """
    # Create a retry config
    config = RetryConfig(max_retries=max_retries)
    
    # Create a temporary wrapped function
    @with_retry(config)
    async def _wrapped_call():
        return await api_call(*args, **kwargs)
    
    # Call the wrapped function
    return await _wrapped_call()
