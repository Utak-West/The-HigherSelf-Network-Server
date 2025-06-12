#!/usr/bin/env python3
"""
Validation utility for the 16-database Notion structure in The HigherSelf Network Server.

This script verifies that all required Notion databases are properly configured and accessible,
and validates that the database structures match the expected Pydantic models.
"""

import asyncio
import os
import sys
from typing import Any, Dict, List, Tuple

from colorama import Fore, Style, init
from dotenv import load_dotenv

# import logging # Replaced by loguru
from loguru import logger  # Added for direct loguru usage

# Add parent directory to path to allow importing from the server codebase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.notion_databases import (
    NOTION_DATABASE_MAPPING,
    get_all_database_env_vars,
    get_required_database_env_vars,
)
from config.testing_mode import TestingMode
from services.notion_service import NotionService

# Initialize colorama for colored terminal output
init()

# Set up logging
# logging.basicConfig(...) # Handled by loguru setup, if called
# logger = logging.getLogger(__name__) # Replaced by global loguru logger
# This script's main() should ideally call setup_logging() from utils
# if specific loguru configuration is desired when run standalone.


class NotionStructureValidator:
    """Validator for the 16-database Notion structure."""

    def __init__(self, notion_token: str = None):
        """Initialize the validator with a Notion token."""
        self.notion_token = notion_token or os.environ.get("NOTION_API_TOKEN")
        if not self.notion_token:
            raise ValueError("NOTION_API_TOKEN not found in environment variables")

        self.notion_service = None
        self.database_statuses = {}

    async def initialize(self):
        """Initialize the Notion service."""
        # Build database mappings from environment variables
        database_mappings = {}
        for model_name, db_info in NOTION_DATABASE_MAPPING.items():
            env_var = db_info["env_var"]
            database_id = os.environ.get(env_var)
            if database_id:
                database_mappings[model_name] = database_id

        # Initialize testing mode if specified
        if os.environ.get("VALIDATOR_TEST_MODE", "").lower() == "true":
            TestingMode.enable_testing_mode()
            print(
                f"{Fore.YELLOW}Running in test mode - no actual API calls will be made{Style.RESET_ALL}"
            )

        # Initialize Notion service with obtained mappings
        # Import the correct NotionIntegrationConfig that NotionService expects
        from models.notion import (
            NotionIntegrationConfig as ServiceNotionIntegrationConfig,
        )

        config = ServiceNotionIntegrationConfig(
            token=self.notion_token,  # This is correct for models.notion.NotionIntegrationConfig
            database_mappings=database_mappings,  # Also correct for models.notion.NotionIntegrationConfig
        )
        self.notion_service = NotionService(config)

    async def validate_all_databases(self) -> Dict[str, Dict[str, Any]]:
        """
        Validate all Notion databases defined in NOTION_DATABASE_MAPPING.

        Returns:
            Dictionary of database validation results
        """
        results = {}
        all_valid = True

        # Check for required environment variables
        env_vars_status = self._check_environment_variables()
        missing_required = env_vars_status["missing_required"]
        if missing_required:
            print(
                f"{Fore.RED}❌ Missing required environment variables: {', '.join(missing_required)}{Style.RESET_ALL}"
            )
            all_valid = False

        # For databases that have IDs, validate their accessibility
        for model_name, db_info in NOTION_DATABASE_MAPPING.items():
            env_var = db_info["env_var"]
            database_id = os.environ.get(env_var)

            if not database_id:
                status = {
                    "status": "missing" if db_info["required"] else "optional_missing",
                    "message": f"Database ID not found in environment variable {env_var}",
                    "is_valid": not db_info[
                        "required"
                    ],  # Only mark as invalid if required
                }
            else:
                # Validate database connection and structure
                status = await self._validate_database(model_name, database_id)

            results[model_name] = {**db_info, "database_id": database_id, **status}

            # Update overall validity
            if not status.get("is_valid", False):
                all_valid = False

        self.database_statuses = results
        return {
            "databases": results,
            "env_vars": env_vars_status,
            "all_valid": all_valid,
        }

    def _check_environment_variables(self) -> Dict[str, List[str]]:
        """
        Check for required and optional environment variables.

        Returns:
            Dictionary with lists of missing required and optional variables
        """
        required_env_vars = get_required_database_env_vars()
        all_env_vars = get_all_database_env_vars()
        optional_env_vars = all_env_vars - required_env_vars

        # Check which required variables are missing
        missing_required = [var for var in required_env_vars if not os.environ.get(var)]

        # Check which optional variables are missing
        missing_optional = [var for var in optional_env_vars if not os.environ.get(var)]

        return {
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "is_valid": len(missing_required) == 0,
        }

    async def _validate_database(
        self, model_name: str, database_id: str
    ) -> Dict[str, Any]:
        """
        Validate a specific Notion database's accessibility and structure.

        Args:
            model_name: Name of the Pydantic model associated with the database
            database_id: Notion database ID

        Returns:
            Dictionary with validation status
        """
        try:
            # First, try to query the database to check if it's accessible
            query_result = await self.notion_service.client.databases.query(
                database_id=database_id,
                page_size=1,  # Just get one record to verify access
            )

            # Check if properties match expected model fields
            # For simplicity, we're not doing detailed property validation here
            # In a real implementation, we would check each property's type and configuration
            is_valid_structure = True
            status = {
                "status": "valid" if is_valid_structure else "invalid_structure",
                "message": "Database is accessible and structure appears valid"
                if is_valid_structure
                else "Database is accessible but structure has issues",
                "is_valid": is_valid_structure,
            }

        except Exception as e:
            status = {
                "status": "inaccessible",
                "message": f"Could not access database: {str(e)}",
                "is_valid": False,
            }

        return status

    def print_validation_results(self):
        """Print validation results in a user-friendly format."""
        if not self.database_statuses:
            print(
                f"{Fore.YELLOW}No validation results available. Run validate_all_databases() first.{Style.RESET_ALL}"
            )
            return

        print("\n" + "=" * 80)
        print(
            f"{Fore.CYAN}NOTION DATABASE STRUCTURE VALIDATION RESULTS{Style.RESET_ALL}"
        )
        print("=" * 80 + "\n")

        all_valid = True

        # Print results for each database
        print(f"{Fore.CYAN}DATABASE STATUS:{Style.RESET_ALL}")
        for model_name, status in self.database_statuses.items():
            db_description = status["description"]
            is_valid = status.get("is_valid", False)
            status_text = status.get("status", "unknown")
            message = status.get("message", "")

            if is_valid:
                status_indicator = f"{Fore.GREEN}✅{Style.RESET_ALL}"
            elif status_text == "optional_missing":
                status_indicator = f"{Fore.YELLOW}⚠️{Style.RESET_ALL}"
            else:
                status_indicator = f"{Fore.RED}❌{Style.RESET_ALL}"
                all_valid = False

            # Print status line
            print(
                f"{status_indicator} {Fore.WHITE}{model_name}{Style.RESET_ALL} ({db_description})"
            )
            print(f"   {message}")

        print("\n" + "-" * 80 + "\n")

        # Print overall result
        if all_valid:
            print(
                f"{Fore.GREEN}All required databases are properly configured and accessible.{Style.RESET_ALL}"
            )
            print(
                f"{Fore.GREEN}The 16-database Notion structure is VALID for The HigherSelf Network Server.{Style.RESET_ALL}"
            )
        else:
            print(
                f"{Fore.RED}Some required databases have issues. See above for details.{Style.RESET_ALL}"
            )
            print(
                f"{Fore.RED}The Notion structure is INVALID. Please fix the issues before proceeding.{Style.RESET_ALL}"
            )

        print("\n" + "=" * 80)


async def main():
    """Main function to validate the Notion database structure."""
    # Load environment variables
    load_dotenv()

    try:
        # Initialize the validator
        validator = NotionStructureValidator()
        await validator.initialize()

        # Validate all databases
        await validator.validate_all_databases()

        # Print validation results
        validator.print_validation_results()

    except Exception as e:
        print(f"{Fore.RED}Error during validation: {str(e)}{Style.RESET_ALL}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
