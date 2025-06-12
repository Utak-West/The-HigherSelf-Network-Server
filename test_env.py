#!/usr/bin/env python3
"""
Test script to check if environment variables are being loaded properly
"""

import os

from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Print environment variables
print(f"TEST_MODE: {os.environ.get('TEST_MODE')}")
print(f"NOTION_API_TOKEN: {os.environ.get('NOTION_API_TOKEN')}")
print(f"Type of TEST_MODE: {type(os.environ.get('TEST_MODE'))}")
print(f"TEST_MODE == 'true': {os.environ.get('TEST_MODE') == 'true'}")
print(
    f"TEST_MODE.lower() == 'true': {os.environ.get('TEST_MODE', '').lower() == 'true'}"
)
