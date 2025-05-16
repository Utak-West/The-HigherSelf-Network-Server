"""Logging configuration for The HigherSelf Network Server.

This module provides structured logging setup with JSON formatting,
file rotation, and request ID tracking for better observability.

Features:
- JSON structured logging for machine-readable logs
- File rotation with compression for efficient log storage
- Request ID tracking for distributed tracing
- Standard library logging interception to unify log formats
- Context-aware logging with bound values
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, Union

# Try to import loguru, but provide a fallback if not available
try:
    from loguru import logger
except ImportError:
    # Create a minimal compatible logger if loguru is not available
    class MinimalLogger:
        def __init__(self):
            self._logger = logging.getLogger("app")
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

            # Define level name mapping
            self._level_mapping = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL,
            }

        def remove(self):
            """Remove all handlers."""
            for handler in self._logger.handlers[:]:
                self._logger.removeHandler(handler)

        def add(self, sink, level=None, format=None, colorize=None, **kwargs):
            """Add a handler with specified parameters."""
            self._logger.setLevel(self._get_level(level))
            return 0  # Return a dummy handler ID

        def bind(self, **kwargs):
            """Create a logger with context values."""
            return self

        def info(self, message):
            self._logger.info(message)

        def debug(self, message):
            self._logger.debug(message)

        def warning(self, message):
            self._logger.warning(message)

        def error(self, message):
            self._logger.error(message)

        def critical(self, message):
            self._logger.critical(message)

        def exception(self, message):
            self._logger.exception(message)

        def opt(self, depth=0, exception=None):
            """Chain for setting options."""
            return self

        def log(self, level, message):
            """Log at the specified level."""
            level_method = getattr(self._logger, level.lower(), self._logger.info)
            level_method(message)

        def level(self, level_name):
            """Get a level object by name, similar to loguru's implementation."""

            class LevelObject:
                def __init__(self, name, level_no):
                    self.name = name
                    self.no = level_no

            if level_name in self._level_mapping:
                return LevelObject(level_name, self._level_mapping[level_name])
            raise ValueError(f"Unknown level: {level_name}")

        def _get_level(self, level_name):
            """Convert level name to logging level."""
            if level_name in self._level_mapping:
                return self._level_mapping[level_name]
            return logging.INFO

    logger = MinimalLogger()


class JsonSink:
    """Custom sink for loguru that formats logs as JSON.

    Formats log records as structured JSON objects suitable for machine processing.
    This is particularly useful for log aggregation systems like ELK stack,
    CloudWatch Logs, or Google Cloud Logging.

    Attributes:
        indent: Optional JSON indentation for pretty-printing (None for compact)
        ensure_ascii: Whether to escape non-ASCII characters in JSON output
    """

    def __init__(self, indent: Optional[int] = None, ensure_ascii: bool = False):
        """Initialize the JSON sink.

        Args:
            indent: Number of spaces for JSON indentation (None for compact)
            ensure_ascii: Whether to escape non-ASCII characters
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    def __call__(self, message):
        """Format and print a log message as JSON.

        Args:
            message: The loguru message object containing the record
        """
        try:
            record = message.record

            # Extract basic log information
            log_entry = {
                "timestamp": record["time"].isoformat(),
                "level": record["level"].name,
                "message": record["message"],
                "module": record["name"],
                "function": record["function"],
                "line": record["line"],
            }

            # Add extra fields from the record
            for key, value in record["extra"].items():
                log_entry[key] = value

            # Add exception info if present
            if record["exception"]:
                log_entry["exception"] = str(record["exception"])
                log_entry["traceback"] = record["exception"].traceback

            # Print as JSON
            print(
                json.dumps(
                    log_entry, indent=self.indent, ensure_ascii=self.ensure_ascii
                )
            )
        except Exception as e:
            # Fallback if JSON serialization fails
            print(f"ERROR LOGGING: {str(e)} - Original message: {message}")


def setup_logging(
    log_level: str = "INFO",
    json_output: bool = False,
    log_file: Optional[str] = None,
    json_indent: Optional[int] = None,
    rotation: str = "10 MB",
    retention: str = "1 week",
    compression: str = "zip",
) -> None:
    """Set up logging for the application with configurable options.

    Configures loguru for application logging with options for console output,
    file output, JSON formatting, and log rotation. Also intercepts standard
    library logging to ensure consistent formatting.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Whether to output logs as JSON format
        log_file: Path to log file, or None to log to stdout only
        json_indent: Number of spaces for JSON indentation (None for compact)
        rotation: When to rotate log files (size or time-based)
        retention: How long to keep rotated log files
        compression: Compression format for rotated logs
    """
    # Remove default loguru handler
    logger.remove()

    # Determine log format based on json_output
    if json_output:
        # Add JSON handler
        logger.add(JsonSink(indent=json_indent), level=log_level)
    else:
        # Add console handler with colored output
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True,
        )

    # Add file handler if specified
    if log_file:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Add rotating file handler
        logger.add(
            log_file,
            rotation=rotation,  # When to rotate logs
            retention=retention,  # How long to keep logs
            compression=compression,  # Compression format
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            backtrace=True,  # Include backtrace in error logs
            diagnose=True,  # Include variables in error logs
        )

    # Intercept standard library logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Log setup completion
    logger.info(f"Logging initialized at {log_level} level")
    if log_file:
        logger.info(f"Logging to file: {log_file}")
    if json_output:
        logger.info("JSON structured logging enabled")


class InterceptHandler(logging.Handler):
    """Intercepts standard library logging and redirects to loguru.

    This handler captures logs from the standard library logging module
    and redirects them through loguru, ensuring all application logs
    have consistent formatting regardless of their source.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Process a log record and dispatch it to loguru.

        Args:
            record: The standard library LogRecord to process
        """
        # Get corresponding loguru level
        try:
            level = logger.level(record.levelname).name
        except (ValueError, AttributeError):
            level = str(record.levelno)

        # Find caller from where the logged message originated
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Log using loguru
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def get_request_id() -> str:
    """Generate a unique request ID for distributed tracing.

    Creates a UUID version 4 for request tracking across microservices
    and for correlating logs from a single transaction.

    Returns:
        str: A unique UUID string for request identification
    """
    return str(uuid.uuid4())


def get_logger_with_context(**context: Any) -> Any:
    """Get a logger with additional context bound to all log messages.

    Creates a logger that automatically includes specified key-value pairs
    with every log message, useful for tracking request IDs, user IDs,
    or other contextual information without repeating it in each log call.

    Args:
        **context: Context key-value pairs to add to all log messages

    Returns:
        Any: Loguru logger with bound context
    """
    return logger.bind(**context)


# Example usage:
# setup_logging(log_level="DEBUG", json_output=True, log_file="logs/app.log")
# request_logger = get_logger_with_context(request_id=get_request_id())
# request_logger.info("Processing request")
