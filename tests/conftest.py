"""
Global test configuration for The HigherSelf Network Server.
Ensures all external API calls are mocked and no live webhooks are triggered during tests.
Maintains Notion as the central hub in the architecture while preventing actual API calls.
"""

import asyncio
import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_test_environment():
    """
    Set up the test environment with mock credentials and test mode flags.
    This prevents any live API calls during tests.
    """
    # Override environment variables with test values
    os.environ["TEST_MODE"] = "True"
    os.environ["DISABLE_WEBHOOKS"] = "True"
    os.environ["NOTION_API_TOKEN"] = "test_notion_token"
    os.environ["TYPEFORM_WEBHOOK_SECRET"] = "test_typeform_secret"
    os.environ["WOOCOMMERCE_API_KEY"] = "test_woocommerce_key"
    os.environ["WOOCOMMERCE_API_SECRET"] = "test_woocommerce_secret"
    os.environ["ACUITY_USER_ID"] = "test_acuity_user"
    os.environ["ACUITY_API_KEY"] = "test_acuity_key"
    os.environ["USERFEEDBACK_API_KEY"] = "test_userfeedback_key"
    os.environ["TUTOR_LM_API_KEY"] = "test_tutor_lm_key"
    os.environ["AMELIA_API_KEY"] = "test_amelia_key"
    os.environ["SNOVIO_API_KEY"] = "test_snovio_key"

    # Yield to allow tests to run
    yield


@pytest.fixture(autouse=True)
def no_http_requests():
    """
    Patch all HTTP libraries to prevent any outgoing requests during tests.
    This ensures no real API calls or webhooks are triggered.
    """
    # Create mock for httpx async client
    httpx_mock = MagicMock()
    httpx_mock.get = MagicMock(
        return_value=MagicMock(
            status_code=200, json=MagicMock(return_value={"success": True})
        )
    )
    httpx_mock.post = MagicMock(
        return_value=MagicMock(
            status_code=200, json=MagicMock(return_value={"success": True})
        )
    )

    # Create mock for aiohttp client session
    aiohttp_mock = MagicMock()
    aiohttp_mock.__aenter__ = MagicMock(
        return_value=MagicMock(
            get=MagicMock(
                return_value=MagicMock(
                    __aenter__=MagicMock(
                        return_value=MagicMock(
                            status=200, json=MagicMock(return_value={"success": True})
                        )
                    ),
                    __aexit__=MagicMock(return_value=None),
                )
            ),
            post=MagicMock(
                return_value=MagicMock(
                    __aenter__=MagicMock(
                        return_value=MagicMock(
                            status=200, json=MagicMock(return_value={"success": True})
                        )
                    ),
                    __aexit__=MagicMock(return_value=None),
                )
            ),
        )
    )
    aiohttp_mock.__aexit__ = MagicMock(return_value=None)

    # Create mock for requests
    requests_mock = MagicMock()
    requests_mock.get = MagicMock(
        return_value=MagicMock(
            status_code=200, json=MagicMock(return_value={"success": True})
        )
    )
    requests_mock.post = MagicMock(
        return_value=MagicMock(
            status_code=200, json=MagicMock(return_value={"success": True})
        )
    )

    # Apply patches
    with patch("httpx.AsyncClient", return_value=httpx_mock), patch(
        "aiohttp.ClientSession", return_value=aiohttp_mock
    ), patch("requests.get", requests_mock.get), patch(
        "requests.post", requests_mock.post
    ):
        yield


@pytest.fixture
def mock_notion_service():
    """
    Mock the Notion service to prevent real API calls while maintaining
    Notion as the central hub in the architecture.
    """
    with patch("services.notion_service.NotionService") as mock_service:
        # Configure mock to return appropriate values
        service_instance = MagicMock()
        service_instance.add_typeform_response = MagicMock(
            return_value=asyncio.Future()
        )
        service_instance.add_typeform_response.return_value.set_result(
            "notion_page_id_123"
        )

        service_instance.sync_woocommerce_data = MagicMock(
            return_value=asyncio.Future()
        )
        service_instance.sync_woocommerce_data.return_value.set_result(
            "notion_page_id_456"
        )

        service_instance.sync_acuity_appointment = MagicMock(
            return_value=asyncio.Future()
        )
        service_instance.sync_acuity_appointment.return_value.set_result(
            "notion_page_id_789"
        )

        service_instance.add_user_feedback = MagicMock(return_value=asyncio.Future())
        service_instance.add_user_feedback.return_value.set_result("notion_page_id_101")

        # Set the mock instance as the return value
        mock_service.return_value = service_instance

        yield service_instance


@pytest.fixture
def mock_integration_manager():
    """
    Mock the Integration Manager to prevent real service initializations
    while maintaining the core principle of Notion as central hub.
    """
    with patch("services.integration_manager.IntegrationManager") as mock_manager:
        # Configure mock to return appropriate values
        manager_instance = MagicMock()

        # Mock get_service to return mocked service instances
        def mock_get_service(service_name):
            mock_service = MagicMock()

            # Configure verification methods to prevent real checks
            mock_service.verify_webhook_signature = MagicMock(return_value=True)

            # Set up processing methods to return test data
            mock_service.process_webhook = MagicMock(return_value=asyncio.Future())
            mock_service.process_webhook.return_value.set_result(
                {"success": True, "id": "test_id"}
            )

            mock_service.process_form_response = MagicMock(
                return_value=asyncio.Future()
            )
            mock_service.process_form_response.return_value.set_result(
                {"success": True, "form_id": "test_form"}
            )

            mock_service.process_feedback = MagicMock(return_value=asyncio.Future())
            mock_service.process_feedback.return_value.set_result(
                {"success": True, "feedback_id": "test_feedback"}
            )

            # Add special methods for certain services
            if service_name == "acuity":
                mock_service.supports_metadata_update = MagicMock(return_value=True)
                mock_service.update_appointment_metadata = MagicMock(
                    return_value=asyncio.Future()
                )
                mock_service.update_appointment_metadata.return_value.set_result(True)

            if service_name == "userfeedback":
                mock_service.update_feedback_source = MagicMock(
                    return_value=asyncio.Future()
                )
                mock_service.update_feedback_source.return_value.set_result(True)

            return mock_service

        manager_instance.get_service = mock_get_service

        # Mock sync_to_notion to return fake page IDs
        manager_instance.sync_to_notion = MagicMock(return_value=asyncio.Future())
        manager_instance.sync_to_notion.return_value.set_result("notion_page_id_test")

        # Set the mock instance as the return value
        mock_manager.return_value = manager_instance

        yield manager_instance
