#!/usr/bin/env python3
"""
Test script for NotionService
"""

import os
from dotenv import load_dotenv
from loguru import logger

# Load .env file
load_dotenv()

# Enable test mode
os.environ['TEST_MODE'] = 'true'

# Make sure TEST_MODE is set
print(f"TEST_MODE: {os.environ.get('TEST_MODE')}")

# Import NotionService
from services.notion_service import NotionService

# Initialize with from_env and check the result
try:
    print("Attempting to initialize NotionService.from_env()...")
    notion_service = NotionService.from_env()
    print(f"SUCCESS: NotionService initialized with config: {notion_service.config}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()