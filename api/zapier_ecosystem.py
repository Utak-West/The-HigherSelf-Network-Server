"""
API endpoints for Zapier Ecosystem integration.

This module provides REST API endpoints for managing the comprehensive Zapier ecosystem
including Tables, Interfaces, Chatbots, Canvases, and Agents across:
- The Connection Practice
- The 7 Space
- HigherSelf Network Core Functions
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from loguru import logger
from pydantic import BaseModel

from services.notion_service import NotionService
from services.zapier_ecosystem_service import (
    ZapierEcosystemService,
    ZapierEntityArea,
    ZapierComponentType,
)
from utils.auth import verify_staff_api_key
from config.testing_mode import is_api_disabled, TestingMode


# Response models
class ZapierEcosystemResponse(BaseModel):
    """Response model for Zapier ecosystem operations."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    component_type: Optional[ZapierComponentType] = None
    entity_area: Optional[ZapierEntityArea] = None


class ZapierTableSyncRequest(BaseModel):
    """Request model for syncing Zapier Tables with Notion."""
    table_id: str
    entity_area: ZapierEntityArea
    force_sync: bool = False


class ZapierWebhookPayload(BaseModel):
    """Model for incoming Zapier webhook payloads."""
    component_type: ZapierComponentType
    entity_area: ZapierEntityArea
    action: str
    data: Dict[str, Any]
    timestamp: datetime


# Initialize router
router = APIRouter(prefix="/zapier-ecosystem", tags=["zapier-ecosystem"])

# Initialize services
notion_service = NotionService.from_env()
zapier_service = ZapierEcosystemService(notion_service=notion_service)


@router.post("/setup", response_model=ZapierEcosystemResponse)
async def setup_complete_ecosystem(
    background_tasks: BackgroundTasks,
    authenticated: bool = Depends(verify_staff_api_key)
):
    """
    Set up the complete Zapier ecosystem with all components.
    
    This endpoint creates all Tables, Interfaces, Chatbots, Canvases, and Agents
    across The Connection Practice, The 7 Space, and HigherSelf Network Core.
    """
    try:
        if is_api_disabled():
            logger.info("API disabled: Simulating Zapier ecosystem setup")
            return ZapierEcosystemResponse(
                success=True,
                message="Zapier ecosystem setup simulated successfully (TEST MODE)",
                data={
                    "tables_created": 9,
                    "interfaces_created": 6,
                    "chatbots_created": 6,
                    "canvases_created": 6,
                    "agents_created": 9,
                    "mode": "simulation"
                }
            )
        
        # Run setup in background for long-running operation
        background_tasks.add_task(zapier_service.setup_complete_ecosystem)
        
        return ZapierEcosystemResponse(
            success=True,
            message="Zapier ecosystem setup initiated. Check logs for progress.",
            data={"status": "initiated", "estimated_duration": "10-15 minutes"}
        )
        
    except Exception as e:
        logger.error(f"Error setting up Zapier ecosystem: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to setup Zapier ecosystem: {str(e)}"
        )


@router.post("/sync-table", response_model=ZapierEcosystemResponse)
async def sync_table_with_notion(
    sync_request: ZapierTableSyncRequest,
    authenticated: bool = Depends(verify_staff_api_key)
):
    """
    Synchronize a specific Zapier Table with its corresponding Notion database.
    
    Args:
        sync_request: Table sync configuration
    """
    try:
        if is_api_disabled():
            logger.info(f"API disabled: Simulating table sync for {sync_request.table_id}")
            return ZapierEcosystemResponse(
                success=True,
                message=f"Table sync simulated for {sync_request.table_id} (TEST MODE)",
                data={
                    "table_id": sync_request.table_id,
                    "synced_records": 25,
                    "mode": "simulation"
                },
                component_type=ZapierComponentType.TABLE,
                entity_area=sync_request.entity_area
            )
        
        # Find the table configuration
        table_config = None
        for config in zapier_service.ecosystem_config.tables:
            if config.table_id == sync_request.table_id:
                table_config = config
                break
        
        if not table_config:
            raise HTTPException(
                status_code=404,
                detail=f"Table configuration not found: {sync_request.table_id}"
            )
        
        # Perform sync
        sync_result = await zapier_service.sync_table_with_notion(table_config)
        
        return ZapierEcosystemResponse(
            success=sync_result.get("success", False),
            message=f"Table sync completed for {sync_request.table_id}",
            data=sync_result,
            component_type=ZapierComponentType.TABLE,
            entity_area=sync_request.entity_area
        )
        
    except Exception as e:
        logger.error(f"Error syncing table {sync_request.table_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync table: {str(e)}"
        )


