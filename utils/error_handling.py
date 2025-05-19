"""
Enhanced Error Handling System for The HigherSelf Network Server.

This module provides a comprehensive error handling system featuring:
1. Standardized error severity and categories
2. Structured error responses
3. Application-specific exceptions
4. Centralized error handling and logging

Usage examples:
    # Basic exception handling
    try:
        # Some operation
        pass
    except Exception as e:
        error_handler = ErrorHandler()
        error_response = await error_handler.handle_exception(e)

    # Using application-specific exceptions
    try:
        if not valid:
            raise ValidationException(
                "Invalid data format", details={"field": "name"}
            )
    except AppException as e:
        error_handler = ErrorHandler()
        error_response = await error_handler.handle_exception(e)
"""

import json
import logging
import os
import traceback
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ErrorSeverity(str, Enum):
    """Standardized severity levels for application errors."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Categories of errors for better organization and handling."""

    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RESOURCE_NOT_FOUND = "resource_not_found"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    WORKFLOW = "workflow"
    AGENT = "agent"


class ErrorResponse(BaseModel):
    """Standardized error response model."""

    error_code: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    details: Optional[Dict[str, Any]] = None
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary suitable for API responses."""
        result = self.model_dump()
        result["timestamp"] = result["timestamp"].isoformat()
        return result


class AppException(Exception):
    """Base application exception with standardized attributes."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.severity = severity
        self.category = category
        self.details = details or {}
        super().__init__(message)


class ValidationException(AppException):
    """Exception for data validation errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.VALIDATION,
            details=details,
        )


class AuthenticationException(AppException):
    """Exception for authentication failures."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.AUTHENTICATION,
            details=details,
        )


class AuthorizationException(AppException):
    """Exception for authorization failures."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.AUTHORIZATION,
            details=details,
        )


class ResourceNotFoundException(AppException):
    """Exception for resource not found errors."""

    def __init__(self, message: str, resource_type: str, resource_id: str):
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.RESOURCE_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ServiceException(AppException):
    """Exception for external service errors."""

    def __init__(
        self, message: str, service_name: str, details: Optional[Dict[str, Any]] = None
    ):
        merged_details = {"service_name": service_name}
        if details:
            merged_details.update(details)

        super().__init__(
            message=message,
            error_code="SERVICE_ERROR",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.EXTERNAL_SERVICE,
            details=merged_details,
        )


class DatabaseException(AppException):
    """Exception for database operation errors."""

    def __init__(
        self, message: str, operation: str, details: Optional[Dict[str, Any]] = None
    ):
        merged_details = {"operation": operation}
        if details:
            merged_details.update(details)

        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.DATABASE,
            details=merged_details,
        )


class WorkflowException(AppException):
    """Exception for workflow errors."""

    def __init__(
        self,
        message: str,
        workflow_name: str,
        workflow_id: Optional[str] = None,
        state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        merged_details = {
            "workflow_name": workflow_name,
        }

        if workflow_id:
            merged_details["workflow_id"] = workflow_id

        if state:
            merged_details["state"] = state

        if details:
            merged_details.update(details)

        super().__init__(
            message=message,
            error_code="WORKFLOW_ERROR",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.WORKFLOW,
            details=merged_details,
        )


class AgentException(AppException):
    """Exception for agent errors."""

    def __init__(
        self,
        message: str,
        agent_name: str,
        agent_id: Optional[str] = None,
        capability: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        merged_details = {
            "agent_name": agent_name,
        }

        if agent_id:
            merged_details["agent_id"] = agent_id

        if capability:
            merged_details["capability"] = capability

        if details:
            merged_details.update(details)

        super().__init__(
            message=message,
            error_code="AGENT_ERROR",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.AGENT,
            details=merged_details,
        )


class BusinessLogicException(AppException):
    """Exception for business logic errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.BUSINESS_LOGIC,
            details=details,
        )


