#!/usr/bin/env python3
"""
Nyra Real-Time Enhanced Agent for HigherSelf Network Server

Enhanced version of Nyra with real-time contact processing capabilities,
integrating with WordPress webhooks and preparing for MCP server integration.

This agent processes contacts from The 7 Space website in real-time and
can be extended to handle AM Consulting and HigherSelf Core contacts.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from loguru import logger

from agents.nyra_enhanced import NyraEnhanced
from agents.multi_entity_agent_orchestrator import MultiEntityAgentOrchestrator
from config.business_entity_workflows import BusinessEntityWorkflows
from models.notion_db_models import ContactWorkflowTrigger
from services.contact_workflow_automation import ContactWorkflowAutomation
from services.notion_service import NotionService


class NyraRealtimeEnhanced(NyraEnhanced):
    """
    Enhanced Nyra agent with real-time contact processing capabilities.
    
    Features:
    - Real-time WordPress contact processing
    - Multi-entity business logic (The 7 Space, AM Consulting, HigherSelf Core)
    - Intelligent contact classification and routing
    - MCP server integration ready
    - Enhanced workflow automation
    """
    
    def __init__(self, notion_client, **kwargs):
        super().__init__(notion_client=notion_client, **kwargs)
        
        # Initialize real-time processing components
        self.business_workflows = BusinessEntityWorkflows()
        self.workflow_automation = ContactWorkflowAutomation()
        self.processing_queue = asyncio.Queue()
        self.is_processing = False

        # Initialize multi-entity orchestrator
        self.multi_entity_orchestrator = MultiEntityAgentOrchestrator(notion_client)
        
        # MCP integration flags (for future enhancement)
        self.mcp_enabled = kwargs.get('mcp_enabled', False)
        self.mcp_servers = kwargs.get('mcp_servers', {})
        
        # Real-time processing metrics
        self.processing_metrics = {
            "contacts_processed": 0,
            "processing_errors": 0,
            "average_processing_time": 0.0,
            "last_processed": None
        }
        
        logger.info("Nyra Real-Time Enhanced agent initialized")
    
    async def start_realtime_processing(self):
        """Start the real-time contact processing loop."""
        if self.is_processing:
            logger.warning("Real-time processing already started")
            return
        
        self.is_processing = True
        logger.info("Starting Nyra real-time contact processing...")
        
        # Start the processing loop
        asyncio.create_task(self._processing_loop())
    
    async def stop_realtime_processing(self):
        """Stop the real-time contact processing loop."""
        self.is_processing = False
        logger.info("Stopping Nyra real-time contact processing...")
    
    async def _processing_loop(self):
        """Main processing loop for real-time contact handling."""
        while self.is_processing:
            try:
                # Wait for contact data with timeout
                contact_data = await asyncio.wait_for(
                    self.processing_queue.get(), 
                    timeout=1.0
                )
                
                # Process the contact
                await self._process_realtime_contact(contact_data)
                
            except asyncio.TimeoutError:
                # No contacts to process, continue loop
                continue
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                self.processing_metrics["processing_errors"] += 1
                await asyncio.sleep(1)  # Brief pause on error
    
    async def queue_contact_for_processing(self, contact_data: Dict[str, Any]):
        """Queue a contact for real-time processing."""
        try:
            # Add timestamp and source tracking
            enhanced_contact_data = {
                **contact_data,
                "queued_at": datetime.now().isoformat(),
                "processing_agent": "nyra_realtime",
                "queue_size": self.processing_queue.qsize()
            }
            
            await self.processing_queue.put(enhanced_contact_data)
            logger.info(f"Contact queued for processing: {contact_data.get('email', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error queuing contact: {e}")
            raise
    
    async def _process_realtime_contact(self, contact_data: Dict[str, Any]):
        """Process a single contact in real-time with enhanced capabilities."""
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing contact: {contact_data.get('email', 'unknown')}")
            
            # Step 1: Determine business entity
            business_entity = self._determine_business_entity(contact_data)

            # Step 2: Process through multi-entity orchestrator
            orchestrator_result = await self.multi_entity_orchestrator.process_multi_entity_contact(
                contact_data, business_entity
            )

            # Step 3: Enhanced contact analysis with entity context
            analysis_result = orchestrator_result.get("analysis", {})
            
            # Step 3: Create or update contact in Notion
            notion_result = await self._create_notion_contact_realtime(
                contact_data, analysis_result, business_entity
            )
            
            # Step 4: Trigger appropriate workflows
            workflow_result = await self._trigger_entity_workflows(
                contact_data, analysis_result, business_entity, notion_result
            )
            
            # Step 5: Log processing results (MCP File System integration point)
            await self._log_processing_results(
                contact_data, analysis_result, notion_result, workflow_result
            )
            
            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_processing_metrics(processing_time)
            
            logger.info(f"Contact processed successfully in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error processing contact: {e}")
            self.processing_metrics["processing_errors"] += 1
            raise
    
    def _determine_business_entity(self, contact_data: Dict[str, Any]) -> str:
        """Determine which business entity this contact belongs to."""
        source = contact_data.get("source", "").lower()
        source_url = contact_data.get("source_url", "").lower()
        interests = contact_data.get("interests", [])
        
        # The 7 Space indicators
        if any(indicator in source for indicator in ["7space", "the7space", "gallery", "wellness"]):
            return "the_7_space"
        if any(indicator in source_url for indicator in ["the7space.com", "7space"]):
            return "the_7_space"
        if any(interest in ["art", "gallery", "wellness", "meditation"] for interest in interests):
            return "the_7_space"
        
        # AM Consulting indicators
        if any(indicator in source for indicator in ["am_consulting", "consulting", "business"]):
            return "am_consulting"
        if "consulting" in contact_data.get("message", "").lower():
            return "am_consulting"
        
        # HigherSelf Core indicators
        if any(indicator in source for indicator in ["higherself", "community", "platform"]):
            return "higherself_core"
        
        # Default to The 7 Space for demo purposes
        return "the_7_space"
    
    async def _analyze_contact_with_entity_context(
        self, contact_data: Dict[str, Any], business_entity: str
    ) -> Dict[str, Any]:
        """Analyze contact with business entity context."""
        
        # Get entity-specific configuration
        entity_config = self.business_workflows.get_entity_config(business_entity)
        
        # Create entity-aware analysis prompt
        entity_context_prompt = PromptTemplate(
            input_variables=["contact_data", "business_entity", "entity_config"],
            template="""As Nyra, analyze this contact with deep understanding of the {business_entity} business context:

Contact Data: {contact_data}
Business Entity: {business_entity}
Entity Configuration: {entity_config}

Provide a comprehensive analysis including:
1. Contact intent and needs assessment
2. Business entity fit and alignment
3. Recommended engagement approach
4. Priority level and urgency
5. Suggested follow-up actions
6. Potential value and opportunity assessment

Return as JSON with clear structure."""
        )
        
        # Run analysis with entity context
        analysis_chain = LLMChain(
            llm=self.llm,
            prompt=entity_context_prompt
        )
        
        result = await analysis_chain.ainvoke({
            "contact_data": json.dumps(contact_data),
            "business_entity": business_entity,
            "entity_config": json.dumps(entity_config.__dict__ if entity_config else {})
        })
        
        try:
            return json.loads(result["text"])
        except json.JSONDecodeError:
            logger.warning("Failed to parse analysis result as JSON")
            return {"analysis": result["text"], "entity": business_entity}
    
    async def _create_notion_contact_realtime(
        self, contact_data: Dict[str, Any], analysis_result: Dict[str, Any], business_entity: str
    ) -> Dict[str, Any]:
        """Create or update contact in Notion with real-time processing."""
        
        # Enhanced contact properties with real-time analysis
        contact_properties = {
            **self._build_enhanced_contact_properties(
                contact_data, analysis_result, {}, {}, {}
            ),
            "Business Entity": {"select": {"name": business_entity.replace("_", " ").title()}},
            "Processing Agent": {"rich_text": [{"text": {"content": "Nyra Real-Time"}}]},
            "Processing Timestamp": {"date": {"start": datetime.now().isoformat()}},
            "Analysis Summary": {"rich_text": [{"text": {"content": str(analysis_result.get("analysis", ""))[:2000]}}]}
        }
        
        # Create contact in Notion (MCP Notion integration point)
        if self.mcp_enabled and "notion" in self.mcp_servers:
            # Use MCP Notion server when available
            return await self._create_contact_via_mcp(contact_properties)
        else:
            # Use existing Notion service
            return await self.tools[3]._arun(
                database_id=self.business_workflows.get_contacts_database_id(business_entity),
                title=f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip(),
                properties=contact_properties
            )
    
    async def _trigger_entity_workflows(
        self, contact_data: Dict[str, Any], analysis_result: Dict[str, Any], 
        business_entity: str, notion_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger appropriate workflows based on business entity and analysis."""
        
        # Create workflow trigger with enhanced context
        trigger = ContactWorkflowTrigger(
            contact_id=notion_result.get("id"),
            contact_email=contact_data.get("email"),
            contact_types=analysis_result.get("contact_types", []),
            lead_source=contact_data.get("source", "website"),
            trigger_event="realtime_contact_processing",
            business_entities=[business_entity],
            metadata={
                "processing_agent": "nyra_realtime",
                "analysis_summary": analysis_result.get("analysis", ""),
                "priority_level": analysis_result.get("priority_level", "medium"),
                "recommended_actions": analysis_result.get("recommended_actions", []),
                "entity_fit_score": analysis_result.get("entity_fit_score", 0.5)
            }
        )
        
        # Process workflow trigger
        return await self.workflow_automation.process_contact_trigger(trigger)
    
    async def _log_processing_results(
        self, contact_data: Dict[str, Any], analysis_result: Dict[str, Any],
        notion_result: Dict[str, Any], workflow_result: Dict[str, Any]
    ):
        """Log processing results for monitoring and debugging."""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": "nyra_realtime",
            "contact_email": contact_data.get("email"),
            "business_entity": self._determine_business_entity(contact_data),
            "processing_success": True,
            "notion_contact_id": notion_result.get("id"),
            "workflows_triggered": workflow_result.get("workflows_executed", []),
            "analysis_summary": analysis_result.get("analysis", "")[:500]
        }
        
        # Log to file system (MCP File System integration point)
        if self.mcp_enabled and "filesystem" in self.mcp_servers:
            await self._log_via_mcp(log_entry)
        else:
            logger.info(f"Processing log: {json.dumps(log_entry, indent=2)}")
    
    def _update_processing_metrics(self, processing_time: float):
        """Update processing metrics."""
        self.processing_metrics["contacts_processed"] += 1
        self.processing_metrics["last_processed"] = datetime.now().isoformat()
        
        # Update average processing time
        current_avg = self.processing_metrics["average_processing_time"]
        count = self.processing_metrics["contacts_processed"]
        self.processing_metrics["average_processing_time"] = (
            (current_avg * (count - 1) + processing_time) / count
        )
    
    async def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status and metrics."""
        return {
            "is_processing": self.is_processing,
            "queue_size": self.processing_queue.qsize(),
            "metrics": self.processing_metrics,
            "mcp_enabled": self.mcp_enabled,
            "mcp_servers": list(self.mcp_servers.keys()) if self.mcp_servers else []
        }
    
    # MCP Integration Methods (for future enhancement)
    async def _create_contact_via_mcp(self, contact_properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create contact via MCP Notion server (placeholder for MCP integration)."""
        # This will be implemented when MCP servers are available
        logger.info("MCP Notion integration not yet available, using fallback")
        return await self.tools[3]._arun(
            database_id=self.business_workflows.get_contacts_database_id("the_7_space"),
            title="MCP Contact",
            properties=contact_properties
        )
    
    async def _log_via_mcp(self, log_entry: Dict[str, Any]):
        """Log via MCP File System server (placeholder for MCP integration)."""
        # This will be implemented when MCP servers are available
        logger.info(f"MCP File System integration not yet available: {log_entry}")
