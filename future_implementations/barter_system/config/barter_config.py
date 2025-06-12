"""
Configuration settings for the HigherSelf Network Barter System.

This module contains all configuration parameters for the barter system
including caching, geographic search, cultural adaptation, and integration settings.
"""

import os
from typing import Dict, List

from pydantic import BaseSettings, Field

from models.barter_models import CulturalRegion, ServiceCategory


class BarterSystemConfig(BaseSettings):
    """Configuration for the barter system."""

    # Redis Configuration
    redis_cache_ttl: int = Field(
        default=3600, description="Default cache TTL in seconds"
    )
    redis_geo_cache_ttl: int = Field(
        default=7200, description="Geographic cache TTL in seconds"
    )
    redis_notification_ttl: int = Field(
        default=604800, description="Notification cache TTL (7 days)"
    )

    # Geographic Search Configuration
    default_search_radius_km: float = Field(
        default=50.0, description="Default search radius in kilometers"
    )
    max_search_radius_km: float = Field(
        default=500.0, description="Maximum allowed search radius"
    )
    min_search_radius_km: float = Field(
        default=1.0, description="Minimum search radius"
    )

    # Matching Algorithm Configuration
    min_compatibility_score: float = Field(
        default=0.3, description="Minimum compatibility score for matches"
    )
    max_matches_per_request: int = Field(
        default=20, description="Maximum matches to return per request"
    )

    # Cultural Adaptation Configuration
    enable_cultural_adaptation: bool = Field(
        default=True, description="Enable cultural adaptation features"
    )
    enable_seasonal_recommendations: bool = Field(
        default=True, description="Enable seasonal service recommendations"
    )

    # Transaction Configuration
    default_transaction_duration_weeks: int = Field(
        default=4, description="Default transaction duration"
    )
    max_concurrent_transactions: int = Field(
        default=10, description="Maximum concurrent transactions per entity"
    )

    # Notification Configuration
    enable_notifications: bool = Field(
        default=True, description="Enable notification system"
    )
    notification_batch_size: int = Field(
        default=100, description="Batch size for notification processing"
    )

    # API Configuration
    api_rate_limit_per_minute: int = Field(
        default=60, description="API rate limit per minute per user"
    )
    api_max_results_per_page: int = Field(
        default=50, description="Maximum results per API page"
    )

    # Integration Configuration
    notion_integration_enabled: bool = Field(
        default=True, description="Enable Notion integration"
    )
    webhook_timeout_seconds: int = Field(
        default=30, description="Webhook timeout in seconds"
    )

    # Security Configuration
    require_profile_verification: bool = Field(
        default=False, description="Require profile verification for transactions"
    )
    enable_location_privacy: bool = Field(
        default=True, description="Enable location privacy features"
    )

    # Performance Configuration
    enable_caching: bool = Field(default=True, description="Enable Redis caching")
    cache_warm_up_on_startup: bool = Field(
        default=True, description="Warm up cache on startup"
    )

    class Config:
        env_prefix = "BARTER_"
        case_sensitive = False


