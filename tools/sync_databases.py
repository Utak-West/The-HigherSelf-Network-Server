#!/usr/bin/env python3
"""
Database Synchronization Utility for The HigherSelf Network Server.

This script synchronizes data between Notion databases and Supabase tables,
ensuring that data is consistent across both systems.

Usage:
    python -m tools.sync_databases [--direction DIRECTION] [--model MODEL] [--since TIMESTAMP]

Options:
    --direction {notion_to_supabase,supabase_to_notion,both}
                        Sync direction (default: both)
    --model MODEL       Specific model to sync (e.g., BusinessEntity)
    --since TIMESTAMP   Only sync records updated since this timestamp (ISO format)
                        Example: 2023-07-15T00:00:00

Examples:
    # Sync all models in both directions
    python -m tools.sync_databases

    # Sync only from Notion to Supabase
    python -m tools.sync_databases --direction notion_to_supabase

    # Sync only BusinessEntity model
    python -m tools.sync_databases --model BusinessEntity

    # Sync only records updated in the last 24 hours
    python -m tools.sync_databases --since $(date -u -v-1d +"%Y-%m-%dT%H:%M:%S")
"""

# import logging # Unused
import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from colorama import Fore, Style, init
from dotenv import load_dotenv

# Add parent directory to path to allow importing from the server codebase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.base import NotionIntegrationConfig
from services.database_sync_service import DatabaseSyncService, SyncResult
from services.notion_service import NotionService
from services.supabase_service import SupabaseConfig, SupabaseService
from utils.logging_setup import setup_logging

try:
    # Try to import from the new settings_v2 module first
    from config.settings_v2 import reload_settings, settings

    print("Using Pydantic v2 settings")
except ImportError:
    # Fall back to the original settings module
    from config.settings import reload_settings, settings

    print("Using Pydantic v1 settings")
from loguru import logger

# Initialize colorama for colored terminal output
init(autoreset=True)


def configure_script_logging():
    """Configure logging for this script using global settings."""
    # log_level = settings.server.log_level.value # Temporarily override for testing
    forced_log_level = "DEBUG"
    json_logs = settings.server.json_logs
    log_file = settings.server.log_file

    setup_logging(
        log_level=forced_log_level,  # Use forced_log_level
        json_output=json_logs,
        log_file=log_file,
    )
    # Using loguru's logger directly after setup
    logger.info(
        f"Script logging FORCED to level: {forced_log_level} (original from settings: {settings.server.log_level.value})"
    )
    if json_logs:
        logger.info("JSON structured logging enabled for script.")
    if log_file:
        logger.info(f"Script logging to file: {log_file}")

    logger.debug(
        "This is a DEBUG message directly from configure_script_logging after forcing level to DEBUG."
    )


def print_header(message: str) -> None:
    """Print a header message in blue."""
    print(Fore.BLUE + Style.BRIGHT + message)


def print_success(message: str) -> None:
    """Print a success message in green."""
    print(Fore.GREEN + message)


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    print(Fore.YELLOW + message)


def print_error(message: str) -> None:
    """Print an error message in red."""
    print(Fore.RED + Style.BRIGHT + message)


def print_info(message: str) -> None:
    """Print an info message in cyan."""
    print(Fore.CYAN + message)


def format_sync_results(results: Dict[str, List[SyncResult]]) -> None:
    """
    Format and print sync results.

    Args:
        results: Dictionary mapping model names to lists of SyncResult instances
    """
    print_header("\n=== Sync Results ===\n")

    for model_name, model_results in results.items():
        success_count = sum(1 for r in model_results if r.success)
        total_count = len(model_results)

        if total_count == 0:
            print_info(f"{model_name}: No records to sync")
        else:
            success_rate = (success_count / total_count) * 100

            if success_rate == 100:
                print_success(
                    f"{model_name}: {success_count}/{total_count} successful ({success_rate:.1f}%)"
                )
            elif success_rate >= 80:
                print_info(
                    f"{model_name}: {success_count}/{total_count} successful ({success_rate:.1f}%)"
                )
            else:
                print_warning(
                    f"{model_name}: {success_count}/{total_count} successful ({success_rate:.1f}%)"
                )

        # Print errors
        errors = [r for r in model_results if not r.success]
        if errors:
            for error in errors[:3]:  # Show at most 3 errors per model
                print_error(f"  - Error: {error.error_message}")

            if len(errors) > 3:
                print_warning(f"  ... and {len(errors) - 3} more errors")


