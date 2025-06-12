"""
Audience Segmentation Agent for The HigherSelf Network.

This agent analyzes data from multiple sources to create and manage audience segments:
- Notion (customer interactions, leads)
- WooCommerce (purchases)
- Amelia (bookings)
- TutorLM (course enrollments)
- Typeform (submissions)

All segment data is stored and maintained in Notion as the central hub.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from agents.base_agent import BaseAgent
from models.audience_models import (AudienceSegment, CustomerProfile,
                                    InteractionType, SegmentCriteria,
                                    SegmentSyncResult)
from models.base import AgentCapability, ApiPlatform
from models.notion_db_models import BusinessEntity, WorkflowInstance
from services.notion_service import NotionService


class AudienceSegmentationAgent(BaseAgent):
    """
    Agent that analyzes customer data and creates audience segments.
    Uses Notion as the central hub for all audience data.
    """

    def __init__(
        self,
        agent_id: str = "AudienceSegmentationAgent",
        name: str = "Audience Segmentation Agent",
        description: str = "Analyzes customer data and creates audience segments",
        version: str = "1.0.0",
        business_entities: List[str] = None,
        api_keys: Dict[str, str] = None,
        notion_service: Optional[NotionService] = None,
        update_frequency_hours: int = 24,
    ):
        """Initialize the Audience Segmentation Agent."""
        capabilities = [
            AgentCapability.CUSTOMER_SEGMENTATION,
            AgentCapability.DATA_ANALYSIS,
            AgentCapability.CRM_SYNC,
        ]

        apis_utilized = [
            ApiPlatform.NOTION,
            ApiPlatform.WOOCOMMERCE,
            ApiPlatform.AMELIA,
            ApiPlatform.TUTORM,
            ApiPlatform.BEEHIIV,
            ApiPlatform.SIMPLE_TEXTING,
        ]

        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            version=version,
            capabilities=capabilities,
            apis_utilized=apis_utilized,
            business_entities=business_entities,
            notion_service=notion_service,
        )

        # Set up API credentials
        self.api_keys = api_keys or {}

        # Retrieve API keys from environment if not provided
        api_key_names = [
            "WOOCOMMERCE_API_KEY",
            "AMELIA_API_KEY",
            "TUTORM_API_KEY",
            "BEEHIIV_API_KEY",
            "SIMPLE_TEXTING_API_KEY",
        ]

        for key_name in api_key_names:
            if key_name not in self.api_keys and os.environ.get(key_name):
                self.api_keys[key_name] = os.environ.get(key_name)

        self.update_frequency = timedelta(hours=update_frequency_hours)
        self.logger.info("Audience Segmentation Agent initialized")

    async def analyze_customer_data(
        self,
        business_entity_id: str,
        data_sources: List[str] = None,
        days_to_analyze: int = 30,
    ) -> Dict[str, Any]:
        """
        Analyze customer data from multiple sources.
        Stores analysis results in Notion as the central hub.
        """
        self.logger.info(f"Analyzing customer data for {business_entity_id}")

        if not data_sources:
            data_sources = ["notion", "woocommerce", "amelia", "tutorm", "typeform"]

        # Prepare date ranges
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_to_analyze)

        # This would fetch and analyze real data in a full implementation
        # For now, simulate analysis results
        data_points = {
            "total_customers": 250,
            "new_customers": 45,
            "active_customers": 120,
            "product_categories": {
                "courses": 68,
                "workshops": 42,
                "retreats": 25,
                "art": 15,
            },
            "engagement_metrics": {
                "email_open_rate": 0.42,
                "form_submissions": 32,
                "course_completions": 18,
            },
            "sources": {"organic": 95, "referral": 65, "social": 50, "direct": 40},
        }

        # Store analysis in Notion (central hub)
        notion_svc = await self.notion_service

        # Update the business entity with latest analysis
        business_entity = await notion_svc.get_business_entity(business_entity_id)
        if business_entity:
            business_entity.customer_data_analysis = {
                "last_analysis_date": end_date.isoformat(),
                "analysis_period_days": days_to_analyze,
                "data_sources": data_sources,
                "results": data_points,
            }

            await notion_svc.update_page(business_entity)

            self.logger.info(
                f"Updated business entity {business_entity_id} with customer data analysis"
            )

        return {
            "status": "success",
            "business_entity_id": business_entity_id,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days_to_analyze,
            },
            "data_sources": data_sources,
            "results": data_points,
        }

    async def define_segment(
        self,
        business_entity_id: str,
        segment_name: str,
        segment_description: str,
        criteria: List[SegmentCriteria],
    ) -> Dict[str, Any]:
        """
        Define a new audience segment based on specific criteria.
        Stores segment definition in Notion as the central hub.
        """
        self.logger.info(f"Defining segment '{segment_name}' for {business_entity_id}")

        # Create segment in Notion
        notion_svc = await self.notion_service

        segment = AudienceSegment(
            name=segment_name,
            description=segment_description,
            criteria=criteria,
            business_entity_id=business_entity_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Store in Notion
        segment_id = await notion_svc.create_audience_segment(segment)

        self.logger.info(f"Created audience segment {segment_id} in Notion")

        return {
            "status": "success",
            "segment_id": segment_id,
            "segment_name": segment_name,
            "criteria_count": len(criteria),
        }

    async def refresh_segment(self, segment_id: str) -> Dict[str, Any]:
        """
        Refresh an audience segment by re-analyzing data and updating membership.
        Updates segment data in Notion as the central hub.
        """
        self.logger.info(f"Refreshing segment {segment_id}")

        # Get segment from Notion
        notion_svc = await self.notion_service
        segment = await notion_svc.get_audience_segment(segment_id)

        if not segment:
            return {"status": "error", "message": f"Segment {segment_id} not found"}

        # This would apply segment criteria to real data in a full implementation
        # For now, simulate segment refresh
        previous_count = segment.member_count
        new_count = previous_count + 5  # Simulate 5 new members

        # Update segment in Notion
        segment.member_count = new_count
        segment.updated_at = datetime.now()

        await notion_svc.update_audience_segment(segment)

        self.logger.info(
            f"Refreshed segment {segment_id} in Notion, member count: {new_count}"
        )

        return {
            "status": "success",
            "segment_id": segment_id,
            "segment_name": segment.name,
            "previous_count": previous_count,
            "new_count": new_count,
            "difference": new_count - previous_count,
        }

    async def sync_segment_to_platform(
        self, segment_id: str, platform: str
    ) -> Dict[str, Any]:
        """
        Sync an audience segment to an external platform like Beehiiv or Simple Texting.
        Updates sync status in Notion as the central hub.
        """
        self.logger.info(f"Syncing segment {segment_id} to {platform}")

        # Get segment from Notion
        notion_svc = await self.notion_service
        segment = await notion_svc.get_audience_segment(segment_id)

        if not segment:
            return {"status": "error", "message": f"Segment {segment_id} not found"}

        # Check if API key for platform is available
        platform_key = f"{platform.upper()}_API_KEY"
        if platform_key not in self.api_keys:
            return {
                "status": "error",
                "message": f"API key for {platform} not configured",
            }

        # This would sync segment to the external platform in a full implementation
        # For now, simulate sync
        external_id = segment.platform_ids.get(
            platform, f"{platform}_segment_{segment.name.lower().replace(' ', '_')}"
        )

        # Record sync result
        sync_result = SegmentSyncResult(
            segment_id=segment_id,
            platform=platform,
            external_id=external_id,
            status="success",
            member_count=segment.member_count,
            sync_time=datetime.now(),
        )

        # Update segment in Notion with platform ID and sync result
        segment.platform_ids[platform] = external_id
        segment.updated_at = datetime.now()

        # Store both updates in Notion
        await notion_svc.update_audience_segment(segment)
        await notion_svc.create_segment_sync_record(sync_result)

        self.logger.info(
            f"Synced segment {segment_id} to {platform} with external ID {external_id}"
        )

        return {
            "status": "success",
            "segment_id": segment_id,
            "segment_name": segment.name,
            "platform": platform,
            "external_id": external_id,
            "member_count": segment.member_count,
        }

    async def get_customer_segments(self, email: str) -> Dict[str, Any]:
        """
        Get segments that a customer belongs to.
        Retrieves information from Notion as the central hub.
        """
        self.logger.info(f"Getting segments for customer {email}")

        # Get customer profile from Notion
        notion_svc = await self.notion_service
        customer = await notion_svc.get_customer_by_email(email)

        if not customer:
            return {
                "status": "error",
                "message": f"Customer with email {email} not found",
            }

        # Get segments from Notion
        customer_segments = []
        for segment_id in customer.segments:
            segment = await notion_svc.get_audience_segment(segment_id)
            if segment:
                customer_segments.append(
                    {
                        "id": segment_id,
                        "name": segment.name,
                        "description": segment.description,
                    }
                )

        return {
            "status": "success",
            "email": email,
            "customer_name": f"{customer.first_name} {customer.last_name}",
            "segments": customer_segments,
        }

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an event received by this agent."""
        event_handlers = {
            "analyze_customer_data": self.analyze_customer_data,
            "define_segment": self.define_segment,
            "refresh_segment": self.refresh_segment,
            "sync_segment_to_platform": self.sync_segment_to_platform,
            "get_customer_segments": self.get_customer_segments,
        }

        handler = event_handlers.get(event_type)
        if not handler:
            return {
                "status": "error",
                "message": f"Unsupported event type: {event_type}",
            }

        try:
            return await handler(**event_data)
        except Exception as e:
            self.logger.error(f"Error processing {event_type}: {e}")
            return {"status": "error", "message": str(e)}

    async def check_health(self) -> Dict[str, Any]:
        """Check the health status of this agent."""
        health_checks = {
            "notion_api": False,
            "woocommerce_api": False,
            "amelia_api": False,
            "tutorm_api": False,
            "distribution_apis": False,
        }

        # Check Notion API
        try:
            notion_svc = await self.notion_service
            await notion_svc.query_database(BusinessEntity, limit=1)
            health_checks["notion_api"] = True
        except Exception as e:
            self.logger.error(f"Notion API health check failed: {e}")

        # Check other APIs based on available keys
        health_checks["woocommerce_api"] = "WOOCOMMERCE_API_KEY" in self.api_keys
        health_checks["amelia_api"] = "AMELIA_API_KEY" in self.api_keys
        health_checks["tutorm_api"] = "TUTORM_API_KEY" in self.api_keys
        health_checks["distribution_apis"] = (
            "BEEHIIV_API_KEY" in self.api_keys
            or "SIMPLE_TEXTING_API_KEY" in self.api_keys
        )

        return {
            "agent_id": self.agent_id,
            "status": "healthy" if all(health_checks.values()) else "degraded",
            "checks": health_checks,
            "timestamp": datetime.now().isoformat(),
        }
