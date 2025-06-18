"""
Termius Integration API Endpoints
Handles GitHub Actions notifications and terminal session management
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from services.termius_notification_service import (
    termius_notification_service,
    NotificationStatus,
    NotificationSource
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/termius", tags=["Termius Integration"])


class TerminalSessionRequest(BaseModel):
    """Request model for terminal session registration."""
    session_id: str = Field(..., description="Unique terminal session ID")
    user_id: str = Field(..., description="User identifier")
    host: str = Field(..., description="Host/server name")
    environment: str = Field(..., description="Environment (dev/staging/prod)")


class GitHubActionsWebhookRequest(BaseModel):
    """Request model for GitHub Actions webhook."""
    source: str = Field(default="github_actions")
    event_type: str = Field(..., description="Type of GitHub Actions event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(..., description="Webhook payload data")


class NotificationResponse(BaseModel):
    """Response model for notifications."""
    success: bool
    message: str
    notification_id: Optional[str] = None


class SessionResponse(BaseModel):
    """Response model for session operations."""
    success: bool
    message: str
    session_id: Optional[str] = None


@router.post("/sessions/register", response_model=SessionResponse)
async def register_terminal_session(request: TerminalSessionRequest):
    """Register a new terminal session for notifications."""
    try:
        success = await termius_notification_service.register_terminal_session(
            session_id=request.session_id,
            user_id=request.user_id,
            host=request.host,
            environment=request.environment
        )
        
        if success:
            return SessionResponse(
                success=True,
                message="Terminal session registered successfully",
                session_id=request.session_id
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to register terminal session"
            )
            
    except Exception as e:
        logger.error(f"Error registering terminal session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error registering terminal session: {str(e)}"
        )


@router.delete("/sessions/{session_id}", response_model=SessionResponse)
async def unregister_terminal_session(session_id: str):
    """Unregister a terminal session."""
    try:
        success = await termius_notification_service.unregister_terminal_session(session_id)
        
        return SessionResponse(
            success=True,
            message="Terminal session unregistered successfully",
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error unregistering terminal session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error unregistering terminal session: {str(e)}"
        )


@router.get("/sessions")
async def get_active_sessions():
    """Get list of active terminal sessions."""
    try:
        sessions = await termius_notification_service.get_active_sessions()
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting active sessions: {str(e)}"
        )


@router.post("/webhooks/github-actions", response_model=NotificationResponse)
async def github_actions_webhook(
    request: GitHubActionsWebhookRequest,
    background_tasks: BackgroundTasks
):
    """Handle GitHub Actions webhook notifications."""
    try:
        logger.info(f"Received GitHub Actions webhook: {request.event_type}")
        
        # Process the webhook in the background
        background_tasks.add_task(
            termius_notification_service.process_github_actions_webhook,
            request.dict()
        )
        
        return NotificationResponse(
            success=True,
            message=f"GitHub Actions webhook processed: {request.event_type}"
        )
        
    except Exception as e:
        logger.error(f"Error processing GitHub Actions webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing webhook: {str(e)}"
        )


@router.post("/notifications/send")
async def send_custom_notification(
    message: str,
    status: NotificationStatus = NotificationStatus.IN_PROGRESS,
    environment: Optional[str] = None,
    background_tasks: BackgroundTasks
):
    """Send a custom notification to terminals."""
    try:
        notification_data = {
            "source": "custom",
            "event_type": "manual_notification",
            "timestamp": datetime.utcnow(),
            "data": {
                "message": message,
                "status": status,
                "environment": environment,
                "workflow": "Manual Notification",
                "actor": "System"
            }
        }
        
        background_tasks.add_task(
            termius_notification_service.process_github_actions_webhook,
            notification_data
        )
        
        return NotificationResponse(
            success=True,
            message="Custom notification sent"
        )
        
    except Exception as e:
        logger.error(f"Error sending custom notification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error sending notification: {str(e)}"
        )


@router.get("/notifications/history")
async def get_notification_history(limit: int = 20):
    """Get recent notification history."""
    try:
        history = await termius_notification_service.get_notification_history(limit)
        return {
            "success": True,
            "notifications": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting notification history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting notification history: {str(e)}"
        )


@router.get("/status")
async def get_service_status():
    """Get Termius integration service status."""
    try:
        sessions = await termius_notification_service.get_active_sessions()
        history = await termius_notification_service.get_notification_history(5)
        
        return {
            "success": True,
            "status": "healthy",
            "active_sessions": len(sessions),
            "recent_notifications": len(history),
            "service_info": {
                "name": "Termius Integration Service",
                "version": "1.0.0",
                "description": "GitHub Actions and terminal notification integration"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        return {
            "success": False,
            "status": "error",
            "error": str(e)
        }


@router.post("/test/notification")
async def test_notification(background_tasks: BackgroundTasks):
    """Send a test notification to verify the system is working."""
    try:
        test_data = {
            "source": "github_actions",
            "event_type": "test_notification",
            "timestamp": datetime.utcnow(),
            "data": {
                "workflow": "Test Workflow",
                "status": "success",
                "branch": "main",
                "commit_sha": "abc12345",
                "commit_message": "Test notification from Termius integration",
                "actor": "System Test",
                "environment": "testing",
                "message": "This is a test notification to verify Termius integration is working correctly.",
                "color": "#28a745",
                "emoji": "🧪"
            }
        }
        
        background_tasks.add_task(
            termius_notification_service.process_github_actions_webhook,
            test_data
        )
        
        return NotificationResponse(
            success=True,
            message="Test notification sent successfully"
        )
        
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error sending test notification: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "termius-integration",
        "timestamp": datetime.utcnow().isoformat()
    }
