#!/usr/bin/env python3
"""
Environment Variable Validator for Higher Self Network Server

This script validates that all required environment variables are properly set
before starting server components, following the Environment Isolation Rule.
"""

import os
import sys
from typing import Dict, List, Optional, Set

# Define required environment variables by category
REQUIRED_VARS = {
    "core": [
        "LOG_LEVEL",
        "SERVER_PORT",
        "WEBHOOK_SECRET",
        "TEST_MODE",
    ],
    "notion": [
        "NOTION_API_TOKEN",
        "NOTION_PARENT_PAGE_ID",
        # Core Notion database IDs
        "NOTION_BUSINESS_ENTITIES_DB",
        "NOTION_CONTACTS_PROFILES_DB",
        "NOTION_COMMUNITY_HUB_DB",
        "NOTION_PRODUCTS_SERVICES_DB",
        "NOTION_ACTIVE_WORKFLOW_INSTANCES_DB",
        "NOTION_MARKETING_CAMPAIGNS_DB",
        "NOTION_FEEDBACK_SURVEYS_DB",
        "NOTION_REWARDS_BOUNTIES_DB",
        "NOTION_TASKS_DB",
        # Agent & System Support Databases
        "NOTION_AGENT_COMMUNICATION_DB",
        "NOTION_AGENT_REGISTRY_DB",
        "NOTION_API_INTEGRATIONS_DB",
        "NOTION_DATA_TRANSFORMATIONS_DB",
        "NOTION_NOTIFICATIONS_TEMPLATES_DB",
        "NOTION_USE_CASES_DB",
        "NOTION_WORKFLOWS_LIBRARY_DB",
    ],
    "mongodb": [
        "MONGODB_CONNECTION_STRING",
    ],
    "postgres": [
        "POSTGRES_CONNECTION_STRING",
    ],
    "redis": [
        "REDIS_URL",
    ],
    "stripe": [
        "STRIPE_API_KEY",
    ],
    "supabase": [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_ACCESS_TOKEN",
    ],
    "github": [
        "GITHUB_PAT",
    ],
    "softr": [
        "SOFTR_API_KEY",
        "SOFTR_APP_ID",
        "SOFTR_API_URL",
        "STAFF_API_KEY",
    ],
}

# Optional variables that might be needed for specific features
OPTIONAL_VARS = {
    "figma": [
        "FIGMA_API_KEY",
    ],
    "perplexity": [
        "PERPLEXITY_API_KEY",
    ],
    "huggingface": [
        "HUGGINGFACE_API_KEY",
        "HUGGINGFACE_API_URL",
    ],
    "third_party": [
        "HUBSPOT_API_KEY",
        "TYPEFORM_API_KEY",
        "AIRTABLE_API_KEY",
        "AIRTABLE_BASE_ID",
        "AMELIA_API_KEY",
        "AMELIA_ENDPOINT",
        "WOOCOMMERCE_CONSUMER_KEY",
        "WOOCOMMERCE_CONSUMER_SECRET",
        "WOOCOMMERCE_URL",
        "TUTORLM_API_KEY",
        "CIRCLE_API_TOKEN",
        "CIRCLE_COMMUNITY_ID",
        "BEEHIIV_API_KEY",
        "BEEHIIV_PUBLICATION_ID",
    ],
}

def validate_environment(categories: Optional[List[str]] = None) -> Dict[str, Set[str]]:
    """
    Validates that required environment variables are set
    
    Args:
        categories: Specific categories to validate, or None for all
        
    Returns:
        Dict mapping categories to missing variables
    """
    missing_vars: Dict[str, Set[str]] = {}
    
    categories_to_check = categories or REQUIRED_VARS.keys()
    
    for category in categories_to_check:
        if category in REQUIRED_VARS:
            category_missing = {var for var in REQUIRED_VARS[category] 
                               if not os.environ.get(var)}
            
            if category_missing:
                missing_vars[category] = category_missing
    
    return missing_vars

def check_environment_isolation() -> bool:
    """
    Verifies that environment-specific variables are consistent
    to prevent mixing development/testing/production configurations
    
    Returns:
        True if environment isolation is properly maintained
    """
    # Extract environment indicators
    is_prod = os.environ.get("ENVIRONMENT") == "production"
    has_prod_keys = any([
        os.environ.get("STRIPE_API_KEY", "").startswith("sk_live_"),
        "prod" in os.environ.get("MONGODB_CONNECTION_STRING", ""),
        "prod" in os.environ.get("POSTGRES_CONNECTION_STRING", ""),
    ])
    
    # Check for inconsistencies
    if is_prod != has_prod_keys:
        print("⚠️  WARNING: Environment isolation issue detected!")
        print("The ENVIRONMENT setting doesn't match the API keys being used.")
        return False
    
    return True

def validate_workflow_requirements() -> bool:
    """
    Validates that necessary environment variables for defined workflows are set
    
    Returns:
        True if all workflow-specific variables are properly set
    """
    # Define workflow-specific variable groupings
    workflow_requirements = {
        "softr_publishing": ["SOFTR_API_KEY", "SOFTR_APP_ID", "SOFTR_API_URL"],
        "agent_communication": ["NOTION_AGENT_COMMUNICATION_DB", "NOTION_AGENT_REGISTRY_DB"],
        "gallery_exhibit": ["NOTION_PRODUCTS_SERVICES_DB", "NOTION_BUSINESS_ENTITIES_DB"],
        "wellness_booking": ["NOTION_PRODUCTS_SERVICES_DB", "NOTION_CONTACTS_PROFILES_DB"],
        "content_distribution": ["BEEHIIV_API_KEY", "BEEHIIV_PUBLICATION_ID"],
    }
    
    workflow_status = {}
    
    for workflow, vars_required in workflow_requirements.items():
        missing = [var for var in vars_required if not os.environ.get(var)]
        workflow_status[workflow] = {
            "ready": len(missing) == 0,
            "missing": missing
        }
    
    # Report workflows not ready
    incomplete_workflows = {name: data for name, data in workflow_status.items() 
                          if not data["ready"]}
    
    if incomplete_workflows:
        print("\n⚠️  Some workflows have missing environment variables:")
        for workflow, data in incomplete_workflows.items():
            print(f"  • {workflow}: Missing {', '.join(data['missing'])}")
        return False
    
    return True

def main():
    """Main validation function"""
    print("🔍 Validating environment variables...")
    
    missing_vars = validate_environment()
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for category, vars in missing_vars.items():
            print(f"  • {category.upper()}: {', '.join(vars)}")
        sys.exit(1)
    
    if not check_environment_isolation():
        print("❌ Environment isolation issue detected")
        sys.exit(1)
    
    # Validate workflow-specific requirements
    validate_workflow_requirements()
    
    print("✅ All required environment variables are set")
    print("✅ Environment isolation verified")
    
    # Optional variables check
    missing_optional = {}
    for category, vars_list in OPTIONAL_VARS.items():
        category_missing = {var for var in vars_list if not os.environ.get(var)}
        if category_missing:
            missing_optional[category] = category_missing
    
    if missing_optional:
        print("\n⚠️  NOTE: Some optional variables are not set:")
        for category, vars in missing_optional.items():
            print(f"  • {category.upper()}: {', '.join(vars)}")
        print("These variables are only needed for specific features.")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
