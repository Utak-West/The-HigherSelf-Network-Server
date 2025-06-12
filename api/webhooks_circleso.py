"""
Circle.so webhook handlers for The HigherSelf Network Server.
This module manages community integration with Notion as the central data hub.
"""

import json
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request

# import logging # Replaced by loguru
from loguru import logger  # Added for direct loguru usage
from pydantic import BaseModel

from agents.community_engagement_agent import CommunityEngagementAgent
from api.webhooks import WebhookResponse, get_community_agent, is_test_mode

# logger = logging.getLogger(__name__) # Replaced by global loguru logger

# Initialize router
router = APIRouter(prefix="/webhooks/circleso", tags=["webhooks", "community"])


@router.post("/new_member", response_model=WebhookResponse)
async def circleso_new_member_webhook(
    request: Request,
    community_agent: CommunityEngagementAgent = Depends(get_community_agent),
):
    """
    Handle webhooks for new member registration from Circle.so.

    Args:
        request: FastAPI request object
        community_agent: Community engagement agent

    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Check if in test mode
        if is_test_mode():
            logger.info(
                "Running in TEST_MODE: Simulating Circle.so new member webhook processing"
            )
            return WebhookResponse(
                success=True,
                message="Circle.so new member webhook simulated successfully (TEST MODE)",
                data={
                    "member_email": "test@example.com",
                    "membership_level": "Standard",
                },
            )

        # Parse request body
        body = await request.json()

        # Extract member data
        member_data = {
            "name": body.get("name", ""),
            "email": body.get("email", ""),
            "membership_level": body.get("membership_level", "Standard"),
            "interest_groups": body.get("interest_groups", []),
            "profile_url": body.get("profile_url", ""),
        }

        logger.info(
            f"Received Circle.so new member webhook for: {member_data['email']}"
        )

        # Process new member using the community engagement agent
        result = await community_agent.process_new_member(member_data)

        return WebhookResponse(
            success=True,
            message="Successfully processed new Circle.so community member",
            data=result,
        )
    except Exception as e:
        logger.error(f"Error processing Circle.so new member webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )


@router.post("/member_activity", response_model=WebhookResponse)
async def circleso_activity_webhook(
    request: Request,
    community_agent: CommunityEngagementAgent = Depends(get_community_agent),
):
    """
    Handle webhooks for member activity from Circle.so.

    Args:
        request: FastAPI request object
        community_agent: Community engagement agent

    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Check if in test mode
        if is_test_mode():
            logger.info(
                "Running in TEST_MODE: Simulating Circle.so activity webhook processing"
            )
            return WebhookResponse(
                success=True,
                message="Circle.so activity webhook simulated successfully (TEST MODE)",
                data={"member_email": "test@example.com", "activity_type": "post"},
            )

        # Parse request body
        body = await request.json()

        # Extract activity data
        activity_data = {
            "member_email": body.get("member_email", ""),
            "activity_type": body.get("activity_type", ""),
            "activity_url": body.get("activity_url", ""),
            "activity_content": body.get("activity_content", ""),
            "timestamp": body.get("timestamp", ""),
        }

        logger.info(
            f"Received Circle.so activity webhook for: {activity_data['member_email']}"
        )

        # Process activity using the community engagement agent
        result = await community_agent.track_member_activity(activity_data)

        return WebhookResponse(
            success=True,
            message=f"Successfully processed Circle.so {activity_data['activity_type']} activity",
            data=result,
        )
    except Exception as e:
        logger.error(f"Error processing Circle.so activity webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )


@router.post("/event", response_model=WebhookResponse)
async def circleso_event_webhook(
    request: Request,
    community_agent: CommunityEngagementAgent = Depends(get_community_agent),
):
    """
    Handle webhooks for community events from Circle.so.

    Args:
        request: FastAPI request object
        community_agent: Community engagement agent

    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Check if in test mode
        if is_test_mode():
            logger.info(
                "Running in TEST_MODE: Simulating Circle.so event webhook processing"
            )
            return WebhookResponse(
                success=True,
                message="Circle.so event webhook simulated successfully (TEST MODE)",
                data={"event_type": "test_event"},
            )

        # Parse request body
        body = await request.json()

        # Extract event data
        event_type = body.get("event_type", "unknown")
        event_data = body.get("event_data", {})

        logger.info(f"Received Circle.so event webhook: {event_type}")

        # Process event based on type
        if event_type == "new_event_created":
            # Schedule event notification
            result = await community_agent.schedule_community_event(event_data)
        else:
            logger.warning(f"Unknown Circle.so event type: {event_type}")
            result = {"event_type": event_type, "status": "unprocessed"}

        return WebhookResponse(
            success=True,
            message=f"Successfully received Circle.so event webhook for {event_type}",
            data=result,
        )
    except Exception as e:
        logger.error(f"Error processing Circle.so event webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )
