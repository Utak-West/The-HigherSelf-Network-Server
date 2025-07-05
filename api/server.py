"""
API server for The HigherSelf Network Server.
Provides webhook endpoints and API routes for interacting with agents.
"""

import asyncio
import json
# Standard library imports
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Third-party imports
import uvicorn
from fastapi import (BackgroundTasks, Depends, FastAPI, Header, HTTPException,
                     Request)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field

from agents.booking_agent import AmeliaBooking, BookingAgent
from agents.lead_capture_agent import LeadCaptureAgent
from api.capcut_pipit_router import router as capcut_pipit_router
from api.crawl_router import router as crawl_router
from api.huggingface_router import router as huggingface_router
from api.mcp_tools_router import router as mcp_tools_router
from api.openml_router import router as openml_router
from api.rag_router import router as rag_router
from api.routes.agent_tasks import router as agent_tasks_router
# from api.routes.barter import router as barter_router  # Module not found
from api.routes.redis_health import router as redis_health_router
from api.softr_router import router as softr_router
from api.video_router import router as video_router
from api.voice_router import router as voice_router
from api.webhooks import router as webhook_router
from api.webhooks_beehiiv import router as beehiiv_router
from api.webhooks_bettermode import router as bettermode_router
from api.webhooks_circleso import router as circleso_router
from api.zapier_ecosystem import router as zapier_ecosystem_router
from api.termius_integration import router as termius_router
from api.contact_workflow_webhooks import router as contact_workflow_router
from api.notion_mail_integration import router as notion_mail_router
from api.dashboard_router import router as dashboard_router
from models.base import ApiPlatform, NotionIntegrationConfig
from models.notion_db_models import WorkflowInstance
from services.acuity_service import AcuityService
from services.ai_router import AIRouter
from services.airtable_service import AirtableService
from services.amelia_service import AmeliaServiceClient
from services.integration_manager import get_integration_manager  # Changed
from services.notion_service import NotionService
from services.plaud_service import PlaudService
from services.snovio_service import SnovIOService
from services.tutorlm_service import TutorLMService
from services.typeform_service import TypeFormService
from services.userfeedback_service import UserFeedbackService
from services.woocommerce_service import WooCommerceService

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
app.include_router(bettermode_router)  # Added BetterMode router
app.include_router(circleso_router)  # Legacy Circle.so router
app.include_router(beehiiv_router)
app.include_router(video_router)
app.include_router(crawl_router)
app.include_router(voice_router)
app.include_router(rag_router)
app.include_router(huggingface_router)
app.include_router(agent_tasks_router)
app.include_router(softr_router)
app.include_router(capcut_pipit_router)
app.include_router(redis_health_router)  # Added Redis health monitoring router
# app.include_router(barter_router)  # Added Barter system router - Module not found
app.include_router(zapier_ecosystem_router)  # Added Zapier ecosystem router
app.include_router(termius_router)  # Added Termius integration router
app.include_router(contact_workflow_router)  # Added Contact Workflow automation router
app.include_router(notion_mail_router)  # Added Notion Mail Integration router
app.include_router(dashboard_router)  # Added Operations Dashboard router
app.include_router(
    mcp_tools_router
)  # Added MCP tools router for Context7 and other MCP services
app.include_router(
    openml_router
)  # Added OpenML router for dataset management and training

# Agents will be passed via app.state.agents from main.py


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

    event_platform: str = Field(
        ...,
        description="Name of the platform where the event was registered (e.g., 'Eventbrite', 'ZapierGenericEvent')",
    )
    event_id: Optional[str] = Field(
        None, description="Unique identifier for the event from the source platform"
    )
    event_name: Optional[str] = Field(None, description="Name of the event")
    attendee_email: str = Field(..., description="Email address of the attendee")
    attendee_name: Optional[str] = Field(None, description="Full name of the attendee")
    attendee_details: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Other details about the attendee"
    )
    business_entity_id: str = Field(
        ..., description="Business entity ID for routing within the system"
    )
    workflow_id: str = Field(
        ..., description="Workflow ID to instantiate for this registration"
    )
    ai_insights: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional AI-generated insights (e.g., interest categorization)",
    )
    sync_to_hubspot: bool = Field(
        True, description="Whether to sync this lead to HubSpot"
    )
    raw_payload: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="The raw, original payload from the source for auditing/debugging",
    )


