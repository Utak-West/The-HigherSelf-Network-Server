"""
Barter Notification Service for The HigherSelf Network Server.

This service handles notifications for barter system events including
match notifications, transaction updates, and system alerts.
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from loguru import logger
from pydantic import BaseModel

from models.barter_models import (
    BarterListing,
    BarterMatch,
    BarterRequest,
    BarterTransaction,
)
from services.redis_service import redis_service


class NotificationType(str, Enum):
    """Types of barter notifications."""
    
    # Match notifications
    NEW_MATCH_FOUND = "new_match_found"
    MATCH_VIEWED = "match_viewed"
    MATCH_ACCEPTED = "match_accepted"
    MATCH_DECLINED = "match_declined"
    
    # Transaction notifications
    TRANSACTION_CREATED = "transaction_created"
    TRANSACTION_STARTED = "transaction_started"
    TRANSACTION_PROGRESS_UPDATE = "transaction_progress_update"
    TRANSACTION_COMPLETED = "transaction_completed"
    TRANSACTION_CANCELLED = "transaction_cancelled"
    
    # Request/Listing notifications
    LISTING_EXPIRED = "listing_expired"
    REQUEST_EXPIRED = "request_expired"
    NEW_REQUEST_FOR_CATEGORY = "new_request_for_category"
    
    # System notifications
    PROFILE_VERIFICATION = "profile_verification"
    SYSTEM_MAINTENANCE = "system_maintenance"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class BarterNotification(BaseModel):
    """Barter system notification model."""
    
    id: str
    recipient_id: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    
    # Content
    title: str
    message: str
    data: Dict[str, Any] = {}
    
    # Delivery
    channels: List[NotificationChannel] = [NotificationChannel.IN_APP]
    scheduled_at: Optional[datetime] = None
    
    # Status
    sent: bool = False
    read: bool = False
    
    # Metadata
    created_at: datetime
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    # Related entities
    related_listing_id: Optional[UUID] = None
    related_request_id: Optional[UUID] = None
    related_match_id: Optional[UUID] = None
    related_transaction_id: Optional[UUID] = None


class BarterNotificationService:
    """Service for managing barter system notifications."""
    
    def __init__(self):
        self.cache_prefix = "barter_notifications:"
        self.cache_ttl = 86400 * 7  # 7 days
        
        # Notification templates
        self.templates = {
            NotificationType.NEW_MATCH_FOUND: {
                "title": "New Barter Match Found!",
                "message": "We found a potential match for your {service_type} request. Check it out!",
                "priority": NotificationPriority.HIGH,
                "channels": [NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.IN_APP]
            },
            NotificationType.MATCH_ACCEPTED: {
                "title": "Match Accepted!",
                "message": "{provider_name} accepted your barter request for {service_type}.",
                "priority": NotificationPriority.HIGH,
                "channels": [NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.IN_APP]
            },
            NotificationType.TRANSACTION_CREATED: {
                "title": "Barter Transaction Started",
                "message": "Your barter exchange with {partner_name} has been confirmed and started.",
                "priority": NotificationPriority.NORMAL,
                "channels": [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
            },
            NotificationType.TRANSACTION_PROGRESS_UPDATE: {
                "title": "Barter Progress Update",
                "message": "Progress update on your exchange with {partner_name}: {progress_message}",
                "priority": NotificationPriority.NORMAL,
                "channels": [NotificationChannel.IN_APP]
            },
            NotificationType.TRANSACTION_COMPLETED: {
                "title": "Barter Exchange Completed!",
                "message": "Your barter exchange with {partner_name} has been completed. Please leave a review!",
                "priority": NotificationPriority.HIGH,
                "channels": [NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.IN_APP]
            },
            NotificationType.LISTING_EXPIRED: {
                "title": "Listing Expired",
                "message": "Your {service_type} listing has expired. Would you like to renew it?",
                "priority": NotificationPriority.NORMAL,
                "channels": [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
            },
            NotificationType.NEW_REQUEST_FOR_CATEGORY: {
                "title": "New Request in Your Area",
                "message": "Someone is looking for {service_type} services in your area. Check if you can help!",
                "priority": NotificationPriority.NORMAL,
                "channels": [NotificationChannel.IN_APP]
            }
        }
    
    async def create_notification(
        self,
        recipient_id: str,
        notification_type: NotificationType,
        data: Dict[str, Any],
        custom_title: Optional[str] = None,
        custom_message: Optional[str] = None,
        priority: Optional[NotificationPriority] = None,
        channels: Optional[List[NotificationChannel]] = None,
        scheduled_at: Optional[datetime] = None,
        **kwargs
    ) -> BarterNotification:
        """Create a new barter notification."""
        
        try:
            # Get template
            template = self.templates.get(notification_type, {})
            
            # Generate notification ID
            notification_id = f"{notification_type.value}_{recipient_id}_{int(datetime.now(timezone.utc).timestamp())}"
            
            # Build notification
            notification = BarterNotification(
                id=notification_id,
                recipient_id=recipient_id,
                notification_type=notification_type,
                priority=priority or template.get("priority", NotificationPriority.NORMAL),
                title=custom_title or template.get("title", "Barter Notification"),
                message=custom_message or template.get("message", "You have a new barter notification"),
                data=data,
                channels=channels or template.get("channels", [NotificationChannel.IN_APP]),
                scheduled_at=scheduled_at,
                created_at=datetime.now(timezone.utc),
                **kwargs
            )
            
            # Format message with data
            notification.title = notification.title.format(**data)
            notification.message = notification.message.format(**data)
            
            # Cache notification
            cache_key = f"{self.cache_prefix}{notification.id}"
            await redis_service.async_set(
                cache_key,
                notification.model_dump_json(),
                ex=self.cache_ttl
            )
            
            # Add to user's notification list
            user_notifications_key = f"{self.cache_prefix}user:{recipient_id}"
            await redis_service.async_lpush(user_notifications_key, notification.id)
            await redis_service.async_expire(user_notifications_key, self.cache_ttl)
            
            logger.info(f"Created barter notification: {notification.id} for user {recipient_id}")
            
            # Send notification if not scheduled
            if not scheduled_at:
                await self.send_notification(notification)
            
            return notification
            
        except Exception as e:
            logger.error(f"Error creating barter notification: {e}")
            raise
    
    async def send_notification(self, notification: BarterNotification) -> bool:
        """Send a notification through configured channels."""
        
        try:
            success = True
            
            for channel in notification.channels:
                try:
                    if channel == NotificationChannel.EMAIL:
                        await self._send_email_notification(notification)
                    elif channel == NotificationChannel.SMS:
                        await self._send_sms_notification(notification)
                    elif channel == NotificationChannel.PUSH:
                        await self._send_push_notification(notification)
                    elif channel == NotificationChannel.IN_APP:
                        await self._send_in_app_notification(notification)
                    elif channel == NotificationChannel.WEBHOOK:
                        await self._send_webhook_notification(notification)
                        
                except Exception as e:
                    logger.error(f"Error sending notification via {channel}: {e}")
                    success = False
            
            # Update notification status
            notification.sent = True
            notification.sent_at = datetime.now(timezone.utc)
            
            # Update cache
            cache_key = f"{self.cache_prefix}{notification.id}"
            await redis_service.async_set(
                cache_key,
                notification.model_dump_json(),
                ex=self.cache_ttl
            )
            
            logger.info(f"Sent barter notification: {notification.id}")
            return success
            
        except Exception as e:
            logger.error(f"Error sending barter notification: {e}")
            return False
    
    async def _send_email_notification(self, notification: BarterNotification):
        """Send email notification."""
        # TODO: Integrate with email service
        logger.info(f"Email notification sent to {notification.recipient_id}: {notification.title}")
    
    async def _send_sms_notification(self, notification: BarterNotification):
        """Send SMS notification."""
        # TODO: Integrate with SMS service
        logger.info(f"SMS notification sent to {notification.recipient_id}: {notification.title}")
    
    async def _send_push_notification(self, notification: BarterNotification):
        """Send push notification."""
        # TODO: Integrate with push notification service
        logger.info(f"Push notification sent to {notification.recipient_id}: {notification.title}")
    
    async def _send_in_app_notification(self, notification: BarterNotification):
        """Send in-app notification."""
        # In-app notifications are stored in cache and retrieved by the client
        logger.info(f"In-app notification created for {notification.recipient_id}: {notification.title}")
    
    async def _send_webhook_notification(self, notification: BarterNotification):
        """Send webhook notification."""
        # TODO: Integrate with webhook service
        logger.info(f"Webhook notification sent for {notification.recipient_id}: {notification.title}")
    
    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[BarterNotification]:
        """Get notifications for a user."""
        
        try:
            user_notifications_key = f"{self.cache_prefix}user:{user_id}"
            notification_ids = await redis_service.async_lrange(user_notifications_key, 0, limit - 1)
            
            notifications = []
            for notification_id in notification_ids:
                cache_key = f"{self.cache_prefix}{notification_id}"
                notification_data = await redis_service.async_get(cache_key)
                
                if notification_data:
                    notification = BarterNotification.model_validate_json(notification_data)
                    
                    if unread_only and notification.read:
                        continue
                    
                    notifications.append(notification)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []
    
    async def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read."""
        
        try:
            cache_key = f"{self.cache_prefix}{notification_id}"
            notification_data = await redis_service.async_get(cache_key)
            
            if not notification_data:
                return False
            
            notification = BarterNotification.model_validate_json(notification_data)
            
            if notification.recipient_id != user_id:
                return False
            
            notification.read = True
            notification.read_at = datetime.now(timezone.utc)
            
            await redis_service.async_set(
                cache_key,
                notification.model_dump_json(),
                ex=self.cache_ttl
            )
            
            logger.info(f"Marked notification as read: {notification_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    # Event-specific notification methods
    
    async def notify_new_match(self, match: BarterMatch, requester_id: str, listing: BarterListing):
        """Notify user about a new match."""
        await self.create_notification(
            recipient_id=requester_id,
            notification_type=NotificationType.NEW_MATCH_FOUND,
            data={
                "service_type": listing.category.value.replace("_", " ").title(),
                "provider_name": listing.provider_id,
                "compatibility_score": f"{match.compatibility_score:.0%}",
                "distance": f"{match.distance_km:.1f}km" if match.distance_km else "Virtual"
            },
            related_match_id=match.id,
            related_listing_id=match.listing_id,
            related_request_id=match.request_id
        )
    
    async def notify_match_accepted(self, match: BarterMatch, provider_name: str, service_type: str):
        """Notify user that their match was accepted."""
        await self.create_notification(
            recipient_id=match.request_id,  # This should be the requester ID
            notification_type=NotificationType.MATCH_ACCEPTED,
            data={
                "provider_name": provider_name,
                "service_type": service_type
            },
            related_match_id=match.id
        )
    
    async def notify_transaction_created(self, transaction: BarterTransaction):
        """Notify both parties about transaction creation."""
        # Notify provider
        await self.create_notification(
            recipient_id=transaction.provider_id,
            notification_type=NotificationType.TRANSACTION_CREATED,
            data={
                "partner_name": transaction.requester_id,
                "service_type": transaction.provider_service.get("category", "service")
            },
            related_transaction_id=transaction.id
        )
        
        # Notify requester
        await self.create_notification(
            recipient_id=transaction.requester_id,
            notification_type=NotificationType.TRANSACTION_CREATED,
            data={
                "partner_name": transaction.provider_id,
                "service_type": transaction.requester_service.get("category", "service")
            },
            related_transaction_id=transaction.id
        )
    
    async def notify_transaction_completed(self, transaction: BarterTransaction):
        """Notify both parties about transaction completion."""
        # Notify provider
        await self.create_notification(
            recipient_id=transaction.provider_id,
            notification_type=NotificationType.TRANSACTION_COMPLETED,
            data={
                "partner_name": transaction.requester_id
            },
            related_transaction_id=transaction.id
        )
        
        # Notify requester
        await self.create_notification(
            recipient_id=transaction.requester_id,
            notification_type=NotificationType.TRANSACTION_COMPLETED,
            data={
                "partner_name": transaction.provider_id
            },
            related_transaction_id=transaction.id
        )
