"""
Pipit payment integration models for The HigherSelf Network Server.
These models define the data structures for interacting with the Pipit payment API.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, EmailStr

from models.base import ApiPlatform


class PipitCurrency(str, Enum):
    """Currency options for Pipit payments."""
    USD = "usd"
    EUR = "eur"
    GBP = "gbp"
    CAD = "cad"
    AUD = "aud"
    JPY = "jpy"


class PipitPaymentMethod(str, Enum):
    """Payment method options for Pipit."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTO = "crypto"


class PipitPaymentStatus(str, Enum):
    """Status options for Pipit payments."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    DISPUTED = "disputed"


class PipitFeatureType(str, Enum):
    """Types of premium video features available for purchase."""
    EXPORT_4K = "export_4k"
    REMOVE_WATERMARK = "remove_watermark"
    AI_ENHANCEMENT = "ai_enhancement"
    EXTENDED_LICENSE = "extended_license"
    PRIORITY_PROCESSING = "priority_processing"
    CUSTOM_BRANDING = "custom_branding"
    ADVANCED_EFFECTS = "advanced_effects"
    STOCK_MEDIA_PACK = "stock_media_pack"


class PipitProductItem(BaseModel):
    """Model for a product item in a Pipit payment."""
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    quantity: int = Field(1, description="Quantity")
    unit_price: float = Field(..., description="Unit price")
    feature_type: PipitFeatureType = Field(..., description="Type of premium feature")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PipitCustomer(BaseModel):
    """Model for customer information in a Pipit payment."""
    id: Optional[str] = Field(None, description="Customer ID if existing")
    email: EmailStr = Field(..., description="Customer email")
    name: Optional[str] = Field(None, description="Customer name")
    phone: Optional[str] = Field(None, description="Customer phone")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PipitPaymentRequest(BaseModel):
    """Request model for creating a payment with Pipit."""
    amount: float = Field(..., description="Payment amount")
    currency: PipitCurrency = Field(PipitCurrency.USD, description="Payment currency")
    description: str = Field(..., description="Payment description")
    customer: PipitCustomer = Field(..., description="Customer information")
    items: List[PipitProductItem] = Field(..., description="Items being purchased")
    payment_method: Optional[PipitPaymentMethod] = Field(None, description="Preferred payment method")
    success_url: HttpUrl = Field(..., description="URL to redirect after successful payment")
    cancel_url: HttpUrl = Field(..., description="URL to redirect after cancelled payment")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    business_entity_id: str = Field(..., description="Business entity ID for tracking")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "amount": 29.99,
                "currency": "usd",
                "description": "Premium video features",
                "customer": {
                    "email": "customer@example.com",
                    "name": "John Doe"
                },
                "items": [
                    {
                        "id": "feat-001",
                        "name": "4K Export",
                        "description": "Export video in 4K resolution",
                        "unit_price": 29.99,
                        "feature_type": "export_4k"
                    }
                ],
                "success_url": "https://thehigherself.network/payment/success",
                "cancel_url": "https://thehigherself.network/payment/cancel",
                "business_entity_id": "the_connection_practice"
            }
        }


class PipitPaymentResponse(BaseModel):
    """Response model for a Pipit payment request."""
    status: str = Field(..., description="Status of the request (success or error)")
    message: str = Field(..., description="Message describing the result")
    payment_id: Optional[str] = Field(None, description="ID of the created payment")
    payment_url: Optional[HttpUrl] = Field(None, description="URL to complete the payment")
    transaction_id: Optional[str] = Field(None, description="ID of the transaction in Notion")


class PipitPaymentStatusResponse(BaseModel):
    """Response model for checking the status of a Pipit payment."""
    status: str = Field(..., description="Status of the request (success or error)")
    payment_id: str = Field(..., description="ID of the payment")
    payment_status: PipitPaymentStatus = Field(..., description="Status of the payment")
    transaction_id: Optional[str] = Field(None, description="ID of the transaction in Notion")
    amount: float = Field(..., description="Payment amount")
    currency: PipitCurrency = Field(..., description="Payment currency")
    customer_email: EmailStr = Field(..., description="Customer email")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    message: Optional[str] = Field(None, description="Additional message about the status")


class PipitWebhookPayload(BaseModel):
    """Webhook payload from Pipit for payment status updates."""
    event_type: str = Field(..., description="Type of event (payment.completed, payment.failed, etc.)")
    payment_id: str = Field(..., description="ID of the payment")
    payment_status: PipitPaymentStatus = Field(..., description="Status of the payment")
    amount: float = Field(..., description="Payment amount")
    currency: PipitCurrency = Field(..., description="Payment currency")
    customer: PipitCustomer = Field(..., description="Customer information")
    items: List[PipitProductItem] = Field(..., description="Items purchased")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    timestamp: datetime = Field(..., description="Timestamp of the webhook event")
