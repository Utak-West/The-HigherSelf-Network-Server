"""
The 7 Space Lead Scoring Engine

Automated lead qualification and scoring system for The 7 Space gallery and wellness center.
Integrates with the 191 Notion contacts to provide intelligent lead prioritization.
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

class LeadSource(Enum):
    """Lead source enumeration"""
    WEBSITE = "website"
    GALLERY_VISIT = "gallery_visit"
    SOCIAL_MEDIA = "social_media"
    REFERRAL = "referral"
    EVENT = "event"
    EMAIL_CAMPAIGN = "email_campaign"
    WELLNESS_INQUIRY = "wellness_inquiry"
    ARTIST_REFERRAL = "artist_referral"
    GOOGLE_ADS = "google_ads"
    ORGANIC_SEARCH = "organic_search"

class InterestCategory(Enum):
    """Interest category enumeration"""
    CONTEMPORARY_ART = "contemporary_art"
    SCULPTURE = "sculpture"
    PAINTING = "painting"
    PHOTOGRAPHY = "photography"
    WELLNESS = "wellness"
    YOGA = "yoga"
    MEDITATION = "meditation"
    MASSAGE = "massage"
    REIKI = "reiki"
    ART_COLLECTING = "art_collecting"
    ART_EDUCATION = "art_education"
    EVENTS = "events"

class LeadStatus(Enum):
    """Lead status enumeration"""
    NEW = "new"
    QUALIFIED = "qualified"
    NURTURING = "nurturing"
    HOT = "hot"
    CONVERTED = "converted"
    COLD = "cold"
    UNQUALIFIED = "unqualified"

@dataclass
class LeadScore:
    """Lead scoring data model"""
    contact_id: str
    total_score: int
    demographic_score: int
    behavioral_score: int
    engagement_score: int
    intent_score: int
    last_calculated: datetime
    score_breakdown: Dict[str, int]
    recommendations: List[str]

@dataclass
class ScoringCriteria:
    """Scoring criteria configuration"""
    # Demographic scoring
    location_match: int = 15  # Local area
    age_range_match: int = 10  # Target demographic
    income_indicator: int = 20  # High-value prospect
    
    # Behavioral scoring
    website_visit: int = 5
    gallery_visit: int = 25
    event_attendance: int = 20
    email_open: int = 3
    email_click: int = 8
    social_engagement: int = 5
    
    # Engagement scoring
    inquiry_submitted: int = 30
    appointment_booked: int = 40
    purchase_made: int = 50
    referral_made: int = 25
    
    # Intent scoring
    pricing_page_view: int = 15
    booking_page_view: int = 20
    contact_form_view: int = 10
    multiple_visits: int = 10

class LeadScoringEngine:
    """
    Automated lead scoring and qualification system for The 7 Space.
    Analyzes the 191 contacts and provides intelligent lead prioritization.
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
        
        # Scoring configuration
        self.scoring_criteria = ScoringCriteria()
        
    async def score_all_leads(self) -> Dict[str, Any]:
        """
        Score all leads in the database and update their scores.
        
        Returns:
            Dict containing scoring results and statistics
        """
        try:
            logger.info("Starting lead scoring for all contacts")
            
            # Get all contacts
            contacts = await self._get_all_contacts()
            
            scoring_results = {
                "total_contacts": len(contacts),
                "scored_contacts": 0,
                "hot_leads": 0,
                "qualified_leads": 0,
                "cold_leads": 0,
                "errors": 0,
                "score_distribution": {},
                "top_leads": []
            }
            
            scored_leads = []
            
            for contact in contacts:
                try:
                    lead_score = await self.calculate_lead_score(contact["id"])
                    if lead_score:
                        scored_leads.append(lead_score)
                        scoring_results["scored_contacts"] += 1
                        
                        # Update contact with new score
                        await self._update_contact_score(contact["id"], lead_score)
                        
                except Exception as e:
                    logger.error(f"Failed to score contact {contact.get('id', 'unknown')}: {str(e)}")
                    scoring_results["errors"] += 1
            
            # Analyze results
            scoring_results.update(await self._analyze_scoring_results(scored_leads))
            
            logger.info(f"Completed lead scoring: {scoring_results['scored_contacts']} contacts scored")
            
            return scoring_results
            
        except Exception as e:
            logger.error(f"Failed to score all leads: {str(e)}")
            return {"error": str(e)}
    
    async def calculate_lead_score(self, contact_id: str) -> Optional[LeadScore]:
        """
        Calculate lead score for a specific contact.
        
        Args:
            contact_id: Contact identifier
            
        Returns:
            LeadScore object with calculated scores
        """
        try:
            # Get contact data
            contact = await self._get_contact_by_id(contact_id)
            if not contact:
                return None
            
            # Get behavioral data
            behavioral_data = await self._get_behavioral_data(contact_id)
            
            # Calculate individual scores
            demographic_score = await self._calculate_demographic_score(contact)
            behavioral_score = await self._calculate_behavioral_score(behavioral_data)
            engagement_score = await self._calculate_engagement_score(contact, behavioral_data)
            intent_score = await self._calculate_intent_score(behavioral_data)
            
            # Calculate total score
            total_score = demographic_score + behavioral_score + engagement_score + intent_score
            
            # Create score breakdown
            score_breakdown = {
                "demographic": demographic_score,
                "behavioral": behavioral_score,
                "engagement": engagement_score,
                "intent": intent_score,
                "bonus_points": 0  # For special circumstances
            }
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                contact, total_score, score_breakdown
            )
            
            lead_score = LeadScore(
                contact_id=contact_id,
                total_score=total_score,
                demographic_score=demographic_score,
                behavioral_score=behavioral_score,
                engagement_score=engagement_score,
                intent_score=intent_score,
                last_calculated=datetime.now(),
                score_breakdown=score_breakdown,
                recommendations=recommendations
            )
            
            logger.info(f"Calculated lead score for {contact_id}: {total_score}")
            
            return lead_score
            
        except Exception as e:
            logger.error(f"Failed to calculate lead score for {contact_id}: {str(e)}")
            return None
    
    async def get_hot_leads(self, threshold: int = 80) -> List[Dict[str, Any]]:
        """
        Get list of hot leads above the specified threshold.
        
        Args:
            threshold: Minimum score for hot leads
            
        Returns:
            List of hot leads with contact information
        """
        try:
            # Query contacts with high scores
            filter_condition = {
                "property": "Lead Score",
                "number": {
                    "greater_than_or_equal_to": threshold
                }
            }
            
            results = await self.notion_helper.query_database(
                database_id=self.contacts_db_id,
                filter_condition=filter_condition,
                sorts=[{
                    "property": "Lead Score",
                    "direction": "descending"
                }]
            )
            
            hot_leads = []
            for page in results:
                contact_data = await self._extract_contact_data(page)
                if contact_data:
                    hot_leads.append(contact_data)
            
            logger.info(f"Found {len(hot_leads)} hot leads with score >= {threshold}")
            
            return hot_leads
            
        except Exception as e:
            logger.error(f"Failed to get hot leads: {str(e)}")
            return []
    
    async def qualify_lead(self, contact_id: str, qualification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manually qualify a lead with additional information.
        
        Args:
            contact_id: Contact identifier
            qualification_data: Additional qualification information
            
        Returns:
            Dict containing qualification result
        """
        try:
            logger.info(f"Qualifying lead {contact_id}")
            
            # Get current lead score
            current_score = await self.calculate_lead_score(contact_id)
            if not current_score:
                return {"success": False, "error": "Contact not found"}
            
            # Apply qualification adjustments
            qualification_bonus = 0
            
            # Budget qualification
            if qualification_data.get("budget_confirmed"):
                qualification_bonus += 20
            
            # Timeline qualification
            if qualification_data.get("immediate_need"):
                qualification_bonus += 15
            
            # Decision maker qualification
            if qualification_data.get("decision_maker"):
                qualification_bonus += 10
            
            # Interest level qualification
            interest_level = qualification_data.get("interest_level", "medium")
            if interest_level == "high":
                qualification_bonus += 15
            elif interest_level == "very_high":
                qualification_bonus += 25
            
            # Update score with qualification bonus
            new_total_score = current_score.total_score + qualification_bonus
            current_score.score_breakdown["qualification_bonus"] = qualification_bonus
            current_score.total_score = new_total_score
            current_score.last_calculated = datetime.now()
            
            # Determine new status
            new_status = self._determine_lead_status(new_total_score)
            
            # Update contact in Notion
            await self._update_contact_qualification(contact_id, current_score, new_status, qualification_data)
            
            logger.info(f"Qualified lead {contact_id}: score {new_total_score}, status {new_status}")
            
            return {
                "success": True,
                "contact_id": contact_id,
                "old_score": current_score.total_score - qualification_bonus,
                "new_score": new_total_score,
                "qualification_bonus": qualification_bonus,
                "new_status": new_status
            }
            
        except Exception as e:
            logger.error(f"Failed to qualify lead: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_lead_recommendations(self, contact_id: str) -> List[str]:
        """
        Get personalized recommendations for a lead.
        
        Args:
            contact_id: Contact identifier
            
        Returns:
            List of recommendations
        """
        try:
            lead_score = await self.calculate_lead_score(contact_id)
            if not lead_score:
                return []
            
            return lead_score.recommendations
            
        except Exception as e:
            logger.error(f"Failed to get lead recommendations: {str(e)}")
            return []
    
    async def _get_all_contacts(self) -> List[Dict[str, Any]]:
        """Get all contacts from the database"""
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
    
    async def _get_contact_by_id(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get contact by ID"""
        try:
            filter_condition = {
                "property": "Contact ID",
                "rich_text": {"equals": contact_id}
            }
            
            results = await self.notion_helper.query_database(
                database_id=self.contacts_db_id,
                filter_condition=filter_condition
            )
            
            if not results:
                return None
            
            return await self._extract_contact_data(results[0])
            
        except Exception as e:
            logger.error(f"Failed to get contact by ID: {str(e)}")
            return None
