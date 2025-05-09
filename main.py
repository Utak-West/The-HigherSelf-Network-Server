#!/usr/bin/env python3
"""
Main entry point for the Windsurf Agent Network.
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
from agents.lead_capture_agent import LeadCaptureAgent
from agents.booking_agent import BookingAgent


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


async def register_agents():
    """Register all agents in Notion."""
    # Initialize lead capture agent
    lead_agent = LeadCaptureAgent(
        agent_id="LeadCaptureAgent",
        name="Lead Capture Agent", 
        description="Captures leads from various sources (Typeform, website forms) and creates workflow instances in Notion",
        business_entities=["The Connection Practice", "The 7 Space"]
    )
    
    # Initialize booking agent for retreat bookings
    booking_agent = BookingAgent(
        agent_id="TCP_AGENT_001",
        name="Retreat Booking Detection Agent", 
        description="Detects retreat bookings from Amelia and creates workflow instances in Notion",
        business_entities=["The Connection Practice"]
    )
    
    # Register agents in Notion
    await lead_agent.register_in_notion()
    logger.info("Lead Capture Agent registered successfully")
    
    await booking_agent.register_in_notion()
    logger.info("Booking Agent registered successfully")
    
    # Add more agents here as they are implemented
    
    return {
        "lead_capture_agent": lead_agent,
        "booking_agent": booking_agent
    }


def ensure_directories():
    """Ensure required directories exist."""
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)


def main():
    """Main entry point for the application."""
    # Load environment variables
    load_dotenv()
    
    # Ensure required directories exist
    ensure_directories()
    
    # Set up logging
    setup_logging()
    
    logger.info("Starting Windsurf Agent Network")
    logger.info("Application running on The HigherSelf Network Server")
    
    # Register agents in Notion
    try:
        asyncio.run(register_agents())
    except Exception as e:
        logger.error("Failed to register agents: {}", e)
    
    # Start the API server
    start_api()


if __name__ == "__main__":
    main()
