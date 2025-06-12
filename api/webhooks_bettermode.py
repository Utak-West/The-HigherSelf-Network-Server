"""
BetterMode webhook handlers for The HigherSelf Network Server.
This module manages community integration with Notion as the central data hub.
"""

import json
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from loguru import logger
from pydantic import BaseModel

from agents.community_engagement_agent import CommunityEngagementAgent
from api.webhooks import WebhookResponse, get_community_agent, is_test_mode
from models.bettermode_models import BetterModeWebhookPayload, BetterModeWebhookType
from services.bettermode_service import BetterModeService, get_bettermode_service

# Initialize router
router = APIRouter(prefix="/webhooks/bettermode", tags=["webhooks", "community"])


async def verify_bettermode_webhook(
    request: Request, x_bettermode_signature: Optional[str] = Header(None)
) -> None:
    """
    Verify BetterMode webhook signature.

    Args:
        request: FastAPI request object
        x_bettermode_signature: Signature from BetterMode

    Raises:
        HTTPException: If signature verification fails
    """
    if is_test_mode():
        return

    if not x_bettermode_signature:
        raise HTTPException(status_code=401, detail="Missing BetterMode signature")

    # Get raw request body
    body = await request.body()

    # Verify signature
    bettermode_service = await get_bettermode_service()
    if not bettermode_service.verify_webhook_signature(x_bettermode_signature, body):
        raise HTTPException(status_code=401, detail="Invalid BetterMode signature")


