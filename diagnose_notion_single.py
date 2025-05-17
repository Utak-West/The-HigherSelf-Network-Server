#!/usr/bin/env python
"""
Diagnostic script to check Notion API configuration from only the main .env file.
"""
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("notion-diagnostics")


def load_env_file():
    """Load only the main .env file"""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment from .env")
        return True
    else:
        logger.warning("No .env file found!")
        return False


def diagnose_notion_config():
    """Diagnose Notion API configuration"""
    # Get Notion API token
    notion_token = os.getenv("NOTION_API_TOKEN")

    # Log information about the token
    token_present = bool(notion_token)
    token_length = len(notion_token) if token_present else 0

    # Create a masked version of the token for logging
    masked_token = "None"
    if token_present and token_length > 8:
        masked_token = notion_token[:4] + "..." + notion_token[-4:]
    elif token_present:
        masked_token = "***"

    logger.info(f"Notion API token present: {token_present}")
    logger.info(f"Notion API token length: {token_length}")
    logger.info(f"Notion API token (masked): {masked_token}")

    # Check if token is likely valid (at least 50 chars for Notion tokens)
    if token_present and token_length >= 50:
        logger.info("✅ Notion API token length looks valid (>= 50 chars)")
    elif token_present:
        logger.error(
            "❌ Notion API token is present but length is suspicious (< 50 chars)"
        )
    else:
        logger.error("❌ Notion API token is missing")


def main():
    """Main diagnostic function"""
    logger.info("Starting Notion API configuration diagnostics (single .env file only)")

    # Load environment variables from only the main .env file
    loaded = load_env_file()
    if not loaded:
        return

    # Diagnose Notion configuration
    diagnose_notion_config()


if __name__ == "__main__":
    main()
