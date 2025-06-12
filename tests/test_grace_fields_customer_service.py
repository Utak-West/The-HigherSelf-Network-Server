#!/usr/bin/env python3
"""
Test Suite for Grace Fields Enhanced Customer Service

This module contains comprehensive tests for the enhanced Grace Fields
customer service orchestration system.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.agent_personalities import BaseAgent
from agents.grace_fields_enhanced import EnhancedGraceFields
from models.customer_service_models import (
    BusinessEntity,
    CustomerSentiment,
    CustomerServiceRequest,
    IssueCategory,
    SeverityLevel,
)
from services.escalation_service import EscalationService
from services.notion_service import NotionService
from utils.message_bus import MessageBus


class MockAgent(BaseAgent):
    """Mock agent for testing purposes."""

    def __init__(self, name: str, agent_type: str = "TestAgent"):
        super().__init__(
            agent_id=f"test_{name.lower()}",
            name=name,
            description=f"Test {name} agent",
            notion_service=None,
        )
        self.agent_type = agent_type
        self.tone = "test"


@pytest.fixture
def mock_agents():
    """Create mock agents for testing."""
    return [
        MockAgent("Nyra", "LeadCaptureAgent"),
        MockAgent("Solari", "BookingAgent"),
        MockAgent("Ruvo", "TaskAgent"),
        MockAgent("Liora", "MarketingAgent"),
        MockAgent("Sage", "CommunityAgent"),
        MockAgent("Elan", "ContentAgent"),
        MockAgent("Zevi", "AnalyticsAgent"),
    ]


@pytest.fixture
def mock_notion_service():
    """Create mock Notion service."""
    return MagicMock(spec=NotionService)


@pytest.fixture
def mock_escalation_service():
    """Create mock escalation service."""
    return MagicMock(spec=EscalationService)


@pytest.fixture
def mock_message_bus():
    """Create mock message bus."""
    return MagicMock(spec=MessageBus)


@pytest.fixture
def enhanced_grace(
    mock_agents, mock_notion_service, mock_escalation_service, mock_message_bus
):
    """Create enhanced Grace Fields instance for testing."""
    return EnhancedGraceFields(
        agents=mock_agents,
        message_bus=mock_message_bus,
        notion_service=mock_notion_service,
        escalation_service=mock_escalation_service,
    )


class TestEnhancedGraceFields:
    """Test cases for Enhanced Grace Fields functionality."""

    def test_initialization(self, enhanced_grace):
        """Test that Enhanced Grace Fields initializes correctly."""
        assert enhanced_grace is not None
        assert len(enhanced_grace.agents) == 7
        assert "Nyra" in enhanced_grace.agents
        assert "Solari" in enhanced_grace.agents
        assert enhanced_grace.coordination_patterns is not None
        assert enhanced_grace.response_templates is not None

    def test_coordination_patterns_initialization(self, enhanced_grace):
        """Test that coordination patterns are properly initialized."""
        patterns = enhanced_grace.coordination_patterns

        assert "high_value_client_onboarding" in patterns
        assert "service_recovery_protocol" in patterns
        assert "campaign_launch_sequence" in patterns

        # Test pattern structure
        onboarding_pattern = patterns["high_value_client_onboarding"]
        assert onboarding_pattern.pattern_name == "High-Value Client Onboarding"
        assert len(onboarding_pattern.coordination_sequence) > 0
        assert onboarding_pattern.expected_duration > timedelta(0)

    def test_response_templates_initialization(self, enhanced_grace):
        """Test that response templates are properly initialized."""
        templates = enhanced_grace.response_templates

        required_templates = [
            "initial_greeting",
            "single_agent_delegation",
            "multi_agent_coordination",
            "complex_issue_acknowledgment",
            "human_escalation",
            "issue_resolution",
        ]

        for template in required_templates:
            assert template in templates
            assert isinstance(templates[template], str)
            assert len(templates[template]) > 0

    @pytest.mark.asyncio
    async def test_analyze_request_billing_issue(self, enhanced_grace):
        """Test request analysis for billing issues."""
        description = "I was charged twice for my order and need a refund"
        business_entity = BusinessEntity.ART_GALLERY

        category, severity = await enhanced_grace._analyze_request(
            description, business_entity
        )

        assert category == IssueCategory.BILLING_ORDER
        assert severity in [SeverityLevel.LEVEL_1, SeverityLevel.LEVEL_2]

    @pytest.mark.asyncio
    async def test_analyze_request_legal_issue(self, enhanced_grace):
        """Test request analysis for legal issues."""
        description = "I need to speak with someone about legal compliance issues"
        business_entity = BusinessEntity.CONSULTANCY

        category, severity = await enhanced_grace._analyze_request(
            description, business_entity
        )

        assert category == IssueCategory.LEGAL_COMPLIANCE
        assert severity == SeverityLevel.LEVEL_4

    @pytest.mark.asyncio
    async def test_analyze_request_vip_issue(self, enhanced_grace):
        """Test request analysis for VIP issues."""
        description = "As a VIP member, I need premium assistance with my booking"
        business_entity = BusinessEntity.WELLNESS_CENTER

        category, severity = await enhanced_grace._analyze_request(
            description, business_entity
        )

        assert severity == SeverityLevel.LEVEL_3

    @pytest.mark.asyncio
    async def test_standard_delegation(self, enhanced_grace):
        """Test Level 1 standard delegation workflow."""
        enhanced_grace.escalation_service.create_escalation_ticket = AsyncMock(
            return_value="ESC-12345"
        )

        result = await enhanced_grace.process_customer_service_request(
            customer_email="test@example.com",
            description="I need to change my booking time",
            business_entity=BusinessEntity.WELLNESS_CENTER,
            priority="medium",
        )

        assert result["status"] == "delegated"
        assert "assigned_agent" in result
        assert "request_id" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self, enhanced_grace):
        """Test Level 2 multi-agent coordination workflow."""
        enhanced_grace.escalation_service.create_escalation_ticket = AsyncMock(
            return_value="ESC-12345"
        )

        result = await enhanced_grace.process_customer_service_request(
            customer_email="test@example.com",
            description="I need a complex marketing campaign with multiple services",
            business_entity=BusinessEntity.ART_GALLERY,
            priority="high",
        )

        assert result["status"] == "coordinating"
        assert "assigned_agents" in result
        assert "workflow_id" in result
        assert len(result["assigned_agents"]) >= 3

    @pytest.mark.asyncio
    async def test_human_escalation(self, enhanced_grace):
        """Test Level 4 human escalation workflow."""
        enhanced_grace.escalation_service.create_escalation_ticket = AsyncMock(
            return_value="ESC-12345"
        )

        result = await enhanced_grace.process_customer_service_request(
            customer_email="test@example.com",
            description="I'm consulting my attorney about legal compliance issues",
            business_entity=BusinessEntity.CONSULTANCY,
            priority="urgent",
        )

        assert result["status"] == "escalated"
        assert "ticket_id" in result
        assert "escalation_reason" in result

    def test_get_primary_agent_for_category(self, enhanced_grace):
        """Test agent selection for different issue categories."""
        assert (
            enhanced_grace._get_primary_agent_for_category(IssueCategory.BILLING_ORDER)
            == "Solari"
        )
        assert (
            enhanced_grace._get_primary_agent_for_category(
                IssueCategory.CUSTOMER_FEEDBACK
            )
            == "Sage"
        )
        assert (
            enhanced_grace._get_primary_agent_for_category(
                IssueCategory.LEAD_MANAGEMENT
            )
            == "Nyra"
        )
        assert (
            enhanced_grace._get_primary_agent_for_category(
                IssueCategory.MARKETING_CAMPAIGN
            )
            == "Liora"
        )

    def test_get_coordination_agents_for_category(self, enhanced_grace):
        """Test multi-agent coordination selection."""
        agents = enhanced_grace._get_coordination_agents_for_category(
            IssueCategory.VIP_SERVICE
        )
        assert len(agents) >= 3
        assert "Sage" in agents  # VIP service should include Sage

    def test_delegation_script_creation(self, enhanced_grace):
        """Test delegation script creation for different agents."""
        request = CustomerServiceRequest(
            customer_email="test@example.com",
            business_entity=BusinessEntity.ART_GALLERY,
            issue_category=IssueCategory.BILLING_ORDER,
            severity_level=SeverityLevel.LEVEL_1,
            description="Test billing issue",
        )

        script = enhanced_grace._create_delegation_script(request, "Solari")
        assert "Solari" in script
        assert "test@example.com" in script
        assert "clear and luminous approach" in script

    def test_escalation_reason_generation(self, enhanced_grace):
        """Test escalation reason generation."""
        request = CustomerServiceRequest(
            customer_email="test@example.com",
            business_entity=BusinessEntity.CONSULTANCY,
            issue_category=IssueCategory.LEGAL_COMPLIANCE,
            severity_level=SeverityLevel.LEVEL_4,
            description="Legal compliance question",
        )

        reason = enhanced_grace._get_escalation_reason(request)
        assert "Legal or compliance matter" in reason

    @pytest.mark.asyncio
    async def test_workflow_harmony_monitoring(self, enhanced_grace):
        """Test workflow harmony monitoring functionality."""
        # Add some test requests
        test_request = CustomerServiceRequest(
            customer_email="test@example.com",
            business_entity=BusinessEntity.ART_GALLERY,
            issue_category=IssueCategory.BILLING_ORDER,
            severity_level=SeverityLevel.LEVEL_1,
            description="Test request",
        )
        enhanced_grace.active_requests["test-123"] = test_request

        harmony_status = await enhanced_grace.monitor_workflow_harmony()

        assert "overall_status" in harmony_status
        assert "active_requests" in harmony_status
        assert "agent_utilization" in harmony_status
        assert "system_health" in harmony_status
        assert "recommendations" in harmony_status

    @pytest.mark.asyncio
    async def test_request_resolution(self, enhanced_grace):
        """Test request resolution functionality."""
        # Create and add a test request
        test_request = CustomerServiceRequest(
            customer_email="test@example.com",
            business_entity=BusinessEntity.WELLNESS_CENTER,
            issue_category=IssueCategory.BILLING_ORDER,
            severity_level=SeverityLevel.LEVEL_1,
            description="Test billing issue",
        )
        request_id = test_request.request_id
        enhanced_grace.active_requests[request_id] = test_request

        result = await enhanced_grace.resolve_request(
            request_id=request_id,
            resolution_summary="Issue resolved successfully",
            agent_name="Solari",
        )

        assert result["status"] == "resolved"
        assert result["resolved_by"] == "Solari"
        assert enhanced_grace.active_requests[request_id].resolved is True

    @pytest.mark.asyncio
    async def test_customer_interaction_history(self, enhanced_grace):
        """Test customer interaction history retrieval."""
        # Create test requests for the same customer
        customer_email = "test@example.com"

        for i in range(3):
            test_request = CustomerServiceRequest(
                customer_email=customer_email,
                business_entity=BusinessEntity.ART_GALLERY,
                issue_category=IssueCategory.BILLING_ORDER,
                severity_level=SeverityLevel.LEVEL_1,
                description=f"Test request {i}",
            )
            enhanced_grace.active_requests[f"test-{i}"] = test_request

        history = await enhanced_grace.get_customer_interaction_history(customer_email)

        assert len(history) == 3
        assert all(req["customer_email"] == customer_email for req in history)

    def test_agent_coordination_action_mapping(self, enhanced_grace):
        """Test agent coordination action mapping."""
        action = enhanced_grace._get_agent_coordination_action(
            "Nyra", IssueCategory.BILLING_ORDER
        )
        assert "review customer history" in action

        action = enhanced_grace._get_agent_coordination_action(
            "Solari", IssueCategory.VIP_SERVICE
        )
        assert "premium service delivery" in action

    def test_response_timeframe_calculation(self, enhanced_grace):
        """Test response timeframe calculation based on priority."""
        assert enhanced_grace._get_response_timeframe("urgent") == "30 minutes"
        assert enhanced_grace._get_response_timeframe("high") == "1 hour"
        assert enhanced_grace._get_response_timeframe("medium") == "2 hours"
        assert enhanced_grace._get_response_timeframe("low") == "4 hours"

    def test_escalation_timeframe_calculation(self, enhanced_grace):
        """Test escalation timeframe calculation."""
        assert enhanced_grace._get_escalation_timeframe("urgent") == "1 hour"
        assert enhanced_grace._get_escalation_timeframe("high") == "2 hours"
        assert enhanced_grace._get_escalation_timeframe("medium") == "4 hours"
        assert enhanced_grace._get_escalation_timeframe("low") == "1 business day"


class TestEscalationService:
    """Test cases for the Escalation Service."""

    @pytest.fixture
    def escalation_service(self):
        """Create escalation service for testing."""
        return EscalationService()

    @pytest.mark.asyncio
    async def test_create_escalation_ticket(self, escalation_service):
        """Test escalation ticket creation."""
        escalation_data = {
            "request_id": "test-123",
            "customer_email": "test@example.com",
            "business_entity": "art_gallery",
            "issue_category": "legal_compliance",
            "description": "Legal compliance question",
            "priority": "urgent",
            "escalation_reason": "Legal matter requiring professional interpretation",
        }

        ticket_id = await escalation_service.create_escalation_ticket(escalation_data)

        assert ticket_id.startswith("ESC-")
        assert ticket_id in escalation_service.tickets

    @pytest.mark.asyncio
    async def test_update_ticket_status(self, escalation_service):
        """Test ticket status updates."""
        # Create a ticket first
        escalation_data = {
            "request_id": "test-123",
            "customer_email": "test@example.com",
            "business_entity": "wellness_center",
            "issue_category": "billing_order",
            "description": "Billing issue",
            "priority": "high",
        }

        ticket_id = await escalation_service.create_escalation_ticket(escalation_data)

        # Update the ticket
        success = await escalation_service.update_ticket_status(
            ticket_id=ticket_id, status="in_progress", assigned_human="John Doe"
        )

        assert success is True
        ticket = await escalation_service.get_ticket(ticket_id)
        assert ticket.status == "in_progress"
        assert ticket.assigned_human == "John Doe"

    @pytest.mark.asyncio
    async def test_escalation_metrics(self, escalation_service):
        """Test escalation metrics calculation."""
        # Create some test tickets
        for i in range(5):
            escalation_data = {
                "request_id": f"test-{i}",
                "customer_email": f"test{i}@example.com",
                "business_entity": "consultancy",
                "issue_category": "technical_support",
                "description": f"Test issue {i}",
                "priority": "medium",
            }
            await escalation_service.create_escalation_ticket(escalation_data)

        metrics = await escalation_service.get_escalation_metrics()

        assert metrics["total_escalations"] == 5
        assert "resolution_rate" in metrics
        assert "escalations_by_priority" in metrics
        assert "escalations_by_category" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
