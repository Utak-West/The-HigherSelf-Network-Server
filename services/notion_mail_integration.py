#!/usr/bin/env python3
"""
Notion Mail Integration Service for HigherSelf Network Server

Automated email classification and workflow automation for multi-entity business structure,
integrating with the existing Notion-based automation platform serving:
- The 7 Space (191 contacts)
- AM Consulting (1,300 contacts) 
- HigherSelf Core (1,300 contacts)

Follows established patterns from services/notion_service.py and config/business_entity_workflows.py
"""

import asyncio
import json
import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from pydantic import BaseModel, Field
from notion_client import Client

from config.business_entity_workflows import BusinessEntityWorkflows
from config.testing_mode import TestingMode, is_api_disabled
from models.notion_db_models import WorkflowInstance
from services.ai_provider_service import AIProviderService
from services.contact_workflow_automation import ContactWorkflowAutomation, ContactWorkflowTrigger
from services.notion_service import NotionService


class EmailCategory(str, Enum):
    """Email classification categories with priority order."""
    AM_CONSULTING = "A.M. Consulting"
    HIGHERSELF_NETWORK = "The HigherSelf Network"
    THE_7_SPACE_GALLERY = "The 7 Space | Art Gallery"
    THE_7_SPACE_WELLNESS = "The 7 Space | Wellness Center"
    TECHNICAL = "Technical"
    HIGHERSELF = "HigherSelf"
    PERSONAL = "Personal"
    OTHER = "Other"


class EmailClassificationResult(BaseModel):
    """Result of email classification analysis."""
    category: EmailCategory
    confidence: float = Field(ge=0.0, le=1.0)
    business_entity: Optional[str] = None
    reasoning: str
    suggested_actions: List[str] = Field(default_factory=list)
    priority_score: int = Field(ge=1, le=8)


class EmailContent(BaseModel):
    """Email content structure for processing."""
    sender_email: str
    sender_name: Optional[str] = None
    subject: str
    body: str
    received_at: datetime
    message_id: str
    thread_id: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)


class NotionMailIntegrationConfig(BaseModel):
    """Configuration for Notion Mail Integration."""
    notion_api_token: str
    openai_api_key: str
    enable_auto_classification: bool = True
    enable_workflow_automation: bool = True
    confidence_threshold: float = 0.7
    testing_mode: bool = False
    
    # Business entity response time SLAs (hours)
    am_consulting_response_time: int = 4
    the_7_space_response_time: int = 24
    higherself_core_response_time: int = 12


