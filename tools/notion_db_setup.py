"""
Utility script to create and configure the required Notion databases.
This script initializes the database structure needed for The HigherSelf Network Server.
"""

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from loguru import logger
from notion_client import APIErrorCode, APIResponseError, Client


# Configure colored terminal output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def print_info(message: str) -> None:
    print(f"{Colors.BLUE}[INFO]{Colors.END} {message}")


def print_success(message: str) -> None:
    print(f"{Colors.GREEN}[SUCCESS]{Colors.END} {message}")


def print_warning(message: str) -> None:
    print(f"{Colors.YELLOW}[WARNING]{Colors.END} {message}")


def print_error(message: str) -> None:
    print(f"{Colors.RED}[ERROR]{Colors.END} {message}")


def print_header(message: str) -> None:
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.END}")


class NotionDatabaseSetup:
    """
    Tool for setting up Notion databases required by The HigherSelf Network Server.
    """

    def __init__(self, notion_token: str):
        """
        Initialize the Notion database setup tool.

        Args:
            notion_token: Notion API token
        """
        self.client = Client(auth=notion_token)
        self.parent_page_id = None
        self.existing_databases = {}

    async def validate_connection(self) -> bool:
        """
        Validate the Notion API connection and token.

        Returns:
            True if validation succeeds, False otherwise
        """
        try:
            # Test the API connection by listing users
            self.client.users.list()
            return True
        except APIResponseError as e:
            if e.code == APIErrorCode.InvalidRequestURL:
                print_error("Invalid Notion API token or insufficient permissions")
            elif e.code == APIErrorCode.RateLimited:
                print_error("Notion API rate limit exceeded. Please try again later.")
            else:
                print_error(f"Notion API error: {e}")
            return False
        except Exception as e:
            print_error(f"Error connecting to Notion: {e}")
            return False

    async def find_existing_database(
        self, parent_page_id: str, title: str
    ) -> Optional[str]:
        """
        Check if a database with the given title already exists in the parent page.

        Args:
            parent_page_id: ID of the parent page
            title: Database title to look for

        Returns:
            Database ID if found, None otherwise
        """
        try:
            # Query the parent page for children
            response = self.client.blocks.children.list(parent_page_id)

            # Look for databases with matching titles
            for block in response.get("results", []):
                if block.get("type") == "child_database":
                    db_id = block["id"]
                    db_info = self.client.databases.retrieve(db_id)

                    # Extract database title
                    db_title = ""
                    title_obj = db_info.get("title", [])
                    if title_obj:
                        db_title = title_obj[0].get("text", {}).get("content", "")

                    if db_title == title:
                        return db_id

            return None
        except Exception as e:
            logger.warning(f"Error finding existing database '{title}': {e}")
            return None

    async def create_database(
        self,
        parent_page_id: str,
        title: str,
        description: str,
        properties: Dict[str, Any],
    ) -> str:
        """
        Create a new Notion database.

        Args:
            parent_page_id: ID of the parent page
            title: Database title
            description: Database description
            properties: Database properties schema

        Returns:
            New database ID
        """
        try:
            # Check if database already exists
            existing_db_id = await self.find_existing_database(parent_page_id, title)
            if existing_db_id:
                print_warning(
                    f"Database '{title}' already exists with ID: {existing_db_id}"
                )
                # Option to update or use existing database could be added here
                return existing_db_id

            # Create new database
            print_info(f"Creating database '{title}'...")
            response = self.client.databases.create(
                parent={"page_id": parent_page_id},
                title=[{"type": "text", "text": {"content": title}}],
                description=[{"type": "text", "text": {"content": description}}],
                properties=properties,
            )

            database_id = response["id"]
            print_success(f"Created database '{title}' with ID: {database_id}")
            logger.info(f"Created database '{title}' with ID: {database_id}")
            return database_id

        except APIResponseError as e:
            error_message = f"Notion API error creating database '{title}': {e.code}"
            print_error(error_message)
            logger.error(error_message)
            if e.code == APIErrorCode.ObjectNotFound:
                print_error(
                    f"Parent page with ID {parent_page_id} not found or insufficient permissions"
                )
            elif e.code == APIErrorCode.InvalidJSON:
                print_error("Invalid database properties schema")
            raise
        except Exception as e:
            error_message = f"Error creating database '{title}': {e}"
            print_error(error_message)
            logger.error(error_message)
            raise

    async def create_all_databases(self, parent_page_id: str) -> Dict[str, str]:
        """
        Create all required databases for The HigherSelf Network Server.

        Args:
            parent_page_id: ID of the parent page to create databases in

        Returns:
            Dictionary mapping database names to their IDs
        """
        self.parent_page_id = parent_page_id
        database_ids = {}

        # Create Business Entities Registry
        database_ids["BusinessEntity"] = await self.create_business_entities_db()

        # Create Agent Registry
        database_ids["Agent"] = await self.create_agent_registry_db()

        # Create Workflows Library
        database_ids["Workflow"] = await self.create_workflows_library_db()

        # Create Active Workflow Instances
        database_ids["WorkflowInstance"] = await self.create_workflow_instances_db()

        # Create API Integrations Catalog
        database_ids["ApiIntegration"] = await self.create_api_integrations_db()

        # Create Data Transformations Registry
        database_ids["DataTransformation"] = await self.create_data_transformations_db()

        # Create Use Cases Library
        database_ids["UseCase"] = await self.create_use_cases_db()

        # Create Notifications Templates
        database_ids[
            "NotificationTemplate"
        ] = await self.create_notifications_templates_db()

        # Create Agent Communication Patterns
        database_ids["AgentCommunication"] = await self.create_agent_communication_db()

        # Create Master Tasks Database
        database_ids["Task"] = await self.create_tasks_db()

        # Create additional databases for complete 16-database setup
        database_ids["ContactProfile"] = await self.create_contacts_profiles_db()
        database_ids["CommunityMember"] = await self.create_community_hub_db()
        database_ids["ProductService"] = await self.create_products_services_db()
        database_ids["MarketingCampaign"] = await self.create_marketing_campaigns_db()
        database_ids["FeedbackSurvey"] = await self.create_feedback_surveys_db()
        database_ids["RewardsBounty"] = await self.create_rewards_bounties_db()

        return database_ids

    async def create_business_entities_db(self) -> str:
        """Create the Business Entities Registry database."""
        properties = {
            "Name": {"title": {}},
            "Entity Type": {
                "select": {
                    "options": [
                        {"name": "CONSULTING_FIRM", "color": "blue"},
                        {"name": "ART_GALLERY", "color": "green"},
                        {"name": "WELLNESS_CENTER", "color": "orange"},
                    ]
                }
            },
            "API Keys Reference": {"rich_text": {}},
            "Primary Workflows": {"rich_text": {}},
            "Active Agents": {"rich_text": {}},
            "Integration Status": {
                "select": {
                    "options": [
                        {"name": "Active", "color": "green"},
                        {"name": "Pending", "color": "yellow"},
                        {"name": "Maintenance", "color": "red"},
                    ]
                }
            },
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Business Entities Registry",
            description="Track all business entities utilizing the agent network",
            properties=properties,
        )

    async def create_agent_registry_db(self) -> str:
        """Create the Agent Registry database."""
        properties = {
            "Agent ID": {"title": {}},
            "Name": {"rich_text": {}},
            "Description": {"rich_text": {}},
            "Version": {"rich_text": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Deployed", "color": "green"},
                        {"name": "Development", "color": "yellow"},
                        {"name": "Inactive", "color": "gray"},
                        {"name": "Deprecated", "color": "red"},
                    ]
                }
            },
            "Business Entity Association": {"rich_text": {}},
            "Capabilities": {"multi_select": {}},
            "Primary APIs Utilized": {"multi_select": {}},
            "Supported Workflows": {"rich_text": {}},
            "Primary Data Sources": {"multi_select": {}},
            "Primary Data Sinks": {"multi_select": {}},
            "Runtime Environment": {
                "select": {
                    "options": [
                        {"name": "Docker (HigherSelf Network Server)", "color": "blue"},
                        {"name": "Serverless", "color": "purple"},
                    ]
                }
            },
            "Source Code Location": {"url": {}},
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Agent Registry",
            description="Catalog all agents in the network",
            properties=properties,
        )

    async def create_workflows_library_db(self) -> str:
        """Create the Workflows Library database."""
        properties = {
            "Workflow ID": {"title": {}},
            "Name": {"rich_text": {}},
            "Description": {"rich_text": {}},
            "Version": {"rich_text": {}},
            "Business Entity": {"rich_text": {}},
            "Initial State": {"rich_text": {}},
            "States": {"rich_text": {}},
            "Transitions": {"rich_text": {}},
            "Required Agents": {"rich_text": {}},
            "Visualization URL": {"url": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Draft", "color": "gray"},
                        {"name": "Implemented", "color": "yellow"},
                        {"name": "Active", "color": "green"},
                    ]
                }
            },
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Workflows Library",
            description="Document all workflow definitions",
            properties=properties,
        )

    async def create_workflow_instances_db(self) -> str:
        """Create the Active Workflow Instances database."""
        properties = {
            "Instance ID": {"title": {}},
            "Workflow": {"rich_text": {}},
            "Business Entity": {"rich_text": {}},
            "Current State": {"rich_text": {}},
            "Client/Lead Email": {"email": {}},
            "Client/Lead Name": {"rich_text": {}},
            "Client/Lead Phone": {"phone_number": {}},
            "Start Date": {"date": {}},
            "Last Transition Date": {"date": {}},
            "Status": {
                "status": {
                    "options": [
                        {"name": "Active", "color": "green"},
                        {"name": "Completed", "color": "blue"},
                        {"name": "Error", "color": "red"},
                        {"name": "On Hold", "color": "yellow"},
                    ]
                }
            },
            "Error Message": {"rich_text": {}},
            "Assigned To": {"rich_text": {}},
            "Priority": {
                "select": {
                    "options": [
                        {"name": "High", "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "blue"},
                    ]
                }
            },
            "Tags": {"multi_select": {}},
            "Source System": {"rich_text": {}},
            "Source Record ID": {"rich_text": {}},
            "HubSpot Contact ID": {"rich_text": {}},
            "Airtable Record ID": {"rich_text": {}},
            "Key Data Payload": {"rich_text": {}},
            "History Log": {"rich_text": {}},
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Active Workflow Instances",
            description="Track currently running workflow instances",
            properties=properties,
        )

    async def create_api_integrations_db(self) -> str:
        """Create the API Integrations Catalog database."""
        properties = {
            "Platform": {"title": {}},
            "Description": {"rich_text": {}},
            "Base URL": {"url": {}},
            "Authentication Type": {"rich_text": {}},
            "Credential Reference": {"rich_text": {}},
            "Primary Endpoints": {"multi_select": {}},
            "Documentation URL": {"url": {}},
            "Business Entities": {"rich_text": {}},
            "Version": {"rich_text": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Active", "color": "green"},
                        {"name": "Deprecated", "color": "red"},
                        {"name": "Planned", "color": "gray"},
                        {"name": "Under Test", "color": "yellow"},
                    ]
                }
            },
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="API Integrations Catalog",
            description="Document all external API integrations",
            properties=properties,
        )

    async def create_data_transformations_db(self) -> str:
        """Create the Data Transformations Registry database."""
        properties = {
            "Transformation Name": {"title": {}},
            "Description": {"rich_text": {}},
            "Source Format": {"rich_text": {}},
            "Target Format": {"rich_text": {}},
            "Transformation Logic": {"rich_text": {}},
            "Sample Input (JSON)": {"rich_text": {}},
            "Sample Output (JSON)": {"rich_text": {}},
            "Used By Workflows": {"rich_text": {}},
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Data Transformations Registry",
            description="Document data transformation patterns",
            properties=properties,
        )

    async def create_use_cases_db(self) -> str:
        """Create the Use Cases Library database."""
        properties = {
            "Use Case ID": {"title": {}},
            "Title": {"rich_text": {}},
            "Description": {"rich_text": {}},
            "Business Entities": {"rich_text": {}},
            "Implemented By Workflows": {"rich_text": {}},
            "User Stories": {"rich_text": {}},
            "Acceptance Criteria": {"rich_text": {}},
            "Implementation Status": {
                "select": {
                    "options": [
                        {"name": "Planned", "color": "gray"},
                        {"name": "In Progress", "color": "yellow"},
                        {"name": "Implemented", "color": "green"},
                    ]
                }
            },
            "Notion Dashboard Link": {"url": {}},
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Use Cases Library",
            description="Document business use cases implemented by the agent network",
            properties=properties,
        )

    async def create_notifications_templates_db(self) -> str:
        """Create the Notifications Templates database."""
        properties = {
            "Template ID": {"title": {}},
            "Description": {"rich_text": {}},
            "Channel": {
                "select": {
                    "options": [
                        {"name": "Email", "color": "blue"},
                        {"name": "SMS", "color": "green"},
                        {"name": "Slack", "color": "purple"},
                        {"name": "Push Notification", "color": "red"},
                    ]
                }
            },
            "Content Template": {"rich_text": {}},
            "Subject Template": {"rich_text": {}},
            "Supported Placeholders": {"multi_select": {}},
            "Business Entities": {"rich_text": {}},
            "Creator": {"rich_text": {}},
            "Created Date": {"date": {}},
            "Last Updated": {"date": {}},
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Notifications Templates",
            description="Manage reusable notification templates",
            properties=properties,
        )

    async def create_agent_communication_db(self) -> str:
        """Create the Agent Communication Patterns database."""
        properties = {
            "Pattern Name": {"title": {}},
            "Description": {"rich_text": {}},
            "Source Agent": {"rich_text": {}},
            "Target Agent": {"rich_text": {}},
            "Message Format": {"rich_text": {}},
            "Communication Protocol": {
                "select": {
                    "options": [
                        {"name": "HTTP", "color": "blue"},
                        {"name": "Message Queue", "color": "green"},
                        {"name": "WebSocket", "color": "purple"},
                    ]
                }
            },
            "Sample Payload": {"rich_text": {}},
            "Active Workflows Using": {"rich_text": {}},
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Agent Communication Patterns",
            description="Document agent-to-agent communication",
            properties=properties,
        )

    async def create_tasks_db(self) -> str:
        """Create the Master Tasks Database."""
        properties = {
            "Task ID": {"title": {}},
            "Task Name": {"rich_text": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "To Do", "color": "gray"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "On Hold", "color": "yellow"},
                        {"name": "Done", "color": "green"},
                        {"name": "Cancelled", "color": "red"},
                    ]
                }
            },
            "Description": {"rich_text": {}},
            "Priority": {
                "select": {
                    "options": [
                        {"name": "High", "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "blue"},
                    ]
                }
            },
            "Due Date": {"date": {}},
            "Assigned To": {"rich_text": {}},
            "Related Workflow Instance": {"rich_text": {}},
            "Related Business Entity": {"rich_text": {}},
            "Created By": {"rich_text": {}},
            "Created Date": {"date": {}},
            "Last Edited Date": {"date": {}},
            "Tags": {"multi_select": {}},
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Master Tasks Database",
            description="Centralize all actionable tasks generated from workflows or manually",
            properties=properties,
        )

    async def create_contacts_profiles_db(self) -> str:
        """Create the Contacts & Profiles database."""
        properties = {
            "Name": {"title": {}},
            "Email": {"email": {}},
            "Phone": {"phone_number": {}},
            "Company": {"rich_text": {}},
            "Role": {"rich_text": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Lead", "color": "yellow"},
                        {"name": "Client", "color": "green"},
                        {"name": "Partner", "color": "blue"},
                        {"name": "Inactive", "color": "gray"},
                    ]
                }
            },
            "Source": {"rich_text": {}},
            "Tags": {"multi_select": {}},
            "Notes": {"rich_text": {}},
            "Created Date": {"date": {}},
            "Last Contact": {"date": {}},
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Contacts & Profiles Database",
            description="Customer and contact information management",
            properties=properties,
        )

    async def create_community_hub_db(self) -> str:
        """Create the Community Hub database."""
        properties = {
            "Member Name": {"title": {}},
            "Email": {"email": {}},
            "Membership Type": {
                "select": {
                    "options": [
                        {"name": "Free", "color": "gray"},
                        {"name": "Premium", "color": "blue"},
                        {"name": "VIP", "color": "purple"},
                    ]
                }
            },
            "Join Date": {"date": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Active", "color": "green"},
                        {"name": "Inactive", "color": "gray"},
                        {"name": "Suspended", "color": "red"},
                    ]
                }
            },
            "Interests": {"multi_select": {}},
            "Engagement Score": {"number": {}},
            "Last Activity": {"date": {}},
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Community Hub Database",
            description="Community member data and engagement tracking",
            properties=properties,
        )

    async def create_products_services_db(self) -> str:
        """Create the Products & Services database."""
        properties = {
            "Name": {"title": {}},
            "Type": {
                "select": {
                    "options": [
                        {"name": "Product", "color": "blue"},
                        {"name": "Service", "color": "green"},
                        {"name": "Package", "color": "purple"},
                    ]
                }
            },
            "Description": {"rich_text": {}},
            "Price": {"number": {}},
            "Currency": {"rich_text": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Active", "color": "green"},
                        {"name": "Draft", "color": "yellow"},
                        {"name": "Discontinued", "color": "red"},
                    ]
                }
            },
            "Category": {"multi_select": {}},
            "Created Date": {"date": {}},
            "Last Updated": {"date": {}},
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Products & Services Database",
            description="Product and service catalog management",
            properties=properties,
        )

    async def create_marketing_campaigns_db(self) -> str:
        """Create the Marketing Campaigns database."""
        properties = {
            "Campaign Name": {"title": {}},
            "Type": {
                "select": {
                    "options": [
                        {"name": "Email", "color": "blue"},
                        {"name": "Social Media", "color": "green"},
                        {"name": "Content", "color": "purple"},
                        {"name": "Paid Ads", "color": "red"},
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Planning", "color": "gray"},
                        {"name": "Active", "color": "green"},
                        {"name": "Paused", "color": "yellow"},
                        {"name": "Completed", "color": "blue"},
                    ]
                }
            },
            "Start Date": {"date": {}},
            "End Date": {"date": {}},
            "Budget": {"number": {}},
            "Target Audience": {"rich_text": {}},
            "Goals": {"rich_text": {}},
            "Results": {"rich_text": {}},
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Marketing Campaigns Database",
            description="Marketing campaign planning and tracking",
            properties=properties,
        )

    async def create_feedback_surveys_db(self) -> str:
        """Create the Feedback & Surveys database."""
        properties = {
            "Survey Name": {"title": {}},
            "Type": {
                "select": {
                    "options": [
                        {"name": "Customer Feedback", "color": "blue"},
                        {"name": "Product Survey", "color": "green"},
                        {"name": "Service Review", "color": "purple"},
                        {"name": "General Survey", "color": "gray"},
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Draft", "color": "gray"},
                        {"name": "Active", "color": "green"},
                        {"name": "Closed", "color": "red"},
                    ]
                }
            },
            "Created Date": {"date": {}},
            "Response Count": {"number": {}},
            "Average Rating": {"number": {}},
            "Key Insights": {"rich_text": {}},
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Feedback & Surveys Database",
            description="Customer feedback and survey response management",
            properties=properties,
        )

    async def create_rewards_bounties_db(self) -> str:
        """Create the Rewards & Bounties database."""
        properties = {
            "Title": {"title": {}},
            "Type": {
                "select": {
                    "options": [
                        {"name": "Reward", "color": "green"},
                        {"name": "Bounty", "color": "blue"},
                        {"name": "Achievement", "color": "purple"},
                    ]
                }
            },
            "Value": {"number": {}},
            "Currency": {"rich_text": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Available", "color": "green"},
                        {"name": "In Progress", "color": "yellow"},
                        {"name": "Completed", "color": "blue"},
                        {"name": "Expired", "color": "red"},
                    ]
                }
            },
            "Description": {"rich_text": {}},
            "Requirements": {"rich_text": {}},
            "Deadline": {"date": {}},
            "Assigned To": {"rich_text": {}},
        }

        return await self.create_database(
            parent_page_id=self.parent_page_id,
            title="Rewards & Bounties Database",
            description="Incentive programs and achievement tracking",
            properties=properties,
        )

    def create_env_file(
        self, database_ids: Dict[str, str], output_path: str = ".env.notion"
    ) -> None:
        """
        Create an .env file with the database IDs for The HigherSelf Network Server.

        Args:
            database_ids: Dictionary mapping database names to IDs
            output_path: Path to output the .env file
        """
        # Create the environment variables
        env_vars = {
            "NOTION_BUSINESS_ENTITIES_DB": database_ids.get("BusinessEntity", ""),
            "NOTION_AGENT_REGISTRY_DB": database_ids.get("Agent", ""),
            "NOTION_WORKFLOWS_LIBRARY_DB": database_ids.get("Workflow", ""),
            "NOTION_ACTIVE_WORKFLOW_INSTANCES_DB": database_ids.get(
                "WorkflowInstance", ""
            ),
            "NOTION_API_INTEGRATIONS_DB": database_ids.get("ApiIntegration", ""),
            "NOTION_DATA_TRANSFORMATIONS_DB": database_ids.get(
                "DataTransformation", ""
            ),
            "NOTION_USE_CASES_DB": database_ids.get("UseCase", ""),
            "NOTION_NOTIFICATIONS_TEMPLATES_DB": database_ids.get(
                "NotificationTemplate", ""
            ),
            "NOTION_AGENT_COMMUNICATION_DB": database_ids.get("AgentCommunication", ""),
            "NOTION_TASKS_DB": database_ids.get("Task", ""),
            # Additional databases for complete 16-database setup
            "NOTION_CONTACTS_PROFILES_DB": database_ids.get("ContactProfile", ""),
            "NOTION_COMMUNITY_HUB_DB": database_ids.get("CommunityMember", ""),
            "NOTION_PRODUCTS_SERVICES_DB": database_ids.get("ProductService", ""),
            "NOTION_MARKETING_CAMPAIGNS_DB": database_ids.get("MarketingCampaign", ""),
            "NOTION_FEEDBACK_SURVEYS_DB": database_ids.get("FeedbackSurvey", ""),
            "NOTION_REWARDS_BOUNTIES_DB": database_ids.get("RewardsBounty", ""),
        }

        # Write to the .env file
        with open(output_path, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        logger.info(f"Created environment file at {output_path}")


def validate_environment() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate the required environment variables.

    Returns:
        Tuple of (is_valid, notion_token, parent_page_id)
    """
    # Load environment variables
    load_dotenv()

    is_valid = True
    errors = []

    # Check for Notion API token
    notion_token = os.environ.get("NOTION_API_TOKEN")
    if not notion_token:
        errors.append("NOTION_API_TOKEN environment variable not set.")
        is_valid = False

    # Check for parent page ID
    parent_page_id = os.environ.get("NOTION_PARENT_PAGE_ID")
    if not parent_page_id:
        errors.append("NOTION_PARENT_PAGE_ID environment variable not set.")
        is_valid = False

    if not is_valid:
        print_error("Environment validation failed")
        for error in errors:
            print_error(f"- {error}")
        print_info("Please set the required environment variables in your .env file.")
        print_info("Example .env file:")
        print(
            """  NOTION_API_TOKEN=secret_your_token_here
  NOTION_PARENT_PAGE_ID=your_parent_page_id_here"""
        )

    return is_valid, notion_token, parent_page_id


async def verify_databases(
    setup: NotionDatabaseSetup, database_ids: Dict[str, str]
) -> bool:
    """
    Verify that all databases were created successfully.

    Args:
        setup: NotionDatabaseSetup instance
        database_ids: Dictionary of database IDs

    Returns:
        True if all databases are accessible, False otherwise
    """
    print_info("Verifying database access...")
    all_valid = True

    for name, db_id in database_ids.items():
        try:
            # Try to query each database
            setup.client.databases.retrieve(db_id)
            print_success(f"✓ {name} database is accessible")
        except Exception as e:
            print_error(f"✗ Cannot access {name} database: {e}")
            all_valid = False

    return all_valid


async def main():
    """Main function to create the Notion databases."""
    print_header("\n=== The HigherSelf Network Server: Notion Database Setup ===\n")

    # Validate environment variables
    is_valid, notion_token, parent_page_id = validate_environment()
    if not is_valid:
        return 1

    print_info(
        f"Setting up Notion databases for The HigherSelf Network in page ID: {parent_page_id}"
    )

    # Initialize setup
    setup = NotionDatabaseSetup(notion_token)

    # Validate Notion connection
    print_info("Validating Notion API connection...")
    if not await setup.validate_connection():
        return 1
    print_success("Notion API connection validated successfully")

    try:
        # Create all databases
        print_header("\nCreating Notion databases...")
        database_ids = await setup.create_all_databases(parent_page_id)

        # Verify database access
        print_header("\nVerifying database access...")
        if not await verify_databases(setup, database_ids):
            print_warning(
                "Some databases may not be accessible. Check permissions and try again."
            )

        # Create environment file
        output_path = ".env.notion"
        setup.create_env_file(database_ids, output_path)

        print_header("\n=== Database Setup Complete ===\n")
        print_info("The following databases were created:")
        for name, db_id in database_ids.items():
            print(f"  - {name}: {db_id}")

        print_success(f"\nEnvironment variables have been written to {output_path}")
        print_info(
            "Add these variables to your .env file for use with The HigherSelf Network Server."
        )
        print_info("Example:")
        print("  cat .env.notion >> .env")

        return 0

    except Exception as e:
        print_error(f"Error creating databases: {e}")
        logger.exception("Error in database setup")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
