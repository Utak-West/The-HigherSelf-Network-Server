"""Logging utilities for The HigherSelf Network Server.

This module provides standardized logging capabilities, including compatibility
with both loguru and the standard Python logging module.
"""

import logging
from typing import Any, Dict, Optional

# Try to import loguru, fall back to standard logging if not available
try:
    from loguru import logger as loguru_logger

    USING_LOGURU = True
except ImportError:
    USING_LOGURU = False


class CompatLogger:
    """Compatible logger that works with both loguru and standard logging.

    This class provides a consistent interface regardless of whether loguru
    is available, allowing code to use the same logging API without worrying
    about which implementation is used.
    """

    def __init__(self, name: str):
        """Initialize compatible logger with the given name.

        Args:
            name: The logger name, typically __name__ of the calling module
        """
        self._name = name
        if USING_LOGURU:
            self._logger = loguru_logger
        else:
            self._logger = logging.getLogger(name)
            # Configure basic logging if not already configured
            if not logging.getLogger().handlers:
                logging.basicConfig(
                    level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                )

    def bind(self, **kwargs: Any) -> "CompatLogger":
        """Create a logger with bound context values.

        Args:
            **kwargs: Context key-value pairs to bind to the logger

        Returns:
            CompatLogger: A logger with the bound context
        """
        if USING_LOGURU:
            self._logger = self._logger.bind(**kwargs)
        return self

    def info(self, message: str) -> None:
        """Log an info level message.

        Args:
            message: The message to log
        """
        if USING_LOGURU:
            self._logger.info(message)
        else:
            self._logger.info(message)

    def warning(self, message: str) -> None:
        """Log a warning level message.

        Args:
            message: The message to log
        """
        if USING_LOGURU:
            self._logger.warning(message)
        else:
            self._logger.warning(message)

    def error(self, message: str) -> None:
        """Log an error level message.

        Args:
            message: The message to log
        """
        if USING_LOGURU:
            self._logger.error(message)
        else:
            self._logger.error(message)

    def debug(self, message: str) -> None:
        """Log a debug level message.

        Args:
            message: The message to log
        """
        if USING_LOGURU:
            self._logger.debug(message)
        else:
            self._logger.debug(message)

    def exception(self, message: str) -> None:
        """Log an exception with traceback.

        Args:
            message: The message to log with the exception
        """
        if USING_LOGURU:
            self._logger.exception(message)
        else:
            self._logger.exception(message)


def get_logger(name: str) -> CompatLogger:
    """Get a compatible logger instance.

    Args:
        name: The logger name, typically __name__ of the calling module

    Returns:
        CompatLogger: A compatible logger instance
    """
    return CompatLogger(name)