@router.get("/status", response_model=ZapierEcosystemResponse)
async def get_ecosystem_status(
    authenticated: bool = Depends(verify_staff_api_key)
):
    """
    Get the current status of the Zapier ecosystem.
    
    Returns information about all components and their operational status.
    """
    try:
        if is_api_disabled():
            logger.info("API disabled: Returning simulated ecosystem status")
            return ZapierEcosystemResponse(
                success=True,
                message="Zapier ecosystem status retrieved (TEST MODE)",
                data={
                    "connection_practice": {
                        "tables": 3,
                        "interfaces": 2,
                        "chatbots": 2,
                        "canvases": 2,
                        "agents": 3,
                        "status": "operational"
                    },
                    "the_7_space": {
                        "tables": 3,
                        "interfaces": 2,
                        "chatbots": 2,
                        "canvases": 2,
                        "agents": 3,
                        "status": "operational"
                    },
                    "network_core": {
                        "tables": 3,
                        "interfaces": 2,
                        "chatbots": 2,
                        "canvases": 2,
                        "agents": 3,
                        "status": "operational"
                    },
                    "overall_status": "operational",
                    "last_updated": datetime.now().isoformat(),
                    "mode": "simulation"
                }
            )
        
        # Get actual status from Zapier service
        # This would involve checking the status of all components
        status_data = {
            "connection_practice": {
                "tables": len([t for t in zapier_service.ecosystem_config.tables 
                             if t.entity_area == ZapierEntityArea.CONNECTION_PRACTICE]),
                "interfaces": len([i for i in zapier_service.ecosystem_config.interfaces 
                                 if i.entity_area == ZapierEntityArea.CONNECTION_PRACTICE]),
                "chatbots": len([c for c in zapier_service.ecosystem_config.chatbots 
                               if c.entity_area == ZapierEntityArea.CONNECTION_PRACTICE]),
                "canvases": len([c for c in zapier_service.ecosystem_config.canvases 
                               if c.entity_area == ZapierEntityArea.CONNECTION_PRACTICE]),
                "agents": len([a for a in zapier_service.ecosystem_config.agents 
                             if a.entity_area == ZapierEntityArea.CONNECTION_PRACTICE]),
                "status": "configured"
            },
            "the_7_space": {
                "tables": len([t for t in zapier_service.ecosystem_config.tables 
                             if t.entity_area == ZapierEntityArea.THE_7_SPACE]),
                "interfaces": len([i for i in zapier_service.ecosystem_config.interfaces 
                                 if i.entity_area == ZapierEntityArea.THE_7_SPACE]),
                "chatbots": len([c for c in zapier_service.ecosystem_config.chatbots 
                               if c.entity_area == ZapierEntityArea.THE_7_SPACE]),
                "canvases": len([c for c in zapier_service.ecosystem_config.canvases 
                               if c.entity_area == ZapierEntityArea.THE_7_SPACE]),
                "agents": len([a for a in zapier_service.ecosystem_config.agents 
                             if a.entity_area == ZapierEntityArea.THE_7_SPACE]),
                "status": "configured"
            },
            "network_core": {
                "tables": len([t for t in zapier_service.ecosystem_config.tables 
                             if t.entity_area == ZapierEntityArea.NETWORK_CORE]),
                "interfaces": len([i for i in zapier_service.ecosystem_config.interfaces 
                                 if i.entity_area == ZapierEntityArea.NETWORK_CORE]),
                "chatbots": len([c for c in zapier_service.ecosystem_config.chatbots 
                               if c.entity_area == ZapierEntityArea.NETWORK_CORE]),
                "canvases": len([c for c in zapier_service.ecosystem_config.canvases 
                               if c.entity_area == ZapierEntityArea.NETWORK_CORE]),
                "agents": len([a for a in zapier_service.ecosystem_config.agents 
                             if a.entity_area == ZapierEntityArea.NETWORK_CORE]),
                "status": "configured"
            },
            "overall_status": "configured",
            "last_updated": datetime.now().isoformat()
        }
        
        return ZapierEcosystemResponse(
            success=True,
            message="Zapier ecosystem status retrieved successfully",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"Error getting ecosystem status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ecosystem status: {str(e)}"
        )


