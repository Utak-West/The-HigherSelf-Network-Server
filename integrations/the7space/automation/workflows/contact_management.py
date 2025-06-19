"""
The 7 Space Contact Management Automation

Automated contact management system for The 7 Space's 191 contacts with intelligent
classification, lead nurturing, and workflow orchestration.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json

from notion_client import Client
from ..config.the7space_config import the7space_config
from ..utils.notion_helpers import NotionHelper
from ..utils.error_recovery import ErrorRecoveryManager
from ..utils.logging_helpers import setup_logger

# Setup logging
logger = setup_logger(__name__)

class ContactType(Enum):
    """Contact type classification for The 7 Space"""
    GALLERY_VISITOR = "gallery_visitor"
    ARTIST = "artist"
    COLLECTOR = "collector"
    WELLNESS_CLIENT = "wellness_client"
    EVENT_ATTENDEE = "event_attendee"
    MEDIA = "media"
    VENDOR = "vendor"
    GENERAL_INQUIRY = "general_inquiry"

class ContactStatus(Enum):
    """Contact status enumeration"""
    NEW = "new"
    ACTIVE = "active"
    ENGAGED = "engaged"
    CONVERTED = "converted"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class LeadSource(Enum):
    """Lead source tracking"""
    WEBSITE = "website"
    GALLERY_VISIT = "gallery_visit"
    SOCIAL_MEDIA = "social_media"
    REFERRAL = "referral"
    EVENT = "event"
    EMAIL_CAMPAIGN = "email_campaign"
    GOOGLE_ADS = "google_ads"
    ORGANIC_SEARCH = "organic_search"

@dataclass
class Contact:
    """Contact data model for The 7 Space"""
    id: str
    name: str
    email: str
    phone: str
    contact_type: ContactType
    status: ContactStatus
    lead_source: LeadSource
    interests: List[str]
    lead_score: int
    last_interaction: datetime
    created_at: datetime
    updated_at: datetime
    notion_page_id: Optional[str] = None
    notes: str = ""
    tags: List[str] = None
    location: str = ""
    preferred_contact_method: str = "email"
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class ContactManager:
    """
    Automated contact management system for The 7 Space's 191 contacts.
    Handles classification, lead scoring, and workflow automation.
    """
    
    def __init__(self):
        self.config = the7space_config
        self.notion_client = Client(auth=self.config.notion_api_token)
        self.notion_helper = NotionHelper(self.notion_client)
        self.error_manager = ErrorRecoveryManager()
        
        # Database IDs
        self.contacts_db_id = self.config.get_database_id("contacts")
        self.analytics_db_id = self.config.get_database_id("analytics")
        
        if not self.contacts_db_id:
            raise ValueError("Contacts database ID not configured")
    
    async def process_all_contacts(self) -> Dict[str, Any]:
        """
        Process all 191 contacts with classification and scoring.
        
        Returns:
            Dict containing processing results and statistics
        """
        try:
            logger.info("Starting automated processing of all contacts")
            
            # Get all contacts from Notion
            contacts = await self._get_all_contacts()
            
            processing_results = {
                "total_contacts": len(contacts),
                "processed_contacts": 0,
                "classified_contacts": 0,
                "scored_contacts": 0,
                "workflow_triggered": 0,
                "errors": 0,
                "contact_breakdown": {},
                "high_value_contacts": []
            }
            
            for contact_data in contacts:
                try:
                    # Process individual contact
                    result = await self._process_individual_contact(contact_data)
                    
                    if result["success"]:
                        processing_results["processed_contacts"] += 1
                        
                        if result.get("classified"):
                            processing_results["classified_contacts"] += 1
                        
                        if result.get("scored"):
                            processing_results["scored_contacts"] += 1
                        
                        if result.get("workflow_triggered"):
                            processing_results["workflow_triggered"] += 1
                        
                        # Track contact types
                        contact_type = result.get("contact_type", "unknown")
                        processing_results["contact_breakdown"][contact_type] = \
                            processing_results["contact_breakdown"].get(contact_type, 0) + 1
                        
                        # Track high-value contacts
                        if result.get("lead_score", 0) >= 80:
                            processing_results["high_value_contacts"].append({
                                "id": contact_data.get("id"),
                                "name": contact_data.get("name"),
                                "score": result.get("lead_score"),
                                "type": contact_type
                            })
                    
                except Exception as e:
                    logger.error(f"Failed to process contact {contact_data.get('id', 'unknown')}: {str(e)}")
                    processing_results["errors"] += 1
            
            logger.info(f"Completed contact processing: {processing_results['processed_contacts']} contacts processed")
            
            return processing_results
            
        except Exception as e:
            logger.error(f"Failed to process all contacts: {str(e)}")
            return {"error": str(e)}
    
    async def classify_contact(self, contact_id: str, classification_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Classify a contact based on their interactions and data.
        
        Args:
            contact_id: Contact identifier
            classification_data: Optional additional classification data
            
        Returns:
            Dict containing classification result
        """
        try:
            logger.info(f"Classifying contact {contact_id}")
            
            # Get contact data
            contact = await self._get_contact_by_id(contact_id)
            if not contact:
                return {"success": False, "error": "Contact not found"}
            
            # Analyze contact data for classification
            classification_result = await self._analyze_contact_for_classification(contact, classification_data)
            
            # Update contact with classification
            await self._update_contact_classification(contact_id, classification_result)
            
            # Trigger appropriate workflows
            await self._trigger_classification_workflows(contact_id, classification_result)
            
            logger.info(f"Successfully classified contact {contact_id} as {classification_result['contact_type']}")
            
            return {
                "success": True,
                "contact_id": contact_id,
                "contact_type": classification_result["contact_type"],
                "confidence": classification_result["confidence"],
                "recommended_actions": classification_result["recommended_actions"]
            }
            
        except Exception as e:
            logger.error(f"Failed to classify contact: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_contact_interaction(self, contact_id: str, interaction_data: Dict[str, Any]) -> bool:
        """
        Update contact with new interaction data.
        
        Args:
            contact_id: Contact identifier
            interaction_data: Interaction details
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Updating interaction for contact {contact_id}")
            
            # Get current contact
            contact = await self._get_contact_by_id(contact_id)
            if not contact:
                return False
            
            # Process interaction
            interaction_result = await self._process_interaction(contact, interaction_data)
            
            # Update contact record
            await self._update_contact_with_interaction(contact_id, interaction_result)
            
            # Recalculate lead score if needed
            if interaction_result.get("score_impact", 0) > 0:
                await self._recalculate_lead_score(contact_id)
            
            # Check for workflow triggers
            await self._check_interaction_triggers(contact_id, interaction_result)
            
            logger.info(f"Successfully updated interaction for contact {contact_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update contact interaction: {str(e)}")
            return False
    
    async def get_contact_recommendations(self, contact_id: str) -> List[str]:
        """
        Get personalized recommendations for a contact.
        
        Args:
            contact_id: Contact identifier
            
        Returns:
            List of recommendations
        """
        try:
            contact = await self._get_contact_by_id(contact_id)
            if not contact:
                return []
            
            recommendations = []
            
            # Analyze contact data
            contact_type = contact.get("contact_type", "general_inquiry")
            interests = contact.get("interests", [])
            lead_score = contact.get("lead_score", 0)
            last_interaction = contact.get("last_interaction")
            
            # Generate type-specific recommendations
            if contact_type == "gallery_visitor":
                recommendations.extend(await self._get_gallery_recommendations(contact))
            elif contact_type == "wellness_client":
                recommendations.extend(await self._get_wellness_recommendations(contact))
            elif contact_type == "artist":
                recommendations.extend(await self._get_artist_recommendations(contact))
            elif contact_type == "collector":
                recommendations.extend(await self._get_collector_recommendations(contact))
            
            # Add engagement recommendations
            if lead_score >= 80:
                recommendations.append("Schedule personal consultation")
                recommendations.append("Invite to VIP events")
            elif lead_score >= 60:
                recommendations.append("Send targeted email campaign")
                recommendations.append("Invite to upcoming events")
            else:
                recommendations.append("Send welcome series")
                recommendations.append("Share relevant content")
            
            # Add re-engagement recommendations
            if last_interaction:
                days_since_interaction = (datetime.now() - last_interaction).days
                if days_since_interaction > 30:
                    recommendations.append("Re-engagement campaign needed")
                elif days_since_interaction > 90:
                    recommendations.append("Win-back campaign recommended")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get contact recommendations: {str(e)}")
            return []
    
    async def segment_contacts(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Segment contacts based on specified criteria.
        
        Args:
            criteria: Segmentation criteria
            
        Returns:
            List of contacts matching criteria
        """
        try:
            logger.info(f"Segmenting contacts with criteria: {criteria}")
            
            # Build filter conditions
            filter_conditions = await self._build_segmentation_filter(criteria)
            
            # Query contacts
            results = await self.notion_helper.query_database(
                database_id=self.contacts_db_id,
                filter_condition=filter_conditions
            )
            
            segmented_contacts = []
            for page in results:
                contact_data = await self._extract_contact_data(page)
                if contact_data:
                    segmented_contacts.append(contact_data)
            
            logger.info(f"Segmented {len(segmented_contacts)} contacts")
            
            return segmented_contacts
            
        except Exception as e:
            logger.error(f"Failed to segment contacts: {str(e)}")
            return []
    
    async def _get_all_contacts(self) -> List[Dict[str, Any]]:
        """Get all contacts from Notion database"""
        try:
            results = await self.notion_helper.query_database(
                database_id=self.contacts_db_id
            )
            
            contacts = []
            for page in results:
                contact_data = await self._extract_contact_data(page)
                if contact_data:
                    contacts.append(contact_data)
            
            return contacts
            
        except Exception as e:
            logger.error(f"Failed to get all contacts: {str(e)}")
            return []
    
    async def _process_individual_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual contact with classification and scoring"""
        try:
            contact_id = contact_data.get("id")
            
            # Classify contact
            classification_result = await self._analyze_contact_for_classification(contact_data)
            
            # Calculate lead score
            lead_score = await self._calculate_contact_lead_score(contact_data)
            
            # Update contact in Notion
            await self._update_contact_processing_results(contact_id, classification_result, lead_score)
            
            # Check for workflow triggers
            workflow_triggered = await self._check_processing_triggers(contact_id, classification_result, lead_score)
            
            return {
                "success": True,
                "contact_id": contact_id,
                "classified": True,
                "scored": True,
                "contact_type": classification_result["contact_type"],
                "lead_score": lead_score,
                "workflow_triggered": workflow_triggered
            }
            
        except Exception as e:
            logger.error(f"Failed to process individual contact: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_contact_for_classification(self, contact_data: Dict[str, Any], 
                                                additional_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze contact data to determine classification"""
        try:
            # Extract relevant data
            interests = contact_data.get("interests", [])
            interactions = contact_data.get("interactions", [])
            source = contact_data.get("lead_source", "")
            notes = contact_data.get("notes", "").lower()
            
            # Classification scoring
            classification_scores = {
                ContactType.GALLERY_VISITOR: 0,
                ContactType.ARTIST: 0,
                ContactType.COLLECTOR: 0,
                ContactType.WELLNESS_CLIENT: 0,
                ContactType.EVENT_ATTENDEE: 0,
                ContactType.MEDIA: 0,
                ContactType.VENDOR: 0,
                ContactType.GENERAL_INQUIRY: 10  # Base score
            }
            
            # Analyze interests
            for interest in interests:
                interest_lower = interest.lower()
                if any(term in interest_lower for term in ["art", "painting", "sculpture", "gallery"]):
                    classification_scores[ContactType.GALLERY_VISITOR] += 20
                    classification_scores[ContactType.COLLECTOR] += 15
                
                if any(term in interest_lower for term in ["wellness", "yoga", "massage", "meditation"]):
                    classification_scores[ContactType.WELLNESS_CLIENT] += 25
                
                if any(term in interest_lower for term in ["artist", "exhibition", "studio"]):
                    classification_scores[ContactType.ARTIST] += 30
            
            # Analyze source
            if source == "gallery_visit":
                classification_scores[ContactType.GALLERY_VISITOR] += 30
            elif source == "event":
                classification_scores[ContactType.EVENT_ATTENDEE] += 25
            elif source == "wellness_inquiry":
                classification_scores[ContactType.WELLNESS_CLIENT] += 35
            
            # Analyze notes for keywords
            if any(term in notes for term in ["artist", "artwork", "exhibition"]):
                classification_scores[ContactType.ARTIST] += 20
            
            if any(term in notes for term in ["collect", "purchase", "buy"]):
                classification_scores[ContactType.COLLECTOR] += 25
            
            if any(term in notes for term in ["media", "press", "interview", "article"]):
                classification_scores[ContactType.MEDIA] += 40
            
            # Determine best classification
            best_type = max(classification_scores, key=classification_scores.get)
            confidence = classification_scores[best_type] / 100.0  # Convert to percentage
            
            # Generate recommended actions
            recommended_actions = await self._generate_classification_actions(best_type, confidence)
            
            return {
                "contact_type": best_type.value,
                "confidence": min(confidence, 1.0),
                "scores": {k.value: v for k, v in classification_scores.items()},
                "recommended_actions": recommended_actions
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze contact for classification: {str(e)}")
            return {
                "contact_type": ContactType.GENERAL_INQUIRY.value,
                "confidence": 0.5,
                "scores": {},
                "recommended_actions": []
            }
