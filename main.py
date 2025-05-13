#!/usr/bin/env python3
"""
Main entry point for The HigherSelf Network Server.
This script initializes the API server and agent system.
"""

import os
import sys
import asyncio
# import logging # Unused directly, setup_logging handles interception
from dotenv import load_dotenv
from pathlib import Path

from loguru import logger
from api.server import start as start_api
from services.integration_manager import get_integration_manager # Changed
from services.notion_service import NotionService

# Import configuration and utilities
from config.settings import settings
from utils.logging_setup import setup_logging
from utils.message_bus import MessageBus

# Import named agent personalities
from agents import (
    # Legacy agent imports (for backwards compatibility)
    LeadCaptureAgent, BookingAgent, ContentLifecycleAgent,
    AudienceSegmentationAgent, TaskManagementAgent,
    MarketingCampaignAgent, CommunityEngagementAgent,

    # Named agent personalities
    Nyra, Solari, Ruvo, Liora, Sage, Elan, Zevi,

    # Orchestration
    GraceOrchestrator, create_agent_collective, create_grace_orchestrator
)


def configure_logging():
    """Configure logging for the application using the new logging setup."""
    # Use settings for log configuration
    log_level = settings.server.log_level.value
    json_logs = settings.server.json_logs
    log_file = settings.server.log_file

    # Set up logging with our new utility
    setup_logging(
        log_level=log_level,
        json_output=json_logs,
        log_file=log_file
    )

    # Add Docker log path if running in container
    if os.environ.get("RUNNING_IN_CONTAINER") == "true":
        container_log_path = "/app/logs/higherself_agents.log"
        os.makedirs(os.path.dirname(container_log_path), exist_ok=True)
        logger.add(
            container_log_path,
            rotation="500 MB",
            retention="30 days",
            level=log_level
        )

    logger.info("Logging configured with level: {}", log_level)
    if json_logs:
        logger.info("JSON structured logging enabled")
    if log_file:
        logger.info("Logging to file: {}", log_file)


async def initialize_integrations():
    """Initialize the Integration Manager and connect all services."""
    logger.info("Fetching/Initializing Integration Manager via singleton accessor...")

    # Get or create Integration Manager instance (this will also initialize it if new)
    integration_manager = await get_integration_manager()

    if not integration_manager:
        logger.error("Failed to obtain Integration Manager instance. Critical error.")
        # This indicates a problem with get_integration_manager or its internal initialization
        raise RuntimeError("Could not initialize Integration Manager")

    logger.info("Integration Manager instance obtained.")
    status = integration_manager.get_initialization_status()

    # Log overall status based on Notion, as it's critical
    if not status.get("notion", False):
        logger.error("Integration Manager's Notion service failed to initialize. This may impact core functionality.")
    else:
        logger.info("Integration Manager's Notion service appears to be initialized.")

    # Log detailed status for all services
    successful_count = 0
    total_count = len(status) if status else 0 # Handle case where status might be None if manager failed badly
    for service, initialized in status.items():
        if initialized:
            logger.info(f"✅ {service.capitalize()} service initialized successfully via Integration Manager.")
            successful_count += 1
        else:
            logger.warning(f"❌ {service.capitalize()} service failed to initialize via Integration Manager.")
    
    if total_count > 0:
        logger.info(f"Integration Manager reported {successful_count}/{total_count} services initialized.")
    else:
        logger.warning("Integration Manager reported no services or status unavailable.")

    return integration_manager


async def register_agents(message_bus=None):
    """
    Register all agents in Notion with named personalities.

    Args:
        message_bus: Optional MessageBus instance for inter-agent communication
    """
    # Initialize Notion service
    notion_service = NotionService.from_env()

    # Initialize all named agent personalities
    nyra = Nyra(notion_client=notion_service)  # Lead Capture Specialist
    solari = Solari(notion_client=notion_service)  # Booking & Order Manager
    ruvo = Ruvo(notion_client=notion_service)  # Task Orchestrator
    liora = Liora(notion_client=notion_service)  # Marketing Strategist
    sage = Sage(notion_client=notion_service)  # Community Curator
    elan = Elan(notion_client=notion_service)  # Content Choreographer
    zevi = Zevi(notion_client=notion_service)  # Audience Analyst

    # Create Grace Fields orchestrator with message bus for enhanced communication
    grace = create_grace_orchestrator(notion_service, message_bus)

    logger.info("🌸 Grace Fields orchestration system initialized with enhanced capabilities")

    # Register all agents in Notion
    await nyra.register_in_notion()
    logger.info("✨ Nyra (Lead Capture Specialist) registered successfully")

    await solari.register_in_notion()
    logger.info("☀️ Solari (Booking & Order Manager) registered successfully")

    await ruvo.register_in_notion()
    logger.info("🏔️ Ruvo (Task Orchestrator) registered successfully")

    await liora.register_in_notion()
    logger.info("💫 Liora (Marketing Strategist) registered successfully")

    await sage.register_in_notion()
    logger.info("🌿 Sage (Community Curator) registered successfully")

    await elan.register_in_notion()
    logger.info("🎭 Elan (Content Choreographer) registered successfully")

    await zevi.register_in_notion()
    logger.info("🐺 Zevi (Audience Analyst) registered successfully")

    # Return all agents and orchestrator for use by the API server
    return {
        # Named agent personalities with unique character
        "nyra": nyra,      # Lead Capture Specialist
        "solari": solari,  # Booking & Order Manager
        "ruvo": ruvo,      # Task Orchestrator
        "liora": liora,    # Marketing Strategist
        "sage": sage,      # Community Curator
        "elan": elan,      # Content Choreographer
        "zevi": zevi,      # Audience Analyst

        # Orchestration
        "grace": grace,     # System Orchestrator

        # Legacy references (for backwards compatibility)
        "lead_capture_agent": nyra,
        "booking_agent": solari,
        "task_management_agent": ruvo,
        "marketing_campaign_agent": liora,
        "community_engagement_agent": sage,
        "content_lifecycle_agent": elan,
        "audience_segmentation_agent": zevi
    }