class CulturalAdaptationConfig:
    """Configuration for cultural adaptation features."""

    # Regional service preferences
    REGIONAL_SERVICE_WEIGHTS: Dict[CulturalRegion, Dict[ServiceCategory, float]] = {
        CulturalRegion.NORTH_AMERICA: {
            ServiceCategory.WELLNESS_CONSULTATION: 1.2,
            ServiceCategory.BUSINESS_STRATEGY: 1.3,
            ServiceCategory.TECHNOLOGY_CONSULTING: 1.4,
            ServiceCategory.YOGA_INSTRUCTION: 1.1,
            ServiceCategory.TRADITIONAL_HEALING: 0.8,
        },
        CulturalRegion.EUROPE: {
            ServiceCategory.ART_CREATION: 1.3,
            ServiceCategory.TRADITIONAL_HEALING: 1.2,
            ServiceCategory.LANGUAGE_INSTRUCTION: 1.2,
            ServiceCategory.CULTURAL_PRACTICES: 1.4,
            ServiceCategory.TECHNOLOGY_CONSULTING: 0.9,
        },
        CulturalRegion.ASIA_PACIFIC: {
            ServiceCategory.TRADITIONAL_HEALING: 1.5,
            ServiceCategory.MEDITATION_GUIDANCE: 1.4,
            ServiceCategory.SPIRITUAL_GUIDANCE: 1.3,
            ServiceCategory.ENERGY_HEALING: 1.2,
            ServiceCategory.BUSINESS_STRATEGY: 0.9,
        },
        CulturalRegion.SOUTH_AMERICA: {
            ServiceCategory.TRADITIONAL_HEALING: 1.3,
            ServiceCategory.ART_CREATION: 1.2,
            ServiceCategory.CULTURAL_PRACTICES: 1.3,
            ServiceCategory.SPIRITUAL_GUIDANCE: 1.2,
            ServiceCategory.TECHNOLOGY_CONSULTING: 0.8,
        },
        CulturalRegion.MIDDLE_EAST: {
            ServiceCategory.TRADITIONAL_HEALING: 1.2,
            ServiceCategory.SPIRITUAL_GUIDANCE: 1.3,
            ServiceCategory.CULTURAL_PRACTICES: 1.2,
            ServiceCategory.BUSINESS_STRATEGY: 1.1,
            ServiceCategory.LANGUAGE_INSTRUCTION: 1.1,
        },
        CulturalRegion.AFRICA: {
            ServiceCategory.TRADITIONAL_HEALING: 1.4,
            ServiceCategory.CULTURAL_PRACTICES: 1.3,
            ServiceCategory.ART_CREATION: 1.2,
            ServiceCategory.SPIRITUAL_GUIDANCE: 1.2,
            ServiceCategory.TECHNOLOGY_CONSULTING: 0.7,
        },
        CulturalRegion.OCEANIA: {
            ServiceCategory.WELLNESS_CONSULTATION: 1.2,
            ServiceCategory.TRADITIONAL_HEALING: 1.1,
            ServiceCategory.ART_CREATION: 1.1,
            ServiceCategory.SPIRITUAL_GUIDANCE: 1.1,
            ServiceCategory.TECHNOLOGY_CONSULTING: 0.9,
        },
    }

    # Language preferences by region
    REGIONAL_LANGUAGES: Dict[CulturalRegion, List[str]] = {
        CulturalRegion.NORTH_AMERICA: ["english", "spanish", "french"],
        CulturalRegion.SOUTH_AMERICA: ["spanish", "portuguese", "english"],
        CulturalRegion.EUROPE: [
            "english",
            "french",
            "german",
            "spanish",
            "italian",
            "dutch",
        ],
        CulturalRegion.ASIA_PACIFIC: [
            "english",
            "mandarin",
            "japanese",
            "korean",
            "hindi",
        ],
        CulturalRegion.MIDDLE_EAST: [
            "arabic",
            "english",
            "persian",
            "turkish",
            "hebrew",
        ],
        CulturalRegion.AFRICA: ["english", "french", "arabic", "swahili", "portuguese"],
        CulturalRegion.OCEANIA: ["english"],
    }

    # Currency preferences by region
    REGIONAL_CURRENCIES: Dict[CulturalRegion, str] = {
        CulturalRegion.NORTH_AMERICA: "USD",
        CulturalRegion.SOUTH_AMERICA: "USD",
        CulturalRegion.EUROPE: "EUR",
        CulturalRegion.ASIA_PACIFIC: "USD",
        CulturalRegion.MIDDLE_EAST: "USD",
        CulturalRegion.AFRICA: "USD",
        CulturalRegion.OCEANIA: "AUD",
    }


class MatchingAlgorithmConfig:
    """Configuration for the matching algorithm."""

    # Scoring weights for compatibility calculation
    CATEGORY_MATCH_WEIGHT: float = 0.4
    SKILL_LEVEL_WEIGHT: float = 0.2
    VALUE_BALANCE_WEIGHT: float = 0.2
    AVAILABILITY_WEIGHT: float = 0.1
    VIRTUAL_AVAILABILITY_WEIGHT: float = 0.1

    # Cultural compatibility weights
    CULTURAL_REGION_MATCH_WEIGHT: float = 0.6
    CULTURAL_PRACTICES_WEIGHT: float = 0.3
    LANGUAGE_COMPATIBILITY_WEIGHT: float = 0.1

    # Distance scoring parameters
    DISTANCE_PENALTY_START_KM: float = 25.0  # Distance where penalty starts
    DISTANCE_PENALTY_MAX_KM: float = 100.0  # Distance where penalty is maximum
    MAX_DISTANCE_PENALTY: float = 0.3  # Maximum penalty for distance

    # Skill level compatibility matrix
    SKILL_LEVEL_COMPATIBILITY: Dict[str, Dict[str, float]] = {
        "beginner": {
            "beginner": 1.0,
            "intermediate": 0.8,
            "advanced": 0.6,
            "expert": 0.4,
            "master": 0.2,
        },
        "intermediate": {
            "beginner": 0.9,
            "intermediate": 1.0,
            "advanced": 0.9,
            "expert": 0.7,
            "master": 0.5,
        },
        "advanced": {
            "beginner": 0.7,
            "intermediate": 0.9,
            "advanced": 1.0,
            "expert": 0.9,
            "master": 0.7,
        },
        "expert": {
            "beginner": 0.5,
            "intermediate": 0.7,
            "advanced": 0.9,
            "expert": 1.0,
            "master": 0.9,
        },
        "master": {
            "beginner": 0.3,
            "intermediate": 0.5,
            "advanced": 0.7,
            "expert": 0.9,
            "master": 1.0,
        },
    }


