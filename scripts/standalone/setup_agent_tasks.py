#!/usr/bin/env python3
"""
Setup Agent Tasks Database in Notion

This script sets up a Notion database for AI agent tasks.
It creates a new database in the specified parent page.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

from tools.notion_agent_tasks import NotionTasksManager
from loguru import logger

def setup_notion_database(parent_page_id=None):
    """
    Set up the Notion database for agent tasks.
    
    Args:
        parent_page_id: The ID of the parent page where the database will be created.
            If not provided, it will use the NOTION_PARENT_PAGE_ID from the environment.
    
    Returns:
        The ID of the created database.
    """
    # Load environment variables
    load_dotenv()
    
    # Get parent page ID
    parent_id = parent_page_id or os.environ.get("NOTION_PARENT_PAGE_ID")
    
    if not parent_id:
        logger.error("No parent page ID provided. Please set NOTION_PARENT_PAGE_ID in .env or provide it as an argument.")
        sys.exit(1)
    
    # Check if Notion API token is set
    if not os.environ.get("NOTION_API_TOKEN"):
        logger.error("NOTION_API_TOKEN is not set in the environment. Please set it in .env.")
        sys.exit(1)
    
    # Create the database
    manager = NotionTasksManager()
    
    try:
        database_id = manager.setup_database(parent_id)
        logger.info(f"Successfully created Notion database with ID: {database_id}")
        logger.info("The database ID has been added to your .env file as NOTION_AGENT_TASKS_DB.")
        
        # Print instructions
        print("\n" + "="*80)
        print("SETUP COMPLETE")
        print("="*80)
        print("\nYour Notion Agent Tasks database has been created!")
        print(f"\nDatabase ID: {database_id}")
        print(f"\nYou can access it at: https://notion.so/{database_id.replace('-', '')}")
        print("\nThis database will be used to track AI agent tasks and their results.")
        print("\nNext steps:")
        print("1. Share this database with your staff")
        print("2. Deploy the frontend to allow staff to create tasks")
        print("3. Update your .env file with any additional configuration")
        print("="*80 + "\n")
        
        return database_id
    
    except Exception as e:
        logger.error(f"Error creating Notion database: {e}")
        sys.exit(1)

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Set up a Notion database for AI agent tasks.")
    parser.add_argument("--parent-id", help="The ID of the parent page where the database will be created.")
    
    args = parser.parse_args()
    
    setup_notion_database(args.parent_id)

if __name__ == "__main__":
    main()
