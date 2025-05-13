"""
API server for The HigherSelf Network Server.
Provides webhook endpoints and API routes for interacting with agents.
"""

import os
import json
# import logging # Replaced by loguru
import asyncio
from loguru import logger # Added for direct loguru usage
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from models.base import NotionIntegrationConfig, ApiPlatform
from services.notion_service import NotionService
from services.integration_manager import IntegrationManager
from services.typeform_service import TypeFormService
from services.woocommerce_service import WooCommerceService
from services.acuity_service import AcuityService
from services.amelia_service import AmeliaServiceClient
from services.airtable_service import AirtableService
from services.snovio_service import SnovIOService
from services.userfeedback_service import UserFeedbackService
from services.tutorlm_service import TutorLMService
from services.plaud_service import PlaudService
from services.ai_router import AIRouter
from agents.lead_capture_agent import LeadCaptureAgent
from agents.booking_agent import BookingAgent, AmeliaBooking
from models.notion_db_models import WorkflowInstance
from api.webhooks import router as webhook_router
from api.webhooks_circleso import router as circleso_router
from api.webhooks_beehiiv import router as beehiiv_router
from api.video_router import router as video_router
from api.crawl_router import router as crawl_router
from api.voice_router import router as voice_router
from api.rag_router import router as rag_router

# Configure logging
# logging.basicConfig removed - assuming setup_logging from utils is called in main.py
# logger = logging.getLogger("windsurf-api") # Replaced by global loguru logger

# Initialize FastAPI app
app = FastAPI(
    title="The HigherSelf Network Server API",
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

# Include routers
app.include_router(webhook_router)
app.include_router(circleso_router)
app.include_router(beehiiv_router)
app.include_router(video_router)
app.include_router(crawl_router)
app.include_router(voice_router)
app.include_router(rag_router)

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


class EventRegistrationPayload(BaseModel):
    """Payload for event registrations coming from external platforms like Zapier."""
    event_platform: str = Field(..., description="Name of the platform where the event was registered (e.g., 'Eventbrite', 'ZapierGenericEvent')")
    event_id: Optional[str] = Field(None, description="Unique identifier for the event from the source platform")
    event_name: Optional[str] = Field(None, description="Name of the event")
    attendee_email: str = Field(..., description="Email address of the attendee")
    attendee_name: Optional[str] = Field(None, description="Full name of the attendee")
    attendee_details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Other details about the attendee")
    business_entity_id: str = Field(..., description="Business entity ID for routing within the system")
    workflow_id: str = Field(..., description="Workflow ID to instantiate for this registration")
    ai_insights: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional AI-generated insights (e.g., interest categorization)")
    sync_to_hubspot: bool = Field(True, description="Whether to sync this lead to HubSpot")
    raw_payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="The raw, original payload from the source for auditing/debugging")


# Authentication middleware
async def verify_webhook_secret(x_webhook_secret: Optional[str] = Header(None)):
    """Verify webhook secret for protected endpoints."""
    webhook_secret = os.environ.get("WEBHOOK_SECRET")
    if not webhook_secret:
        logger.warning("WEBHOOK_SECRET environment variable not set")
        return

    if not x_webhook_secret or x_webhook_secret != webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


# Initialize the Integration Manager
integration_manager = IntegrationManager()

