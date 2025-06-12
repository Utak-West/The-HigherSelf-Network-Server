"""

Webhook handlers for The HigherSelf Network Server.
All webhooks ensure data is properly processed and stored in Notion as the central hub.
"""

import hashlib
import hmac
import json
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from loguru import logger
from pydantic import BaseModel

from agents.booking_agent import BookingAgent
from agents.community_engagement_agent import CommunityEngagementAgent
# Import all necessary agents
from agents.lead_capture_agent import LeadCaptureAgent
from agents.marketing_campaign_agent import MarketingCampaignAgent
from agents.task_management_agent import TaskManagementAgent
from config.testing_mode import TestingMode, is_api_disabled
# Import models
from models.notion_db_models import NotionSetupConfig
from models.notion_db_models_extended import CommunityMember, ContactProfile
from services.integration_manager import (IntegrationManager,
                                          get_integration_manager)
from services.notion_service import NotionService

# Initialize router
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Initialize services
# Use the from_env class method to properly initialize the NotionService
notion_service = NotionService.from_env()


# Initialize agents (dependency injection pattern)
def get_lead_capture_agent():
    return LeadCaptureAgent(notion_service)


def get_booking_agent():
    return BookingAgent(notion_service)


def get_marketing_agent():
    return MarketingCampaignAgent(notion_service)


def get_community_agent():
    return CommunityEngagementAgent(notion_service)


def get_task_agent():
    return TaskManagementAgent(notion_service)


class WebhookResponse(BaseModel):
    """Standard response model for webhook endpoints."""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


def is_test_mode() -> bool:
    """
    Check if the application is running in test mode.
    In test mode, no real API calls or webhook triggers should be made.
    """
    return (
        os.environ.get("TEST_MODE", "").lower() == "true"
        or os.environ.get("DISABLE_WEBHOOKS", "").lower() == "true"
        or is_api_disabled("webhook")
    )


