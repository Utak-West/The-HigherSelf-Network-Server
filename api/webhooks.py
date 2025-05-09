"""
Webhook handlers for The HigherSelf Network Server.
All webhooks ensure data is properly processed and stored in Notion as the central hub.
"""

import os
import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from pydantic import BaseModel
from loguru import logger

from services.notion_service import NotionService
from models.notion_models import NotionIntegrationConfig


# Initialize router
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Initialize services
notion_service = NotionService()


class WebhookResponse(BaseModel):
    """Standard response model for webhook endpoints."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


async def verify_typeform_webhook(request: Request, signature: str = Header(None)) -> bool:
    """
    Verify that a webhook is genuinely from TypeForm.
    
    Args:
        request: FastAPI request object
        signature: Signature header from TypeForm
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature header")
    
    # Get TypeForm signing secret from environment
    typeform_secret = os.environ.get("TYPEFORM_WEBHOOK_SECRET")
    if not typeform_secret:
        logger.error("TypeForm webhook secret not configured")
        raise HTTPException(status_code=500, detail="Webhook verification not configured")
    
    # Get request body
    body = await request.body()
    
    # Compute HMAC signature
    computed_signature = hmac.new(
        typeform_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    if not hmac.compare_digest(computed_signature, signature):
        logger.warning("Invalid TypeForm webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return True


async def verify_woocommerce_webhook(request: Request, signature: str = Header(None, alias="X-WC-Webhook-Signature")) -> bool:
    """
    Verify that a webhook is genuinely from WooCommerce.
    
    Args:
        request: FastAPI request object
        signature: Signature header from WooCommerce
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature header")
    
    # Get WooCommerce webhook secret from environment
    woocommerce_secret = os.environ.get("WOOCOMMERCE_WEBHOOK_SECRET")
    if not woocommerce_secret:
        logger.error("WooCommerce webhook secret not configured")
        raise HTTPException(status_code=500, detail="Webhook verification not configured")
    
    # Get request body
    body = await request.body()
    
    # Compute HMAC signature
    computed_signature = hmac.new(
        woocommerce_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    if not hmac.compare_digest(computed_signature, signature):
        logger.warning("Invalid WooCommerce webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return True


@router.post("/typeform", response_model=WebhookResponse)
async def typeform_webhook(request: Request, verified: bool = Depends(verify_typeform_webhook)):
    """
    Handle webhooks from TypeForm.
    
    Args:
        request: FastAPI request object
        verified: Result of the signature verification
        
    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Parse request body
        body = await request.json()
        
        # Extract form response data
        form_id = body.get("form_response", {}).get("form_id")
        form_title = body.get("form_response", {}).get("definition", {}).get("title", "Unknown Form")
        
        logger.info(f"Received TypeForm webhook for form: {form_title} (ID: {form_id})")
        
        # Process form response and store in Notion
        # This will be handled by a specialized agent, which will be implemented separately
        
        return WebhookResponse(
            success=True,
            message=f"Successfully received TypeForm webhook for {form_title}",
            data={"form_id": form_id}
        )
    except Exception as e:
        logger.error(f"Error processing TypeForm webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post("/woocommerce", response_model=WebhookResponse)
async def woocommerce_webhook(request: Request, verified: bool = Depends(verify_woocommerce_webhook)):
    """
    Handle webhooks from WooCommerce.
    
    Args:
        request: FastAPI request object
        verified: Result of the signature verification
        
    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Parse request body
        body = await request.json()
        
        # Get webhook event type from headers
        event_type = request.headers.get("X-WC-Webhook-Event", "unknown")
        resource = request.headers.get("X-WC-Webhook-Resource", "unknown")
        
        logger.info(f"Received WooCommerce webhook: {event_type} for {resource}")
        
        # Process webhook based on event type
        # This will be handled by a specialized agent, which will be implemented separately
        
        return WebhookResponse(
            success=True,
            message=f"Successfully received WooCommerce webhook for {event_type}",
            data={"event_type": event_type, "resource": resource}
        )
    except Exception as e:
        logger.error(f"Error processing WooCommerce webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post("/amelia", response_model=WebhookResponse)
async def amelia_webhook(request: Request):
    """
    Handle webhooks from Amelia Booking.
    
    Args:
        request: FastAPI request object
        
    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Parse request body
        body = await request.json()
        
        # Extract webhook data
        event_type = body.get("type", "unknown")
        appointment_id = body.get("appointment", {}).get("id")
        
        logger.info(f"Received Amelia webhook: {event_type} for appointment {appointment_id}")
        
        # Process webhook based on event type
        # This will be handled by a specialized agent, which will be implemented separately
        
        return WebhookResponse(
            success=True,
            message=f"Successfully received Amelia webhook for {event_type}",
            data={"event_type": event_type, "appointment_id": appointment_id}
        )
    except Exception as e:
        logger.error(f"Error processing Amelia webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post("/acuity", response_model=WebhookResponse)
async def acuity_webhook(request: Request):
    """
    Handle webhooks from Acuity Scheduling.
    
    Args:
        request: FastAPI request object
        
    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Parse request body
        body = await request.json()
        
        # Extract webhook data
        action = body.get("action", "unknown")
        appointment_id = body.get("id")
        
        logger.info(f"Received Acuity webhook: {action} for appointment {appointment_id}")
        
        # Process webhook based on action type
        # This will be handled by a specialized agent, which will be implemented separately
        
        return WebhookResponse(
            success=True,
            message=f"Successfully received Acuity webhook for {action}",
            data={"action": action, "appointment_id": appointment_id}
        )
    except Exception as e:
        logger.error(f"Error processing Acuity webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post("/userfeedback", response_model=WebhookResponse)
async def userfeedback_webhook(request: Request):
    """
    Handle webhooks from UserFeedback.
    
    Args:
        request: FastAPI request object
        
    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Parse request body
        body = await request.json()
        
        # Extract feedback data
        feedback_id = body.get("feedback", {}).get("id")
        feedback_text = body.get("feedback", {}).get("feedback_text", "")
        
        logger.info(f"Received UserFeedback webhook for feedback ID: {feedback_id}")
        
        # Process feedback and store in Notion
        # This will be handled by a specialized agent, which will be implemented separately
        
        return WebhookResponse(
            success=True,
            message=f"Successfully received UserFeedback webhook",
            data={"feedback_id": feedback_id}
        )
    except Exception as e:
        logger.error(f"Error processing UserFeedback webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


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
        # Parse request body
        body = await request.json()
        
        # Extract webhook data
        event_type = body.get("event", "unknown")
        
        logger.info(f"Received Snov.io webhook: {event_type}")
        
        # Process webhook based on event type
        # This will be handled by a specialized agent, which will be implemented separately
        
        return WebhookResponse(
            success=True,
            message=f"Successfully received Snov.io webhook for {event_type}",
            data={"event_type": event_type}
        )
    except Exception as e:
        logger.error(f"Error processing Snov.io webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")
