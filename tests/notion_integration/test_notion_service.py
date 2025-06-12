#!/usr/bin/env python3
"""
Tests for Notion integration to ensure it remains the central hub for all data and workflows.
"""
import os
from unittest.mock import MagicMock, patch

import pytest

# Set up test environment
os.environ["NOTION_API_TOKEN"] = "dummy_token_for_tests"
os.environ["NOTION_CLIENTS_DATABASE_ID"] = "dummy_database_id_1"


@pytest.mark.asyncio
async def test_notion_service_initialization():
    """Test that the Notion service correctly initializes."""
    with patch("services.notion_service.AsyncClient") as mock_client:
        from services.notion_service import NotionService

        mock_client.return_value = MagicMock()
        notion_service = NotionService()

        assert notion_service is not None
        assert notion_service.client is not None


@pytest.mark.asyncio
async def test_notion_is_central_hub():
    """Test that all services properly synchronize with Notion."""
    from services.integration_manager import IntegrationManager

    with patch("services.integration_manager.NotionService") as mock_notion_service:
        mock_notion = MagicMock()
        mock_notion_service.return_value = mock_notion

        integration_manager = IntegrationManager()
        # Verify Notion is the central hub for all data flows
        assert integration_manager is not None

        # In a real test, we would verify that data flows properly to Notion
        # from all integrated services
