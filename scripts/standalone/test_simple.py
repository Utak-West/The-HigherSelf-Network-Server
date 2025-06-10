#!/usr/bin/env python3
"""
Simple test script to debug environment variables and NotionService
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent))

# Configure simple logging
# import logging # Replaced by loguru
from loguru import logger # Added for direct loguru usage
# logging.basicConfig(level=logging.INFO) # Handled by loguru setup in main or utils.logging_setup
# logger = logging.getLogger(__name__) # Replaced by global loguru logger

def main():
    # Load environment variables
    load_dotenv()
    
    # Print environment variables
    logger.info("Environment variables loaded:")
    logger.info(f"TEST_MODE = {os.environ.get('TEST_MODE')}")
    logger.info(f"TESTING = {os.environ.get('TESTING')}")
    logger.info(f"NOTION_API_TOKEN = {os.environ.get('NOTION_API_TOKEN')}")
    
    # Check if test mode condition is satisfied
    test_mode = os.environ.get('TEST_MODE', '').lower() == 'true' or os.environ.get('TESTING', '').lower() == 'true'
    logger.info(f"test_mode = {test_mode}")
    
    # Directly patch the NotionService to use a mock token in test mode
    os.environ['NOTION_API_TOKEN'] = 'mock_token_for_testing'
    logger.info(f"Set NOTION_API_TOKEN = {os.environ.get('NOTION_API_TOKEN')}")
    
    # Import NotionService
    from services.notion_service import NotionService
    
    try:
        logger.info("Trying to create NotionService.from_env()...")
        notion_service = NotionService.from_env()
        if notion_service:
            logger.info(f"SUCCESS: NotionService created")
            logger.info(f"Config token: {notion_service.config.token[:5]}...")
    except Exception as e:
        logger.error(f"ERROR: Could not create NotionService: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()