class ErrorHandler:
    """Centralized error handling for the application."""

    def __init__(self, notion_client=None, logger=None):
        self.notion_client = notion_client
        self.logger = logger or logging.getLogger("error.handler")

        # Database ID for Notion error logging
        self.error_log_db_id = os.getenv(
            "NOTION_ERROR_LOG_DB_ID", "error_log_database_id"
        )
        self.environment = os.getenv("ENVIRONMENT", "development")

    async def handle_exception(
        self,
        exception: Exception,
        log_to_notion: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> ErrorResponse:
        """
        Handle an exception and return a standardized error response.

        Args:
            exception: The exception to handle
            log_to_notion: Whether to log the error to Notion
            context: Additional context for the error

        Returns:
            ErrorResponse: Standardized error response
        """

        # Convert to AppException if it's a standard Exception
        if not isinstance(exception, AppException):
            app_exception = AppException(
                message=str(exception),
                error_code=type(exception).__name__,
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.SYSTEM,
                details={"original_exception": type(exception).__name__},
            )
        else:
            app_exception = exception

        # Prepare the error response
        error_response = ErrorResponse(
            error_code=app_exception.error_code,
            message=app_exception.message,
            severity=app_exception.severity,
            category=app_exception.category,
            details=app_exception.details,
        )

        # Add additional context if provided
        if context:
            if error_response.details is None:
                error_response.details = {}
            error_response.details["context"] = context

        # Add stack trace in non-production environments
        if self.environment != "production":
            if error_response.details is None:
                error_response.details = {}
            error_response.details["stack_trace"] = traceback.format_exc()

        # Log the error
        log_message = f"Error {error_response.error_code}: {error_response.message}"

        if error_response.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(
                log_message, extra={"error_details": error_response.model_dump()}
            )
        elif error_response.severity == ErrorSeverity.ERROR:
            self.logger.error(
                log_message, extra={"error_details": error_response.model_dump()}
            )
        elif error_response.severity == ErrorSeverity.WARNING:
            self.logger.warning(
                log_message, extra={"error_details": error_response.model_dump()}
            )
        else:
            self.logger.info(
                log_message, extra={"error_details": error_response.model_dump()}
            )

        # Log to Notion if requested and available
        if log_to_notion and self.notion_client:
            try:
                # Convert to a format suitable for Notion
                notion_properties = {
                    "Error Code": error_response.error_code,
                    "Message": error_response.message,
                    "Severity": error_response.severity,
                    "Category": error_response.category,
                    "Trace ID": error_response.trace_id,
                    "Timestamp": error_response.timestamp.isoformat(),
                    "Details": json.dumps(error_response.details or {}),
                }

                # Log to the error logging database
                await self.notion_client.create_page(
                    database_id=self.error_log_db_id, properties=notion_properties
                )
            except Exception as e:
                self.logger.error(f"Failed to log error to Notion: {str(e)}")

        return error_response

    async def log_error(
        self,
        message: str,
        error_code: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        details: Optional[Dict[str, Any]] = None,
        log_to_notion: bool = True,
    ) -> ErrorResponse:
        """
        Log an error without an exception.

        Args:
            message: Error message
            error_code: Error code
            severity: Error severity
            category: Error category
            details: Additional error details
            log_to_notion: Whether to log the error to Notion

        Returns:
            ErrorResponse: Standardized error response
        """
        error_response = ErrorResponse(
            error_code=error_code,
            message=message,
            severity=severity,
            category=category,
            details=details,
        )

        # Log the error
        log_message = f"Error {error_response.error_code}: {error_response.message}"

        if error_response.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(
                log_message, extra={"error_details": error_response.model_dump()}
            )
        elif error_response.severity == ErrorSeverity.ERROR:
            self.logger.error(
                log_message, extra={"error_details": error_response.model_dump()}
            )
        elif error_response.severity == ErrorSeverity.WARNING:
            self.logger.warning(
                log_message, extra={"error_details": error_response.model_dump()}
            )
        else:
            self.logger.info(
                log_message, extra={"error_details": error_response.model_dump()}
            )

        # Log to Notion if requested and available
        if log_to_notion and self.notion_client:
            try:
                # Convert to a format suitable for Notion
                notion_properties = {
                    "Error Code": error_response.error_code,
                    "Message": error_response.message,
                    "Severity": error_response.severity,
                    "Category": error_response.category,
                    "Trace ID": error_response.trace_id,
                    "Timestamp": error_response.timestamp.isoformat(),
                    "Details": json.dumps(error_response.details or {}),
                }

                # Log to the error logging database
                await self.notion_client.create_page(
                    database_id=self.error_log_db_id, properties=notion_properties
                )
            except Exception as e:
                self.logger.error(f"Failed to log error to Notion: {str(e)}")

        return error_response


def format_exception_for_api(error_response: ErrorResponse) -> Dict[str, Any]:
    """
    Format an error response for API consumption.

    Args:
        error_response: The error response to format

    Returns:
        Dict: API-friendly error response
    """
    return {
        "error": {
            "code": error_response.error_code,
            "message": error_response.message,
            "trace_id": error_response.trace_id,
            "timestamp": error_response.timestamp.isoformat(),
            "details": error_response.details,
        }
    }


# Utility functions for FastAPI integration
def register_exception_handlers(app):
    """
    Register exception handlers for a FastAPI application.

    Args:
        app: FastAPI application
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        error_handler = ErrorHandler()
        error_response = await error_handler.handle_exception(
            exc, context={"path": request.url.path, "method": request.method}
        )

        status_code = 500
        if exc.category == ErrorCategory.VALIDATION:
            status_code = 400
        elif exc.category == ErrorCategory.AUTHENTICATION:
            status_code = 401
        elif exc.category == ErrorCategory.AUTHORIZATION:
            status_code = 403
        elif exc.category == ErrorCategory.RESOURCE_NOT_FOUND:
            status_code = 404

        return JSONResponse(
            status_code=status_code, content=format_exception_for_api(error_response)
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        error_handler = ErrorHandler()
        error_response = await error_handler.handle_exception(
            exc, context={"path": request.url.path, "method": request.method}
        )

        return JSONResponse(
            status_code=500, content=format_exception_for_api(error_response)
        )
