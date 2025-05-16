"""
CapCut and Pipit integration API router for The HigherSelf Network Server.
Provides endpoints for video export from CapCut and payment processing with Pipit.
"""

import os
from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Header, Request
from pydantic import BaseModel, Field

from loguru import logger
from models.capcut_models import (
    CapCutExportRequest, CapCutExportResponse, CapCutExportStatusResponse,
    CapCutWebhookPayload
)
from models.pipit_models import (
    PipitPaymentRequest, PipitPaymentResponse, PipitPaymentStatusResponse,
    PipitWebhookPayload
)
from models.video_transaction_models import (
    VideoTransactionRequest, VideoTransactionResponse, VideoTransactionStatusResponse
)
from services.capcut_service import CapCutService
from services.pipit_service import PipitService
from services.notion_service import NotionService


# Create router
router = APIRouter(
    prefix="/api/capcut-pipit",
    tags=["capcut-pipit"],
    responses={404: {"description": "Not found"}},
)


# Authentication middleware
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key for protected endpoints."""
    api_key = os.environ.get("API_KEY")
    if not api_key:
        logger.warning("API_KEY environment variable not set")
        return
    
    if not x_api_key or x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


# Service dependencies
async def get_capcut_service(notion_service: NotionService = Depends(get_notion_service)):
    """Get or initialize the CapCut service."""
    return CapCutService(notion_service=notion_service)


async def get_pipit_service(notion_service: NotionService = Depends(get_notion_service)):
    """Get or initialize the Pipit service."""
    return PipitService(notion_service=notion_service)


async def get_notion_service():
    """Get or initialize the Notion service."""
    return NotionService()


# CapCut endpoints
@router.post("/capcut/export", response_model=CapCutExportResponse, dependencies=[Depends(verify_api_key)])
async def export_video(
    request: CapCutExportRequest,
    background_tasks: BackgroundTasks,
    capcut_service: CapCutService = Depends(get_capcut_service)
):
    """
    Export a video from CapCut.
    
    This endpoint triggers the video export process and returns immediately.
    The actual export happens asynchronously in the background.
    """
    logger.info(f"Received CapCut export request for project: {request.project_id}")
    
    try:
        # Process the export request
        result = await capcut_service.export_video(request)
        
        if result.status == "error":
            raise HTTPException(status_code=500, detail=result.message)
        
        return result
    except Exception as e:
        logger.error(f"Error exporting video from CapCut: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capcut/exports/{export_id}", response_model=CapCutExportStatusResponse, dependencies=[Depends(verify_api_key)])
async def get_export_status(
    export_id: str,
    capcut_service: CapCutService = Depends(get_capcut_service)
):
    """
    Get the status of a video export from CapCut.
    
    Args:
        export_id: ID of the export task
    """
    logger.info(f"Checking status of CapCut export: {export_id}")
    
    try:
        result = await capcut_service.get_export_status(export_id)
        
        if result.status == "error":
            raise HTTPException(status_code=404, detail=result.message)
        
        return result
    except Exception as e:
        logger.error(f"Error getting CapCut export status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capcut/webhook")
async def capcut_webhook(
    request: Request,
    capcut_service: CapCutService = Depends(get_capcut_service)
):
    """
    Webhook endpoint for CapCut export status updates.
    
    This endpoint receives notifications from CapCut when an export is completed or fails.
    """
    logger.info("Received webhook from CapCut")
    
    try:
        # Get the raw request body for signature verification
        body = await request.body()
        
        # Get the signature from headers if available
        signature = request.headers.get("x-capcut-signature")
        
        # Parse the request body
        payload = await request.json()
        
        # Process the webhook
        result = await capcut_service.process_webhook(payload, signature)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
    except Exception as e:
        logger.error(f"Error processing CapCut webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Pipit endpoints
@router.post("/pipit/payments", response_model=PipitPaymentResponse, dependencies=[Depends(verify_api_key)])
async def create_payment(
    request: PipitPaymentRequest,
    pipit_service: PipitService = Depends(get_pipit_service)
):
    """
    Create a payment with Pipit.
    
    This endpoint creates a payment and returns a URL for the customer to complete the payment.
    """
    logger.info(f"Received Pipit payment request for amount: {request.amount} {request.currency}")
    
    try:
        # Process the payment request
        result = await pipit_service.create_payment(request)
        
        if result.status == "error":
            raise HTTPException(status_code=500, detail=result.message)
        
        return result
    except Exception as e:
        logger.error(f"Error creating Pipit payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipit/payments/{payment_id}", response_model=PipitPaymentStatusResponse, dependencies=[Depends(verify_api_key)])
async def get_payment_status(
    payment_id: str,
    pipit_service: PipitService = Depends(get_pipit_service)
):
    """
    Get the status of a payment from Pipit.
    
    Args:
        payment_id: ID of the payment
    """
    logger.info(f"Checking status of Pipit payment: {payment_id}")
    
    try:
        result = await pipit_service.get_payment_status(payment_id)
        
        if result.status == "error":
            raise HTTPException(status_code=404, detail=result.message)
        
        return result
    except Exception as e:
        logger.error(f"Error getting Pipit payment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipit/webhook")
async def pipit_webhook(
    request: Request,
    pipit_service: PipitService = Depends(get_pipit_service)
):
    """
    Webhook endpoint for Pipit payment status updates.
    
    This endpoint receives notifications from Pipit when a payment is completed, failed, or refunded.
    """
    logger.info("Received webhook from Pipit")
    
    try:
        # Get the raw request body for signature verification
        body = await request.body()
        
        # Get the signature from headers if available
        signature = request.headers.get("x-pipit-signature")
        
        # Verify the signature
        if signature and not pipit_service.verify_webhook_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse the request body
        payload = await request.json()
        
        # Process the webhook
        result = await pipit_service.process_webhook(payload, signature)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
    except Exception as e:
        logger.error(f"Error processing Pipit webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Video transaction endpoints
@router.post("/transactions", response_model=VideoTransactionResponse, dependencies=[Depends(verify_api_key)])
async def create_transaction(
    request: VideoTransactionRequest,
    pipit_service: PipitService = Depends(get_pipit_service),
    notion_service: NotionService = Depends(get_notion_service)
):
    """
    Create a video transaction and initiate payment if needed.
    
    This endpoint creates a transaction record and returns a payment URL if payment is required.
    """
    logger.info(f"Received video transaction request for video: {request.video_id}")
    
    try:
        # Calculate total amount
        total_amount = sum(feature.price for feature in request.features)
        
        # Create payment request
        payment_request = PipitPaymentRequest(
            amount=total_amount,
            currency=PipitCurrency.USD,
            description=f"Premium video features for {request.video_id}",
            customer={
                "email": request.customer_email,
                "name": request.customer_name
            },
            items=[{
                "id": feature.feature_id,
                "name": feature.name,
                "description": feature.description,
                "unit_price": feature.price,
                "feature_type": feature.feature_type
            } for feature in request.features],
            success_url=f"https://thehigherself.network/videos/{request.video_id}/success",
            cancel_url=f"https://thehigherself.network/videos/{request.video_id}/cancel",
            metadata={
                "video_id": request.video_id,
                "transaction_type": request.transaction_type,
                "business_entity_id": request.business_entity_id
            },
            business_entity_id=request.business_entity_id
        )
        
        # Create payment with Pipit
        payment_result = await pipit_service.create_payment(payment_request)
        
        if payment_result.status == "error":
            raise HTTPException(status_code=500, detail=payment_result.message)
        
        return VideoTransactionResponse(
            status="success",
            message="Transaction created successfully",
            transaction_id=payment_result.transaction_id,
            payment_url=payment_result.payment_url
        )
    except Exception as e:
        logger.error(f"Error creating video transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{transaction_id}", response_model=VideoTransactionStatusResponse, dependencies=[Depends(verify_api_key)])
async def get_transaction_status(
    transaction_id: str,
    notion_service: NotionService = Depends(get_notion_service)
):
    """
    Get the status of a video transaction.
    
    Args:
        transaction_id: ID of the transaction
    """
    logger.info(f"Checking status of video transaction: {transaction_id}")
    
    try:
        # Get transaction from Notion
        transaction = await notion_service.get_video_transaction(transaction_id)
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return VideoTransactionStatusResponse(
            status="success",
            transaction_id=transaction_id,
            transaction_status=transaction.transaction_status,
            payment_status=transaction.payment_status,
            video_id=transaction.video_id,
            features=transaction.features,
            amount=transaction.amount,
            currency=transaction.currency,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
            expires_at=transaction.expires_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video transaction status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