async def setup_services() -> tuple:
    """
    Set up the required services.

    Returns:
        Tuple of (NotionService, SupabaseService, DatabaseSyncService)
    """
    # Load environment variables
    load_dotenv()

    # Set up Notion service
    notion_token = os.environ.get("NOTION_API_TOKEN")
    if not notion_token:
        print_error(
            "Missing Notion API token. Please set NOTION_API_TOKEN environment variable."
        )
        sys.exit(1)

    # Create database mappings from environment variables
    db_mappings = {
        "BusinessEntity": os.environ.get("NOTION_BUSINESS_ENTITIES_DB", ""),
        "ContactProfile": os.environ.get("NOTION_CONTACTS_PROFILES_DB", ""),
        "CommunityMember": os.environ.get("NOTION_COMMUNITY_HUB_DB", ""),
        "ProductService": os.environ.get("NOTION_PRODUCTS_SERVICES_DB", ""),
        "WorkflowInstance": os.environ.get("NOTION_ACTIVE_WORKFLOW_INSTANCES_DB", ""),
        "MarketingCampaign": os.environ.get("NOTION_MARKETING_CAMPAIGNS_DB", ""),
        "FeedbackSurvey": os.environ.get("NOTION_FEEDBACK_SURVEYS_DB", ""),
        "RewardBounty": os.environ.get("NOTION_REWARDS_BOUNTIES_DB", ""),
        "Task": os.environ.get("NOTION_TASKS_DB", ""),
        "AgentCommunication": os.environ.get("NOTION_AGENT_COMMUNICATION_DB", ""),
        "Agent": os.environ.get("NOTION_AGENT_REGISTRY_DB", ""),
        "ApiIntegration": os.environ.get("NOTION_API_INTEGRATIONS_DB", ""),
        "DataTransformation": os.environ.get("NOTION_DATA_TRANSFORMATIONS_DB", ""),
        "NotificationTemplate": os.environ.get("NOTION_NOTIFICATIONS_TEMPLATES_DB", ""),
        "UseCase": os.environ.get("NOTION_USE_CASES_DB", ""),
        "Workflow": os.environ.get("NOTION_WORKFLOWS_LIBRARY_DB", ""),
    }

    # Check if all required database IDs are set
    missing_dbs = [name for name, id in db_mappings.items() if not id]
    if missing_dbs:
        print_warning(f"Missing Notion database IDs for: {', '.join(missing_dbs)}")
        print_warning("Some databases will not be synchronized.")

    notion_config = NotionIntegrationConfig(
        token=notion_token, database_mappings=db_mappings
    )
    notion_service = NotionService(notion_config)

    # Set up Supabase service
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_API_KEY")
    supabase_project_id = os.environ.get("SUPABASE_PROJECT_ID")

    if not supabase_url or not supabase_key or not supabase_project_id:
        print_error(
            "Missing Supabase configuration. Please set SUPABASE_URL, SUPABASE_API_KEY, and SUPABASE_PROJECT_ID environment variables."
        )
        sys.exit(1)

    supabase_config = SupabaseConfig(
        url=supabase_url, api_key=supabase_key, project_id=supabase_project_id
    )
    supabase_service = SupabaseService(supabase_config)

    # Set up database sync service
    sync_service = DatabaseSyncService(notion_service, supabase_service)

    return notion_service, supabase_service, sync_service


async def main():
    """Main function."""
    # Load .env file and reload settings to ensure LOG_LEVEL is respected
    load_dotenv()
    reload_settings()  # Reload settings after .env is loaded

    # Configure logging first, now using potentially updated settings
    configure_script_logging()

    # Check if we're in test mode and handle accordingly
    from config.testing_mode import (
        TestingMode,
        enable_testing_mode,
        is_api_disabled,
        is_testing_mode,
    )

    if is_testing_mode():
        print_info("Running in TEST_MODE. API calls will be simulated.")
        # Make sure both Notion and Supabase APIs are disabled
        if not is_api_disabled("notion") or not is_api_disabled("supabase"):
            print_info("Enabling testing mode with Notion and Supabase APIs disabled.")
            # Force disable both Notion and Supabase APIs
            TestingMode.add_disabled_api("notion")
            TestingMode.add_disabled_api("supabase")
            logger.debug(
                f"Disabled APIs in testing mode: {TestingMode.get_disabled_apis()}"
            )

    # Force disable APIs in testing mode if environment variables are set
    if os.environ.get("TEST_MODE", "").lower() == "true":
        if os.environ.get("DISABLE_APIS", "").lower().find("notion") != -1:
            TestingMode.add_disabled_api("notion")

        if os.environ.get("DISABLE_APIS", "").lower().find("supabase") != -1:
            TestingMode.add_disabled_api("supabase")

    parser = argparse.ArgumentParser(description="Database Synchronization Utility")
    parser.add_argument(
        "--direction",
        choices=["notion_to_supabase", "supabase_to_notion", "both"],
        default="both",
        help="Sync direction (default: both)",
    )
    parser.add_argument("--model", help="Specific model to sync (e.g., BusinessEntity)")
    parser.add_argument(
        "--since", help="Only sync records updated since this timestamp (ISO format)"
    )
    args = parser.parse_args()

    # Using loguru's logger for script-level info after setup
    logger.info("\n=== Database Synchronization Utility Starting ===\n")

    # Set up services
    notion_service, supabase_service, sync_service = await setup_services()

    # Parse since timestamp
    since = None
    if args.since:
        try:
            since = datetime.fromisoformat(args.since)
            print_info(f"Syncing records updated since: {since.isoformat()}")
        except ValueError:
            print_warning(
                f"Invalid timestamp format: {args.since}. Using default (30 days ago)."
            )
            since = datetime.now() - timedelta(days=30)

    # Sync specific model or all models
    if args.model:
        print_info(f"Syncing model: {args.model}")

        # Import the model class
        try:
            # Try to import from notion_db_models first
            try:
                from models.notion_db_models import (
                    Agent,
                    AgentCommunication,
                    ApiIntegration,
                    BusinessEntity,
                    DataTransformation,
                    NotificationTemplate,
                    Task,
                    UseCase,
                    Workflow,
                    WorkflowInstance,
                )

                model_class = locals()[args.model]
            except (ImportError, KeyError):
                # If not found, try to import from notion_db_models_extended
                from models.notion_db_models_extended import (
                    CommunityMember,
                    ContactProfile,
                    FeedbackSurvey,
                    MarketingCampaign,
                    ProductService,
                    RewardBounty,
                )

                model_class = locals()[args.model]

            # Sync the model
            results = {
                args.model: await sync_service.sync_all_records(
                    model_class, args.direction, since
                )
            }
            format_sync_results(results)
        except (ImportError, KeyError):
            print_error(f"Model not found: {args.model}")
            sys.exit(1)
    else:
        print_info(f"Syncing all models in direction: {args.direction}")
        results = await sync_service.sync_all_databases(args.direction, since)
        format_sync_results(results)

    print_header("\n=== Synchronization Complete ===\n")


if __name__ == "__main__":
    asyncio.run(main())
