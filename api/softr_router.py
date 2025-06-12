"""
Softr Router

This module provides API endpoints for staff to interact with agents via Softr.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query
from loguru import logger

from models.softr_models import (
    AgentHistoryResponse,
    AgentInteraction,
    AgentInteractionResponse,
    AgentListResponse,
    AgentRequest,
    AgentResponse,
    SoftrWebhookPayload,
    StaffUser,
)
from services.agent_manager import AgentManager, get_agent_manager
from services.notion_service import NotionService
from services.softr_service import SoftrService
from utils.auth import get_staff_user, verify_webhook_signature

# Create router
router = APIRouter(
    prefix="/api/staff", tags=["staff"], responses={404: {"description": "Not found"}}
)


# Get services
async def get_softr_service():
    """Get or initialize the Softr service."""
    # In a real implementation, this would be a singleton or dependency injection
    return SoftrService()


async def get_notion_service():
    """Get or initialize the Notion service."""
    # In a real implementation, this would be a singleton or dependency injection
    return NotionService()


# Endpoints
@router.get("/agents", response_model=AgentListResponse)
async def list_available_agents(
    staff_user: StaffUser = Depends(get_staff_user),
    softr_service: SoftrService = Depends(get_softr_service),
):
    """
    List all available agents that staff can interact with.

    This endpoint returns a list of agents with their capabilities and status.
    """
    try:
        agents = await softr_service.get_available_agents()
        return AgentListResponse(agents=agents)
    except Exception as e:
        logger.error(f"Error listing available agents: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error listing available agents: {str(e)}"
        )


@router.post("/agents/{agent_id}/interact", response_model=AgentInteractionResponse)
async def interact_with_agent(
    agent_id: str,
    request: AgentRequest = Body(...),
    staff_user: StaffUser = Depends(get_staff_user),
    softr_service: SoftrService = Depends(get_softr_service),
    notion_service: NotionService = Depends(get_notion_service),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    """
    Send a request to an agent and get a response.

    This endpoint allows staff to interact with agents by sending requests
    and receiving responses.
    """
    # Validate that the agent exists
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    # Ensure the staff ID in the request matches the authenticated user
    if request.staff_id != staff_user.id:
        raise HTTPException(
            status_code=403,
            detail="Staff ID in request does not match authenticated user",
        )

    # Ensure the agent ID in the request matches the URL parameter
    if request.agent_id != agent_id:
        request.agent_id = agent_id

    try:
        # Process the request with the agent
        # In a real implementation, this would route to the appropriate agent method
        # For now, we'll create a mock response
        response = AgentResponse(
            request_id=request.id,
            agent_id=agent_id,
            status="success",
            content=f"Processed request: {request.content}",
            data={"processed_at": datetime.now().isoformat()},
        )

        # Create an interaction record
        interaction = AgentInteraction(
            staff_id=staff_user.id,
            agent_id=agent_id,
            request=request,
            response=response,
            status="completed",
            workflow_instance_id=request.workflow_instance_id,
        )

        # Record the interaction in Softr
        await softr_service.record_agent_interaction(interaction)

        # If there's a workflow instance, log to its history
        if request.workflow_instance_id:
            await notion_service.log_to_workflow_history(
                request.workflow_instance_id,
                "INFO",
                f"Staff {staff_user.name} interacted with {agent_id}: {request.content}",
                "StaffAgentInterface",
            )

        return AgentInteractionResponse(interaction=interaction)

    except Exception as e:
        # Log the error
        logger.error(f"Error processing staff request: {str(e)}")

        if request.workflow_instance_id:
            await notion_service.log_to_workflow_history(
                request.workflow_instance_id,
                "ERROR",
                f"Error processing staff request: {str(e)}",
                "StaffAgentInterface",
            )

        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )


@router.get("/interactions", response_model=AgentHistoryResponse)
async def get_interaction_history(
    agent_id: Optional[str] = Query(None),
    staff_user: StaffUser = Depends(get_staff_user),
    softr_service: SoftrService = Depends(get_softr_service),
):
    """
    Get the history of interactions between the staff member and agents.

    This endpoint returns a list of past interactions, optionally filtered by agent.
    """
    try:
        # Get the interaction history from Softr
        interactions = await softr_service.get_staff_agent_history(
            staff_user.id, agent_id
        )

        return AgentHistoryResponse(interactions=interactions)

    except Exception as e:
        logger.error(f"Error retrieving interaction history: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving interaction history: {str(e)}"
        )


@router.post("/webhooks/softr", dependencies=[Depends(verify_webhook_signature)])
async def softr_webhook(
    payload: SoftrWebhookPayload = Body(...),
    notion_service: NotionService = Depends(get_notion_service),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    """
    Webhook endpoint for Softr events.

    This endpoint handles events from Softr, such as new staff requests or updates.
    """
    try:
        # Process the webhook payload
        event_type = payload.event_type

        if event_type == "new_staff_request":
            # Handle new staff request
            request_data = payload.data

            # Create an agent request
            request = AgentRequest(**request_data)

            # Get the appropriate agent
            agent = agent_manager.get_agent(request.agent_id)
            if not agent:
                logger.warning(
                    f"Agent {request.agent_id} not found for webhook request"
                )
                return {
                    "status": "error",
                    "message": f"Agent {request.agent_id} not found",
                }

            # In a real implementation, this would route the request to the appropriate agent
            # For now, we'll just log it
            if request.workflow_instance_id:
                await notion_service.log_to_workflow_history(
                    request.workflow_instance_id,
                    "INFO",
                    f"Received new staff request via webhook: {request.content}",
                    "StaffAgentInterface",
                )

        return {"status": "success", "message": f"Processed {event_type} webhook"}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )
