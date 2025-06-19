#!/usr/bin/env python3
"""
Contact Workflow Webhooks API

This module provides webhook endpoints for triggering contact-based workflows
in real-time. It integrates with the Contact Workflow Automation service to
process contact events and trigger appropriate business workflows.

Endpoints:
- POST /contact-workflows/trigger - Manual workflow trigger
- POST /contact-workflows/notion-webhook - Notion database change webhook
- POST /contact-workflows/new-contact - New contact registration webhook
- GET /contact-workflows/status - Workflow status and analytics
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, EmailStr
from loguru import logger

from services.contact_workflow_automation import (
    ContactWorkflowAutomation,
    ContactWorkflowTrigger,
    ContactType,
    LeadSource,
    BusinessEntity
)

# Global AI agent instances (will be initialized in main.py)
nyra_realtime_agent = None

router = APIRouter(prefix="/contact-workflows", tags=["Contact Workflows"])

# Initialize the workflow automation service
workflow_automation = ContactWorkflowAutomation()


class ManualWorkflowTriggerRequest(BaseModel):
    """Request model for manual workflow triggers."""
    contact_email: EmailStr
    contact_types: List[str]
    lead_source: str
    business_entities: List[str]
    trigger_event: str = "manual_trigger"
    metadata: Dict[str, Any] = {}


class NewContactRequest(BaseModel):
    """Request model for new contact registration."""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    contact_types: List[str] = ["General Contact"]
    lead_source: str = "Website"
    business_entities: List[str] = ["HigherSelf Core"]
    source_metadata: Dict[str, Any] = {}


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    active_workflows: int
    total_contacts_processed: int
    recent_executions: List[Dict[str, Any]]
    system_status: str


@router.post("/trigger")
async def trigger_manual_workflow(
    request: ManualWorkflowTriggerRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Manually trigger a contact workflow.
    
    This endpoint allows manual triggering of contact workflows for testing
    or special circumstances.
    """
    try:
        # Convert string enums to proper enum types
        contact_types = []
        for ct_str in request.contact_types:
            try:
                contact_types.append(ContactType(ct_str))
            except ValueError:
                logger.warning(f"Unknown contact type: {ct_str}")
        
        try:
            lead_source = LeadSource(request.lead_source)
        except ValueError:
            lead_source = LeadSource.WEBSITE
            logger.warning(f"Unknown lead source: {request.lead_source}, using default")
        
        business_entities = []
        for be_str in request.business_entities:
            try:
                business_entities.append(BusinessEntity(be_str))
            except ValueError:
                logger.warning(f"Unknown business entity: {be_str}")
        
        # Create workflow trigger
        trigger = ContactWorkflowTrigger(
            contact_id=f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            contact_email=request.contact_email,
            contact_types=contact_types,
            lead_source=lead_source,
            trigger_event=request.trigger_event,
            business_entities=business_entities,
            metadata=request.metadata
        )
        
        # Process workflow in background
        background_tasks.add_task(workflow_automation.process_contact_trigger, trigger)
        
        return {
            "success": True,
            "message": "Workflow triggered successfully",
            "contact_email": request.contact_email,
            "trigger_id": trigger.contact_id
        }
        
    except Exception as e:
        logger.error(f"Error triggering manual workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Error triggering workflow: {str(e)}")


