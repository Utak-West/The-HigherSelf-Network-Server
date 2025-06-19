#!/usr/bin/env python3
"""
Business Entity-Specific Workflow Configurations

This module defines detailed workflow configurations for each business entity
in The HigherSelf Network, providing targeted automation sequences based on
contact types, lead sources, and business objectives.

Business Entities:
- The 7 Space: Art gallery and wellness center workflows
- AM Consulting: Business consulting and client management workflows  
- HigherSelf Core: Community platform and general engagement workflows
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

from services.contact_workflow_automation import WorkflowAction, ContactType, LeadSource


class WorkflowPriority(Enum):
    """Workflow execution priority levels."""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EngagementChannel(Enum):
    """Available engagement channels."""
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    SOCIAL_MEDIA = "social_media"
    IN_PERSON = "in_person"
    VIRTUAL_MEETING = "virtual_meeting"


@dataclass
class BusinessEntityWorkflowConfig:
    """Configuration for business entity-specific workflows."""
    entity_name: str
    primary_contact_types: List[ContactType]
    preferred_channels: List[EngagementChannel]
    response_time_hours: int
    follow_up_sequence_days: List[int]
    personalization_templates: Dict[str, str]
    success_metrics: List[str]


class BusinessEntityWorkflows:
    """
    Comprehensive workflow configurations for all business entities.
    
    This class provides detailed workflow templates, engagement sequences,
    and automation rules specific to each business entity's objectives.
    """

    def __init__(self):
        """Initialize business entity workflow configurations."""
        self.entity_configs = self._initialize_entity_configs()
        self.workflow_templates = self._initialize_workflow_templates()

    def _initialize_entity_configs(self) -> Dict[str, BusinessEntityWorkflowConfig]:
        """Initialize configuration for each business entity."""
        return {
            "the_7_space": BusinessEntityWorkflowConfig(
                entity_name="The 7 Space",
                primary_contact_types=[ContactType.ARTIST, ContactType.GALLERY_CONTACT],
                preferred_channels=[EngagementChannel.EMAIL, EngagementChannel.IN_PERSON, EngagementChannel.SOCIAL_MEDIA],
                response_time_hours=24,
                follow_up_sequence_days=[1, 3, 7, 14, 30],
                personalization_templates={
                    "artist_welcome": "Welcome to The 7 Space artist community! We're excited to learn about your creative journey.",
                    "gallery_inquiry": "Thank you for your interest in The 7 Space. We'd love to discuss potential collaboration opportunities.",
                    "exhibition_invite": "We're hosting an upcoming exhibition that aligns with your artistic vision.",
                    "wellness_program": "Discover our wellness programs designed specifically for creative professionals."
                },
                success_metrics=["exhibition_bookings", "artist_registrations", "wellness_session_bookings", "community_engagement"]
            ),
            
            "am_consulting": BusinessEntityWorkflowConfig(
                entity_name="AM Consulting",
                primary_contact_types=[ContactType.BUSINESS_CONTACT, ContactType.POTENTIAL_CLIENT],
                preferred_channels=[EngagementChannel.EMAIL, EngagementChannel.PHONE, EngagementChannel.VIRTUAL_MEETING],
                response_time_hours=4,
                follow_up_sequence_days=[1, 2, 5, 10, 21],
                personalization_templates={
                    "business_welcome": "Welcome to AM Consulting. We specialize in strategic business transformation.",
                    "consultation_offer": "Let's schedule a complimentary consultation to discuss your business objectives.",
                    "case_study_share": "Here's how we've helped similar businesses achieve their goals.",
                    "proposal_follow_up": "Following up on our proposal discussion and next steps."
                },
                success_metrics=["consultation_bookings", "proposal_requests", "client_conversions", "revenue_generated"]
            ),
            
            "higherself_core": BusinessEntityWorkflowConfig(
                entity_name="HigherSelf Core",
                primary_contact_types=[ContactType.GENERAL_CONTACT, ContactType.ACADEMIC_CONTACT, ContactType.MEDIA_CONTACT],
                preferred_channels=[EngagementChannel.EMAIL, EngagementChannel.SOCIAL_MEDIA, EngagementChannel.VIRTUAL_MEETING],
                response_time_hours=12,
                follow_up_sequence_days=[1, 7, 14, 30, 60],
                personalization_templates={
                    "community_welcome": "Welcome to The HigherSelf Network! Join our community of growth-minded individuals.",
                    "platform_introduction": "Discover how our platform can support your personal and professional development.",
                    "content_sharing": "Here's valuable content aligned with your interests and goals.",
                    "community_event": "Join us for upcoming community events and networking opportunities."
                },
                success_metrics=["community_signups", "platform_engagement", "event_attendance", "content_consumption"]
            )
        }

    def _initialize_workflow_templates(self) -> Dict[str, List[WorkflowAction]]:
        """Initialize comprehensive workflow templates for each business entity."""
        return {
            # The 7 Space Workflows
            "the7space_artist_discovery": [
                WorkflowAction(
                    action_type="send_notification",
                    target="gallery_curator",
                    content={
                        "title": "New Artist Discovery",
                        "message": "Potential artist contact requires portfolio review",
                        "priority": "high",
                        "channel": "email"
                    }
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="gallery_team",
                    content={
                        "title": "Artist Portfolio Review",
                        "description": "Review artist's work and assess exhibition potential",
                        "category": "CURATION",
                        "priority": "HIGH",
                        "estimated_hours": 2
                    },
                    delay_hours=2
                ),
                WorkflowAction(
                    action_type="schedule_follow_up",
                    target="contact",
                    content={
                        "template": "artist_welcome",
                        "subject": "Welcome to The 7 Space Artist Community",
                        "personalization": "artist_focused",
                        "channel": "email"
                    },
                    delay_hours=24
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="social_media_team",
                    content={
                        "title": "Artist Social Media Research",
                        "description": "Research artist's social media presence and engagement",
                        "category": "RESEARCH",
                        "priority": "MEDIUM"
                    },
                    delay_hours=48
                )
            ],
            
            "the7space_wellness_inquiry": [
                WorkflowAction(
                    action_type="send_notification",
                    target="wellness_coordinator",
                    content={
                        "title": "Wellness Program Inquiry",
                        "message": "New wellness program inquiry requires response",
                        "priority": "medium"
                    }
                ),
                WorkflowAction(
                    action_type="schedule_follow_up",
                    target="contact",
                    content={
                        "template": "wellness_program",
                        "subject": "Your Wellness Journey Starts Here",
                        "personalization": "wellness_focused",
                        "channel": "email"
                    },
                    delay_hours=4
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="wellness_team",
                    content={
                        "title": "Wellness Consultation Booking",
                        "description": "Schedule initial wellness consultation",
                        "category": "BOOKING",
                        "priority": "HIGH"
                    },
                    delay_hours=6
                )
            ],
            
            # AM Consulting Workflows
            "am_consulting_lead_qualification": [
                WorkflowAction(
                    action_type="send_notification",
                    target="business_development",
                    content={
                        "title": "High-Priority Business Lead",
                        "message": "New business lead requires immediate qualification",
                        "priority": "urgent"
                    }
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="lead_qualifier",
                    content={
                        "title": "Business Lead Qualification",
                        "description": "Assess business needs, budget, and decision-making process",
                        "category": "SALES",
                        "priority": "URGENT",
                        "estimated_hours": 1
                    },
                    delay_hours=1
                ),
                WorkflowAction(
                    action_type="schedule_follow_up",
                    target="contact",
                    content={
                        "template": "consultation_offer",
                        "subject": "Strategic Consultation Opportunity",
                        "personalization": "business_focused",
                        "channel": "email"
                    },
                    delay_hours=2
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="research_team",
                    content={
                        "title": "Company Research & Analysis",
                        "description": "Research company background, industry, and potential challenges",
                        "category": "RESEARCH",
                        "priority": "HIGH"
                    },
                    delay_hours=4
                )
            ],
            
            "am_consulting_proposal_follow_up": [
                WorkflowAction(
                    action_type="create_task",
                    target="account_manager",
                    content={
                        "title": "Proposal Follow-up Call",
                        "description": "Follow up on submitted proposal and address questions",
                        "category": "SALES",
                        "priority": "HIGH"
                    },
                    delay_hours=48
                ),
                WorkflowAction(
                    action_type="schedule_follow_up",
                    target="contact",
                    content={
                        "template": "proposal_follow_up",
                        "subject": "Following Up on Your Strategic Proposal",
                        "personalization": "proposal_focused",
                        "channel": "email"
                    },
                    delay_hours=72
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="proposal_team",
                    content={
                        "title": "Proposal Optimization",
                        "description": "Review and optimize proposal based on client feedback",
                        "category": "PROPOSAL",
                        "priority": "MEDIUM"
                    },
                    delay_hours=120
                )
            ],
            
            # HigherSelf Core Workflows
            "higherself_community_onboarding": [
                WorkflowAction(
                    action_type="send_notification",
                    target="community_manager",
                    content={
                        "title": "New Community Member",
                        "message": "New member joined the HigherSelf community",
                        "priority": "medium"
                    }
                ),
                WorkflowAction(
                    action_type="schedule_follow_up",
                    target="contact",
                    content={
                        "template": "community_welcome",
                        "subject": "Welcome to The HigherSelf Network Community",
                        "personalization": "community_focused",
                        "channel": "email"
                    },
                    delay_hours=1
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="community_team",
                    content={
                        "title": "Member Onboarding Sequence",
                        "description": "Guide new member through platform features and community guidelines",
                        "category": "ONBOARDING",
                        "priority": "MEDIUM"
                    },
                    delay_hours=24
                ),
                WorkflowAction(
                    action_type="schedule_follow_up",
                    target="contact",
                    content={
                        "template": "platform_introduction",
                        "subject": "Discover Your HigherSelf Platform Features",
                        "personalization": "platform_focused",
                        "channel": "email"
                    },
                    delay_hours=168  # 1 week
                )
            ],
            
            "higherself_content_engagement": [
                WorkflowAction(
                    action_type="create_task",
                    target="content_team",
                    content={
                        "title": "Personalized Content Curation",
                        "description": "Curate content based on member interests and engagement history",
                        "category": "CONTENT",
                        "priority": "LOW"
                    },
                    delay_hours=24
                ),
                WorkflowAction(
                    action_type="schedule_follow_up",
                    target="contact",
                    content={
                        "template": "content_sharing",
                        "subject": "Curated Content for Your Growth Journey",
                        "personalization": "content_focused",
                        "channel": "email"
                    },
                    delay_hours=72
                )
            ],
            
            # Lead Source-Specific Workflows
            "event_lead_hot_follow_up": [
                WorkflowAction(
                    action_type="send_notification",
                    target="event_coordinator",
                    content={
                        "title": "Hot Event Lead",
                        "message": "Event attendee requires immediate follow-up",
                        "priority": "urgent"
                    }
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="event_team",
                    content={
                        "title": "Event Lead Personal Outreach",
                        "description": "Personal follow-up with event attendee while interaction is fresh",
                        "category": "EVENT",
                        "priority": "URGENT"
                    },
                    delay_hours=4
                ),
                WorkflowAction(
                    action_type="schedule_follow_up",
                    target="contact",
                    content={
                        "template": "event_follow_up_sequence",
                        "subject": "Great connecting at our event!",
                        "personalization": "event_focused",
                        "channel": "email"
                    },
                    delay_hours=24
                )
            ],
            
            "referral_vip_treatment": [
                WorkflowAction(
                    action_type="send_notification",
                    target="leadership_team",
                    content={
                        "title": "VIP Referral Contact",
                        "message": "High-value referral contact requires executive attention",
                        "priority": "urgent"
                    }
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="executive_team",
                    content={
                        "title": "VIP Referral Personal Outreach",
                        "description": "Executive-level personal outreach to referral contact",
                        "category": "VIP",
                        "priority": "URGENT"
                    },
                    delay_hours=2
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="account_management",
                    content={
                        "title": "Referral Source Thank You",
                        "description": "Thank referral source and strengthen relationship",
                        "category": "RELATIONSHIP",
                        "priority": "HIGH"
                    },
                    delay_hours=6
                )
            ]
        }

    def get_entity_config(self, entity_name: str) -> BusinessEntityWorkflowConfig:
        """Get configuration for a specific business entity."""
        return self.entity_configs.get(entity_name.lower().replace(" ", "_"))

    def get_workflow_template(self, template_name: str) -> List[WorkflowAction]:
        """Get a specific workflow template."""
        return self.workflow_templates.get(template_name, [])

    def get_entity_workflows(self, entity_name: str) -> Dict[str, List[WorkflowAction]]:
        """Get all workflows for a specific business entity."""
        entity_key = entity_name.lower().replace(" ", "_")
        return {
            name: template for name, template in self.workflow_templates.items()
            if name.startswith(entity_key)
        }