class NotificationConfig:
    """Configuration for the notification system."""

    # Notification priorities and their delivery settings
    PRIORITY_SETTINGS = {
        "low": {
            "channels": ["in_app"],
            "delay_minutes": 60,
            "batch_allowed": True,
        },
        "normal": {
            "channels": ["in_app", "email"],
            "delay_minutes": 15,
            "batch_allowed": True,
        },
        "high": {
            "channels": ["in_app", "email", "push"],
            "delay_minutes": 0,
            "batch_allowed": False,
        },
        "urgent": {
            "channels": ["in_app", "email", "push", "sms"],
            "delay_minutes": 0,
            "batch_allowed": False,
        },
    }

    # Notification templates
    TEMPLATES = {
        "new_match_found": {
            "subject": "New Barter Match Found!",
            "template": "new_match_notification.html",
            "priority": "high",
        },
        "match_accepted": {
            "subject": "Your Barter Match Was Accepted!",
            "template": "match_accepted_notification.html",
            "priority": "high",
        },
        "transaction_created": {
            "subject": "Barter Transaction Started",
            "template": "transaction_created_notification.html",
            "priority": "normal",
        },
        "transaction_completed": {
            "subject": "Barter Exchange Completed!",
            "template": "transaction_completed_notification.html",
            "priority": "high",
        },
    }


class SecurityConfig:
    """Security configuration for the barter system."""

    # Rate limiting
    RATE_LIMITS = {
        "search_listings": {"requests": 30, "window": 60},  # 30 requests per minute
        "create_listing": {"requests": 10, "window": 60},  # 10 listings per minute
        "create_request": {"requests": 10, "window": 60},  # 10 requests per minute
        "find_matches": {"requests": 20, "window": 60},  # 20 match searches per minute
    }

    # Data validation
    MAX_DESCRIPTION_LENGTH: int = 2000
    MAX_TITLE_LENGTH: int = 200
    MAX_TAGS_PER_LISTING: int = 10
    MAX_PREFERRED_EXCHANGE_TYPES: int = 5

    # Location privacy
    LOCATION_PRECISION_METERS: float = 1000.0  # Round location to nearest 1km
    HIDE_EXACT_LOCATION: bool = True

    # Profile verification requirements
    VERIFICATION_REQUIRED_FOR_HIGH_VALUE: float = (
        1000.0  # Require verification for high-value exchanges
    )
    VERIFICATION_REQUIRED_FOR_BUSINESS: bool = True


# Global configuration instance
barter_config = BarterSystemConfig()


# Configuration validation
def validate_config():
    """Validate configuration settings."""
    errors = []

    if barter_config.min_search_radius_km >= barter_config.max_search_radius_km:
        errors.append("min_search_radius_km must be less than max_search_radius_km")

    if (
        barter_config.min_compatibility_score < 0
        or barter_config.min_compatibility_score > 1
    ):
        errors.append("min_compatibility_score must be between 0 and 1")

    if barter_config.max_matches_per_request <= 0:
        errors.append("max_matches_per_request must be positive")

    if errors:
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

    return True


# Validate configuration on import
validate_config()


def get_barter_config() -> BarterSystemConfig:
    """Get the global barter system configuration."""
    return barter_config


def get_cultural_config() -> CulturalAdaptationConfig:
    """Get the cultural adaptation configuration."""
    return CulturalAdaptationConfig()


def get_matching_config() -> MatchingAlgorithmConfig:
    """Get the matching algorithm configuration."""
    return MatchingAlgorithmConfig()


def get_notification_config() -> NotificationConfig:
    """Get the notification configuration."""
    return NotificationConfig()


def get_security_config() -> SecurityConfig:
    """Get the security configuration."""
    return SecurityConfig()


# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "development":
    barter_config.redis_cache_ttl = 300  # Shorter cache in development
    barter_config.require_profile_verification = False
    barter_config.api_rate_limit_per_minute = 120  # Higher rate limit for development

elif os.getenv("ENVIRONMENT") == "production":
    barter_config.require_profile_verification = True
    barter_config.enable_location_privacy = True
    barter_config.api_rate_limit_per_minute = 30  # Lower rate limit for production
