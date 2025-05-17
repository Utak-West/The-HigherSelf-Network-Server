#!/usr/bin/env python
"""
Diagnostic script to check Notion API configuration without dependencies on the full system.
This script will load environment variables and check the Notion API token.
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


def load_env_files():
    """Load .env files"""
    env_files = [
        ".env",
        ".env.local",
        ".env.development",
        ".env.development.local",
        ".env.production",
        ".env.production.local",
    ]

    loaded_files = []
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
            loaded_files.append(env_file)
            logger.info(f"Loaded environment from {env_file}")

    if not loaded_files:
        logger.warning("No .env files found!")

    return loaded_files


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

    # Check for other Notion-related environment variables
    notion_vars = [
        "NOTION_PARENT_PAGE_ID",
        "NOTION_BUSINESS_ENTITIES_DB",
        "NOTION_CONTACTS_PROFILES_DB",
        "NOTION_COMMUNITY_HUB_DB",
        "NOTION_PRODUCTS_SERVICES_DB",
        "NOTION_ACTIVE_WORKFLOW_INSTANCES_DB",
        "NOTION_MARKETING_CAMPAIGNS_DB",
        "NOTION_FEEDBACK_SURVEYS_DB",
        "NOTION_REWARDS_BOUNTIES_DB",
        "NOTION_TASKS_DB",
        "NOTION_AGENT_COMMUNICATION_DB",
        "NOTION_AGENT_REGISTRY_DB",
        "NOTION_API_INTEGRATIONS_DB",
        "NOTION_DATA_TRANSFORMATIONS_DB",
        "NOTION_NOTIFICATIONS_TEMPLATES_DB",
        "NOTION_USE_CASES_DB",
        "NOTION_WORKFLOWS_LIBRARY_DB",
    ]

    missing_vars = []
    present_vars = []

    for var in notion_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            present_vars.append(var)

    logger.info(f"Found {len(present_vars)} Notion environment variables")

    if missing_vars:
        logger.warning(f"Missing {len(missing_vars)} Notion environment variables:")
        for var in missing_vars:
            logger.warning(f"  - {var}")

    return {
        "token_present": token_present,
        "token_valid_length": token_present and token_length >= 50,
        "vars_present": present_vars,
        "vars_missing": missing_vars,
    }


def main():
    """Main diagnostic function"""
    logger.info("Starting Notion API configuration diagnostics")

    # Load environment variables
    loaded_files = load_env_files()

    # Diagnose Notion configuration
    notion_results = diagnose_notion_config()

    # Summarize findings
    logger.info("\n--- DIAGNOSTIC SUMMARY ---")
    if notion_results["token_present"] and notion_results["token_valid_length"]:
        logger.info("✅ Notion API token appears valid")
    else:
        logger.error("❌ Notion API token issues detected")

    if not notion_results["vars_missing"]:
        logger.info("✅ All Notion environment variables are present")
    else:
        num_missing = len(notion_results["vars_missing"])
        total = num_missing + len(notion_results["vars_present"])
        logger.warning(f"⚠️ Missing {num_missing}/{total} Notion environment variables")

    if (
        not notion_results["token_present"]
        or not notion_results["token_valid_length"]
        or notion_results["vars_missing"]
    ):
        logger.error("\n❌ CONFIGURATION ISSUES DETECTED - See above for details")
    else:
        logger.info("\n✅ CONFIGURATION LOOKS GOOD")


if __name__ == "__main__":
    main()