@router.post(
    "/member",
    response_model=WebhookResponse,
    dependencies=[Depends(verify_bettermode_webhook)],
)
async def bettermode_member_webhook(
    request: Request,
    community_agent: CommunityEngagementAgent = Depends(get_community_agent),
):
    """
    Handle webhooks for member events from BetterMode.

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
                "Running in TEST_MODE: Simulating BetterMode member webhook processing"
            )
            return WebhookResponse(
                success=True,
                message="BetterMode member webhook simulated successfully (TEST MODE)",
                data={
                    "member_email": "test@example.com",
                    "membership_level": "Standard",
                },
            )

        # Parse request body
        body = await request.json()

        # Parse webhook payload
        webhook_payload = BetterModeWebhookPayload(**body)

        # Process based on event type
        if webhook_payload.event_type == BetterModeWebhookType.MEMBER_CREATED:
            # Extract member data
            member_data = {
                "name": webhook_payload.data.get("name", ""),
                "email": webhook_payload.data.get("email", ""),
                "membership_level": "Standard",  # Default mapping
                "profile_url": f"https://app.bettermode.com/members/{webhook_payload.data.get('id')}",
            }

            logger.info(
                f"Received BetterMode new member webhook for: {member_data['email']}"
            )

            # Process new member using the community engagement agent
            result = await community_agent.process_new_member(member_data)

            return WebhookResponse(
                success=True,
                message="Successfully processed BetterMode community member",
                data=result,
            )
        elif webhook_payload.event_type == BetterModeWebhookType.MEMBER_UPDATED:
            # Handle member update event
            logger.info(
                f"Received BetterMode member update webhook for: {webhook_payload.data.get('email')}"
            )

            # TODO: Implement member update logic

            return WebhookResponse(
                success=True,
                message="Successfully processed BetterMode member update",
                data=webhook_payload.data,
            )
        else:
            logger.warning(
                f"Unhandled BetterMode member event type: {webhook_payload.event_type}"
            )
            return WebhookResponse(
                success=False,
                message=f"Unhandled BetterMode member event type: {webhook_payload.event_type}",
                data={},
            )
    except Exception as e:
        logger.error(f"Error processing BetterMode member webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )


@router.post(
    "/activity",
    response_model=WebhookResponse,
    dependencies=[Depends(verify_bettermode_webhook)],
)
async def bettermode_activity_webhook(
    request: Request,
    community_agent: CommunityEngagementAgent = Depends(get_community_agent),
):
    """
    Handle webhooks for member activity from BetterMode.

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
                "Running in TEST_MODE: Simulating BetterMode activity webhook processing"
            )
            return WebhookResponse(
                success=True,
                message="BetterMode activity webhook simulated successfully (TEST MODE)",
                data={"member_email": "test@example.com", "activity_type": "post"},
            )

        # Parse request body
        body = await request.json()

        # Parse webhook payload
        webhook_payload = BetterModeWebhookPayload(**body)

        # Get BetterMode service
        bettermode_service = await get_bettermode_service()

        # Process based on event type
        if webhook_payload.event_type in [
            BetterModeWebhookType.POST_CREATED,
            BetterModeWebhookType.COMMENT_CREATED,
            BetterModeWebhookType.REACTION_CREATED,
        ]:
            # Get member information
            member_id = webhook_payload.data.get(
                "authorId"
            ) or webhook_payload.data.get("memberId")
            if not member_id:
                logger.warning(
                    f"No member ID found in BetterMode activity webhook: {webhook_payload.event_type}"
                )
                return WebhookResponse(
                    success=False,
                    message="No member ID found in BetterMode activity webhook",
                    data={},
                )

            member = await bettermode_service.get_member(member_id)
            if not member:
                logger.warning(
                    f"Member not found for ID {member_id} in BetterMode activity webhook"
                )
                return WebhookResponse(
                    success=False,
                    message=f"Member not found for ID {member_id}",
                    data={},
                )

            # Map activity type
            activity_type_map = {
                BetterModeWebhookType.POST_CREATED: "post",
                BetterModeWebhookType.COMMENT_CREATED: "comment",
                BetterModeWebhookType.REACTION_CREATED: "reaction",
            }

            activity_type = activity_type_map.get(webhook_payload.event_type, "unknown")

            # Extract activity data
            activity_data = {
                "member_email": member.email,
                "activity_type": activity_type,
                "activity_url": f"https://app.bettermode.com/post/{webhook_payload.data.get('id')}",
                "activity_content": webhook_payload.data.get("content", ""),
                "timestamp": webhook_payload.timestamp.isoformat(),
            }

            logger.info(
                f"Received BetterMode activity webhook for: {activity_data['member_email']}"
            )

            # Process activity using the community engagement agent
            result = await community_agent.track_member_activity(activity_data)

            return WebhookResponse(
                success=True,
                message=f"Successfully processed BetterMode {activity_data['activity_type']} activity",
                data=result,
            )
        else:
            logger.warning(
                f"Unhandled BetterMode activity event type: {webhook_payload.event_type}"
            )
            return WebhookResponse(
                success=False,
                message=f"Unhandled BetterMode activity event type: {webhook_payload.event_type}",
                data={},
            )
    except Exception as e:
        logger.error(f"Error processing BetterMode activity webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )


@router.post(
    "/event",
    response_model=WebhookResponse,
    dependencies=[Depends(verify_bettermode_webhook)],
)
async def bettermode_event_webhook(
    request: Request,
    community_agent: CommunityEngagementAgent = Depends(get_community_agent),
):
    """
    Handle webhooks for community events from BetterMode.

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
                "Running in TEST_MODE: Simulating BetterMode event webhook processing"
            )
            return WebhookResponse(
                success=True,
                message="BetterMode event webhook simulated successfully (TEST MODE)",
                data={"event_type": "test_event"},
            )

        # Parse request body
        body = await request.json()

        # Parse webhook payload
        webhook_payload = BetterModeWebhookPayload(**body)

        # Process based on event type
        if webhook_payload.event_type == BetterModeWebhookType.POST_CREATED:
            # Check if this is an event post
            if webhook_payload.data.get("spaceType") == "event":
                # Extract event data
                event_data = {
                    "title": webhook_payload.data.get("title", ""),
                    "description": webhook_payload.data.get("content", ""),
                    "start_time": webhook_payload.data.get("startTime"),
                    "end_time": webhook_payload.data.get("endTime"),
                    "location": webhook_payload.data.get("location", ""),
                    "url": f"https://app.bettermode.com/post/{webhook_payload.data.get('id')}",
                }

                logger.info(f"Received BetterMode event webhook: {event_data['title']}")

                # Schedule event notification
                result = await community_agent.schedule_community_event(event_data)

                return WebhookResponse(
                    success=True,
                    message="Successfully processed BetterMode event",
                    data=result,
                )

        logger.warning(f"Unhandled BetterMode event type: {webhook_payload.event_type}")
        return WebhookResponse(
            success=False,
            message=f"Unhandled BetterMode event type: {webhook_payload.event_type}",
            data={},
        )
    except Exception as e:
        logger.error(f"Error processing BetterMode event webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )
