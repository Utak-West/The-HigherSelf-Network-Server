"""
Testing mode configuration for The HigherSelf Network Server.

This module provides functionality to disable external API calls during testing
to prevent unintended interactions with third-party services.
"""

import os
from typing import Dict, Optional, List, Set

class TestingMode:
    """
    Controls API access during testing to prevent real API calls.
    """

    _instance = None
    _testing_enabled: bool = False
    _disabled_apis: Set[str] = set()
    _api_call_log: List[Dict] = []

    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super(TestingMode, cls).__new__(cls)
        return cls._instance

    @classmethod
    def enable_testing_mode(cls, disabled_apis: Optional[List[str]] = None):
        """
        Enable testing mode, optionally specifying which APIs to disable.

        Args:
            disabled_apis: List of API names to disable (e.g., ["notion", "openai", "perplexity"])
                          If None, all APIs are disabled by default
        """
        cls._testing_enabled = True

        # Default APIs to disable if not specified
        default_apis = [
            "notion", "openai", "anthropic", "perplexity",
            "beehiiv", "typeform", "woocommerce", "amelia",
            "google_calendar", "hubspot", "airtable", "tutorlm",
            "plaud", "snov", "supabase"
        ]

        if disabled_apis is None:
            cls._disabled_apis = set(default_apis)
        else:
            cls._disabled_apis = set(disabled_apis)

        # Set environment flag
        os.environ["TESTING_MODE"] = "1"

        print(f"✅ Testing mode enabled. Disabled APIs: {', '.join(sorted(cls._disabled_apis))}")

    @classmethod
    def disable_testing_mode(cls):
        """Disable testing mode, allowing real API calls."""
        cls._testing_enabled = False
        cls._disabled_apis.clear()
        cls._api_call_log.clear()

        # Remove environment flag
        if "TESTING_MODE" in os.environ:
            del os.environ["TESTING_MODE"]

        print("✅ Testing mode disabled. All APIs are now active.")

    @classmethod
    def is_testing_mode(cls) -> bool:
        """Check if testing mode is enabled."""
        return cls._testing_enabled or os.environ.get("TEST_MODE", "").lower() == "true"

    @classmethod
    def is_api_disabled(cls, api_name: str) -> bool:
        """
        Check if a specific API is disabled.

        Args:
            api_name: Name of the API to check

        Returns:
            True if the API is disabled, False otherwise
        """
        return cls.is_testing_mode() and api_name.lower() in cls._disabled_apis

    @classmethod
    def get_disabled_apis(cls) -> Set[str]:
        """Get the set of disabled APIs."""
        return cls._disabled_apis

    @classmethod
    def add_disabled_api(cls, api_name: str) -> None:
        """Add an API to the disabled list."""
        cls._disabled_apis.add(api_name.lower())

    @classmethod
    def log_attempted_api_call(cls, api_name: str, endpoint: str, method: str, params: Dict = None):
        """
        Log attempted API calls during testing mode.

        Args:
            api_name: Name of the API (e.g., "notion")
            endpoint: API endpoint called
            method: HTTP method used
            params: Parameters passed to the API
        """
        if cls.is_testing_mode():
            log_entry = {
                "api": api_name,
                "endpoint": endpoint,
                "method": method,
                "params": params or {},
                "blocked": api_name.lower() in cls._disabled_apis
            }
            cls._api_call_log.append(log_entry)

    @classmethod
    def get_api_call_log(cls) -> List[Dict]:
        """Get the log of attempted API calls during testing mode."""
        return cls._api_call_log.copy()

    @classmethod
    def clear_api_call_log(cls):
        """Clear the API call log."""
        cls._api_call_log.clear()


# Convenience functions
def enable_testing_mode(disabled_apis: Optional[List[str]] = None):
    """Enable testing mode with specified disabled APIs."""
    TestingMode.enable_testing_mode(disabled_apis)

def disable_testing_mode():
    """Disable testing mode."""
    TestingMode.disable_testing_mode()

def is_api_disabled(api_name: str) -> bool:
    """Check if an API is disabled."""
    return TestingMode.is_api_disabled(api_name)

def is_testing_mode() -> bool:
    """Check if testing mode is enabled."""
    return TestingMode.is_testing_mode()
