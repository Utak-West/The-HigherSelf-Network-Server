#!/usr/bin/env python3
"""
The 7 Space Contact Management Configuration

Comprehensive configuration for The 7 Space's 191 Notion contacts integration,
gallery/wellness workflow automation, and contact segmentation within the
multi-entity HigherSelf Network Server architecture.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import os

class The7SpaceContactType(Enum):
    """Contact types specific to The 7 Space"""
    ARTIST = "artist"
    GALLERY_VISITOR = "gallery_visitor"
    WELLNESS_CLIENT = "wellness_client"
    EVENT_ATTENDEE = "event_attendee"
    WORKSHOP_PARTICIPANT = "workshop_participant"
    MEDITATION_PRACTITIONER = "meditation_practitioner"
    BUSINESS_PARTNER = "business_partner"
    MEDIA_CONTACT = "media_contact"
    VOLUNTEER = "volunteer"
    GENERAL_INQUIRY = "general_inquiry"

class The7SpaceLeadSource(Enum):
    """Lead sources for The 7 Space"""
    WEBSITE_CONTACT_FORM = "website_contact_form"
    GALLERY_VISIT = "gallery_visit"
    WELLNESS_APPOINTMENT = "wellness_appointment"
    EVENT_REGISTRATION = "event_registration"
    WORKSHOP_SIGNUP = "workshop_signup"
    SOCIAL_MEDIA = "social_media"
    REFERRAL = "referral"
    WALK_IN = "walk_in"
    PHONE_INQUIRY = "phone_inquiry"
    EMAIL_INQUIRY = "email_inquiry"
    NEWSLETTER_SIGNUP = "newsletter_signup"
    EXHIBITION_OPENING = "exhibition_opening"

class The7SpaceEngagementLevel(Enum):
    """Engagement levels for contact scoring"""
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"
    ACTIVE_CLIENT = "active_client"
    VIP = "vip"
    INACTIVE = "inactive"

@dataclass
class The7SpaceContactSegment:
    """Contact segment configuration"""
    name: str
    description: str
    contact_types: List[The7SpaceContactType]
    lead_sources: List[The7SpaceLeadSource]
    engagement_criteria: Dict[str, Any]
    workflow_templates: List[str]
    priority_score: int = 1

@dataclass
class The7SpaceWorkflowAction:
    """Workflow action configuration"""
    action_type: str
    target: str
    content: Dict[str, Any]
    delay_hours: int = 0
    conditions: Optional[Dict[str, Any]] = None
    retry_attempts: int = 3

@dataclass
class The7SpaceWorkflowTemplate:
    """Workflow template configuration"""
    name: str
    description: str
    trigger_conditions: Dict[str, Any]
    actions: List[The7SpaceWorkflowAction]
    enabled: bool = True
    priority: int = 1

class The7SpaceContactManager:
    """
    Contact management configuration for The 7 Space's 191 contacts.
    Handles contact segmentation, workflow automation, and integration
    with the multi-entity HigherSelf Network Server architecture.
    """
    
    def __init__(self):
        self.business_entity = "the_7_space"
        self.total_contacts = 191
        self.notion_databases = self._get_notion_database_config()
        self.contact_segments = self._initialize_contact_segments()
        self.workflow_templates = self._initialize_workflow_templates()
        self.automation_config = self._initialize_automation_config()
    
    def _get_notion_database_config(self) -> Dict[str, str]:
        """Get Notion database configuration"""
        return {
            "contacts": os.getenv("THE_7_SPACE_CONTACTS_DB", ""),
            "artworks": os.getenv("THE_7_SPACE_ARTWORKS_DB", ""),
            "artists": os.getenv("THE_7_SPACE_ARTISTS_DB", ""),
            "events": os.getenv("THE_7_SPACE_EVENTS_DB", ""),
            "services": os.getenv("THE_7_SPACE_SERVICES_DB", ""),
            "appointments": os.getenv("THE_7_SPACE_APPOINTMENTS_DB", ""),
            "classes": os.getenv("THE_7_SPACE_CLASSES_DB", ""),
            "sales": os.getenv("THE_7_SPACE_SALES_DB", ""),
            "marketing": os.getenv("THE_7_SPACE_MARKETING_DB", ""),
            "analytics": os.getenv("THE_7_SPACE_ANALYTICS_DB", "")
        }
    
    def _initialize_contact_segments(self) -> Dict[str, The7SpaceContactSegment]:
        """Initialize contact segments for The 7 Space"""
        return {
            "artists_and_creators": The7SpaceContactSegment(
                name="Artists & Creators",
                description="Artists, creators, and potential exhibition participants",
                contact_types=[
                    The7SpaceContactType.ARTIST,
                    The7SpaceContactType.BUSINESS_PARTNER
                ],
                lead_sources=[
                    The7SpaceLeadSource.WEBSITE_CONTACT_FORM,
                    The7SpaceLeadSource.SOCIAL_MEDIA,
                    The7SpaceLeadSource.REFERRAL,
                    The7SpaceLeadSource.EXHIBITION_OPENING
                ],
                engagement_criteria={
                    "portfolio_submitted": True,
                    "exhibition_interest": True,
                    "social_media_following": ">100"
                },
                workflow_templates=[
                    "artist_welcome_sequence",
                    "portfolio_review_workflow",
                    "exhibition_opportunity_alerts"
                ],
                priority_score=5
            ),
            
            "gallery_visitors": The7SpaceContactSegment(
                name="Gallery Visitors",
                description="Visitors interested in art exhibitions and gallery events",
                contact_types=[
                    The7SpaceContactType.GALLERY_VISITOR,
                    The7SpaceContactType.EVENT_ATTENDEE
                ],
                lead_sources=[
                    The7SpaceLeadSource.GALLERY_VISIT,
                    The7SpaceLeadSource.EVENT_REGISTRATION,
                    The7SpaceLeadSource.WALK_IN,
                    The7SpaceLeadSource.EXHIBITION_OPENING
                ],
                engagement_criteria={
                    "gallery_visits": ">=1",
                    "event_attendance": ">=1",
                    "artwork_interest": True
                },
                workflow_templates=[
                    "gallery_visitor_welcome",
                    "exhibition_updates",
                    "art_appreciation_series"
                ],
                priority_score=3
            ),
            
            "wellness_clients": The7SpaceContactSegment(
                name="Wellness Clients",
                description="Clients interested in wellness services and meditation",
                contact_types=[
                    The7SpaceContactType.WELLNESS_CLIENT,
                    The7SpaceContactType.MEDITATION_PRACTITIONER,
                    The7SpaceContactType.WORKSHOP_PARTICIPANT
                ],
                lead_sources=[
                    The7SpaceLeadSource.WELLNESS_APPOINTMENT,
                    The7SpaceLeadSource.WORKSHOP_SIGNUP,
                    The7SpaceLeadSource.WEBSITE_CONTACT_FORM
                ],
                engagement_criteria={
                    "wellness_services_used": ">=1",
                    "meditation_interest": True,
                    "holistic_health_focus": True
                },
                workflow_templates=[
                    "wellness_client_onboarding",
                    "meditation_journey_guide",
                    "holistic_health_tips"
                ],
                priority_score=4
            ),
            
            "active_community": The7SpaceContactSegment(
                name="Active Community Members",
                description="Highly engaged community members and VIP clients",
                contact_types=[
                    The7SpaceContactType.ARTIST,
                    The7SpaceContactType.WELLNESS_CLIENT,
                    The7SpaceContactType.VOLUNTEER
                ],
                lead_sources=[
                    The7SpaceLeadSource.REFERRAL,
                    The7SpaceLeadSource.EVENT_REGISTRATION,
                    The7SpaceLeadSource.WORKSHOP_SIGNUP
                ],
                engagement_criteria={
                    "engagement_level": "VIP",
                    "referrals_made": ">=2",
                    "community_participation": "high"
                },
                workflow_templates=[
                    "vip_member_benefits",
                    "community_leadership_opportunities",
                    "exclusive_event_invitations"
                ],
                priority_score=5
            ),
            
            "business_partners": The7SpaceContactSegment(
                name="Business Partners",
                description="Business partners, media contacts, and collaboration opportunities",
                contact_types=[
                    The7SpaceContactType.BUSINESS_PARTNER,
                    The7SpaceContactType.MEDIA_CONTACT
                ],
                lead_sources=[
                    The7SpaceLeadSource.REFERRAL,
                    The7SpaceLeadSource.EMAIL_INQUIRY,
                    The7SpaceLeadSource.PHONE_INQUIRY
                ],
                engagement_criteria={
                    "business_collaboration": True,
                    "media_coverage": True,
                    "partnership_potential": "high"
                },
                workflow_templates=[
                    "business_partnership_workflow",
                    "media_collaboration_sequence",
                    "cross_promotion_opportunities"
                ],
                priority_score=4
            ),
            
            "nurture_prospects": The7SpaceContactSegment(
                name="Nurture Prospects",
                description="Prospects requiring nurturing and engagement building",
                contact_types=[
                    The7SpaceContactType.GENERAL_INQUIRY,
                    The7SpaceContactType.GALLERY_VISITOR
                ],
                lead_sources=[
                    The7SpaceLeadSource.NEWSLETTER_SIGNUP,
                    The7SpaceLeadSource.SOCIAL_MEDIA,
                    The7SpaceLeadSource.EMAIL_INQUIRY
                ],
                engagement_criteria={
                    "engagement_level": ["cold", "warm"],
                    "initial_interest": True,
                    "follow_up_needed": True
                },
                workflow_templates=[
                    "prospect_nurturing_sequence",
                    "educational_content_series",
                    "gentle_engagement_workflow"
                ],
                priority_score=2
            )
        }
    
    def _initialize_workflow_templates(self) -> Dict[str, The7SpaceWorkflowTemplate]:
        """Initialize workflow templates for The 7 Space"""
        return {
            "artist_welcome_sequence": The7SpaceWorkflowTemplate(
                name="Artist Welcome Sequence",
                description="Welcome sequence for new artist contacts",
                trigger_conditions={
                    "contact_type": "artist",
                    "first_contact": True
                },
                actions=[
                    The7SpaceWorkflowAction(
                        action_type="send_email",
                        target="contact",
                        content={
                            "template": "artist_welcome_email",
                            "subject": "Welcome to The 7 Space Artist Community",
                            "personalization": True
                        },
                        delay_hours=1
                    ),
                    The7SpaceWorkflowAction(
                        action_type="create_task",
                        target="gallery_team",
                        content={
                            "title": "Review New Artist Portfolio",
                            "description": "Review portfolio and assess exhibition potential",
                            "priority": "high",
                            "category": "artist_review"
                        },
                        delay_hours=24
                    ),
                    The7SpaceWorkflowAction(
                        action_type="schedule_follow_up",
                        target="contact",
                        content={
                            "template": "artist_portfolio_request",
                            "subject": "Share Your Artistic Journey",
                            "call_to_action": "portfolio_submission"
                        },
                        delay_hours=72
                    )
                ]
            ),
            
            "wellness_client_onboarding": The7SpaceWorkflowTemplate(
                name="Wellness Client Onboarding",
                description="Onboarding sequence for new wellness clients",
                trigger_conditions={
                    "contact_type": "wellness_client",
                    "first_appointment": True
                },
                actions=[
                    The7SpaceWorkflowAction(
                        action_type="send_email",
                        target="contact",
                        content={
                            "template": "wellness_welcome_email",
                            "subject": "Welcome to Your Wellness Journey",
                            "include_intake_form": True
                        },
                        delay_hours=2
                    ),
                    The7SpaceWorkflowAction(
                        action_type="create_appointment_reminder",
                        target="contact",
                        content={
                            "reminder_type": "appointment_confirmation",
                            "send_24h_before": True,
                            "send_2h_before": True
                        },
                        delay_hours=0
                    ),
                    The7SpaceWorkflowAction(
                        action_type="schedule_follow_up",
                        target="contact",
                        content={
                            "template": "post_session_feedback",
                            "subject": "How was your wellness session?",
                            "feedback_form": True
                        },
                        delay_hours=48
                    )
                ]
            ),
            
            "gallery_visitor_engagement": The7SpaceWorkflowTemplate(
                name="Gallery Visitor Engagement",
                description="Engagement sequence for gallery visitors",
                trigger_conditions={
                    "contact_type": "gallery_visitor",
                    "gallery_visit": True
                },
                actions=[
                    The7SpaceWorkflowAction(
                        action_type="send_email",
                        target="contact",
                        content={
                            "template": "gallery_visit_thank_you",
                            "subject": "Thank you for visiting The 7 Space",
                            "include_upcoming_events": True
                        },
                        delay_hours=6
                    ),
                    The7SpaceWorkflowAction(
                        action_type="add_to_newsletter",
                        target="contact",
                        content={
                            "newsletter_type": "gallery_updates",
                            "frequency": "weekly"
                        },
                        delay_hours=24
                    ),
                    The7SpaceWorkflowAction(
                        action_type="send_event_invitation",
                        target="contact",
                        content={
                            "event_type": "upcoming_exhibitions",
                            "personalized": True
                        },
                        delay_hours=168  # 1 week
                    )
                ]
            ),
            
            "vip_member_benefits": The7SpaceWorkflowTemplate(
                name="VIP Member Benefits",
                description="Special workflow for VIP community members",
                trigger_conditions={
                    "engagement_level": "vip",
                    "community_member": True
                },
                actions=[
                    The7SpaceWorkflowAction(
                        action_type="send_email",
                        target="contact",
                        content={
                            "template": "vip_welcome_email",
                            "subject": "Welcome to The 7 Space VIP Community",
                            "exclusive_benefits": True
                        },
                        delay_hours=1
                    ),
                    The7SpaceWorkflowAction(
                        action_type="grant_access",
                        target="contact",
                        content={
                            "access_type": "vip_events",
                            "early_booking": True,
                            "exclusive_content": True
                        },
                        delay_hours=2
                    ),
                    The7SpaceWorkflowAction(
                        action_type="assign_personal_curator",
                        target="contact",
                        content={
                            "curator_type": "art_advisor",
                            "personalized_recommendations": True
                        },
                        delay_hours=24
                    )
                ]
            ),
            
            "prospect_nurturing_sequence": The7SpaceWorkflowTemplate(
                name="Prospect Nurturing Sequence",
                description="Gentle nurturing sequence for cold prospects",
                trigger_conditions={
                    "engagement_level": ["cold", "warm"],
                    "nurturing_needed": True
                },
                actions=[
                    The7SpaceWorkflowAction(
                        action_type="send_email",
                        target="contact",
                        content={
                            "template": "educational_content_1",
                            "subject": "Discover the Healing Power of Art",
                            "content_type": "educational"
                        },
                        delay_hours=24
                    ),
                    The7SpaceWorkflowAction(
                        action_type="send_email",
                        target="contact",
                        content={
                            "template": "wellness_tips_1",
                            "subject": "5 Simple Wellness Practices for Daily Life",
                            "content_type": "wellness_tips"
                        },
                        delay_hours=168  # 1 week
                    ),
                    The7SpaceWorkflowAction(
                        action_type="send_invitation",
                        target="contact",
                        content={
                            "invitation_type": "free_meditation_session",
                            "subject": "Complimentary Meditation Session Invitation",
                            "low_pressure": True
                        },
                        delay_hours=336  # 2 weeks
                    )
                ]
            )
        }
    
    def _initialize_automation_config(self) -> Dict[str, Any]:
        """Initialize automation configuration"""
        return {
            "processing": {
                "batch_size": 10,
                "max_concurrent_workflows": 5,
                "retry_attempts": 3,
                "retry_delay_seconds": 300,
                "timeout_seconds": 600
            },
            "scheduling": {
                "sync_frequency": "every_15_minutes",
                "workflow_check_frequency": "every_5_minutes",
                "cleanup_frequency": "daily",
                "analytics_update_frequency": "hourly"
            },
            "notifications": {
                "admin_email": "admin@the7space.com",
                "gallery_team_email": "gallery@the7space.com",
                "wellness_team_email": "wellness@the7space.com",
                "slack_webhook": os.getenv("THE_7_SPACE_SLACK_WEBHOOK", ""),
                "enable_sms": False
            },
            "integrations": {
                "notion_api_rate_limit": 3,  # requests per second
                "wordpress_sync_enabled": True,
                "email_provider": "sendgrid",
                "calendar_integration": "google_calendar",
                "crm_integration": "notion"
            },
            "analytics": {
                "track_email_opens": True,
                "track_link_clicks": True,
                "track_website_visits": True,
                "track_appointment_bookings": True,
                "track_event_attendance": True,
                "generate_weekly_reports": True
            },
            "compliance": {
                "gdpr_compliant": True,
                "data_retention_days": 2555,  # 7 years
                "consent_tracking": True,
                "opt_out_handling": "immediate",
                "data_export_available": True
            }
        }
    
    def get_contact_segment(self, contact_data: Dict[str, Any]) -> Optional[str]:
        """Determine contact segment based on contact data"""
        contact_type = contact_data.get("contact_type")
        lead_source = contact_data.get("lead_source")
        engagement_level = contact_data.get("engagement_level", "cold")
        
        # Check each segment for matches
        for segment_name, segment in self.contact_segments.items():
            if (contact_type in [ct.value for ct in segment.contact_types] and
                lead_source in [ls.value for ls in segment.lead_sources]):
                return segment_name
        
        # Default to nurture prospects if no specific match
        return "nurture_prospects"
    
    def get_workflows_for_contact(self, contact_data: Dict[str, Any]) -> List[str]:
        """Get appropriate workflows for a contact"""
        segment = self.get_contact_segment(contact_data)
        if segment and segment in self.contact_segments:
            return self.contact_segments[segment].workflow_templates
        return ["prospect_nurturing_sequence"]
    
    def get_automation_config(self) -> Dict[str, Any]:
        """Get automation configuration"""
        return self.automation_config
    
    def get_notion_databases(self) -> Dict[str, str]:
        """Get Notion database configuration"""
        return self.notion_databases
    
    def get_contact_segments(self) -> Dict[str, The7SpaceContactSegment]:
        """Get all contact segments"""
        return self.contact_segments
    
    def get_workflow_templates(self) -> Dict[str, The7SpaceWorkflowTemplate]:
        """Get all workflow templates"""
        return self.workflow_templates

# Global instance for The 7 Space contact management
the7space_contact_manager = The7SpaceContactManager()
