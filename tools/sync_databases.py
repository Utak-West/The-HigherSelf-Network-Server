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

import os
import sys
import asyncio
# import logging # Unused
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Add parent directory to path to allow importing from the server codebase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.notion_service import NotionService
from services.supabase_service import SupabaseService, SupabaseConfig
from services.database_sync_service import DatabaseSyncService, SyncResult
from models.base import NotionIntegrationConfig


# Initialize colorama for colored terminal output
init(autoreset=True)


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
                print_success(f"{model_name}: {success_count}/{total_count} successful ({success_rate:.1f}%)")
            elif success_rate >= 80:
                print_info(f"{model_name}: {success_count}/{total_count} successful ({success_rate:.1f}%)")
            else:
                print_warning(f"{model_name}: {success_count}/{total_count} successful ({success_rate:.1f}%)")

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
        print_error("Missing Notion API token. Please set NOTION_API_TOKEN environment variable.")
        sys.exit(1)

    # Create database mappings from environment variables
    db_mappings = {
        'BusinessEntity': os.environ.get('NOTION_BUSINESS_ENTITIES_DB', ''),
        'ContactProfile': os.environ.get('NOTION_CONTACTS_PROFILES_DB', ''),
        'CommunityMember': os.environ.get('NOTION_COMMUNITY_HUB_DB', ''),
        'ProductService': os.environ.get('NOTION_PRODUCTS_SERVICES_DB', ''),
        'WorkflowInstance': os.environ.get('NOTION_ACTIVE_WORKFLOW_INSTANCES_DB', ''),
        'MarketingCampaign': os.environ.get('NOTION_MARKETING_CAMPAIGNS_DB', ''),
        'FeedbackSurvey': os.environ.get('NOTION_FEEDBACK_SURVEYS_DB', ''),
        'RewardBounty': os.environ.get('NOTION_REWARDS_BOUNTIES_DB', ''),
        'Task': os.environ.get('NOTION_TASKS_DB', ''),
        'AgentCommunication': os.environ.get('NOTION_AGENT_COMMUNICATION_DB', ''),
        'Agent': os.environ.get('NOTION_AGENT_REGISTRY_DB', ''),
        'ApiIntegration': os.environ.get('NOTION_API_INTEGRATIONS_DB', ''),
        'DataTransformation': os.environ.get('NOTION_DATA_TRANSFORMATIONS_DB', ''),
        'NotificationTemplate': os.environ.get('NOTION_NOTIFICATIONS_TEMPLATES_DB', ''),
        'UseCase': os.environ.get('NOTION_USE_CASES_DB', ''),
        'Workflow': os.environ.get('NOTION_WORKFLOWS_LIBRARY_DB', ''),
    }

    # Check if all required database IDs are set
    missing_dbs = [name for name, id in db_mappings.items() if not id]
    if missing_dbs:
        print_warning(f"Missing Notion database IDs for: {', '.join(missing_dbs)}")
        print_warning("Some databases will not be synchronized.")

    notion_config = NotionIntegrationConfig(token=notion_token, database_mappings=db_mappings)
    notion_service = NotionService(notion_config)

    # Set up Supabase service
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_API_KEY")
    supabase_project_id = os.environ.get("SUPABASE_PROJECT_ID")

    if not supabase_url or not supabase_key or not supabase_project_id:
        print_error("Missing Supabase configuration. Please set SUPABASE_URL, SUPABASE_API_KEY, and SUPABASE_PROJECT_ID environment variables.")
        sys.exit(1)

    supabase_config = SupabaseConfig(url=supabase_url, api_key=supabase_key, project_id=supabase_project_id)
    supabase_service = SupabaseService(supabase_config)

    # Set up database sync service
    sync_service = DatabaseSyncService(notion_service, supabase_service)

    return notion_service, supabase_service, sync_service


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Database Synchronization Utility")
    parser.add_argument("--direction", choices=["notion_to_supabase", "supabase_to_notion", "both"], default="both",
                        help="Sync direction (default: both)")
    parser.add_argument("--model", help="Specific model to sync (e.g., BusinessEntity)")
    parser.add_argument("--since", help="Only sync records updated since this timestamp (ISO format)")
    args = parser.parse_args()

    print_header("\n=== Database Synchronization Utility ===\n")

    # Set up services
    notion_service, supabase_service, sync_service = await setup_services()

    # Parse since timestamp
    since = None
    if args.since:
        try:
            since = datetime.fromisoformat(args.since)
            print_info(f"Syncing records updated since: {since.isoformat()}")
        except ValueError:
            print_warning(f"Invalid timestamp format: {args.since}. Using default (30 days ago).")
            since = datetime.now() - timedelta(days=30)

    # Sync specific model or all models
    if args.model:
        print_info(f"Syncing model: {args.model}")

        # Import the model class
        try:
            # Try to import from notion_db_models first
            try:
                from models.notion_db_models import (
                    BusinessEntity, Agent, Workflow, WorkflowInstance,
                    ApiIntegration, DataTransformation, UseCase,
                    NotificationTemplate, AgentCommunication, Task
                )
                model_class = locals()[args.model]
            except (ImportError, KeyError):
                # If not found, try to import from notion_db_models_extended
                from models.notion_db_models_extended import (
                    ContactProfile, CommunityMember, ProductService,
                    MarketingCampaign, FeedbackSurvey, RewardBounty
                )
                model_class = locals()[args.model]

            # Sync the model
            results = {args.model: await sync_service.sync_all_records(model_class, args.direction, since)}
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
