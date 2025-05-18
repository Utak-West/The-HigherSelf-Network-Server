"""
Booking Detection Agent for The HigherSelf Network Server.

This agent is responsible for:
1. Detecting new bookings from Amelia
2. Processing booking data
3. Creating workflow instances in Notion for retreat bookings
4. Tracking the status of bookings through their lifecycle

All operations follow the Pydantic model framework and maintain proper
logging in the Notion workflow instances.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from pydantic import BaseModel, Field, validator

from agents.base_agent import BaseAgent
from models.base import AgentCapability, ApiPlatform
from models.notion_db_models import BusinessEntity, Workflow, WorkflowInstance


class AmeliaBooking(BaseModel):
    """Model for an Amelia booking."""

    booking_id: str
    customer_id: str
    service_id: str
    appointment_id: str
    status: str
    created_at: datetime
    starts_at: datetime
    ends_at: datetime
    customer_info: Dict[str, Any]
    payment_info: Optional[Dict[str, Any]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class BookingAgent(BaseAgent):
    """
    Agent responsible for detecting and processing bookings from Amelia
    and creating workflow instances in Notion.
    """

    def __init__(
        self,
        agent_id: str = "TCP_AGENT_001",
        name: str = "Retreat Booking Detection Agent",
        description: str = "Detects retreat bookings from Amelia and creates workflow instances",
        version: str = "1.0.0",
        business_entities: List[str] = None,
        amelia_api_key: Optional[str] = None,
    ):
        """
        Initialize the Booking Agent.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            version: Agent version
            business_entities: Associated business entities
            amelia_api_key: Optional Amelia API key
        """
        capabilities = [
            AgentCapability.BOOKING_DETECTION,
            AgentCapability.WORKFLOW_MANAGEMENT,
            AgentCapability.CLIENT_COMMUNICATION,
        ]

        apis_utilized = [ApiPlatform.NOTION, ApiPlatform.AMELIA]

        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            version=version,
            capabilities=capabilities,
            apis_utilized=apis_utilized,
            business_entities=business_entities,
        )

        # Set up API credentials
        self.amelia_api_key = amelia_api_key or os.environ.get("AMELIA_API_KEY")
        self.amelia_endpoint = os.environ.get("AMELIA_ENDPOINT")

        self.logger.info("Booking Agent initialized")

    async def _map_retreat_name(self, service_id: str) -> str:
        """
        Map a service ID to a retreat name.
        In a real implementation, this might query a mapping table or API.

        Args:
            service_id: Amelia service ID

        Returns:
            Retreat name
        """
        # This is a simple mock implementation
        # In a real implementation, this would query a database or API
        retreat_mapping = {
            "service_001": "Connection Practice Retreat - Basic",
            "service_002": "Connection Practice Retreat - Advanced",
            "service_003": "7 Space Art Retreat",
            "service_004": "Wellness Integration Weekend",
        }

        return retreat_mapping.get(service_id, f"Unknown Retreat ({service_id})")

    async def _check_for_existing_workflow(
        self, booking_id: str
    ) -> Optional[WorkflowInstance]:
        """
        Check if a workflow instance already exists for this booking.

        Args:
            booking_id: Amelia booking ID

        Returns:
            Existing WorkflowInstance if found, None otherwise
        """
        notion_svc = await self.notion_service

        # Query for existing instances with this booking ID
        filter_conditions = {
            "property": "source_record_id",
            "rich_text": {"equals": booking_id},
        }

        existing_instances = await notion_svc.query_database(
            WorkflowInstance, filter_conditions=filter_conditions
        )

        if existing_instances:
            self.logger.info(f"Found existing workflow for booking ID: {booking_id}")
            return existing_instances[0]

        return None

    async def process_booking(
        self, booking: AmeliaBooking, business_entity_id: str, workflow_id: str
    ) -> Dict[str, Any]:
        """
        Process a booking from Amelia and create a workflow instance.

        Args:
            booking: AmeliaBooking data
            business_entity_id: Business entity ID
            workflow_id: Workflow ID to instantiate

        Returns:
            Processing result
        """
        self.logger.info(f"Processing booking: {booking.booking_id}")

        # Check if workflow already exists
        existing_instance = await self._check_for_existing_workflow(booking.booking_id)

        if existing_instance:
            self.logger.info(
                f"Booking {booking.booking_id} already has a workflow instance"
            )

            # Update the instance with any new information if needed
            await self.log_action(
                workflow_instance=existing_instance,
                action="Received booking update",
                details={
                    "booking_id": booking.booking_id,
                    "status": booking.status,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            return {
                "status": "exists",
                "message": "Booking already has a workflow instance",
                "instance_id": existing_instance.instance_id,
                "workflow_id": existing_instance.workflow_id,
            }

        # Get the workflow to determine initial state
        notion_svc = await self.notion_service

        filter_conditions = {
            "property": "workflow_id",
            "rich_text": {"equals": workflow_id},
        }

        workflows = await notion_svc.query_database(
            Workflow, filter_conditions=filter_conditions, limit=1
        )

        if not workflows:
            raise ValueError(f"Workflow with ID {workflow_id} not found")

        workflow = workflows[0]
        initial_state = workflow.initial_state

        # Get retreat name from service ID
        retreat_name = await self._map_retreat_name(booking.service_id)

        # Extract customer information
        customer_email = booking.customer_info.get("email", "")
        customer_name = f"{booking.customer_info.get('first_name', '')} {booking.customer_info.get('last_name', '')}".strip()
        customer_phone = booking.customer_info.get("phone", "")

        # Create key data payload
        key_data = {
            "booking_id": booking.booking_id,
            "retreat_name": retreat_name,
            "retreat_start": booking.starts_at.isoformat(),
            "retreat_end": booking.ends_at.isoformat(),
            "payment_status": (
                booking.payment_info.get("status", "unknown")
                if booking.payment_info
                else "unknown"
            ),
            "customer_id": booking.customer_id,
            "service_id": booking.service_id,
        }

        # Create the workflow instance
        instance = WorkflowInstance(
            workflow_id=workflow_id,
            business_entity=business_entity_id,
            current_state=initial_state,
            client_lead_email=customer_email,
            client_lead_name=customer_name,
            client_lead_phone=customer_phone,
            source_system="Amelia",
            source_record_id=booking.booking_id,
            key_data_payload=key_data,
        )

        # Add initial history entry
        instance.add_history_entry(
            action=f"[{self.agent_id}] New booking detected from Amelia",
            details={
                "booking_id": booking.booking_id,
                "retreat_name": retreat_name,
                "customer_email": customer_email,
                "starts_at": booking.starts_at.isoformat(),
                "status": booking.status,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Create in Notion
        instance.page_id = await notion_svc.create_page(instance)

        self.logger.info(f"Created workflow instance for booking: {booking.booking_id}")

        return {
            "status": "success",
            "message": "Booking processed and workflow created",
            "instance_id": instance.instance_id,
            "workflow_id": instance.workflow_id,
        }

    async def update_booking_status(
        self,
        booking_id: str,
        new_status: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update the status of a booking in its workflow instance.

        Args:
            booking_id: Amelia booking ID
            new_status: New booking status
            additional_data: Additional data about the status update

        Returns:
            Update result
        """
        # Find the workflow instance for this booking
        existing_instance = await self._check_for_existing_workflow(booking_id)

        if not existing_instance:
            self.logger.error(
                f"No workflow instance found for booking ID: {booking_id}"
            )
            return {
                "status": "error",
                "message": "No workflow instance found for this booking",
            }

        # Determine the workflow state based on the booking status
        # This mapping would be customized based on your workflow
        state_mapping = {
            "pending": "new_booking",
            "approved": "payment_pending",
            "paid": "payment_confirmed",
            "canceled": "canceled",
            "no_show": "canceled",
            "rejected": "canceled",
        }

        new_workflow_state = state_mapping.get(new_status.lower())

        if not new_workflow_state:
            self.logger.warning(
                f"Unknown booking status: {new_status}, staying in current state"
            )
            new_workflow_state = existing_instance.current_state

        # Update the workflow instance
        action_description = f"Booking status updated to {new_status}"
        details = additional_data or {}
        details["booking_status"] = new_status
        details["timestamp"] = datetime.now().isoformat()

        # Only update the state if it's different
        if new_workflow_state != existing_instance.current_state:
            success = await self.update_workflow_state(
                workflow_instance=existing_instance,
                new_state=new_workflow_state,
                action_description=action_description,
                details=details,
            )
        else:
            # Just log the action if the state isn't changing
            success = await self.log_action(
                workflow_instance=existing_instance,
                action=action_description,
                details=details,
            )

        if success:
            return {
                "status": "success",
                "message": f"Booking status updated to {new_status}",
                "instance_id": existing_instance.instance_id,
                "new_state": new_workflow_state,
            }
        else:
            return {"status": "error", "message": "Failed to update booking status"}

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
        if event_type == "new_booking":
            # Process a new booking from Amelia
            booking_data = event_data.get("booking", {})

            # Convert to AmeliaBooking model
            booking = AmeliaBooking(
                booking_id=booking_data.get("booking_id"),
                customer_id=booking_data.get("customer_id"),
                service_id=booking_data.get("service_id"),
                appointment_id=booking_data.get("appointment_id"),
                status=booking_data.get("status"),
                created_at=datetime.fromisoformat(booking_data.get("created_at")),
                starts_at=datetime.fromisoformat(booking_data.get("starts_at")),
                ends_at=datetime.fromisoformat(booking_data.get("ends_at")),
                customer_info=booking_data.get("customer_info", {}),
                payment_info=booking_data.get("payment_info"),
                custom_fields=booking_data.get("custom_fields"),
            )

            return await self.process_booking(
                booking=booking,
                business_entity_id=event_data.get("business_entity_id"),
                workflow_id=event_data.get("workflow_id"),
            )

        elif event_type == "booking_status_update":
            # Update booking status
            return await self.update_booking_status(
                booking_id=event_data.get("booking_id"),
                new_status=event_data.get("status"),
                additional_data=event_data.get("additional_data"),
            )

        else:
            return {
                "status": "error",
                "message": f"Unsupported event type: {event_type}",
            }

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.

        Returns:
            Health check result
        """
        health_checks = {"notion_api": False, "amelia_api": False}

        # Check Notion API
        try:
            notion_svc = await self.notion_service
            # Try to query a database to verify connection
            await notion_svc.query_database(WorkflowInstance, limit=1)
            health_checks["notion_api"] = True
        except Exception as e:
            self.logger.error(f"Notion API health check failed: {e}")

        # Check Amelia API (mock check for now)
        if self.amelia_api_key and self.amelia_endpoint:
            health_checks["amelia_api"] = True

        return {
            "agent_id": self.agent_id,
            "status": "healthy" if all(health_checks.values()) else "degraded",
            "checks": health_checks,
            "timestamp": datetime.now().isoformat(),
        }
