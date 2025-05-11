#!/usr/bin/env python3
"""
Main entry point for The HigherSelf Network Server.
This script initializes the API server and agent system.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from pathlib import Path

from loguru import logger
from api.server import start as start_api
from services.integration_manager import IntegrationManager
from services.notion_service import NotionService

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


def setup_logging():
    """Configure logging for the application."""
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        level=log_level,
    )
    logger.add(
        "logs/windsurf_agents.log",
        rotation="500 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        level=log_level,
    )
    
    # Add Docker log path if running in container
    container_log_path = "/var/log/windsurf/windsurf_agents.log"
    if os.environ.get("RUNNING_IN_CONTAINER") == "true" and os.path.exists(os.path.dirname(container_log_path)):
        logger.add(
            container_log_path,
            rotation="500 MB",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
            level=log_level,
        )
    
    # Intercept standard library logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    logger.info("Logging configured with level: {}", log_level)


class InterceptHandler(logging.Handler):
    """Intercept standard library logging and redirect to loguru."""
    
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


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


async def register_agents():
    """Register all agents in Notion with named personalities."""
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
    
    # Create Grace Fields orchestrator
    grace = GraceOrchestrator([
        nyra, solari, ruvo, liora, sage, elan, zevi
    ])
    
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
    
    logger.info("🌸 Grace Fields orchestration system initialized")
    
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
    
    # Set up logging
    setup_logging()
    
    logger.info("Starting The HigherSelf Network Server")
    logger.info("Notion is configured as the central hub for all operations")
    logger.info("Initializing the named agent personality system - Grace Fields Orchestration")
    
    # Initialize integrations and register agents asynchronously
    try:
        # Run both initialization tasks
        asyncio.run(async_initialization())
    except Exception as e:
        logger.error("Failed during initialization: {}", e)
    
    # Start the API server
    start_api()


async def async_initialization():
    """Run all async initialization tasks."""
    # First initialize integrations to ensure Notion connection is established
    try:
        integration_manager = await initialize_integrations()
        logger.info("All integrations initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize integrations: {}", e)
        # Continue even if some integrations fail, as long as Notion works
    
    # Then register agents which require Notion connection
    try:
        await register_agents()
        logger.info("All agents registered successfully")
    except Exception as e:
        logger.error("Failed to register agents: {}", e)


if __name__ == "__main__":
    main()
