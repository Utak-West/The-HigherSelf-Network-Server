#!/usr/bin/env python3
"""
Enhanced Agent Workflow Example for The HigherSelf Network Server.

This example demonstrates how to use the enhanced agent system with multi-agent workflows
to automate complex business processes across your art gallery, wellness center, and
consultancy businesses.
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

from loguru import logger
from dotenv import load_dotenv

from services.notion_service import NotionService
from utils.message_bus import MessageBus, AgentMessage
from agents import (
    Nyra, Solari, Ruvo, Liora, Sage, Elan, Zevi,
    create_grace_orchestrator
)


async def run_lead_to_booking_workflow():
    """
    Demonstrate a complete lead-to-booking workflow using the enhanced agent system.
    
    This workflow shows how a lead captured by Nyra can be automatically processed
    through multiple stages, involving several agents working together through
    the message bus and Grace orchestration.
    """
    # Initialize services
    load_dotenv()
    notion_service = NotionService.from_env()
    message_bus = MessageBus(notion_service)
    
    logger.info("Initializing enhanced agent workflow example...")
    
    # Initialize agents
    nyra = Nyra(notion_client=notion_service)
    solari = Solari(notion_client=notion_service)
    ruvo = Ruvo(notion_client=notion_service)
    liora = Liora(notion_client=notion_service)
    
    # Create enhanced Grace orchestrator with message bus
    grace = create_grace_orchestrator(notion_service, message_bus)
    
    # Subscribe to message bus for monitoring
    message_bus.subscribe("workflow_monitor", log_message)
    
    # 1. Simulate a new lead from a website form
    lead_data = {
        "source": "website_form",
        "form_id": "contact_form",
        "business_entity_id": "the_connection_practice",
        "form_data": {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone": "+1-555-123-4567",
            "interest": "Wellness Retreat",
            "message": "I'm interested in your upcoming wellness retreat. Please send me more information."
        },
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info("Starting lead-to-booking workflow with enhanced agent orchestration")
    
    # 2. Process the lead with Nyra through Grace orchestrator
    lead_result = await grace.route_event("website_form", lead_data)
    logger.info(f"Lead processed by Nyra: {lead_result.get('nyra', {}).get('status')}")
    
    # The lead processing will trigger a message on the bus that other agents can react to
    await asyncio.sleep(1)  # Give time for message processing
    
    # 3. Simulate Ruvo creating a follow-up task based on the new lead
    # This would normally happen automatically through the message bus
    task_data = {
        "task_template": "new_lead_followup",
        "contact_id": lead_result.get("nyra", {}).get("contact_id", "sample-contact-id"),
        "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "priority": "high",
        "assignee": "sales_team"
    }
    
    task_result = await grace.route_event("create_task", task_data)
    logger.info(f"Follow-up task created by Ruvo: {task_result.get('ruvo', {}).get('status')}")
    
    # 4. Simulate the lead converting to a booking
    booking_data = {
        "type": "retreat_booking",
        "contact_id": lead_result.get("nyra", {}).get("contact_id", "sample-contact-id"),
        "product_id": "wellness_retreat_june",
        "booking_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "amount": 1200.00,
        "status": "confirmed",
        "notes": "Converted from website inquiry"
    }
    
    booking_result = await grace.route_event("booking_created", booking_data)
    logger.info(f"Booking processed by Solari: {booking_result.get('solari', {}).get('status')}")
    
    # 5. This will trigger a multi-agent workflow through Grace
    workflow_data = {
        "workflow_id": "booking_confirmation_workflow",
        "contact_id": lead_result.get("nyra", {}).get("contact_id", "sample-contact-id"),
        "booking_id": booking_result.get("solari", {}).get("booking_id", "sample-booking-id"),
        "business_entity_id": "the_connection_practice"
    }
    
    # Trigger the multi-agent workflow
    workflow_result = await grace.route_event("workflow_booking_confirmed", workflow_data)
    logger.info("Multi-agent workflow triggered for booking confirmation")
    
    # Print the results from each agent
    for agent, result in workflow_result.items():
        if agent != "error":
            logger.info(f"{agent.capitalize()} result: {result.get('status')}")
    
    # 6. Check the health of all agents
    health_status = await grace.check_health()
    logger.info(f"System health: {health_status.get('status')}")
    
    logger.info("Enhanced agent workflow example completed successfully")
    return {
        "lead_result": lead_result,
        "task_result": task_result,
        "booking_result": booking_result,
        "workflow_result": workflow_result,
        "health_status": health_status
    }


async def log_message(message: AgentMessage):
    """Log messages from the message bus for monitoring."""
    logger.info(f"Message Bus: {message.message_type} from {message.sender} to {message.recipient}")


if __name__ == "__main__":
    # Run the example workflow
    asyncio.run(run_lead_to_booking_workflow())
