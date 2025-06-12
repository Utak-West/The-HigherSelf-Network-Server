#!/usr/bin/env python3
"""
Simple test for Grace Fields Enhanced Customer Service functionality.
Tests only the core models and classes without external dependencies.
"""

import os
import sys
import uuid
from datetime import datetime
from enum import Enum

# Set testing mode before importing anything else
os.environ["TESTING_MODE"] = "true"

# Add the project root to the path
sys.path.insert(0, ".")

from loguru import logger


def test_customer_service_models():
    """Test the customer service models can be imported and instantiated."""

    try:
        # Test importing the customer service models
        from models.customer_service_models import (
            CustomerSentiment, CustomerServiceBusinessEntity,
            CustomerServiceRequest, IssueCategory, SeverityLevel,
            WorkflowStatus)

        logger.info("✅ Successfully imported customer service models")

        # Test creating a customer service request
        request = CustomerServiceRequest(
            customer_email="test@example.com",
            business_entity=CustomerServiceBusinessEntity.WELLNESS_CENTER,
            issue_category=IssueCategory.BILLING_ORDER,
            severity_level=SeverityLevel.LEVEL_1,
            description="Test booking issue",
            priority="medium",
        )

        logger.info("✅ Successfully created CustomerServiceRequest")
        logger.info(f"📧 Request ID: {request.request_id}")
        logger.info(f"🏢 Business Entity: {request.business_entity.value}")
        logger.info(f"📋 Issue Category: {request.issue_category.value}")

        # Test updating request status
        request.update_status(WorkflowStatus.IN_PROGRESS, "Processing request")
        logger.info("✅ Successfully updated request status")

        return True

    except Exception as e:
        logger.error(f"❌ Model test error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_grace_fields_classes():
    """Test that Grace Fields classes can be imported."""

    try:
        # Test importing the enhanced Grace Fields classes
        from agents.grace_fields_enhanced import \
            CustomerServiceBusinessEntity as GraceBusinessEntity
        from agents.grace_fields_enhanced import \
            CustomerServiceRequest as GraceRequest
        from agents.grace_fields_enhanced import \
            IssueCategory as GraceIssueCategory
        from agents.grace_fields_enhanced import \
            SeverityLevel as GraceSeverityLevel

        logger.info("✅ Successfully imported Grace Fields enhanced classes")

        # Test creating instances
        request = GraceRequest(
            customer_email="grace.test@example.com",
            business_entity=GraceBusinessEntity.ART_GALLERY,
            issue_category=GraceIssueCategory.VIP_SERVICE,
            severity_level=GraceSeverityLevel.LEVEL_2,
            description="VIP client needs assistance",
            priority="high",
        )

        logger.info("✅ Successfully created Grace Fields request")
        logger.info(f"📧 Request: {request.customer_email}")
        logger.info(f"🎨 Business: {request.business_entity.value}")

        return True

    except Exception as e:
        logger.error(f"❌ Grace Fields test error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_enum_values():
    """Test that all enum values are properly defined."""

    try:
        from models.customer_service_models import (
            CustomerSentiment, CustomerServiceBusinessEntity, IssueCategory,
            SeverityLevel, WorkflowStatus)

        # Test business entities
        business_entities = list(CustomerServiceBusinessEntity)
        logger.info(f"✅ Business entities: {len(business_entities)} defined")

        # Test issue categories
        issue_categories = list(IssueCategory)
        logger.info(f"✅ Issue categories: {len(issue_categories)} defined")

        # Test severity levels
        severity_levels = list(SeverityLevel)
        logger.info(f"✅ Severity levels: {len(severity_levels)} defined")

        # Test customer sentiments
        sentiments = list(CustomerSentiment)
        logger.info(f"✅ Customer sentiments: {len(sentiments)} defined")

        # Test workflow statuses
        statuses = list(WorkflowStatus)
        logger.info(f"✅ Workflow statuses: {len(statuses)} defined")

        return True

    except Exception as e:
        logger.error(f"❌ Enum test error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test function."""
    logger.info("🧪 Starting Grace Fields Simple Test")
    logger.info("=" * 50)

    tests = [
        ("Customer Service Models", test_customer_service_models),
        ("Grace Fields Classes", test_grace_fields_classes),
        ("Enum Values", test_enum_values),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n🔬 Running: {test_name}")
        logger.info("-" * 30)

        if test_func():
            logger.info(f"✅ {test_name} PASSED")
            passed += 1
        else:
            logger.error(f"❌ {test_name} FAILED")

    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
