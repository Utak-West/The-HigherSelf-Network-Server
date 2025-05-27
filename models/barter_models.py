"""
Barter System Models for The HigherSelf Network Server.

This module provides comprehensive models for the location-based barter system,
enabling service exchanges between all network entities with cultural adaptation
and geographic filtering capabilities.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ServiceCategory(str, Enum):
    """Categories of services available for barter."""

    # Wellness & Health
    WELLNESS_CONSULTATION = "wellness_consultation"
    MASSAGE_THERAPY = "massage_therapy"
    YOGA_INSTRUCTION = "yoga_instruction"
    MEDITATION_GUIDANCE = "meditation_guidance"
    NUTRITION_COUNSELING = "nutrition_counseling"
    ENERGY_HEALING = "energy_healing"

    # Art & Creative
    ART_CREATION = "art_creation"
    ART_CURATION = "art_curation"
    PHOTOGRAPHY = "photography"
    GRAPHIC_DESIGN = "graphic_design"
    CREATIVE_WORKSHOPS = "creative_workshops"
    ART_INSTALLATION = "art_installation"

    # Business & Consulting
    BUSINESS_STRATEGY = "business_strategy"
    MARKETING_CONSULTATION = "marketing_consultation"
    FINANCIAL_PLANNING = "financial_planning"
    LEGAL_CONSULTATION = "legal_consultation"
    TECHNOLOGY_CONSULTING = "technology_consulting"
    PROJECT_MANAGEMENT = "project_management"

    # Education & Training
    SKILL_TRAINING = "skill_training"
    LANGUAGE_INSTRUCTION = "language_instruction"
    PROFESSIONAL_DEVELOPMENT = "professional_development"
    MENTORSHIP = "mentorship"
    WORKSHOP_FACILITATION = "workshop_facilitation"

    # Traditional & Cultural
    TRADITIONAL_HEALING = "traditional_healing"
    CULTURAL_PRACTICES = "cultural_practices"
    SPIRITUAL_GUIDANCE = "spiritual_guidance"
    CEREMONIAL_SERVICES = "ceremonial_services"

    # Technical & Digital
    WEB_DEVELOPMENT = "web_development"
    DIGITAL_MARKETING = "digital_marketing"
    CONTENT_CREATION = "content_creation"
    SOCIAL_MEDIA_MANAGEMENT = "social_media_management"

    # Lifestyle & Personal
    PERSONAL_STYLING = "personal_styling"
    HOME_ORGANIZATION = "home_organization"
    GARDENING = "gardening"
    COOKING_INSTRUCTION = "cooking_instruction"

    # Other
    OTHER = "other"


class SkillLevel(str, Enum):
    """Skill levels for service providers."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


class BarterStatus(str, Enum):
    """Status of barter transactions."""

    DRAFT = "draft"
    ACTIVE = "active"
    PENDING_APPROVAL = "pending_approval"
    MATCHED = "matched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class CulturalRegion(str, Enum):
    """Cultural regions for service adaptation."""

    NORTH_AMERICA = "north_america"
    SOUTH_AMERICA = "south_america"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    MIDDLE_EAST = "middle_east"
    AFRICA = "africa"
    OCEANIA = "oceania"


class Location(BaseModel):
    """Geographic location model with cultural context."""

    address: Optional[str] = None
    city: str = Field(..., description="City name")
    state_province: Optional[str] = Field(None, description="State or province")
    country: str = Field(..., description="Country name")
    postal_code: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    cultural_region: CulturalRegion = Field(
        ..., description="Cultural region for adaptation"
    )
    timezone_name: Optional[str] = Field(None, alias="timezone")

    @field_validator("latitude", "longitude")
    @classmethod
    def validate_coordinates(cls, v, info):
        """Ensure both lat and lng are provided together."""
        if v is not None and info.data:
            lat = info.data.get("latitude")
            lng = info.data.get("longitude")
            if (lat is None) != (lng is None):  # XOR - one is None, other is not
                raise ValueError(
                    "Both latitude and longitude must be provided together"
                )
        return v


class CulturalAdaptation(BaseModel):
    """Cultural adaptation settings for regional customization."""

    region: CulturalRegion
    preferred_categories: List[ServiceCategory] = Field(default_factory=list)
    seasonal_services: Dict[str, List[ServiceCategory]] = Field(default_factory=dict)
    cultural_practices: List[str] = Field(default_factory=list)
    local_customs: Dict[str, str] = Field(default_factory=dict)
    language_preferences: List[str] = Field(default_factory=list)
    currency_equivalent_base: str = Field(
        default="USD", description="Base currency for valuations"
    )

    class Config:
        schema_extra = {
            "example": {
                "region": "north_america",
                "preferred_categories": ["wellness_consultation", "yoga_instruction"],
                "seasonal_services": {
                    "winter": ["meditation_guidance", "energy_healing"],
                    "summer": ["outdoor_workshops", "garden_therapy"],
                },
                "cultural_practices": ["mindfulness", "holistic_wellness"],
                "local_customs": {
                    "greeting_style": "warm_professional",
                    "session_duration": "60_minutes_standard",
                },
                "language_preferences": ["english", "spanish"],
                "currency_equivalent_base": "USD",
            }
        }


