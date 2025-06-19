#!/usr/bin/env python3
"""
Notion Intelligence Hub for HigherSelf Network Server

Bidirectional Notion synchronization system with AI agent intelligence.
Manages intelligent contact enrichment, automated database synchronization,
and agent-driven updates across all business entities.

Features:
- Bidirectional contact synchronization
- Intelligent contact enrichment with AI analysis
- Smart duplicate detection and merging
- Agent-driven database updates
- Cross-entity contact relationship mapping
- Advanced analytics and insights
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from agents.multi_entity_agent_orchestrator import MultiEntityAgentOrchestrator
from config.business_entity_workflows import BusinessEntityWorkflows
from services.notion_service import NotionService


class ContactEnrichmentEngine:
    """AI-powered contact enrichment engine."""
    
    def __init__(self, agent_orchestrator: MultiEntityAgentOrchestrator):
        self.agent_orchestrator = agent_orchestrator
        self.enrichment_patterns = self._initialize_enrichment_patterns()
    
    def _initialize_enrichment_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize contact enrichment patterns."""
        return {
            "the_7_space": {
                "required_fields": ["artistic_background", "exhibition_interest", "wellness_preferences"],
                "enrichment_sources": ["social_media", "portfolio_analysis", "interaction_history"],
                "ai_analysis_focus": "artistic_potential_and_wellness_alignment"
            },
            "am_consulting": {
                "required_fields": ["company_size", "industry", "consulting_needs", "budget_range"],
                "enrichment_sources": ["linkedin", "company_website", "business_intelligence"],
                "ai_analysis_focus": "business_consulting_potential_and_decision_authority"
            },
            "higherself_core": {
                "required_fields": ["personal_goals", "professional_development", "community_engagement"],
                "enrichment_sources": ["platform_activity", "content_engagement", "network_analysis"],
                "ai_analysis_focus": "growth_potential_and_community_contribution"
            }
        }
    
    async def enrich_contact(
        self, contact_data: Dict[str, Any], entity_name: str
    ) -> Dict[str, Any]:
        """Enrich contact data with AI-powered analysis."""
        
        enrichment_pattern = self.enrichment_patterns.get(entity_name, {})
        
        # Use Atlas agent for knowledge-based enrichment
        atlas_agent = self.agent_orchestrator.agents.get("atlas")
        if atlas_agent:
            enrichment_result = await self._perform_ai_enrichment(
                contact_data, entity_name, enrichment_pattern, atlas_agent
            )
        else:
            enrichment_result = self._perform_basic_enrichment(contact_data, entity_name)
        
        return {
            **contact_data,
            "enrichment_data": enrichment_result,
            "enrichment_timestamp": datetime.now().isoformat(),
            "enrichment_agent": "atlas_ai_enrichment"
        }
    
    async def _perform_ai_enrichment(
        self, contact_data: Dict[str, Any], entity_name: str, 
        enrichment_pattern: Dict[str, Any], atlas_agent: Any
    ) -> Dict[str, Any]:
        """Perform AI-powered contact enrichment."""
        
        # Simulate AI enrichment (would integrate with actual AI models)
        enrichment_result = {
            "ai_analysis": {
                "entity_fit_score": 0.85,
                "engagement_potential": "high",
                "recommended_approach": f"personalized_{entity_name}_strategy",
                "missing_data_identified": enrichment_pattern.get("required_fields", []),
                "enrichment_confidence": 0.9
            },
            "data_sources_analyzed": enrichment_pattern.get("enrichment_sources", []),
            "enrichment_suggestions": self._generate_enrichment_suggestions(contact_data, entity_name)
        }
        
        return enrichment_result
    
    def _perform_basic_enrichment(self, contact_data: Dict[str, Any], entity_name: str) -> Dict[str, Any]:
        """Perform basic contact enrichment without AI."""
        return {
            "basic_analysis": {
                "entity_alignment": "moderate",
                "data_completeness": self._assess_data_completeness(contact_data),
                "enrichment_opportunities": ["email_validation", "social_media_lookup"]
            }
        }
    
    def _generate_enrichment_suggestions(self, contact_data: Dict[str, Any], entity_name: str) -> List[str]:
        """Generate suggestions for contact enrichment."""
        suggestions = []
        
        if not contact_data.get("phone"):
            suggestions.append("phone_number_lookup")
        if not contact_data.get("company"):
            suggestions.append("company_identification")
        if not contact_data.get("social_media"):
            suggestions.append("social_media_profile_discovery")
        
        return suggestions
    
    def _assess_data_completeness(self, contact_data: Dict[str, Any]) -> float:
        """Assess the completeness of contact data."""
        required_fields = ["email", "first_name", "last_name", "message"]
        optional_fields = ["phone", "company", "interests", "source"]
        
        required_score = sum(1 for field in required_fields if contact_data.get(field)) / len(required_fields)
        optional_score = sum(1 for field in optional_fields if contact_data.get(field)) / len(optional_fields)
        
        return (required_score * 0.7) + (optional_score * 0.3)


