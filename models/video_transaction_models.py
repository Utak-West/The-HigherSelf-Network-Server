"""
Video transaction models for The HigherSelf Network Server.
These models define the data structures for tracking video-related transactions.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, EmailStr, Field, HttpUrl

from models.base import ApiPlatform
from models.pipit_models import PipitCurrency, PipitFeatureType, PipitPaymentStatus


class VideoTransactionType(str, Enum):
    """Types of video transactions."""

    PREMIUM_FEATURE = "premium_feature"
    SUBSCRIPTION = "subscription"
    ONE_TIME_PURCHASE = "one_time_purchase"
    RENTAL = "rental"


class VideoTransactionStatus(str, Enum):
    """Status options for video transactions."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class VideoFeature(BaseModel):
    """Model for a video feature in a transaction."""

    feature_id: str = Field(..., description="Feature ID")
    feature_type: PipitFeatureType = Field(..., description="Type of premium feature")
    name: str = Field(..., description="Feature name")
    description: Optional[str] = Field(None, description="Feature description")
    price: float = Field(..., description="Feature price")
    duration_days: Optional[int] = Field(
        None, description="Duration in days if applicable"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class VideoTransaction(BaseModel):
    """Model for a video transaction in Notion."""

    id: Optional[str] = Field(None, description="Notion page ID")
    transaction_id: str = Field(..., description="Unique transaction ID")
    video_id: str = Field(..., description="ID of the related video content")
    customer_email: EmailStr = Field(..., description="Customer email")
    customer_name: Optional[str] = Field(None, description="Customer name")
    transaction_type: VideoTransactionType = Field(
        ..., description="Type of transaction"
    )
    transaction_status: VideoTransactionStatus = Field(
        ..., description="Status of the transaction"
    )
    payment_id: Optional[str] = Field(None, description="ID of the related payment")
    payment_status: Optional[PipitPaymentStatus] = Field(
        None, description="Status of the payment"
    )
    amount: float = Field(..., description="Transaction amount")
    currency: PipitCurrency = Field(
        PipitCurrency.USD, description="Transaction currency"
    )
    features: List[VideoFeature] = Field(..., description="Features purchased")
    business_entity_id: str = Field(..., description="Business entity ID")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Expiration timestamp if applicable"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        """Pydantic configuration."""

        schema_extra = {
            "example": {
                "transaction_id": "vt-123456789",
                "video_id": "vid-987654321",
                "customer_email": "customer@example.com",
                "customer_name": "John Doe",
                "transaction_type": "premium_feature",
                "transaction_status": "completed",
                "payment_id": "pay-123456789",
                "payment_status": "completed",
                "amount": 29.99,
                "currency": "usd",
                "features": [
                    {
                        "feature_id": "feat-001",
                        "feature_type": "export_4k",
                        "name": "4K Export",
                        "description": "Export video in 4K resolution",
                        "price": 29.99,
                    }
                ],
                "business_entity_id": "the_connection_practice",
                "created_at": "2023-08-01T12:00:00Z",
                "updated_at": "2023-08-01T12:05:00Z",
            }
        }


class VideoTransactionRequest(BaseModel):
    """Request model for creating a video transaction."""

    video_id: str = Field(..., description="ID of the related video content")
    customer_email: EmailStr = Field(..., description="Customer email")
    customer_name: Optional[str] = Field(None, description="Customer name")
    transaction_type: VideoTransactionType = Field(
        ..., description="Type of transaction"
    )
    features: List[VideoFeature] = Field(..., description="Features to purchase")
    business_entity_id: str = Field(..., description="Business entity ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        """Pydantic configuration."""

        schema_extra = {
            "example": {
                "video_id": "vid-987654321",
                "customer_email": "customer@example.com",
                "customer_name": "John Doe",
                "transaction_type": "premium_feature",
                "features": [
                    {
                        "feature_id": "feat-001",
                        "feature_type": "export_4k",
                        "name": "4K Export",
                        "description": "Export video in 4K resolution",
                        "price": 29.99,
                    }
                ],
                "business_entity_id": "the_connection_practice",
            }
        }


class VideoTransactionResponse(BaseModel):
    """Response model for a video transaction request."""

    status: str = Field(..., description="Status of the request (success or error)")
    message: str = Field(..., description="Message describing the result")
    transaction_id: Optional[str] = Field(
        None, description="ID of the created transaction"
    )
    payment_url: Optional[HttpUrl] = Field(
        None, description="URL to complete the payment if required"
    )


class VideoTransactionStatusResponse(BaseModel):
    """Response model for checking the status of a video transaction."""

    status: str = Field(..., description="Status of the request (success or error)")
    transaction_id: str = Field(..., description="ID of the transaction")
    transaction_status: VideoTransactionStatus = Field(
        ..., description="Status of the transaction"
    )
    payment_status: Optional[PipitPaymentStatus] = Field(
        None, description="Status of the payment if applicable"
    )
    video_id: str = Field(..., description="ID of the related video content")
    features: List[VideoFeature] = Field(..., description="Features purchased")
    amount: float = Field(..., description="Transaction amount")
    currency: PipitCurrency = Field(..., description="Transaction currency")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    expires_at: Optional[datetime] = Field(
        None, description="Expiration timestamp if applicable"
    )
    message: Optional[str] = Field(
        None, description="Additional message about the status"
    )
