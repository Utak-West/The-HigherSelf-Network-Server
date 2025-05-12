#!/usr/bin/env python3
"""
Debug script to diagnose issues with Notion database IDs.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
# import logging # Replaced by loguru
from loguru import logger # Added for direct loguru usage

# Configure basic logging
# logging.basicConfig(level=logging.INFO) # Handled by loguru setup in main or utils.logging_setup
# logger = logging.getLogger(__name__) # Replaced by global loguru logger

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent))

def main():
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    logger.info("==== Testing Configuration ====")
    logger.info(f"TEST_MODE = {os.environ.get('TEST_MODE')}")
    logger.info(f"TESTING = {os.environ.get('TESTING')}")
    
    # Check Notion credentials
    logger.info("\n==== Notion Credentials ====")
    token = os.environ.get('NOTION_API_TOKEN')
    logger.info(f"NOTION_API_TOKEN = {'set' if token else 'not set'}")
    if token:
        logger.info(f"Token value: {token[:5]}...{token[-5:] if len(token) > 10 else ''}")
    
    # Check database IDs
    logger.info("\n==== Notion Database IDs ====")
    databases = {
        'NOTION_BUSINESS_ENTITIES_DB': 'BusinessEntity',
        'NOTION_AGENT_REGISTRY_DB': 'Agent',
        'NOTION_WORKFLOWS_LIBRARY_DB': 'Workflow',
        'NOTION_ACTIVE_WORKFLOW_INSTANCES_DB': 'WorkflowInstance',
        'NOTION_API_INTEGRATIONS_DB': 'ApiIntegration',
        'NOTION_DATA_TRANSFORMATIONS_DB': 'DataTransformation',
        'NOTION_USE_CASES_DB': 'UseCase',
        'NOTION_NOTIFICATIONS_TEMPLATES_DB': 'NotificationTemplate',
        'NOTION_AGENT_COMMUNICATION_DB': 'AgentCommunication',
        'NOTION_TASKS_DB': 'Task',
        'NOTION_BEST_PRACTICES_DB': 'AgentBestPractices',
        'NOTION_WORKFLOW_PATTERNS_DB': 'WorkflowPatterns',
        'NOTION_TRAINING_RESULTS_DB': 'AgentTrainingResults'
    }
    
    missing_dbs = []
    set_dbs = []
    
    for env_var, model_name in databases.items():
        db_id = os.environ.get(env_var)
        if db_id:
            set_dbs.append(f"{model_name} ({env_var}): {db_id[:8]}...")
        else:
            missing_dbs.append(f"{model_name} ({env_var})")
    
    if set_dbs:
        logger.info("Configured database IDs:")
        for db in set_dbs:
            logger.info(f"  - {db}")
    
    if missing_dbs:
        logger.info("Missing database IDs:")
        for db in missing_dbs:
            logger.info(f"  - {db}")
    
    # Import NotionService and test creation
    try:
        logger.info("\n==== Testing NotionService Creation ====")
        from services.notion_service import NotionService
        from config.testing_mode import is_api_disabled
        
        logger.info(f"API disabled for Notion: {is_api_disabled('notion')}")
        
        notion_service = NotionService.from_env()
        logger.info(f"NotionService created successfully")
        logger.info(f"Config token: {notion_service.config.token[:5]}...")
        logger.info(f"Number of DB mappings: {len(notion_service.db_mappings)}")
        
        # Print empty db_mappings
        if notion_service.db_mappings:
            logger.info("Database mappings:")
            for model, db_id in notion_service.db_mappings.items():
                if db_id:
                    logger.info(f"  - {model}: {db_id}")
                else:
                    logger.info(f"  - {model}: <empty>")
    except Exception as e:
        logger.error(f"Error creating NotionService: {e}")
        import traceback
        traceback.print_exc()
    
    # Check if initialization would work in production
    logger.info("\n==== Production Readiness Check ====")
    if all(os.environ.get(db) for db in databases.keys()):
        logger.info("✅ All database IDs are set - system would work in production mode")
    else:
        logger.info("❌ Missing database IDs - system would fail in production mode")
        logger.info(f"Missing: {len(missing_dbs)}/{len(databases)} database IDs")

if __name__ == "__main__":
    main()