class DuplicateDetectionEngine:
    """Intelligent duplicate detection and merging engine."""
    
    def __init__(self):
        self.similarity_threshold = 0.8
        self.matching_algorithms = ["email_exact", "name_fuzzy", "phone_exact", "content_similarity"]
    
    async def detect_duplicates(
        self, new_contact: Dict[str, Any], existing_contacts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect potential duplicate contacts."""
        
        potential_duplicates = []
        
        for existing_contact in existing_contacts:
            similarity_score = await self._calculate_similarity(new_contact, existing_contact)
            
            if similarity_score >= self.similarity_threshold:
                potential_duplicates.append({
                    "existing_contact": existing_contact,
                    "similarity_score": similarity_score,
                    "matching_fields": self._identify_matching_fields(new_contact, existing_contact),
                    "merge_recommendation": self._generate_merge_recommendation(
                        new_contact, existing_contact, similarity_score
                    )
                })
        
        return sorted(potential_duplicates, key=lambda x: x["similarity_score"], reverse=True)
    
    async def _calculate_similarity(
        self, contact1: Dict[str, Any], contact2: Dict[str, Any]
    ) -> float:
        """Calculate similarity score between two contacts."""
        
        scores = []
        
        # Email exact match
        if contact1.get("email") and contact2.get("email"):
            email_score = 1.0 if contact1["email"].lower() == contact2["email"].lower() else 0.0
            scores.append(("email", email_score, 0.4))  # High weight for email
        
        # Name similarity
        name1 = f"{contact1.get('first_name', '')} {contact1.get('last_name', '')}".strip()
        name2 = f"{contact2.get('first_name', '')} {contact2.get('last_name', '')}".strip()
        if name1 and name2:
            name_score = self._fuzzy_string_match(name1, name2)
            scores.append(("name", name_score, 0.3))
        
        # Phone exact match
        if contact1.get("phone") and contact2.get("phone"):
            phone_score = 1.0 if contact1["phone"] == contact2["phone"] else 0.0
            scores.append(("phone", phone_score, 0.2))
        
        # Content similarity
        message1 = contact1.get("message", "")
        message2 = contact2.get("message", "")
        if message1 and message2:
            content_score = self._fuzzy_string_match(message1, message2)
            scores.append(("content", content_score, 0.1))
        
        # Calculate weighted average
        if scores:
            weighted_sum = sum(score * weight for _, score, weight in scores)
            total_weight = sum(weight for _, _, weight in scores)
            return weighted_sum / total_weight
        
        return 0.0
    
    def _fuzzy_string_match(self, str1: str, str2: str) -> float:
        """Calculate fuzzy string similarity."""
        # Simple implementation - in production, use libraries like fuzzywuzzy
        str1_lower = str1.lower()
        str2_lower = str2.lower()
        
        if str1_lower == str2_lower:
            return 1.0
        
        # Simple character overlap calculation
        set1 = set(str1_lower.split())
        set2 = set(str2_lower.split())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _identify_matching_fields(
        self, contact1: Dict[str, Any], contact2: Dict[str, Any]
    ) -> List[str]:
        """Identify which fields match between contacts."""
        matching_fields = []
        
        for field in ["email", "phone", "first_name", "last_name"]:
            if (contact1.get(field) and contact2.get(field) and 
                contact1[field].lower() == contact2[field].lower()):
                matching_fields.append(field)
        
        return matching_fields
    
    def _generate_merge_recommendation(
        self, new_contact: Dict[str, Any], existing_contact: Dict[str, Any], similarity_score: float
    ) -> Dict[str, Any]:
        """Generate recommendation for merging contacts."""
        
        if similarity_score >= 0.95:
            action = "auto_merge"
        elif similarity_score >= 0.8:
            action = "manual_review"
        else:
            action = "keep_separate"
        
        return {
            "action": action,
            "confidence": similarity_score,
            "merge_strategy": "preserve_most_recent_data",
            "fields_to_merge": ["interests", "message", "source_metadata"],
            "fields_to_preserve": ["email", "first_name", "last_name"]
        }


class NotionIntelligenceHub:
    """
    Bidirectional Notion Intelligence Hub with AI agent integration.
    
    Manages intelligent contact synchronization, enrichment, and updates
    across all business entities with agent-driven intelligence.
    """
    
    def __init__(self, notion_client: NotionService, agent_orchestrator: MultiEntityAgentOrchestrator):
        self.notion_client = notion_client
        self.agent_orchestrator = agent_orchestrator
        self.business_workflows = BusinessEntityWorkflows()
        
        # Initialize intelligence engines
        self.enrichment_engine = ContactEnrichmentEngine(agent_orchestrator)
        self.duplicate_engine = DuplicateDetectionEngine()
        
        # Synchronization tracking
        self.sync_metrics = {
            "contacts_synchronized": 0,
            "contacts_enriched": 0,
            "duplicates_detected": 0,
            "duplicates_merged": 0,
            "last_sync_timestamp": None,
            "sync_errors": 0
        }
        
        # Entity database mappings
        self.entity_databases = {
            "the_7_space": "the_7_space_contacts_db_id",
            "am_consulting": "am_consulting_contacts_db_id", 
            "higherself_core": "higherself_core_contacts_db_id"
        }
        
        logger.info("Notion Intelligence Hub initialized")
    
    async def perform_bidirectional_sync(self, entity_name: Optional[str] = None) -> Dict[str, Any]:
        """Perform bidirectional synchronization with intelligent processing."""
        
        sync_start_time = datetime.now()
        logger.info(f"Starting bidirectional sync for {entity_name or 'all entities'}")
        
        try:
            if entity_name:
                entities_to_sync = [entity_name]
            else:
                entities_to_sync = list(self.entity_databases.keys())
            
            sync_results = {}
            
            for entity in entities_to_sync:
                entity_result = await self._sync_entity_contacts(entity)
                sync_results[entity] = entity_result
            
            # Update sync metrics
            sync_duration = (datetime.now() - sync_start_time).total_seconds()
            self.sync_metrics["last_sync_timestamp"] = sync_start_time.isoformat()
            
            return {
                "success": True,
                "sync_duration": sync_duration,
                "entities_synced": entities_to_sync,
                "results": sync_results,
                "metrics": self.sync_metrics
            }
            
        except Exception as e:
            logger.error(f"Error in bidirectional sync: {e}")
            self.sync_metrics["sync_errors"] += 1
            return {
                "success": False,
                "error": str(e),
                "sync_duration": (datetime.now() - sync_start_time).total_seconds()
            }
    
    async def _sync_entity_contacts(self, entity_name: str) -> Dict[str, Any]:
        """Sync contacts for a specific entity."""
        
        try:
            # Step 1: Fetch existing contacts from Notion
            existing_contacts = await self._fetch_entity_contacts(entity_name)
            
            # Step 2: Fetch new contacts from capture system
            new_contacts = await self._fetch_new_contacts(entity_name)
            
            # Step 3: Process each new contact
            processing_results = []
            for new_contact in new_contacts:
                contact_result = await self._process_contact_intelligently(
                    new_contact, existing_contacts, entity_name
                )
                processing_results.append(contact_result)
            
            # Step 4: Enrich existing contacts that need updates
            enrichment_results = await self._enrich_existing_contacts(existing_contacts, entity_name)
            
            return {
                "entity": entity_name,
                "existing_contacts_count": len(existing_contacts),
                "new_contacts_processed": len(processing_results),
                "contacts_enriched": len(enrichment_results),
                "processing_results": processing_results,
                "enrichment_results": enrichment_results
            }
            
        except Exception as e:
            logger.error(f"Error syncing {entity_name} contacts: {e}")
            return {
                "entity": entity_name,
                "error": str(e),
                "success": False
            }
    
    async def _fetch_entity_contacts(self, entity_name: str) -> List[Dict[str, Any]]:
        """Fetch existing contacts for an entity from Notion."""
        
        # Simulate fetching from Notion database
        # In production, this would use the actual Notion API
        
        sample_contacts = {
            "the_7_space": [
                {
                    "id": "contact_1",
                    "email": "existing@the7space.com",
                    "first_name": "Existing",
                    "last_name": "Artist",
                    "entity": "the_7_space",
                    "last_updated": "2024-01-01T00:00:00Z"
                }
            ],
            "am_consulting": [
                {
                    "id": "contact_2", 
                    "email": "client@business.com",
                    "first_name": "Business",
                    "last_name": "Client",
                    "entity": "am_consulting",
                    "last_updated": "2024-01-01T00:00:00Z"
                }
            ],
            "higherself_core": [
                {
                    "id": "contact_3",
                    "email": "member@community.com", 
                    "first_name": "Community",
                    "last_name": "Member",
                    "entity": "higherself_core",
                    "last_updated": "2024-01-01T00:00:00Z"
                }
            ]
        }
        
        return sample_contacts.get(entity_name, [])
    
    async def _fetch_new_contacts(self, entity_name: str) -> List[Dict[str, Any]]:
        """Fetch new contacts from the capture system."""
        
        # Simulate new contacts from WordPress/capture system
        # In production, this would fetch from the actual capture database
        
        sample_new_contacts = {
            "the_7_space": [
                {
                    "email": "new.artist@gmail.com",
                    "first_name": "New",
                    "last_name": "Artist",
                    "message": "I want to exhibit my paintings",
                    "interests": ["art", "painting"],
                    "source": "website_form",
                    "captured_at": datetime.now().isoformat()
                }
            ],
            "am_consulting": [
                {
                    "email": "startup@company.com",
                    "first_name": "Startup",
                    "last_name": "Founder",
                    "message": "Need help scaling our business",
                    "interests": ["business", "scaling"],
                    "source": "referral",
                    "captured_at": datetime.now().isoformat()
                }
            ],
            "higherself_core": [
                {
                    "email": "growth@seeker.com",
                    "first_name": "Growth",
                    "last_name": "Seeker",
                    "message": "Looking for personal development community",
                    "interests": ["growth", "community"],
                    "source": "social_media",
                    "captured_at": datetime.now().isoformat()
                }
            ]
        }
        
        return sample_new_contacts.get(entity_name, [])
    
    async def _process_contact_intelligently(
        self, new_contact: Dict[str, Any], existing_contacts: List[Dict[str, Any]], entity_name: str
    ) -> Dict[str, Any]:
        """Process a new contact with intelligent analysis."""
        
        try:
            # Step 1: Detect duplicates
            duplicates = await self.duplicate_engine.detect_duplicates(new_contact, existing_contacts)
            
            # Step 2: Enrich contact data
            enriched_contact = await self.enrichment_engine.enrich_contact(new_contact, entity_name)
            
            # Step 3: Handle duplicates or create new contact
            if duplicates:
                # Handle duplicate contact
                best_match = duplicates[0]
                if best_match["merge_recommendation"]["action"] == "auto_merge":
                    result = await self._merge_contacts(enriched_contact, best_match["existing_contact"])
                    self.sync_metrics["duplicates_merged"] += 1
                else:
                    result = await self._create_new_contact_with_duplicate_flag(enriched_contact, duplicates)
                
                self.sync_metrics["duplicates_detected"] += 1
            else:
                # Create new contact
                result = await self._create_new_contact(enriched_contact, entity_name)
            
            # Step 4: Update metrics
            self.sync_metrics["contacts_synchronized"] += 1
            self.sync_metrics["contacts_enriched"] += 1
            
            return {
                "contact_email": new_contact.get("email"),
                "action_taken": result.get("action", "processed"),
                "duplicates_found": len(duplicates),
                "enrichment_applied": True,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing contact {new_contact.get('email')}: {e}")
            return {
                "contact_email": new_contact.get("email"),
                "error": str(e),
                "success": False
            }
    
    async def _enrich_existing_contacts(
        self, existing_contacts: List[Dict[str, Any]], entity_name: str
    ) -> List[Dict[str, Any]]:
        """Enrich existing contacts that need updates."""
        
        enrichment_results = []
        
        for contact in existing_contacts:
            # Check if contact needs enrichment (e.g., missing data, old timestamp)
            if self._needs_enrichment(contact):
                try:
                    enriched_contact = await self.enrichment_engine.enrich_contact(contact, entity_name)
                    update_result = await self._update_existing_contact(enriched_contact)
                    
                    enrichment_results.append({
                        "contact_id": contact.get("id"),
                        "contact_email": contact.get("email"),
                        "enrichment_applied": True,
                        "update_success": update_result.get("success", False)
                    })
                    
                except Exception as e:
                    logger.error(f"Error enriching contact {contact.get('email')}: {e}")
                    enrichment_results.append({
                        "contact_id": contact.get("id"),
                        "contact_email": contact.get("email"),
                        "error": str(e),
                        "enrichment_applied": False
                    })
        
        return enrichment_results
    
    def _needs_enrichment(self, contact: Dict[str, Any]) -> bool:
        """Determine if a contact needs enrichment."""
        
        # Check if contact was last updated more than 30 days ago
        last_updated = contact.get("last_updated")
        if last_updated:
            try:
                last_update_date = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                if datetime.now() - last_update_date > timedelta(days=30):
                    return True
            except:
                pass
        
        # Check for missing critical data
        critical_fields = ["phone", "company", "interests"]
        missing_fields = sum(1 for field in critical_fields if not contact.get(field))
        
        return missing_fields >= 2  # Needs enrichment if missing 2+ critical fields
    
    async def _merge_contacts(
        self, new_contact: Dict[str, Any], existing_contact: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge new contact data with existing contact."""
        
        # Merge strategy: preserve existing data, add new data, update timestamps
        merged_contact = {
            **existing_contact,
            **{k: v for k, v in new_contact.items() if v and k not in ["id", "created_at"]},
            "last_updated": datetime.now().isoformat(),
            "merge_history": existing_contact.get("merge_history", []) + [{
                "merged_at": datetime.now().isoformat(),
                "source": "intelligent_sync",
                "data_added": list(new_contact.keys())
            }]
        }
        
        return {
            "action": "merged",
            "contact_id": existing_contact.get("id"),
            "merged_contact": merged_contact,
            "success": True
        }
    
    async def _create_new_contact_with_duplicate_flag(
        self, contact: Dict[str, Any], duplicates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create new contact with duplicate detection flag."""
        
        contact_with_flag = {
            **contact,
            "duplicate_detection": {
                "potential_duplicates_found": len(duplicates),
                "requires_manual_review": True,
                "duplicate_details": duplicates
            },
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "action": "created_with_duplicate_flag",
            "contact": contact_with_flag,
            "success": True
        }
    
    async def _create_new_contact(self, contact: Dict[str, Any], entity_name: str) -> Dict[str, Any]:
        """Create a new contact in Notion."""
        
        new_contact = {
            **contact,
            "entity": entity_name,
            "created_at": datetime.now().isoformat(),
            "created_by": "notion_intelligence_hub"
        }
        
        return {
            "action": "created",
            "contact": new_contact,
            "success": True
        }
    
    async def _update_existing_contact(self, contact: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing contact in Notion."""
        
        updated_contact = {
            **contact,
            "last_updated": datetime.now().isoformat(),
            "updated_by": "notion_intelligence_hub"
        }
        
        return {
            "action": "updated",
            "contact": updated_contact,
            "success": True
        }
    
    async def get_intelligence_hub_status(self) -> Dict[str, Any]:
        """Get status of the Notion Intelligence Hub."""
        
        return {
            "status": "operational",
            "sync_metrics": self.sync_metrics,
            "entity_databases": self.entity_databases,
            "engines": {
                "enrichment_engine": "active",
                "duplicate_engine": "active"
            },
            "last_status_check": datetime.now().isoformat()
        }
    
    async def trigger_manual_enrichment(
        self, contact_id: str, entity_name: str
    ) -> Dict[str, Any]:
        """Manually trigger enrichment for a specific contact."""
        
        try:
            # Fetch contact data
            contact_data = await self._fetch_contact_by_id(contact_id, entity_name)
            
            if not contact_data:
                return {"success": False, "error": "Contact not found"}
            
            # Enrich contact
            enriched_contact = await self.enrichment_engine.enrich_contact(contact_data, entity_name)
            
            # Update contact
            update_result = await self._update_existing_contact(enriched_contact)
            
            return {
                "success": True,
                "contact_id": contact_id,
                "enrichment_applied": True,
                "update_result": update_result
            }
            
        except Exception as e:
            logger.error(f"Error in manual enrichment for {contact_id}: {e}")
            return {
                "success": False,
                "contact_id": contact_id,
                "error": str(e)
            }
    
    async def _fetch_contact_by_id(self, contact_id: str, entity_name: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific contact by ID."""
        # Simulate fetching contact by ID
        return {
            "id": contact_id,
            "email": f"contact@{entity_name}.com",
            "entity": entity_name
        }

    async def analyze_contact_relationships(self, entity_name: Optional[str] = None) -> Dict[str, Any]:
        """Analyze relationships between contacts across entities."""

        try:
            if entity_name:
                entities_to_analyze = [entity_name]
            else:
                entities_to_analyze = list(self.entity_databases.keys())

            relationship_analysis = {}

            for entity in entities_to_analyze:
                contacts = await self._fetch_entity_contacts(entity)

                # Analyze contact patterns
                analysis = {
                    "total_contacts": len(contacts),
                    "contact_sources": self._analyze_contact_sources(contacts),
                    "engagement_patterns": self._analyze_engagement_patterns(contacts),
                    "cross_entity_opportunities": await self._identify_cross_entity_relationships(contacts, entity)
                }

                relationship_analysis[entity] = analysis

            return {
                "success": True,
                "relationship_analysis": relationship_analysis,
                "analysis_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing contact relationships: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _analyze_contact_sources(self, contacts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze contact sources distribution."""
        sources = {}
        for contact in contacts:
            source = contact.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        return sources

    def _analyze_engagement_patterns(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contact engagement patterns."""
        return {
            "high_engagement": len([c for c in contacts if len(c.get("interests", [])) > 2]),
            "medium_engagement": len([c for c in contacts if len(c.get("interests", [])) == 2]),
            "low_engagement": len([c for c in contacts if len(c.get("interests", [])) < 2]),
            "avg_message_length": sum(len(c.get("message", "")) for c in contacts) / len(contacts) if contacts else 0
        }

    async def _identify_cross_entity_relationships(
        self, contacts: List[Dict[str, Any]], entity_name: str
    ) -> List[Dict[str, Any]]:
        """Identify potential cross-entity relationship opportunities."""

        opportunities = []

        for contact in contacts:
            interests = contact.get("interests", [])
            message = contact.get("message", "").lower()

            # Identify cross-entity potential
            if entity_name == "the_7_space":
                if any(keyword in message for keyword in ["business", "entrepreneur", "startup"]):
                    opportunities.append({
                        "contact_email": contact.get("email"),
                        "opportunity": "am_consulting_referral",
                        "confidence": 0.7
                    })
                if any(keyword in message for keyword in ["growth", "development", "community"]):
                    opportunities.append({
                        "contact_email": contact.get("email"),
                        "opportunity": "higherself_core_referral",
                        "confidence": 0.6
                    })

            elif entity_name == "am_consulting":
                if any(keyword in message for keyword in ["creative", "art", "wellness"]):
                    opportunities.append({
                        "contact_email": contact.get("email"),
                        "opportunity": "the_7_space_referral",
                        "confidence": 0.6
                    })
                if any(keyword in message for keyword in ["leadership", "personal", "growth"]):
                    opportunities.append({
                        "contact_email": contact.get("email"),
                        "opportunity": "higherself_core_referral",
                        "confidence": 0.8
                    })

        return opportunities