@router.post("/webhook", response_model=ZapierEcosystemResponse)
async def handle_zapier_webhook(
    request: Request,
    payload: ZapierWebhookPayload
):
    """
    Handle incoming webhooks from Zapier components.
    
    This endpoint receives notifications from Zapier Tables, Interfaces, Chatbots,
    Canvases, and Agents and processes them accordingly.
    """
    try:
        if is_api_disabled():
            logger.info(f"API disabled: Simulating webhook processing for {payload.component_type}")
            return ZapierEcosystemResponse(
                success=True,
                message=f"Zapier webhook processed (TEST MODE): {payload.action}",
                data={
                    "component_type": payload.component_type,
                    "entity_area": payload.entity_area,
                    "action": payload.action,
                    "processed_at": datetime.now().isoformat(),
                    "mode": "simulation"
                },
                component_type=payload.component_type,
                entity_area=payload.entity_area
            )
        
        # Validate webhook signature (if configured)
        if zapier_service.webhook_secret:
            # Implement webhook signature validation here
            pass
        
        # Process webhook based on component type and entity area
        result = await process_zapier_webhook(payload)
        
        return ZapierEcosystemResponse(
            success=True,
            message=f"Zapier webhook processed successfully: {payload.action}",
            data=result,
            component_type=payload.component_type,
            entity_area=payload.entity_area
        )
        
    except Exception as e:
        logger.error(f"Error processing Zapier webhook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process webhook: {str(e)}"
        )


async def process_zapier_webhook(payload: ZapierWebhookPayload) -> Dict[str, Any]:
    """
    Process a Zapier webhook payload based on component type and entity area.
    
    Args:
        payload: The webhook payload from Zapier
        
    Returns:
        Processing result
    """
    logger.info(f"Processing Zapier webhook: {payload.component_type} - {payload.action}")
    
    # Route to appropriate handler based on component type
    if payload.component_type == ZapierComponentType.TABLE:
        return await handle_table_webhook(payload)
    elif payload.component_type == ZapierComponentType.INTERFACE:
        return await handle_interface_webhook(payload)
    elif payload.component_type == ZapierComponentType.CHATBOT:
        return await handle_chatbot_webhook(payload)
    elif payload.component_type == ZapierComponentType.CANVAS:
        return await handle_canvas_webhook(payload)
    elif payload.component_type == ZapierComponentType.AGENT:
        return await handle_agent_webhook(payload)
    else:
        raise ValueError(f"Unknown component type: {payload.component_type}")


async def handle_table_webhook(payload: ZapierWebhookPayload) -> Dict[str, Any]:
    """Handle webhooks from Zapier Tables."""
    # Sync data back to Notion if needed
    if payload.action in ["record_created", "record_updated", "record_deleted"]:
        # Update corresponding Notion database
        await notion_service.sync_from_zapier_table(payload.data)
    
    return {"action": payload.action, "records_processed": 1}


async def handle_interface_webhook(payload: ZapierWebhookPayload) -> Dict[str, Any]:
    """Handle webhooks from Zapier Interfaces."""
    # Process interface actions (form submissions, button clicks, etc.)
    return {"action": payload.action, "interface_event_processed": True}


async def handle_chatbot_webhook(payload: ZapierWebhookPayload) -> Dict[str, Any]:
    """Handle webhooks from Zapier Chatbots."""
    # Process chatbot interactions and responses
    return {"action": payload.action, "chatbot_interaction_processed": True}


async def handle_canvas_webhook(payload: ZapierWebhookPayload) -> Dict[str, Any]:
    """Handle webhooks from Zapier Canvases."""
    # Process canvas interactions and updates
    return {"action": payload.action, "canvas_update_processed": True}


async def handle_agent_webhook(payload: ZapierWebhookPayload) -> Dict[str, Any]:
    """Handle webhooks from Zapier Agents."""
    # Process agent automation results
    return {"action": payload.action, "agent_automation_processed": True}
