"""Authentication utilities for The HigherSelf Network Server.

This module provides authentication utilities for securing API endpoints through
various methods including webhook signature verification and API key validation.
It handles authentication for staff users and webhook integrations with
external services.
"""

import hashlib
import hmac
import os
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, Request

# Setup logger with fallback to standard logging if loguru is not available
try:
    from loguru import logger
except ImportError:
    import logging

    # Create a compatible logger that mimics loguru's interface
    class CompatLogger:
        def __init__(self, name):
            self._logger = logging.getLogger(name)

        def info(self, message):
            self._logger.info(message)

        def warning(self, message):
            self._logger.warning(message)

        def error(self, message):
            self._logger.error(message)

        def debug(self, message):
            self._logger.debug(message)

    logger = CompatLogger(__name__)

from models.softr_models import StaffUser
from services.softr_service import SoftrService

# Secure webhook verification using HMAC
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
if not WEBHOOK_SECRET and os.getenv("ENVIRONMENT", "development") == "production":
    logger.warning(
        "WEBHOOK_SECRET environment variable not set in production environment"
    )

# Staff API key for authentication
STAFF_API_KEY = os.getenv("STAFF_API_KEY", "")
if not STAFF_API_KEY and os.getenv("ENVIRONMENT", "development") == "production":
    logger.warning(
        "STAFF_API_KEY environment variable not set in production environment"
    )


async def verify_webhook_signature(request: Request) -> bool:
    """Verify that the webhook request is authentic by checking its signature.

    Uses HMAC with SHA-256 to verify the authenticity of incoming webhook requests
    by comparing the signature in the request headers with the calculated signature
    using the shared secret.

    Args:
        request: The FastAPI request object containing the webhook payload and headers

    Returns:
        bool: True if the signature is valid

    Raises:
        HTTPException: If signature is missing or invalid (401 Unauthorized)
    """
    if not WEBHOOK_SECRET:
        # In development, we may not have a secret set
        # In production, this should never happen
        logger.warning("No webhook secret set - webhook verification disabled")
        return True

    # Get the signature from the headers
    signature_header = request.headers.get("x-signature")
    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing signature header")

    # Get the request body for verification
    body = await request.body()

    # Calculate expected signature
    hmac_obj = hmac.new(WEBHOOK_SECRET.encode("utf-8"), body, hashlib.sha256)
    expected_signature = hmac_obj.hexdigest()

    # Check if signatures match
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=401, detail="Invalid signature")

    return True


async def verify_staff_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """Verify that the staff API key is valid.

    Validates the API key provided in the request header against the configured
    staff API key to ensure the request is coming from an authorized source.

    Args:
        x_api_key: The API key from the request header (X-Api-Key)

    Returns:
        bool: True if the API key is valid

    Raises:
        HTTPException: If API key is missing or invalid (401 Unauthorized)
    """
    if not STAFF_API_KEY:
        # In development, we may not have a key set
        # In production, this should never happen
        logger.warning("No staff API key set - API key verification disabled")
        return True

    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    if x_api_key != STAFF_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return True


async def get_staff_user(
    x_staff_id: Optional[str] = Header(None),
    api_key_valid: bool = Depends(verify_staff_api_key),
) -> StaffUser:
    """Get the staff user from the request headers.

    Retrieves staff user information based on the staff ID provided in the request
    header. This endpoint requires a valid API key, which is validated through the
    verify_staff_api_key dependency.

    Args:
        x_staff_id: The staff ID from the request header (X-Staff-Id)
        api_key_valid: Whether the API key is valid (validated by verify_staff_api_key)

    Returns:
        StaffUser: Staff user object with user details

    Raises:
        HTTPException: If staff ID is missing (401 Unauthorized)
    """
    if not x_staff_id:
        raise HTTPException(status_code=401, detail="Missing staff ID")

    # In a real implementation, this would look up the staff user in a database
    # For now, we'll return a mock user
    # Validate the staff ID format before creating the user
    if not x_staff_id or not x_staff_id.strip():
        raise HTTPException(status_code=401, detail="Invalid staff ID format")

    # Create a mock user with the provided ID
    staff_user = StaffUser(
        id=x_staff_id.strip(),
        name="Staff User",
        email=f"{x_staff_id.strip()}@thehigherself.network",
        roles=["staff"],
    )

    logger.debug(f"Staff user authenticated: {staff_user.id}")
    return staff_user


async def get_current_user(
    x_staff_id: Optional[str] = Header(None),
    api_key_valid: bool = Depends(verify_staff_api_key),
) -> StaffUser:
    """Get the current authenticated user from the request headers.

    This is an alias for get_staff_user to maintain compatibility with
    existing code that expects a get_current_user function.

    Args:
        x_staff_id: The staff ID from the request header (X-Staff-Id)
        api_key_valid: Whether the API key is valid (validated by verify_staff_api_key)

    Returns:
        StaffUser: Current authenticated staff user object

    Raises:
        HTTPException: If staff ID is missing (401 Unauthorized)
    """
    return await get_staff_user(x_staff_id, api_key_valid)
