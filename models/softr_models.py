"""
Softr Models

This module defines models for Softr integration, particularly for staff interfaces with agents.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import uuid

class StaffUser(BaseModel):
    """Staff user model for Softr integration"""
    id: str
    name: str
    email: str
    roles: List[str] = Field(default_factory=list)

class AgentRequest(BaseModel):
    """Request from a staff member to an agent"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    staff_id: str = Field(..., description="ID of the staff member making the request")
    agent_id: str = Field(..., description="ID of the agent to interact with")
    request_type: str = Field(..., description="Type of request (e.g., 'task', 'question', 'action')")
    content: str = Field(..., description="Content of the request")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for the request")
    created_at: datetime = Field(default_factory=datetime.now)
    workflow_instance_id: Optional[str] = Field(None, description="ID of the workflow instance if applicable")

class AgentResponse(BaseModel):
    """Response from an agent to a staff member"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = Field(..., description="ID of the request this is responding to")
    agent_id: str = Field(..., description="ID of the agent providing the response")
    status: Literal["success", "error", "pending"] = "success"
    content: str = Field(..., description="Content of the response")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional data returned by the agent")
    created_at: datetime = Field(default_factory=datetime.now)
    
class AgentInteraction(BaseModel):
    """Record of an interaction between a staff member and an agent"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    staff_id: str = Field(..., description="ID of the staff member")
    agent_id: str = Field(..., description="ID of the agent")
    request: AgentRequest
    response: Optional[AgentResponse] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: Literal["pending", "completed", "failed"] = "pending"
    workflow_instance_id: Optional[str] = Field(None, description="ID of the workflow instance if applicable")

# API Request/Response Models
class AgentListResponse(BaseModel):
    """Response model for listing available agents"""
    agents: List[Dict[str, Any]]

class AgentInteractionResponse(BaseModel):
    """Response model for agent interactions"""
    interaction: AgentInteraction

class AgentHistoryResponse(BaseModel):
    """Response model for agent interaction history"""
    interactions: List[AgentInteraction]

class SoftrWebhookPayload(BaseModel):
    """Payload for Softr webhooks"""
    event_type: str = Field(..., description="Type of event (e.g., 'new_staff_request')")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(default_factory=datetime.now)