class BarterListing(BaseModel):
    """A service listing available for barter exchange."""

    id: UUID = Field(default_factory=uuid4)
    provider_id: str = Field(..., description="ID of the service provider")
    provider_type: str = Field(
        ..., description="Type of provider (individual/business)"
    )

    # Service Details
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    category: ServiceCategory
    subcategory: Optional[str] = None
    skill_level: SkillLevel

    # Location & Cultural Context
    location: Location
    service_radius_km: Optional[float] = Field(
        None, description="Service delivery radius in kilometers"
    )
    virtual_available: bool = Field(
        default=False, description="Available for virtual delivery"
    )
    cultural_adaptation: Optional[CulturalAdaptation] = None

    # Availability & Capacity
    available_hours_per_week: float = Field(..., gt=0, le=168)
    estimated_session_duration: float = Field(..., description="Duration in hours")
    max_concurrent_exchanges: int = Field(default=3, ge=1)

    # Valuation
    base_value_per_hour: float = Field(
        ..., description="Base monetary equivalent per hour"
    )
    preferred_exchange_types: List[ServiceCategory] = Field(default_factory=list)

    # Status & Metadata
    status: BarterStatus = Field(default=BarterStatus.DRAFT)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    # Integration
    notion_page_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "provider_id": "provider_123",
                "provider_type": "business",
                "title": "Holistic Wellness Consultation",
                "description": "Comprehensive wellness assessment and personalized guidance",
                "category": "wellness_consultation",
                "skill_level": "expert",
                "location": {
                    "city": "San Francisco",
                    "state_province": "California",
                    "country": "United States",
                    "cultural_region": "north_america",
                },
                "available_hours_per_week": 20,
                "estimated_session_duration": 1.5,
                "base_value_per_hour": 150,
                "preferred_exchange_types": ["massage_therapy", "energy_healing"],
            }
        }


class BarterRequest(BaseModel):
    """A request for a specific service through barter."""

    id: UUID = Field(default_factory=uuid4)
    requester_id: str = Field(..., description="ID of the service requester")
    requester_type: str = Field(
        ..., description="Type of requester (individual/business)"
    )

    # Service Requirements
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    category: ServiceCategory
    preferred_skill_level: SkillLevel = Field(default=SkillLevel.INTERMEDIATE)

    # Location Preferences
    preferred_location: Location
    max_distance_km: float = Field(
        default=50, description="Maximum distance for service provider"
    )
    virtual_acceptable: bool = Field(default=True)

    # Exchange Offer
    offered_service_category: ServiceCategory
    offered_service_description: str
    offered_value_per_hour: float
    offered_total_hours: float

    # Requirements
    required_total_hours: float
    flexible_scheduling: bool = Field(default=True)
    urgency_level: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")

    # Status & Metadata
    status: BarterStatus = Field(default=BarterStatus.ACTIVE)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    # Integration
    notion_page_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "requester_id": "requester_456",
                "requester_type": "individual",
                "title": "Seeking Yoga Instruction",
                "description": "Looking for experienced yoga instructor for weekly sessions",
                "category": "yoga_instruction",
                "preferred_skill_level": "advanced",
                "offered_service_category": "graphic_design",
                "offered_service_description": "Professional logo and branding design",
                "offered_value_per_hour": 100,
                "offered_total_hours": 10,
                "required_total_hours": 8,
            }
        }


