#!/usr/bin/env python3
"""
Script to find and list all databases accessible to your Notion integration.
This will help identify the correct database IDs for your .env file.
"""

import os
from dotenv import load_dotenv
from notion_client import Client

def find_databases():
    """Find all databases accessible to the integration."""
    
    # Load environment variables
    load_dotenv()
    
    print("🔍 Finding Notion Databases...")
    print("=" * 50)
    
    # Check if required environment variables are set
    notion_token = os.getenv("NOTION_API_TOKEN")
    parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID")
    
    if not notion_token:
        print("❌ NOTION_API_TOKEN not found in environment")
        return False
    
    if not parent_page_id:
        print("❌ NOTION_PARENT_PAGE_ID not found in environment")
        return False
    
    print("✅ Notion credentials found")
    print(f"📄 Parent Page ID: {parent_page_id}")
    
    try:
        # Initialize Notion client
        client = Client(auth=notion_token)
        print("✅ Notion client initialized")
        
        # Try to access the parent page
        try:
            page_info = client.pages.retrieve(parent_page_id)
            page_title = ""
            if page_info.get("properties"):
                title_prop = page_info["properties"].get("title")
                if title_prop and title_prop.get("title"):
                    page_title = title_prop["title"][0]["text"]["content"]
            print(f"✅ Parent page accessible: {page_title}")
        except Exception as e:
            print(f"❌ Cannot access parent page: {e}")
            print("❗ Make sure the parent page is shared with your integration")
            return False
        
        # List child blocks (databases) in the parent page
        print(f"\n📊 Searching for databases in parent page...")
        try:
            children = client.blocks.children.list(parent_page_id)
            databases_found = []
            
            for block in children.get("results", []):
                if block.get("type") == "child_database":
                    db_id = block["id"]
                    try:
                        db_info = client.databases.retrieve(db_id)
                        db_title = ""
                        if db_info.get("title"):
                            title_parts = db_info["title"]
                            if title_parts and len(title_parts) > 0:
                                db_title = title_parts[0].get("text", {}).get("content", "")
                        
                        databases_found.append({
                            "id": db_id,
                            "title": db_title
                        })
                        print(f"✅ Found database: {db_title}")
                        print(f"   🆔 ID: {db_id}")
                        
                    except Exception as e:
                        print(f"❌ Found database but cannot access: {db_id}")
                        print(f"   ❗ Error: {e}")
            
            if databases_found:
                print(f"\n📋 Summary: Found {len(databases_found)} accessible databases")
                print("\n🔧 Suggested .env file updates:")
                print("-" * 50)
                
                # Map found databases to environment variables
                db_mapping = {
                    "Business Entities": "NOTION_BUSINESS_ENTITIES_DB",
                    "Contacts": "NOTION_CONTACTS_PROFILES_DB", 
                    "Community": "NOTION_COMMUNITY_HUB_DB",
                    "Products": "NOTION_PRODUCTS_SERVICES_DB",
                    "Workflow": "NOTION_ACTIVE_WORKFLOW_INSTANCES_DB",
                    "Marketing": "NOTION_MARKETING_CAMPAIGNS_DB",
                    "Feedback": "NOTION_FEEDBACK_SURVEYS_DB",
                    "Rewards": "NOTION_REWARDS_BOUNTIES_DB",
                    "Tasks": "NOTION_TASKS_DB",
                    "Agent Communication": "NOTION_AGENT_COMMUNICATION_DB",
                    "Agent Registry": "NOTION_AGENT_REGISTRY_DB",
                    "API": "NOTION_API_INTEGRATIONS_DB",
                    "Data": "NOTION_DATA_TRANSFORMATIONS_DB",
                    "Notifications": "NOTION_NOTIFICATIONS_TEMPLATES_DB",
                    "Use Cases": "NOTION_USE_CASES_DB",
                    "Workflows": "NOTION_WORKFLOWS_LIBRARY_DB",
                }
                
                for db in databases_found:
                    # Try to match database title to environment variable
                    matched_env_var = None
                    for keyword, env_var in db_mapping.items():
                        if keyword.lower() in db["title"].lower():
                            matched_env_var = env_var
                            break
                    
                    if matched_env_var:
                        print(f"{matched_env_var}={db['id']}")
                    else:
                        print(f"# Unknown database: {db['title']}")
                        print(f"# ID: {db['id']}")
                
                return True
            else:
                print("❌ No databases found in parent page")
                print("❗ Make sure databases are created and shared with your integration")
                return False
                
        except Exception as e:
            print(f"❌ Error listing child blocks: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Error connecting to Notion: {e}")
        return False

if __name__ == "__main__":
    success = find_databases()
    if not success:
        print("\n💡 Next steps:")
        print("1. Make sure your parent page is shared with your integration")
        print("2. Make sure all databases are shared with your integration")
        print("3. Run this script again to get the correct database IDs")
        exit(1)
    else:
        print("\n✅ Database discovery completed successfully!")
        print("💡 Copy the suggested environment variables to your .env file")
