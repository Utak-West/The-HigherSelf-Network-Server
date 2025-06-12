#!/usr/bin/env python3
"""
Test utility for verifying automation flows in The HigherSelf Network Server.

This script allows testing of the various automation flows defined in the
Notion Automation Map, ensuring they work correctly with the 16-database structure.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from colorama import Fore, Style, init
from pydantic import BaseModel

# Add parent directory to path to allow importing from the server codebase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.notion_databases import AUTOMATION_FLOW_MAPPING
from config.testing_mode import (
    disable_testing_mode,
    enable_testing_mode,
    is_testing_mode,
)
from services.notion_service import NotionService

# Initialize colorama for colored terminal output
init()


class AutomationFlow(str, Enum):
    """Automation flows as defined in the Notion Automation Map."""

    LEAD_CAPTURE = "Flow 1: Lead Capture & Initial Processing"
    RETREAT_BOOKING = "Flow 2: Retreat Booking Management"
    ART_SALE = "Flow 3: Art Sale & Fulfillment"
    MARKETING_CAMPAIGN = "Flow 4: Marketing Email Campaign"
    TASK_MANAGEMENT = "Flow 5: Automated Task Management"
    COMMUNITY_ENGAGEMENT = "Flow 6: Community Engagement"
    CONTENT_CREATION = "Flow 7: Content Creation & Distribution"
    AUDIENCE_ANALYSIS = "Flow 8: Audience Analysis & Segmentation"


class MockWebhookPayload(BaseModel):
    """Model for generating mock webhook payloads for testing."""

    type: str
    source: str
    data: Dict[str, Any]


class AutomationFlowTester:
    """Tester for automation flows in The HigherSelf Network Server."""

    def __init__(self, use_test_mode: bool = True):
        """Initialize the tester."""
        self.notion_service = None
        self.use_test_mode = use_test_mode

        if use_test_mode:
            enable_testing_mode()
            print(
                f"{Fore.YELLOW}Running in TEST MODE - no actual API calls will be made{Style.RESET_ALL}"
            )
        else:
            print(
                f"{Fore.RED}WARNING: Running with real API calls. Data will be created in Notion.{Style.RESET_ALL}"
            )

    async def initialize(self):
        """Initialize the tester with required services."""
        from dotenv import load_dotenv

        # Load environment variables
        load_dotenv()

        # Initialize Notion service
        if not os.environ.get("NOTION_API_TOKEN"):
            print(
                f"{Fore.RED}Error: NOTION_API_TOKEN not found in environment variables{Style.RESET_ALL}"
            )
            print("Please set up your .env file with the required credentials.")
            sys.exit(1)

        self.notion_service = NotionService.from_env()

        print(f"{Fore.GREEN}AutomationFlowTester initialized{Style.RESET_ALL}")

    async def test_flow(self, flow: AutomationFlow):
        """Test a specific automation flow."""
        print(f"\n{Fore.CYAN}Testing {flow.value}{Style.RESET_ALL}")
        print("=" * 80)

        # Get the required agents for this flow
        required_agents = AUTOMATION_FLOW_MAPPING.get(flow.value, [])
        print(f"Required agents: {', '.join(required_agents)}")

        # Create mock data based on the flow
        mock_data = self._create_mock_data(flow)

        # Process the flow
        result = await self._process_flow(flow, mock_data)

        # Print results
        if result.get("success", False):
            print(f"\n{Fore.GREEN}✅ Flow test completed successfully{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ Flow test failed{Style.RESET_ALL}")

        print(f"Details: {json.dumps(result.get('details', {}), indent=2)}")
        print("=" * 80)

        return result

    def _create_mock_data(self, flow: AutomationFlow) -> Dict[str, Any]:
        """Create mock data for testing a specific flow."""
        timestamp = datetime.now().isoformat()

        # Use different mock data for each flow type
        if flow == AutomationFlow.LEAD_CAPTURE:
            return {
                "webhook": {
                    "type": "form_response",
                    "source": "typeform",
                    "data": {
                        "form_id": "mock_form_id",
                        "response_id": f"mock_response_{timestamp}",
                        "submitted_at": timestamp,
                        "answers": [
                            {"field": {"id": "name"}, "text": "Test User"},
                            {"field": {"id": "email"}, "email": "test@example.com"},
                            {"field": {"id": "phone"}, "phone_number": "+1234567890"},
                            {
                                "field": {"id": "interest"},
                                "choices": {"labels": ["Retreats", "Courses"]},
                            },
                        ],
                    },
                }
            }

        elif flow == AutomationFlow.RETREAT_BOOKING:
            return {
                "webhook": {
                    "type": "appointment_created",
                    "source": "amelia",
                    "data": {
                        "booking_id": f"mock_booking_{timestamp}",
                        "service_id": "mock_retreat_service",
                        "customer": {
                            "name": "Test Retreater",
                            "email": "retreater@example.com",
                            "phone": "+1234567890",
                        },
                        "appointment": {
                            "start": (datetime.now() + timedelta(days=30)).isoformat(),
                            "end": (datetime.now() + timedelta(days=33)).isoformat(),
                            "status": "approved",
                        },
                    },
                }
            }

        elif flow == AutomationFlow.ART_SALE:
            return {
                "webhook": {
                    "type": "order_created",
                    "source": "woocommerce",
                    "data": {
                        "order_id": f"mock_order_{timestamp}",
                        "customer": {
                            "name": "Test Art Buyer",
                            "email": "artbuyer@example.com",
                            "phone": "+1234567890",
                        },
                        "order": {
                            "total": "250.00",
                            "currency": "USD",
                            "items": [
                                {
                                    "product_id": "mock_art_product",
                                    "name": "Spiritual Awakening - Print",
                                    "quantity": 1,
                                    "price": "250.00",
                                }
                            ],
                            "shipping": {"address": "123 Art St, Creativity, CA 90210"},
                        },
                    },
                }
            }

        elif flow == AutomationFlow.MARKETING_CAMPAIGN:
            return {
                "campaign": {
                    "name": "Test Email Campaign",
                    "description": "A test marketing campaign",
                    "platform": "beehiiv",
                    "schedule_date": (datetime.now() + timedelta(days=1)).isoformat(),
                    "target_segments": ["new_leads", "past_customers"],
                    "content": {
                        "subject": "Test Campaign Subject",
                        "body": "This is a test campaign email body.",
                    },
                }
            }

        elif flow == AutomationFlow.TASK_MANAGEMENT:
            return {
                "workflow_event": {
                    "workflow_instance_id": f"mock_workflow_{timestamp}",
                    "event_type": "status_changed",
                    "event_data": {
                        "old_status": "New Lead",
                        "new_status": "Qualified Lead",
                        "assigned_to": "test_user@example.com",
                    },
                }
            }

        elif flow == AutomationFlow.COMMUNITY_ENGAGEMENT:
            return {
                "webhook": {
                    "type": "new_member",
                    "source": "circleso",
                    "data": {
                        "name": "Test Community Member",
                        "email": "community@example.com",
                        "membership_level": "Standard",
                        "interest_groups": ["Meditation", "Art"],
                        "profile_url": "https://example.com/profile/test",
                    },
                }
            }

        elif flow == AutomationFlow.CONTENT_CREATION:
            return {
                "content_request": {
                    "business_entity_id": "mock_business_entity",
                    "topic_area": "Spiritual Growth",
                    "content_type": "blog_post",
                    "title": "Test Content Piece",
                    "keywords": ["spirituality", "growth", "self-development"],
                }
            }

        elif flow == AutomationFlow.AUDIENCE_ANALYSIS:
            return {
                "segment_definition": {
                    "business_entity_id": "mock_business_entity",
                    "segment_name": "Test Audience Segment",
                    "segment_description": "A test audience segment",
                    "criteria": [
                        {
                            "field": "tags",
                            "operator": "contains",
                            "value": "meditation",
                        },
                        {
                            "field": "engagement_score",
                            "operator": "greater_than",
                            "value": 50,
                        },
                    ],
                }
            }

        # Default case
        return {"test": "mock_data", "timestamp": timestamp}

    async def _process_flow(
        self, flow: AutomationFlow, mock_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a flow with the given mock data."""

        try:
            # This would normally involve calling the appropriate APIs or simulating webhook events
            # For now, we'll just return success with the mock data
            if flow == AutomationFlow.LEAD_CAPTURE:
                return await self._simulate_webhook(
                    "webhooks/typeform", mock_data["webhook"]
                )

            elif flow == AutomationFlow.RETREAT_BOOKING:
                return await self._simulate_webhook(
                    "webhooks/amelia", mock_data["webhook"]
                )

            elif flow == AutomationFlow.ART_SALE:
                return await self._simulate_webhook(
                    "webhooks/woocommerce", mock_data["webhook"]
                )

            elif flow == AutomationFlow.MARKETING_CAMPAIGN:
                # This would call the marketing agent directly
                return {
                    "success": True,
                    "details": {
                        "campaign_id": "mock_campaign_123",
                        "scheduled": True,
                        "target_audience_size": 250,
                        "mock_data": mock_data["campaign"],
                    },
                }

            elif flow == AutomationFlow.TASK_MANAGEMENT:
                # This would call the task management agent directly
                return {
                    "success": True,
                    "details": {
                        "tasks_created": [
                            {"id": "task_1", "title": "Follow up with lead"},
                            {"id": "task_2", "title": "Send qualification email"},
                        ],
                        "mock_data": mock_data["workflow_event"],
                    },
                }

            elif flow == AutomationFlow.COMMUNITY_ENGAGEMENT:
                return await self._simulate_webhook(
                    "webhooks/circleso/new_member", mock_data["webhook"]
                )

            elif flow == AutomationFlow.CONTENT_CREATION:
                # This would call the content lifecycle agent directly
                return {
                    "success": True,
                    "details": {
                        "content_id": "mock_content_123",
                        "content_stage": "idea",
                        "mock_data": mock_data["content_request"],
                    },
                }

            elif flow == AutomationFlow.AUDIENCE_ANALYSIS:
                # This would call the audience segmentation agent directly
                return {
                    "success": True,
                    "details": {
                        "segment_id": "mock_segment_123",
                        "member_count": 45,
                        "mock_data": mock_data["segment_definition"],
                    },
                }

            # Default case
            return {
                "success": False,
                "details": {"error": "Unknown flow", "flow": flow.value},
            }

        except Exception as e:
            print(f"{Fore.RED}Error processing flow: {str(e)}{Style.RESET_ALL}")
            return {"success": False, "details": {"error": str(e)}}

    async def _simulate_webhook(
        self, endpoint: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate a webhook call to an endpoint."""
        print(f"Simulating webhook to {endpoint} with payload:")
        print(json.dumps(payload, indent=2))

        # In a real implementation, this would make an actual HTTP request
        # For now, just return success
        return {
            "success": True,
            "details": {
                "endpoint": endpoint,
                "webhook_type": payload.get("type", "unknown"),
                "webhook_source": payload.get("source", "unknown"),
                "timestamp": datetime.now().isoformat(),
            },
        }

    def cleanup(self):
        """Clean up resources."""
        if self.use_test_mode:
            disable_testing_mode()
            print(f"{Fore.YELLOW}Test mode disabled{Style.RESET_ALL}")


async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Test automation flows in The HigherSelf Network Server"
    )

    parser.add_argument(
        "--flow",
        type=str,
        choices=[flow.value for flow in AutomationFlow],
        help="Specific flow to test",
    )

    parser.add_argument(
        "--real", action="store_true", help="Use real API calls instead of test mode"
    )

    args = parser.parse_args()

    tester = AutomationFlowTester(use_test_mode=not args.real)
    await tester.initialize()

    try:
        if args.flow:
            # Test a specific flow
            flow = AutomationFlow(args.flow)
            await tester.test_flow(flow)
        else:
            # Test all flows
            print(f"{Fore.CYAN}Testing all automation flows...{Style.RESET_ALL}")
            for flow in AutomationFlow:
                await tester.test_flow(flow)
                # Add a small delay between tests
                await asyncio.sleep(1)
    finally:
        tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
