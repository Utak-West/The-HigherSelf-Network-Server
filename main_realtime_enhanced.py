#!/usr/bin/env python3
"""
Enhanced Main Application for HigherSelf Network Server with Real-Time AI Agent Processing

This enhanced version integrates Nyra's real-time contact processing capabilities
with the existing WordPress webhook system and prepares for MCP server integration.

Key Features:
- Real-time contact processing with Nyra
- Multi-entity business logic
- MCP server integration ready
- Enhanced workflow automation
"""

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import existing components
from agents.nyra_realtime_enhanced import NyraRealtimeEnhanced
from api import contact_workflow_webhooks, multi_entity_workflows, notion_intelligence_hub
from api.server import app as existing_app
from config.settings import settings
from services.notion_service import NotionService
from services.multi_entity_workflow_automation import MultiEntityWorkflowAutomation
from services.notion_intelligence_hub import NotionIntelligenceHub


# Global agent instances
nyra_realtime = None
notion_service = None
multi_entity_automation = None
notion_intelligence_hub = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with AI agent initialization."""
    global nyra_realtime, notion_service
    
    logger.info("🚀 Starting HigherSelf Network Server with Real-Time AI Processing...")
    
    try:
        # Initialize Notion service
        logger.info("Initializing Notion service...")
        notion_service = NotionService()
        
        # Initialize Nyra with real-time capabilities
        logger.info("Initializing Nyra Real-Time Enhanced agent...")
        nyra_realtime = NyraRealtimeEnhanced(
            notion_client=notion_service,
            mcp_enabled=os.getenv("MCP_ENABLED", "false").lower() == "true",
            mcp_servers={
                "notion": os.getenv("MCP_NOTION_ENABLED", "false").lower() == "true",
                "filesystem": os.getenv("MCP_FILESYSTEM_ENABLED", "false").lower() == "true",
                "github": os.getenv("MCP_GITHUB_ENABLED", "false").lower() == "true",
                "brave_search": os.getenv("MCP_BRAVE_SEARCH_ENABLED", "false").lower() == "true"
            }
        )
        
        # Start real-time processing
        logger.info("Starting Nyra real-time contact processing...")
        await nyra_realtime.start_realtime_processing()
        
        # Initialize multi-entity workflow automation
        logger.info("Initializing multi-entity workflow automation...")
        multi_entity_automation = MultiEntityWorkflowAutomation(notion_service)

        # Initialize Notion Intelligence Hub
        logger.info("Initializing Notion Intelligence Hub...")
        notion_intelligence_hub = NotionIntelligenceHub(notion_service, nyra_realtime.multi_entity_orchestrator)

        # Initialize webhook AI agent integration
        logger.info("Initializing webhook AI agent integration...")
        contact_workflow_webhooks.initialize_ai_agents(nyra_realtime)

        logger.info("✅ HigherSelf Network Server with Real-Time AI Processing started successfully!")
        
        # Log system status
        status = await nyra_realtime.get_processing_status()
        logger.info(f"AI Processing Status: {status}")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise
    finally:
        # Cleanup
        logger.info("🔄 Shutting down HigherSelf Network Server...")
        if nyra_realtime:
            await nyra_realtime.stop_realtime_processing()
        logger.info("✅ Shutdown complete")


# Create enhanced FastAPI app
app = FastAPI(
    title="HigherSelf Network Server - Real-Time AI Enhanced",
    description="""
    Enterprise automation platform with real-time AI agent processing for:
    - The 7 Space (191 contacts)
    - AM Consulting (1,300 contacts) 
    - HigherSelf Core (1,300 contacts)
    
    Features:
    - Real-time contact processing with Nyra AI agent
    - Multi-entity workflow automation
    - WordPress integration with The 7 Space
    - MCP server integration ready
    - Intelligent contact classification and routing
    """,
    version="2.0.0-realtime",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include existing routers
app.include_router(contact_workflow_webhooks.router, prefix="/api")
app.include_router(multi_entity_workflows.router, prefix="/api")
app.include_router(notion_intelligence_hub.router, prefix="/api")

# Add new real-time AI endpoints
@app.get("/api/ai/status")
async def get_ai_status():
    """Get real-time AI processing status."""
    if nyra_realtime:
        return await nyra_realtime.get_processing_status()
    return {"error": "AI agent not initialized"}


@app.post("/api/ai/process-contact")
async def process_contact_manually(contact_data: dict):
    """Manually process a contact through the AI pipeline."""
    if nyra_realtime:
        await nyra_realtime.queue_contact_for_processing(contact_data)
        return {"success": True, "message": "Contact queued for AI processing"}
    return {"error": "AI agent not initialized"}


@app.get("/api/ai/metrics")
async def get_ai_metrics():
    """Get AI processing metrics and analytics."""
    if nyra_realtime:
        status = await nyra_realtime.get_processing_status()
        return {
            "processing_metrics": status.get("metrics", {}),
            "queue_status": {
                "queue_size": status.get("queue_size", 0),
                "is_processing": status.get("is_processing", False)
            },
            "mcp_integration": {
                "enabled": status.get("mcp_enabled", False),
                "servers": status.get("mcp_servers", [])
            }
        }
    return {"error": "AI agent not initialized"}


@app.get("/api/health/realtime")
async def health_check_realtime():
    """Enhanced health check including AI agent status."""
    health_status = {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "components": {
            "notion_service": notion_service is not None,
            "nyra_realtime": nyra_realtime is not None,
            "ai_processing": False,
            "mcp_integration": False
        }
    }
    
    if nyra_realtime:
        ai_status = await nyra_realtime.get_processing_status()
        health_status["components"]["ai_processing"] = ai_status.get("is_processing", False)
        health_status["components"]["mcp_integration"] = ai_status.get("mcp_enabled", False)
    
    return health_status


@app.get("/")
async def root():
    """Root endpoint with enhanced information."""
    return {
        "message": "HigherSelf Network Server - Real-Time AI Enhanced",
        "version": "2.0.0-realtime",
        "features": [
            "Real-time AI contact processing",
            "Multi-entity workflow automation",
            "WordPress integration",
            "MCP server integration ready",
            "Intelligent contact classification"
        ],
        "business_entities": [
            "The 7 Space (191 contacts)",
            "AM Consulting (1,300 contacts)",
            "HigherSelf Core (1,300 contacts)"
        ],
        "ai_agents": [
            "Nyra Real-Time Enhanced (Lead Processing)",
            "Solari (Booking Management)",
            "Ruvo (Task Orchestration)",
            "Liora (Marketing Strategy)",
            "Sage (Community Curation)",
            "Elan (Content Management)",
            "Zevi (Audience Analysis)",
            "Atlas (Knowledge Retrieval)"
        ],
        "endpoints": {
            "ai_status": "/api/ai/status",
            "ai_metrics": "/api/ai/metrics",
            "contact_workflows": "/api/contact-workflows",
            "health_check": "/api/health/realtime"
        }
    }


async def main():
    """Main application entry point."""
    logger.info("🚀 Starting HigherSelf Network Server with Real-Time AI Processing...")
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    # Start server
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
