"""
Logging configuration for The HigherSelf Network Server.

This module provides structured logging setup with JSON formatting,
file rotation, and request ID tracking for better observability.
"""

import os
import sys
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from loguru import logger


class JsonSink:
    """
    Custom sink for loguru that formats logs as JSON.
    Useful for structured logging and integration with log aggregation tools.
    """
    
    def __call__(self, message):
        """Format and print a log message as JSON."""
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
        print(json.dumps(log_entry))


def setup_logging(
    log_level: str = "INFO",
    json_output: bool = False,
    log_file: Optional[str] = None
):
    """
    Set up logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Whether to output logs as JSON
        log_file: Path to log file, or None to log to stdout only
    """
    # Remove default loguru handler
    logger.remove()
    
    # Determine log format based on json_output
    if json_output:
        # Add JSON handler
        logger.add(JsonSink(), level=log_level)
    else:
        # Add console handler with colored output
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True
        )
    
    # Add file handler if specified
    if log_file:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Add rotating file handler
        logger.add(
            log_file,
            rotation="10 MB",  # Rotate when file reaches 10 MB
            retention="1 week",  # Keep logs for 1 week
            compression="zip",  # Compress rotated logs
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level
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
    """
    Intercepts standard library logging and redirects to loguru.
    This ensures all logs go through the same pipeline.
    """
    
    def emit(self, record):
        # Get corresponding loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
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
    """Generate a unique request ID for tracking."""
    return str(uuid.uuid4())


def get_logger_with_context(**context):
    """
    Get a logger with additional context.
    
    Args:
        **context: Context key-value pairs to add to all log messages
        
    Returns:
        Loguru logger with bound context
    """
    return logger.bind(**context)


# Example usage:
# setup_logging(log_level="DEBUG", json_output=True, log_file="logs/app.log")
# request_logger = get_logger_with_context(request_id=get_request_id())
# request_logger.info("Processing request")
