"""
API server for the Windsurf Agent Network.
Provides webhook endpoints and API routes for interacting with agents.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from models.base import NotionIntegrationConfig, ApiPlatform
from services.notion_service import NotionService
from agents.lead_capture_agent import LeadCaptureAgent
from agents.booking_agent import BookingAgent, AmeliaBooking
from models.notion_db_models import WorkflowInstance


# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("windsurf-api")

# Initialize FastAPI app
app = FastAPI(
    title="Windsurf Agent Network API",
    description="API for The HigherSelf Network's agent system integrated with Notion",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
lead_capture_agent = LeadCaptureAgent(
    agent_id="LeadCaptureAgent",
    name="Lead Capture Agent",
    description="Captures leads from various sources and creates workflow instances",
    business_entities=["The Connection Practice", "The 7 Space"]
)

booking_agent = BookingAgent(
    agent_id="TCP_AGENT_001",
    name="Retreat Booking Detection Agent",
    description="Detects retreat bookings from Amelia and creates workflow instances",
    business_entities=["The Connection Practice"]
)


# API Models
class WebhookResponse(BaseModel):
    """Standard response for webhook endpoints."""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


class TypeformWebhookPayload(BaseModel):
    """Typeform webhook payload model."""
    event_id: str
    event_type: str
    form_id: str
    response_id: str
    submitted_at: str
    answers: Dict[str, Any]


class WebsiteFormPayload(BaseModel):
    """Website form submission payload model."""
    form_id: str
    business_entity_id: str
    workflow_id: str
    form_data: Dict[str, Any]
    sync_to_hubspot: bool = True


# Authentication middleware
async def verify_webhook_secret(x_webhook_secret: Optional[str] = Header(None)):
    """Verify webhook secret for protected endpoints."""
    webhook_secret = os.environ.get("WEBHOOK_SECRET")
    if not webhook_secret:
        logger.warning("WEBHOOK_SECRET environment variable not set")
        return
    
    if not x_webhook_secret or x_webhook_secret != webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


@app.on_event("startup")
async def startup_event():
    """Initialize services and register agents on startup."""
    try:
        # Register agents in Notion
        await lead_capture_agent.register_in_notion()
        logger.info("Lead Capture Agent registered in Notion")
        
        await booking_agent.register_in_notion()
        logger.info("Booking Agent registered in Notion")
    except Exception as e:
        logger.error(f"Error during startup: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    lead_agent_health = await lead_capture_agent.check_health()
    booking_agent_health = await booking_agent.check_health()
    
    overall_status = "healthy"
    if lead_agent_health.get("status") != "healthy" or booking_agent_health.get("status") != "healthy":
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "lead_capture_agent": lead_agent_health,
            "booking_agent": booking_agent_health
        }
    }


@app.post("/webhooks/typeform", response_model=WebhookResponse, dependencies=[Depends(verify_webhook_secret)])
async def typeform_webhook(background_tasks: BackgroundTasks, payload: Dict[str, Any], request: Request):
    """
    Typeform webhook endpoint.
    Receives form submissions from Typeform and processes them.
    """
    logger.info(f"Received Typeform webhook: {payload.get('event_id')}")
    
    # Extract query parameters for workflow and business entity
    business_entity_id = request.query_params.get("business_entity_id")
    workflow_id = request.query_params.get("workflow_id")
    sync_to_hubspot = request.query_params.get("sync_to_hubspot", "true").lower() == "true"
    
    if not business_entity_id or not workflow_id:
        raise HTTPException(
            status_code=400,
            detail="business_entity_id and workflow_id query parameters are required"
        )
    
    # Process the webhook in the background
    background_tasks.add_task(
        lead_capture_agent.process_event,
        event_type="typeform_webhook",
        event_data={
            "payload": payload,
            "business_entity_id": business_entity_id,
            "workflow_id": workflow_id,
            "sync_to_hubspot": sync_to_hubspot
        }
    )
    
    return WebhookResponse(
        status="success",
        message="Typeform webhook received and processing started",
        data={"event_id": payload.get("event_id")}
    )


@app.post("/api/forms/submit", response_model=WebhookResponse)
async def submit_website_form(payload: WebsiteFormPayload):
    """
    Submit a website form for processing.
    Creates a workflow instance for the form submission.
    """
    logger.info(f"Received website form submission for form: {payload.form_id}")
    
    # Process the form submission
    result = await lead_capture_agent.process_event(
        event_type="website_form",
        event_data={
            "form_data": payload.form_data,
            "form_id": payload.form_id,
            "business_entity_id": payload.business_entity_id,
            "workflow_id": payload.workflow_id,
            "sync_to_hubspot": payload.sync_to_hubspot
        }
    )
    
    return WebhookResponse(
        status=result.get("status", "error"),
        message=result.get("message", "Unknown error"),
        data=result
    )


@app.post("/webhooks/amelia", response_model=WebhookResponse, dependencies=[Depends(verify_webhook_secret)])
async def amelia_webhook(background_tasks: BackgroundTasks, payload: Dict[str, Any], request: Request):
    """
    Amelia webhook endpoint.
    Receives booking events from Amelia (new bookings, status updates) and processes them.
    """
    logger.info(f"Received Amelia webhook: {payload.get('event_type')}")
    
    event_type = payload.get("event_type")
    if not event_type:
        raise HTTPException(status_code=400, detail="event_type is required")
    
    # Extract query parameters for workflow and business entity
    business_entity_id = request.query_params.get("business_entity_id", "The Connection Practice")
    workflow_id = request.query_params.get("workflow_id")
    
    if not workflow_id and event_type == "new_booking":
        raise HTTPException(status_code=400, detail="workflow_id query parameter is required for new_booking events")
    
    # Process based on event type
    if event_type == "new_booking":
        # Process in the background
        background_tasks.add_task(
            booking_agent.process_event,
            event_type="new_booking",
            event_data={
                "booking": payload.get("booking", {}),
                "business_entity_id": business_entity_id,
                "workflow_id": workflow_id
            }
        )
        
        return WebhookResponse(
            status="success",
            message="Amelia booking received and processing started",
            data={"booking_id": payload.get("booking", {}).get("booking_id")}
        )
        
    elif event_type == "booking_status_update":
        # Process in the background
        background_tasks.add_task(
            booking_agent.process_event,
            event_type="booking_status_update",
            event_data={
                "booking_id": payload.get("booking_id"),
                "status": payload.get("status"),
                "additional_data": payload.get("additional_data", {})
            }
        )
        
        return WebhookResponse(
            status="success",
            message="Booking status update received and processing started",
            data={"booking_id": payload.get("booking_id")}
        )
        
    else:
        return WebhookResponse(
            status="error",
            message=f"Unsupported event type: {event_type}"
        )


@app.get("/workflows/{instance_id}")
async def get_workflow_instance(instance_id: str):
    """
    Get details of a workflow instance.
    """
    try:
        notion_service = NotionService.from_env()
        
        # Query for the workflow instance
        filter_conditions = {
            "property": "instance_id",
            "rich_text": {
                "equals": instance_id
            }
        }
        
        instances = await notion_service.query_database(
            model_class=WorkflowInstance,
            filter_conditions=filter_conditions,
            limit=1
        )
        
        if not instances:
            raise HTTPException(status_code=404, detail="Workflow instance not found")
            
        instance = instances[0]
        
        return {
            "instance_id": instance.instance_id,
            "workflow_id": instance.workflow_id,
            "current_state": instance.current_state,
            "status": instance.status,
            "client_lead_email": instance.client_lead_email,
            "start_date": instance.start_date.isoformat(),
            "last_transition_date": instance.last_transition_date.isoformat(),
            "history_log": instance.history_log
        }
        
    except Exception as e:
        logger.error(f"Error retrieving workflow instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def start():
    """Start the API server."""
    port = int(os.environ.get("SERVER_PORT", 8000))
    
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level=os.environ.get("LOG_LEVEL", "info").lower()
    )


if __name__ == "__main__":
    start()
