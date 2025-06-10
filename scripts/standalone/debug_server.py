#!/usr/bin/env python3
"""
Debug server for The HigherSelf Network Server.
This script helps identify issues with the server startup.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Configure logging
logger.remove()  # Remove default handler
logger.add(sys.stderr, level="DEBUG")
logger.add("logs/debug_server.log", rotation="10 MB", level="DEBUG")

def main():
    """Main entry point for debugging."""
    # Load environment variables
    load_dotenv()
    logger.info("Environment variables loaded")
    
    # Print key environment variables (sanitized)
    env_vars = {}
    for key, value in os.environ.items():
        if key.startswith(("NOTION_", "SERVER_", "LOG_", "WEBHOOK_")):
            # Sanitize sensitive values
            if "TOKEN" in key or "SECRET" in key or "KEY" in key:
                env_vars[key] = f"{value[:3]}...{value[-3:]}" if value else None
            else:
                env_vars[key] = value
    
    logger.info(f"Environment variables: {env_vars}")
    
    # Check for required directories
    logger.info("Checking required directories")
    required_dirs = ["logs", "data"]
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            logger.info(f"Creating directory: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # Try importing key modules
    logger.info("Checking imports")
    try:
        logger.info("Importing FastAPI")
        from fastapi import FastAPI
        logger.info("FastAPI imported successfully")
        
        logger.info("Importing Uvicorn")
        import uvicorn
        logger.info("Uvicorn imported successfully")
        
        logger.info("Importing Pydantic")
        from pydantic import BaseModel
        logger.info("Pydantic imported successfully")
        
        # Try importing from the project
        try:
            logger.info("Importing from api.server")
            from api.server import app
            logger.info("api.server.app imported successfully")
        except ImportError as e:
            logger.error(f"Failed to import from api.server: {e}")
            
        try:
            logger.info("Importing from config.settings")
            from config.settings import settings
            logger.info("config.settings imported successfully")
            logger.info(f"Environment: {settings.environment.value}")
        except ImportError as e:
            logger.error(f"Failed to import from config.settings: {e}")
            
        try:
            logger.info("Importing from utils.logging_setup")
            from utils.logging_setup import setup_logging
            logger.info("utils.logging_setup imported successfully")
        except ImportError as e:
            logger.error(f"Failed to import from utils.logging_setup: {e}")
            
        try:
            logger.info("Importing from services.integration_manager")
            from services.integration_manager import get_integration_manager
            logger.info("services.integration_manager imported successfully")
        except ImportError as e:
            logger.error(f"Failed to import from services.integration_manager: {e}")
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
    
    # Try starting a simple server
    try:
        logger.info("Creating a simple FastAPI app")
        from fastapi import FastAPI
        import uvicorn
        
        app = FastAPI(
            title="The HigherSelf Network Server Debug API",
            description="Debug API for The HigherSelf Network Server",
            version="1.0.0",
        )
        
        @app.get("/")
        async def root():
            return {
                "message": "The HigherSelf Network Server Debug API",
                "status": "running"
            }
        
        @app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "environment": env_vars
            }
        
        port = int(os.getenv("SERVER_PORT", "8002"))
        logger.info(f"Starting debug server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
        
    except Exception as e:
        logger.error(f"Failed to start debug server: {e}")
        logger.exception(e)

if __name__ == "__main__":
    main()
