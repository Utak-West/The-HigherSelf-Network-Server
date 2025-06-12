"""
Pipit payment integration service for The HigherSelf Network Server.
This service handles integration with Pipit payment processing while maintaining Notion as the central hub.
"""

import asyncio
import hashlib
import hmac
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import httpx
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from models.base import ApiPlatform
from models.pipit_models import (PipitCurrency, PipitPaymentRequest,
                                 PipitPaymentResponse, PipitPaymentStatus,
                                 PipitPaymentStatusResponse,
                                 PipitWebhookPayload)
from models.video_transaction_models import (VideoTransaction,
                                             VideoTransactionStatus,
                                             VideoTransactionType)
from services.base_service import BaseService, ServiceCredentials
from services.notion_service import NotionService
from utils.api_decorators import handle_async_api_errors


class PipitConfig(BaseModel):
    """Configuration for Pipit API integration."""

    api_key: str
    api_secret: str
    base_url: str = "https://api.pipit.com/v1"
    webhook_secret: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        env_prefix = "PIPIT_"


class PipitService(BaseService):
    """
    Service for interacting with the Pipit payment API.
    Handles payment processing while maintaining Notion as the central hub.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        notion_service: Optional[NotionService] = None,
    ):
        """
        Initialize the Pipit service.

        Args:
            api_key: Pipit API key
            api_secret: Pipit API secret
            base_url: Pipit API base URL
            webhook_secret: Secret for validating Pipit webhooks
            notion_service: NotionService instance for data persistence
        """
        # Load config from environment if not provided
        self.api_key = api_key or os.environ.get("PIPIT_API_KEY")
        self.api_secret = api_secret or os.environ.get("PIPIT_API_SECRET")
        self.base_url = base_url or os.environ.get(
            "PIPIT_BASE_URL", "https://api.pipit.com/v1"
        )
        self.webhook_secret = webhook_secret or os.environ.get("PIPIT_WEBHOOK_SECRET")

        # Create credentials object
        credentials = ServiceCredentials(
            api_key=self.api_key,
            api_secret=self.api_secret,
            additional_params={
                "base_url": self.base_url,
                "webhook_secret": self.webhook_secret,
            },
        )

        # Initialize base service
        super().__init__(service_name="pipit", credentials=credentials)

        # Store NotionService instance
        self.notion_service = notion_service

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        if not self.api_key or not self.api_secret:
            logger.warning("Pipit API credentials not fully configured")
        else:
            logger.info("Pipit service initialized successfully")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    @handle_async_api_errors(api_name="pipit")
    async def create_payment(
        self, request: PipitPaymentRequest
    ) -> PipitPaymentResponse:
        """
        Create a payment with Pipit.

        Args:
            request: Payment request parameters

        Returns:
            Payment response with status and payment URL
        """
        logger.info(
            f"Creating Pipit payment for amount: {request.amount} {request.currency}"
        )

        try:
            # Prepare request payload
            payload = request.dict(exclude_none=True)

            # Make API request
            response = await self.client.post("/payments", json=payload)
            response.raise_for_status()
            data = response.json()

            # Calculate total amount from items
            total_amount = sum(
                item.unit_price * item.quantity for item in request.items
            )

            # Create transaction in Notion if NotionService is available
            transaction_id = None
            if self.notion_service:
                # Extract video ID from metadata if available
                video_id = (
                    request.metadata.get("video_id") if request.metadata else None
                )

                if video_id:
                    # Create a VideoTransaction object
                    transaction = VideoTransaction(
                        transaction_id=f"vt-{data.get('payment_id')}",
                        video_id=video_id,
                        customer_email=request.customer.email,
                        customer_name=request.customer.name,
                        transaction_type=VideoTransactionType.PREMIUM_FEATURE,
                        transaction_status=VideoTransactionStatus.PENDING,
                        payment_id=data.get("payment_id"),
                        payment_status=PipitPaymentStatus.PENDING,
                        amount=total_amount,
                        currency=request.currency,
                        features=[
                            {
                                "feature_id": item.id,
                                "feature_type": item.feature_type,
                                "name": item.name,
                                "description": item.description,
                                "price": item.unit_price,
                            }
                            for item in request.items
                        ],
                        business_entity_id=request.business_entity_id,
                        metadata=request.metadata,
                    )

                    # Save to Notion
                    transaction_id = await self.notion_service.create_video_transaction(
                        transaction
                    )
                    logger.info(
                        f"Created video transaction in Notion with ID: {transaction_id}"
                    )

            # Return response
            return PipitPaymentResponse(
                status="success",
                message="Payment created successfully",
                payment_id=data.get("payment_id"),
                payment_url=data.get("payment_url"),
                transaction_id=transaction_id,
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error creating payment: {e.response.status_code} - {e.response.text}"
            )
            return PipitPaymentResponse(
                status="error",
                message=f"HTTP error: {e.response.status_code} - {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            return PipitPaymentResponse(status="error", message=f"Error: {str(e)}")

    @handle_async_api_errors(api_name="pipit")
    async def get_payment_status(self, payment_id: str) -> PipitPaymentStatusResponse:
        """
        Check the status of a payment.

        Args:
            payment_id: ID of the payment

        Returns:
            Payment status response
        """
        logger.info(f"Checking status of Pipit payment: {payment_id}")

        try:
            # Make API request
            response = await self.client.get(f"/payments/{payment_id}")
            response.raise_for_status()
            data = response.json()

            # Get transaction ID from Notion if NotionService is available
            transaction_id = None
            if self.notion_service:
                # Query Notion for transaction with this payment ID
                transaction = await self.notion_service.find_transaction_by_payment_id(
                    payment_id
                )
                if transaction:
                    transaction_id = transaction.id

                    # Update transaction if payment status has changed
                    if transaction.payment_status != data.get("status"):
                        # Map payment status to transaction status
                        transaction_status = VideoTransactionStatus.PENDING
                        if data.get("status") == PipitPaymentStatus.COMPLETED:
                            transaction_status = VideoTransactionStatus.COMPLETED
                        elif data.get("status") in [
                            PipitPaymentStatus.FAILED,
                            PipitPaymentStatus.DISPUTED,
                        ]:
                            transaction_status = VideoTransactionStatus.FAILED
                        elif data.get("status") == PipitPaymentStatus.REFUNDED:
                            transaction_status = VideoTransactionStatus.REFUNDED

                        # Update transaction in Notion
                        updates = {
                            "payment_status": data.get("status"),
                            "transaction_status": transaction_status,
                            "updated_at": datetime.now(),
                        }
                        await self.notion_service.update_video_transaction(
                            transaction.id, updates
                        )
                        logger.info(
                            f"Updated video transaction in Notion with payment status: {transaction.id}"
                        )

            # Return response
            return PipitPaymentStatusResponse(
                status="success",
                payment_id=payment_id,
                payment_status=PipitPaymentStatus(data.get("status", "pending")),
                transaction_id=transaction_id,
                amount=data.get("amount"),
                currency=PipitCurrency(data.get("currency", "usd")),
                customer_email=data.get("customer", {}).get("email"),
                created_at=datetime.fromisoformat(data.get("created_at")),
                updated_at=datetime.fromisoformat(data.get("updated_at")),
                message=data.get("message"),
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error checking payment status: {e.response.status_code} - {e.response.text}"
            )
            return PipitPaymentStatusResponse(
                status="error",
                payment_id=payment_id,
                payment_status=PipitPaymentStatus.FAILED,
                amount=0.0,
                currency=PipitCurrency.USD,
                customer_email="unknown@example.com",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                message=f"HTTP error: {e.response.status_code} - {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            return PipitPaymentStatusResponse(
                status="error",
                payment_id=payment_id,
                payment_status=PipitPaymentStatus.FAILED,
                amount=0.0,
                currency=PipitCurrency.USD,
                customer_email="unknown@example.com",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                message=f"Error: {str(e)}",
            )

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify the signature of a webhook from Pipit.

        Args:
            payload: Raw webhook payload
            signature: Signature from the webhook header

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning(
                "Webhook secret not configured, skipping signature verification"
            )
            return True

        # Calculate expected signature
        hmac_obj = hmac.new(
            self.webhook_secret.encode("utf-8"), payload, hashlib.sha256
        )
        expected_signature = hmac_obj.hexdigest()

        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)

    async def process_webhook(
        self, payload: Dict[str, Any], signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a webhook from Pipit.

        Args:
            payload: Webhook payload
            signature: Webhook signature for verification

        Returns:
            Processed webhook data
        """
        logger.info(f"Processing Pipit webhook for event: {payload.get('event_type')}")

        try:
            # Parse webhook payload
            webhook_data = PipitWebhookPayload(**payload)

            # Update transaction in Notion if NotionService is available
            if self.notion_service:
                # Query Notion for transaction with this payment ID
                transaction = await self.notion_service.find_transaction_by_payment_id(
                    webhook_data.payment_id
                )
                if transaction:
                    # Map payment status to transaction status
                    transaction_status = VideoTransactionStatus.PENDING
                    if webhook_data.payment_status == PipitPaymentStatus.COMPLETED:
                        transaction_status = VideoTransactionStatus.COMPLETED
                    elif webhook_data.payment_status in [
                        PipitPaymentStatus.FAILED,
                        PipitPaymentStatus.DISPUTED,
                    ]:
                        transaction_status = VideoTransactionStatus.FAILED
                    elif webhook_data.payment_status == PipitPaymentStatus.REFUNDED:
                        transaction_status = VideoTransactionStatus.REFUNDED

                    # Update transaction in Notion
                    updates = {
                        "payment_status": webhook_data.payment_status,
                        "transaction_status": transaction_status,
                        "updated_at": datetime.now(),
                    }
                    await self.notion_service.update_video_transaction(
                        transaction.id, updates
                    )
                    logger.info(
                        f"Updated video transaction in Notion from webhook: {transaction.id}"
                    )

            return {
                "status": "success",
                "message": "Webhook processed successfully",
                "event_type": webhook_data.event_type,
                "payment_id": webhook_data.payment_id,
                "payment_status": webhook_data.payment_status,
            }

        except ValidationError as e:
            logger.error(f"Error validating webhook payload: {e}")
            return {"status": "error", "message": f"Validation error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {"status": "error", "message": f"Error: {str(e)}"}