@router.post("/notion-webhook")
async def handle_notion_webhook(
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Handle webhooks from Notion database changes.
    
    This endpoint processes Notion database change notifications and triggers
    appropriate contact workflows.
    """
    try:
        # Parse webhook payload
        payload = await request.json()
        
        # Extract relevant information from Notion webhook
        event_type = payload.get("event", "unknown")
        page_data = payload.get("data", {})
        
        logger.info(f"Received Notion webhook: {event_type}")
        
        # Process based on event type
        if event_type in ["page.created", "page.updated"]:
            # Check if this is a contact database change
            database_id = page_data.get("parent", {}).get("database_id")
            
            if database_id == workflow_automation.contacts_db_id:
                # Process contact change
                background_tasks.add_task(
                    workflow_automation._process_contact_change,
                    page_data
                )
                
                return {
                    "success": True,
                    "message": "Contact change processed",
                    "event_type": event_type
                }
        
        return {
            "success": True,
            "message": "Webhook received but no action required",
            "event_type": event_type
        }
        
    except Exception as e:
        logger.error(f"Error processing Notion webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post("/new-contact")
async def register_new_contact(
    request: NewContactRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Register a new contact and trigger welcome workflows.
    
    This endpoint is used when new contacts are added through forms,
    integrations, or other sources.
    """
    try:
        # Convert string enums to proper enum types
        contact_types = []
        for ct_str in request.contact_types:
            try:
                contact_types.append(ContactType(ct_str))
            except ValueError:
                contact_types.append(ContactType.GENERAL_CONTACT)
        
        try:
            lead_source = LeadSource(request.lead_source)
        except ValueError:
            lead_source = LeadSource.WEBSITE
        
        business_entities = []
        for be_str in request.business_entities:
            try:
                business_entities.append(BusinessEntity(be_str))
            except ValueError:
                pass
        
        if not business_entities:
            business_entities = [BusinessEntity.HIGHERSELF_CORE]
        
        # Create contact in Notion first
        contact_data = {
            "Email": {"email": request.email},
            "First Name": {"title": [{"text": {"content": request.first_name or ""}}]},
            "Last Name": {"rich_text": [{"text": {"content": request.last_name or ""}}]},
            "Contact Type": {"multi_select": [{"name": ct.value} for ct in contact_types]},
            "Lead Source": {"select": {"name": lead_source.value}},
            "Date Added": {"date": {"start": datetime.now().isoformat()[:10]}},
            "Contact ID": {"rich_text": [{"text": {"content": f"CONTACT-NEW-{datetime.now().strftime('%Y%m%d_%H%M%S')}"}}]}
        }
        
        # Create contact in Notion
        notion_response = await workflow_automation.notion.pages.create(
            parent={"database_id": workflow_automation.contacts_db_id},
            properties=contact_data
        )
        
        contact_id = notion_response["id"]
        
        # Create workflow trigger
        trigger = ContactWorkflowTrigger(
            contact_id=contact_id,
            contact_email=request.email,
            contact_types=contact_types,
            lead_source=lead_source,
            trigger_event="new_contact",
            business_entities=business_entities,
            metadata={
                "notion_page_id": contact_id,
                "source_metadata": request.source_metadata,
                "first_name": request.first_name,
                "last_name": request.last_name
            }
        )
        
        # Process workflow in background
        background_tasks.add_task(workflow_automation.process_contact_trigger, trigger)

        # NEW: Queue contact for real-time AI agent processing
        background_tasks.add_task(_queue_contact_for_ai_processing, {
            "contact_id": contact_id,
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "phone": request.phone,
            "message": request.message,
            "interests": request.interests,
            "source": lead_source,
            "source_metadata": request.source_metadata,
            "business_entities": business_entities,
            "contact_types": contact_types
        })

        return {
            "success": True,
            "message": "Contact registered, workflows triggered, and AI processing queued",
            "contact_id": contact_id,
            "contact_email": request.email,
            "workflows_triggered": True,
            "ai_processing_queued": True
        }


async def _queue_contact_for_ai_processing(contact_data: Dict[str, Any]):
    """Queue contact for AI agent processing."""
    try:
        if nyra_realtime_agent is not None:
            await nyra_realtime_agent.queue_contact_for_processing(contact_data)
            logger.info(f"Contact queued for AI processing: {contact_data.get('email')}")
        else:
            logger.warning("Nyra real-time agent not initialized, skipping AI processing")
    except Exception as e:
        logger.error(f"Error queuing contact for AI processing: {e}")


def initialize_ai_agents(nyra_agent):
    """Initialize AI agents for webhook processing."""
    global nyra_realtime_agent
    nyra_realtime_agent = nyra_agent
    logger.info("AI agents initialized for webhook processing")


@router.get("/status")
async def get_workflow_status() -> WorkflowStatusResponse:
    """
    Get current workflow automation status and analytics.
    
    Returns information about active workflows, processing statistics,
    and system health.
    """
    try:
        # Query recent workflow executions from Notion
        recent_executions = []
        try:
            response = await workflow_automation.notion.databases.query(
                database_id=workflow_automation.workflows_db_id,
                page_size=10,
                sorts=[{
                    "property": "Timestamp",
                    "direction": "descending"
                }]
            )
            
            for execution in response.get("results", []):
                properties = execution.get("properties", {})
                recent_executions.append({
                    "contact_email": properties.get("Contact Email", {}).get("email", ""),
                    "workflows": properties.get("Workflows Executed", {}).get("rich_text", [{}])[0].get("text", {}).get("content", ""),
                    "timestamp": properties.get("Timestamp", {}).get("date", {}).get("start", ""),
                    "status": properties.get("Status", {}).get("select", {}).get("name", "")
                })
        except Exception as e:
            logger.warning(f"Could not fetch recent executions: {e}")
        
        # Count total contacts processed
        total_contacts = 0
        try:
            contacts_response = await workflow_automation.notion.databases.query(
                database_id=workflow_automation.contacts_db_id,
                page_size=1
            )
            total_contacts = len(contacts_response.get("results", []))
        except Exception as e:
            logger.warning(f"Could not count total contacts: {e}")
        
        return WorkflowStatusResponse(
            active_workflows=len(workflow_automation.workflow_templates),
            total_contacts_processed=total_contacts,
            recent_executions=recent_executions,
            system_status="operational"
        )
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.post("/start-monitoring")
async def start_contact_monitoring(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Start the contact change monitoring service.
    
    This endpoint starts the background service that monitors Notion
    for contact changes and triggers workflows automatically.
    """
    try:
        background_tasks.add_task(workflow_automation.monitor_contact_changes)
        
        return {
            "success": True,
            "message": "Contact monitoring started",
            "status": "monitoring_active"
        }
        
    except Exception as e:
        logger.error(f"Error starting contact monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting monitoring: {str(e)}")


@router.get("/templates")
async def get_workflow_templates() -> Dict[str, Any]:
    """
    Get available workflow templates and their configurations.
    
    Returns information about all available workflow templates
    and their action sequences.
    """
    try:
        templates_info = {}
        
        for template_name, actions in workflow_automation.workflow_templates.items():
            templates_info[template_name] = {
                "name": template_name,
                "action_count": len(actions),
                "actions": [
                    {
                        "type": action.action_type,
                        "target": action.target,
                        "delay_hours": action.delay_hours
                    }
                    for action in actions
                ]
            }
        
        return {
            "success": True,
            "templates": templates_info,
            "total_templates": len(templates_info)
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow templates: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting templates: {str(e)}")
