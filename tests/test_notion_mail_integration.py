#!/usr/bin/env python3
"""
Test suite for Notion Mail Integration Service

Comprehensive tests for email classification and workflow automation
following established testing patterns from the HigherSelf Network Server.
"""

import asyncio
import json
import os
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from services.notion_mail_integration import (
    EmailCategory,
    EmailClassificationResult,
    EmailContent,
    NotionMailIntegrationConfig,
    NotionMailIntegrationService,
)


@pytest.fixture
def test_config():
    """Test configuration for Notion Mail Integration."""
    return NotionMailIntegrationConfig(
        notion_api_token="test_notion_token",
        openai_api_key="test_openai_key",
        enable_auto_classification=True,
        enable_workflow_automation=True,
        confidence_threshold=0.7,
        testing_mode=True,
        am_consulting_response_time=4,
        the_7_space_response_time=24,
        higherself_core_response_time=12
    )


@pytest.fixture
def sample_emails():
    """Sample emails for testing different categories."""
    return {
        "am_consulting": EmailContent(
            sender_email="ceo@businesscorp.com",
            sender_name="John Smith",
            subject="Business Consultation Request - Strategic Planning",
            body="We are interested in your consulting services for our strategic planning initiative. Could we schedule a consultation to discuss our business transformation needs?",
            received_at=datetime.utcnow(),
            message_id="test_am_consulting_001",
            thread_id="thread_001"
        ),
        "the_7_space_gallery": EmailContent(
            sender_email="artist@creativestudio.com",
            sender_name="Jane Artist",
            subject="Exhibition Proposal - Contemporary Art Collection",
            body="I would like to propose an exhibition of my contemporary art collection at The 7 Space gallery. My work focuses on abstract expressionism and mixed media installations.",
            received_at=datetime.utcnow(),
            message_id="test_gallery_001",
            thread_id="thread_002"
        ),
        "the_7_space_wellness": EmailContent(
            sender_email="client@wellness.com",
            sender_name="Sarah Johnson",
            subject="Wellness Session Booking - Meditation and Healing",
            body="I'm interested in booking a wellness session at The 7 Space wellness center. I'm particularly interested in meditation and energy healing services.",
            received_at=datetime.utcnow(),
            message_id="test_wellness_001",
            thread_id="thread_003"
        ),
        "higherself_network": EmailContent(
            sender_email="member@join.higherselflife.com",
            sender_name="Community Member",
            subject="HigherSelf Network - Community Platform Access",
            body="I'm interested in joining the HigherSelf Network community platform. Could you provide information about membership and networking opportunities?",
            received_at=datetime.utcnow(),
            message_id="test_network_001",
            thread_id="thread_004"
        ),
        "technical": EmailContent(
            sender_email="admin@github.com",
            sender_name="GitHub Support",
            subject="Server Error Alert - API Timeout",
            body="Your server is experiencing API timeout errors. Please check your system logs and database connections for performance issues.",
            received_at=datetime.utcnow(),
            message_id="test_technical_001",
            thread_id="thread_005"
        ),
        "personal": EmailContent(
            sender_email="friend@gmail.com",
            sender_name="Best Friend",
            subject="Coffee Date This Weekend?",
            body="Hey! Want to catch up over coffee this weekend? It's been too long since we last talked. Let me know what works for you!",
            received_at=datetime.utcnow(),
            message_id="test_personal_001",
            thread_id="thread_006"
        )
    }


