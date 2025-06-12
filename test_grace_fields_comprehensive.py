#!/usr/bin/env python3
"""
Comprehensive test for Grace Fields Enhanced Customer Service functionality.

This test validates the complete customer service orchestration system including:
- Enhanced Grace Fields instantiation
- Multi-level severity processing (Level 1-4)
- Business entity routing across all 7 entities
- Agent coordination and delegation
- Workflow harmony monitoring
"""

import asyncio
import os
import sys
from typing import Any, Dict, List

# Set testing mode before importing anything else
os.environ["TESTING_MODE"] = "true"

# Add the project root to the path
sys.path.insert(0, ".")

from loguru import logger


class MockAgent:
    """Mock agent for comprehensive testing."""

    def __init__(self, name: str, description: str, agent_type: str = None):
        self.name = name
        self.description = description
        self.agent_type = agent_type or f"{name}Agent"
        self.tone = "professional"
        self.capabilities = ["general_support"]


class MockNotionService:
    """Mock Notion service for testing."""

    async def create_page(self, database_id: str, properties: Dict[str, Any]) -> str:
        """Mock page creation."""
        return f"page_{database_id[:8]}"

    async def update_page(self, page_id: str, properties: Dict[str, Any]) -> bool:
        """Mock page update."""
        return True


class MockEscalationService:
    """Mock escalation service for testing."""

    async def create_escalation_ticket(self, escalation_data: Dict[str, Any]) -> str:
        """Create a mock escalation ticket."""
        return f"ESC-{escalation_data.get('request_id', 'TEST')[:8]}"

    async def notify_human_agent(self, ticket_id: str, urgency: str) -> bool:
        """Mock human agent notification."""
        return True


class MockMessageBus:
    """Mock message bus for testing."""

    def __init__(self):
        self.messages = []

    async def publish(self, message) -> None:
        """Mock message publishing."""
        self.messages.append(message)

    def subscribe(self, subscriber: str, callback) -> None:
        """Mock subscription."""
        pass


async def test_enhanced_grace_fields_instantiation():
    """Test that Enhanced Grace Fields can be instantiated properly."""

    try:
        from agents.grace_fields_enhanced import EnhancedGraceFields
        from models.customer_service_models import \
            CustomerServiceBusinessEntity

        logger.info("🔧 Testing Enhanced Grace Fields instantiation...")

        # Create mock agents representing all 7 agent personalities
        mock_agents = [
            MockAgent("Nyra", "Lead Capture Specialist", "LeadCaptureAgent"),
            MockAgent("Solari", "Booking & Order Manager", "BookingAgent"),
            MockAgent("Ruvo", "Task Orchestrator", "TaskManagementAgent"),
            MockAgent("Liora", "Marketing Strategist", "MarketingCampaignAgent"),
            MockAgent("Sage", "Community Curator", "CommunityEngagementAgent"),
            MockAgent("Elan", "Content Choreographer", "ContentLifecycleAgent"),
            MockAgent("Zevi", "Audience Analyst", "AudienceSegmentationAgent"),
        ]

        # Create enhanced Grace Fields instance
        grace = EnhancedGraceFields(
            agents=mock_agents,
            message_bus=MockMessageBus(),
            notion_service=MockNotionService(),
            escalation_service=MockEscalationService(),
        )

        logger.info(
            f"✅ Enhanced Grace Fields instantiated with {len(grace.agents)} agents"
        )
        logger.info(f"📋 Available agents: {', '.join(grace.agents.keys())}")

        # Verify agent mapping
        assert len(grace.agents) == 7, f"Expected 7 agents, got {len(grace.agents)}"
        assert "Nyra" in grace.agents, "Nyra agent not found"
        assert "Solari" in grace.agents, "Solari agent not found"
        assert "Ruvo" in grace.agents, "Ruvo agent not found"

        return True

    except Exception as e:
        logger.error(f"❌ Enhanced Grace Fields instantiation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_multi_level_severity_processing():
    """Test the multi-level severity system (Level 1-4)."""

    try:
        from agents.grace_fields_enhanced import (
            CustomerServiceBusinessEntity, EnhancedGraceFields)

        logger.info("🔧 Testing multi-level severity processing...")

        # Create Grace Fields instance
        mock_agents = [
            MockAgent("Nyra", "Lead Specialist"),
            MockAgent("Solari", "Order Manager"),
            MockAgent("Ruvo", "Task Coordinator"),
        ]

        grace = EnhancedGraceFields(
            agents=mock_agents,
            message_bus=None,
            notion_service=None,
            escalation_service=None,
        )

        # Test scenarios for each severity level
        test_scenarios = [
            {
                "level": "Level 1",
                "description": "Simple booking change request",
                "business_entity": CustomerServiceBusinessEntity.WELLNESS_CENTER,
                "priority": "low",
                "expected_agents": 1,
            },
            {
                "level": "Level 2",
                "description": "Complex service package inquiry",
                "business_entity": CustomerServiceBusinessEntity.CONSULTANCY,
                "priority": "medium",
                "expected_agents": 2,
            },
            {
                "level": "Level 3",
                "description": "VIP client luxury service request",
                "business_entity": CustomerServiceBusinessEntity.ART_GALLERY,
                "priority": "high",
                "expected_agents": 3,
            },
            {
                "level": "Level 4",
                "description": "Legal compliance emergency",
                "business_entity": CustomerServiceBusinessEntity.CONSULTANCY,
                "priority": "urgent",
                "expected_escalation": True,
            },
        ]

        for scenario in test_scenarios:
            logger.info(
                f"🧪 Testing {scenario['level']}: {scenario['description'][:50]}..."
            )

            result = await grace.process_customer_service_request(
                customer_email=f"test.{scenario['level'].lower().replace(' ', '')}@example.com",
                description=scenario["description"],
                business_entity=scenario["business_entity"],
                priority=scenario["priority"],
            )

            logger.info(f"✅ {scenario['level']} processed: {result.get('status')}")

            # Verify appropriate handling based on severity
            if scenario.get("expected_escalation"):
                assert (
                    "ticket_id" in result
                ), f"{scenario['level']} should have escalation ticket"
            else:
                assert (
                    "assigned_agent" in result or "assigned_agents" in result
                ), f"{scenario['level']} should have assigned agents"

        logger.info("✅ All severity levels processed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Multi-level severity processing failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_business_entity_routing():
    """Test routing across all 7 business entities."""

    try:
        from agents.grace_fields_enhanced import (
            CustomerServiceBusinessEntity, EnhancedGraceFields)

        logger.info("🔧 Testing business entity routing...")

        # Create Grace Fields instance
        mock_agents = [
            MockAgent("Nyra", "Lead Specialist"),
            MockAgent("Solari", "Order Manager"),
            MockAgent("Liora", "Marketing Strategist"),
        ]

        grace = EnhancedGraceFields(
            agents=mock_agents,
            message_bus=None,
            notion_service=None,
            escalation_service=None,
        )

        # Test all 7 business entities
        business_entities = [
            CustomerServiceBusinessEntity.ART_GALLERY,
            CustomerServiceBusinessEntity.WELLNESS_CENTER,
            CustomerServiceBusinessEntity.CONSULTANCY,
            CustomerServiceBusinessEntity.INTERIOR_DESIGN,
            CustomerServiceBusinessEntity.LUXURY_RENOVATIONS,
            CustomerServiceBusinessEntity.EXECUTIVE_WELLNESS,
            CustomerServiceBusinessEntity.CORPORATE_WELLNESS,
        ]

        for entity in business_entities:
            logger.info(f"🧪 Testing routing for {entity.value}...")

            result = await grace.process_customer_service_request(
                customer_email=f"test.{entity.value}@example.com",
                description=f"Service inquiry for {entity.value}",
                business_entity=entity,
                priority="medium",
            )

            logger.info(
                f"✅ {entity.value} routed successfully: {result.get('status')}"
            )
            assert result.get("status") in [
                "delegated",
                "coordinating",
                "full_network_activated",
                "escalated",
            ], f"Invalid status for {entity.value}: {result.get('status')}"

        logger.info("✅ All business entities routed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Business entity routing failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_workflow_harmony_monitoring():
    """Test workflow harmony monitoring functionality."""

    try:
        from agents.grace_fields_enhanced import (
            CustomerServiceBusinessEntity, EnhancedGraceFields)

        logger.info("🔧 Testing workflow harmony monitoring...")

        # Create Grace Fields instance
        mock_agents = [MockAgent("Nyra", "Lead Specialist")]

        grace = EnhancedGraceFields(
            agents=mock_agents,
            message_bus=None,
            notion_service=None,
            escalation_service=None,
        )

        # Process a few requests to generate activity
        for i in range(3):
            await grace.process_customer_service_request(
                customer_email=f"harmony.test.{i}@example.com",
                description=f"Test request {i} for harmony monitoring",
                business_entity=CustomerServiceBusinessEntity.WELLNESS_CENTER,
                priority="medium",
            )

        # Test harmony monitoring
        harmony_status = await grace.monitor_workflow_harmony()

        logger.info(f"✅ Harmony monitoring completed")
        logger.info(f"📊 Overall status: {harmony_status.get('overall_status')}")
        logger.info(f"📈 Active requests: {harmony_status.get('active_requests', 0)}")
        logger.info(
            f"📋 Total processed: {harmony_status.get('total_requests_processed', 0)}"
        )

        # Verify harmony status structure
        required_fields = [
            "overall_status",
            "active_requests",
            "total_requests_processed",
        ]
        for field in required_fields:
            assert field in harmony_status, f"Missing field in harmony status: {field}"

        return True

    except Exception as e:
        logger.error(f"❌ Workflow harmony monitoring failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main comprehensive test function."""
    logger.info("🚀 Starting Grace Fields Comprehensive Test Suite")
    logger.info("=" * 70)

    tests = [
        (
            "Enhanced Grace Fields Instantiation",
            test_enhanced_grace_fields_instantiation,
        ),
        ("Multi-Level Severity Processing", test_multi_level_severity_processing),
        ("Business Entity Routing", test_business_entity_routing),
        ("Workflow Harmony Monitoring", test_workflow_harmony_monitoring),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n🔬 Running: {test_name}")
        logger.info("-" * 50)

        try:
            if await test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")

    logger.info(f"\n📊 Comprehensive Test Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All comprehensive tests passed!")
        logger.info("✨ Grace Fields Enhanced Customer Service system is ready!")
        return 0
    else:
        logger.error("❌ Some comprehensive tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
