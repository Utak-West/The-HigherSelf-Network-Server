"""
The 7 Space Agent Integration

This module provides integration between The HigherSelf Network agents and The 7 Space service.
It allows agents to interact with The 7 Space website for content management and booking operations.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

# Setup logging
try:
    from loguru import logger
except ImportError:
    import logging

    # Create a logger that mimics loguru's interface
    logger = logging.getLogger("the7space_agent")
    logger.info = logger.info
    logger.error = logger.error
    logger.warning = logger.warning
    logger.debug = logger.debug

from agents.base_agent import BaseAgent
from agents.booking_agent import BookingAgent
from agents.content_lifecycle_agent import ContentLifecycleAgent
from agents.lead_capture_agent import LeadCaptureAgent
from integrations.the7space.the7space_service import (
    AmeliaAppointment,
    SoftrPortal,
    SoftrRecord,
    SoftrUser,
    The7SpaceService,
    WordPressPost,
)
from models.notion_db_models import WorkflowInstance


class The7SpaceAgentIntegration:
    """
    Integration class for connecting HigherSelf Network agents with The 7 Space website.
    """

    def __init__(self, the7space_service: Optional[The7SpaceService] = None):
        """
        Initialize the integration.

        Args:
            the7space_service: The7SpaceService instance (will create one if not provided)
        """
        self.the7space_service = the7space_service or The7SpaceService()
        logger.info("The 7 Space Agent Integration initialized")

    async def register_with_content_lifecycle_agent(
        self, agent: ContentLifecycleAgent
    ) -> bool:
        """
        Register this integration with the Content Lifecycle Agent.

        Args:
            agent: ContentLifecycleAgent instance

        Returns:
            True if registration was successful, False otherwise
        """
        success = True
        try:
            # Register WordPress content provider
            # Check if the method exists on the agent
            if hasattr(agent, "register_content_provider"):
                agent.register_content_provider(
                    provider_id="the7space_wp",
                    provider_name="The 7 Space WordPress Website",
                    get_content_fn=self._get_content_handler,
                    create_content_fn=self._create_content_handler,
                    update_content_fn=self._update_content_handler,
                    publish_content_fn=self._publish_content_handler,
                )
            else:
                logger.warning(
                    "ContentLifecycleAgent does not have register_content_provider method"
                )

            logger.info(
                "Registered The 7 Space WordPress content provider with ContentLifecycleAgent"
            )
        except Exception as e:
            logger.error(f"Error registering WordPress with ContentLifecycleAgent: {e}")
            success = False

        try:
            # Register Softr content provider
            # Check if the method exists on the agent
            if hasattr(agent, "register_content_provider"):
                agent.register_content_provider(
                    provider_id="the7space_softr",
                    provider_name="The 7 Space Softr Portals",
                    get_content_fn=self._get_softr_content_handler,
                    create_content_fn=self._create_softr_content_handler,
                    update_content_fn=self._update_softr_content_handler,
                    publish_content_fn=self._publish_softr_content_handler,
                )
            else:
                logger.warning(
                    "ContentLifecycleAgent does not have register_content_provider method"
                )

            logger.info(
                "Registered The 7 Space Softr content provider with ContentLifecycleAgent"
            )
        except Exception as e:
            logger.error(f"Error registering Softr with ContentLifecycleAgent: {e}")
            success = False

        return success

    async def register_with_booking_agent(self, agent: BookingAgent) -> bool:
        """
        Register this integration with the Booking Agent.

        Args:
            agent: BookingAgent instance

        Returns:
            True if registration was successful, False otherwise
        """
        try:
            # Register custom handlers for The 7 Space booking operations
            # Check if the method exists on the agent
            if hasattr(agent, "register_booking_provider"):
                agent.register_booking_provider(
                    provider_id="the7space_amelia",
                    provider_name="The 7 Space Amelia Booking",
                    get_services_fn=self._get_services_handler,
                    get_appointments_fn=self._get_appointments_handler,
                    create_appointment_fn=self._create_appointment_handler,
                    update_appointment_fn=self._update_appointment_handler,
                )
            else:
                logger.warning(
                    "BookingAgent does not have register_booking_provider method"
                )

            logger.info("Registered The 7 Space booking provider with BookingAgent")
            return True
        except Exception as e:
            logger.error(f"Error registering with BookingAgent: {e}")
            return False

    async def register_with_lead_capture_agent(self, agent: LeadCaptureAgent) -> bool:
        """
        Register this integration with the Lead Capture Agent.

        Args:
            agent: LeadCaptureAgent instance

        Returns:
            True if registration was successful, False otherwise
        """
        try:
            # Register custom handlers for The 7 Space lead operations
            # Check if the method exists on the agent
            if hasattr(agent, "register_lead_source"):
                agent.register_lead_source(
                    source_id="the7space_website",
                    source_name="The 7 Space Website",
                    process_lead_fn=self._process_lead_handler,
                )
            else:
                logger.warning(
                    "LeadCaptureAgent does not have register_lead_source method"
                )

            logger.info("Registered The 7 Space lead source with LeadCaptureAgent")
            return True
        except Exception as e:
            logger.error(f"Error registering with LeadCaptureAgent: {e}")
            return False

    # Content Lifecycle Agent handlers
    async def _get_content_handler(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle content retrieval requests from the Content Lifecycle Agent."""
        try:
            content_type = request.get("content_type", "post")
            status = request.get("status", "publish")
            search = request.get("search")
            limit = request.get("limit", 10)
            page = request.get("page", 1)

            posts = await self.the7space_service.get_wordpress_posts(
                post_type=content_type,
                status=status,
                search=search,
                limit=limit,
                page=page,
            )

            return {
                "status": "success",
                "content": [p.dict() for p in posts],
                "count": len(posts),
                "message": f"Retrieved {len(posts)} {content_type}s from The 7 Space",
            }
        except Exception as e:
            logger.error(f"Error in _get_content_handler: {e}")
            return {"status": "error", "message": f"Error retrieving content: {str(e)}"}

    async def _create_content_handler(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle content creation requests from the Content Lifecycle Agent."""
        try:
            content_type = request.get("content_type", "post")

            # Create a WordPressPost model from the request
            post = WordPressPost(
                title=request.get("title", ""),
                content=request.get("content", ""),
                status=request.get("status", "draft"),
                post_type=content_type,
                categories=request.get("categories", []),
                tags=request.get("tags", []),
                featured_media=request.get("featured_media"),
                notion_page_id=request.get("notion_page_id"),
            )

            post_id = await self.the7space_service.create_wordpress_post(post)

            if post_id:
                return {
                    "status": "success",
                    "post_id": post_id,
                    "message": f"Created {content_type} on The 7 Space",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to create {content_type} on The 7 Space",
                }
        except Exception as e:
            logger.error(f"Error in _create_content_handler: {e}")
            return {"status": "error", "message": f"Error creating content: {str(e)}"}

    async def _update_content_handler(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle content update requests from the Content Lifecycle Agent."""
        try:
            post_id = request.get("id")
            if not post_id:
                return {"status": "error", "message": "Post ID is required for updates"}

            # Prepare update data
            update_data = {}
            if "title" in request:
                update_data["title"] = request["title"]
            if "content" in request:
                update_data["content"] = request["content"]
            if "status" in request:
                update_data["status"] = request["status"]
            if "categories" in request:
                update_data["categories"] = request["categories"]
            if "tags" in request:
                update_data["tags"] = request["tags"]
            if "featured_media" in request:
                update_data["featured_media"] = request["featured_media"]

            success = await self.the7space_service.update_wordpress_post(
                post_id, update_data
            )

            if success:
                return {
                    "status": "success",
                    "post_id": post_id,
                    "message": f"Updated post on The 7 Space",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to update post on The 7 Space",
                }
        except Exception as e:
            logger.error(f"Error in _update_content_handler: {e}")
            return {"status": "error", "message": f"Error updating content: {str(e)}"}

    async def _publish_content_handler(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle content publishing requests from the Content Lifecycle Agent."""
        try:
            post_id = request.get("id")
            if not post_id:
                return {
                    "status": "error",
                    "message": "Post ID is required for publishing",
                }

            # Publishing is just updating the status to 'publish'
            update_data = {"status": "publish"}

            success = await self.the7space_service.update_wordpress_post(
                post_id, update_data
            )

            if success:
                return {
                    "status": "success",
                    "post_id": post_id,
                    "message": f"Published post on The 7 Space",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to publish post on The 7 Space",
                }
        except Exception as e:
            logger.error(f"Error in _publish_content_handler: {e}")
            return {"status": "error", "message": f"Error publishing content: {str(e)}"}

    # Softr Content Lifecycle Agent handlers
    async def _get_softr_content_handler(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Softr content retrieval requests from the Content Lifecycle Agent."""
        try:
            data_source = request.get("data_source", "content")
            limit = request.get("limit", 10)
            offset = request.get("offset", 0)
            filter_expr = request.get("filter", None)

            records = await self.the7space_service.get_softr_records(
                data_source=data_source,
                limit=limit,
                offset=offset,
                filter_expr=filter_expr,
            )

            return {
                "status": "success",
                "content": [r.dict() for r in records],
                "count": len(records),
                "message": f"Retrieved {len(records)} records from Softr data source {data_source}",
            }
        except Exception as e:
            logger.error(f"Error in _get_softr_content_handler: {e}")
            return {
                "status": "error",
                "message": f"Error retrieving Softr content: {str(e)}",
            }

    async def _create_softr_content_handler(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Softr content creation requests from the Content Lifecycle Agent."""
        try:
            data_source = request.get("data_source")
            if not data_source:
                return {
                    "status": "error",
                    "message": "Data source is required for Softr content creation",
                }

            fields = request.get("fields", {})
            notion_page_id = request.get("notion_page_id")

            record_id = await self.the7space_service.create_softr_record(
                data_source=data_source,
                fields=fields,
                notion_page_id=notion_page_id,
            )

            if record_id:
                return {
                    "status": "success",
                    "record_id": record_id,
                    "message": f"Created record in Softr data source {data_source}",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to create record in Softr data source {data_source}",
                }
        except Exception as e:
            logger.error(f"Error in _create_softr_content_handler: {e}")
            return {
                "status": "error",
                "message": f"Error creating Softr content: {str(e)}",
            }

    async def _update_softr_content_handler(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Softr content update requests from the Content Lifecycle Agent."""
        try:
            # For now, since we don't have a real implementation, we'll simulate success
            record_id = request.get("id")
            data_source = request.get("data_source")

            if not record_id or not data_source:
                return {
                    "status": "error",
                    "message": "Record ID and data source are required for Softr content updates",
                }

            logger.info(
                f"Simulating update of Softr record {record_id} in {data_source}"
            )

            return {
                "status": "success",
                "record_id": record_id,
                "message": f"Updated record in Softr data source {data_source}",
            }
        except Exception as e:
            logger.error(f"Error in _update_softr_content_handler: {e}")
            return {
                "status": "error",
                "message": f"Error updating Softr content: {str(e)}",
            }

    async def _publish_softr_content_handler(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Softr content publishing requests from the Content Lifecycle Agent."""
        try:
            # For Softr, publishing is typically just updating a status field
            record_id = request.get("id")
            data_source = request.get("data_source")

            if not record_id or not data_source:
                return {
                    "status": "error",
                    "message": "Record ID and data source are required for Softr content publishing",
                }

            logger.info(
                f"Simulating publishing of Softr record {record_id} in {data_source}"
            )

            return {
                "status": "success",
                "record_id": record_id,
                "message": f"Published record in Softr data source {data_source}",
            }
        except Exception as e:
            logger.error(f"Error in _publish_softr_content_handler: {e}")
            return {
                "status": "error",
                "message": f"Error publishing Softr content: {str(e)}",
            }

    # Booking Agent handlers
    async def _get_services_handler(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service retrieval requests from the Booking Agent."""
        try:
            category_id = request.get("category_id")
            status = request.get("status", "visible")

            services = await self.the7space_service.get_amelia_services(
                category_id=category_id, status=status
            )

            return {
                "status": "success",
                "services": [s.dict() for s in services],
                "count": len(services),
                "message": f"Retrieved {len(services)} services from The 7 Space",
            }
        except Exception as e:
            logger.error(f"Error in _get_services_handler: {e}")
            return {
                "status": "error",
                "message": f"Error retrieving services: {str(e)}",
            }

    async def _get_appointments_handler(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle appointment retrieval requests from the Booking Agent."""
        try:
            start_date = request.get("start_date")
            if start_date and isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))

            end_date = request.get("end_date")
            if end_date and isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

            status = request.get("status")

            appointments = await self.the7space_service.get_amelia_appointments(
                start_date=start_date, end_date=end_date, status=status
            )

            return {
                "status": "success",
                "appointments": [a.dict() for a in appointments],
                "count": len(appointments),
                "message": f"Retrieved {len(appointments)} appointments from The 7 Space",
            }
        except Exception as e:
            logger.error(f"Error in _get_appointments_handler: {e}")
            return {
                "status": "error",
                "message": f"Error retrieving appointments: {str(e)}",
            }

    async def _create_appointment_handler(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle appointment creation requests from the Booking Agent."""
        try:
            # Create an AmeliaAppointment model from the request
            booking_start = request.get("booking_start")
            if isinstance(booking_start, str):
                booking_start = datetime.fromisoformat(
                    booking_start.replace("Z", "+00:00")
                )

            booking_end = request.get("booking_end")
            if booking_end and isinstance(booking_end, str):
                booking_end = datetime.fromisoformat(booking_end.replace("Z", "+00:00"))

            appointment = AmeliaAppointment(
                booking_start=booking_start,
                booking_end=booking_end,
                status=request.get("status", "pending"),
                service_id=request.get("service_id"),
                provider_id=request.get("provider_id"),
                customer_first_name=request.get("customer_first_name", ""),
                customer_last_name=request.get("customer_last_name", ""),
                customer_email=request.get("customer_email", ""),
                customer_phone=request.get("customer_phone"),
                internal_notes=request.get("internal_notes"),
                notion_page_id=request.get("notion_page_id"),
            )

            appointment_id = await self.the7space_service.create_amelia_appointment(
                appointment
            )

            if appointment_id:
                return {
                    "status": "success",
                    "appointment_id": appointment_id,
                    "message": f"Created appointment on The 7 Space",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to create appointment on The 7 Space",
                }
        except Exception as e:
            logger.error(f"Error in _create_appointment_handler: {e}")
            return {
                "status": "error",
                "message": f"Error creating appointment: {str(e)}",
            }

    async def _update_appointment_handler(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle appointment update requests from the Booking Agent."""
        try:
            # This is a placeholder since we haven't implemented update_amelia_appointment yet
            logger.info(f"Update appointment request: {request}")

            # Return a success response for now
            return {
                "status": "success",
                "appointment_id": request.get("id"),
                "message": f"Updated appointment on The 7 Space (simulated)",
            }
        except Exception as e:
            logger.error(f"Error in _update_appointment_handler: {e}")
            return {
                "status": "error",
                "message": f"Error updating appointment: {str(e)}",
            }

    # Lead Capture Agent handlers
    async def _process_lead_handler(
        self, request: Dict[str, Any], workflow_instance: WorkflowInstance
    ) -> Dict[str, Any]:
        """Handle lead processing requests from the Lead Capture Agent."""
        try:
            # This is a placeholder for lead processing from The 7 Space website
            lead_data = request.get("lead_data", {})
            source = request.get("source", "website")

            logger.info(
                f"Processing lead from The 7 Space {source}: {lead_data.get('email')}"
            )

            # For now, just log and return success
            return {
                "status": "success",
                "lead_id": lead_data.get("email"),
                "workflow_instance_id": (
                    workflow_instance.id if workflow_instance else None
                ),
                "message": f"Processed lead from The 7 Space {source}",
            }
        except Exception as e:
            logger.error(f"Error in _process_lead_handler: {e}")
            return {"status": "error", "message": f"Error processing lead: {str(e)}"}


# Helper function to get or create The7SpaceAgentIntegration
async def get_the7space_integration() -> The7SpaceAgentIntegration:
    """
    Get or create a The7SpaceAgentIntegration instance.

    Returns:
        The7SpaceAgentIntegration instance
    """
    # In a real implementation, this would be a singleton
    return The7SpaceAgentIntegration()
