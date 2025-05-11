#!/usr/bin/env python3
"""
Supabase Database Setup Utility for The HigherSelf Network Server.

This script creates the necessary tables in Supabase to align with the 16-database Notion structure.
It reads SQL migration files and executes them against the Supabase database.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv
import httpx
import argparse
from colorama import init, Fore, Style

# Add parent directory to path to allow importing from the server codebase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.supabase_service import SupabaseService, SupabaseConfig


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


class SupabaseDatabaseSetup:
    """Utility for setting up Supabase database tables."""
    
    def __init__(self, supabase_service: SupabaseService):
        """
        Initialize the Supabase database setup utility.
        
        Args:
            supabase_service: SupabaseService instance
        """
        self.supabase_service = supabase_service
        self.logger = logging.getLogger(__name__)
    
    async def execute_sql_file(self, file_path: str) -> bool:
        """
        Execute a SQL file against the Supabase database.
        
        Args:
            file_path: Path to the SQL file
            
        Returns:
            True if execution was successful
        """
        try:
            # Read the SQL file
            with open(file_path, 'r') as f:
                sql = f.read()
            
            # Execute the SQL
            await self.supabase_service._make_request(
                method="POST",
                path=f"/v1/projects/{self.supabase_service.project_id}/database/query",
                data={"query": sql}
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Error executing SQL file {file_path}: {e}")
            return False
    
    async def verify_tables(self) -> Dict[str, bool]:
        """
        Verify that all required tables exist in the Supabase database.
        
        Returns:
            Dictionary mapping table names to existence status
        """
        try:
            # Query for all tables in the public schema
            response = await self.supabase_service._make_request(
                method="POST",
                path=f"/v1/projects/{self.supabase_service.project_id}/database/query",
                data={"query": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"}
            )
            
            # Extract table names from response
            tables = [row["table_name"] for row in response.get("data", [])]
            
            # Check if all required tables exist
            required_tables = [
                "business_entities",
                "contacts_profiles",
                "community_members",
                "products_services",
                "workflow_instances",
                "marketing_campaigns",
                "feedback_surveys",
                "rewards_bounties",
                "tasks",
                "agent_communication_patterns",
                "agents",
                "api_integrations",
                "data_transformations",
                "notification_templates",
                "use_cases",
                "workflows"
            ]
            
            return {table: table in tables for table in required_tables}
        except Exception as e:
            self.logger.error(f"Error verifying tables: {e}")
            return {table: False for table in required_tables}
    
    async def setup_database(self) -> bool:
        """
        Set up the Supabase database by executing all migration files.
        
        Returns:
            True if setup was successful
        """
        try:
            # Get the migration files
            migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "migrations")
            migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith(".sql")])
            
            if not migration_files:
                self.logger.error("No migration files found")
                return False
            
            # Execute each migration file
            for file_name in migration_files:
                file_path = os.path.join(migrations_dir, file_name)
                print_info(f"Executing migration: {file_name}")
                success = await self.execute_sql_file(file_path)
                
                if not success:
                    print_error(f"Failed to execute migration: {file_name}")
                    return False
                
                print_success(f"Successfully executed migration: {file_name}")
            
            # Verify tables
            table_status = await self.verify_tables()
            all_tables_exist = all(table_status.values())
            
            if all_tables_exist:
                print_success("All required tables exist in the database")
            else:
                missing_tables = [table for table, exists in table_status.items() if not exists]
                print_warning(f"Missing tables: {', '.join(missing_tables)}")
            
            return all_tables_exist
        except Exception as e:
            self.logger.error(f"Error setting up database: {e}")
            return False


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Supabase Database Setup Utility")
    parser.add_argument("--url", help="Supabase URL")
    parser.add_argument("--key", help="Supabase API key")
    parser.add_argument("--project-id", help="Supabase project ID")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Get Supabase configuration
    url = args.url or os.environ.get("SUPABASE_URL")
    api_key = args.key or os.environ.get("SUPABASE_API_KEY")
    project_id = args.project_id or os.environ.get("SUPABASE_PROJECT_ID")
    
    if not url or not api_key or not project_id:
        print_error("Missing Supabase configuration. Please provide URL, API key, and project ID.")
        sys.exit(1)
    
    print_header("\n=== Supabase Database Setup ===\n")
    print_info(f"Supabase URL: {url}")
    print_info(f"Supabase Project ID: {project_id}")
    
    # Create Supabase service
    config = SupabaseConfig(url=url, api_key=api_key, project_id=project_id)
    supabase_service = SupabaseService(config)
    
    # Create database setup utility
    setup = SupabaseDatabaseSetup(supabase_service)
    
    # Set up database
    print_header("\nSetting up database...")
    success = await setup.setup_database()
    
    if success:
        print_header("\n=== Database Setup Complete ===\n")
        print_success("All tables have been created successfully.")
    else:
        print_header("\n=== Database Setup Failed ===\n")
        print_error("Failed to set up database. Please check the logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
