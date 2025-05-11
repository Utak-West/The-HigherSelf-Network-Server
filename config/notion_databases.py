"""
Configuration module for Notion databases in The HigherSelf Network Server.

This module defines the structure and mappings for the 16-database Notion environment
that serves as the central hub for all operations.
"""

from typing import Dict, List, Any, Set

# Database mapping structure
NOTION_DATABASE_MAPPING = {
    # Core Operational Databases
    "BusinessEntity": {
        "env_var": "NOTION_BUSINESS_ENTITIES_DB",
        "description": "Business Entities Registry",
        "model_name": "BusinessEntity",
        "required": True
    },
    "ContactProfile": {
        "env_var": "NOTION_CONTACTS_PROFILES_DB",
        "description": "Contacts & Profiles Database",
        "model_name": "ContactProfile",
        "required": True
    },
    "CommunityMember": {
        "env_var": "NOTION_COMMUNITY_HUB_DB",
        "description": "Community Hub Database",
        "model_name": "CommunityMember",
        "required": True
    },
    "ProductService": {
        "env_var": "NOTION_PRODUCTS_SERVICES_DB",
        "description": "Products & Services Database",
        "model_name": "ProductService",
        "required": True
    },
    "WorkflowInstance": {
        "env_var": "NOTION_ACTIVE_WORKFLOW_INSTANCES_DB",
        "description": "Active Workflow Instances Database",
        "model_name": "WorkflowInstance",
        "required": True
    },
    "MarketingCampaign": {
        "env_var": "NOTION_MARKETING_CAMPAIGNS_DB",
        "description": "Marketing Campaigns Database",
        "model_name": "MarketingCampaign",
        "required": True
    },
    "FeedbackSurvey": {
        "env_var": "NOTION_FEEDBACK_SURVEYS_DB",
        "description": "Feedback & Surveys Database",
        "model_name": "FeedbackSurvey",
        "required": True
    },
    "RewardBounty": {
        "env_var": "NOTION_REWARDS_BOUNTIES_DB",
        "description": "Rewards & Bounties Database",
        "model_name": "RewardBounty",
        "required": False  # Optional for initial implementation
    },
    "Task": {
        "env_var": "NOTION_TASKS_DB",
        "description": "Master Tasks Database",
        "model_name": "Task",
        "required": True
    },
    
    # Agent & System Support Databases
    "AgentCommunication": {
        "env_var": "NOTION_AGENT_COMMUNICATION_DB",
        "description": "Agent Communication Patterns Database",
        "model_name": "AgentCommunication",
        "required": True
    },
    "Agent": {
        "env_var": "NOTION_AGENT_REGISTRY_DB",
        "description": "Agent Registry Database",
        "model_name": "Agent",
        "required": True
    },
    "ApiIntegration": {
        "env_var": "NOTION_API_INTEGRATIONS_DB",
        "description": "API Integrations Catalog Database",
        "model_name": "ApiIntegration",
        "required": True
    },
    "DataTransformation": {
        "env_var": "NOTION_DATA_TRANSFORMATIONS_DB",
        "description": "Data Transformations Registry Database",
        "model_name": "DataTransformation",
        "required": True
    },
    "NotificationTemplate": {
        "env_var": "NOTION_NOTIFICATIONS_TEMPLATES_DB",
        "description": "Notifications Templates Database",
        "model_name": "NotificationTemplate",
        "required": True
    },
    "UseCase": {
        "env_var": "NOTION_USE_CASES_DB",
        "description": "Use Cases Library Database",
        "model_name": "UseCase",
        "required": True
    },
    "Workflow": {
        "env_var": "NOTION_WORKFLOWS_LIBRARY_DB",
        "description": "Workflows Library Database",
        "model_name": "Workflow",
        "required": True
    }
}

# Agent-Database relationship mapping
# Shows which databases each agent primarily interacts with
AGENT_DATABASE_MAPPING = {
    "LeadCaptureAgent": [
        "ContactProfile", 
        "WorkflowInstance",
        "Task",
        "ApiIntegration",
        "DataTransformation",
        "NotificationTemplate"
    ],
    "BookingAgent": [
        "ContactProfile",
        "ProductService",
        "WorkflowInstance",
        "Task",
        "ApiIntegration"
    ],
    "ContentLifecycleAgent": [
        "WorkflowInstance",
        "MarketingCampaign",
        "UseCase",
        "NotificationTemplate"
    ],
    "AudienceSegmentationAgent": [
        "ContactProfile",
        "CommunityMember",
        "MarketingCampaign",
        "ApiIntegration"
    ],
    "TaskManagementAgent": [
        "Task",
        "WorkflowInstance",
        "NotificationTemplate"
    ],
    "MarketingCampaignAgent": [
        "MarketingCampaign",
        "ContactProfile",
        "WorkflowInstance",
        "NotificationTemplate",
        "ApiIntegration"
    ],
    "CommunityEngagementAgent": [
        "CommunityMember",
        "ContactProfile",
        "WorkflowInstance",
        "Task",
        "NotificationTemplate"
    ]
}

# Automation Flow to Agent mapping
# Shows which agents are needed for each automation flow from the Automation Map
AUTOMATION_FLOW_MAPPING = {
    "Flow 1: Lead Capture & Initial Processing": [
        "LeadCaptureAgent",
        "TaskManagementAgent"
    ],
    "Flow 2: Retreat Booking Management": [
        "BookingAgent",
        "TaskManagementAgent"
    ],
    "Flow 3: Art Sale & Fulfillment": [
        "BookingAgent",  # Used for WooCommerce orders too
        "TaskManagementAgent"
    ],
    "Flow 4: Marketing Email Campaign": [
        "MarketingCampaignAgent",
        "LeadCaptureAgent"
    ],
    "Flow 5: Automated Task Management": [
        "TaskManagementAgent"
    ],
    "Flow 6: Community Engagement": [
        "CommunityEngagementAgent",
        "TaskManagementAgent"
    ],
    "Flow 7: Content Creation & Distribution": [
        "ContentLifecycleAgent",
        "MarketingCampaignAgent"
    ],
    "Flow 8: Audience Analysis & Segmentation": [
        "AudienceSegmentationAgent",
        "MarketingCampaignAgent"
    ]
}

def get_required_database_env_vars() -> Set[str]:
    """
    Get a set of required environment variable names for Notion databases.
    
    Returns:
        Set of environment variable names
    """
    return {
        db_info["env_var"] 
        for db_name, db_info in NOTION_DATABASE_MAPPING.items() 
        if db_info["required"]
    }

def get_all_database_env_vars() -> Set[str]:
    """
    Get a set of all environment variable names for Notion databases.
    
    Returns:
        Set of environment variable names
    """
    return {db_info["env_var"] for db_name, db_info in NOTION_DATABASE_MAPPING.items()}

def get_agent_required_databases(agent_name: str) -> List[Dict[str, Any]]:
    """
    Get database information required by a specific agent.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        List of database information dictionaries
    """
    if agent_name not in AGENT_DATABASE_MAPPING:
        return []
        
    db_names = AGENT_DATABASE_MAPPING[agent_name]
    return [
        {**NOTION_DATABASE_MAPPING[db_name], "name": db_name}
        for db_name in db_names
        if db_name in NOTION_DATABASE_MAPPING
    ]
