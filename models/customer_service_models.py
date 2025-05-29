#!/usr/bin/env python3
"""
Customer Service Models for Grace Fields Enhanced Orchestration

This module defines Pydantic models for customer service workflows,
delegation protocols, and multi-agent coordination patterns.
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class SeverityLevel(Enum):
    """Customer service issue severity levels."""

    LEVEL_1 = "standard_delegation"  # 1-2 agents needed
    LEVEL_2 = "multi_agent_coordination"  # 3-4 agents needed
    LEVEL_3 = "full_network_response"  # 5+ agents needed
    LEVEL_4 = "human_specialist_required"  # Beyond agent capabilities


class CustomerServiceBusinessEntity(Enum):
    """Business entity types for customer service in The HigherSelf Network."""

    ART_GALLERY = "art_gallery"
    WELLNESS_CENTER = "wellness_center"
    CONSULTANCY = "consultancy"
    INTERIOR_DESIGN = "interior_design"
    LUXURY_RENOVATIONS = "luxury_renovations"
    EXECUTIVE_WELLNESS = "executive_wellness"
    CORPORATE_WELLNESS = "corporate_wellness"


class IssueCategory(Enum):
    """Customer service issue categories."""

    BILLING_ORDER = "billing_order"
    CUSTOMER_FEEDBACK = "customer_feedback"
    LEAD_MANAGEMENT = "lead_management"
    TASK_COORDINATION = "task_coordination"
    MARKETING_CAMPAIGN = "marketing_campaign"
    TECHNICAL_SUPPORT = "technical_support"
    LEGAL_COMPLIANCE = "legal_compliance"
    VIP_SERVICE = "vip_service"
    COMMUNITY_ENGAGEMENT = "community_engagement"
    CONTENT_REQUEST = "content_request"


class CustomerSentiment(Enum):
    """Customer sentiment levels."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    CONCERNED = "concerned"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"


