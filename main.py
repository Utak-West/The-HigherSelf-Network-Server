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
from services.integration_manager import IntegrationManager
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
    logger.info("Initializing Integration Manager with Notion as the central hub...")

    # Create Integration Manager
    integration_manager = IntegrationManager()

    # Initialize all integrations (this will validate Notion connection first)
    success = await integration_manager.initialize()

    if not success:
        logger.error("Failed to initialize Integration Manager. Check Notion connection and API keys.")

    # Log initialization status
    status = integration_manager.get_initialization_status()
    for service, initialized in status.items():
        if initialized:
            logger.info(f"✅ {service.capitalize()} service initialized successfully")
        else:
            logger.warning(f"❌ {service.capitalize()} service failed to initialize")

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
    try:
        # Run both initialization tasks
        asyncio.run(async_initialization(message_bus))
    except Exception as e:
        logger.error("Failed during initialization: {}", e)
        logger.exception(e)

    # Start the API server with configured settings
    start_api(
        host=settings.server.host,
        port=settings.server.port,
        log_level=settings.server.log_level.value.lower(),
        workers=settings.server.workers
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

    # Then register agents which require Notion connection
    try:
        # Pass the message bus to register_agents for enhanced orchestration
        agents = await register_agents(message_bus)
        logger.info("All agents registered successfully with enhanced orchestration")

        # If we have a message bus, register agents as subscribers
        if message_bus and agents:
            for agent_id, agent in agents.items():
                if hasattr(agent, 'process_message'):
                    message_bus.subscribe(agent_id, agent.process_message)
                    logger.info(f"Agent {agent_id} subscribed to message bus")

            # Subscribe the message bus to the GraceOrchestrator for centralized event handling
            if "grace" in agents:
                logger.info("Enhanced Grace Orchestrator connected to message bus for multi-agent workflows")
    except Exception as e:
        logger.error("Failed to register agents: {}", e)
        logger.exception(e)


if __name__ == "__main__":
    main()
