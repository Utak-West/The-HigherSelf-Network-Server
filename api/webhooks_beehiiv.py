"""
Beehiiv webhook handlers for The HigherSelf Network Server.
This module manages newsletter and marketing campaign integration with Notion as the central hub.
"""

import os
import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Header
# import logging # Replaced by loguru
from loguru import logger # Added for direct loguru usage

from agents.marketing_campaign_agent import MarketingCampaignAgent
from agents.lead_capture_agent import LeadCaptureAgent
from api.webhooks import WebhookResponse, is_test_mode, get_marketing_agent, get_lead_capture_agent

# logger = logging.getLogger(__name__) # Replaced by global loguru logger

# Initialize router
router = APIRouter(prefix="/webhooks/beehiiv", tags=["webhooks", "marketing"])


async def verify_beehiiv_webhook(request: Request, signature: str = Header(None)) -> bool:
    """
    Verify that a webhook is genuinely from Beehiiv.
    
    Args:
        request: FastAPI request object
        signature: Signature header from Beehiiv
        
    Returns:
        True if signature is valid, False otherwise
    """
    # In test mode, skip actual verification
    if is_test_mode():
        logger.info("Running in TEST_MODE: Skipping Beehiiv webhook signature verification")
        return True
        
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature header")
    
    # Get Beehiiv signing secret from environment
    beehiiv_secret = os.environ.get("BEEHIIV_WEBHOOK_SECRET")
    if not beehiiv_secret:
        logger.error("Beehiiv webhook secret not found in environment variables")
        raise HTTPException(status_code=500, detail="Webhook verification configuration error")
    
    # Get raw request body
    body = await request.body()
    
    # Create HMAC SHA256 hash using the secret key
    computed_signature = hmac.new(
        beehiiv_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    if not hmac.compare_digest(signature, computed_signature):
        logger.warning(f"Beehiiv webhook signature verification failed")
        return False
    
    logger.info("Beehiiv webhook signature verified successfully")
    return True


@router.post("/newsletter/metrics", response_model=WebhookResponse)
async def beehiiv_metrics_webhook(
    request: Request,
    marketing_agent: MarketingCampaignAgent = Depends(get_marketing_agent),
    signature: str = Header(None, alias="x-beehiiv-signature")
):
    """
    Handle metrics webhooks from Beehiiv for newsletter campaigns.
    
    Args:
        request: FastAPI request object
        marketing_agent: Marketing campaign agent
        signature: Signature header from Beehiiv
        
    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Check if in test mode
        if is_test_mode():
            logger.info("Running in TEST_MODE: Simulating Beehiiv metrics webhook processing")
            return WebhookResponse(
                success=True,
                message="Beehiiv metrics webhook simulated successfully (TEST MODE)",
                data={
                    "campaign_id": "test_campaign",
                    "metrics": {
                        "opens": 42,
                        "clicks": 18
                    }
                }
            )
            
        # Verify the webhook signature
        if signature and not await verify_beehiiv_webhook(request, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
        # Parse request body
        body = await request.json()
        
        # Extract campaign data
        campaign_id = body.get("campaign_id", "")
        
        logger.info(f"Received Beehiiv metrics webhook for campaign: {campaign_id}")
        
        # Update campaign metrics in Notion via the marketing agent
        result = await marketing_agent.track_campaign_metrics(campaign_id)
        
        return WebhookResponse(
            success=True,
            message="Successfully processed Beehiiv metrics",
            data=result
        )
    except Exception as e:
        logger.error(f"Error processing Beehiiv metrics webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post("/subscriber", response_model=WebhookResponse)
async def beehiiv_subscriber_webhook(
    request: Request,
    lead_agent: LeadCaptureAgent = Depends(get_lead_capture_agent),
    signature: str = Header(None, alias="x-beehiiv-signature")
):
    """
    Handle subscriber webhooks from Beehiiv.
    
    Args:
        request: FastAPI request object
        lead_agent: Lead capture agent
        signature: Signature header from Beehiiv
        
    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Check if in test mode
        if is_test_mode():
            logger.info("Running in TEST_MODE: Simulating Beehiiv subscriber webhook processing")
            return WebhookResponse(
                success=True,
                message="Beehiiv subscriber webhook simulated successfully (TEST MODE)",
                data={
                    "email": "test@example.com",
                    "action": "subscribed"
                }
            )
            
        # Verify the webhook signature
        if signature and not await verify_beehiiv_webhook(request, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
        # Parse request body
        body = await request.json()
        
        # Extract subscriber data
        action = body.get("action", "")  # subscribed, unsubscribed
        subscriber = body.get("subscriber", {})
        email = subscriber.get("email", "")
        
        logger.info(f"Received Beehiiv {action} webhook for: {email}")
        
        # Process the lead via lead capture agent
        lead_data = {
            "email": email,
            "first_name": subscriber.get("first_name", ""),
            "last_name": subscriber.get("last_name", ""),
            "utm_source": subscriber.get("utm_source", "beehiiv"),
            "utm_medium": subscriber.get("utm_medium", "newsletter"),
            "utm_campaign": subscriber.get("utm_campaign", ""),
            "lead_source": "Beehiiv Newsletter",
            "notes": f"Action: {action}",
            "subscribed_at": subscriber.get("created_at", ""),
            "referrer": subscriber.get("referrer", "")
        }
        
        # Process based on action type
        if action == "subscribed":
            result = await lead_agent.process_lead(lead_data)
        elif action == "unsubscribed":
            result = await lead_agent.update_lead_status(email, "Unsubscribed")
        else:
            logger.warning(f"Unknown Beehiiv subscriber action: {action}")
            result = {"status": "unprocessed", "reason": f"Unknown action: {action}"}
        
        return WebhookResponse(
            success=True,
            message=f"Successfully processed Beehiiv {action} webhook",
            data=result
        )
    except Exception as e:
        logger.error(f"Error processing Beehiiv subscriber webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post("/referral", response_model=WebhookResponse)
async def beehiiv_referral_webhook(
    request: Request,
    lead_agent: LeadCaptureAgent = Depends(get_lead_capture_agent),
    signature: str = Header(None, alias="x-beehiiv-signature")
):
    """
    Handle referral webhooks from Beehiiv.
    
    Args:
        request: FastAPI request object
        lead_agent: Lead capture agent
        signature: Signature header from Beehiiv
        
    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Check if in test mode
        if is_test_mode():
            logger.info("Running in TEST_MODE: Simulating Beehiiv referral webhook processing")
            return WebhookResponse(
                success=True,
                message="Beehiiv referral webhook simulated successfully (TEST MODE)",
                data={
                    "referrer_email": "referrer@example.com", 
                    "new_subscriber_email": "referred@example.com"
                }
            )
            
        # Verify the webhook signature
        if signature and not await verify_beehiiv_webhook(request, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
        # Parse request body
        body = await request.json()
        
        # Extract referral data
        referral = body.get("referral", {})
        referrer_email = referral.get("referrer_email", "")
        referred_email = referral.get("referred_email", "")
        
        logger.info(f"Received Beehiiv referral webhook: {referrer_email} referred {referred_email}")
        
        # Process the referral
        # For the referred person (new lead)
        lead_data = {
            "email": referred_email,
            "lead_source": "Beehiiv Referral",
            "utm_source": "beehiiv",
            "utm_medium": "referral",
            "notes": f"Referred by: {referrer_email}",
            "tags": ["newsletter_subscriber", "referred"]
        }
        
        # Process the new lead
        new_lead_result = await lead_agent.process_lead(lead_data)
        
        # Update the referrer's record to track their successful referral
        referrer_update = await lead_agent.add_referral_to_lead(referrer_email, referred_email)
        
        return WebhookResponse(
            success=True,
            message="Successfully processed Beehiiv referral",
            data={
                "new_lead_processed": new_lead_result.get("success", False),
                "referrer_updated": referrer_update.get("success", False)
            }
        )
    except Exception as e:
        logger.error(f"Error processing Beehiiv referral webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")