# Authentication middleware
async def verify_webhook_secret(x_webhook_secret: Optional[str] = Header(None)):
    """Verify webhook secret for protected endpoints."""
    webhook_secret = os.environ.get("WEBHOOK_SECRET")
    if not webhook_secret:
        logger.warning("WEBHOOK_SECRET environment variable not set")
        return

    if not x_webhook_secret or x_webhook_secret != webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


# Integration Manager will be fetched via get_integration_manager() where needed


@app.on_event("startup")
async def startup_event():
    """Initialize services, integrations, and register agents on startup."""
    try:
        # Get or create Integration Manager instance (this will also initialize it if new)
        logger.info(
            "Fetching/Initializing Integration Manager via singleton accessor for startup..."
        )
        integration_manager = await get_integration_manager()  # Changed

        if not integration_manager:
            logger.error(
                "Failed to obtain Integration Manager instance during startup. Critical error."
            )
            # This indicates a problem with get_integration_manager or its internal initialization
            # Depending on desired behavior, you might want to raise an error to stop startup
            return  # Or raise an exception

        logger.info("Integration Manager instance obtained for startup.")
        status = (
            integration_manager.get_initialization_status()
        )  # Get status after it's initialized

        # Log overall status based on Notion, as it's critical
        if not status.get("notion", False):
            logger.error(
                "Integration Manager's Notion service failed to initialize. This may impact core functionality."
            )
        else:
            logger.info(
                "Integration Manager's Notion service appears to be initialized."
            )

        # Log detailed status for all services
        successful_count = 0
        total_count = len(status) if status else 0
        for service, initialized in status.items():
            if initialized:
                logger.info(
                    f"✅ {service.capitalize()} service initialized successfully via Integration Manager."
                )
                successful_count += 1
            else:
                logger.warning(
                    f"❌ {service.capitalize()} service failed to initialize via Integration Manager."
                )

        if total_count > 0:
            logger.info(
                f"Integration Manager reported {successful_count}/{total_count} services initialized during startup."
            )
        else:
            logger.warning(
                "Integration Manager reported no services or status unavailable during startup."
            )

        # Agent registration is now handled in main.py before starting the API.
        # We can log the availability of agents passed via app.state
        if hasattr(app.state, "agents") and app.state.agents:
            logger.info(
                f"Agents available to API server: {list(app.state.agents.keys())}"
            )
            if "lead_capture_agent" in app.state.agents:
                logger.info("Lead Capture Agent (or its alias Nyra) instance provided.")
            if "booking_agent" in app.state.agents:
                logger.info("Booking Agent (or its alias Solari) instance provided.")
        else:
            logger.warning("No agents dictionary found in app.state or it's empty.")

        # Initialize RAG services
        logger.info("Initializing RAG services...")
        try:
            from knowledge.rag_pipeline import get_rag_pipeline
            from knowledge.semantic_search import get_semantic_search
            from knowledge.vector_store import get_vector_store
            from services.ai_router import AIRouter
            from services.aqua_voice_service import get_aqua_voice_service
            from services.crawl4ai_service import get_crawl4ai_service

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

            # Initialize Hugging Face service and router
            from api.huggingface_router import \
                init_router as init_huggingface_router
            from services.huggingface_service import HuggingFaceService

            try:
                # Create Hugging Face service
                huggingface_service = HuggingFaceService(
                    notion_service=integration_manager.get_notion_service()
                )
                if await huggingface_service.initialize():
                    # Initialize the router with the service
                    init_huggingface_router(
                        huggingface_service, integration_manager.get_notion_service()
                    )
                    logger.info("✅ Hugging Face service initialized successfully")
                else:
                    logger.warning("⚠️ Hugging Face service initialization failed")
            except Exception as e:
                logger.error(f"Error initializing Hugging Face service: {e}")

        except Exception as e:
            logger.error(f"Error initializing RAG services: {e}")
    except Exception as e:
        logger.error(f"Error during startup: {e}")


@app.get("/health")
async def health_check(request: Request):  # Added request
    """Health check endpoint."""
    # Access agents from app.state
    lead_agent = request.app.state.agents.get("lead_capture_agent")  # or 'nyra'
    booking_agent = request.app.state.agents.get("booking_agent")  # or 'solari'

    lead_agent_health = {
        "status": "unavailable",
        "reason": "Agent not found in app.state",
    }
    if lead_agent and hasattr(lead_agent, "check_health"):
        lead_agent_health = await lead_agent.check_health()
    else:
        logger.warning("Lead Capture Agent not available for health check.")

    booking_agent_health = {
        "status": "unavailable",
        "reason": "Agent not found in app.state",
    }
    if booking_agent and hasattr(booking_agent, "check_health"):
        booking_agent_health = await booking_agent.check_health()
    else:
        logger.warning("Booking Agent not available for health check.")

    # Get integration statuses
    integration_manager = await get_integration_manager()  # Added
    if not integration_manager:
        logger.error("Failed to get IntegrationManager for health check.")
        integration_status = {"error": "IntegrationManager unavailable"}
    else:
        integration_status = integration_manager.get_initialization_status()

    # Check RAG services
    rag_services_status = {}
    try:
        from knowledge.semantic_search import get_semantic_search
        from knowledge.vector_store import get_vector_store
        from services.crawl4ai_service import get_crawl4ai_service

        vector_store = await get_vector_store()
        semantic_search = await get_semantic_search()
        crawl_service = await get_crawl4ai_service()

        rag_services_status = {
            "vector_store": True,
            "semantic_search": True,
            "crawl4ai_service": True,
        }
    except Exception as e:
        logger.error(f"Error checking RAG services: {e}")
        rag_services_status = {
            "vector_store": False,
            "semantic_search": False,
            "crawl4ai_service": False,
            "error": str(e),
        }

    # Calculate overall status
    overall_status = "healthy"
    if (
        lead_agent_health.get("status") != "healthy"
        or booking_agent_health.get("status") != "healthy"
    ):
        overall_status = "degraded"

    # If Notion is not healthy, system is unhealthy as it's the central hub
    if not integration_status.get("notion", False):
        overall_status = "unhealthy"
    # If more than 30% of integrations failed, system is degraded
    elif (
        sum(1 for status in integration_status.values() if not status)
        / len(integration_status)
        > 0.3
    ):
        overall_status = "degraded"

    # Check Hugging Face service
    huggingface_status = False
    try:
        from services.huggingface_service import HuggingFaceService

        huggingface_service = HuggingFaceService()
        huggingface_status = await huggingface_service.initialize()
    except Exception as e:
        logger.error(f"Error checking Hugging Face service: {e}")
        huggingface_status = False

    # If RAG services are not healthy, system is degraded
    if not all(
        rag_services_status.get(service, False)
        for service in ["vector_store", "semantic_search"]
    ):
        if overall_status == "healthy":
            overall_status = "degraded"

    # If Hugging Face service is not healthy, system is degraded
    if not huggingface_status and overall_status == "healthy":
        overall_status = "degraded"

    # Check Redis service
    redis_status = {"status": "unavailable", "error": "Redis service not available"}
    try:
        from services.redis_service import redis_service

        redis_health = redis_service.health_check()
        redis_status = {
            "status": redis_health.get("status", "unknown"),
            "latency_ms": (
                redis_health.get("latency", 0) * 1000
                if redis_health.get("latency")
                else None
            ),
            "last_check": redis_health.get("last_check"),
            "enabled": True,
        }

        # If Redis is not healthy, system is degraded
        if redis_health.get("status") != "healthy" and overall_status == "healthy":
            overall_status = "degraded"

    except Exception as e:
        logger.error(f"Error checking Redis service: {e}")
        redis_status = {"status": "error", "error": str(e), "enabled": False}
        # Redis failure doesn't make system unhealthy, but degraded
        if overall_status == "healthy":
            overall_status = "degraded"

    return {
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "lead_capture_agent": lead_agent_health,
            "booking_agent": booking_agent_health,
        },
        "integrations": integration_status,
        "rag_services": rag_services_status,
        "huggingface_service": huggingface_status,
        "redis_service": redis_status,
    }


