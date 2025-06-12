#!/usr/bin/env python3
"""
Test script to debug environment variables from main.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Set up the directory structure the same way as main.py
sys.path.append(str(Path(__file__).parent))
from loguru import logger


def main():
    # Load environment variables just like in main.py
    load_dotenv()

    # Print all environment variables
    logger.info("Environment variables loaded:")
    logger.info(f"TEST_MODE = {os.environ.get('TEST_MODE')}")
    logger.info(f"TESTING = {os.environ.get('TESTING')}")
    logger.info(f"NOTION_API_TOKEN = {os.environ.get('NOTION_API_TOKEN')}")

    # Check if we're in test mode using the same condition as NotionService.from_env()
    test_mode = (
        os.environ.get("TEST_MODE", "").lower() == "true"
        or os.environ.get("TESTING", "").lower() == "true"
    )
    logger.info(f"test_mode = {test_mode}")

    # Import the actual settings
    from config.settings import settings

    logger.info(f"settings.testing = {settings.testing}")

    try:
        from services.notion_service import NotionService

        logger.info("Trying to create NotionService.from_env()...")
        notion_service = NotionService.from_env()
        logger.info(
            f"SUCCESS: NotionService created with token = {notion_service.config.token[:5]}..."
        )
    except Exception as e:
        logger.error(f"ERROR: Could not create NotionService: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
