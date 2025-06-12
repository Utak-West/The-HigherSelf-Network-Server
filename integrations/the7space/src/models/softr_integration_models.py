"""
Pydantic models for Softr to Higher Self Network server integration.
These models define the API contract between Softr interfaces and backend services.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Enum, Field, enum, field_validator


class SoftrIntegrationConfig(BaseModel):
    """Configuration for Softr integration with Higher Self Network Server"""

    server_api_endpoint: str = Field(
        ..., description="Higher Self Network API endpoint"
    )
    api_key: str = Field(..., description="API key for authentication")
    webhook_secret: str = Field(
        ..., description="Secret for webhook signature validation"
    )
    softr_site_id: str = Field(..., description="Softr site identifier")

    class Config:
        env_file = ".env"
        env_prefix = "HIGHERSELF_"


class WebhookEventType(str, Enum):
    """Event types for Softr webhooks"""

    FORM_SUBMISSION = "form_submission"
    USER_REGISTRATION = "user_registration"
    USER_LOGIN = "user_login"
    PAYMENT_RECEIVED = "payment_received"
    BOOKING_CREATED = "booking_created"
    BOOKING_UPDATED = "booking_updated"
    BOOKING_CANCELLED = "booking_cancelled"
    CONTACT_REQUEST = "contact_request"
    ARTWORK_INQUIRY = "artwork_inquiry"


class WebhookPayload(BaseModel):
    """Model for incoming webhook data from Softr"""

    event_type: WebhookEventType
    timestamp: datetime
    site_id: str
    data: Dict[str, Any]
    signature: str

    @field_validator("timestamp", pre=True, mode="before")
    @classmethod
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class FormSubmissionData(BaseModel):
    """Data model for form submissions from Softr"""

    form_id: str
    form_name: str
    user_id: Optional[str] = None
    fields: Dict[str, Any]
    page_url: str
    submission_id: str = Field(default_factory=lambda: str(uuid4()))


class UserRegistrationData(BaseModel):
    """Data model for user registration events from Softr"""

    user_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    membership_level: Optional[str] = None
    registration_date: datetime


class PaymentData(BaseModel):
    """Data model for payment events from Softr"""

    payment_id: str
    user_id: Optional[str] = None
    email: str
    amount: float
    currency: str
    payment_method: str
    status: str
    metadata: Optional[Dict[str, Any]] = None
    items: List[Dict[str, Any]]


class BookingData(BaseModel):
    """Data model for booking events from Softr"""

    booking_id: str
    user_id: Optional[str] = None
    service_id: str
    service_name: str
    practitioner_id: Optional[str] = None
    practitioner_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: str
    payment_status: Optional[str] = None
    notes: Optional[str] = None


class ArtworkInquiryData(BaseModel):
    """Data model for artwork inquiry events from Softr"""

    inquiry_id: str = Field(default_factory=lambda: str(uuid4()))
    artwork_id: str
    artwork_title: str
    artist_name: str
    user_id: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    message: str
    inquiry_type: str  # purchase, commission, more_info


class ContactRequestData(BaseModel):
    """Data model for contact request events from Softr"""

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    email: str
    phone: Optional[str] = None
    subject: Optional[str] = None
    message: str
    interested_in: Optional[List[str]] = None
    how_heard: Optional[str] = None


class ApiResponse(BaseModel):
    """Standard API response model for Higher Self Network server"""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WorkflowTriggerRequest(BaseModel):
    """Request model for triggering workflows in the Higher Self Network"""

    workflow_id: str
    trigger_event: str
    trigger_data: Dict[str, Any]
    source: str = "softr"
    idempotency_key: str = Field(default_factory=lambda: str(uuid4()))


class ArtworkListRequest(BaseModel):
    """Request model for fetching artwork listings"""

    page: int = 1
    limit: int = 20
    sort_by: Optional[str] = None
    sort_direction: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class ArtworkListResponse(BaseModel):
    """Response model for artwork listings"""

    items: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    has_more: bool


class EventListRequest(BaseModel):
    """Request model for fetching event listings"""

    page: int = 1
    limit: int = 20
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_type: Optional[List[str]] = None
    sort_by: Optional[str] = None
    sort_direction: Optional[str] = None


class EventListResponse(BaseModel):
    """Response model for event listings"""

    items: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    has_more: bool


class ServiceBookingRequest(BaseModel):
    """Request model for booking a wellness service"""

    service_id: str
    practitioner_id: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    user_id: Optional[str] = None
    user_email: str
    user_name: str
    user_phone: Optional[str] = None
    notes: Optional[str] = None
    payment_method: Optional[str] = None

    @field_validator("end_time", always=True, mode="before")
    @classmethod
    def set_end_time(cls, v, values):
        if v is None and "start_time" in values:
            # Default to 1 hour if not specified
            return values["start_time"] + datetime.timedelta(hours=1)
        return v


class ServiceBookingResponse(BaseModel):
    """Response model for service booking"""

    booking_id: str
    service_id: str
    practitioner_id: Optional[str]
    start_time: datetime
    end_time: datetime
    status: str
    payment_status: Optional[str]
    payment_link: Optional[str]
    calendar_link: Optional[str]


class EmailSubscriptionRequest(BaseModel):
    """Request model for email list subscription"""

    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    interests: Optional[List[str]] = None
    source: str = "website"
    consent: bool = True


class UserProfileData(BaseModel):
    """User profile data model for Softr integration"""

    user_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    preferences: Optional[Dict[str, Any]] = None
    membership_level: Optional[str] = None
    membership_expiry: Optional[datetime] = None
    custom_fields: Optional[Dict[str, Any]] = None
    last_login: Optional[datetime] = None
    created_at: datetime


class ArtPurchaseRequest(BaseModel):
    """Request model for initiating an art purchase"""

    artwork_id: str
    user_id: Optional[str] = None
    user_email: str
    user_name: str
    user_phone: Optional[str] = None
    shipping_address: Optional[Dict[str, str]] = None
    payment_method: str
    special_instructions: Optional[str] = None
    is_gift: bool = False
    gift_message: Optional[str] = None
    gift_recipient: Optional[Dict[str, str]] = None


class ArtPurchaseResponse(BaseModel):
    """Response model for art purchase initiation"""

    purchase_id: str
    artwork_id: str
    status: str
    payment_status: str
    payment_link: Optional[str]
    estimated_shipping_date: Optional[datetime]
    confirmation_email_sent: bool