@app.post(
    "/webhooks/typeform",
    response_model=WebhookResponse,
    dependencies=[Depends(verify_webhook_secret)],
)
async def typeform_webhook(
    background_tasks: BackgroundTasks, payload: Dict[str, Any], request: Request
):
    """
    Typeform webhook endpoint.
    Receives form submissions from Typeform and processes them.
    """
    logger.info(f"Received Typeform webhook: {payload.get('event_id')}")
    lead_agent = request.app.state.agents.get("lead_capture_agent")  # or 'nyra'
    if not lead_agent:
        logger.error("Lead Capture Agent not found in app.state for Typeform webhook.")
        raise HTTPException(status_code=500, detail="Lead Capture Agent not available")

    # Extract query parameters for workflow and business entity
    business_entity_id = request.query_params.get("business_entity_id")
    workflow_id = request.query_params.get("workflow_id")
    sync_to_hubspot = (
        request.query_params.get("sync_to_hubspot", "true").lower() == "true"
    )

    if not business_entity_id or not workflow_id:
        raise HTTPException(
            status_code=400,
            detail="business_entity_id and workflow_id query parameters are required",
        )

    # Process the webhook in the background
    background_tasks.add_task(
        lead_agent.process_event,  # Use agent from app.state
        event_type="typeform_webhook",
        event_data={
            "payload": payload,
            "business_entity_id": business_entity_id,
            "workflow_id": workflow_id,
            "sync_to_hubspot": sync_to_hubspot,
        },
    )

    return WebhookResponse(
        status="success",
        message="Typeform webhook received and processing started",
        data={"event_id": payload.get("event_id")},
    )


@app.post("/api/forms/submit", response_model=WebhookResponse)
async def submit_website_form(
    payload: WebsiteFormPayload, request: Request
):  # Added request
    """
    Submit a website form for processing.
    Creates a workflow instance for the form submission.
    """
    logger.info(f"Received website form submission for form: {payload.form_id}")
    lead_agent = request.app.state.agents.get("lead_capture_agent")  # or 'nyra'
    if not lead_agent:
        logger.error(
            "Lead Capture Agent not found in app.state for website form submission."
        )
        raise HTTPException(status_code=500, detail="Lead Capture Agent not available")

    # Process the form submission
    result = await lead_agent.process_event(  # Use agent from app.state
        event_type="website_form",
        event_data={
            "form_data": payload.form_data,
            "form_id": payload.form_id,
            "business_entity_id": payload.business_entity_id,
            "workflow_id": payload.workflow_id,
            "sync_to_hubspot": payload.sync_to_hubspot,
        },
    )

    return WebhookResponse(
        status=result.get("status", "error"),
        message=result.get("message", "Unknown error"),
        data=result,
    )


@app.post(
    "/api/integrations/event_registration",
    response_model=WebhookResponse,
    dependencies=[Depends(verify_webhook_secret)],
)
async def event_registration_webhook(
    payload: EventRegistrationPayload,
    background_tasks: BackgroundTasks,
    request: Request,  # Added to potentially access headers or client info if needed later
):
    """
    Webhook endpoint for receiving event registrations from integrated platforms like Zapier.
    Processes the registration through the LeadCaptureAgent.
    """
    logger.info(
        f"Received event registration from platform: {payload.event_platform} for attendee: {payload.attendee_email}"
    )

    # Prepare event data for the LeadCaptureAgent
    # The structure should align with what LeadCaptureAgent expects or be adapted within the agent
    event_data_for_agent = {
        "source_platform": payload.event_platform,
        "event_id": payload.event_id,
        "event_name": payload.event_name,
        "email": payload.attendee_email,  # Standardizing to 'email'
        "name": payload.attendee_name,  # Standardizing to 'name'
        "details": payload.attendee_details,
        "business_entity_id": payload.business_entity_id,
        "workflow_id": payload.workflow_id,
        "ai_insights": payload.ai_insights,
        "sync_to_hubspot": payload.sync_to_hubspot,
        "raw_payload": payload.raw_payload,  # Store the original payload for reference
        # You might want to add a specific field to indicate the source, e.g., 'zapier_event_registration'
        # This helps LeadCaptureAgent distinguish this from, say, a Typeform submission.
        "integration_source": "zapier_event_registration",
    }

    lead_agent = request.app.state.agents.get("lead_capture_agent")  # or 'nyra'
    if not lead_agent:
        logger.error(
            "Lead Capture Agent not found in app.state for event registration webhook."
        )
        raise HTTPException(status_code=500, detail="Lead Capture Agent not available")

    # Process the event in the background
    background_tasks.add_task(
        lead_agent.process_event,  # Use agent from app.state
        event_type="generic_event_registration",  # A new event type for LeadCaptureAgent
        event_data=event_data_for_agent,
    )

    return WebhookResponse(
        status="success",
        message=f"Event registration for {payload.attendee_email} received and processing started.",
        data={
            "attendee_email": payload.attendee_email,
            "event_platform": payload.event_platform,
        },
    )


