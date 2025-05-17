#!/usr/bin/env python3
"""
Simple test server for The HigherSelf Network Server.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logging
logger.add("logs/test_server.log", rotation="10 MB", level="INFO")

# Initialize FastAPI app
app = FastAPI(
    title="The HigherSelf Network Server Test API",
    description="Test API for The HigherSelf Network Server",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to The HigherSelf Network Server Test API",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check environment variables
    env_vars = {
        "NOTION_API_TOKEN": bool(os.getenv("NOTION_API_TOKEN")),
        "WEBHOOK_SECRET": bool(os.getenv("WEBHOOK_SECRET")),
        "SERVER_PORT": os.getenv("SERVER_PORT", "8000"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    }
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": env_vars
    }

@app.get("/env")
async def environment():
    """Show environment variables (sanitized)."""
    env_vars = {}
    for key, value in os.environ.items():
        if key.startswith(("NOTION_", "SERVER_", "LOG_", "WEBHOOK_")):
            # Sanitize sensitive values
            if "TOKEN" in key or "SECRET" in key or "KEY" in key:
                env_vars[key] = f"{value[:3]}...{value[-3:]}" if value else None
            else:
                env_vars[key] = value
    
    return {
        "environment": env_vars
    }

if __name__ == "__main__":
    port = int(os.getenv("SERVER_PORT", "8000"))
    logger.info(f"Starting test server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
