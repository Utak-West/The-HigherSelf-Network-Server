"""
Barter Service for The HigherSelf Network Server.

This service provides comprehensive location-based barter functionality,
including geographic search, cultural adaptation, and transaction management.
"""

import asyncio
import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from loguru import logger

from models.barter_models import (
    BarterAuditLog,
    BarterListing,
    BarterMatch,
    BarterMetric,
    BarterProfile,
    BarterRequest,
    BarterSearchCache,
    BarterTransaction,
    BarterTranslation,
    BarterUserProfile,
    CulturalAdaptation,
    CulturalRegion,
    LanguageCode,
    Location,
    ServiceCategory,
    TranslationEntity,
    VerificationStatus,
)
from services.redis_service import redis_service


class LocationService:
    """Service for location-based operations and geographic calculations."""

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth.

        Args:
            lat1, lon1: Latitude and longitude of first point
            lat2, lon2: Latitude and longitude of second point

        Returns:
            Distance in kilometers
        """
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in kilometers
        r = 6371

        return c * r

    @staticmethod
    def is_within_radius(
        center_lat: float,
        center_lon: float,
        point_lat: float,
        point_lon: float,
        radius_km: float,
    ) -> bool:
        """Check if a point is within a given radius of a center point."""
        distance = LocationService.calculate_distance(
            center_lat, center_lon, point_lat, point_lon
        )
        return distance <= radius_km


class CulturalAdaptationService:
    """Service for cultural adaptation and regional customization."""

    # Regional service preferences
    REGIONAL_PREFERENCES = {
        CulturalRegion.NORTH_AMERICA: {
            "preferred_categories": [
                ServiceCategory.WELLNESS_CONSULTATION,
                ServiceCategory.BUSINESS_STRATEGY,
                ServiceCategory.TECHNOLOGY_CONSULTING,
                ServiceCategory.YOGA_INSTRUCTION,
            ],
            "seasonal_services": {
                "winter": [
                    ServiceCategory.MEDITATION_GUIDANCE,
                    ServiceCategory.ENERGY_HEALING,
                ],
                "spring": [
                    ServiceCategory.GARDENING,
                    ServiceCategory.NUTRITION_COUNSELING,
                ],
                "summer": [
                    ServiceCategory.YOGA_INSTRUCTION,
                    ServiceCategory.PHOTOGRAPHY,
                ],
                "fall": [ServiceCategory.ART_CREATION, ServiceCategory.SKILL_TRAINING],
            },
            "cultural_practices": [
                "mindfulness",
                "holistic_wellness",
                "work_life_balance",
            ],
            "currency_base": "USD",
        },
        CulturalRegion.EUROPE: {
            "preferred_categories": [
                ServiceCategory.ART_CREATION,
                ServiceCategory.TRADITIONAL_HEALING,
                ServiceCategory.LANGUAGE_INSTRUCTION,
                ServiceCategory.CULTURAL_PRACTICES,
            ],
            "seasonal_services": {
                "winter": [
                    ServiceCategory.ART_CREATION,
                    ServiceCategory.SKILL_TRAINING,
                ],
                "spring": [
                    ServiceCategory.GARDENING,
                    ServiceCategory.CULTURAL_PRACTICES,
                ],
                "summer": [
                    ServiceCategory.PHOTOGRAPHY,
                    ServiceCategory.CREATIVE_WORKSHOPS,
                ],
                "fall": [
                    ServiceCategory.TRADITIONAL_HEALING,
                    ServiceCategory.MENTORSHIP,
                ],
            },
            "cultural_practices": [
                "traditional_arts",
                "cultural_heritage",
                "community_focus",
            ],
            "currency_base": "EUR",
        },
        CulturalRegion.ASIA_PACIFIC: {
            "preferred_categories": [
                ServiceCategory.TRADITIONAL_HEALING,
                ServiceCategory.MEDITATION_GUIDANCE,
                ServiceCategory.MARTIAL_ARTS,
                ServiceCategory.SPIRITUAL_GUIDANCE,
            ],
            "seasonal_services": {
                "winter": [
                    ServiceCategory.MEDITATION_GUIDANCE,
                    ServiceCategory.TRADITIONAL_HEALING,
                ],
                "spring": [
                    ServiceCategory.ENERGY_HEALING,
                    ServiceCategory.SPIRITUAL_GUIDANCE,
                ],
                "summer": [
                    ServiceCategory.MARTIAL_ARTS,
                    ServiceCategory.CULTURAL_PRACTICES,
                ],
                "fall": [ServiceCategory.SKILL_TRAINING, ServiceCategory.MENTORSHIP],
            },
            "cultural_practices": ["harmony", "balance", "ancestral_wisdom"],
            "currency_base": "USD",  # Default, varies by country
        },
    }

    @classmethod
    def get_cultural_adaptation(cls, region: CulturalRegion) -> CulturalAdaptation:
        """Get cultural adaptation settings for a region."""
        preferences = cls.REGIONAL_PREFERENCES.get(
            region, cls.REGIONAL_PREFERENCES[CulturalRegion.NORTH_AMERICA]
        )

        return CulturalAdaptation(
            region=region,
            preferred_categories=preferences["preferred_categories"],
            seasonal_services=preferences["seasonal_services"],
            cultural_practices=preferences["cultural_practices"],
            currency_equivalent_base=preferences["currency_base"],
        )

    @classmethod
    def get_seasonal_services(
        cls, region: CulturalRegion, season: str
    ) -> List[ServiceCategory]:
        """Get seasonal service recommendations for a region."""
        preferences = cls.REGIONAL_PREFERENCES.get(
            region, cls.REGIONAL_PREFERENCES[CulturalRegion.NORTH_AMERICA]
        )
        return preferences["seasonal_services"].get(season, [])


class BarterMatchingService:
    """Service for matching barter requests with listings."""

    @staticmethod
    def calculate_compatibility_score(
        listing: BarterListing, request: BarterRequest
    ) -> float:
        """
        Calculate compatibility score between a listing and request.

        Returns:
            Score between 0 and 1, where 1 is perfect match
        """
        score = 0.0

        # Category match (40% weight)
        if listing.category == request.category:
            score += 0.4
        elif request.category in listing.preferred_exchange_types:
            score += 0.3

        # Skill level match (20% weight)
        skill_levels = ["beginner", "intermediate", "advanced", "expert", "master"]
        listing_level = skill_levels.index(listing.skill_level.value)
        preferred_level = skill_levels.index(request.preferred_skill_level.value)

        if listing_level >= preferred_level:
            skill_score = 1.0 - (abs(listing_level - preferred_level) * 0.1)
            score += 0.2 * max(0, skill_score)

        # Value balance (20% weight)
        offered_value = request.offered_value_per_hour * request.offered_total_hours
        requested_value = listing.base_value_per_hour * request.required_total_hours

        if offered_value > 0 and requested_value > 0:
            value_ratio = min(offered_value, requested_value) / max(
                offered_value, requested_value
            )
            score += 0.2 * value_ratio

        # Availability match (10% weight)
        if listing.available_hours_per_week >= request.required_total_hours:
            score += 0.1

        # Virtual availability (10% weight)
        if request.virtual_acceptable and listing.virtual_available:
            score += 0.1
        elif not request.virtual_acceptable and listing.service_radius_km:
            score += 0.1

        return min(1.0, score)

    @staticmethod
    def calculate_cultural_compatibility(
        listing: BarterListing, request: BarterRequest
    ) -> float:
        """Calculate cultural compatibility score."""
        if not listing.cultural_adaptation or not listing.location.cultural_region:
            return 1.0  # Default to compatible if no cultural data

        # Same cultural region
        if (
            listing.location.cultural_region
            == request.preferred_location.cultural_region
        ):
            return 1.0

        # Different regions but compatible practices
        listing_practices = set(listing.cultural_adaptation.cultural_practices)
        request_adaptation = CulturalAdaptationService.get_cultural_adaptation(
            request.preferred_location.cultural_region
        )
        request_practices = set(request_adaptation.cultural_practices)

        if listing_practices & request_practices:  # Intersection
            return 0.8

        return 0.6  # Different but not incompatible


class BarterService:
    """Main barter service for managing the complete barter system."""

    def __init__(self):
        self.location_service = LocationService()
        self.cultural_service = CulturalAdaptationService()
        self.matching_service = BarterMatchingService()
        self.cache_prefix = "barter:"
        self.cache_ttl = 3600  # 1 hour

    async def create_listing(self, listing: BarterListing) -> BarterListing:
        """Create a new barter listing."""
        try:
            # Auto-apply cultural adaptation if not provided
            if not listing.cultural_adaptation:
                listing.cultural_adaptation = (
                    self.cultural_service.get_cultural_adaptation(
                        listing.location.cultural_region
                    )
                )

            # Cache the listing
            cache_key = f"{self.cache_prefix}listing:{listing.id}"
            await redis_service.async_set(
                cache_key, listing.model_dump_json(), ex=self.cache_ttl
            )

            # Add to geographic index
            await self._add_to_geo_index(listing)

            logger.info(f"Created barter listing: {listing.id}")
            return listing

        except Exception as e:
            logger.error(f"Error creating barter listing: {e}")
            raise

    async def _add_to_geo_index(self, listing: BarterListing):
        """Add listing to geographic index for location-based search."""
        if listing.location.latitude and listing.location.longitude:
            geo_key = f"{self.cache_prefix}geo:listings"
            await redis_service.async_geoadd(
                geo_key,
                listing.location.longitude,
                listing.location.latitude,
                str(listing.id),
            )

    async def search_listings(
        self,
        location: Location,
        radius_km: float = 50,
        category: Optional[ServiceCategory] = None,
        cultural_region: Optional[CulturalRegion] = None,
        limit: int = 20,
    ) -> List[BarterListing]:
        """Search for barter listings based on location and criteria."""
        try:
            listings = []

            if location.latitude and location.longitude:
                # Geographic search using Redis
                geo_key = f"{self.cache_prefix}geo:listings"
                nearby_ids = await redis_service.async_georadius(
                    geo_key,
                    location.longitude,
                    location.latitude,
                    radius_km,
                    unit="km",
                    count=limit * 2,  # Get more to filter
                )

                # Fetch and filter listings
                for listing_id in nearby_ids:
                    cache_key = f"{self.cache_prefix}listing:{listing_id}"
                    listing_data = await redis_service.async_get(cache_key)

                    if listing_data:
                        listing = BarterListing.model_validate_json(listing_data)

                        # Apply filters
                        if category and listing.category != category:
                            continue

                        if (
                            cultural_region
                            and listing.location.cultural_region != cultural_region
                        ):
                            continue

                        listings.append(listing)

                        if len(listings) >= limit:
                            break

            logger.info(f"Found {len(listings)} listings within {radius_km}km")
            return listings

        except Exception as e:
            logger.error(f"Error searching listings: {e}")
            return []

    async def create_request(self, request: BarterRequest) -> BarterRequest:
        """Create a new barter request."""
        try:
            # Cache the request
            cache_key = f"{self.cache_prefix}request:{request.id}"
            await redis_service.async_set(
                cache_key, request.model_dump_json(), ex=self.cache_ttl
            )

            logger.info(f"Created barter request: {request.id}")
            return request

        except Exception as e:
            logger.error(f"Error creating barter request: {e}")
            raise

    async def find_matches(
        self, request: BarterRequest, limit: int = 10
    ) -> List[BarterMatch]:
        """Find potential matches for a barter request."""
        try:
            # Search for relevant listings
            listings = await self.search_listings(
                location=request.preferred_location,
                radius_km=request.max_distance_km,
                category=request.category,
                limit=limit * 2,  # Get more to rank
            )

            matches = []

            for listing in listings:
                # Calculate compatibility
                compatibility_score = (
                    self.matching_service.calculate_compatibility_score(
                        listing, request
                    )
                )

                if compatibility_score < 0.3:  # Minimum threshold
                    continue

                # Calculate cultural compatibility
                cultural_score = self.matching_service.calculate_cultural_compatibility(
                    listing, request
                )

                # Calculate distance if coordinates available
                distance_km = None
                if (
                    listing.location.latitude
                    and listing.location.longitude
                    and request.preferred_location.latitude
                    and request.preferred_location.longitude
                ):
                    distance_km = self.location_service.calculate_distance(
                        listing.location.latitude,
                        listing.location.longitude,
                        request.preferred_location.latitude,
                        request.preferred_location.longitude,
                    )

                # Create match
                match = BarterMatch(
                    listing_id=listing.id,
                    request_id=request.id,
                    compatibility_score=compatibility_score,
                    distance_km=distance_km,
                    category_match=(listing.category == request.category),
                    skill_level_match=(
                        listing.skill_level == request.preferred_skill_level
                    ),
                    value_balance_ratio=self._calculate_value_ratio(listing, request),
                    cultural_compatibility_score=cultural_score,
                    suggested_exchange_structure=self._suggest_exchange_structure(
                        listing, request
                    ),
                )

                matches.append(match)

            # Sort by compatibility score
            matches.sort(key=lambda m: m.compatibility_score, reverse=True)

            # Cache matches
            for match in matches[:limit]:
                cache_key = f"{self.cache_prefix}match:{match.id}"
                await redis_service.async_set(
                    cache_key, match.model_dump_json(), ex=self.cache_ttl
                )

            logger.info(
                f"Found {len(matches[:limit])} matches for request {request.id}"
            )
            return matches[:limit]

        except Exception as e:
            logger.error(f"Error finding matches: {e}")
            return []

    def _calculate_value_ratio(
        self, listing: BarterListing, request: BarterRequest
    ) -> float:
        """Calculate the value balance ratio between listing and request."""
        offered_value = request.offered_value_per_hour * request.offered_total_hours
        requested_value = listing.base_value_per_hour * request.required_total_hours

        if offered_value == 0 or requested_value == 0:
            return 0.0

        return min(offered_value, requested_value) / max(offered_value, requested_value)

    def _suggest_exchange_structure(
        self, listing: BarterListing, request: BarterRequest
    ) -> Dict[str, Any]:
        """Suggest an exchange structure for the match."""
        return {
            "provider_service": listing.category.value,
            "provider_hours": request.required_total_hours,
            "requester_service": request.offered_service_category.value,
            "requester_hours": request.offered_total_hours,
            "session_duration": listing.estimated_session_duration,
            "virtual_option": listing.virtual_available and request.virtual_acceptable,
            "estimated_duration_weeks": max(
                1, request.required_total_hours / listing.available_hours_per_week
            ),
        }

    async def create_transaction(
        self, match: BarterMatch, provider_id: str, requester_id: str
    ) -> BarterTransaction:
        """Create a confirmed barter transaction from a match."""
        try:
            # Get the original listing and request
            listing_cache_key = f"{self.cache_prefix}listing:{match.listing_id}"
            request_cache_key = f"{self.cache_prefix}request:{match.request_id}"

            listing_data = await redis_service.async_get(listing_cache_key)
            request_data = await redis_service.async_get(request_cache_key)

            if not listing_data or not request_data:
                raise ValueError("Original listing or request not found")

            listing = BarterListing.model_validate_json(listing_data)
            request = BarterRequest.model_validate_json(request_data)

            # Create transaction
            transaction = BarterTransaction(
                match_id=match.id,
                provider_id=provider_id,
                requester_id=requester_id,
                provider_service={
                    "category": listing.category.value,
                    "description": listing.description,
                    "skill_level": listing.skill_level.value,
                    "value_per_hour": listing.base_value_per_hour,
                },
                requester_service={
                    "category": request.offered_service_category.value,
                    "description": request.offered_service_description,
                    "value_per_hour": request.offered_value_per_hour,
                },
                agreed_provider_hours=request.required_total_hours,
                agreed_requester_hours=request.offered_total_hours,
                total_value_exchanged=listing.base_value_per_hour
                * request.required_total_hours,
                start_date=datetime.now(timezone.utc),
                estimated_completion_date=datetime.now(timezone.utc)
                + timedelta(
                    weeks=int(
                        match.suggested_exchange_structure.get(
                            "estimated_duration_weeks", 4
                        )
                    )
                ),
            )

            # Cache transaction
            cache_key = f"{self.cache_prefix}transaction:{transaction.id}"
            await redis_service.async_set(
                cache_key,
                transaction.model_dump_json(),
                ex=self.cache_ttl * 24,  # Longer cache for transactions
            )

            logger.info(f"Created barter transaction: {transaction.id}")
            return transaction

        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            raise

    async def get_profile(self, entity_id: str) -> Optional[BarterProfile]:
        """Get barter profile for an entity."""
        try:
            cache_key = f"{self.cache_prefix}profile:{entity_id}"
            profile_data = await redis_service.async_get(cache_key)

            if profile_data:
                return BarterProfile.model_validate_json(profile_data)

            return None

        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return None

    async def update_profile(self, profile: BarterProfile) -> BarterProfile:
        """Update or create a barter profile."""
        try:
            cache_key = f"{self.cache_prefix}profile:{profile.entity_id}"
            await redis_service.async_set(
                cache_key,
                profile.model_dump_json(),
                ex=self.cache_ttl * 24,  # Longer cache for profiles
            )

            logger.info(f"Updated barter profile: {profile.entity_id}")
            return profile

        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            raise

    async def get_request(self, request_id: UUID) -> Optional[BarterRequest]:
        """Get a barter request by ID."""
        try:
            cache_key = f"{self.cache_prefix}request:{request_id}"
            request_data = await redis_service.async_get(cache_key)

            if request_data:
                return BarterRequest.model_validate_json(request_data)

            return None

        except Exception as e:
            logger.error(f"Error getting request: {e}")
            return None

    async def get_match(self, match_id: UUID) -> Optional[BarterMatch]:
        """Get a barter match by ID."""
        try:
            cache_key = f"{self.cache_prefix}match:{match_id}"
            match_data = await redis_service.async_get(cache_key)

            if match_data:
                return BarterMatch.model_validate_json(match_data)

            return None

        except Exception as e:
            logger.error(f"Error getting match: {e}")
            return None

    async def get_transaction(
        self, transaction_id: UUID
    ) -> Optional[BarterTransaction]:
        """Get a barter transaction by ID."""
        try:
            cache_key = f"{self.cache_prefix}transaction:{transaction_id}"
            transaction_data = await redis_service.async_get(cache_key)

            if transaction_data:
                return BarterTransaction.model_validate_json(transaction_data)

            return None

        except Exception as e:
            logger.error(f"Error getting transaction: {e}")
            return None

    async def update_transaction(
        self, transaction: BarterTransaction
    ) -> BarterTransaction:
        """Update a barter transaction."""
        try:
            # Update timestamp
            transaction.updated_at = datetime.now(timezone.utc)

            # Cache updated transaction
            cache_key = f"{self.cache_prefix}transaction:{transaction.id}"
            await redis_service.async_set(
                cache_key,
                transaction.model_dump_json(),
                ex=self.cache_ttl * 24,  # Longer cache for transactions
            )

            logger.info(f"Updated barter transaction: {transaction.id}")
            return transaction

        except Exception as e:
            logger.error(f"Error updating transaction: {e}")
            raise