@app.on_event("startup")
async def startup_event():
    """Initialize services, integrations, and register agents on startup."""
    try:
        # Initialize the Integration Manager
        logger.info("Initializing Integration Manager...")
        integration_success = await integration_manager.initialize()

        if not integration_success:
            logger.warning("Some integrations could not be initialized. Check logs for details.")

        # Log initialization status
        status = integration_manager.get_initialization_status()
        for service, initialized in status.items():
            if initialized:
                logger.info(f"✅ {service.capitalize()} service initialized successfully")
            else:
                logger.warning(f"❌ {service.capitalize()} service failed to initialize")

        # Register agents in Notion
        await lead_capture_agent.register_in_notion()
        logger.info("Lead Capture Agent registered in Notion")

        await booking_agent.register_in_notion()
        logger.info("Booking Agent registered in Notion")

        # Initialize RAG services
        logger.info("Initializing RAG services...")
        try:
            from knowledge.vector_store import get_vector_store
            from knowledge.semantic_search import get_semantic_search
            from services.crawl4ai_service import get_crawl4ai_service
            from services.aqua_voice_service import get_aqua_voice_service
            from services.ai_router import AIRouter
            from knowledge.rag_pipeline import get_rag_pipeline

            # Initialize AI router for completions
            ai_router = AIRouter()

            # Initialize vector store and semantic search
            vector_store = await get_vector_store()
            logger.info("✅ Vector store initialized successfully")

            semantic_search = await get_semantic_search()
            logger.info("✅ Semantic search initialized successfully")

            # Initialize Crawl4AI service
            crawl_service = await get_crawl4ai_service()
            logger.info("✅ Crawl4AI service initialized successfully")

            # Initialize Aqua Voice service
            voice_service = await get_aqua_voice_service(ai_router)
            logger.info("✅ Aqua Voice service initialized successfully")

            # Initialize RAG pipeline
            rag_pipeline = await get_rag_pipeline(ai_router)
            logger.info("✅ RAG pipeline initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing RAG services: {e}")
    except Exception as e:
        logger.error(f"Error during startup: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    lead_agent_health = await lead_capture_agent.check_health()
    booking_agent_health = await booking_agent.check_health()

    # Get integration statuses
    integration_status = integration_manager.get_initialization_status()

    # Check RAG services
    rag_services_status = {}
    try:
        from knowledge.vector_store import get_vector_store
        from knowledge.semantic_search import get_semantic_search
        from services.crawl4ai_service import get_crawl4ai_service

        vector_store = await get_vector_store()
        semantic_search = await get_semantic_search()
        crawl_service = await get_crawl4ai_service()

        rag_services_status = {
            "vector_store": True,
            "semantic_search": True,
            "crawl4ai_service": True
        }
    except Exception as e:
        logger.error(f"Error checking RAG services: {e}")
        rag_services_status = {
            "vector_store": False,
            "semantic_search": False,
            "crawl4ai_service": False,
            "error": str(e)
        }

    # Calculate overall status
    overall_status = "healthy"
    if lead_agent_health.get("status") != "healthy" or booking_agent_health.get("status") != "healthy":
        overall_status = "degraded"

    # If Notion is not healthy, system is unhealthy as it's the central hub
    if not integration_status.get("notion", False):
        overall_status = "unhealthy"
    # If more than 30% of integrations failed, system is degraded
    elif sum(1 for status in integration_status.values() if not status) / len(integration_status) > 0.3:
        overall_status = "degraded"

    # If RAG services are not healthy, system is degraded
    if not all(rag_services_status.get(service, False) for service in ["vector_store", "semantic_search"]):
        if overall_status == "healthy":
            overall_status = "degraded"

    return {
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "lead_capture_agent": lead_agent_health,
            "booking_agent": booking_agent_health
        },
        "integrations": integration_status,
        "rag_services": rag_services_status
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


@app.post("/api/integrations/event_registration", response_model=WebhookResponse, dependencies=[Depends(verify_webhook_secret)])
async def event_registration_webhook(
    payload: EventRegistrationPayload,
    background_tasks: BackgroundTasks,
    request: Request  # Added to potentially access headers or client info if needed later
):
    """
    Webhook endpoint for receiving event registrations from integrated platforms like Zapier.
    Processes the registration through the LeadCaptureAgent.
    """
    logger.info(f"Received event registration from platform: {payload.event_platform} for attendee: {payload.attendee_email}")

    # Prepare event data for the LeadCaptureAgent
    # The structure should align with what LeadCaptureAgent expects or be adapted within the agent
    event_data_for_agent = {
        "source_platform": payload.event_platform,
        "event_id": payload.event_id,
        "event_name": payload.event_name,
        "email": payload.attendee_email, # Standardizing to 'email'
        "name": payload.attendee_name, # Standardizing to 'name'
        "details": payload.attendee_details,
        "business_entity_id": payload.business_entity_id,
        "workflow_id": payload.workflow_id,
        "ai_insights": payload.ai_insights,
        "sync_to_hubspot": payload.sync_to_hubspot,
        "raw_payload": payload.raw_payload, # Store the original payload for reference
        # You might want to add a specific field to indicate the source, e.g., 'zapier_event_registration'
        # This helps LeadCaptureAgent distinguish this from, say, a Typeform submission.
        "integration_source": "zapier_event_registration"
    }

    # Process the event in the background
    background_tasks.add_task(
        lead_capture_agent.process_event,
        event_type="generic_event_registration", # A new event type for LeadCaptureAgent
        event_data=event_data_for_agent
    )

    return WebhookResponse(
        status="success",
        message=f"Event registration for {payload.attendee_email} received and processing started.",
        data={"attendee_email": payload.attendee_email, "event_platform": payload.event_platform}
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

    logger.info(f"Starting The HigherSelf Network Server on port {port}")
    logger.info("Notion is configured as the central hub for all data and workflows")

    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level=os.environ.get("LOG_LEVEL", "info").lower()
    )


if __name__ == "__main__":
    start()