@app.post(
    "/webhooks/amelia",
    response_model=WebhookResponse,
    dependencies=[Depends(verify_webhook_secret)],
)
async def amelia_webhook(
    background_tasks: BackgroundTasks, payload: Dict[str, Any], request: Request
):
    """
    Amelia webhook endpoint.
    Receives booking events from Amelia (new bookings, status updates) and processes them.
    """
    logger.info(f"Received Amelia webhook: {payload.get('event_type')}")

    event_type = payload.get("event_type")
    if not event_type:
        raise HTTPException(status_code=400, detail="event_type is required")

    # Extract query parameters for workflow and business entity
    business_entity_id = request.query_params.get(
        "business_entity_id", "The Connection Practice"
    )
    workflow_id = request.query_params.get("workflow_id")

    if not workflow_id and event_type == "new_booking":
        raise HTTPException(
            status_code=400,
            detail="workflow_id query parameter is required for new_booking events",
        )

    # Process based on event type
    book_agent = request.app.state.agents.get("booking_agent")  # or 'solari'
    if not book_agent:
        logger.error("Booking Agent not found in app.state for Amelia webhook.")
        raise HTTPException(status_code=500, detail="Booking Agent not available")

    if event_type == "new_booking":
        # Process in the background
        background_tasks.add_task(
            book_agent.process_event,  # Use agent from app.state
            event_type="new_booking",
            event_data={
                "booking": payload.get("booking", {}),
                "business_entity_id": business_entity_id,
                "workflow_id": workflow_id,
            },
        )

        return WebhookResponse(
            status="success",
            message="Amelia booking received and processing started",
            data={"booking_id": payload.get("booking", {}).get("booking_id")},
        )

    elif event_type == "booking_status_update":
        # Process in the background
        background_tasks.add_task(
            book_agent.process_event,  # Use agent from app.state
            event_type="booking_status_update",
            event_data={
                "booking_id": payload.get("booking_id"),
                "status": payload.get("status"),
                "additional_data": payload.get("additional_data", {}),
            },
        )

        return WebhookResponse(
            status="success",
            message="Booking status update received and processing started",
            data={"booking_id": payload.get("booking_id")},
        )

    else:
        return WebhookResponse(
            status="error", message=f"Unsupported event type: {event_type}"
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
            "rich_text": {"equals": instance_id},
        }

        instances = await notion_service.query_database(
            model_class=WorkflowInstance, filter_conditions=filter_conditions, limit=1
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
            "history_log": instance.history_log,
        }

    except Exception as e:
        logger.error(f"Error retrieving workflow instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def start(
    host: str,
    port: int,
    log_level: str,
    workers: int,
    agents: Optional[Dict[str, Any]] = None,
):
    """Start the API server, now accepting configuration and agents."""
    # Store agents in app state to make them accessible to endpoints
    app.state.agents = agents if agents is not None else {}

    if not app.state.agents:
        logger.warning(
            "API server (app.state.agents) starting without any agents provided."
        )
    else:
        logger.info(
            f"API server (app.state.agents) starting with agents: {list(app.state.agents.keys())}"
        )

    logger.info(
        f"Attempting to start The HigherSelf Network Server on {host}:{port} with {workers} worker(s) and log level {log_level}"
    )
    logger.info(
        "Notion is configured as the central hub for all data and workflows (as per earlier logs)."
    )

    uvicorn.run(
        app,  # Pass the FastAPI app instance directly
        host=host,
        port=port,
        log_level=log_level,
        workers=workers,
        reload=False,  # Preserving reload=False from original
    )


# This block is likely redundant if main.py is the sole entry point.
# Commenting out to prevent accidental direct execution without proper setup.
# if __name__ == "__main__":
#     # This would require default parameters or a different setup if run directly.
#     # For now, assume main.py is the entry point.
#     logger.warning("api/server.py executed directly. This is not the intended entry point. Use main.py.")
#     # start(host="0.0.0.0", port=8000, log_level="info", workers=1, agents=None)
