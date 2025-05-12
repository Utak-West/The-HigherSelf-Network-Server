#!/usr/bin/env python3
"""
Notion to Vector Store Synchronization Utility for The HigherSelf Network Server.

This script synchronizes Notion databases to the vector store for semantic search capabilities.
It can sync all databases or specific ones, with options for forced updates and time filters.
"""

import os
import sys
import asyncio
# import logging # Unused
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from colorama import init, Fore, Style

# Add parent directory to path to allow importing from the server codebase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.knowledge_service import KnowledgeService, get_knowledge_service
from knowledge.vector_store import get_vector_store
from knowledge.providers import provider_registry
from config.notion_databases import NOTION_DATABASES

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


async def check_services_health() -> bool:
    """
    Check the health of all required services.
    
    Returns:
        True if all services are healthy
    """
    print_header("\nChecking service health...\n")
    
    # Get services
    knowledge_service = get_knowledge_service()
    vector_store = get_vector_store()
    
    # Check knowledge service health
    knowledge_health = await knowledge_service.health_check()
    if knowledge_health["healthy"]:
        print_success("✓ Knowledge service is healthy")
    else:
        print_error(f"✗ Knowledge service is unhealthy: {knowledge_health.get('error', 'Unknown error')}")
        return False
    
    # Check vector store health
    vector_health = await vector_store.health_check()
    if vector_health["healthy"]:
        print_success("✓ Vector store is healthy")
    else:
        print_error(f"✗ Vector store is unhealthy: {vector_health.get('error', 'Unknown error')}")
        return False
    
    # Check embedding providers
    provider_result = await provider_registry.get_embeddings(["health check"])
    if provider_result["success"]:
        print_success(f"✓ Embedding provider ({provider_result['provider']}) is healthy")
    else:
        print_error("✗ No embedding providers are available")
        return False
    
    return True


async def sync_database(
    knowledge_service: KnowledgeService, 
    database_id: str, 
    database_name: str,
    modified_since: Optional[datetime] = None,
    force_update: bool = False
) -> List[str]:
    """
    Synchronize a Notion database to the vector store.
    
    Args:
        knowledge_service: KnowledgeService instance
        database_id: Notion database ID
        database_name: Name of the database (for display)
        modified_since: Only sync pages modified since this time
        force_update: Whether to force an update even if content hasn't changed
        
    Returns:
        List of embedding IDs that were created or updated
    """
    print_header(f"\nSynchronizing database: {database_name} ({database_id})\n")
    
    since_msg = f" modified since {modified_since.isoformat()}" if modified_since else ""
    force_msg = " (forced update)" if force_update else ""
    print_info(f"Syncing pages{since_msg}{force_msg}...")
    
    try:
        embedding_ids = await knowledge_service.sync_notion_database_to_vector(
            database_id, modified_since, force_update)
        
        print_success(f"✓ Synchronized {len(embedding_ids)} pages from {database_name}")
        return [str(eid) for eid in embedding_ids]
    except Exception as e:
        print_error(f"✗ Error synchronizing {database_name}: {e}")
        return []


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Notion to Vector Store Synchronization Utility")
    parser.add_argument(
        "--databases", 
        nargs='+', 
        help="Specific database names to sync (from config.notion_databases)"
    )
    parser.add_argument(
        "--since", 
        help="Only sync pages modified since this time (ISO format or relative like '1d', '12h')"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force update even if content hasn't changed"
    )
    parser.add_argument(
        "--check-health-only", 
        action="store_true", 
        help="Only check service health without syncing"
    )
    args = parser.parse_args()
    
    print_header("\n=== Notion to Vector Store Synchronization ===\n")
    
    # Check service health
    services_healthy = await check_services_health()
    if not services_healthy:
        print_error("\nServices are not healthy. Cannot proceed with synchronization.")
        sys.exit(1)
    
    if args.check_health_only:
        print_success("\nHealth check completed successfully.")
        return
    
    # Parse the since argument
    modified_since = None
    if args.since:
        if args.since.endswith('d'):
            # Relative days
            days = int(args.since[:-1])
            modified_since = datetime.now() - timedelta(days=days)
        elif args.since.endswith('h'):
            # Relative hours
            hours = int(args.since[:-1])
            modified_since = datetime.now() - timedelta(hours=hours)
        else:
            # ISO format
            try:
                modified_since = datetime.fromisoformat(args.since)
            except ValueError:
                print_error(f"Invalid time format: {args.since}. Use ISO format or relative time like '1d', '12h'")
                sys.exit(1)
    
    # Get knowledge service
    knowledge_service = get_knowledge_service()
    await knowledge_service.initialize()
    
    # Determine which databases to sync
    databases_to_sync = {}
    if args.databases:
        # Sync specific databases
        for db_name in args.databases:
            if db_name in NOTION_DATABASES:
                db_id = NOTION_DATABASES[db_name].get("id")
                if db_id:
                    databases_to_sync[db_name] = db_id
                else:
                    print_warning(f"Database '{db_name}' has no ID in configuration")
            else:
                print_warning(f"Database '{db_name}' not found in configuration")
    else:
        # Sync all databases
        for db_name, db_info in NOTION_DATABASES.items():
            db_id = db_info.get("id")
            if db_id:
                databases_to_sync[db_name] = db_id
    
    if not databases_to_sync:
        print_error("No valid databases to synchronize")
        sys.exit(1)
    
    # Sync each database
    total_count = 0
    since_msg = f" modified since {modified_since.isoformat()}" if modified_since else ""
    print_header(f"\nSynchronizing {len(databases_to_sync)} databases{since_msg}...\n")
    
    for db_name, db_id in databases_to_sync.items():
        embedding_ids = await sync_database(
            knowledge_service, db_id, db_name, modified_since, args.force)
        total_count += len(embedding_ids)
    
    print_header("\n=== Synchronization Complete ===\n")
    print_success(f"Total pages synchronized: {total_count}")


if __name__ == "__main__":
    asyncio.run(main())