class NotionMailIntegrationService:
    """
    Notion Mail Integration Service for automated email classification and workflow automation.
    
    Integrates with existing NotionService and BusinessEntityWorkflows patterns.
    """

    def __init__(self, config: NotionMailIntegrationConfig):
        """Initialize the Notion Mail Integration service."""
        self.config = config
        self.notion_client = Client(auth=config.notion_api_token)
        
        # Initialize existing services following established patterns
        self.notion_service = NotionService()
        self.ai_provider = AIProviderService()
        self.workflow_automation = ContactWorkflowAutomation()
        self.business_workflows = BusinessEntityWorkflows()
        
        # Load classification configurations
        self._load_classification_configs()
        
        # Category configuration with colors and priorities
        self.category_config = {
            EmailCategory.AM_CONSULTING: {"priority": 1, "color": "blue", "entity": "am_consulting"},
            EmailCategory.HIGHERSELF_NETWORK: {"priority": 2, "color": "green", "entity": "higherself_core"},
            EmailCategory.THE_7_SPACE_GALLERY: {"priority": 3, "color": "purple", "entity": "the_7_space"},
            EmailCategory.THE_7_SPACE_WELLNESS: {"priority": 4, "color": "orange", "entity": "the_7_space"},
            EmailCategory.TECHNICAL: {"priority": 5, "color": "red", "entity": None},
            EmailCategory.HIGHERSELF: {"priority": 6, "color": "teal", "entity": "higherself_core"},
            EmailCategory.PERSONAL: {"priority": 7, "color": "yellow", "entity": None},
            EmailCategory.OTHER: {"priority": 8, "color": "gray", "entity": None}
        }
        
        logger.info("Notion Mail Integration service initialized")
        
        # Check if we're in testing mode
        if is_api_disabled("notion") or config.testing_mode:
            logger.warning("TESTING MODE ACTIVE: Email classification will be simulated")

    def _load_classification_configs(self) -> None:
        """Load JSON classification configuration files."""
        config_dir = "config/email_classification"
        self.classification_configs = {}
        
        for category in EmailCategory:
            config_file = f"{config_dir}/{category.value.lower().replace(' ', '_').replace('|', '').replace('.', '')}.json"
            try:
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        self.classification_configs[category] = json.load(f)
                        logger.debug(f"Loaded classification config for {category.value}")
                else:
                    logger.warning(f"Classification config not found: {config_file}")
                    self.classification_configs[category] = self._get_default_config(category)
            except Exception as e:
                logger.error(f"Error loading classification config for {category.value}: {e}")
                self.classification_configs[category] = self._get_default_config(category)

    def _get_default_config(self, category: EmailCategory) -> Dict[str, Any]:
        """Get default classification configuration for a category."""
        base_config = {
            "keywords": [],
            "domain_patterns": [],
            "sender_patterns": [],
            "subject_patterns": [],
            "confidence_threshold": 0.7,
            "business_rules": []
        }
        
        # Category-specific default configurations
        if category == EmailCategory.AM_CONSULTING:
            base_config.update({
                "keywords": ["consulting", "business", "strategy", "proposal", "client", "meeting"],
                "domain_patterns": ["amconsulting.com", "business", "consulting", "corp", "inc"],
                "confidence_threshold": 0.95
            })
        elif category == EmailCategory.THE_7_SPACE_GALLERY:
            base_config.update({
                "keywords": ["art", "gallery", "exhibition", "artist", "artwork", "curator"],
                "domain_patterns": ["the7space.com", "art", "gallery", "studio"],
                "confidence_threshold": 0.92
            })
        elif category == EmailCategory.THE_7_SPACE_WELLNESS:
            base_config.update({
                "keywords": ["wellness", "meditation", "yoga", "healing", "therapy", "mindfulness"],
                "domain_patterns": ["the7space.com", "wellness", "health", "spa"],
                "confidence_threshold": 0.88
            })
        elif category == EmailCategory.HIGHERSELF_NETWORK:
            base_config.update({
                "keywords": ["higherself", "network", "community", "platform", "ecosystem"],
                "domain_patterns": ["join.higherselflife.com", "higherselfnetwork"],
                "confidence_threshold": 0.95
            })
        elif category == EmailCategory.TECHNICAL:
            base_config.update({
                "keywords": ["server", "api", "bug", "error", "system", "technical", "support"],
                "domain_patterns": ["github.com", "tech", "dev", "support"],
                "confidence_threshold": 0.90
            })
        
        return base_config

    async def classify_email(self, email: EmailContent) -> EmailClassificationResult:
        """
        Classify email using AI analysis and business rules.
        
        Args:
            email: EmailContent to classify
            
        Returns:
            EmailClassificationResult with classification details
        """
        logger.info(f"Classifying email from {email.sender_email}: {email.subject}")
        
        try:
            # Check if we're in testing mode
            if is_api_disabled("notion") or self.config.testing_mode:
                return self._simulate_classification(email)
            
            # Step 1: Rule-based pre-classification
            rule_based_result = self._apply_business_rules(email)
            
            # Step 2: AI-powered classification
            ai_result = await self._ai_classify_email(email)
            
            # Step 3: Combine results and determine final classification
            final_result = self._combine_classification_results(rule_based_result, ai_result, email)
            
            # Step 4: Validate business entity boundaries
            validated_result = self._validate_entity_boundaries(final_result)
            
            logger.info(f"Email classified as {validated_result.category.value} with {validated_result.confidence:.2f} confidence")
            
            return validated_result
            
        except Exception as e:
            logger.error(f"Error classifying email: {e}")
            # Return default classification on error
            return EmailClassificationResult(
                category=EmailCategory.OTHER,
                confidence=0.5,
                reasoning=f"Classification failed: {str(e)}",
                priority_score=8
            )

    def _simulate_classification(self, email: EmailContent) -> EmailClassificationResult:
        """Simulate email classification for testing mode."""
        TestingMode.log_attempted_api_call(
            api_name="notion_mail_integration",
            endpoint="classify_email",
            method="POST",
            params={"sender": email.sender_email, "subject": email.subject}
        )
        
        # Simple simulation based on sender domain
        domain = email.sender_email.split('@')[1].lower()
        
        if 'amconsulting' in domain or 'consulting' in domain:
            category = EmailCategory.AM_CONSULTING
            confidence = 0.95
        elif 'the7space' in domain or 'art' in domain:
            category = EmailCategory.THE_7_SPACE_GALLERY
            confidence = 0.92
        elif 'higherself' in domain:
            category = EmailCategory.HIGHERSELF_NETWORK
            confidence = 0.95
        else:
            category = EmailCategory.OTHER
            confidence = 0.70
        
        return EmailClassificationResult(
            category=category,
            confidence=confidence,
            reasoning="[TESTING MODE] Simulated classification based on domain",
            priority_score=self.category_config[category]["priority"]
        )

    def _apply_business_rules(self, email: EmailContent) -> Optional[EmailClassificationResult]:
        """Apply business rules for email classification."""
        sender_domain = email.sender_email.split('@')[1].lower()
        sender_local = email.sender_email.split('@')[0].lower()
        subject_lower = email.subject.lower()
        body_lower = email.body.lower()
        
        # Strict business entity boundary rules
        for category, config in self.classification_configs.items():
            domain_patterns = config.get("domain_patterns", [])
            keywords = config.get("keywords", [])
            
            # Check domain patterns
            domain_match = any(pattern in sender_domain for pattern in domain_patterns)
            
            # Check keywords in subject and body
            keyword_matches = sum(1 for keyword in keywords if keyword in subject_lower or keyword in body_lower)
            keyword_score = keyword_matches / max(len(keywords), 1)
            
            # Calculate confidence based on matches
            confidence = 0.0
            if domain_match:
                confidence += 0.6
            confidence += keyword_score * 0.4
            
            if confidence >= config.get("confidence_threshold", 0.7):
                return EmailClassificationResult(
                    category=category,
                    confidence=confidence,
                    business_entity=self.category_config[category]["entity"],
                    reasoning=f"Rule-based match: domain={domain_match}, keywords={keyword_matches}/{len(keywords)}",
                    priority_score=self.category_config[category]["priority"]
                )
        
        return None

    async def _ai_classify_email(self, email: EmailContent) -> EmailClassificationResult:
        """Use AI to classify email content."""
        # Prepare classification prompt
        categories_desc = "\n".join([
            f"{i+1}. {cat.value} (Priority {self.category_config[cat]['priority']})"
            for i, cat in enumerate(EmailCategory)
        ])
        
        prompt = f"""
        Classify this email into one of the following categories for the HigherSelf Network multi-entity business:

        Categories:
        {categories_desc}

        Business Entity Boundaries:
        - A.M. Consulting ≠ The HigherSelf Network ≠ The 7 Space
        - HigherSelf (Nonprofit) [https://higherselflife.com/] ≠ The HigherSelf Network (Ecosystem) [https://join.higherselflife.com/]
        - The 7 Space | Art Gallery ≠ The 7 Space | Wellness Center [https://the7space.com/]

        Email Details:
        From: {email.sender_email}
        Subject: {email.subject}
        Body: {email.body[:1000]}...

        Respond with JSON:
        {{
            "category": "category_name",
            "confidence": 0.0-1.0,
            "reasoning": "explanation",
            "business_entity": "entity_name_or_null",
            "suggested_actions": ["action1", "action2"]
        }}
        """
        
        try:
            # Use existing AI provider service
            response = await self.ai_provider.process_request({
                "provider": "openai",
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.1
            })
            
            if response and response.get("success"):
                ai_result = json.loads(response["content"])
                
                # Map category name to enum
                category = EmailCategory(ai_result["category"])
                
                return EmailClassificationResult(
                    category=category,
                    confidence=ai_result["confidence"],
                    business_entity=ai_result.get("business_entity"),
                    reasoning=ai_result["reasoning"],
                    suggested_actions=ai_result.get("suggested_actions", []),
                    priority_score=self.category_config[category]["priority"]
                )
            else:
                raise Exception("AI classification failed")
                
        except Exception as e:
            logger.error(f"AI classification error: {e}")
            # Fallback to rule-based classification
            return EmailClassificationResult(
                category=EmailCategory.OTHER,
                confidence=0.5,
                reasoning=f"AI classification failed, using fallback: {str(e)}",
                priority_score=8
            )

    def _combine_classification_results(
        self, 
        rule_result: Optional[EmailClassificationResult], 
        ai_result: EmailClassificationResult,
        email: EmailContent
    ) -> EmailClassificationResult:
        """Combine rule-based and AI classification results."""
        
        # If rule-based classification has high confidence, prefer it
        if rule_result and rule_result.confidence >= 0.9:
            return rule_result
        
        # If AI classification has high confidence and no strong rule match, use AI
        if ai_result.confidence >= 0.8 and (not rule_result or rule_result.confidence < 0.7):
            return ai_result
        
        # If both have moderate confidence, prefer rule-based for business entities
        if rule_result and rule_result.business_entity:
            return rule_result
        
        # Default to AI result
        return ai_result

    def _validate_entity_boundaries(self, result: EmailClassificationResult) -> EmailClassificationResult:
        """Validate and enforce strict business entity boundaries."""
        
        # Ensure business entity mapping is correct
        if result.category in self.category_config:
            correct_entity = self.category_config[result.category]["entity"]
            if result.business_entity != correct_entity:
                result.business_entity = correct_entity
                result.reasoning += " [Entity boundary corrected]"
        
        return result

    async def process_email_workflow(self, email: EmailContent, classification: EmailClassificationResult) -> Dict[str, Any]:
        """
        Process email workflow automation based on classification.
        
        Args:
            email: EmailContent that was classified
            classification: EmailClassificationResult from classification
            
        Returns:
            Dict containing workflow processing results
        """
        logger.info(f"Processing workflow for {classification.category.value} email from {email.sender_email}")
        
        try:
            # Skip workflow for non-business categories
            if not classification.business_entity:
                logger.info(f"Skipping workflow for {classification.category.value} - no business entity")
                return {"success": True, "message": "No workflow required for this category"}
            
            # Create workflow trigger following existing patterns
            workflow_trigger = ContactWorkflowTrigger(
                contact_email=email.sender_email,
                contact_name=email.sender_name or email.sender_email,
                trigger_type="email_received",
                trigger_source="notion_mail_integration",
                business_entity=classification.business_entity,
                metadata={
                    "email_subject": email.subject,
                    "email_category": classification.category.value,
                    "classification_confidence": classification.confidence,
                    "message_id": email.message_id,
                    "received_at": email.received_at.isoformat(),
                    "priority_score": classification.priority_score
                }
            )
            
            # Process workflow using existing automation service
            workflow_result = await self.workflow_automation.process_contact_workflow(workflow_trigger)
            
            # Log to Notion if workflow was successful
            if workflow_result.get("success"):
                await self._log_email_processing(email, classification, workflow_result)
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"Error processing email workflow: {e}")
            return {"success": False, "error": str(e)}

    async def _log_email_processing(
        self, 
        email: EmailContent, 
        classification: EmailClassificationResult, 
        workflow_result: Dict[str, Any]
    ) -> None:
        """Log email processing to Notion database."""
        try:
            # Create workflow instance record following existing patterns
            workflow_instance = WorkflowInstance(
                workflow_name=f"email_classification_{classification.category.value.lower().replace(' ', '_')}",
                trigger_type="email_received",
                status="completed",
                business_entity=classification.business_entity or "unknown",
                contact_email=email.sender_email,
                metadata={
                    "email_subject": email.subject,
                    "classification": classification.category.value,
                    "confidence": classification.confidence,
                    "workflows_executed": workflow_result.get("workflows_executed", []),
                    "processing_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Save to Notion using existing service
            if not (is_api_disabled("notion") or self.config.testing_mode):
                await self.notion_service.create_page(workflow_instance)
                logger.info(f"Email processing logged to Notion for {email.sender_email}")
            else:
                logger.info(f"[TESTING MODE] Would log email processing to Notion for {email.sender_email}")
                
        except Exception as e:
            logger.error(f"Error logging email processing to Notion: {e}")
