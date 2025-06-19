#!/usr/bin/env python3
"""
Business Entity Configuration for The 7 Space Demo Environment

This module defines the business entity configuration specifically for The 7 Space
demo environment, including contact classification, workflow automation, and
database isolation settings.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from services.contact_workflow_automation import ContactType, LeadSource, WorkflowAction


class DemoBusinessEntity(str, Enum):
    """Business entities available in demo environment"""
    THE_7_SPACE = "the_7_space"
    # AM Consulting and HigherSelf disabled for demo
    # AM_CONSULTING = "am_consulting"  
    # HIGHERSELF_CORE = "higherself_core"


class The7SpaceContactType(str, Enum):
    """Contact types specific to The 7 Space"""
    ARTIST = "artist"
    GALLERY_VISITOR = "gallery_visitor"
    WELLNESS_CLIENT = "wellness_client"
    EVENT_ATTENDEE = "event_attendee"
    WORKSHOP_PARTICIPANT = "workshop_participant"
    COMMUNITY_MEMBER = "community_member"
    VENDOR = "vendor"
    MEDIA = "media"
    COLLECTOR = "collector"
    CURATOR = "curator"


class The7SpaceLeadSource(str, Enum):
    """Lead sources specific to The 7 Space"""
    GALLERY_VISIT = "gallery_visit"
    WEBSITE_CONTACT = "website_contact"
    SOCIAL_MEDIA = "social_media"
    EVENT_SIGNUP = "event_signup"
    WORKSHOP_REGISTRATION = "workshop_registration"
    ARTIST_REFERRAL = "artist_referral"
    WELLNESS_INQUIRY = "wellness_inquiry"
    EXHIBITION_INTEREST = "exhibition_interest"
    COMMUNITY_REFERRAL = "community_referral"
    WALK_IN = "walk_in"


@dataclass
class The7SpaceWorkflowConfig:
    """Workflow configuration for The 7 Space"""
    
    # Artist workflows
    artist_onboarding_enabled: bool = True
    artist_portfolio_review: bool = True
    artist_exhibition_planning: bool = True
    artist_commission_tracking: bool = True
    
    # Gallery visitor workflows
    visitor_welcome_sequence: bool = True
    visitor_followup_automation: bool = True
    visitor_event_invitations: bool = True
    visitor_newsletter_signup: bool = True
    
    # Wellness program workflows
    wellness_consultation_booking: bool = True
    wellness_program_enrollment: bool = True
    wellness_progress_tracking: bool = True
    wellness_renewal_reminders: bool = True
    
    # Event management workflows
    event_promotion_automation: bool = True
    event_registration_management: bool = True
    event_reminder_sequences: bool = True
    event_followup_surveys: bool = True
    
    # Community engagement workflows
    community_welcome_series: bool = True
    community_engagement_tracking: bool = True
    community_event_notifications: bool = True
    community_feedback_collection: bool = True


@dataclass
class The7SpaceDemoConfig:
    """Complete demo configuration for The 7 Space"""
    
    # Basic configuration
    entity_name: str = "The 7 Space"
    entity_id: str = "the_7_space"
    demo_mode: bool = True
    contact_count: int = 191
    
    # Database configuration
    primary_database: str = "the7space_contacts"
    isolated_data: bool = True
    
    # Contact classification
    default_contact_type: The7SpaceContactType = The7SpaceContactType.GALLERY_VISITOR
    auto_classification: bool = True
    
    # Workflow configuration
    workflows: The7SpaceWorkflowConfig = The7SpaceWorkflowConfig()
    
    # Lead scoring configuration
    lead_scoring_enabled: bool = True
    lead_score_threshold: int = 75
    priority_threshold: int = 85
    
    # Automation settings
    auto_task_creation: bool = True
    auto_followup_enabled: bool = True
    email_automation: bool = True
    calendar_integration: bool = True
    
    # Demo specific settings
    demo_dashboard_enabled: bool = True
    demo_analytics_enabled: bool = True
    sample_data_generation: bool = False  # Using real data
    
    # Integration settings
    notion_integration: bool = True
    gohighlevel_integration: bool = False  # Disabled for demo
    calendar_integration_enabled: bool = True


class The7SpaceContactClassifier:
    """Contact classification logic for The 7 Space"""
    
    @staticmethod
    def classify_contact(contact_data: Dict[str, Any]) -> The7SpaceContactType:
        """
        Classify a contact based on their data and interactions
        
        Args:
            contact_data: Dictionary containing contact information
            
        Returns:
            The7SpaceContactType: Classified contact type
        """
        # Extract relevant fields
        tags = contact_data.get("tags", [])
        interests = contact_data.get("interests", [])
        lead_source = contact_data.get("lead_source", "")
        notes = contact_data.get("notes", "").lower()
        
        # Classification logic
        if any(tag.lower() in ["artist", "creator", "painter", "sculptor"] for tag in tags):
            return The7SpaceContactType.ARTIST
            
        if any(interest.lower() in ["wellness", "meditation", "yoga", "healing"] for interest in interests):
            return The7SpaceContactType.WELLNESS_CLIENT
            
        if "workshop" in lead_source.lower() or "workshop" in notes:
            return The7SpaceContactType.WORKSHOP_PARTICIPANT
            
        if "event" in lead_source.lower() or "exhibition" in notes:
            return The7SpaceContactType.EVENT_ATTENDEE
            
        if any(tag.lower() in ["collector", "buyer"] for tag in tags):
            return The7SpaceContactType.COLLECTOR
            
        if any(tag.lower() in ["curator", "gallery"] for tag in tags):
            return The7SpaceContactType.CURATOR
            
        if any(tag.lower() in ["media", "press", "journalist"] for tag in tags):
            return The7SpaceContactType.MEDIA
            
        if any(tag.lower() in ["vendor", "supplier", "service"] for tag in tags):
            return The7SpaceContactType.VENDOR
            
        # Default classification
        return The7SpaceContactType.GALLERY_VISITOR
    
    @staticmethod
    def determine_lead_source(contact_data: Dict[str, Any]) -> The7SpaceLeadSource:
        """
        Determine lead source based on contact data
        
        Args:
            contact_data: Dictionary containing contact information
            
        Returns:
            The7SpaceLeadSource: Determined lead source
        """
        source = contact_data.get("lead_source", "").lower()
        referrer = contact_data.get("referrer", "").lower()
        
        if "gallery" in source or "visit" in source:
            return The7SpaceLeadSource.GALLERY_VISIT
            
        if "website" in source or "contact" in source:
            return The7SpaceLeadSource.WEBSITE_CONTACT
            
        if "social" in source or "instagram" in source or "facebook" in source:
            return The7SpaceLeadSource.SOCIAL_MEDIA
            
        if "event" in source:
            return The7SpaceLeadSource.EVENT_SIGNUP
            
        if "workshop" in source:
            return The7SpaceLeadSource.WORKSHOP_REGISTRATION
            
        if "artist" in referrer:
            return The7SpaceLeadSource.ARTIST_REFERRAL
            
        if "wellness" in source:
            return The7SpaceLeadSource.WELLNESS_INQUIRY
            
        if "exhibition" in source:
            return The7SpaceLeadSource.EXHIBITION_INTEREST
            
        if "community" in referrer or "member" in referrer:
            return The7SpaceLeadSource.COMMUNITY_REFERRAL
            
        # Default
        return The7SpaceLeadSource.WALK_IN


class The7SpaceWorkflowManager:
    """Workflow management for The 7 Space demo"""
    
    def __init__(self, config: The7SpaceDemoConfig):
        self.config = config
        self.classifier = The7SpaceContactClassifier()
    
    def get_workflows_for_contact(self, contact_type: The7SpaceContactType, 
                                 lead_source: The7SpaceLeadSource) -> List[str]:
        """
        Get appropriate workflows for a contact based on type and source
        
        Args:
            contact_type: The contact's classified type
            lead_source: How the contact was acquired
            
        Returns:
            List[str]: List of workflow names to execute
        """
        workflows = []
        
        # Base workflows for all contacts
        workflows.append("the7space_welcome_sequence")
        
        # Contact type specific workflows
        if contact_type == The7SpaceContactType.ARTIST:
            workflows.extend([
                "the7space_artist_onboarding",
                "the7space_artist_portfolio_review",
                "the7space_artist_community_intro"
            ])
            
        elif contact_type == The7SpaceContactType.WELLNESS_CLIENT:
            workflows.extend([
                "the7space_wellness_consultation",
                "the7space_wellness_program_info",
                "the7space_wellness_booking_followup"
            ])
            
        elif contact_type == The7SpaceContactType.GALLERY_VISITOR:
            workflows.extend([
                "the7space_visitor_followup",
                "the7space_upcoming_events",
                "the7space_newsletter_signup"
            ])
            
        elif contact_type == The7SpaceContactType.EVENT_ATTENDEE:
            workflows.extend([
                "the7space_event_followup",
                "the7space_future_events",
                "the7space_community_invitation"
            ])
            
        elif contact_type == The7SpaceContactType.COLLECTOR:
            workflows.extend([
                "the7space_collector_vip",
                "the7space_new_acquisitions",
                "the7space_private_viewings"
            ])
        
        # Lead source specific additions
        if lead_source == The7SpaceLeadSource.SOCIAL_MEDIA:
            workflows.append("the7space_social_engagement")
            
        elif lead_source == The7SpaceLeadSource.ARTIST_REFERRAL:
            workflows.append("the7space_referral_appreciation")
        
        return workflows


# Demo configuration instance
THE_7_SPACE_DEMO_CONFIG = The7SpaceDemoConfig()

# Export for use in other modules
__all__ = [
    'DemoBusinessEntity',
    'The7SpaceContactType', 
    'The7SpaceLeadSource',
    'The7SpaceWorkflowConfig',
    'The7SpaceDemoConfig',
    'The7SpaceContactClassifier',
    'The7SpaceWorkflowManager',
    'THE_7_SPACE_DEMO_CONFIG'
]
