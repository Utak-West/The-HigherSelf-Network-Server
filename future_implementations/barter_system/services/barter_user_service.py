"""
User Profile Service for the HigherSelf Network Barter System.

This service manages user profiles, authentication integration, verification,
and user-specific settings for the barter system.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from loguru import logger

from models.barter_models import (
    BarterUserProfile,
    BarterProfile,
    BarterNotificationPreference,
    LanguageCode,
    VerificationStatus,
    NotificationFrequency,
)
from services.redis_service import redis_service


class BarterUserService:
    """Service for managing barter user profiles and authentication integration."""

    def __init__(self):
        self.cache_prefix = "barter:user:"
        self.cache_ttl = 3600  # 1 hour
        self.verification_cache_ttl = 86400  # 24 hours

    async def create_user_profile(
        self,
        user_id: str,
        preferred_language: LanguageCode = LanguageCode.ENGLISH,
        timezone_name: Optional[str] = None,
        notification_preferences: Optional[Dict[str, Any]] = None,
        privacy_settings: Optional[Dict[str, Any]] = None
    ) -> BarterUserProfile:
        """
        Create a new barter user profile.
        
        Args:
            user_id: Main system user ID
            preferred_language: User's preferred language
            timezone_name: User's timezone
            notification_preferences: Notification settings
            privacy_settings: Privacy settings
            
        Returns:
            Created user profile
        """
        try:
            user_profile = BarterUserProfile(
                user_id=user_id,
                preferred_language=preferred_language,
                timezone_name=timezone_name,
                notification_preferences=notification_preferences or {},
                privacy_settings=privacy_settings or self._get_default_privacy_settings(),
                verification_status=VerificationStatus.PENDING
            )
            
            # Cache the profile
            cache_key = f"{self.cache_prefix}profile:{user_id}"
            await redis_service.async_set(
                cache_key,
                user_profile.model_dump_json(),
                ex=self.cache_ttl
            )
            
            # Create default notification preferences
            await self._create_default_notification_preferences(user_id)
            
            logger.info(f"Created barter user profile for user {user_id}")
            return user_profile

        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            raise

    async def get_user_profile(self, user_id: str) -> Optional[BarterUserProfile]:
        """
        Get user profile by user ID.
        
        Args:
            user_id: Main system user ID
            
        Returns:
            User profile if found
        """
        try:
            cache_key = f"{self.cache_prefix}profile:{user_id}"
            cached_data = await redis_service.async_get(cache_key)
            
            if cached_data:
                return BarterUserProfile.model_validate_json(cached_data)
            
            # If not in cache, would query database here
            return None

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None

    async def update_user_profile(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[BarterUserProfile]:
        """
        Update user profile with new data.
        
        Args:
            user_id: Main system user ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated user profile
        """
        try:
            user_profile = await self.get_user_profile(user_id)
            if not user_profile:
                return None
            
            # Update fields
            for field, value in updates.items():
                if hasattr(user_profile, field):
                    setattr(user_profile, field, value)
            
            user_profile.updated_at = datetime.now(timezone.utc)
            
            # Update cache
            cache_key = f"{self.cache_prefix}profile:{user_id}"
            await redis_service.async_set(
                cache_key,
                user_profile.model_dump_json(),
                ex=self.cache_ttl
            )
            
            logger.info(f"Updated user profile for user {user_id}")
            return user_profile

        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return None

    async def link_barter_profile(
        self,
        user_id: str,
        barter_profile_id: UUID
    ) -> bool:
        """
        Link a barter profile to a user profile.
        
        Args:
            user_id: Main system user ID
            barter_profile_id: Barter profile UUID
            
        Returns:
            Success status
        """
        try:
            updates = {"barter_profile_id": barter_profile_id}
            user_profile = await self.update_user_profile(user_id, updates)
            
            if user_profile:
                logger.info(f"Linked barter profile {barter_profile_id} to user {user_id}")
                return True
            
            return False

        except Exception as e:
            logger.error(f"Error linking barter profile: {e}")
            return False

    async def update_verification_status(
        self,
        user_id: str,
        status: VerificationStatus,
        verification_documents: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Update user verification status.
        
        Args:
            user_id: Main system user ID
            status: New verification status
            verification_documents: Supporting documents
            
        Returns:
            Success status
        """
        try:
            updates = {
                "verification_status": status,
                "verification_documents": verification_documents or []
            }
            
            user_profile = await self.update_user_profile(user_id, updates)
            
            if user_profile:
                # Cache verification status separately for quick access
                verification_cache_key = f"{self.cache_prefix}verification:{user_id}"
                await redis_service.async_set(
                    verification_cache_key,
                    status.value,
                    ex=self.verification_cache_ttl
                )
                
                logger.info(f"Updated verification status for user {user_id} to {status}")
                return True
            
            return False

        except Exception as e:
            logger.error(f"Error updating verification status: {e}")
            return False

    async def is_user_verified(self, user_id: str) -> bool:
        """
        Check if user is verified.
        
        Args:
            user_id: Main system user ID
            
        Returns:
            Verification status
        """
        try:
            # Check cache first
            verification_cache_key = f"{self.cache_prefix}verification:{user_id}"
            cached_status = await redis_service.async_get(verification_cache_key)
            
            if cached_status:
                return cached_status == VerificationStatus.VERIFIED.value
            
            # Get from user profile
            user_profile = await self.get_user_profile(user_id)
            if user_profile:
                return user_profile.verification_status == VerificationStatus.VERIFIED
            
            return False

        except Exception as e:
            logger.error(f"Error checking verification status: {e}")
            return False

    async def get_notification_preferences(
        self,
        user_id: str
    ) -> List[BarterNotificationPreference]:
        """
        Get user's notification preferences.
        
        Args:
            user_id: Main system user ID
            
        Returns:
            List of notification preferences
        """
        try:
            cache_key = f"{self.cache_prefix}notifications:{user_id}"
            cached_data = await redis_service.async_get(cache_key, as_json=True)
            
            if cached_data:
                return [
                    BarterNotificationPreference.model_validate(pref)
                    for pref in cached_data
                ]
            
            # Return default preferences if none found
            return await self._create_default_notification_preferences(user_id)

        except Exception as e:
            logger.error(f"Error getting notification preferences: {e}")
            return []

    async def update_notification_preference(
        self,
        user_id: str,
        notification_type: str,
        enabled: bool,
        channels: Optional[List[str]] = None,
        frequency: Optional[NotificationFrequency] = None
    ) -> bool:
        """
        Update a specific notification preference.
        
        Args:
            user_id: Main system user ID
            notification_type: Type of notification
            enabled: Whether notification is enabled
            channels: Notification channels
            frequency: Notification frequency
            
        Returns:
            Success status
        """
        try:
            preferences = await self.get_notification_preferences(user_id)
            
            # Find existing preference or create new one
            existing_pref = None
            for pref in preferences:
                if pref.notification_type == notification_type:
                    existing_pref = pref
                    break
            
            if existing_pref:
                existing_pref.enabled = enabled
                if channels:
                    existing_pref.channels = channels
                if frequency:
                    existing_pref.frequency = frequency
                existing_pref.updated_at = datetime.now(timezone.utc)
            else:
                new_pref = BarterNotificationPreference(
                    user_id=user_id,
                    notification_type=notification_type,
                    enabled=enabled,
                    channels=channels or ["in_app"],
                    frequency=frequency or NotificationFrequency.IMMEDIATE
                )
                preferences.append(new_pref)
            
            # Update cache
            cache_key = f"{self.cache_prefix}notifications:{user_id}"
            preferences_data = [pref.model_dump() for pref in preferences]
            await redis_service.async_set(
                cache_key,
                preferences_data,
                ex=self.cache_ttl
            )
            
            logger.info(f"Updated notification preference for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating notification preference: {e}")
            return False

    def _get_default_privacy_settings(self) -> Dict[str, Any]:
        """Get default privacy settings for new users."""
        return {
            "location_precision": "approximate",  # exact, approximate, city_only
            "show_real_name": False,
            "show_contact_info": False,
            "allow_direct_contact": True,
            "show_transaction_history": False,
            "data_sharing_consent": False,
        }

    async def _create_default_notification_preferences(
        self,
        user_id: str
    ) -> List[BarterNotificationPreference]:
        """Create default notification preferences for a new user."""
        default_preferences = [
            BarterNotificationPreference(
                user_id=user_id,
                notification_type="new_match_found",
                enabled=True,
                channels=["in_app", "email"],
                frequency=NotificationFrequency.IMMEDIATE
            ),
            BarterNotificationPreference(
                user_id=user_id,
                notification_type="match_accepted",
                enabled=True,
                channels=["in_app", "email", "push"],
                frequency=NotificationFrequency.IMMEDIATE
            ),
            BarterNotificationPreference(
                user_id=user_id,
                notification_type="transaction_created",
                enabled=True,
                channels=["in_app", "email"],
                frequency=NotificationFrequency.IMMEDIATE
            ),
            BarterNotificationPreference(
                user_id=user_id,
                notification_type="transaction_completed",
                enabled=True,
                channels=["in_app", "email"],
                frequency=NotificationFrequency.IMMEDIATE
            ),
            BarterNotificationPreference(
                user_id=user_id,
                notification_type="system_updates",
                enabled=True,
                channels=["in_app"],
                frequency=NotificationFrequency.WEEKLY
            ),
        ]
        
        # Cache the preferences
        cache_key = f"{self.cache_prefix}notifications:{user_id}"
        preferences_data = [pref.model_dump() for pref in default_preferences]
        await redis_service.async_set(
            cache_key,
            preferences_data,
            ex=self.cache_ttl
        )
        
        return default_preferences


# Global user service instance
barter_user_service = BarterUserService()


def get_barter_user_service() -> BarterUserService:
    """Get the global barter user service instance."""
    return barter_user_service
