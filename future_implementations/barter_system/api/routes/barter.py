"""
Barter System API Routes for The HigherSelf Network Server.

This module provides comprehensive API endpoints for the location-based barter system,
including listing management, search functionality, matching, and transaction handling.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel

from models.barter_models import (BarterListing, BarterMatch, BarterProfile,
                                  BarterRequest, BarterTransaction,
                                  BarterTranslation, BarterUserProfile,
                                  CulturalRegion, LanguageCode, Location,
                                  ServiceCategory, TranslationEntity,
                                  VerificationStatus)
from services.barter_service import BarterService
from services.barter_translation_service import get_translation_service
from services.barter_user_service import get_barter_user_service

# Create router
router = APIRouter(prefix="/barter", tags=["Barter System"])


# Dependency to get barter service
def get_barter_service() -> BarterService:
    return BarterService()


# Request/Response Models
class SearchRequest(BaseModel):
    """Request model for searching barter listings."""

    location: Location
    radius_km: float = 50
    category: Optional[ServiceCategory] = None
    cultural_region: Optional[CulturalRegion] = None
    limit: int = 20


class MatchRequest(BaseModel):
    """Request model for finding matches."""

    request_id: UUID
    limit: int = 10


class TransactionCreateRequest(BaseModel):
    """Request model for creating a transaction."""

    match_id: UUID
    provider_id: str
    requester_id: str


# Listing Endpoints
@router.post("/listings", response_model=BarterListing)
async def create_listing(
    listing: BarterListing, barter_service: BarterService = Depends(get_barter_service)
):
    """Create a new barter listing."""
    try:
        return await barter_service.create_listing(listing)
    except Exception as e:
        logger.error(f"Error creating listing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/listings/search", response_model=List[BarterListing])
async def search_listings(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    city: str = Query(..., description="City name"),
    country: str = Query(..., description="Country name"),
    cultural_region: CulturalRegion = Query(..., description="Cultural region"),
    radius_km: float = Query(50, description="Search radius in kilometers"),
    category: Optional[ServiceCategory] = Query(
        None, description="Service category filter"
    ),
    limit: int = Query(20, description="Maximum number of results"),
    barter_service: BarterService = Depends(get_barter_service),
):
    """Search for barter listings based on location and criteria."""
    try:
        location = Location(
            city=city,
            country=country,
            latitude=lat,
            longitude=lon,
            cultural_region=cultural_region,
        )

        return await barter_service.search_listings(
            location=location,
            radius_km=radius_km,
            category=category,
            cultural_region=cultural_region,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Error searching listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Request Endpoints
@router.post("/requests", response_model=BarterRequest)
async def create_request(
    request: BarterRequest, barter_service: BarterService = Depends(get_barter_service)
):
    """Create a new barter request."""
    try:
        return await barter_service.create_request(request)
    except Exception as e:
        logger.error(f"Error creating request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/{request_id}/matches", response_model=List[BarterMatch])
async def find_matches(
    request_id: UUID,
    limit: int = Query(10, description="Maximum number of matches"),
    barter_service: BarterService = Depends(get_barter_service),
):
    """Find potential matches for a barter request."""
    try:
        # Get the request from cache
        request = await barter_service.get_request(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        return await barter_service.find_matches(request, limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Transaction Endpoints
@router.post("/transactions", response_model=BarterTransaction)
async def create_transaction(
    transaction_request: TransactionCreateRequest,
    barter_service: BarterService = Depends(get_barter_service),
):
    """Create a confirmed barter transaction from a match."""
    try:
        # Get the match from cache
        match = await barter_service.get_match(transaction_request.match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        return await barter_service.create_transaction(
            match=match,
            provider_id=transaction_request.provider_id,
            requester_id=transaction_request.requester_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{transaction_id}", response_model=BarterTransaction)
async def get_transaction(
    transaction_id: UUID, barter_service: BarterService = Depends(get_barter_service)
):
    """Get a specific barter transaction."""
    try:
        transaction = await barter_service.get_transaction(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        return transaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/transactions/{transaction_id}/progress")
async def update_transaction_progress(
    transaction_id: UUID,
    provider_progress: Optional[float] = None,
    requester_progress: Optional[float] = None,
    barter_service: BarterService = Depends(get_barter_service),
):
    """Update progress on a barter transaction."""
    try:
        transaction = await barter_service.get_transaction(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        if provider_progress is not None:
            transaction.provider_progress_percentage = provider_progress

        if requester_progress is not None:
            transaction.requester_progress_percentage = requester_progress

        return await barter_service.update_transaction(transaction)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating transaction progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Profile Endpoints
@router.get("/profiles/{entity_id}", response_model=BarterProfile)
async def get_profile(
    entity_id: str, barter_service: BarterService = Depends(get_barter_service)
):
    """Get barter profile for an entity."""
    try:
        profile = await barter_service.get_profile(entity_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles", response_model=BarterProfile)
async def create_or_update_profile(
    profile: BarterProfile, barter_service: BarterService = Depends(get_barter_service)
):
    """Create or update a barter profile."""
    try:
        return await barter_service.update_profile(profile)
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Cultural Adaptation Endpoints
@router.get("/cultural-adaptation/{region}")
async def get_cultural_adaptation(
    region: CulturalRegion, barter_service: BarterService = Depends(get_barter_service)
):
    """Get cultural adaptation settings for a region."""
    try:
        adaptation = barter_service.cultural_service.get_cultural_adaptation(region)
        return adaptation
    except Exception as e:
        logger.error(f"Error getting cultural adaptation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cultural-adaptation/{region}/seasonal/{season}")
async def get_seasonal_services(
    region: CulturalRegion,
    season: str,
    barter_service: BarterService = Depends(get_barter_service),
):
    """Get seasonal service recommendations for a region."""
    try:
        services = barter_service.cultural_service.get_seasonal_services(region, season)
        return {"region": region, "season": season, "recommended_services": services}
    except Exception as e:
        logger.error(f"Error getting seasonal services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Enhanced User Profile Endpoints
@router.post("/users/profiles", response_model=BarterUserProfile)
async def create_user_profile(
    user_id: str,
    preferred_language: LanguageCode = LanguageCode.ENGLISH,
    timezone_name: Optional[str] = None,
    user_service=Depends(get_barter_user_service),
):
    """Create a new barter user profile."""
    try:
        profile = await user_service.create_user_profile(
            user_id=user_id,
            preferred_language=preferred_language,
            timezone_name=timezone_name,
        )
        return profile
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/profile", response_model=BarterUserProfile)
async def get_user_profile(user_id: str, user_service=Depends(get_barter_user_service)):
    """Get user profile by user ID."""
    try:
        profile = await user_service.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}/verification")
async def update_verification_status(
    user_id: str,
    status: VerificationStatus,
    user_service=Depends(get_barter_user_service),
):
    """Update user verification status."""
    try:
        success = await user_service.update_verification_status(user_id, status)
        if not success:
            raise HTTPException(status_code=404, detail="User profile not found")
        return {"status": "success", "verification_status": status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating verification status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Translation Endpoints
@router.post("/translations")
async def create_translation(
    entity_type: TranslationEntity,
    entity_id: UUID,
    field_name: str,
    translated_text: str,
    language_code: LanguageCode,
    translation_service=Depends(get_translation_service),
):
    """Create a new translation."""
    try:
        translation = await translation_service.create_translation(
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            translated_text=translated_text,
            language_code=language_code,
        )
        return translation
    except Exception as e:
        logger.error(f"Error creating translation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/translations/{entity_type}/{entity_id}")
async def get_entity_translations(
    entity_type: TranslationEntity,
    entity_id: UUID,
    language_code: LanguageCode,
    translation_service=Depends(get_translation_service),
):
    """Get all translations for an entity in a specific language."""
    try:
        translations = await translation_service.get_entity_translations(
            entity_type=entity_type, entity_id=entity_id, language_code=language_code
        )
        return translations
    except Exception as e:
        logger.error(f"Error getting translations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translations/auto-translate")
async def auto_translate_entity(
    entity_type: TranslationEntity,
    entity_id: UUID,
    target_languages: List[LanguageCode],
    entity_data: dict,
    source_language: Optional[LanguageCode] = None,
    translation_service=Depends(get_translation_service),
):
    """Automatically translate all fields of an entity."""
    try:
        results = await translation_service.auto_translate_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_data=entity_data,
            target_languages=target_languages,
            source_language=source_language,
        )
        return results
    except Exception as e:
        logger.error(f"Error in auto-translation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Enhanced Search Endpoints
@router.get("/search/enhanced")
async def enhanced_search(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius_km: float = Query(50, description="Search radius in kilometers"),
    category: Optional[ServiceCategory] = Query(None, description="Service category"),
    language: LanguageCode = Query(LanguageCode.ENGLISH, description="Language"),
    limit: int = Query(20, description="Maximum results"),
    barter_service: BarterService = Depends(get_barter_service),
):
    """Enhanced search with multi-language support."""
    try:
        # This would use the enhanced search function from the database
        # For now, we'll use the existing search and add language support
        location = Location(
            city="Search Location",
            country="Unknown",
            latitude=lat,
            longitude=lon,
            cultural_region=CulturalRegion.NORTH_AMERICA,  # Default
        )

        listings = await barter_service.search_listings(
            location=location, radius_km=radius_km, category=category, limit=limit
        )

        return {"results": listings, "language": language, "total_count": len(listings)}
    except Exception as e:
        logger.error(f"Error in enhanced search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility Endpoints
@router.get("/categories", response_model=List[str])
async def get_service_categories():
    """Get all available service categories."""
    return [category.value for category in ServiceCategory]


@router.get("/regions", response_model=List[str])
async def get_cultural_regions():
    """Get all available cultural regions."""
    return [region.value for region in CulturalRegion]


@router.get("/health")
async def health_check():
    """Health check endpoint for the barter system."""
    return {"status": "healthy", "service": "barter_system"}
