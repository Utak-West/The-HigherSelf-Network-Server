"""
The HigherSelf Network Server - Agent Personality System

This module implements the named agent personalities that bring character
and intentionality to automated processes within The HigherSelf Network Server.
Each agent has a distinct name, tone, and specialized role while maintaining
Notion as the central hub.
"""

from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

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
        description = "Intuitive & responsive agent that captures leads from various sources"
        super().__init__(
            agent_id=agent_id,
            name="Nyra",
            description=description,
            notion_service=notion_client,
            **kwargs
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
        self.logger.info(f"Nyra processing lead capture event: {event_data.get('source', 'unknown')}")

        # Fetch leads from Typeform, Snov.io, etc.
        # Create/update Contact & Business Entity records in Notion

        # Implementation will be added based on existing LeadCaptureAgent logic

        return {"status": "processed", "message": "Lead captured successfully"}

    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
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
            "new_lead": self.run
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Nyra: {event_type}")
            return {"status": "error", "message": f"Unsupported event type: {event_type}"}

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
                    "notion_connected": True
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e)
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
        description = "Clear & luminous agent that processes retreat bookings and orders"
        super().__init__(
            agent_id=agent_id,
            name="Solari",
            description=description,
            notion_service=notion_client,
            **kwargs
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
        self.logger.info(f"Solari processing booking/order event: {event_data.get('type', 'unknown')}")

        # Sync booking data from Amelia/WooCommerce
        # Create Workflow Instances & link to Products/Contacts

        # Implementation will be added based on existing BookingAgent logic

        return {"status": "processed", "message": "Booking/order processed successfully"}

    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
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
            "booking_created": self.run
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Solari: {event_type}")
            return {"status": "error", "message": f"Unsupported event type: {event_type}"}

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
                    "notion_connected": True
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e)
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
        description = "Grounded & task-driven agent that creates, assigns, and tracks tasks"
        super().__init__(
            agent_id=agent_id,
            name="Ruvo",
            description=description,
            notion_service=notion_client,
            **kwargs
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
        self.logger.info(f"Ruvo processing task event: {event_data.get('trigger', 'unknown')}")

        # Monitor Workflow status changes
        # Generate tasks using templates; update Master Tasks DB

        # Implementation will be added based on existing TaskManagementAgent logic

        return {"status": "processed", "message": "Tasks created successfully"}

    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
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
            "task_needed": self.run
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Ruvo: {event_type}")
            return {"status": "error", "message": f"Unsupported event type: {event_type}"}

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
                    "notion_connected": True
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e)
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
            **kwargs
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
        self.logger.info(f"Liora processing marketing campaign event: {event_data.get('campaign_type', 'unknown')}")

        # Read marketing strategies from Notion
        # Send campaign triggers to Beehiiv; log results

        # Implementation will be added based on existing MarketingCampaignAgent logic

        return {"status": "processed", "message": "Campaign processed successfully"}

    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
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
            "newsletter_metrics": self.run
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Liora: {event_type}")
            return {"status": "error", "message": f"Unsupported event type: {event_type}"}

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
                    "notion_connected": True
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e)
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
        description = "Warm & connected agent that handles community member interactions"
        super().__init__(
            agent_id=agent_id,
            name="Sage",
            description=description,
            notion_service=notion_client,
            **kwargs
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
        self.logger.info(f"Sage processing community event: {event_data.get('event_type', 'unknown')}")

        # Track activity in Circle.so
        # Update Community Hub DB and member profile engagement

        # Implementation will be added based on existing CommunityEngagementAgent logic

        return {"status": "processed", "message": "Community event processed successfully"}

    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
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
            "member_engagement": self.run
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Sage: {event_type}")
            return {"status": "error", "message": f"Unsupported event type: {event_type}"}

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
                    "notion_connected": True
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e)
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
            **kwargs
        )
        self.agent_type = "ContentLifecycleAgent"
        self.tone = "Creative & adaptive"

    async def run(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage content lifecycle from idea generation to distribution across platforms,
        tracking content performance metrics.

        Args:
            event_data: Content event data (idea submission, stage change, etc.)

        Returns:
            Dict containing processing results and content item IDs
        """
        self.logger.info(f"Elan processing content event: {event_data.get('content_type', 'unknown')}")

        # Pull content ideas, schedule posts
        # Update lifecycle stages across Notion + distribute

        # Implementation will be added based on existing ContentLifecycleAgent logic

        return {"status": "processed", "message": "Content processed successfully"}

    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
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
            "distribute_content": self.run
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Elan: {event_type}")
            return {"status": "error", "message": f"Unsupported event type: {event_type}"}

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
                    "notion_connected": True
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e)
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
        description = "Analytical & sharp agent that analyzes customer data for segmentation"
        super().__init__(
            agent_id=agent_id,
            name="Zevi",
            description=description,
            notion_service=notion_client,
            **kwargs
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
        self.logger.info(f"Zevi processing audience segmentation event: {event_data.get('analysis_type', 'unknown')}")

        # Analyze customer data, generate audience tags
        # Link results to Campaigns, Community Hub

        # Implementation will be added based on existing AudienceSegmentationAgent logic

        return {"status": "processed", "message": "Audience analysis completed successfully"}

    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
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
            "analyze_audience": self.run
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for Zevi: {event_type}")
            return {"status": "error", "message": f"Unsupported event type: {event_type}"}

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
                    "notion_connected": True
                }
            else:
                return {
                    "status": "degraded",
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "notion_connected": False,
                    "message": "Notion service not available"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "error": str(e)
            }


class GraceOrchestrator:
    """
    Grace Fields - System Orchestrator

    The orchestration layer that routes events to the appropriate agent personality
    and maintains system coordination across The HigherSelf Network Server.

    Grace ensures that each agent is activated at the right time, maintaining
    the flow of information and actions throughout the system.
    """

    def __init__(self, agents: List[BaseAgent]):
        """
        Initialize the orchestrator with a list of agent instances.

        Args:
            agents: List of agent instances to be managed by this orchestrator
        """
        self.agents = {agent.name: agent for agent in agents}
        self.logger = None  # Will be initialized with a proper logger

    async def route_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route an event to the appropriate agent(s) based on the event type.

        Args:
            event_type: Type of event to route
            event_data: Data associated with the event

        Returns:
            Dict containing processing results from the agent(s)
        """
        results = {}

        if event_type == "new_lead":
            results["nyra"] = await self.agents["Nyra"].run(event_data)
        elif event_type == "booking_created" or event_type == "order_created":
            results["solari"] = await self.agents["Solari"].run(event_data)
        elif event_type == "workflow_status_changed" or event_type == "task_needed":
            results["ruvo"] = await self.agents["Ruvo"].run(event_data)
        elif event_type == "content_ready" or event_type == "content_stage_change":
            results["elan"] = await self.agents["Elan"].run(event_data)
        elif event_type == "community_event" or event_type == "member_activity":
            results["sage"] = await self.agents["Sage"].run(event_data)
        elif event_type == "audience_analysis" or event_type == "segment_update":
            results["zevi"] = await self.agents["Zevi"].run(event_data)
        elif event_type == "campaign_trigger" or event_type == "campaign_metrics":
            results["liora"] = await self.agents["Liora"].run(event_data)
        else:
            # Log unhandled event type
            if self.logger:
                self.logger.warning(f"No agent available for event type: {event_type}")
            results["error"] = f"No agent available for event type: {event_type}"

        return results


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
def create_grace_orchestrator(notion_client) -> GraceOrchestrator:
    """
    Create the Grace Fields orchestrator with all agent personalities.

    Args:
        notion_client: The Notion client instance to be used by all agents

    Returns:
        Initialized GraceOrchestrator instance
    """
    agent_instances = list(create_agent_collective(notion_client).values())
    return GraceOrchestrator(agents=agent_instances)
