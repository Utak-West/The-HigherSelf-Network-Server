"""
Authentication Utilities

This module provides authentication utilities for API endpoints.
"""

import os
import hmac
import hashlib
from fastapi import Request, HTTPException, Depends, Header
from typing import Optional

from models.softr_models import StaffUser
from services.softr_service import SoftrService

# Secure webhook verification using HMAC
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

# Staff API key for authentication
STAFF_API_KEY = os.getenv("STAFF_API_KEY", "")

async def verify_webhook_signature(request: Request) -> bool:
    """
    Verify that the webhook request is authentic by checking its signature.
    Uses HMAC with SHA-256.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        True if the signature is valid, raises an exception otherwise
    """
    if not WEBHOOK_SECRET:
        # In development, we may not have a secret set
        # In production, this should never happen
        print("WARNING: No webhook secret set - verification disabled")
        return True
        
    # Get the signature from the headers
    signature_header = request.headers.get("x-signature")
    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing signature header")
    
    # Get the request body for verification
    body = await request.body()
    
    # Calculate expected signature
    hmac_obj = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    )
    expected_signature = hmac_obj.hexdigest()
    
    # Check if signatures match
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return True

async def verify_staff_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Verify that the staff API key is valid.
    
    Args:
        x_api_key: The API key from the request header
        
    Returns:
        True if the API key is valid, raises an exception otherwise
    """
    if not STAFF_API_KEY:
        # In development, we may not have a key set
        # In production, this should never happen
        print("WARNING: No staff API key set - verification disabled")
        return True
        
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
        
    if x_api_key != STAFF_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
        
    return True

async def get_staff_user(
    x_staff_id: Optional[str] = Header(None),
    api_key_valid: bool = Depends(verify_staff_api_key)
) -> StaffUser:
    """
    Get the staff user from the request headers.
    
    Args:
        x_staff_id: The staff ID from the request header
        api_key_valid: Whether the API key is valid (from verify_staff_api_key)
        
    Returns:
        StaffUser object if valid, raises an exception otherwise
    """
    if not x_staff_id:
        raise HTTPException(status_code=401, detail="Missing staff ID")
        
    # In a real implementation, this would look up the staff user in a database
    # For now, we'll return a mock user
    return StaffUser(
        id=x_staff_id,
        name="Staff User",
        email=f"{x_staff_id}@thehigherself.network",
        roles=["staff"]
    )
