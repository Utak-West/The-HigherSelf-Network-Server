"""
Community Engagement Agent for The HigherSelf Network Server.

This agent is responsible for:
1. Managing community member onboarding and engagement in Circle.so
2. Synchronizing community data with Notion as the central hub
3. Tracking engagement metrics and activity
4. Triggering notifications based on community events
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

# import logging # Replaced by loguru
from loguru import logger  # Added for direct loguru usage
from pydantic import ValidationError

from agents.base_agent import BaseAgent
from config.testing_mode import TestingMode, is_api_disabled
from models.base import AgentCapability, ApiPlatform
from models.notion_db_models_extended import CommunityMember, ContactProfile
from services.notion_service import NotionService

# logger = logging.getLogger(__name__) # Replaced by global loguru logger


class CommunityEngagementAgent(BaseAgent):
    """
    Agent for managing community engagement and member activities.
    Integrates with Circle.so and maintains Notion as the central data hub.
    """

    def __init__(self, notion_service: NotionService):
        """Initialize the Community Engagement Agent."""
        super().__init__(
            agent_id="community-engagement-agent",
            name="Community Engagement Agent",
            description="Manages community member engagement and activities",
            version="1.0",
            capabilities=[
                AgentCapability.CLIENT_COMMUNICATION,
                AgentCapability.NOTIFICATION_DISPATCH,
                AgentCapability.WORKFLOW_MANAGEMENT,
            ],
            apis_utilized=[ApiPlatform.NOTION],  # Primary data store
        )
        self.notion_service = notion_service
        logger.info("Community Engagement Agent initialized")

    async def process_new_member(self, member_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a new member joining the community platform (e.g., Circle.so).

        Args:
            member_data: New member data from Circle.so webhook

        Returns:
            Result of processing the new member
        """
        logger.info(f"Processing new community member: {member_data.get('email')}")

        # Step 1: Check if contact already exists in Contacts & Profiles DB
        contact = await self._find_or_create_contact(member_data)

        # Step 2: Create community member record
        member = CommunityMember(
            member_name=member_data.get("name"),
            member_email=member_data.get("email"),
            join_date=datetime.now(),
            membership_level=member_data.get("membership_level", "Standard"),
            membership_status="Active",
            primary_platform="Circle.so",
            interest_groups=member_data.get("interest_groups", []),
            profile_link=member_data.get("profile_url"),
            related_contact=contact.contact_id,
        )

        # Step 3: Save to Notion
        member_page_id = await self.notion_service.create_page(member)
        member.page_id = member_page_id

        # Step 4: Create workflow instance for member onboarding
        workflow_instance = await self._create_onboarding_workflow(member, contact)

        # Step 5: Send welcome notification
        notification_result = await self._send_welcome_notification(member)

        return {
            "success": True,
            "message": "New community member processed successfully",
            "member_id": member.member_id,
            "workflow_instance_id": workflow_instance.get("instance_id"),
            "notification_sent": notification_result.get("success", False),
        }

    async def track_member_activity(
        self, activity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track community member activity (posts, comments, reactions).

        Args:
            activity_data: Member activity data from Circle.so webhook

        Returns:
            Result of processing the activity
        """
        logger.info(
            f"Tracking community activity for: {activity_data.get('member_email')}"
        )

        # Step 1: Find the member in the Community Hub DB
        member = await self._find_member_by_email(activity_data.get("member_email"))
        if not member:
            logger.warning(
                f"Community member not found: {activity_data.get('member_email')}"
            )
            return {
                "success": False,
                "message": f"Community member not found: {activity_data.get('member_email')}",
            }

        # Step 2: Update engagement metrics
        member.last_engagement_date = datetime.now()
        member.engagement_type = activity_data.get("activity_type")

        # Update engagement score (simple algorithm)
        if member.engagement_score is None:
            member.engagement_score = 10  # Initial score
        else:
            # Different activities have different point values
            points = {"post": 10, "comment": 5, "reaction": 2, "login": 1}.get(
                activity_data.get("activity_type").lower(), 1
            )

            # Cap at 100
            member.engagement_score = min(100, member.engagement_score + points)

        # Step 3: Save updates to Notion
        await self.notion_service.update_page(member)

        # Step 4: Update related contact if available
        if member.related_contact:
            await self._update_contact_engagement(member.related_contact, activity_data)

        return {
            "success": True,
            "message": "Member activity tracked successfully",
            "member_id": member.member_id,
            "new_engagement_score": member.engagement_score,
        }

    async def schedule_community_event(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Schedule a community event and notify relevant members.

        Args:
            event_data: Event details including title, description, date

        Returns:
            Result of event creation and notifications
        """
        logger.info(f"Scheduling community event: {event_data.get('title')}")

        # Step 1: Create event in Notion (would typically be in an Events database)
        # For this example, we'll just log it
        logger.info(f"Event would be created in Notion: {event_data}")

        # Step 2: Find members matching the target criteria
        target_members = await self._find_members_for_event(
            event_data.get("target_criteria", {})
        )

        # Step 3: Send event notifications
        notification_count = 0
        for member in target_members:
            notification_sent = await self._notify_member_about_event(
                member, event_data
            )
            if notification_sent:
                notification_count += 1

        return {
            "success": True,
            "message": f"Event scheduled and {notification_count} members notified",
            "event_title": event_data.get("title"),
            "event_date": event_data.get("date"),
            "notified_members_count": notification_count,
        }

    async def _find_or_create_contact(
        self, member_data: Dict[str, Any]
    ) -> ContactProfile:
        """
        Find existing contact or create a new one.

        Args:
            member_data: Member data from community platform

        Returns:
            ContactProfile model instance
        """
        # Query by email
        filter_conditions = {
            "property": "email",
            "rich_text": {"equals": member_data.get("email")},
        }

        contacts = await self.notion_service.query_database(
            ContactProfile, filter_conditions=filter_conditions
        )

        if contacts:
            # Contact exists, update with community info
            contact = contacts[0]
            contact.tags = list(set(contact.tags + ["Community Member"]))
            contact.last_contacted_date = datetime.now()
            await self.notion_service.update_page(contact)
            return contact
        else:
            # Create new contact
            new_contact = ContactProfile(
                full_name=member_data.get("name"),
                email=member_data.get("email"),
                contact_type="Community Member",
                lead_source="Circle.so",
                status="Active",
                tags=["Community Member"],
                marketing_segments=["Community"],
            )

            page_id = await self.notion_service.create_page(new_contact)
            new_contact.page_id = page_id
            return new_contact

    async def _find_member_by_email(self, email: str) -> Optional[CommunityMember]:
        """
        Find a community member by email.

        Args:
            email: Member's email address

        Returns:
            CommunityMember if found, None otherwise
        """
        filter_conditions = {"property": "member_email", "rich_text": {"equals": email}}

        members = await self.notion_service.query_database(
            CommunityMember, filter_conditions=filter_conditions
        )

        return members[0] if members else None

    async def _create_onboarding_workflow(
        self, member: CommunityMember, contact: ContactProfile
    ) -> Dict[str, Any]:
        """
        Create a workflow instance for member onboarding.

        Args:
            member: New community member
            contact: Related contact profile

        Returns:
            Created workflow instance details
        """
        # In a real implementation, this would use the WorkflowInstance model
        # and create a proper workflow instance in Notion

        workflow_data = {
            "instance_id": f"ONBOARD-{member.member_id}",
            "workflow": "Community Member Onboarding",
            "business_entity": contact.related_business_entity or "DEFAULT_ENTITY",
            "current_state": "New Member Welcome",
            "status": "Active",
            "key_data_payload": json.dumps(
                {
                    "member_id": member.member_id,
                    "member_email": member.member_email,
                    "join_date": member.join_date.isoformat(),
                    "membership_level": member.membership_level,
                }
            ),
            "history_log": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "action": "Member joined community platform",
                    "details": {"platform": "Circle.so"},
                }
            ],
        }

        logger.info(f"Creating onboarding workflow for member {member.member_id}")

        # This would typically be created in Notion
        # For this example, we'll just return the data
        return workflow_data

    async def _send_welcome_notification(
        self, member: CommunityMember
    ) -> Dict[str, Any]:
        """
        Send welcome notification to new community member.

        Args:
            member: New community member

        Returns:
            Notification result
        """
        # Check if in testing mode
        if is_api_disabled("circle"):
            TestingMode.log_attempted_api_call(
                api_name="circle",
                endpoint="direct_messages/send",
                method="POST",
                params={
                    "recipient_email": member.member_email,
                    "message_type": "welcome",
                },
            )
            logger.info(
                f"[TESTING MODE] Simulated sending welcome message to {member.member_email}"
            )
            return {
                "success": True,
                "channel": "Circle.so Direct Message",
                "recipient": member.member_email,
            }

        # In a real implementation, this would use a NotificationService
        # and potentially the NotificationTemplate model from Notion
        logger.info(f"Sending welcome notification to {member.member_email}")

        # Simulate API call to Circle.so
        # In real implementation: result = await circle_service.send_message(...)
        return {
            "success": True,
            "channel": "Circle.so Direct Message",
            "recipient": member.member_email,
        }

    async def _update_contact_engagement(
        self, contact_id: str, activity_data: Dict[str, Any]
    ):
        """
        Update contact profile with community engagement data.

        Args:
            contact_id: ID of the contact to update
            activity_data: Activity data to record
        """
        # Find the contact
        filter_conditions = {
            "property": "contact_id",
            "rich_text": {"equals": contact_id},
        }

        contacts = await self.notion_service.query_database(
            ContactProfile, filter_conditions=filter_conditions
        )

        if contacts:
            contact = contacts[0]
            contact.last_contacted_date = datetime.now()

            # Add engagement note
            engagement_note = f"{datetime.now().isoformat()}: Community activity - {activity_data.get('activity_type')}"
            if contact.notes:
                contact.notes += f"\n{engagement_note}"
            else:
                contact.notes = engagement_note

            # Update contact
            await self.notion_service.update_page(contact)
            logger.info(f"Updated contact {contact_id} with community activity")

    async def _find_members_for_event(
        self, criteria: Dict[str, Any]
    ) -> List[CommunityMember]:
        """
        Find community members matching criteria for event targeting.

        Args:
            criteria: Targeting criteria for the event

        Returns:
            List of matching community members
        """
        # Build filter based on criteria
        filters = []

        if "interest_groups" in criteria and criteria["interest_groups"]:
            # Filter by interest groups
            group_filter = {
                "property": "interest_groups",
                "multi_select": {
                    "contains": criteria["interest_groups"][0]  # Simplified for demo
                },
            }
            filters.append(group_filter)

        if "membership_level" in criteria:
            # Filter by membership level
            level_filter = {
                "property": "membership_level",
                "select": {"equals": criteria["membership_level"]},
            }
            filters.append(level_filter)

        # Combine filters with AND logic
        filter_conditions = None
        if len(filters) > 1:
            filter_conditions = {"and": filters}
        elif filters:
            filter_conditions = filters[0]

        # Query for matching members
        members = await self.notion_service.query_database(
            CommunityMember, filter_conditions=filter_conditions
        )

        return members

    async def _notify_member_about_event(
        self, member: CommunityMember, event_data: Dict[str, Any]
    ) -> bool:
        """
        Notify a community member about an upcoming event.

        Args:
            member: Community member to notify
            event_data: Event details

        Returns:
            Whether notification was successfully sent
        """
        # Check if in testing mode
        if is_api_disabled("circle"):
            TestingMode.log_attempted_api_call(
                api_name="circle",
                endpoint="direct_messages/send",
                method="POST",
                params={
                    "recipient_email": member.member_email,
                    "message_type": "event_notification",
                    "event_title": event_data.get("title"),
                },
            )
            logger.info(
                f"[TESTING MODE] Simulated sending event notification to {member.member_email}"
            )
            return True

        # In a real implementation, this would use a NotificationService
        # and potentially the NotificationTemplate model from Notion
        logger.info(
            f"Notifying {member.member_email} about event: {event_data.get('title')}"
        )

        # Simulate API call to Circle.so
        # In real implementation: result = await circle_service.send_message(...)
        return True