async def verify_typeform_webhook(
    request: Request, signature: str = Header(None)
) -> bool:
    """
    Verify that a webhook is genuinely from TypeForm.

    Args:
        request: FastAPI request object
        signature: Signature header from TypeForm

    Returns:
        True if signature is valid, False otherwise
    """
    # In test mode, skip actual verification
    if is_test_mode():
        logger.info(
            "Running in TEST_MODE: Skipping TypeForm webhook signature verification"
        )
        return True

    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature header")

    # Get TypeForm signing secret from environment
    typeform_secret = os.environ.get("TYPEFORM_WEBHOOK_SECRET")
    if not typeform_secret:
        logger.error("TypeForm webhook secret not found in environment variables")
        raise HTTPException(
            status_code=500, detail="Webhook verification configuration error"
        )

    # Get raw request body
    body = await request.body()

    # Create HMAC SHA256 hash using the secret key
    computed_signature = hmac.new(
        typeform_secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()

    # Compare signatures
    if not hmac.compare_digest(signature, computed_signature):
        logger.warning(f"TypeForm webhook signature verification failed")
        return False

    logger.info("TypeForm webhook signature verified successfully")
    return True


@router.post("/typeform", response_model=WebhookResponse)
async def typeform_webhook(
    request: Request,
    integration_manager: IntegrationManager = Depends(get_integration_manager),
    signature: str = Header(None, alias="x-signature"),
):
    """
    Handle webhooks from TypeForm.

    Args:
        request: FastAPI request object
        integration_manager: Integration manager instance
        signature: Signature header from TypeForm

    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Check if in test mode
        if is_test_mode():
            logger.info("Running in TEST_MODE: Simulating TypeForm webhook processing")
            return WebhookResponse(
                success=True,
                message="TypeForm webhook simulated successfully (TEST MODE)",
                data={
                    "form_id": "test_form_id",
                    "notion_page_id": "mock_notion_page_id",
                },
            )

        # Verify the webhook signature
        if signature and not await verify_typeform_webhook(request, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Parse the request body
        body = await request.body()
        data = json.loads(body)

        # Get form response data
        form_response = data.get("form_response", {})
        form_id = form_response.get("form_id", "unknown")

        logger.info(f"Received TypeForm webhook for form {form_id}")

        # Get TypeForm service from integration manager
        typeform_service = integration_manager.get_service("typeform")
        if not typeform_service:
            logger.error("TypeForm service not initialized")
            raise HTTPException(
                status_code=503, detail="TypeForm service not available"
            )

        # Process the form response
        result = await typeform_service.process_form_response(form_response)

        # Ensure the data is properly stored in Notion as the central hub
        notion_page_id = await notion_service.add_typeform_response(result)

        logger.info(
            f"TypeForm response processed and stored in Notion with page ID: {notion_page_id}"
        )

        return WebhookResponse(
            success=True,
            message="TypeForm webhook processed successfully",
            data={"form_id": form_id, "notion_page_id": notion_page_id},
        )
    except Exception as e:
        logger.error(f"Error processing TypeForm webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )


@router.post("/woocommerce", response_model=WebhookResponse)
async def woocommerce_webhook(
    request: Request,
    integration_manager: IntegrationManager = Depends(get_integration_manager),
):
    """
    Handle webhooks from WooCommerce.

    Args:
        request: FastAPI request object
        integration_manager: Integration manager instance

    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Check if in test mode
        if is_test_mode():
            logger.info(
                "Running in TEST_MODE: Simulating WooCommerce webhook processing"
            )
            return WebhookResponse(
                success=True,
                message="WooCommerce webhook simulated successfully (TEST MODE)",
                data={
                    "topic": "test_topic",
                    "resource_id": "test_resource_id",
                    "notion_page_id": "mock_notion_page_id",
                },
            )

        # Parse request body
        body = await request.json()

        # Extract webhook data
        webhook_topic = body.get("topic", "unknown")
        resource_id = body.get("id", "unknown")

        logger.info(
            f"Received WooCommerce webhook: {webhook_topic} for resource {resource_id}"
        )

        # Get WooCommerce service from integration manager
        woocommerce_service = integration_manager.get_service("woocommerce")
        if not woocommerce_service:
            logger.error("WooCommerce service not initialized")
            raise HTTPException(
                status_code=503, detail="WooCommerce service not available"
            )

        # Process webhook based on topic
        result = await woocommerce_service.process_webhook(body)

        # Ensure data is properly stored in Notion as the central hub
        notion_page_id = await notion_service.sync_woocommerce_data(result)

        return WebhookResponse(
            success=True,
            message=f"Successfully processed WooCommerce webhook for {webhook_topic}",
            data={
                "topic": webhook_topic,
                "resource_id": resource_id,
                "notion_page_id": notion_page_id,
            },
        )
    except Exception as e:
        logger.error(f"Error processing WooCommerce webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )


@router.post("/acuity", response_model=WebhookResponse)
async def acuity_webhook(
    request: Request,
    integration_manager: IntegrationManager = Depends(get_integration_manager),
):
    """
    Handle webhooks from Acuity Scheduling.

    Args:
        request: FastAPI request object
        integration_manager: Integration manager instance

    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Check if in test mode
        if is_test_mode():
            logger.info("Running in TEST_MODE: Simulating Acuity webhook processing")
            return WebhookResponse(
                success=True,
                message="Acuity webhook simulated successfully (TEST MODE)",
                data={
                    "action": "test_action",
                    "appointment_id": "test_appointment_id",
                    "notion_page_id": "mock_notion_page_id",
                },
            )

        # Get Acuity service from integration manager
        acuity_service = integration_manager.get_service("acuity")
        if not acuity_service:
            logger.error("Acuity service not initialized")
            raise HTTPException(status_code=503, detail="Acuity service not available")

        # Parse request body
        body = await request.json()

        # Extract webhook data
        action = body.get("action", "unknown")
        appointment_id = body.get("id")

        logger.info(
            f"Received Acuity webhook: {action} for appointment {appointment_id}"
        )

        # Process the webhook with Acuity service
        result = await acuity_service.process_webhook(body)

        # Ensure data is properly stored in Notion as the central hub
        notion_page_id = await notion_service.sync_acuity_appointment(result)

        # Update Acuity with the Notion reference for bidirectional sync
        if notion_page_id and acuity_service.supports_metadata_update():
            await acuity_service.update_appointment_metadata(
                appointment_id, {"notion_page_id": notion_page_id}
            )

        return WebhookResponse(
            success=True,
            message=f"Successfully processed Acuity webhook for {action}",
            data={
                "action": action,
                "appointment_id": appointment_id,
                "notion_page_id": notion_page_id,
            },
        )
    except Exception as e:
        logger.error(f"Error processing Acuity webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )


@router.post("/userfeedback", response_model=WebhookResponse)
async def userfeedback_webhook(
    request: Request,
    integration_manager: IntegrationManager = Depends(get_integration_manager),
):
    """
    Handle webhooks from UserFeedback.

    Args:
        request: FastAPI request object
        integration_manager: Integration manager instance

    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Check if in test mode
        if is_test_mode():
            logger.info(
                "Running in TEST_MODE: Simulating UserFeedback webhook processing"
            )
            return WebhookResponse(
                success=True,
                message="UserFeedback webhook simulated successfully (TEST MODE)",
                data={
                    "feedback_id": "test_feedback_id",
                    "sentiment": "positive",
                    "notion_page_id": "mock_notion_page_id",
                },
            )

        # Get UserFeedback service from integration manager
        userfeedback_service = integration_manager.get_service("userfeedback")
        if not userfeedback_service:
            logger.error("UserFeedback service not initialized")
            raise HTTPException(
                status_code=503, detail="UserFeedback service not available"
            )

        # Parse request body
        body = await request.json()

        # Extract feedback data
        feedback_id = body.get("feedback", {}).get("id")
        feedback_text = body.get("feedback", {}).get("feedback_text", "")
        sentiment = body.get("feedback", {}).get("sentiment", "neutral")
        source = body.get("source", "unknown")

        logger.info(
            f"Received UserFeedback webhook from {source} with sentiment {sentiment}"
        )

        # Process webhook data
        result = await userfeedback_service.process_feedback(body)

        # Ensure feedback is properly stored in Notion as the central hub
        notion_page_id = await notion_service.add_user_feedback(result)

        # Update the originating system with the Notion reference if applicable
        if notion_page_id and hasattr(userfeedback_service, "update_feedback_source"):
            await userfeedback_service.update_feedback_source(
                feedback_id, {"notion_page_id": notion_page_id}
            )

        return WebhookResponse(
            success=True,
            message=f"Successfully processed UserFeedback webhook",
            data={
                "feedback_id": feedback_id,
                "sentiment": sentiment,
                "notion_page_id": notion_page_id,
            },
        )
    except Exception as e:
        logger.error(f"Error processing UserFeedback webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )


@router.post("/tutorLM", response_model=WebhookResponse)
async def tutor_lm_webhook(request: Request):
    """
    Handle webhooks from TutorLM.

    Args:
        request: FastAPI request object

    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Check if in test mode
        if is_test_mode():
            logger.info("Running in TEST_MODE: Simulating TutorLM webhook processing")
            return WebhookResponse(
                success=True,
                message="TutorLM webhook simulated successfully (TEST MODE)",
                data={"event_type": "test_event", "student_id": "test_student_id"},
            )

        # Parse request body
        body = await request.json()

        # Extract webhook data
        event_type = body.get("event", "unknown")
        student_id = body.get("student_id")

        logger.info(f"Received TutorLM webhook: {event_type} for student {student_id}")

        # Process webhook based on event type
        # This will be handled by a specialized agent, which will be implemented separately

        # Ensure data is properly stored in Notion as the central hub
        await notion_service.sync_tutor_lm_event(body)

        return WebhookResponse(
            success=True,
            message=f"Successfully received TutorLM webhook for {event_type}",
            data={"event_type": event_type, "student_id": student_id},
        )
    except Exception as e:
        logger.error(f"Error processing TutorLM webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )


@router.post("/amelia", response_model=WebhookResponse)
async def amelia_webhook(request: Request):
    """
    Handle webhooks from Amelia.

    Args:
        request: FastAPI request object

    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Check if in test mode
        if is_test_mode():
            logger.info("Running in TEST_MODE: Simulating Amelia webhook processing")
            return WebhookResponse(
                success=True,
                message="Amelia webhook simulated successfully (TEST MODE)",
                data={"action": "test_action", "booking_id": "test_booking_id"},
            )

        # Parse request body
        body = await request.json()

        # Extract webhook data
        action = body.get("action", "unknown")
        booking_id = body.get("booking_id")

        logger.info(f"Received Amelia webhook: {action} for booking {booking_id}")

        # Process webhook based on action type
        # This will be handled by a specialized agent, which will be implemented separately

        # Ensure data is properly stored in Notion as the central hub
        await notion_service.sync_amelia_booking(body)

        return WebhookResponse(
            success=True,
            message=f"Successfully received Amelia webhook for {action}",
            data={"action": action, "booking_id": booking_id},
        )
    except Exception as e:
        logger.error(f"Error processing Amelia webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )


@router.post("/snovio", response_model=WebhookResponse)
async def snovio_webhook(request: Request):
    """
    Handle webhooks from Snov.io.

    Args:
        request: FastAPI request object

    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Check if in test mode
        if is_test_mode():
            logger.info("Running in TEST_MODE: Simulating Snov.io webhook processing")
            return WebhookResponse(
                success=True,
                message="Snov.io webhook simulated successfully (TEST MODE)",
                data={"event_type": "test_event"},
            )

        # Parse request body
        body = await request.json()

        # Extract webhook data
        event_type = body.get("event", "unknown")

        logger.info(f"Received Snov.io webhook: {event_type}")

        # Process webhook based on event type
        # This will be handled by a specialized agent, which will be implemented separately

        # Ensure data is properly stored in Notion as the central hub
        await notion_service.sync_snovio_data(body)

        return WebhookResponse(
            success=True,
            message=f"Successfully received Snov.io webhook for {event_type}",
            data={"event_type": event_type},
        )
    except Exception as e:
        logger.error(f"Error processing Snov.io webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )
