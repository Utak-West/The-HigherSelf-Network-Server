#!/usr/bin/env python3
"""
Grace Fields Enhanced Customer Service Demo

This example demonstrates the enhanced Grace Fields customer service
orchestration capabilities for The HigherSelf Network Server.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Any, Dict

# Set testing mode before importing anything else
os.environ["TESTING_MODE"] = "true"

from loguru import logger


# Mock implementations for demo purposes
class MockAgent:
    """Mock agent for demonstration."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.agent_type = f"{name}Agent"
        self.tone = "professional"


class MockNotionService:
    """Mock Notion service for demonstration."""

    pass


class MockEscalationService:
    """Mock escalation service for demonstration."""

    async def create_escalation_ticket(self, escalation_data: Dict[str, Any]) -> str:
        """Create a mock escalation ticket."""
        return f"ESC-{escalation_data.get('request_id', 'DEMO')[:8]}"


class MockMessageBus:
    """Mock message bus for demonstration."""

    pass


async def demo_customer_service_scenarios():
    """Demonstrate various customer service scenarios."""

    # Import here to avoid circular imports
    from agents.grace_fields_enhanced import EnhancedGraceFields
    from models.customer_service_models import CustomerServiceBusinessEntity

    # Create mock agents
    mock_agents = [
        MockAgent("Nyra", "Lead Capture Specialist"),
        MockAgent("Solari", "Booking & Order Manager"),
        MockAgent("Ruvo", "Task Orchestrator"),
        MockAgent("Liora", "Marketing Strategist"),
        MockAgent("Sage", "Community Curator"),
        MockAgent("Elan", "Content Choreographer"),
        MockAgent("Zevi", "Audience Analyst"),
    ]

    # Create enhanced Grace Fields instance
    grace = EnhancedGraceFields(
        agents=mock_agents,
        message_bus=None,
        notion_service=None,
        escalation_service=None,
    )

    logger.info("🌟 Grace Fields Enhanced Customer Service Demo")
    logger.info("=" * 60)

    # Demo scenarios
    scenarios = [
        {
            "name": "Level 1 - Simple Booking Change",
            "customer_email": "sarah.wellness@example.com",
            "description": "I need to reschedule my massage appointment from Tuesday to Thursday",
            "business_entity": CustomerServiceBusinessEntity.WELLNESS_CENTER,
            "priority": "medium",
        },
        {
            "name": "Level 2 - Complex Service Package",
            "customer_email": "executive@company.com",
            "description": "I need a comprehensive package including strategic consulting, team wellness programs, and executive coaching",
            "business_entity": CustomerServiceBusinessEntity.CONSULTANCY,
            "priority": "high",
        },
        {
            "name": "Level 3 - VIP Client Service",
            "customer_email": "vip.client@luxury.com",
            "description": "As a VIP client, I need white-glove service for my luxury home renovation project",
            "business_entity": CustomerServiceBusinessEntity.ART_GALLERY,
            "priority": "high",
        },
        {
            "name": "Level 4 - Legal Compliance Issue",
            "customer_email": "legal@corporation.com",
            "description": "We need to discuss GDPR compliance requirements for our data handling practices",
            "business_entity": CustomerServiceBusinessEntity.CONSULTANCY,
            "priority": "urgent",
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        logger.info(f"\n📋 Scenario {i}: {scenario['name']}")
        logger.info("-" * 50)

        try:
            result = await grace.process_customer_service_request(
                customer_email=scenario["customer_email"],
                description=scenario["description"],
                business_entity=scenario["business_entity"].value,
                priority=scenario["priority"],
            )

            logger.info(f"✅ Status: {result['status']}")
            logger.info(f"📧 Customer: {scenario['customer_email']}")
            logger.info(f"🏢 Business: {scenario['business_entity'].value}")

            if "assigned_agent" in result:
                logger.info(f"👤 Assigned Agent: {result['assigned_agent']}")
            elif "assigned_agents" in result:
                logger.info(
                    f"👥 Assigned Agents: {', '.join(result['assigned_agents'])}"
                )

            if "workflow_id" in result:
                logger.info(f"🔄 Workflow ID: {result['workflow_id']}")

            if "ticket_id" in result:
                logger.info(f"🎫 Escalation Ticket: {result['ticket_id']}")

            logger.info(f"💬 Response: {result['message'][:100]}...")

        except Exception as e:
            logger.error(f"❌ Error in scenario {i}: {e}")

    # Demo workflow harmony monitoring
    logger.info(f"\n🔍 Workflow Harmony Monitoring")
    logger.info("-" * 50)

    try:
        harmony_status = await grace.monitor_workflow_harmony()
        logger.info(f"📊 Overall Status: {harmony_status['overall_status']}")
        logger.info(f"📈 Active Requests: {harmony_status['active_requests']}")
        logger.info(f"⚠️ Escalated Requests: {harmony_status['escalated_requests']}")
        logger.info(f"📋 Total Processed: {harmony_status['total_requests_processed']}")

        if harmony_status.get("recommendations"):
            logger.info("💡 Recommendations:")
            for rec in harmony_status["recommendations"]:
                logger.info(f"   • {rec}")

    except Exception as e:
        logger.error(f"❌ Error monitoring harmony: {e}")

    logger.info(f"\n🎉 Demo completed successfully!")
    logger.info("=" * 60)


async def demo_training_scenarios():
    """Demonstrate training scenario capabilities."""

    logger.info("\n🎓 Grace Fields Training Demo")
    logger.info("=" * 60)

    try:
        from agents.grace_fields_enhanced import EnhancedGraceFields
        from models.customer_service_models import (
            CustomerSentiment,
            CustomerServiceBusinessEntity,
            IssueCategory,
            SeverityLevel,
        )
        from training.grace_fields_customer_service_training import (
            CustomerServiceTrainingScenario,
            GraceFieldsCustomerServiceTrainer,
        )

        # Create mock enhanced Grace Fields
        mock_agents = [
            MockAgent("Nyra", "Lead Specialist"),
            MockAgent("Solari", "Order Manager"),
        ]
        grace = EnhancedGraceFields(
            agents=mock_agents,
            message_bus=None,
            notion_service=None,
            escalation_service=None,
        )

        # Create trainer
        trainer = GraceFieldsCustomerServiceTrainer(grace)

        # Create a sample training scenario
        scenario = CustomerServiceTrainingScenario(
            scenario_id="DEMO-001",
            name="Demo Billing Issue",
            description="Customer has a billing question",
            customer_email="demo@example.com",
            customer_name="Demo Customer",
            business_entity=CustomerServiceBusinessEntity.WELLNESS_CENTER,
            issue_description="I was charged twice for my wellness package",
            expected_category=IssueCategory.BILLING_ORDER,
            expected_severity=SeverityLevel.LEVEL_1,
            expected_agents=["Solari"],
            success_criteria=["Single agent delegation", "Professional response"],
            customer_sentiment=CustomerSentiment.CONCERNED,
        )

        # Run the training scenario
        logger.info(f"🧪 Running training scenario: {scenario.name}")
        result = await trainer.run_training_scenario(scenario)

        logger.info(f"✅ Scenario: {result['scenario_name']}")
        logger.info(f"⏱️ Processing Time: {result['processing_time_seconds']:.2f}s")

        evaluation = result.get("evaluation", {})
        logger.info(f"📊 Score: {evaluation.get('overall_score', 0)}/100")
        logger.info(f"✅ Passed: {evaluation.get('passed', False)}")

        if evaluation.get("feedback"):
            logger.info("📝 Feedback:")
            for feedback in evaluation["feedback"]:
                logger.info(f"   {feedback}")

    except ImportError as e:
        logger.warning(f"⚠️ Training demo requires additional modules: {e}")
    except Exception as e:
        logger.error(f"❌ Error in training demo: {e}")


async def main():
    """Main demo function."""
    logger.info("🚀 Starting Grace Fields Enhanced Customer Service Demo")

    try:
        await demo_customer_service_scenarios()
        await demo_training_scenarios()

    except KeyboardInterrupt:
        logger.info("\n👋 Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
