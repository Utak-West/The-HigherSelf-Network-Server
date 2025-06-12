#!/usr/bin/env python3
"""
Basic test for Grace Fields Enhanced Customer Service functionality.
"""

import asyncio
import sys
from typing import Any, Dict

# Add the project root to the path
sys.path.insert(0, ".")

from loguru import logger


# Mock implementations for testing
class MockAgent:
    """Mock agent for testing."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.agent_type = f"{name}Agent"
        self.tone = "professional"


class MockNotionService:
    """Mock Notion service for testing."""

    pass


class MockEscalationService:
    """Mock escalation service for testing."""

    async def create_escalation_ticket(self, escalation_data: Dict[str, Any]) -> str:
        """Create a mock escalation ticket."""
        return f"ESC-{escalation_data.get('request_id', 'TEST')[:8]}"


class MockMessageBus:
    """Mock message bus for testing."""

    pass


async def test_basic_functionality():
    """Test basic Grace Fields functionality."""

    try:
        # Enable testing mode to disable external dependencies
        from config.testing_mode import enable_testing_mode

        enable_testing_mode(["redis", "notion", "openai", "anthropic"])

        # Import the enhanced Grace Fields
        from agents.grace_fields_enhanced import EnhancedGraceFields
        from models.customer_service_models import \
            CustomerServiceBusinessEntity

        logger.info("✅ Successfully imported EnhancedGraceFields")

        # Create mock agents
        mock_agents = [
            MockAgent("Nyra", "Lead Capture Specialist"),
            MockAgent("Solari", "Booking & Order Manager"),
            MockAgent("Ruvo", "Task Orchestrator"),
        ]

        # Create enhanced Grace Fields instance
        grace = EnhancedGraceFields(
            agents=mock_agents,
            message_bus=None,  # Use None instead of mock
            notion_service=None,  # Use None instead of mock
            escalation_service=None,  # Use None instead of mock
        )

        logger.info("✅ Successfully created EnhancedGraceFields instance")

        # Test a simple customer service request
        result = await grace.process_customer_service_request(
            customer_email="test@example.com",
            description="I need help with my booking",
            business_entity=CustomerServiceBusinessEntity.WELLNESS_CENTER,
            priority="medium",
        )

        logger.info("✅ Successfully processed customer service request")
        logger.info(f"📊 Result status: {result.get('status')}")
        logger.info(f"💬 Response preview: {result.get('message', '')[:100]}...")

        # Test workflow harmony monitoring
        harmony_status = await grace.monitor_workflow_harmony()
        logger.info("✅ Successfully monitored workflow harmony")
        logger.info(f"📈 Overall status: {harmony_status.get('overall_status')}")

        return True

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    logger.info("🧪 Starting Grace Fields Basic Test")
    logger.info("=" * 50)

    success = await test_basic_functionality()

    if success:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("❌ Tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
