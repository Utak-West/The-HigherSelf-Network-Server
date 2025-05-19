"""
The HigherSelf Network Server - Agent Personality System

This module implements the named agent personalities that bring character
and intentionality to automated processes within The HigherSelf Network Server.
Each agent has a distinct name, tone, and specialized role while maintaining
Notion as the central hub.
"""

import asyncio
import inspect
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from loguru import logger

from models.base import AgentCapability, InstanceStatus
from models.notion_db_models import WorkflowInstance
from utils.message_bus import AgentMessage, MessageBus

from .base_agent import BaseAgent


class Nyra(BaseAgent):
    """
    Nyra - Lead Capture Specialist

    Intuitive & responsive agent that captures leads from various sources
    like Typeform, Snov.io, and Userfeedback, with optional HubSpot CRM synchronization.

    From the Sanskrit root *nira* meaning "water," Nyra embodies the fluid,
    adaptable nature of lead capture, ensuring that no potential relationship is lost.
    """

    def __init__(self, notion_client=None, **kwargs):
        agent_id = kwargs.get("agent_id", "nyra_lead_capture_agent")
        description = (
            "Intuitive & responsive agent that captures leads from various sources"
        )
        super().__init__(
            agent_id=agent_id,
            name="Nyra",
            description=description,
            notion_service=notion_client,
            **kwargs,
        )
        self.agent_type = "LeadCaptureAgent"
        self.tone = "Intuitive & responsive"

    async def run(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process new leads from various intake sources and create/update
        corresponding records in Notion databases.

        Args:
            event_data: Data from the triggering event (form submission, API webhook, etc.)

        Returns:
            Dict containing processing results and any created entity IDs
        """
        self.logger.info(
            f"Nyra processing lead capture event: {event_data.get('source', 'unknown')}"
        )

        # Fetch leads from Typeform, Snov.io, etc.
        # Create/update Contact & Business Entity records in Notion

        # Implementation will be added based on existing LeadCaptureAgent logic

        return {"status": "processed", "message": "Lead captured successfully"}

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an event received by this agent.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Processing result
        """
        # Map event types to handler methods
        event_handlers = {
            "typeform_webhook": self.run,
            "website_form": self.run,
            "lead_capture": self.run,
            "new_lead": self.run,
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Nyra: {event_type}")
            return {
                "status": "error",
                "message": f"Unsupported event type: {event_type}",
            }

        try:
            return await handler(event_data)
        except Exception as e:
            self.logger.error(f"Error processing {event_type}: {e}")
            return {"status": "error", "message": str(e)}

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.

        Returns:
            Health check result
        """
        try:
            # Check if Notion service is available
            notion_svc = await self.notion_service
            if notion_svc:
                return {
                    "status": "healthy",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": True,
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available",
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e),
            }


class Solari(BaseAgent):
    """
    Solari - Booking & Order Manager

    Clear & luminous agent that processes retreat bookings from Amelia
    and handles WooCommerce orders, creating and managing workflow instances.

    Bringing solar precision to booking processes, Solari manages the structured flow of
    appointments, retreats, and purchases with clarity and warmth.
    """

    def __init__(self, notion_client=None, **kwargs):
        agent_id = kwargs.get("agent_id", "solari_booking_agent")
        description = (
            "Clear & luminous agent that processes retreat bookings and orders"
        )
        super().__init__(
            agent_id=agent_id,
            name="Solari",
            description=description,
            notion_service=notion_client,
            **kwargs,
        )
        self.agent_type = "BookingAgent"
        self.tone = "Clear & luminous"

    async def run(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process booking data from Amelia or order data from WooCommerce,
        creating workflow instances and linking to products/contacts.

        Args:
            event_data: Booking or order data from the triggering event

        Returns:
            Dict containing processing results and created workflow instance IDs
        """
        self.logger.info(
            f"Solari processing booking/order event: {event_data.get('type', 'unknown')}"
        )

        # Sync booking data from Amelia/WooCommerce
        # Create Workflow Instances & link to Products/Contacts

        # Implementation will be added based on existing BookingAgent logic

        return {
            "status": "processed",
            "message": "Booking/order processed successfully",
        }

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an event received by this agent.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Processing result
        """
        # Map event types to handler methods
        event_handlers = {
            "new_booking": self.run,
            "booking_status_update": self.run,
            "order_created": self.run,
            "booking_created": self.run,
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Solari: {event_type}")
            return {
                "status": "error",
                "message": f"Unsupported event type: {event_type}",
            }

        try:
            return await handler(event_data)
        except Exception as e:
            self.logger.error(f"Error processing {event_type}: {e}")
            return {"status": "error", "message": str(e)}

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.

        Returns:
            Health check result
        """
        try:
            # Check if Notion service is available
            notion_svc = await self.notion_service
            if notion_svc:
                return {
                    "status": "healthy",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": True,
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available",
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e),
            }


class Ruvo(BaseAgent):
    """
    Ruvo - Task Orchestrator

    Grounded & task-driven agent that creates, assigns, and tracks tasks
    based on workflow events and templates.

    Derived from *ruvus* (Latin root of "resolve"), Ruvo handles the practical
    execution of workflow-generated tasks with calm efficiency.
    """

    def __init__(self, notion_client=None, **kwargs):
        agent_id = kwargs.get("agent_id", "ruvo_task_agent")
        description = (
            "Grounded & task-driven agent that creates, assigns, and tracks tasks"
        )
        super().__init__(
            agent_id=agent_id,
            name="Ruvo",
            description=description,
            notion_service=notion_client,
            **kwargs,
        )
        self.agent_type = "TaskManagementAgent"
        self.tone = "Grounded & task-driven"

    async def run(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create and assign tasks based on workflow events and templates,
        updating the Master Tasks database in Notion.

        Args:
            event_data: Workflow status change or task creation request data

        Returns:
            Dict containing processing results and created task IDs
        """
        self.logger.info(
            f"Ruvo processing task event: {event_data.get('trigger', 'unknown')}"
        )

        # Monitor Workflow status changes
        # Generate tasks using templates; update Master Tasks DB

        # Implementation will be added based on existing TaskManagementAgent logic

        return {"status": "processed", "message": "Tasks created successfully"}

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an event received by this agent.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Processing result
        """
        # Map event types to handler methods
        event_handlers = {
            "create_task": self.run,
            "update_task_status": self.run,
            "workflow_status_changed": self.run,
            "task_needed": self.run,
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Ruvo: {event_type}")
            return {
                "status": "error",
                "message": f"Unsupported event type: {event_type}",
            }

        try:
            return await handler(event_data)
        except Exception as e:
            self.logger.error(f"Error processing {event_type}: {e}")
            return {"status": "error", "message": str(e)}

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.

        Returns:
            Health check result
        """
        try:
            # Check if Notion service is available
            notion_svc = await self.notion_service
            if notion_svc:
                return {
                    "status": "healthy",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": True,
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available",
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e),
            }


class Liora(BaseAgent):
    """
    Liora - Marketing Strategist

    Elegant & strategic agent that manages email campaigns through Beehiiv,
    including audience targeting and performance tracking.

    Liora ("light-bearer") brings illumination and strategic thinking to marketing campaigns,
    maintaining a calm presence amid the chaos of promotional activities.
    """

    def __init__(self, notion_client=None, **kwargs):
        agent_id = kwargs.get("agent_id", "liora_marketing_agent")
        description = "Elegant & strategic agent that manages email campaigns"
        super().__init__(
            agent_id=agent_id,
            name="Liora",
            description=description,
            notion_service=notion_client,
            **kwargs,
        )
        self.agent_type = "MarketingCampaignAgent"
        self.tone = "Elegant & strategic"

    async def run(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage marketing campaigns through Beehiiv, including audience targeting
        and performance tracking.

        Args:
            event_data: Campaign trigger or metrics data

        Returns:
            Dict containing processing results and campaign IDs
        """
        self.logger.info(
            f"Liora processing marketing campaign event: {event_data.get('campaign_type', 'unknown')}"
        )

        # Read marketing strategies from Notion
        # Send campaign triggers to Beehiiv; log results

        # Implementation will be added based on existing MarketingCampaignAgent logic

        return {"status": "processed", "message": "Campaign processed successfully"}

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an event received by this agent.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Processing result
        """
        # Map event types to handler methods
        event_handlers = {
            "campaign_trigger": self.run,
            "campaign_metrics": self.run,
            "email_campaign": self.run,
            "newsletter_metrics": self.run,
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Liora: {event_type}")
            return {
                "status": "error",
                "message": f"Unsupported event type: {event_type}",
            }

        try:
            return await handler(event_data)
        except Exception as e:
            self.logger.error(f"Error processing {event_type}: {e}")
            return {"status": "error", "message": str(e)}

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.

        Returns:
            Health check result
        """
        try:
            # Check if Notion service is available
            notion_svc = await self.notion_service
            if notion_svc:
                return {
                    "status": "healthy",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": True,
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available",
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e),
            }


class Sage(BaseAgent):
    """
    Sage - Community Curator

    Warm & connected agent that handles community member interactions in Circle.so,
    tracking engagement and managing member profiles.

    Sage embodies the collective wisdom of community interactions, holding space for
    relationships with a warm, inviting presence.
    """

    def __init__(self, notion_client=None, **kwargs):
        agent_id = kwargs.get("agent_id", "sage_community_agent")
        description = (
            "Warm & connected agent that handles community member interactions"
        )
        super().__init__(
            agent_id=agent_id,
            name="Sage",
            description=description,
            notion_service=notion_client,
            **kwargs,
        )
        self.agent_type = "CommunityEngagementAgent"
        self.tone = "Warm & connected"

    async def run(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle community member interactions in Circle.so, tracking engagement
        and managing member profiles in the Community Hub database.

        Args:
            event_data: Community event data from Circle.so

        Returns:
            Dict containing processing results and community activity IDs
        """
        self.logger.info(
            f"Sage processing community event: {event_data.get('event_type', 'unknown')}"
        )

        # Track activity in Circle.so
        # Update Community Hub DB and member profile engagement

        # Implementation will be added based on existing CommunityEngagementAgent logic

        return {
            "status": "processed",
            "message": "Community event processed successfully",
        }

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an event received by this agent.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Processing result
        """
        # Map event types to handler methods
        event_handlers = {
            "community_event": self.run,
            "member_activity": self.run,
            "new_member": self.run,
            "member_engagement": self.run,
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Sage: {event_type}")
            return {
                "status": "error",
                "message": f"Unsupported event type: {event_type}",
            }

        try:
            return await handler(event_data)
        except Exception as e:
            self.logger.error(f"Error processing {event_type}: {e}")
            return {"status": "error", "message": str(e)}

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.

        Returns:
            Health check result
        """
        try:
            # Check if Notion service is available
            notion_svc = await self.notion_service
            if notion_svc:
                return {
                    "status": "healthy",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": True,
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available",
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e),
            }


class Elan(BaseAgent):
    """
    Elan - Content Choreographer

    Creative & adaptive agent that manages content from idea generation to
    distribution across various platforms.

    Elan ("energetic momentum") manages content with both flair and discipline,
    ensuring that creative work moves through the system with inspiration and structure.
    """

    def __init__(self, notion_client=None, **kwargs):
        agent_id = kwargs.get("agent_id", "elan_content_agent")
        description = "Creative & adaptive agent that manages content lifecycle"
        super().__init__(
            agent_id=agent_id,
            name="Elan",
            description=description,
            notion_service=notion_client,
            **kwargs,
        )
        self.agent_type = "ContentLifecycleAgent"
        self.tone = "Creative & adaptive"

        # Initialize the video content agent extension
        from agents.video_content_agent import VideoContentAgent

        self.video_agent = VideoContentAgent(notion_service=notion_client)

    async def run(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage content lifecycle from idea generation to distribution across platforms,
        tracking content performance metrics.

        Args:
            event_data: Content event data (idea submission, stage change, etc.)

        Returns:
            Dict containing processing results and content item IDs
        """
        self.logger.info(
            f"Elan processing content event: {event_data.get('content_type', 'unknown')}"
        )

        # Pull content ideas, schedule posts
        # Update lifecycle stages across Notion + distribute

        # Implementation will be added based on existing ContentLifecycleAgent logic

        return {"status": "processed", "message": "Content processed successfully"}

    async def generate_video(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a video using MoneyPrinterTurbo integration.

        Args:
            event_data: Video generation parameters

        Returns:
            Dict containing processing results and video content ID
        """
        self.logger.info(
            f"Elan generating video for topic: {event_data.get('topic', 'unknown')}"
        )

        # Convert event data to VideoGenerationConfig
        from models.video_models import VideoGenerationConfig

        try:
            # Extract required parameters
            config = VideoGenerationConfig(
                topic=event_data.get("topic", ""),
                language=event_data.get("language", "en"),
                voice_name=event_data.get("voice_name"),
                resolution=event_data.get("resolution", "1080x1920"),
                clip_duration=event_data.get("clip_duration", 5),
                subtitle_font=event_data.get("subtitle_font"),
                subtitle_position=event_data.get("subtitle_position", "bottom"),
                subtitle_color=event_data.get("subtitle_color", "#FFFFFF"),
                subtitle_size=event_data.get("subtitle_size", 40),
                subtitle_stroke_width=event_data.get("subtitle_stroke_width", 1.5),
                background_music_volume=event_data.get("background_music_volume", 0.1),
                custom_script=event_data.get("custom_script"),
            )

            # Get business entity ID
            business_entity_id = event_data.get(
                "business_entity_id", "the_connection_practice"
            )

            # Generate video using the video agent extension
            result = await self.video_agent.generate_video(config, business_entity_id)

            return result
        except Exception as e:
            self.logger.error(f"Error generating video: {e}")
            return {"status": "error", "message": str(e)}

    async def get_video_status(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the status of a video generation task.

        Args:
            event_data: Must contain content_id

        Returns:
            Dict containing status information
        """
        content_id = event_data.get("content_id")
        if not content_id:
            return {"status": "error", "message": "content_id is required"}

        return await self.video_agent.get_video_status(content_id)

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an event received by this agent.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Processing result
        """
        # Map event types to handler methods
        event_handlers = {
            "content_ready": self.run,
            "content_stage_change": self.run,
            "generate_content": self.run,
            "distribute_content": self.run,
            "generate_video": self.generate_video,
            "get_video_status": self.get_video_status,
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Elan: {event_type}")
            return {
                "status": "error",
                "message": f"Unsupported event type: {event_type}",
            }

        try:
            return await handler(event_data)
        except Exception as e:
            self.logger.error(f"Error processing {event_type}: {e}")
            return {"status": "error", "message": str(e)}

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.

        Returns:
            Health check result
        """
        try:
            # Check if Notion service is available
            notion_svc = await self.notion_service
            if notion_svc:
                return {
                    "status": "healthy",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": True,
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available",
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e),
            }


class Zevi(BaseAgent):
    """
    Zevi - Audience Analyst

    Analytical & sharp agent that analyzes customer data to create and manage
    audience segments for targeted marketing.

    Named after the wolf (keen observer), Zevi brings analytical precision to
    audience segmentation with sharp perception of patterns.
    """

    def __init__(self, notion_client=None, **kwargs):
        agent_id = kwargs.get("agent_id", "zevi_audience_agent")
        description = (
            "Analytical & sharp agent that analyzes customer data for segmentation"
        )
        super().__init__(
            agent_id=agent_id,
            name="Zevi",
            description=description,
            notion_service=notion_client,
            **kwargs,
        )
        self.agent_type = "AudienceSegmentationAgent"
        self.tone = "Analytical & sharp"

    async def run(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze customer data to create and manage audience segments for
        targeted marketing campaigns.

        Args:
            event_data: Analysis trigger or customer data update

        Returns:
            Dict containing processing results and segment IDs
        """
        self.logger.info(
            f"Zevi processing audience segmentation event: {event_data.get('analysis_type', 'unknown')}"
        )

        # Analyze customer data, generate audience tags
        # Link results to Campaigns, Community Hub

        # Implementation will be added based on existing AudienceSegmentationAgent logic

        return {
            "status": "processed",
            "message": "Audience analysis completed successfully",
        }

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an event received by this agent.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Processing result
        """
        # Map event types to handler methods
        event_handlers = {
            "audience_analysis": self.run,
            "segment_update": self.run,
            "customer_data_update": self.run,
            "analyze_audience": self.run,
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Zevi: {event_type}")
            return {
                "status": "error",
                "message": f"Unsupported event type: {event_type}",
            }

        try:
            return await handler(event_data)
        except Exception as e:
            self.logger.error(f"Error processing {event_type}: {e}")
            return {"status": "error", "message": str(e)}

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.

        Returns:
            Health check result
        """
        try:
            # Check if Notion service is available
            notion_svc = await self.notion_service
            if notion_svc:
                return {
                    "status": "healthy",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": True,
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available",
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e),
            }


class GraceFields:
    """
    Grace Fields - Master Orchestrator

    The orchestration layer that intelligently coordinates specialized AI agents
    to support the operations of multiple business entities within The HigherSelf
    Network ecosystem.

    Grace Fields ensures that each agent is activated at the right time, maintaining
    the flow of information and actions throughout the system. She serves as the
    central intelligence that coordinates all agent activities and complex workflows
    while maintaining the unique vision and values of each business entity.
    """

    def __init__(
        self, agents: List[BaseAgent], message_bus: Optional[MessageBus] = None
    ):
        """
        Initialize the orchestrator with a list of agent instances.

        Args:
            agents: List of agent instances to be managed by this orchestrator
            message_bus: Optional MessageBus instance for inter-agent communication
        """
        self.agents = {agent.name: agent for agent in agents}
        self.agent_types = {agent.agent_type: agent.name for agent in agents}
        self.message_bus = message_bus
        self.logger = logger.bind(component="GraceFields")

        # Track active workflows for monitoring and coordination
        self.active_workflows = {}

        # Track agent capabilities for capability-based routing
        self.agent_capabilities = {}
        for name, agent in self.agents.items():
            if hasattr(agent, "capabilities"):
                for capability in agent.capabilities:
                    if capability not in self.agent_capabilities:
                        self.agent_capabilities[capability] = []
                    self.agent_capabilities[capability].append(name)

        # Event routing map - maps event types to agent names
        self.event_routing = {
            # Nyra - Lead Capture events
            "new_lead": "Nyra",
            "typeform_webhook": "Nyra",
            "website_form": "Nyra",
            "lead_capture": "Nyra",
            "lead_enrichment": "Nyra",
            "contact_update": "Nyra",
            # Solari - Booking & Order events
            "booking_created": "Solari",
            "order_created": "Solari",
            "new_booking": "Solari",
            "booking_status_update": "Solari",
            "payment_received": "Solari",
            "appointment_reminder": "Solari",
            "retreat_registration": "Solari",
            # Ruvo - Task Management events
            "workflow_status_changed": "Ruvo",
            "task_needed": "Ruvo",
            "create_task": "Ruvo",
            "update_task_status": "Ruvo",
            "task_reminder": "Ruvo",
            "task_assignment": "Ruvo",
            "task_completion": "Ruvo",
            # Elan - Content Lifecycle events
            "content_ready": "Elan",
            "content_stage_change": "Elan",
            "generate_content": "Elan",
            "distribute_content": "Elan",
            "content_idea": "Elan",
            "content_draft": "Elan",
            "content_review": "Elan",
            "content_publish": "Elan",
            # Sage - Community Engagement events
            "community_event": "Sage",
            "member_activity": "Sage",
            "new_member": "Sage",
            "member_engagement": "Sage",
            "forum_post": "Sage",
            "community_question": "Sage",
            "member_milestone": "Sage",
            # Zevi - Audience Segmentation events
            "audience_analysis": "Zevi",
            "segment_update": "Zevi",
            "customer_data_update": "Zevi",
            "analyze_audience": "Zevi",
            "segment_creation": "Zevi",
            "audience_insight": "Zevi",
            "customer_journey": "Zevi",
            # Liora - Marketing Campaign events
            "campaign_trigger": "Liora",
            "campaign_metrics": "Liora",
            "email_campaign": "Liora",
            "newsletter_metrics": "Liora",
            "campaign_schedule": "Liora",
            "marketing_content": "Liora",
            "campaign_performance": "Liora",
        }

        # Define multi-agent workflow patterns
        self.workflow_patterns = {
            # Lead capture to booking workflow
            "lead_to_booking": {
                "description": "Process a lead from capture through to booking",
                "steps": [
                    {
                        "agent": "Nyra",
                        "event": "lead_capture",
                        "next_on_success": "lead_enrichment",
                    },
                    {
                        "agent": "Nyra",
                        "event": "lead_enrichment",
                        "next_on_success": "create_task",
                    },
                    {
                        "agent": "Ruvo",
                        "event": "create_task",
                        "next_on_success": "campaign_trigger",
                    },
                    {
                        "agent": "Liora",
                        "event": "campaign_trigger",
                        "next_on_success": None,
                    },
                ],
            },
            # Content creation and distribution workflow
            "content_lifecycle": {
                "description": "Manage content from idea to distribution",
                "steps": [
                    {
                        "agent": "Elan",
                        "event": "content_idea",
                        "next_on_success": "content_draft",
                    },
                    {
                        "agent": "Elan",
                        "event": "content_draft",
                        "next_on_success": "content_review",
                    },
                    {
                        "agent": "Elan",
                        "event": "content_review",
                        "next_on_success": "content_publish",
                    },
                    {
                        "agent": "Elan",
                        "event": "content_publish",
                        "next_on_success": "campaign_trigger",
                    },
                    {
                        "agent": "Liora",
                        "event": "campaign_trigger",
                        "next_on_success": "audience_analysis",
                    },
                    {
                        "agent": "Zevi",
                        "event": "audience_analysis",
                        "next_on_success": None,
                    },
                ],
            },
            # Retreat booking workflow
            "retreat_booking": {
                "description": "Handle retreat booking from registration to completion",
                "steps": [
                    {
                        "agent": "Solari",
                        "event": "retreat_registration",
                        "next_on_success": "payment_received",
                    },
                    {
                        "agent": "Solari",
                        "event": "payment_received",
                        "next_on_success": "create_task",
                    },
                    {
                        "agent": "Ruvo",
                        "event": "create_task",
                        "next_on_success": "appointment_reminder",
                    },
                    {
                        "agent": "Solari",
                        "event": "appointment_reminder",
                        "next_on_success": "community_event",
                    },
                    {
                        "agent": "Sage",
                        "event": "community_event",
                        "next_on_success": None,
                    },
                ],
            },
        }

        # Register for multi-agent workflow events
        if self.message_bus:
            self.message_bus.subscribe("GraceFields", self.process_message)

        self.logger.info("✨ Grace Fields initialized with enhanced capabilities")
        self.logger.info(
            f"Coordinating {len(self.agents)} agents: {', '.join(self.agents.keys())}"
        )
        if self.agent_capabilities:
            self.logger.info(
                f"Registered {len(self.agent_capabilities)} agent capabilities for dynamic routing"
            )

    async def route_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route an event to the appropriate agent(s) based on the event type.

        Grace Fields uses sophisticated routing logic to determine which agent(s)
        should handle each event, including pattern matching, capability-based routing,
        and multi-agent workflow orchestration.

        Args:
            event_type: Type of event to route
            event_data: Data associated with the event

        Returns:
            Dict containing processing results from the agent(s)
        """
        results = {}

        # Add tracking ID if not present
        if "tracking_id" not in event_data:
            event_data["tracking_id"] = str(uuid.uuid4())

        tracking_id = event_data.get("tracking_id")
        self.logger.info(
            f"Grace Fields processing event: {event_type} [tracking: {tracking_id}]"
        )

        # Check for named workflow patterns
        if event_type.startswith("workflow_pattern_"):
            pattern_name = event_type.replace("workflow_pattern_", "")
            if pattern_name in self.workflow_patterns:
                return await self.start_workflow_pattern(pattern_name, event_data)
            else:
                self.logger.warning(f"Unknown workflow pattern: {pattern_name}")
                return {"error": f"Unknown workflow pattern: {pattern_name}"}

        # Check for workflow continuation
        if (
            "workflow_id" in event_data
            and event_data.get("workflow_id") in self.active_workflows
        ):
            return await self.continue_workflow(
                event_data["workflow_id"], event_type, event_data
            )

        # Check if this is a multi-agent workflow event
        if event_type.startswith("workflow_"):
            return await self.handle_workflow_event(event_type, event_data)

        # Check for business entity specific routing
        business_entity = event_data.get("business_entity_id")
        if business_entity:
            # Try to find an agent specifically for this business entity
            for name, agent in self.agents.items():
                if (
                    hasattr(agent, "business_entities")
                    and business_entity in agent.business_entities
                ):
                    if await self._can_agent_handle_event(agent, event_type):
                        self.logger.info(
                            f"Business entity routing: {event_type} for {business_entity} to {name}"
                        )
                        return await self._route_to_agent(name, event_type, event_data)

        # Look up the appropriate agent in the routing map
        agent_name = self.event_routing.get(event_type)

        if agent_name and agent_name in self.agents:
            # Route to the specific agent
            return await self._route_to_agent(agent_name, event_type, event_data)

        # Try capability-based routing
        capability_result = await self._try_capability_routing(event_type, event_data)
        if capability_result:
            return capability_result

        # Try pattern-based routing
        if "_" in event_type:
            # Extract the domain from event type (e.g., "lead_capture" -> "lead")
            domain = event_type.split("_")[0]
            for pattern, agent in [
                ("lead", "Nyra"),
                ("contact", "Nyra"),
                ("book", "Solari"),
                ("order", "Solari"),
                ("payment", "Solari"),
                ("task", "Ruvo"),
                ("content", "Elan"),
                ("community", "Sage"),
                ("member", "Sage"),
                ("audience", "Zevi"),
                ("segment", "Zevi"),
                ("campaign", "Liora"),
                ("email", "Liora"),
                ("marketing", "Liora"),
            ]:
                if domain.startswith(pattern) and agent in self.agents:
                    self.logger.info(
                        f"Pattern-based routing: {event_type} to {agent} based on '{pattern}' prefix"
                    )
                    # Add to routing map for future use
                    self.event_routing[event_type] = agent
                    return await self._route_to_agent(agent, event_type, event_data)

        # Try to infer the agent from the event type by asking each agent
        for agent_name, agent in self.agents.items():
            if hasattr(agent, "process_event"):
                try:
                    # Check if the agent can handle this event type
                    agent_result = await agent.process_event(event_type, event_data)
                    if agent_result.get("status") != "error":
                        results[agent_name.lower()] = agent_result
                        self.logger.info(
                            f"Dynamic routing: {event_type} to {agent_name}"
                        )

                        # Add this event type to the routing map for future use
                        self.event_routing[event_type] = agent_name

                        # If we have a message bus, publish the event result
                        if self.message_bus:
                            await self.publish_event_result(
                                event_type, event_data, agent_name, agent_result
                            )

                        return results
                except Exception:
                    # This agent couldn't handle the event, try the next one
                    continue

        # If no agent could handle the event, try to delegate to AI router
        if hasattr(self, "ai_router") and self.ai_router:
            try:
                ai_routing_result = await self.ai_router.route_event(
                    event_type, event_data
                )
                if ai_routing_result.get("status") != "error":
                    self.logger.info(f"AI-based routing successful for {event_type}")
                    return ai_routing_result
            except Exception as e:
                self.logger.error(f"Error in AI-based routing: {e}")

        # If we get here, no agent could handle the event
        self.logger.warning(f"No agent available for event type: {event_type}")
        return {
            "error": f"No agent available for event type: {event_type}",
            "status": "error",
            "message": f"Grace Fields could not find an agent to handle {event_type}",
            "tracking_id": tracking_id,
        }

    async def _can_agent_handle_event(self, agent: BaseAgent, event_type: str) -> bool:
        """Check if an agent can handle a specific event type."""
        if not hasattr(agent, "process_event"):
            return False

        # Check if the agent has a specific handler for this event
        if hasattr(agent, "event_handlers") and event_type in agent.event_handlers:
            return True

        # For agents that use a map in process_event
        method_source = inspect.getsource(agent.process_event)
        if f'"{event_type}"' in method_source or f"'{event_type}'" in method_source:
            return True

        return False

    async def _route_to_agent(
        self, agent_name: str, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route an event to a specific agent and handle results."""
        results = {}
        self.logger.info(f"Grace Fields routing {event_type} to {agent_name}")

        try:
            # Process the event with the agent
            agent_result = await self.agents[agent_name].process_event(
                event_type, event_data
            )
            results[agent_name.lower()] = agent_result

            # If we have a message bus, publish the event for other interested agents
            if self.message_bus:
                await self.publish_event_result(
                    event_type, event_data, agent_name, agent_result
                )

            # Check if this event should trigger a workflow
            await self._check_for_workflow_triggers(
                event_type, event_data, agent_name, agent_result
            )

            return results
        except Exception as e:
            error_msg = f"Error routing {event_type} to {agent_name}: {e}"
            self.logger.error(error_msg)

            # Try to recover with a fallback agent if available
            fallback_result = await self._try_fallback_routing(
                event_type, event_data, agent_name
            )
            if fallback_result:
                return fallback_result

            # No fallback available
            return {
                "error": error_msg,
                "status": "error",
                "agent": agent_name,
                "tracking_id": event_data.get("tracking_id"),
            }

    async def _try_capability_routing(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Try to route an event based on required capabilities."""
        # Extract capabilities from event data if specified
        required_capability = event_data.get("required_capability")

        if required_capability and required_capability in self.agent_capabilities:
            # Find agents with this capability
            capable_agents = self.agent_capabilities[required_capability]
            if capable_agents:
                # Use the first capable agent
                agent_name = capable_agents[0]
                self.logger.info(
                    f"Capability-based routing: {event_type} to {agent_name} with {required_capability}"
                )
                return await self._route_to_agent(agent_name, event_type, event_data)

        return None

    async def _try_fallback_routing(
        self, event_type: str, event_data: Dict[str, Any], failed_agent: str
    ) -> Optional[Dict[str, Any]]:
        """Try to find a fallback agent when the primary agent fails."""
        # Skip fallback if explicitly disabled
        if event_data.get("disable_fallback", False):
            return None

        # Check if there's a defined fallback for this agent
        fallbacks = {
            "Nyra": ["Solari", "Zevi"],  # Lead capture fallbacks
            "Solari": ["Nyra", "Ruvo"],  # Booking fallbacks
            "Ruvo": ["Solari", "Liora"],  # Task fallbacks
            "Elan": ["Liora", "Sage"],  # Content fallbacks
            "Sage": ["Elan", "Zevi"],  # Community fallbacks
            "Zevi": ["Liora", "Nyra"],  # Audience fallbacks
            "Liora": ["Elan", "Zevi"],  # Marketing fallbacks
        }

        if failed_agent in fallbacks:
            for fallback_agent in fallbacks[failed_agent]:
                if fallback_agent in self.agents:
                    try:
                        self.logger.info(
                            f"Trying fallback from {failed_agent} to {fallback_agent} for {event_type}"
                        )
                        result = await self.agents[fallback_agent].process_event(
                            event_type, event_data
                        )
                        if result.get("status") != "error":
                            return {
                                fallback_agent.lower(): result,
                                "fallback_from": failed_agent,
                                "message": f"Fallback from {failed_agent} to {fallback_agent} successful",
                            }
                    except Exception:
                        continue

        return None

    async def _check_for_workflow_triggers(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        agent_name: str,
        agent_result: Dict[str, Any],
    ) -> None:
        """Check if an event should trigger a workflow."""
        # Define events that should trigger workflows
        workflow_triggers = {
            "lead_capture": "lead_to_booking",
            "content_idea": "content_lifecycle",
            "retreat_registration": "retreat_booking",
        }

        if event_type in workflow_triggers and agent_result.get("status") != "error":
            workflow_name = workflow_triggers[event_type]
            self.logger.info(f"Event {event_type} triggering workflow: {workflow_name}")

            # Start the workflow if it exists
            if workflow_name in self.workflow_patterns:
                workflow_data = {
                    **event_data,
                    "triggered_by": event_type,
                    "source_agent": agent_name,
                }
                await self.start_workflow_pattern(workflow_name, workflow_data)

    async def start_workflow_pattern(
        self, pattern_name: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Start a new workflow based on a predefined pattern.

        Args:
            pattern_name: Name of the workflow pattern to start
            event_data: Initial data for the workflow

        Returns:
            Dict containing the initial workflow results
        """
        if pattern_name not in self.workflow_patterns:
            return {"error": f"Unknown workflow pattern: {pattern_name}"}

        # Create a new workflow ID if not provided
        workflow_id = event_data.get("workflow_id", str(uuid.uuid4()))

        # Initialize workflow data
        workflow = {
            "id": workflow_id,
            "pattern": pattern_name,
            "status": "active",
            "current_step": 0,
            "start_time": datetime.now().isoformat(),
            "data": event_data,
            "results": {},
            "steps_completed": [],
        }

        # Store in active workflows
        self.active_workflows[workflow_id] = workflow

        self.logger.info(
            f"Grace Fields starting workflow pattern: {pattern_name} [ID: {workflow_id}]"
        )

        # Execute the first step
        pattern = self.workflow_patterns[pattern_name]
        first_step = pattern["steps"][0]

        agent_name = first_step["agent"]
        event_type = first_step["event"]

        # Add workflow context to the event data
        step_data = {
            **event_data,
            "workflow_id": workflow_id,
            "workflow_pattern": pattern_name,
            "workflow_step": 0,
            "is_workflow_step": True,
        }

        # Process the first step
        try:
            if agent_name in self.agents:
                step_result = await self.agents[agent_name].process_event(
                    event_type, step_data
                )

                # Update workflow with results
                workflow["results"][f"step_0_{agent_name}_{event_type}"] = step_result
                workflow["steps_completed"].append(0)

                # Check if we should continue to the next step
                if (
                    step_result.get("status") != "error"
                    and first_step["next_on_success"]
                ):
                    # Queue the next step for async execution
                    asyncio.create_task(
                        self._continue_workflow_async(
                            workflow_id, first_step["next_on_success"]
                        )
                    )

                return {
                    "status": "workflow_started",
                    "workflow_id": workflow_id,
                    "pattern": pattern_name,
                    "first_step_result": step_result,
                    "message": f"Workflow {pattern_name} started successfully",
                }
            else:
                error_msg = f"Agent {agent_name} not found for workflow step"
                self.logger.error(error_msg)
                return {"error": error_msg, "status": "error"}
        except Exception as e:
            error_msg = f"Error starting workflow {pattern_name}: {e}"
            self.logger.error(error_msg)
            return {"error": error_msg, "status": "error"}

    async def _continue_workflow_async(self, workflow_id: str, next_event: str) -> None:
        """Continue a workflow asynchronously with the next event."""
        if workflow_id not in self.active_workflows:
            self.logger.error(
                f"Cannot continue workflow {workflow_id}: not found in active workflows"
            )
            return

        workflow = self.active_workflows[workflow_id]

        # Find the next step in the pattern
        pattern = self.workflow_patterns[workflow["pattern"]]
        current_step = workflow["current_step"]
        next_step = current_step + 1

        if next_step >= len(pattern["steps"]):
            self.logger.info(f"Workflow {workflow_id} completed all steps")
            workflow["status"] = "completed"
            return

        # Update workflow step
        workflow["current_step"] = next_step

        # Get the next step details
        step = pattern["steps"][next_step]
        agent_name = step["agent"]
        event_type = step["event"]

        # If a specific next event was requested, use that instead
        if next_event:
            event_type = next_event

        # Prepare data for the next step
        step_data = {
            **workflow["data"],
            "workflow_id": workflow_id,
            "workflow_pattern": workflow["pattern"],
            "workflow_step": next_step,
            "is_workflow_step": True,
            "previous_results": workflow["results"],
        }

        # Execute the next step
        try:
            if agent_name in self.agents:
                self.logger.info(
                    f"Continuing workflow {workflow_id} with step {next_step}: {agent_name}.{event_type}"
                )
                step_result = await self.agents[agent_name].process_event(
                    event_type, step_data
                )

                # Update workflow with results
                workflow["results"][
                    f"step_{next_step}_{agent_name}_{event_type}"
                ] = step_result
                workflow["steps_completed"].append(next_step)

                # Check if we should continue to the next step
                if step_result.get("status") != "error" and step["next_on_success"]:
                    # Queue the next step for async execution
                    asyncio.create_task(
                        self._continue_workflow_async(
                            workflow_id, step["next_on_success"]
                        )
                    )
                elif (
                    step_result.get("status") != "error"
                    and next_step == len(pattern["steps"]) - 1
                ):
                    # This was the last step and it succeeded
                    workflow["status"] = "completed"
                    self.logger.info(f"Workflow {workflow_id} completed successfully")

                    # Publish workflow completion event if we have a message bus
                    if self.message_bus:
                        await self.message_bus.publish(
                            AgentMessage(
                                sender="GraceFields",
                                recipient="all",
                                message_type="workflow_completed",
                                payload={
                                    "workflow_id": workflow_id,
                                    "pattern": workflow["pattern"],
                                    "results": workflow["results"],
                                },
                            )
                        )
            else:
                self.logger.error(
                    f"Agent {agent_name} not found for workflow step {next_step}"
                )
                workflow["status"] = "error"
        except Exception as e:
            self.logger.error(f"Error in workflow {workflow_id} step {next_step}: {e}")
            workflow["status"] = "error"
            workflow["error"] = str(e)

    async def continue_workflow(
        self, workflow_id: str, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Continue an existing workflow with a new event.

        Args:
            workflow_id: ID of the workflow to continue
            event_type: Type of event to process
            event_data: Event data

        Returns:
            Dict containing the workflow continuation results
        """
        if workflow_id not in self.active_workflows:
            return {"error": f"Workflow {workflow_id} not found", "status": "error"}

        workflow = self.active_workflows[workflow_id]

        if workflow["status"] != "active":
            return {
                "error": f"Workflow {workflow_id} is not active (status: {workflow['status']})",
                "status": "error",
            }

        # Get the current step in the pattern
        pattern = self.workflow_patterns[workflow["pattern"]]
        current_step = workflow["current_step"]

        if current_step >= len(pattern["steps"]):
            return {
                "error": f"Workflow {workflow_id} has no more steps",
                "status": "error",
            }

        # Get the current step details
        step = pattern["steps"][current_step]
        agent_name = step["agent"]

        # Prepare data for this step
        step_data = {
            **event_data,
            "workflow_id": workflow_id,
            "workflow_pattern": workflow["pattern"],
            "workflow_step": current_step,
            "is_workflow_step": True,
            "previous_results": workflow["results"],
        }

        # Execute the step
        try:
            if agent_name in self.agents:
                self.logger.info(
                    f"Continuing workflow {workflow_id} with event {event_type} at step {current_step}"
                )
                step_result = await self.agents[agent_name].process_event(
                    event_type, step_data
                )

                # Update workflow with results
                workflow["results"][
                    f"step_{current_step}_{agent_name}_{event_type}"
                ] = step_result

                # Check if we should continue to the next step
                if step_result.get("status") != "error" and step["next_on_success"]:
                    # Move to the next step
                    workflow["current_step"] += 1
                    workflow["steps_completed"].append(current_step)

                    # Queue the next step for async execution
                    asyncio.create_task(
                        self._continue_workflow_async(
                            workflow_id, step["next_on_success"]
                        )
                    )

                return {
                    "status": "workflow_continued",
                    "workflow_id": workflow_id,
                    "step_result": step_result,
                    "message": f"Workflow {workflow_id} continued successfully",
                }
            else:
                error_msg = (
                    f"Agent {agent_name} not found for workflow step {current_step}"
                )
                self.logger.error(error_msg)
                return {"error": error_msg, "status": "error"}
        except Exception as e:
            error_msg = f"Error continuing workflow {workflow_id}: {e}"
            self.logger.error(error_msg)
            return {"error": error_msg, "status": "error"}

    async def handle_workflow_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle a workflow event that may involve multiple agents.

        Args:
            event_type: Type of workflow event
            event_data: Data associated with the event

        Returns:
            Dict containing processing results from all involved agents
        """
        results = {}
        workflow_id = event_data.get("workflow_id", str(uuid.uuid4()))

        # Add workflow ID if not present
        if "workflow_id" not in event_data:
            event_data["workflow_id"] = workflow_id

        self.logger.info(
            f"Grace Fields processing workflow event {event_type} [ID: {workflow_id}]"
        )

        # Check if this is a named workflow pattern
        if event_type.replace("workflow_", "") in self.workflow_patterns:
            pattern_name = event_type.replace("workflow_", "")
            return await self.start_workflow_pattern(pattern_name, event_data)

        # Handle specific workflow events
        if event_type == "workflow_lead_capture_complete":
            # When lead capture is complete, notify booking agent and create follow-up task
            results["nyra"] = await self.agents["Nyra"].process_event(
                "lead_capture_complete", event_data
            )

            # Only continue if lead capture was successful
            if results["nyra"].get("status") != "error":
                results["solari"] = await self.agents["Solari"].process_event(
                    "new_lead_notification", event_data
                )

                # Create follow-up task
                task_data = {
                    **event_data,
                    "task_template": "lead_followup",
                    "due_date_offset": 1,  # 1 day from now
                }
                results["ruvo"] = await self.agents["Ruvo"].process_event(
                    "create_task", task_data
                )

                # Record workflow in Notion if available
                if self.message_bus and hasattr(self.message_bus, "notion_service"):
                    from models.base import (
                        InstanceStatus,
                    )  # Ensure this import exists or add it at top of file
                    from models.notion_db_models import (
                        WorkflowInstance,
                    )  # Ensure this import exists or add it at top of file

                    # Data from event_data for key_data_payload
                    key_data = {
                        "lead_id": event_data.get("lead_id"),
                        "contact_id": event_data.get("contact_id"),
                        # any other relevant fields from event_data
                    }

                    # Map status string to Enum
                    instance_status_val = InstanceStatus.ACTIVE
                    if notion_data_status := event_data.get(
                        "status", "active"
                    ).upper():  # Using event_data for status
                        if hasattr(InstanceStatus, notion_data_status):
                            instance_status_val = getattr(
                                InstanceStatus, notion_data_status
                            )
                        else:
                            logger.warning(
                                f"Invalid status '{notion_data_status}' for WorkflowInstance, defaulting to ACTIVE."
                            )

                    workflow_instance_data = WorkflowInstance(
                        workflow_id=workflow_id,
                        business_entity=event_data.get("business_entity_id"),
                        current_state=event_data.get(
                            "workflow_type", "lead_capture_initiated"
                        ),  # Using workflow_type from event_data or a default
                        status=instance_status_val,
                        client_lead_name=event_data.get(
                            "lead_name"
                        ),  # Assuming lead_name might be available
                        # Add other relevant fields from event_data if available and mapped
                        # For example, if lead_email is available:
                        client_lead_email=event_data.get("lead_email"),
                        key_data_payload=key_data,
                        source_record_id=event_data.get(
                            "lead_id"
                        ),  # Or a more specific source ID
                    )
                    try:
                        await self.message_bus.notion_service.create_page(
                            workflow_instance_data
                        )
                        logger.info(
                            f"Successfully created WorkflowInstance in Notion for workflow {workflow_id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to create WorkflowInstance in Notion for workflow {workflow_id}: {e}"
                        )

        elif event_type == "workflow_booking_confirmed":
            # When booking is confirmed, create tasks and notify marketing
            results["solari"] = await self.agents["Solari"].process_event(
                "booking_confirmed", event_data
            )

            # Only continue if booking confirmation was successful
            if results["solari"].get("status") != "error":
                # Create confirmation task
                task_data = {
                    **event_data,
                    "task_template": "booking_confirmed",
                    "due_date_offset": 2,  # 2 days from now
                }
                results["ruvo"] = await self.agents["Ruvo"].process_event(
                    "create_task", task_data
                )

                # Notify marketing for follow-up campaign
                campaign_data = {
                    **event_data,
                    "campaign_type": "booking_followup",
                    "delay_days": 1,
                }
                results["liora"] = await self.agents["Liora"].process_event(
                    "campaign_trigger", campaign_data
                )

                # Add to audience segment
                segment_data = {
                    **event_data,
                    "segment_name": "recent_bookings",
                    "contact_id": event_data.get("contact_id"),
                }
                results["zevi"] = await self.agents["Zevi"].process_event(
                    "segment_update", segment_data
                )

        elif event_type == "workflow_content_published":
            # When content is published, distribute and create marketing campaign
            results["elan"] = await self.agents["Elan"].process_event(
                "content_publish", event_data
            )

            # Only continue if content publishing was successful
            if results["elan"].get("status") != "error":
                # Distribute to social media
                results["elan_distribute"] = await self.agents["Elan"].process_event(
                    "distribute_content", event_data
                )

                # Create marketing campaign
                campaign_data = {
                    **event_data,
                    "campaign_type": "content_promotion",
                    "delay_days": 0,
                }
                results["liora"] = await self.agents["Liora"].process_event(
                    "campaign_trigger", campaign_data
                )

                # Analyze target audience
                results["zevi"] = await self.agents["Zevi"].process_event(
                    "audience_analysis",
                    {
                        **event_data,
                        "content_id": event_data.get("content_id"),
                        "analysis_type": "content_audience_match",
                    },
                )

        else:
            # Try to handle dynamically based on the event type
            workflow_type = event_type.replace("workflow_", "")

            # Check if any agent can handle this directly
            for agent_name, agent in self.agents.items():
                if await self._can_agent_handle_event(agent, workflow_type):
                    results[agent_name.lower()] = await agent.process_event(
                        workflow_type, event_data
                    )
                    self.logger.info(
                        f"Workflow {workflow_type} handled by {agent_name}"
                    )
                    break

            # If no agent handled it directly
            if not results:
                self.logger.warning(f"Unhandled workflow event type: {event_type}")
                results["error"] = f"Unhandled workflow event type: {event_type}"
                results["status"] = "error"

        # Add workflow metadata to results
        results["workflow_id"] = workflow_id
        results["workflow_event"] = event_type
        results["timestamp"] = datetime.now().isoformat()

        return results

    async def publish_event_result(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        agent_name: str,
        result: Dict[str, Any],
    ) -> None:
        """
        Publish event results to the message bus for other agents to consume.

        Args:
            event_type: Original event type
            event_data: Original event data
            agent_name: Name of the agent that processed the event
            result: Processing result from the agent
        """
        if not self.message_bus:
            return

        # Create a message for the event result
        message = AgentMessage(
            sender="GraceOrchestrator",
            recipient="all",  # Broadcast to all agents
            message_type=f"event_result.{event_type}",
            payload={
                "original_event": event_type,
                "original_data": event_data,
                "processing_agent": agent_name,
                "result": result,
            },
        )

        # Publish to the message bus
        await self.message_bus.publish(message)

    async def process_message(self, message: AgentMessage) -> None:
        """
        Process a message received from the message bus.

        Args:
            message: The message to process
        """
        # Handle messages directed to the orchestrator
        if message.message_type == "agent_status_update":
            self.logger.info(
                f"Agent status update from {message.sender}: {message.payload.get('status')}"
            )

        elif message.message_type == "workflow_transition_request":
            # Handle workflow transition requests
            workflow_id = message.payload.get("workflow_id")
            transition = message.payload.get("transition")

            if workflow_id and transition:
                self.logger.info(
                    f"Workflow transition request: {workflow_id} -> {transition}"
                )
                # Process the workflow transition (implementation would depend on your workflow engine)

        elif message.message_type.startswith("request_agent_"):
            # Handle requests for specific agent capabilities
            requested_capability = message.message_type.replace("request_agent_", "")

            # Find an agent with the requested capability
            for agent in self.agents.values():
                if (
                    hasattr(agent, "capabilities")
                    and requested_capability in agent.capabilities
                ):
                    # Forward the request to the appropriate agent
                    response_message = AgentMessage(
                        sender="GraceOrchestrator",
                        recipient=agent.name,
                        message_type="capability_request",
                        payload=message.payload,
                        response_to=message.message_id,
                    )

                    await self.message_bus.publish(response_message)
                    break

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of all agents managed by this orchestrator.

        Returns:
            Dict containing health status of all agents
        """
        health_results = {}
        health_check_tasks = []

        # Create tasks to check health of all agents
        for name, agent in self.agents.items():
            if hasattr(agent, "check_health"):
                health_check_tasks.append(self.check_agent_health(name, agent))

        # Run all health checks concurrently
        agent_results = await asyncio.gather(
            *health_check_tasks, return_exceptions=True
        )

        # Process results
        for i, name in enumerate([a for a in self.agents.keys()]):
            if isinstance(agent_results[i], Exception):
                health_results[name] = {
                    "status": "unhealthy",
                    "error": str(agent_results[i]),
                }
            else:
                health_results[name] = agent_results[i]

        # Calculate overall status
        statuses = [r.get("status", "unhealthy") for r in health_results.values()]
        if all(s == "healthy" for s in statuses):
            overall = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall = "unhealthy"
        else:
            overall = "degraded"

        return {
            "status": overall,
            "agents": health_results,
            "timestamp": datetime.now().isoformat(),
        }

    async def check_agent_health(self, name: str, agent: BaseAgent) -> Dict[str, Any]:
        """
        Check health of a specific agent with timeout.

        Args:
            name: Agent name
            agent: Agent instance

        Returns:
            Health check result
        """
        try:
            # Set a timeout for health checks
            health_result = await asyncio.wait_for(agent.check_health(), timeout=5.0)

            # Add agent name to the result
            if isinstance(health_result, dict):
                health_result["agent_name"] = name

            return health_result
        except asyncio.TimeoutError:
            return {
                "status": "unhealthy",
                "agent_name": name,
                "error": "Health check timed out",
            }
        except Exception as e:
            return {"status": "unhealthy", "agent_name": name, "error": str(e)}


# Factory function to create all agent instances
def create_agent_collective(notion_client) -> Dict[str, BaseAgent]:
    """
    Create instances of all agent personalities.

    Args:
        notion_client: The Notion client instance to be used by all agents

    Returns:
        Dictionary mapping agent names to agent instances
    """
    agents = {
        "Nyra": Nyra(notion_client=notion_client),
        "Solari": Solari(notion_client=notion_client),
        "Ruvo": Ruvo(notion_client=notion_client),
        "Liora": Liora(notion_client=notion_client),
        "Sage": Sage(notion_client=notion_client),
        "Elan": Elan(notion_client=notion_client),
        "Zevi": Zevi(notion_client=notion_client),
    }

    return agents


# Create the Grace Fields orchestrator with all agents
def create_grace_orchestrator(notion_client, message_bus=None) -> GraceFields:
    """
    Create the Grace Fields orchestrator with all agent personalities.

    Args:
        notion_client: The Notion client instance to be used by all agents
        message_bus: Optional MessageBus instance for inter-agent communication

    Returns:
        Initialized GraceFields instance
    """
    agent_instances = list(create_agent_collective(notion_client).values())
    return GraceFields(agents=agent_instances, message_bus=message_bus)