def ensure_directories():
    """Ensure required directories exist."""
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Create data directory for persistent storage if it doesn't exist
    Path("data").mkdir(exist_ok=True)

    # In Docker, check for mounted volumes
    if os.environ.get("RUNNING_IN_CONTAINER") == "true":
        # Ensure docker volume directories exist
        for path in ["/var/log/windsurf", "/var/data/windsurf"]:
            if not os.path.exists(path):
                try:
                    Path(path).mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory {path}")
                except Exception as e:
                    logger.warning(f"Could not create directory {path}: {e}")


def main():
    """Main entry point for the application."""
    # Load environment variables
    load_dotenv()

    # Ensure required directories exist
    ensure_directories()

    # Set up logging with our new configuration
    configure_logging()

    # Create message bus for agent communication
    message_bus = MessageBus()

    logger.info("Starting The HigherSelf Network Server")
    logger.info(f"Environment: {settings.environment.value}")
    logger.info("Notion is configured as the central hub for all operations")
    logger.info("Initializing the named agent personality system - Grace Fields Orchestration")

    # Initialize integrations and register agents asynchronously
    agents_dict = None # Initialize to None
    try:
        # Run both initialization tasks and get the agents dictionary
        agents_dict = asyncio.run(async_initialization(message_bus)) # Capture returned agents
    except Exception as e:
        logger.error("Failed during initialization: {}", e)
        logger.exception(e)
        # Potentially exit or handle critical failure if agents_dict is None and required

    if agents_dict is None:
        logger.critical("Agent initialization failed. API server cannot start with agents.")
        # Decide on behavior: exit, or start API without agents (if that's a valid state)
        # For now, let's assume we log and it might proceed without agents if start_api allows
        # Or, more robustly:
        # sys.exit("Critical: Agent initialization failed.")


    # Start the API server with configured settings and pass the agents
    start_api(
        host=settings.server.host,
        port=settings.server.port,
        log_level=settings.server.log_level.value.lower(),
        workers=settings.server.workers,
        agents=agents_dict  # Pass agents to the API server
    )


async def async_initialization(message_bus=None):
    """
    Run all async initialization tasks.

    Args:
        message_bus: Optional MessageBus instance for agent communication
    """
    # First initialize integrations to ensure Notion connection is established
    try:
        integration_manager = await initialize_integrations()
        logger.info("All integrations initialized successfully")

        # If we have a message bus, set its Notion service
        if message_bus and hasattr(integration_manager, 'notion_service'):
            message_bus.notion_service = integration_manager.notion_service
            logger.info("Message bus connected to Notion service")
    except Exception as e:
        logger.error("Failed to initialize integrations: {}", e)
        logger.exception(e)
        # Continue even if some integrations fail, as long as Notion works

    agents = None # Initialize to None
    # Then register agents which require Notion connection
    try:
        # Pass the message bus to register_agents for enhanced orchestration
        agents = await register_agents(message_bus)
        logger.info("All agents registered successfully with enhanced orchestration")

        # If we have a message bus, register agents as subscribers
        if message_bus and agents:
            for agent_id, agent_instance in agents.items(): # Renamed 'agent' to 'agent_instance' for clarity
                if hasattr(agent_instance, 'process_message'):
                    message_bus.subscribe(agent_id, agent_instance.process_message)
                    logger.info(f"Agent {agent_id} subscribed to message bus")

            # Subscribe the message bus to the GraceOrchestrator for centralized event handling
            if "grace" in agents:
                logger.info("Enhanced Grace Orchestrator connected to message bus for multi-agent workflows")
    except Exception as e:
        logger.error("Failed to register agents: {}", e)
        logger.exception(e)
        # agents will remain None if registration fails

    return agents # Return the dictionary of initialized agents


if __name__ == "__main__":
    main()