class WorkflowStatus(Enum):
    """Workflow status options."""

    PENDING = "pending"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class AgentInteraction(BaseModel):
    """Model for individual agent interactions within a workflow."""

    interaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    action_type: str
    description: str
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_minutes: Optional[int] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[str] = None
    next_agent: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CustomerServiceRequest(BaseModel):
    """Comprehensive model for customer service requests."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_email: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    business_entity: CustomerServiceBusinessEntity
    issue_category: IssueCategory
    severity_level: SeverityLevel
    description: str
    priority: str = "medium"  # low, medium, high, urgent
    customer_sentiment: CustomerSentiment = CustomerSentiment.NEUTRAL

    # Workflow tracking
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    assigned_agents: List[str] = Field(default_factory=list)
    workflow_id: Optional[str] = None
    current_step: int = 0

    # Status tracking
    status: WorkflowStatus = WorkflowStatus.PENDING
    resolved: bool = False
    escalated: bool = False
    resolution_summary: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    # Interaction history
    interaction_history: List[AgentInteraction] = Field(default_factory=list)

    # Customer context
    customer_tier: str = "standard"  # standard, premium, vip
    previous_interactions: int = 0
    lifetime_value: float = 0.0

    # Business context
    related_orders: List[str] = Field(default_factory=list)
    related_bookings: List[str] = Field(default_factory=list)
    related_campaigns: List[str] = Field(default_factory=list)

    @validator("updated_at", pre=True, always=True)
    def set_updated_at(cls, v):
        return datetime.now()

    def add_interaction(
        self, agent_name: str, action_type: str, description: str, **kwargs
    ):
        """Add an interaction to the request history."""
        interaction = AgentInteraction(
            agent_name=agent_name,
            action_type=action_type,
            description=description,
            **kwargs,
        )
        self.interaction_history.append(interaction)
        self.updated_at = datetime.now()

    def update_status(self, new_status: WorkflowStatus, notes: Optional[str] = None):
        """Update the request status with optional notes."""
        self.status = new_status
        self.updated_at = datetime.now()

        if notes:
            self.add_interaction(
                agent_name="Grace",
                action_type="status_update",
                description=f"Status changed to {new_status.value}: {notes}",
            )


class CoordinationStep(BaseModel):
    """Model for individual steps in a coordination pattern."""

    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    action_type: str
    description: str
    estimated_duration: timedelta
    dependencies: List[str] = Field(
        default_factory=list
    )  # Other step IDs this depends on
    success_criteria: List[str] = Field(default_factory=list)
    fallback_actions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CoordinationPattern(BaseModel):
    """Model for multi-agent coordination patterns."""

    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pattern_name: str
    description: str
    trigger_conditions: List[str]
    coordination_steps: List[CoordinationStep]
    expected_duration: timedelta
    success_criteria: List[str]
    fallback_actions: List[str]
    applicable_categories: List[IssueCategory] = Field(default_factory=list)
    applicable_entities: List[CustomerServiceBusinessEntity] = Field(
        default_factory=list
    )
    minimum_severity: SeverityLevel = SeverityLevel.LEVEL_2
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    success_rate: float = 0.0


class WorkflowExecution(BaseModel):
    """Model for tracking workflow execution."""

    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    pattern_id: Optional[str] = None
    pattern_name: Optional[str] = None

    # Execution tracking
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    current_step_index: int = 0

    # Step execution details
    step_executions: List[Dict[str, Any]] = Field(default_factory=list)

    # Performance metrics
    total_duration: Optional[timedelta] = None
    agent_handoffs: int = 0
    escalations: int = 0
    customer_touchpoints: int = 0

    # Results
    success: bool = False
    failure_reason: Optional[str] = None
    customer_satisfaction_score: Optional[float] = None
    resolution_quality_score: Optional[float] = None

    def add_step_execution(
        self, step_id: str, agent_name: str, status: WorkflowStatus, **kwargs
    ):
        """Add a step execution record."""
        step_execution = {
            "step_id": step_id,
            "agent_name": agent_name,
            "status": status.value,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        }
        self.step_executions.append(step_execution)

    def complete_execution(self, success: bool, failure_reason: Optional[str] = None):
        """Mark the workflow execution as completed."""
        self.completed_at = datetime.now()
        self.status = WorkflowStatus.COMPLETED if success else WorkflowStatus.FAILED
        self.success = success
        self.failure_reason = failure_reason

        if self.started_at and self.completed_at:
            self.total_duration = self.completed_at - self.started_at


class DelegationRule(BaseModel):
    """Model for agent delegation rules."""

    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_name: str
    description: str

    # Conditions
    issue_categories: List[IssueCategory] = Field(default_factory=list)
    business_entities: List[CustomerServiceBusinessEntity] = Field(default_factory=list)
    severity_levels: List[SeverityLevel] = Field(default_factory=list)
    customer_tiers: List[str] = Field(default_factory=list)
    sentiment_levels: List[CustomerSentiment] = Field(default_factory=list)

    # Actions
    primary_agent: str
    backup_agents: List[str] = Field(default_factory=list)
    coordination_pattern: Optional[str] = None
    escalation_threshold: int = 3  # Number of failed attempts before escalation

    # Metadata
    priority_boost: int = 0  # How much to increase priority (0-3)
    response_time_target: timedelta = timedelta(hours=2)
    created_at: datetime = Field(default_factory=datetime.now)
    active: bool = True
    usage_count: int = 0
    success_rate: float = 0.0


class EscalationTrigger(BaseModel):
    """Model for escalation trigger conditions."""

    trigger_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trigger_name: str
    description: str

    # Trigger conditions
    keywords: List[str] = Field(default_factory=list)
    issue_categories: List[IssueCategory] = Field(default_factory=list)
    severity_levels: List[SeverityLevel] = Field(default_factory=list)
    sentiment_levels: List[CustomerSentiment] = Field(default_factory=list)
    customer_tiers: List[str] = Field(default_factory=list)

    # Escalation criteria
    max_agent_attempts: int = 3
    max_resolution_time: timedelta = timedelta(hours=24)
    requires_human_judgment: bool = False
    legal_compliance_required: bool = False
    high_value_threshold: float = 500.0

    # Notification settings
    notification_email: Optional[str] = None
    notification_priority: str = "high"  # low, medium, high, urgent
    include_interaction_history: bool = True

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    active: bool = True
    trigger_count: int = 0


class CustomerServiceMetrics(BaseModel):
    """Model for customer service performance metrics."""

    metrics_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    period_start: datetime
    period_end: datetime

    # Volume metrics
    total_requests: int = 0
    requests_by_category: Dict[str, int] = Field(default_factory=dict)
    requests_by_entity: Dict[str, int] = Field(default_factory=dict)
    requests_by_severity: Dict[str, int] = Field(default_factory=dict)

    # Resolution metrics
    resolved_requests: int = 0
    escalated_requests: int = 0
    first_contact_resolution: int = 0
    average_resolution_time: timedelta = timedelta(0)
    resolution_rate: float = 0.0
    escalation_rate: float = 0.0

    # Quality metrics
    customer_satisfaction_score: float = 0.0
    agent_coordination_success_rate: float = 0.0
    workflow_completion_rate: float = 0.0

    # Agent performance
    agent_utilization: Dict[str, int] = Field(default_factory=dict)
    agent_success_rates: Dict[str, float] = Field(default_factory=dict)
    agent_average_response_times: Dict[str, float] = Field(default_factory=dict)

    # System health
    system_uptime: float = 100.0
    integration_health: Dict[str, str] = Field(default_factory=dict)

    # Recommendations
    improvement_recommendations: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.now)

    def calculate_derived_metrics(self):
        """Calculate derived metrics from base data."""
        if self.total_requests > 0:
            self.resolution_rate = self.resolved_requests / self.total_requests
            self.escalation_rate = self.escalated_requests / self.total_requests

        # Add other derived calculations as needed
