#!/usr/bin/env python3
"""
Grace Fields Orchestrator Demo

This example demonstrates how to use the enhanced Grace Fields orchestrator
to coordinate complex workflows across multiple agents in The HigherSelf Network Server.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

from dotenv import load_dotenv
from loguru import logger

from agents import (
    Elan,
    Liora,
    Nyra,
    Ruvo,
    Sage,
    Solari,
    Zevi,
    create_grace_orchestrator,
)
from models.base import AgentCapability
from services.notion_service import NotionService
from utils.message_bus import AgentMessage, MessageBus


async def setup_grace_fields():
    """Initialize Grace Fields with all agents and message bus."""
    # Load environment variables
    load_dotenv()

    # Initialize Notion service
    notion_service = NotionService.from_env()

    # Create message bus for inter-agent communication
    message_bus = MessageBus(notion_service)

    # Initialize all agent personalities
    nyra = Nyra(notion_client=notion_service)
    solari = Solari(notion_client=notion_service)
    ruvo = Ruvo(notion_client=notion_service)
    liora = Liora(notion_client=notion_service)
    sage = Sage(notion_client=notion_service)
    elan = Elan(notion_client=notion_service)
    zevi = Zevi(notion_client=notion_service)

    # Create enhanced Grace Fields orchestrator
    grace = create_grace_orchestrator(notion_service, message_bus)

    # Subscribe all agents to the message bus
    for agent_id, agent in {
        "nyra": nyra,
        "solari": solari,
        "ruvo": ruvo,
        "liora": liora,
        "sage": sage,
        "elan": elan,
        "zevi": zevi,
        "grace": grace,
    }.items():
        if hasattr(agent, "process_message"):
            message_bus.subscribe(agent_id, agent.process_message)

    # Add a monitor to log all messages
    message_bus.subscribe("monitor", log_message)

    logger.info(
        "✨ Grace Fields orchestration system initialized with enhanced capabilities"
    )

    return grace, message_bus


async def demo_lead_to_booking_workflow(grace):
    """Demonstrate the lead capture to booking workflow."""
    logger.info("🌟 Starting Lead-to-Booking Workflow Demo")

    # Simulate a new lead from a website form
    lead_data = {
        "source": "website_form",
        "form_id": "contact_form",
        "business_entity_id": "the_connection_practice",
        "form_data": {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone": "+1-555-123-4567",
            "interest": "Wellness Retreat",
            "message": "I'm interested in your upcoming wellness retreat. Please send me more information.",
        },
        "timestamp": datetime.now().isoformat(),
    }

    # Start the workflow using the pattern
    result = await grace.route_event("workflow_pattern_lead_to_booking", lead_data)

    logger.info(f"Workflow started: {result.get('status')}")
    logger.info(f"Workflow ID: {result.get('workflow_id')}")

    # Wait for the workflow to progress
    await asyncio.sleep(2)

    # Check the workflow status
    workflow_id = result.get("workflow_id")
    if workflow_id in grace.active_workflows:
        workflow = grace.active_workflows[workflow_id]
        logger.info(f"Workflow status: {workflow['status']}")
        logger.info(f"Steps completed: {workflow['steps_completed']}")

    return result


async def demo_content_lifecycle_workflow(grace):
    """Demonstrate the content lifecycle workflow."""
    logger.info("📝 Starting Content Lifecycle Workflow Demo")

    # Simulate a new content idea
    content_data = {
        "content_type": "blog_post",
        "business_entity_id": "the_7_space",
        "title": "Mindfulness Practices for Creative Professionals",
        "description": "A guide to incorporating mindfulness into creative work",
        "target_audience": "artists, designers, writers",
        "keywords": ["mindfulness", "creativity", "focus", "productivity"],
        "timestamp": datetime.now().isoformat(),
    }

    # Start the workflow using the pattern
    result = await grace.route_event("workflow_pattern_content_lifecycle", content_data)

    logger.info(f"Workflow started: {result.get('status')}")
    logger.info(f"Workflow ID: {result.get('workflow_id')}")

    # Wait for the workflow to progress
    await asyncio.sleep(2)

    # Check the workflow status
    workflow_id = result.get("workflow_id")
    if workflow_id in grace.active_workflows:
        workflow = grace.active_workflows[workflow_id]
        logger.info(f"Workflow status: {workflow['status']}")
        logger.info(f"Steps completed: {workflow['steps_completed']}")

    return result


async def demo_dynamic_routing(grace):
    """Demonstrate Grace's dynamic routing capabilities."""
    logger.info("🧭 Starting Dynamic Routing Demo")

    # Event with no explicit mapping
    event_data = {
        "business_entity_id": "the_connection_practice",
        "contact_id": "contact_12345",
        "event_details": "Customer requested information about upcoming events",
        "timestamp": datetime.now().isoformat(),
    }

    # Route an event with pattern-based routing
    result1 = await grace.route_event("contact_information_request", event_data)
    logger.info(f"Pattern-based routing result: {result1}")

    # Route an event with capability-based routing
    capability_data = {
        **event_data,
        "required_capability": AgentCapability.CONTENT_CREATION,
    }
    result2 = await grace.route_event("generate_newsletter_content", capability_data)
    logger.info(f"Capability-based routing result: {result2}")

    # Route an event with business entity routing
    entity_data = {**event_data, "business_entity_id": "the_7_space"}
    result3 = await grace.route_event("member_welcome", entity_data)
    logger.info(f"Business entity routing result: {result3}")

    return {
        "pattern_routing": result1,
        "capability_routing": result2,
        "entity_routing": result3,
    }


async def log_message(message: AgentMessage):
    """Log messages from the message bus."""
    logger.info(
        f"📨 Message: {message.message_type} from {message.sender} to {message.recipient}"
    )


async def run_demo():
    """Run the complete Grace Fields demo."""
    # Setup Grace Fields and agents
    grace, message_bus = await setup_grace_fields()

    # Check health of all agents
    health = await grace.check_health()
    logger.info(f"System health: {health['status']}")

    # Run the lead-to-booking workflow demo
    await demo_lead_to_booking_workflow(grace)

    # Run the content lifecycle workflow demo
    await demo_content_lifecycle_workflow(grace)

    # Run the dynamic routing demo
    await demo_dynamic_routing(grace)

    logger.info("✅ Grace Fields demonstration completed")


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # Run the demo
    asyncio.run(run_demo())