class BarterMatch(BaseModel):
    """A potential match between a barter listing and request."""

    id: UUID = Field(default_factory=uuid4)
    listing_id: UUID
    request_id: UUID

    # Match Quality Metrics
    compatibility_score: float = Field(
        ..., ge=0, le=1, description="Overall compatibility score"
    )
    distance_km: Optional[float] = None
    category_match: bool = Field(default=False)
    skill_level_match: bool = Field(default=False)
    value_balance_ratio: float = Field(
        ..., description="Ratio of offered vs requested value"
    )

    # Cultural Compatibility
    cultural_compatibility_score: float = Field(default=1.0, ge=0, le=1)
    language_compatibility: bool = Field(default=True)

    # Match Details
    suggested_exchange_structure: Dict[str, Any] = Field(default_factory=dict)
    estimated_completion_time: Optional[str] = None

    # Status
    status: str = Field(
        default="suggested",
        pattern="^(suggested|viewed|contacted|negotiating|accepted|declined)$",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        schema_extra = {
            "example": {
                "listing_id": "550e8400-e29b-41d4-a716-446655440000",
                "request_id": "550e8400-e29b-41d4-a716-446655440001",
                "compatibility_score": 0.85,
                "distance_km": 12.5,
                "category_match": True,
                "value_balance_ratio": 0.95,
                "suggested_exchange_structure": {
                    "provider_hours": 8,
                    "requester_hours": 10,
                    "session_schedule": "weekly",
                },
            }
        }


class BarterTransaction(BaseModel):
    """A confirmed barter transaction between two parties."""

    id: UUID = Field(default_factory=uuid4)
    match_id: UUID
    provider_id: str
    requester_id: str

    # Service Details
    provider_service: Dict[str, Any] = Field(
        ..., description="Details of provided service"
    )
    requester_service: Dict[str, Any] = Field(
        ..., description="Details of requested service"
    )

    # Agreement Terms
    agreed_provider_hours: float
    agreed_requester_hours: float
    total_value_exchanged: float

    # Schedule & Delivery
    start_date: datetime
    estimated_completion_date: datetime
    actual_completion_date: Optional[datetime] = None

    # Progress Tracking
    provider_progress_percentage: float = Field(default=0, ge=0, le=100)
    requester_progress_percentage: float = Field(default=0, ge=0, le=100)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)

    # Communication
    communication_log: List[Dict[str, Any]] = Field(default_factory=list)

    # Status & Completion
    status: str = Field(
        default="active", pattern="^(active|paused|completed|cancelled|disputed)$"
    )
    completion_notes: Optional[str] = None

    # Reviews & Ratings
    provider_rating: Optional[float] = Field(None, ge=1, le=5)
    requester_rating: Optional[float] = Field(None, ge=1, le=5)
    provider_review: Optional[str] = None
    requester_review: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Integration
    notion_page_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "provider_id": "provider_123",
                "requester_id": "requester_456",
                "provider_service": {
                    "category": "yoga_instruction",
                    "description": "Weekly yoga sessions",
                    "skill_level": "advanced",
                },
                "requester_service": {
                    "category": "graphic_design",
                    "description": "Logo and branding design",
                    "skill_level": "expert",
                },
                "agreed_provider_hours": 8,
                "agreed_requester_hours": 10,
                "total_value_exchanged": 1200,
            }
        }


class BarterProfile(BaseModel):
    """Barter profile for a network entity (individual or business)."""

    entity_id: str = Field(..., description="Unique identifier for the entity")
    entity_type: str = Field(..., pattern="^(individual|business|organization)$")

    # Basic Information
    name: str
    description: Optional[str] = None
    location: Location

    # Service Capabilities
    offered_services: List[ServiceCategory] = Field(default_factory=list)
    skill_levels: Dict[ServiceCategory, SkillLevel] = Field(default_factory=dict)
    service_descriptions: Dict[ServiceCategory, str] = Field(default_factory=dict)

    # Service Needs
    needed_services: List[ServiceCategory] = Field(default_factory=list)
    service_priorities: Dict[ServiceCategory, int] = Field(default_factory=dict)

    # Preferences & Constraints
    max_travel_distance_km: float = Field(default=25)
    virtual_service_preference: bool = Field(default=True)
    preferred_exchange_duration: str = Field(
        default="medium", pattern="^(short|medium|long)$"
    )
    cultural_preferences: Optional[CulturalAdaptation] = None

    # Capacity & Availability
    available_hours_per_week: float = Field(default=10, gt=0, le=168)
    max_concurrent_transactions: int = Field(default=3, ge=1)

    # Performance Metrics
    total_transactions: int = Field(default=0, ge=0)
    average_rating: Optional[float] = Field(None, ge=1, le=5)
    completion_rate: float = Field(default=1.0, ge=0, le=1)
    response_time_hours: Optional[float] = None

    # Status
    active: bool = Field(default=True)
    verified: bool = Field(default=False)
    last_active: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Integration
    notion_page_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "entity_id": "entity_789",
                "entity_type": "business",
                "name": "Wellness Center Downtown",
                "offered_services": ["wellness_consultation", "massage_therapy"],
                "needed_services": ["marketing_consultation", "web_development"],
                "max_travel_distance_km": 50,
                "available_hours_per_week": 30,
                "total_transactions": 15,
                "average_rating": 4.8,
                "completion_rate": 0.95,
            }
        }
