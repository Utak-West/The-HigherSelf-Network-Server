"""
CapCut and Pipit integration for The HigherSelf Network Server.
This module provides a standalone FastAPI application for testing the integration.
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from fastapi import (BackgroundTasks, Depends, FastAPI, Header, HTTPException,
                     Request)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add parent directory to path to import from main project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from models.capcut_models import (CapCutExportRequest, CapCutExportResponse,
                                  CapCutExportStatusResponse,
                                  CapCutWebhookPayload)
from models.pipit_models import (PipitPaymentRequest, PipitPaymentResponse,
                                 PipitPaymentStatusResponse,
                                 PipitWebhookPayload)
from models.video_transaction_models import (VideoTransactionRequest,
                                             VideoTransactionResponse,
                                             VideoTransactionStatusResponse)
from services.capcut_service import CapCutService
from services.notion_service import NotionService
from services.pipit_service import PipitService

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="CapCut and Pipit Integration",
    description="Integration between CapCut and Pipit for The HigherSelf Network Server",
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


# Authentication middleware
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key for protected endpoints."""
    api_key = os.environ.get("API_KEY")
    if not api_key:
        print("WARNING: API_KEY environment variable not set")
        return

    if not x_api_key or x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


# Service dependencies
async def get_notion_service():
    """Get or initialize the Notion service."""
    return NotionService.from_env()


async def get_capcut_service(
    notion_service: NotionService = Depends(get_notion_service),
):
    """Get or initialize the CapCut service."""
    return CapCutService(notion_service=notion_service)


async def get_pipit_service(
    notion_service: NotionService = Depends(get_notion_service),
):
    """Get or initialize the Pipit service."""
    return PipitService(notion_service=notion_service)


# CapCut endpoints
@app.post(
    "/capcut/export",
    response_model=CapCutExportResponse,
    dependencies=[Depends(verify_api_key)],
)
async def export_video(
    request: CapCutExportRequest,
    background_tasks: BackgroundTasks,
    capcut_service: CapCutService = Depends(get_capcut_service),
):
    """
    Export a video from CapCut.

    This endpoint triggers the video export process and returns immediately.
    The actual export happens asynchronously in the background.
    """
    print(f"Received CapCut export request for project: {request.project_id}")

    try:
        # Process the export request
        result = await capcut_service.export_video(request)

        if result.status == "error":
            raise HTTPException(status_code=500, detail=result.message)

        return result
    except Exception as e:
        print(f"Error exporting video from CapCut: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/capcut/exports/{export_id}",
    response_model=CapCutExportStatusResponse,
    dependencies=[Depends(verify_api_key)],
)
async def get_export_status(
    export_id: str, capcut_service: CapCutService = Depends(get_capcut_service)
):
    """
    Get the status of a video export from CapCut.

    Args:
        export_id: ID of the export task
    """
    print(f"Checking status of CapCut export: {export_id}")

    try:
        result = await capcut_service.get_export_status(export_id)

        if result.status == "error":
            raise HTTPException(status_code=404, detail=result.message)

        return result
    except Exception as e:
        print(f"Error getting CapCut export status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/capcut/webhook")
async def capcut_webhook(
    request: Request, capcut_service: CapCutService = Depends(get_capcut_service)
):
    """
    Webhook endpoint for CapCut export status updates.

    This endpoint receives notifications from CapCut when an export is completed or fails.
    """
    print("Received webhook from CapCut")

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
        print(f"Error processing CapCut webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Pipit endpoints
@app.post(
    "/pipit/payments",
    response_model=PipitPaymentResponse,
    dependencies=[Depends(verify_api_key)],
)
async def create_payment(
    request: PipitPaymentRequest,
    pipit_service: PipitService = Depends(get_pipit_service),
):
    """
    Create a payment with Pipit.

    This endpoint creates a payment and returns a URL for the customer to complete the payment.
    """
    print(
        f"Received Pipit payment request for amount: {request.amount} {request.currency}"
    )

    try:
        # Process the payment request
        result = await pipit_service.create_payment(request)

        if result.status == "error":
            raise HTTPException(status_code=500, detail=result.message)

        return result
    except Exception as e:
        print(f"Error creating Pipit payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/pipit/payments/{payment_id}",
    response_model=PipitPaymentStatusResponse,
    dependencies=[Depends(verify_api_key)],
)
async def get_payment_status(
    payment_id: str, pipit_service: PipitService = Depends(get_pipit_service)
):
    """
    Get the status of a payment from Pipit.

    Args:
        payment_id: ID of the payment
    """
    print(f"Checking status of Pipit payment: {payment_id}")

    try:
        result = await pipit_service.get_payment_status(payment_id)

        if result.status == "error":
            raise HTTPException(status_code=404, detail=result.message)

        return result
    except Exception as e:
        print(f"Error getting Pipit payment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipit/webhook")
async def pipit_webhook(
    request: Request, pipit_service: PipitService = Depends(get_pipit_service)
):
    """
    Webhook endpoint for Pipit payment status updates.

    This endpoint receives notifications from Pipit when a payment is completed, failed, or refunded.
    """
    print("Received webhook from Pipit")

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
        print(f"Error processing Pipit webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Video transaction endpoints
@app.post(
    "/transactions",
    response_model=VideoTransactionResponse,
    dependencies=[Depends(verify_api_key)],
)
async def create_transaction(
    request: VideoTransactionRequest,
    pipit_service: PipitService = Depends(get_pipit_service),
    notion_service: NotionService = Depends(get_notion_service),
):
    """
    Create a video transaction and initiate payment if needed.

    This endpoint creates a transaction record and returns a payment URL if payment is required.
    """
    print(f"Received video transaction request for video: {request.video_id}")

    try:
        # Calculate total amount
        total_amount = sum(feature.price for feature in request.features)

        # Create payment request
        payment_request = PipitPaymentRequest(
            amount=total_amount,
            currency="usd",
            description=f"Premium video features for {request.video_id}",
            customer={"email": request.customer_email, "name": request.customer_name},
            items=[
                {
                    "id": feature.feature_id,
                    "name": feature.name,
                    "description": feature.description,
                    "unit_price": feature.price,
                    "feature_type": feature.feature_type,
                }
                for feature in request.features
            ],
            success_url=f"https://thehigherself.network/videos/{request.video_id}/success",
            cancel_url=f"https://thehigherself.network/videos/{request.video_id}/cancel",
            metadata={
                "video_id": request.video_id,
                "transaction_type": request.transaction_type,
                "business_entity_id": request.business_entity_id,
            },
            business_entity_id=request.business_entity_id,
        )

        # Create payment with Pipit
        payment_result = await pipit_service.create_payment(payment_request)

        if payment_result.status == "error":
            raise HTTPException(status_code=500, detail=payment_result.message)

        return VideoTransactionResponse(
            status="success",
            message="Transaction created successfully",
            transaction_id=payment_result.transaction_id,
            payment_url=payment_result.payment_url,
        )
    except Exception as e:
        print(f"Error creating video transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
