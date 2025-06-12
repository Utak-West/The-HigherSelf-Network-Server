"""
Marketing Campaign Agent for The HigherSelf Network Server.

This agent is responsible for:
1. Managing marketing campaigns across various channels
2. Segmenting audiences and targeting contacts
3. Tracking campaign metrics and results
4. Integrating with email platforms like Beehiiv
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

# import logging # Replaced by loguru
from loguru import logger  # Added for direct loguru usage
from pydantic import ValidationError

from agents.base_agent import BaseAgent
from config.testing_mode import TestingMode, is_api_disabled
from models.base import AgentCapability, ApiPlatform
from models.notion_db_models_extended import ContactProfile, MarketingCampaign
from services.notion_service import NotionService

# logger = logging.getLogger(__name__) # Replaced by global loguru logger


class MarketingCampaignAgent(BaseAgent):
    """
    Agent for executing and tracking marketing campaigns across channels.
    Integrates with Beehiiv for newsletter campaigns and manages audience segmentation.
    """

    def __init__(self, notion_service: NotionService):
        """Initialize the Marketing Campaign Agent."""
        super().__init__(
            agent_id="marketing-campaign-agent",
            name="Marketing Campaign Agent",
            description="Executes marketing campaigns and tracks performance metrics",
            version="1.0",
            capabilities=[
                AgentCapability.CLIENT_COMMUNICATION,
                AgentCapability.NOTIFICATION_DISPATCH,
                AgentCapability.CONTENT_GENERATION,
            ],
            apis_utilized=[
                ApiPlatform.NOTION,
                ApiPlatform.HUBSPOT,  # Optional CRM integration
            ],
        )
        self.notion_service = notion_service
        logger.info("Marketing Campaign Agent initialized")

    async def execute_email_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Execute an email campaign based on details stored in Notion.

        Args:
            campaign_id: ID of the campaign in Marketing Campaigns DB

        Returns:
            Result of campaign execution with metrics
        """
        logger.info(f"Executing email campaign {campaign_id}")

        # Step 1: Get campaign details from Notion
        filter_conditions = {
            "property": "campaign_id",
            "rich_text": {"equals": campaign_id},
        }
        campaigns = await self.notion_service.query_database(
            MarketingCampaign, filter_conditions=filter_conditions
        )

        if not campaigns:
            raise ValueError(f"Campaign with ID {campaign_id} not found")

        campaign = campaigns[0]

        # Step 2: Get target contacts based on segmentation criteria
        target_contacts = await self._get_targeted_contacts(campaign.target_contacts)

        if not target_contacts:
            logger.warning(
                f"No contacts match the targeting criteria for campaign {campaign_id}"
            )
            return {
                "success": False,
                "message": "No contacts match the targeting criteria",
                "campaign_id": campaign_id,
            }

        # Step 3: Get notification template content
        template_ids = campaign.related_notification_templates
        if not template_ids:
            raise ValueError("Campaign has no associated notification templates")

        # For simplicity, use the first template
        template_id = template_ids[0]
        template = await self._get_notification_template(template_id)

        # Step 4: Send campaign through selected channel (e.g., Beehiiv)
        if campaign.channels and "Email - Beehiiv" in campaign.channels:
            result = await self._send_beehiiv_campaign(
                campaign, target_contacts, template
            )
        else:
            raise ValueError(f"Unsupported campaign channel: {campaign.channels}")

        # Step 5: Update campaign with initial metrics
        campaign.status = "Active"
        campaign.last_updated = datetime.now()
        await self.notion_service.update_page(campaign)

        return {
            "success": True,
            "campaign_id": campaign_id,
            "message": f"Campaign executed successfully, sent to {len(target_contacts)} contacts",
            "recipients_count": len(target_contacts),
            **result,
        }

    async def track_campaign_metrics(self, campaign_id: str) -> Dict[str, Any]:
        """
        Update campaign metrics by retrieving analytics data from the email provider.

        Args:
            campaign_id: ID of the campaign to update metrics for

        Returns:
            Updated metrics for the campaign
        """
        logger.info(f"Tracking metrics for campaign {campaign_id}")

        # Get campaign details
        filter_conditions = {
            "property": "campaign_id",
            "rich_text": {"equals": campaign_id},
        }
        campaigns = await self.notion_service.query_database(
            MarketingCampaign, filter_conditions=filter_conditions
        )

        if not campaigns:
            raise ValueError(f"Campaign with ID {campaign_id} not found")

        campaign = campaigns[0]

        # Retrieve metrics based on campaign channel
        if campaign.channels and "Email - Beehiiv" in campaign.channels:
            metrics = await self._get_beehiiv_metrics(campaign)
        else:
            raise ValueError(
                f"Unsupported campaign channel for metrics: {campaign.channels}"
            )

        # Update campaign in Notion with new metrics
        campaign.leads_generated = metrics.get("new_leads", campaign.leads_generated)
        campaign.conversions = metrics.get("conversions", campaign.conversions)
        campaign.results_summary = json.dumps(metrics)
        campaign.last_updated = datetime.now()

        await self.notion_service.update_page(campaign)

        return {"success": True, "campaign_id": campaign_id, "metrics": metrics}

    async def _get_targeted_contacts(
        self, targeting_criteria: Dict[str, Any]
    ) -> List[ContactProfile]:
        """
        Get contacts matching the targeting criteria.

        Args:
            targeting_criteria: Criteria for selecting contacts

        Returns:
            List of contacts matching criteria
        """
        # Convert targeting criteria to Notion filter conditions
        filter_conditions = self._build_filter_from_criteria(targeting_criteria)

        # Query Contacts DB with filter
        contacts = await self.notion_service.query_database(
            ContactProfile, filter_conditions=filter_conditions
        )

        return contacts

    def _build_filter_from_criteria(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a Notion filter from targeting criteria.

        Args:
            criteria: Targeting criteria from campaign

        Returns:
            Notion filter object
        """
        # Convert high-level criteria to Notion filters
        # This is a simplified example - real implementation would be more complex
        filters = []

        if "segments" in criteria and criteria["segments"]:
            # Filter by segments
            segment_filter = {
                "property": "marketing_segments",
                "multi_select": {
                    "contains": criteria["segments"][0]  # Simplified for demo
                },
            }
            filters.append(segment_filter)

        if "status" in criteria:
            # Filter by contact status
            status_filter = {
                "property": "status",
                "select": {"equals": criteria["status"]},
            }
            filters.append(status_filter)

        # Combine filters with AND logic
        if len(filters) > 1:
            return {"and": filters}
        elif filters:
            return filters[0]
        else:
            # Default to active contacts
            return {"property": "status", "select": {"equals": "Active"}}

    async def _get_notification_template(self, template_id: str) -> Dict[str, Any]:
        """
        Get a notification template by ID.

        Args:
            template_id: ID of the notification template

        Returns:
            Template content and details
        """
        # Get template from Notion
        filter_conditions = {
            "property": "template_id",
            "rich_text": {"equals": template_id},
        }

        templates = await self.notion_service.query_database(
            model_class="NotificationTemplate",  # Use string as it's imported via *
            filter_conditions=filter_conditions,
        )

        if not templates:
            raise ValueError(f"Template with ID {template_id} not found")

        template = templates[0]

        return {
            "subject": template.subject_template,
            "content": template.content_template,
            "placeholders": template.supported_placeholders,
        }

    async def _send_beehiiv_campaign(
        self,
        campaign: MarketingCampaign,
        contacts: List[ContactProfile],
        template: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Send a campaign through Beehiiv API.

        Args:
            campaign: Campaign details
            contacts: Target contacts
            template: Email template

        Returns:
            Result of sending campaign
        """
        # This would use a BeehiivService in a real implementation
        # For this example, we'll simulate API calls

        # Check if in testing mode
        if is_api_disabled("beehiiv"):
            TestingMode.log_attempted_api_call(
                api_name="beehiiv",
                endpoint="campaigns/send",
                method="POST",
                params={
                    "campaign_name": campaign.name,
                    "recipients_count": len(contacts),
                },
            )
            logger.info(
                f"[TESTING MODE] Simulated sending Beehiiv campaign to {len(contacts)} recipients"
            )
            return {
                "provider": "beehiiv",
                "campaign_external_id": f"beehiiv_test_{campaign.campaign_id}",
                "send_time": datetime.now().isoformat(),
            }

        # In a real implementation, this would make an API call to Beehiiv
        # For demonstration purposes, we're simulating the API call
        logger.info(f"Sending Beehiiv campaign to {len(contacts)} contacts")

        # Prepare recipient data
        recipients = [
            {"email": contact.email, "name": contact.full_name}
            for contact in contacts
            if contact.email
        ]

        # Simulate API call to Beehiiv
        # In real implementation: result = await beehiiv_service.send_campaign(...)
        return {
            "provider": "beehiiv",
            "campaign_external_id": f"beehiiv_{campaign.campaign_id}",
            "send_time": datetime.now().isoformat(),
        }

    async def _get_beehiiv_metrics(self, campaign: MarketingCampaign) -> Dict[str, Any]:
        """
        Get metrics for a Beehiiv campaign.

        Args:
            campaign: Campaign to get metrics for

        Returns:
            Campaign metrics
        """
        # Check if in testing mode
        if is_api_disabled("beehiiv"):
            TestingMode.log_attempted_api_call(
                api_name="beehiiv",
                endpoint="campaigns/metrics",
                method="GET",
                params={"campaign_external_id": f"beehiiv_{campaign.campaign_id}"},
            )
            logger.info(
                f"[TESTING MODE] Simulated retrieving Beehiiv metrics for campaign {campaign.campaign_id}"
            )
            # Return simulated metrics
            return {
                "opens": 42,
                "clicks": 18,
                "unique_opens": 35,
                "unique_clicks": 15,
                "open_rate": 0.35,
                "click_rate": 0.15,
                "unsubscribes": 2,
                "new_leads": 5,
                "conversions": 2,
            }

        # In a real implementation, this would make an API call to Beehiiv
        # For demonstration purposes, we're simulating the API call
        logger.info(f"Getting Beehiiv metrics for campaign {campaign.campaign_id}")

        # Simulate API call to Beehiiv analytics endpoint
        # In real implementation: metrics = await beehiiv_service.get_campaign_metrics(...)
        return {
            "opens": 42,
            "clicks": 18,
            "unique_opens": 35,
            "unique_clicks": 15,
            "open_rate": 0.35,
            "click_rate": 0.15,
            "unsubscribes": 2,
            "new_leads": 5,
            "conversions": 2,
        }
