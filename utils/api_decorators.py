"""API decorators for The HigherSelf Network Server.

This module provides decorators to standardize API interactions,
handle testing mode, and implement consistent error handling and logging
for external service integrations while maintaining Notion as the central hub.

The decorators handle both synchronous and asynchronous API calls, with features
including automatic retries, exponential backoff, error logging, and testing mode
with mock responses.
"""

import functools
import os
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union, cast

try:
    from loguru import logger
except ImportError:
    import logging

    # Create a compatible logger that mimics loguru's bind method
    class CompatLogger:
        def __init__(self, name):
            self._logger = logging.getLogger(name)

        def bind(self, **kwargs):
            """Create a logger with bound context values similar to loguru."""
            return self

        def info(self, message):
            self._logger.info(message)

        def warning(self, message):
            self._logger.warning(message)

        def error(self, message):
            self._logger.error(message)

        def debug(self, message):
            self._logger.debug(message)

    logger = CompatLogger(__name__)

from config.testing_mode import TestingMode, is_api_disabled, is_testing_mode

# Type variables for better type hinting with decorators
F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Any])


def handle_api_errors(
    api_name: str,
    retry_count: int = 3,
    retry_delay: float = 1.0,
    log_to_notion: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to standardize API error handling across the application.

    Args:
        api_name: Name of the API being called (e.g., "notion", "hubspot")
        retry_count: Number of retries for transient errors
        retry_delay: Delay between retries in seconds
        log_to_notion: Whether to log errors to the History Log in Notion

    Returns:
        Decorated function with error handling
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None

            # Get the function name and arguments for logging
            func_name = func.__name__

            for attempt in range(retry_count):
                try:
                    # Check if we're in testing mode and this API is disabled
                    if is_api_disabled(api_name):
                        logger.info(
                            f"[TESTING MODE] API call blocked: {api_name}.{func_name}()"
                        )
                        # Log the attempted call
                        TestingMode.log_attempted_api_call(
                            api_name=api_name,
                            endpoint=func_name,
                            method="call",
                            params={"args": str(args), "kwargs": str(kwargs)},
                        )

                        # Return a mock response based on the API
                        return _get_mock_response(api_name, func_name, *args, **kwargs)

                    # Make the actual API call
                    return func(*args, **kwargs)

                except Exception as e:
                    last_error = e

                    # Log the error
                    if attempt < retry_count - 1:
                        logger.warning(
                            f"API call to {api_name}.{func_name}() failed (attempt {attempt + 1}/{retry_count}): {str(e)}"
                        )
                        time.sleep(retry_delay * (2**attempt))  # Exponential backoff
                    else:
                        logger.error(
                            f"API call to {api_name}.{func_name}() failed after {retry_count} attempts: {str(e)}"
                        )

                        # Log to Notion if requested and possible
                        if log_to_notion:
                            _log_error_to_notion(
                                api_name, func_name, str(e), args, kwargs
                            )

            # If we get here, all retries failed
            if last_error:
                raise last_error

            return None  # This should never be reached

        return cast(F, wrapper)

    return decorator


def handle_async_api_errors(
    api_name: str,
    retry_count: int = 3,
    retry_delay: float = 1.0,
    log_to_notion: bool = True,
) -> Callable[[AsyncF], AsyncF]:
    """
    Decorator to standardize async API error handling across the application.

    Args:
        api_name: Name of the API being called (e.g., "notion", "hubspot")
        retry_count: Number of retries for transient errors
        retry_delay: Delay between retries in seconds
        log_to_notion: Whether to log errors to the History Log in Notion

    Returns:
        Decorated async function with error handling
    """

    def decorator(func: AsyncF) -> AsyncF:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            import asyncio

            last_error = None

            # Get the function name and arguments for logging
            func_name = func.__name__

            for attempt in range(retry_count):
                try:
                    # Check if we're in testing mode and this API is disabled
                    if is_api_disabled(api_name):
                        logger.info(
                            f"[TESTING MODE] Async API call blocked: {api_name}.{func_name}()"
                        )
                        # Log the attempted call
                        TestingMode.log_attempted_api_call(
                            api_name=api_name,
                            endpoint=func_name,
                            method="async_call",
                            params={"args": str(args), "kwargs": str(kwargs)},
                        )

                        # Return a mock response based on the API
                        return _get_mock_response(api_name, func_name, *args, **kwargs)

                    # Make the actual API call
                    return await func(*args, **kwargs)

                except Exception as e:
                    last_error = e

                    # Log the error
                    if attempt < retry_count - 1:
                        logger.warning(
                            f"Async API call to {api_name}.{func_name}() failed (attempt {attempt + 1}/{retry_count}): {str(e)}"
                        )
                        await asyncio.sleep(
                            retry_delay * (2**attempt)
                        )  # Exponential backoff
                    else:
                        logger.error(
                            f"Async API call to {api_name}.{func_name}() failed after {retry_count} attempts: {str(e)}"
                        )

                        # Log to Notion if requested and possible
                        if log_to_notion:
                            await _async_log_error_to_notion(
                                api_name, func_name, str(e), args, kwargs
                            )

            # If we get here, all retries failed
            if last_error:
                raise last_error

            return None  # This should never be reached

        return cast(AsyncF, wrapper)

    return decorator


def _get_mock_response(api_name: str, func_name: str, *args: Any, **kwargs: Any) -> Any:
    """Generate a mock response for testing mode.

    Creates appropriate mock responses for different APIs and function calls
    to simulate API behavior in testing mode without making actual external requests.

    Args:
        api_name: Name of the API (e.g., "notion", "hubspot")
        func_name: Name of the function being called
        *args: Positional arguments passed to the original function
        **kwargs: Keyword arguments passed to the original function

    Returns:
        Any: A suitable mock response based on the API and function
    """
    # Default mock responses by API
    mock_responses = {
        "notion": {
            "default": {"object": "mock", "status": "success"},
            "query_database": {"results": [], "has_more": False, "next_cursor": None},
            "create_page": {
                "id": "mock_page_id",
                "object": "page",
                "created_time": "2023-01-01T00:00:00.000Z",
            },
            "update_page": {
                "id": "mock_page_id",
                "object": "page",
                "last_edited_time": "2023-01-01T00:00:00.000Z",
            },
        },
        "hubspot": {
            "default": {"status": "OK", "data": {}},
            "create_contact": {
                "id": "mock_contact_id",
                "status": "OK",
                "properties": {},
            },
            "update_contact": {
                "id": "mock_contact_id",
                "status": "OK",
                "properties": {},
            },
        },
        "typeform": {
            "default": {"data": []},
            "get_responses": {"items": [], "total_items": 0, "page_count": 1},
        },
        "circle": {
            "default": {"success": True, "data": {}},
            "get_member": {
                "id": "mock_member_id",
                "name": "Mock Member",
                "email": "mock@example.com",
            },
            "create_post": {
                "id": "mock_post_id",
                "status": "published",
                "created_at": "2023-01-01T00:00:00.000Z",
            },
        },
        "beehiiv": {
            "default": {"success": True, "data": {}},
            "send_email": {
                "id": "mock_email_id",
                "status": "queued",
                "created_at": "2023-01-01T00:00:00.000Z",
            },
            "get_subscribers": {"subscribers": [], "total": 0, "page": 1, "limit": 100},
        },
        "woocommerce": {
            "default": {"success": True, "data": {}},
            "get_order": {
                "id": "mock_order_id",
                "status": "processing",
                "total": "99.99",
            },
            "get_product": {
                "id": "mock_product_id",
                "name": "Mock Product",
                "price": "49.99",
            },
        },
        "amelia": {
            "default": {"success": True, "data": {}},
            "get_appointment": {
                "id": "mock_appointment_id",
                "status": "approved",
                "start": "2023-01-01T09:00:00",
            },
            "create_booking": {
                "id": "mock_booking_id",
                "status": "pending",
                "created": "2023-01-01T00:00:00",
            },
        },
    }

    # Get the appropriate mock response
    api_responses = mock_responses.get(api_name.lower(), {"default": {}})
    return api_responses.get(func_name, api_responses["default"])


def _log_error_to_notion(
    api_name: str, func_name: str, error_message: str, args: Any, kwargs: Any
) -> None:
    """Log an API error to the History Log in Notion's Workflow Instances database.

    This function extracts the workflow instance ID from the function arguments,
    then logs the error details to the associated workflow instance record in Notion.
    If no workflow instance ID is found, it only logs locally.

    Args:
        api_name: Name of the API that failed (e.g., "notion", "hubspot")
        func_name: Name of the function that failed
        error_message: Error message from the exception
        args: Positional arguments from the original function call
        kwargs: Keyword arguments from the original function call
    """
    from datetime import datetime

    from services.notion_service import NotionService

    # Get the workflow instance ID if available
    workflow_instance_id = kwargs.get("workflow_instance_id", None)
    if not workflow_instance_id:
        # Try to extract from args if it's a WorkflowInstance object
        for arg in args:
            if hasattr(arg, "instance_id"):
                workflow_instance_id = arg.instance_id
                break

    if workflow_instance_id:
        error_log = {
            "timestamp": datetime.now().isoformat(),
            "api": api_name,
            "function": func_name,
            "error": error_message,
            "workflow_instance_id": workflow_instance_id,
        }

        # Log locally first
        logger.info(
            f"Error logged for workflow instance {workflow_instance_id}: {error_log}"
        )

        try:
            # Create a Notion service instance
            notion_service = NotionService.from_env()

            # Get the workflow instance
            from models.notion_db_models import WorkflowInstance

            # Query for the workflow instance
            filter_conditions = {
                "property": "instance_id",
                "rich_text": {"equals": workflow_instance_id},
            }

            # This is a synchronous function, so we can't use async/await
            # We'll use a simple thread-based approach to call the async method
            import asyncio
            import threading

            def run_async_in_thread(coro):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(coro)
                finally:
                    loop.close()

            # Query for the workflow instance and log the error
            async def query_and_log():
                instances = await notion_service.query_database(
                    model_class=WorkflowInstance,
                    filter_conditions=filter_conditions,
                    limit=1,
                )

                if instances:
                    instance = instances[0]
                    action = (
                        f"[API ERROR] {api_name}.{func_name}() failed: {error_message}"
                    )
                    await notion_service.append_to_history_log(
                        instance, action, error_log
                    )
                    return True
                return False

            # Run the async function in a thread
            thread = threading.Thread(
                target=run_async_in_thread, args=(query_and_log(),)
            )
            thread.start()
            thread.join(timeout=10)  # Wait for up to 10 seconds

        except Exception as e:
            logger.error(f"Failed to log error to Notion: {e}")
    else:
        # No workflow instance ID available, just log locally
        logger.warning(
            f"API error in {api_name}.{func_name}(): {error_message} (no workflow instance ID available)"
        )


async def _async_log_error_to_notion(
    api_name: str, func_name: str, error_message: str, args: Any, kwargs: Any
) -> None:
    """Async version of _log_error_to_notion for logging to Notion's Workflow Instances.

    This is the asynchronous counterpart to _log_error_to_notion, designed to be called
    from async functions. It performs the same operations but using async/await syntax
    for Notion API calls.

    Args:
        api_name: Name of the API that failed (e.g., "notion", "hubspot")
        func_name: Name of the function that failed
        error_message: Error message from the exception
        args: Positional arguments from the original function call
        kwargs: Keyword arguments from the original function call
    """
    from datetime import datetime

    from services.notion_service import NotionService

    # Get the workflow instance ID if available
    workflow_instance_id = kwargs.get("workflow_instance_id", None)
    if not workflow_instance_id:
        # Try to extract from args if it's a WorkflowInstance object
        for arg in args:
            if hasattr(arg, "instance_id"):
                workflow_instance_id = arg.instance_id
                break

    if workflow_instance_id:
        error_log = {
            "timestamp": datetime.now().isoformat(),
            "api": api_name,
            "function": func_name,
            "error": error_message,
            "workflow_instance_id": workflow_instance_id,
        }

        # Log locally first
        logger.info(
            f"Error logged for workflow instance {workflow_instance_id}: {error_log}"
        )

        try:
            # Create a Notion service instance
            notion_service = NotionService.from_env()

            # Get the workflow instance
            from models.notion_db_models import WorkflowInstance

            # Query for the workflow instance
            filter_conditions = {
                "property": "instance_id",
                "rich_text": {"equals": workflow_instance_id},
            }

            # Query for the workflow instance and log the error
            instances = await notion_service.query_database(
                model_class=WorkflowInstance,
                filter_conditions=filter_conditions,
                limit=1,
            )

            if instances:
                instance = instances[0]
                action = f"[API ERROR] {api_name}.{func_name}() failed: {error_message}"
                await notion_service.append_to_history_log(instance, action, error_log)
            else:
                logger.warning(
                    f"Could not find workflow instance {workflow_instance_id} to log error"
                )

        except Exception as e:
            logger.error(f"Failed to log error to Notion: {e}")
    else:
        # No workflow instance ID available, just log locally
        logger.warning(
            f"API error in {api_name}.{func_name}(): {error_message} (no workflow instance ID available)"
        )