class TestNotionMailIntegrationService:
    """Test cases for NotionMailIntegrationService."""

    @pytest.mark.asyncio
    async def test_service_initialization(self, test_config):
        """Test service initialization with configuration."""
        service = NotionMailIntegrationService(test_config)
        
        assert service.config == test_config
        assert len(service.category_config) == 8
        assert len(service.classification_configs) == 8
        
        # Verify category priorities
        assert service.category_config[EmailCategory.AM_CONSULTING]["priority"] == 1
        assert service.category_config[EmailCategory.HIGHERSELF_NETWORK]["priority"] == 2
        assert service.category_config[EmailCategory.THE_7_SPACE_GALLERY]["priority"] == 3

    @pytest.mark.asyncio
    async def test_email_classification_am_consulting(self, test_config, sample_emails):
        """Test email classification for AM Consulting category."""
        service = NotionMailIntegrationService(test_config)
        
        result = await service.classify_email(sample_emails["am_consulting"])
        
        assert isinstance(result, EmailClassificationResult)
        assert result.category == EmailCategory.AM_CONSULTING
        assert result.confidence >= 0.7
        assert result.business_entity == "am_consulting"
        assert result.priority_score == 1

    @pytest.mark.asyncio
    async def test_email_classification_the_7_space_gallery(self, test_config, sample_emails):
        """Test email classification for The 7 Space Gallery category."""
        service = NotionMailIntegrationService(test_config)
        
        result = await service.classify_email(sample_emails["the_7_space_gallery"])
        
        assert isinstance(result, EmailClassificationResult)
        assert result.category == EmailCategory.THE_7_SPACE_GALLERY
        assert result.confidence >= 0.7
        assert result.business_entity == "the_7_space"
        assert result.priority_score == 3

    @pytest.mark.asyncio
    async def test_email_classification_the_7_space_wellness(self, test_config, sample_emails):
        """Test email classification for The 7 Space Wellness category."""
        service = NotionMailIntegrationService(test_config)
        
        result = await service.classify_email(sample_emails["the_7_space_wellness"])
        
        assert isinstance(result, EmailClassificationResult)
        assert result.category == EmailCategory.THE_7_SPACE_WELLNESS
        assert result.confidence >= 0.7
        assert result.business_entity == "the_7_space"
        assert result.priority_score == 4

    @pytest.mark.asyncio
    async def test_email_classification_higherself_network(self, test_config, sample_emails):
        """Test email classification for HigherSelf Network category."""
        service = NotionMailIntegrationService(test_config)
        
        result = await service.classify_email(sample_emails["higherself_network"])
        
        assert isinstance(result, EmailClassificationResult)
        assert result.category == EmailCategory.HIGHERSELF_NETWORK
        assert result.confidence >= 0.7
        assert result.business_entity == "higherself_core"
        assert result.priority_score == 2

    @pytest.mark.asyncio
    async def test_email_classification_technical(self, test_config, sample_emails):
        """Test email classification for Technical category."""
        service = NotionMailIntegrationService(test_config)
        
        result = await service.classify_email(sample_emails["technical"])
        
        assert isinstance(result, EmailClassificationResult)
        assert result.category == EmailCategory.TECHNICAL
        assert result.confidence >= 0.7
        assert result.business_entity is None
        assert result.priority_score == 5

    @pytest.mark.asyncio
    async def test_email_classification_personal(self, test_config, sample_emails):
        """Test email classification for Personal category."""
        service = NotionMailIntegrationService(test_config)
        
        result = await service.classify_email(sample_emails["personal"])
        
        assert isinstance(result, EmailClassificationResult)
        assert result.category == EmailCategory.PERSONAL
        assert result.confidence >= 0.7
        assert result.business_entity is None
        assert result.priority_score == 7

    @pytest.mark.asyncio
    async def test_business_entity_boundary_enforcement(self, test_config):
        """Test strict business entity boundary enforcement."""
        service = NotionMailIntegrationService(test_config)
        
        # Test email that could be confused between entities
        ambiguous_email = EmailContent(
            sender_email="info@higherself.com",
            sender_name="HigherSelf Info",
            subject="HigherSelf Community and Art Gallery Information",
            body="Information about HigherSelf community platform and art gallery services. We offer both networking and artistic experiences.",
            received_at=datetime.utcnow(),
            message_id="test_ambiguous_001"
        )
        
        result = await service.classify_email(ambiguous_email)
        
        # Should classify as one specific category, not mixed
        assert result.category in [
            EmailCategory.HIGHERSELF_NETWORK,
            EmailCategory.THE_7_SPACE_GALLERY,
            EmailCategory.HIGHERSELF
        ]
        
        # Business entity should match the category
        if result.category == EmailCategory.HIGHERSELF_NETWORK:
            assert result.business_entity == "higherself_core"
        elif result.category == EmailCategory.THE_7_SPACE_GALLERY:
            assert result.business_entity == "the_7_space"

    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self, test_config):
        """Test confidence threshold filtering for workflow triggers."""
        service = NotionMailIntegrationService(test_config)
        
        # Create email with low confidence classification
        low_confidence_email = EmailContent(
            sender_email="unclear@example.com",
            sender_name="Unclear Sender",
            subject="Vague Subject",
            body="This is a very vague email with no clear business context or keywords.",
            received_at=datetime.utcnow(),
            message_id="test_low_confidence_001"
        )
        
        result = await service.classify_email(low_confidence_email)
        
        # Should still return a classification but may have low confidence
        assert isinstance(result, EmailClassificationResult)
        
        # If confidence is below threshold, workflow should not be triggered
        if result.confidence < service.config.confidence_threshold:
            assert result.category in [EmailCategory.OTHER, EmailCategory.PERSONAL]

    @pytest.mark.asyncio
    @patch('services.notion_mail_integration.ContactWorkflowAutomation')
    async def test_workflow_automation_trigger(self, mock_workflow_automation, test_config, sample_emails):
        """Test workflow automation triggering for business entities."""
        # Setup mock
        mock_workflow_instance = AsyncMock()
        mock_workflow_instance.process_contact_workflow.return_value = {
            "success": True,
            "workflows_executed": ["am_consulting_lead_qualification"],
            "tasks_created": 2
        }
        mock_workflow_automation.return_value = mock_workflow_instance
        
        service = NotionMailIntegrationService(test_config)
        
        # Test workflow processing for AM Consulting email
        classification = EmailClassificationResult(
            category=EmailCategory.AM_CONSULTING,
            confidence=0.95,
            business_entity="am_consulting",
            reasoning="High confidence business consulting email",
            priority_score=1
        )
        
        result = await service.process_email_workflow(
            sample_emails["am_consulting"],
            classification
        )
        
        assert result["success"] is True
        assert "workflows_executed" in result
        mock_workflow_instance.process_contact_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_skipping_for_non_business_categories(self, test_config, sample_emails):
        """Test that workflow is skipped for non-business categories."""
        service = NotionMailIntegrationService(test_config)
        
        # Test with personal email classification
        classification = EmailClassificationResult(
            category=EmailCategory.PERSONAL,
            confidence=0.85,
            business_entity=None,
            reasoning="Personal communication",
            priority_score=7
        )
        
        result = await service.process_email_workflow(
            sample_emails["personal"],
            classification
        )
        
        assert result["success"] is True
        assert "No workflow required" in result["message"]

    @pytest.mark.asyncio
    async def test_classification_config_loading(self, test_config):
        """Test classification configuration loading from JSON files."""
        service = NotionMailIntegrationService(test_config)
        
        # Verify all categories have configurations loaded
        for category in EmailCategory:
            assert category in service.classification_configs
            config = service.classification_configs[category]
            
            # Verify required configuration fields
            assert "keywords" in config
            assert "domain_patterns" in config
            assert "confidence_threshold" in config
            assert isinstance(config["keywords"], list)
            assert isinstance(config["domain_patterns"], list)

    @pytest.mark.asyncio
    async def test_error_handling_classification_failure(self, test_config):
        """Test error handling when classification fails."""
        service = NotionMailIntegrationService(test_config)
        
        # Create email that might cause processing errors
        problematic_email = EmailContent(
            sender_email="",  # Empty sender
            sender_name=None,
            subject="",  # Empty subject
            body="",  # Empty body
            received_at=datetime.utcnow(),
            message_id="test_error_001"
        )
        
        result = await service.classify_email(problematic_email)
        
        # Should return fallback classification instead of raising exception
        assert isinstance(result, EmailClassificationResult)
        assert result.category == EmailCategory.OTHER
        assert result.confidence <= 0.5

    def test_category_configuration_completeness(self, test_config):
        """Test that all email categories have complete configuration."""
        service = NotionMailIntegrationService(test_config)
        
        # Verify all categories are configured
        for category in EmailCategory:
            assert category in service.category_config
            
            category_config = service.category_config[category]
            
            # Verify required fields
            assert "priority" in category_config
            assert "color" in category_config
            assert isinstance(category_config["priority"], int)
            assert 1 <= category_config["priority"] <= 8
            
            # Verify business entity mapping is correct
            if category in [EmailCategory.AM_CONSULTING]:
                assert category_config["entity"] == "am_consulting"
            elif category in [EmailCategory.THE_7_SPACE_GALLERY, EmailCategory.THE_7_SPACE_WELLNESS]:
                assert category_config["entity"] == "the_7_space"
            elif category in [EmailCategory.HIGHERSELF_NETWORK, EmailCategory.HIGHERSELF]:
                assert category_config["entity"] == "higherself_core"
            else:
                assert category_config["entity"] is None

    def test_response_time_sla_configuration(self, test_config):
        """Test response time SLA configuration for business entities."""
        service = NotionMailIntegrationService(test_config)
        
        # Verify SLA configuration matches business requirements
        assert service.config.am_consulting_response_time == 4  # 4 hours
        assert service.config.the_7_space_response_time == 24  # 24 hours
        assert service.config.higherself_core_response_time == 12  # 12 hours

    @pytest.mark.asyncio
    async def test_testing_mode_simulation(self, test_config, sample_emails):
        """Test that testing mode properly simulates classification."""
        # Ensure testing mode is enabled
        test_config.testing_mode = True
        service = NotionMailIntegrationService(test_config)
        
        result = await service.classify_email(sample_emails["am_consulting"])
        
        # Should return simulated result
        assert isinstance(result, EmailClassificationResult)
        assert "[TESTING MODE]" in result.reasoning
        
        # Should still follow business logic for simulation
        assert result.category != EmailCategory.OTHER or result.confidence > 0.5


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
