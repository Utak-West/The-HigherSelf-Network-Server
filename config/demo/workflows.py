#!/usr/bin/env python3
"""
The 7 Space Demo Workflow Automation Configuration

This module defines specific workflow automation sequences for The 7 Space demo,
including task management, lead qualification, response optimization, and 
targeted engagement sequences for different contact types.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from services.contact_workflow_automation import WorkflowAction, ContactType, LeadSource
from config.demo.business_entities import The7SpaceContactType, The7SpaceLeadSource


class WorkflowActionType(str, Enum):
    """Types of workflow actions available"""
    SEND_EMAIL = "send_email"
    CREATE_TASK = "create_task"
    SCHEDULE_FOLLOWUP = "schedule_followup"
    UPDATE_CONTACT = "update_contact"
    SEND_NOTIFICATION = "send_notification"
    BOOK_APPOINTMENT = "book_appointment"
    ADD_TO_SEQUENCE = "add_to_sequence"
    SCORE_LEAD = "score_lead"
    ASSIGN_AGENT = "assign_agent"
    CREATE_OPPORTUNITY = "create_opportunity"


@dataclass
class The7SpaceWorkflowAction:
    """Enhanced workflow action for The 7 Space"""
    action_type: WorkflowActionType
    delay_hours: int = 0
    priority: str = "medium"  # low, medium, high, urgent
    template_id: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = None
    conditions: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.conditions is None:
            self.conditions = {}


class The7SpaceWorkflowTemplates:
    """Workflow templates for The 7 Space demo"""
    
    @staticmethod
    def get_welcome_sequence() -> List[The7SpaceWorkflowAction]:
        """Universal welcome sequence for all new contacts"""
        return [
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.SEND_EMAIL,
                delay_hours=0,
                priority="high",
                template_id="the7space_welcome",
                subject="Welcome to The 7 Space Community! 🎨",
                content="""
                Welcome to The 7 Space! We're thrilled to have you join our vibrant 
                community of artists, wellness enthusiasts, and creative souls.
                
                What makes The 7 Space special:
                • Contemporary art gallery featuring local and international artists
                • Wellness center with meditation, yoga, and healing services
                • Community events, workshops, and creative gatherings
                • A space where art and wellness intersect
                
                We'll be in touch soon with personalized recommendations based on your interests.
                
                Warm regards,
                The 7 Space Team
                """,
                metadata={"campaign": "welcome", "entity": "the_7_space"}
            ),
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.CREATE_TASK,
                delay_hours=1,
                priority="medium",
                subject="Review new contact profile",
                content="New contact joined The 7 Space community. Review profile and determine personalized engagement strategy.",
                metadata={"task_type": "contact_review", "assignee": "community_manager"}
            ),
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.SCORE_LEAD,
                delay_hours=2,
                priority="low",
                metadata={"scoring_model": "the7space_engagement", "base_score": 50}
            )
        ]
    
    @staticmethod
    def get_artist_onboarding() -> List[The7SpaceWorkflowAction]:
        """Artist-specific onboarding sequence"""
        return [
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.SEND_EMAIL,
                delay_hours=24,
                priority="high",
                template_id="the7space_artist_welcome",
                subject="Welcome to The 7 Space Artist Community! 🎨✨",
                content="""
                Dear Artist,
                
                Welcome to The 7 Space artist community! We're excited to support 
                your creative journey and potentially showcase your work.
                
                Next steps for artists:
                1. Portfolio Review: We'd love to see your work
                2. Studio Visit: Schedule a visit to see our space
                3. Artist Resources: Access our artist support programs
                4. Exhibition Opportunities: Learn about upcoming shows
                
                Please reply with:
                • Your portfolio or website link
                • Your artistic medium and style
                • Your exhibition goals and timeline
                
                Looking forward to connecting!
                
                Best,
                The 7 Space Curatorial Team
                """,
                metadata={"campaign": "artist_onboarding", "contact_type": "artist"}
            ),
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.CREATE_TASK,
                delay_hours=25,
                priority="high",
                subject="Artist Portfolio Review Required",
                content="New artist contact needs portfolio review and potential studio visit scheduling.",
                metadata={"task_type": "portfolio_review", "assignee": "curator"}
            ),
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.SCHEDULE_FOLLOWUP,
                delay_hours=72,
                priority="medium",
                subject="Artist Onboarding Follow-up",
                content="Follow up on artist portfolio submission and schedule studio visit if interested.",
                metadata={"followup_type": "artist_engagement"}
            ),
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.UPDATE_CONTACT,
                delay_hours=1,
                priority="low",
                metadata={"tags": ["artist", "onboarding"], "status": "artist_prospect"}
            )
        ]
    
    @staticmethod
    def get_wellness_consultation() -> List[The7SpaceWorkflowAction]:
        """Wellness client consultation sequence"""
        return [
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.SEND_EMAIL,
                delay_hours=2,
                priority="high",
                template_id="the7space_wellness_intro",
                subject="Your Wellness Journey Begins at The 7 Space 🧘‍♀️",
                content="""
                Hello,
                
                Thank you for your interest in our wellness programs at The 7 Space!
                
                Our holistic wellness center offers:
                • Meditation and mindfulness sessions
                • Yoga classes for all levels
                • Energy healing and Reiki
                • Sound therapy and crystal healing
                • Personalized wellness consultations
                
                We'd love to schedule a complimentary consultation to discuss 
                your wellness goals and recommend the perfect program for you.
                
                Available consultation times:
                • Weekdays: 10am-6pm
                • Weekends: 9am-4pm
                
                Please reply with your preferred time, or call us at (555) 123-7777.
                
                Namaste,
                The 7 Space Wellness Team
                """,
                metadata={"campaign": "wellness_consultation", "contact_type": "wellness_client"}
            ),
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.CREATE_TASK,
                delay_hours=4,
                priority="high",
                subject="Schedule Wellness Consultation",
                content="New wellness prospect needs consultation scheduling. Follow up within 24 hours.",
                metadata={"task_type": "consultation_booking", "assignee": "wellness_coordinator"}
            ),
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.SEND_NOTIFICATION,
                delay_hours=24,
                priority="medium",
                content="Wellness consultation follow-up needed for new prospect",
                metadata={"notification_type": "task_reminder", "recipient": "wellness_team"}
            )
        ]
    
    @staticmethod
    def get_gallery_visitor_followup() -> List[The7SpaceWorkflowAction]:
        """Gallery visitor follow-up sequence"""
        return [
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.SEND_EMAIL,
                delay_hours=6,
                priority="medium",
                template_id="the7space_visitor_thanks",
                subject="Thank you for visiting The 7 Space! 🎨",
                content="""
                Dear Art Lover,
                
                Thank you for visiting The 7 Space! We hope you enjoyed exploring 
                our current exhibition and experiencing our unique space where 
                art and wellness converge.
                
                Stay connected with us:
                • Follow us on Instagram @the7space for daily inspiration
                • Join our newsletter for exhibition updates and events
                • Attend our monthly artist talks and openings
                • Explore our wellness programs
                
                Upcoming events you might enjoy:
                • Artist Talk: [Next scheduled talk]
                • Meditation & Art Session: Every Sunday 10am
                • Gallery Opening: [Next opening]
                
                We'd love to see you again soon!
                
                With gratitude,
                The 7 Space Team
                """,
                metadata={"campaign": "visitor_followup", "contact_type": "gallery_visitor"}
            ),
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.SCHEDULE_FOLLOWUP,
                delay_hours=168,  # 1 week
                priority="low",
                subject="Gallery Visitor Re-engagement",
                content="Follow up with gallery visitor about upcoming events and programs.",
                metadata={"followup_type": "visitor_reengagement"}
            )
        ]
    
    @staticmethod
    def get_event_followup() -> List[The7SpaceWorkflowAction]:
        """Event attendee follow-up sequence"""
        return [
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.SEND_EMAIL,
                delay_hours=12,
                priority="medium",
                template_id="the7space_event_thanks",
                subject="Thank you for joining us at The 7 Space! ✨",
                content="""
                Dear Friend,
                
                Thank you for attending our recent event at The 7 Space! 
                Your presence made the evening even more special.
                
                We hope you:
                • Connected with fellow art and wellness enthusiasts
                • Discovered new artists and perspectives
                • Felt inspired by our community
                
                What's next:
                • Share your experience on social media (tag @the7space)
                • Join our community newsletter for future events
                • Explore our ongoing exhibitions and wellness programs
                • Consider becoming a member for exclusive benefits
                
                Upcoming events:
                [List of next 3 events]
                
                Thank you for being part of The 7 Space community!
                
                Warmly,
                The 7 Space Team
                """,
                metadata={"campaign": "event_followup", "contact_type": "event_attendee"}
            ),
            The7SpaceWorkflowAction(
                action_type=WorkflowActionType.CREATE_TASK,
                delay_hours=24,
                priority="low",
                subject="Event Attendee Engagement Review",
                content="Review event attendee engagement and consider for membership invitation.",
                metadata={"task_type": "engagement_review", "assignee": "community_manager"}
            )
        ]


class The7SpaceLeadScoring:
    """Lead scoring system for The 7 Space"""
    
    @staticmethod
    def calculate_lead_score(contact_data: Dict[str, Any]) -> int:
        """
        Calculate lead score based on contact data and engagement
        
        Args:
            contact_data: Dictionary containing contact information
            
        Returns:
            int: Lead score (0-100)
        """
        score = 0
        
        # Base score
        score += 20
        
        # Contact type scoring
        contact_type = contact_data.get("contact_type", "")
        if contact_type == "artist":
            score += 25  # High value for artists
        elif contact_type == "wellness_client":
            score += 20  # High value for wellness clients
        elif contact_type == "collector":
            score += 30  # Highest value for collectors
        elif contact_type == "gallery_visitor":
            score += 15
        
        # Lead source scoring
        lead_source = contact_data.get("lead_source", "")
        if lead_source in ["artist_referral", "community_referral"]:
            score += 15  # Referrals are valuable
        elif lead_source == "gallery_visit":
            score += 10  # Physical visits show interest
        elif lead_source == "event_signup":
            score += 12  # Event engagement is positive
        
        # Engagement scoring
        email_opens = contact_data.get("email_opens", 0)
        score += min(email_opens * 2, 10)  # Max 10 points for email engagement
        
        website_visits = contact_data.get("website_visits", 0)
        score += min(website_visits * 1, 5)  # Max 5 points for website visits
        
        # Interest indicators
        interests = contact_data.get("interests", [])
        if "art_collecting" in interests:
            score += 15
        if "wellness" in interests:
            score += 10
        if "events" in interests:
            score += 8
        
        # Demographic factors
        location = contact_data.get("location", "").lower()
        if "local" in location or "nearby" in location:
            score += 5  # Local contacts are easier to engage
        
        # Ensure score is within bounds
        return min(max(score, 0), 100)


class The7SpaceWorkflowEngine:
    """Main workflow engine for The 7 Space demo"""
    
    def __init__(self):
        self.templates = The7SpaceWorkflowTemplates()
        self.lead_scorer = The7SpaceLeadScoring()
    
    def get_workflow_for_contact(self, contact_type: The7SpaceContactType, 
                                lead_source: The7SpaceLeadSource,
                                contact_data: Dict[str, Any]) -> List[The7SpaceWorkflowAction]:
        """
        Get complete workflow sequence for a contact
        
        Args:
            contact_type: The contact's classified type
            lead_source: How the contact was acquired
            contact_data: Additional contact information
            
        Returns:
            List[The7SpaceWorkflowAction]: Complete workflow sequence
        """
        workflow = []
        
        # Start with welcome sequence for all contacts
        workflow.extend(self.templates.get_welcome_sequence())
        
        # Add contact type specific workflows
        if contact_type == The7SpaceContactType.ARTIST:
            workflow.extend(self.templates.get_artist_onboarding())
            
        elif contact_type == The7SpaceContactType.WELLNESS_CLIENT:
            workflow.extend(self.templates.get_wellness_consultation())
            
        elif contact_type == The7SpaceContactType.GALLERY_VISITOR:
            workflow.extend(self.templates.get_gallery_visitor_followup())
            
        elif contact_type == The7SpaceContactType.EVENT_ATTENDEE:
            workflow.extend(self.templates.get_event_followup())
        
        # Calculate and add lead scoring
        lead_score = self.lead_scorer.calculate_lead_score(contact_data)
        
        # Add high-priority follow-up for high-scoring leads
        if lead_score >= 80:
            workflow.append(
                The7SpaceWorkflowAction(
                    action_type=WorkflowActionType.CREATE_TASK,
                    delay_hours=2,
                    priority="urgent",
                    subject="High-Value Lead - Immediate Follow-up Required",
                    content=f"High-scoring lead (score: {lead_score}) requires immediate personal attention.",
                    metadata={"task_type": "high_value_lead", "lead_score": lead_score}
                )
            )
        
        return workflow


# Export for use in other modules
__all__ = [
    'WorkflowActionType',
    'The7SpaceWorkflowAction',
    'The7SpaceWorkflowTemplates',
    'The7SpaceLeadScoring',
    'The7SpaceWorkflowEngine'
]
