"""
Pydantic models for The 7 Space Art Gallery & Wellness Center.
These models define the data structures needed for client portals,
sales dashboards, and other visualizations.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Enum, Field, enum, field_validator


class ArtworkStatus(str, Enum):
    """Status of artwork in the gallery"""

    AVAILABLE = "available"
    SOLD = "sold"
    ON_HOLD = "on_hold"
    ON_DISPLAY = "on_display"
    IN_STORAGE = "in_storage"


class EventType(str, Enum):
    """Types of events at The 7 Space"""

    EXHIBITION = "exhibition"
    WORKSHOP = "workshop"
    CLASS = "class"
    MEDITATION = "meditation"
    PRIVATE_EVENT = "private_event"
    COMMUNITY_GATHERING = "community_gathering"
    PERFORMANCE = "performance"


class ServiceType(str, Enum):
    """Types of wellness services offered"""

    YOGA = "yoga"
    MEDITATION = "meditation"
    SOUND_HEALING = "sound_healing"
    ENERGY_WORK = "energy_work"
    COACHING = "coaching"
    BODYWORK = "bodywork"
    CONSULTATION = "consultation"


class Artist(BaseModel):
    """Artist model for The 7 Space gallery"""

    id: UUID
    name: str
    bio: str
    contact_info: Dict[str, str]
    website: Optional[str] = None
    social_media: Optional[Dict[str, str]] = None
    commission_rate: float = Field(..., ge=0.0, le=1.0)
    represented_since: datetime
    artworks: List[UUID] = Field(default_factory=list)
    notion_page_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Jane Doe",
                "bio": "Contemporary artist focusing on abstract expressionism.",
                "contact_info": {"email": "jane@example.com", "phone": "555-123-4567"},
                "website": "https://janedoe.art",
                "social_media": {"instagram": "@janedoeart", "twitter": "@janedoe"},
                "commission_rate": 0.4,
                "represented_since": "2023-01-15T00:00:00Z",
                "notion_page_id": "7a774b0e-9abc-4def-8123-456789012345",
            }
        }


class Artwork(BaseModel):
    """Artwork model for gallery inventory"""

    id: UUID
    title: str
    artist_id: UUID
    description: str
    medium: str
    dimensions: Dict[str, float]  # e.g., {"height": 24, "width": 36, "depth": 2}
    creation_date: Optional[datetime] = None
    acquisition_date: datetime
    price: float
    status: ArtworkStatus
    location: str
    image_urls: List[str]
    tags: List[str] = Field(default_factory=list)
    notion_page_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "title": "Sunset Abstraction",
                "artist_id": "123e4567-e89b-12d3-a456-426614174000",
                "description": "An abstract interpretation of a sunset over water.",
                "medium": "Oil on canvas",
                "dimensions": {"height": 24, "width": 36, "depth": 1.5},
                "creation_date": "2023-05-10T00:00:00Z",
                "acquisition_date": "2023-06-15T00:00:00Z",
                "price": 2500.00,
                "status": "available",
                "location": "Main Gallery - North Wall",
                "image_urls": ["https://example.com/artwork1.jpg"],
                "tags": ["abstract", "landscape", "warm colors"],
                "notion_page_id": "8b774b0e-9abc-4def-8123-456789012346",
            }
        }


class Client(BaseModel):
    """Client model for patrons and collectors"""

    id: UUID
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    preferences: List[str] = Field(default_factory=list)
    acquisition_history: List[UUID] = Field(default_factory=list)
    event_attendance: List[UUID] = Field(default_factory=list)
    notes: Optional[str] = None
    membership_level: Optional[str] = None
    membership_start: Optional[datetime] = None
    membership_end: Optional[datetime] = None
    marketing_preferences: Dict[str, bool] = Field(default_factory=dict)
    notion_page_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "name": "John Smith",
                "email": "john@example.com",
                "phone": "555-987-6543",
                "address": {
                    "street": "123 Art Lover Lane",
                    "city": "Creativeville",
                    "state": "CA",
                    "zip": "94123",
                },
                "preferences": ["abstract", "sculpture", "photography"],
                "acquisition_history": ["123e4567-e89b-12d3-a456-426614174001"],
                "marketing_preferences": {
                    "email": True,
                    "sms": False,
                    "physical_mail": True,
                },
                "notion_page_id": "9c774b0e-9abc-4def-8123-456789012347",
            }
        }


class Sale(BaseModel):
    """Sales record model"""

    id: UUID
    artwork_id: UUID
    client_id: UUID
    sale_date: datetime
    price: float
    payment_method: str
    commission_paid: float
    taxes: float
    shipping_cost: Optional[float] = None
    shipping_address: Optional[Dict[str, str]] = None
    notes: Optional[str] = None
    invoice_number: str
    notion_page_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "artwork_id": "123e4567-e89b-12d3-a456-426614174001",
                "client_id": "123e4567-e89b-12d3-a456-426614174002",
                "sale_date": "2023-07-20T14:30:00Z",
                "price": 2500.00,
                "payment_method": "credit_card",
                "commission_paid": 1000.00,
                "taxes": 206.25,
                "shipping_cost": 150.00,
                "invoice_number": "INV-2023-0042",
                "notion_page_id": "1d774b0e-9abc-4def-8123-456789012348",
            }
        }


class Event(BaseModel):
    """Event model for exhibitions, workshops, classes, etc."""

    id: UUID
    title: str
    description: str
    event_type: EventType
    start_datetime: datetime
    end_datetime: datetime
    facilitator: Optional[str] = None
    capacity: int
    price: Optional[float] = None
    registered_clients: List[UUID] = Field(default_factory=list)
    location: str = "The 7 Space Main Gallery"
    materials_provided: Optional[List[str]] = None
    materials_to_bring: Optional[List[str]] = None
    image_url: Optional[str] = None
    notion_page_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174004",
                "title": "Watercolor Basics Workshop",
                "description": "Learn the fundamentals of watercolor painting techniques.",
                "event_type": "workshop",
                "start_datetime": "2023-08-15T13:00:00Z",
                "end_datetime": "2023-08-15T16:00:00Z",
                "facilitator": "Jane Doe",
                "capacity": 12,
                "price": 75.00,
                "location": "The 7 Space Workshop Room",
                "materials_provided": ["watercolor paper", "paint samples", "brushes"],
                "materials_to_bring": ["water container", "pencil", "eraser"],
                "image_url": "https://example.com/workshop.jpg",
                "notion_page_id": "2e774b0e-9abc-4def-8123-456789012349",
            }
        }


class WellnessService(BaseModel):
    """Model for wellness services offered"""

    id: UUID
    name: str
    description: str
    service_type: ServiceType
    duration_minutes: int
    price: float
    practitioner: str
    availability: Dict[
        str, List[str]
    ]  # e.g., {"Monday": ["10:00-12:00", "14:00-16:00"]}
    location: str = "The 7 Space Wellness Room"
    image_url: Optional[str] = None
    notion_page_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174005",
                "name": "Restorative Yoga",
                "description": "A gentle yoga practice focused on relaxation and recovery.",
                "service_type": "yoga",
                "duration_minutes": 75,
                "price": 25.00,
                "practitioner": "Sarah Johnson",
                "availability": {
                    "Monday": ["10:00-11:15", "17:30-18:45"],
                    "Wednesday": ["10:00-11:15", "17:30-18:45"],
                    "Friday": ["10:00-11:15"],
                },
                "image_url": "https://example.com/restorative-yoga.jpg",
                "notion_page_id": "3f774b0e-9abc-4def-8123-456789012350",
            }
        }


class Booking(BaseModel):
    """Model for service bookings"""

    id: UUID
    service_id: UUID
    client_id: UUID
    booking_datetime: datetime
    duration_minutes: int
    payment_status: str
    payment_amount: float
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    notion_page_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174006",
                "service_id": "123e4567-e89b-12d3-a456-426614174005",
                "client_id": "123e4567-e89b-12d3-a456-426614174002",
                "booking_datetime": "2023-08-21T10:00:00Z",
                "duration_minutes": 75,
                "payment_status": "paid",
                "payment_amount": 25.00,
                "payment_method": "credit_card",
                "notion_page_id": "4g774b0e-9abc-4def-8123-456789012351",
            }
        }


class Expense(BaseModel):
    """Model for tracking gallery and wellness center expenses"""

    id: UUID
    date: datetime
    amount: float
    category: str
    description: str
    vendor: str
    payment_method: str
    receipt_url: Optional[str] = None
    notion_page_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174007",
                "date": "2023-08-01T00:00:00Z",
                "amount": 350.00,
                "category": "supplies",
                "description": "Art supplies for workshop",
                "vendor": "Artist Supply Co.",
                "payment_method": "business_credit_card",
                "receipt_url": "https://example.com/receipt.pdf",
                "notion_page_id": "5h774b0e-9abc-4def-8123-456789012352",
            }
        }


class DashboardConfig(BaseModel):
    """Configuration for dashboard visualizations"""

    id: UUID
    name: str
    type: str  # "sales", "client", "inventory", "events", "wellness", "financial"
    components: List[Dict[str, Any]]
    filters: Optional[Dict[str, Any]] = None
    refresh_interval_minutes: int = 60
    access_roles: List[str] = ["admin"]
    notion_database_ids: Dict[str, str]

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174008",
                "name": "Sales Overview",
                "type": "sales",
                "components": [
                    {
                        "type": "chart",
                        "chart_type": "bar",
                        "title": "Monthly Sales",
                        "data_source": "sales_by_month",
                    },
                    {
                        "type": "metric",
                        "title": "Total Revenue YTD",
                        "data_source": "revenue_ytd",
                    },
                ],
                "filters": {
                    "date_range": {"start": "2023-01-01", "end": "2023-12-31"},
                    "categories": ["painting", "sculpture", "photography"],
                },
                "refresh_interval_minutes": 120,
                "access_roles": ["admin", "manager"],
                "notion_database_ids": {
                    "sales": "8b774b0e-9abc-4def-8123-456789012353",
                    "artworks": "8b774b0e-9abc-4def-8123-456789012354",
                },
            }
        }


class The7SpacePortalConfig(BaseModel):
    """Configuration for The 7 Space web portal"""

    site_name: str = "The 7 Space | Art Gallery & Wellness Center"
    logo_url: str
    primary_color: str = "#4A6274"
    secondary_color: str = "#F9A26C"
    accent_color: str = "#9BBEC8"
    font_family: str = "Montserrat, sans-serif"
    notion_integration_config: Dict[str, str]
    enable_online_sales: bool = True
    enable_class_booking: bool = True
    enable_client_portal: bool = True
    analytics_tracking_id: Optional[str] = None
    social_media: Dict[str, str]
    contact_info: Dict[str, str]
    about_text: str

    class Config:
        schema_extra = {
            "example": {
                "logo_url": "https://the7space.com/logo.png",
                "primary_color": "#4A6274",
                "secondary_color": "#F9A26C",
                "notion_integration_config": {
                    "artworks_database_id": "8b774b0e-9abc-4def-8123-456789012354",
                    "events_database_id": "8b774b0e-9abc-4def-8123-456789012355",
                    "services_database_id": "8b774b0e-9abc-4def-8123-456789012356",
                },
                "social_media": {
                    "instagram": "https://instagram.com/the7space",
                    "facebook": "https://facebook.com/the7space",
                },
                "contact_info": {
                    "email": "info@the7space.com",
                    "phone": "555-123-7777",
                    "address": "123 Creativity Lane, Artville, CA 94123",
                },
                "about_text": "The 7 Space is a unique art gallery and wellness center...",
            }
        }


class ClientPortalUser(BaseModel):
    """User model for client portal access"""

    id: UUID
    client_id: UUID
    email: str
    password_hash: str
    first_name: str
    last_name: str
    last_login: Optional[datetime] = None
    account_created: datetime
    preferences: Dict[str, Any] = Field(default_factory=dict)
    notification_settings: Dict[str, bool] = Field(default_factory=dict)
    notion_page_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174009",
                "client_id": "123e4567-e89b-12d3-a456-426614174002",
                "email": "john@example.com",
                "password_hash": "[hashed_password]",
                "first_name": "John",
                "last_name": "Smith",
                "last_login": "2023-08-20T14:30:00Z",
                "account_created": "2023-06-15T10:00:00Z",
                "preferences": {
                    "theme": "light",
                    "interests": ["abstract", "sculpture"],
                },
                "notification_settings": {
                    "email_new_artwork": True,
                    "email_events": True,
                    "sms_reminders": False,
                },
                "notion_page_id": "6i774b0e-9abc-4def-8123-456789012357",
            }
        }
