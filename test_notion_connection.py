#!/usr/bin/env python3
"""
Test script to verify Notion integration is working correctly.
This script tests connectivity to all existing databases.
"""

import asyncio
import os
from dotenv import load_dotenv
from notion_client import Client

# Database mapping from environment variables to friendly names
DATABASE_MAPPING = {
    "NOTION_BUSINESS_ENTITIES_DB": "Business Entities Registry",
    "NOTION_CONTACTS_PROFILES_DB": "Contacts & Profiles Database",
    "NOTION_COMMUNITY_HUB_DB": "Community Hub Database",
    "NOTION_PRODUCTS_SERVICES_DB": "Products & Services Database",
    "NOTION_ACTIVE_WORKFLOW_INSTANCES_DB": "Active Workflow Instances",
    "NOTION_MARKETING_CAMPAIGNS_DB": "Marketing Campaigns Database",
    "NOTION_FEEDBACK_SURVEYS_DB": "Feedback & Surveys Database",
    "NOTION_REWARDS_BOUNTIES_DB": "Rewards & Bounties Database",
    "NOTION_TASKS_DB": "Master Tasks Database",
    "NOTION_AGENT_COMMUNICATION_DB": "Agent Communication Patterns",
    "NOTION_AGENT_REGISTRY_DB": "Agent Registry",
    "NOTION_API_INTEGRATIONS_DB": "API Integrations Catalog",
    "NOTION_DATA_TRANSFORMATIONS_DB": "Data Transformations Registry",
    "NOTION_NOTIFICATIONS_TEMPLATES_DB": "Notifications Templates",
    "NOTION_USE_CASES_DB": "Use Cases Library",
    "NOTION_WORKFLOWS_LIBRARY_DB": "Workflows Library",
}

async def test_notion_connection():
    """Test the Notion connection and database access."""

    # Load environment variables
    load_dotenv()

    print("🔍 Testing Notion Integration with Existing Databases...")
    print("=" * 60)

    # Check if required environment variables are set
    notion_token = os.getenv("NOTION_API_TOKEN")
    if not notion_token or notion_token == "secret_your_token_here":
        print("❌ NOTION_API_TOKEN not set or still using placeholder value")
        print("Please update your .env file with your actual Notion API token")
        return False

    print("✅ Notion API token found")

    try:
        # Initialize Notion client
        client = Client(auth=notion_token)
        print("✅ Notion client initialized successfully")

        # Test database access
        print(f"\n📊 Testing access to all {len(DATABASE_MAPPING)} databases...")
        print("-" * 60)

        accessible_databases = 0
        total_databases = len(DATABASE_MAPPING)

        for env_var, friendly_name in DATABASE_MAPPING.items():
            db_id = os.getenv(env_var)
            if not db_id:
                print(f"⚠️  {friendly_name}: No database ID found in environment")
                continue

            try:
                # Try to retrieve database info
                db_info = client.databases.retrieve(db_id)
                db_title = ""
                if db_info.get("title"):
                    title_parts = db_info["title"]
                    if title_parts and len(title_parts) > 0:
                        db_title = title_parts[0].get("text", {}).get("content", "")

                print(f"✅ {friendly_name}")
                print(f"   📋 Title: {db_title}")
                print(f"   🆔 ID: {db_id}")
                accessible_databases += 1

            except Exception as e:
                print(f"❌ {friendly_name}: Cannot access database")
                print(f"   🆔 ID: {db_id}")
                print(f"   ❗ Error: {str(e)}")

        print("-" * 60)
        print(f"📊 Database Access Summary:")
        print(f"   ✅ Accessible: {accessible_databases}/{total_databases}")
        print(f"   ❌ Inaccessible: {total_databases - accessible_databases}/{total_databases}")

        if accessible_databases == total_databases:
            print("\n🎉 All databases are accessible!")
            print("✅ Your Notion integration is fully functional.")
            print("✅ Your server can now index and edit all Notion content.")
            return True
        elif accessible_databases > 0:
            print(f"\n⚠️  Partial success: {accessible_databases} out of {total_databases} databases accessible")
            print("❗ Some databases may need permission updates or have invalid IDs")
            return False
        else:
            print("\n❌ No databases are accessible")
            print("❗ Check your integration permissions and database IDs")
            return False

    except Exception as e:
        print(f"❌ Error testing Notion connection: {e}")
        print("Please check your Notion API token and integration setup.")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_notion_connection())
    if not success:
        exit(1)
