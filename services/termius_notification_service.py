"""
Termius Notification Service for HigherSelf Network Server
Handles GitHub Actions notifications and displays them in Termius terminals
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import aiohttp
from fastapi import HTTPException
from pydantic import BaseModel, Field

from config.settings import get_settings

logger = logging.getLogger(__name__)


class NotificationStatus(str, Enum):
    """Notification status types."""
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in_progress"
    WARNING = "warning"


class NotificationSource(str, Enum):
    """Notification source types."""
    GITHUB_ACTIONS = "github_actions"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    SECURITY = "security"


@dataclass
class TerminalSession:
    """Represents an active Termius terminal session."""
    session_id: str
    user_id: str
    host: str
    environment: str
    last_activity: datetime
    active: bool = True


class GitHubActionsNotification(BaseModel):
    """GitHub Actions notification model."""
    source: NotificationSource = NotificationSource.GITHUB_ACTIONS
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]


class TermiusNotificationService:
    """Service for handling Termius notifications and terminal integration."""
    
    def __init__(self):
        self.settings = get_settings()
        self.active_sessions: Dict[str, TerminalSession] = {}
        self.notification_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
    async def register_terminal_session(
        self, 
        session_id: str, 
        user_id: str, 
        host: str, 
        environment: str
    ) -> bool:
        """Register a new terminal session for notifications."""
        try:
            session = TerminalSession(
                session_id=session_id,
                user_id=user_id,
                host=host,
                environment=environment,
                last_activity=datetime.now(timezone.utc)
            )
            
            self.active_sessions[session_id] = session
            logger.info(f"Registered terminal session: {session_id} for {user_id}@{host}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering terminal session: {e}")
            return False
    
    async def unregister_terminal_session(self, session_id: str) -> bool:
        """Unregister a terminal session."""
        try:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Unregistered terminal session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering terminal session: {e}")
            return False
    
    async def process_github_actions_webhook(self, payload: Dict[str, Any]) -> bool:
        """Process incoming GitHub Actions webhook."""
        try:
            notification = GitHubActionsNotification(**payload)
            
            # Format notification for terminal display
            formatted_message = await self._format_github_actions_message(notification)
            
            # Send to active terminal sessions
            await self._broadcast_to_terminals(formatted_message, notification.data.get("environment"))
            
            # Store in history
            self._add_to_history(notification.dict())
            
            logger.info(f"Processed GitHub Actions notification: {notification.event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing GitHub Actions webhook: {e}")
            return False
    
    async def _format_github_actions_message(self, notification: GitHubActionsNotification) -> str:
        """Format GitHub Actions notification for terminal display."""
        data = notification.data
        
        # Get status emoji and color codes
        status_info = self._get_status_display_info(data.get("status", "unknown"))
        
        # Build the terminal message
        lines = [
            f"\n{status_info['border']}",
            f"{status_info['emoji']} HigherSelf Network Server - {data.get('workflow', 'Unknown Workflow')}",
            f"{status_info['border']}",
            f"Status: {status_info['color']}{data.get('status', 'unknown').upper()}{status_info['reset']}",
            f"Branch: {data.get('branch', 'unknown')}",
            f"Commit: {data.get('commit_sha', 'unknown')[:8]}",
        ]
        
        if data.get("commit_message"):
            lines.append(f"Message: {data.get('commit_message')[:60]}...")
        
        if data.get("environment"):
            lines.append(f"Environment: {data.get('environment')}")
        
        if data.get("image_tag"):
            lines.append(f"Image: {data.get('image_tag')}")
        
        lines.extend([
            f"Actor: {data.get('actor', 'unknown')}",
            f"Time: {notification.timestamp.strftime('%H:%M:%S UTC')}",
        ])
        
        # Add detailed status if available
        if data.get("pre_flight_status"):
            lines.extend([
                "",
                "Detailed Status:",
                f"  • Pre-flight: {self._format_job_status(data.get('pre_flight_status'))}",
                f"  • Quality Checks: {self._format_job_status(data.get('quality_checks_status'))}",
                f"  • Test Suite: {self._format_job_status(data.get('test_suite_status'))}",
                f"  • Build: {self._format_job_status(data.get('build_status'))}",
                f"  • Security Scan: {self._format_job_status(data.get('security_scan_status'))}",
                f"  • Deploy: {self._format_job_status(data.get('deploy_status'))}",
            ])
        
        if data.get("run_url"):
            lines.append(f"\nView Details: {data.get('run_url')}")
        
        lines.append(f"{status_info['border']}\n")
        
        return "\n".join(lines)
    
    def _get_status_display_info(self, status: str) -> Dict[str, str]:
        """Get display information for status."""
        status_map = {
            "success": {
                "emoji": "✅",
                "color": "\033[32m",  # Green
                "border": "=" * 60,
                "reset": "\033[0m"
            },
            "failure": {
                "emoji": "❌",
                "color": "\033[31m",  # Red
                "border": "=" * 60,
                "reset": "\033[0m"
            },
            "cancelled": {
                "emoji": "⚠️",
                "color": "\033[33m",  # Yellow
                "border": "=" * 60,
                "reset": "\033[0m"
            },
            "in_progress": {
                "emoji": "🔄",
                "color": "\033[34m",  # Blue
                "border": "-" * 60,
                "reset": "\033[0m"
            }
        }
        
        return status_map.get(status, status_map["in_progress"])
    
    def _format_job_status(self, status: str) -> str:
        """Format individual job status with color."""
        if not status:
            return "skipped"
        
        color_map = {
            "success": "\033[32m✓\033[0m",  # Green checkmark
            "failure": "\033[31m✗\033[0m",  # Red X
            "cancelled": "\033[33m⚠\033[0m",  # Yellow warning
            "skipped": "\033[90m-\033[0m"  # Gray dash
        }
        
        return f"{color_map.get(status, status)} {status}"
    
    async def _broadcast_to_terminals(self, message: str, environment: Optional[str] = None) -> None:
        """Broadcast message to active terminal sessions."""
        target_sessions = []
        
        for session_id, session in self.active_sessions.items():
            # Filter by environment if specified
            if environment and session.environment != environment:
                continue
            
            target_sessions.append(session)
        
        if not target_sessions:
            logger.warning("No active terminal sessions to broadcast to")
            return
        
        # Send to each terminal session
        for session in target_sessions:
            try:
                await self._send_to_terminal(session, message)
            except Exception as e:
                logger.error(f"Error sending to terminal {session.session_id}: {e}")
    
    async def _send_to_terminal(self, session: TerminalSession, message: str) -> None:
        """Send message to a specific terminal session."""
        try:
            import subprocess
            import os

            # Try simple file-based notifier first
            simple_notifier_path = os.path.expanduser("~/.termius_higherself/scripts/simple_termius_notifier.py")
            if os.path.exists(simple_notifier_path):
                subprocess.run([
                    "python3", simple_notifier_path, "send",
                    "--message", message,
                    "--type", "info",
                    "--title", "HigherSelf Network Server"
                ], capture_output=True, timeout=10)
                logger.info(f"File notification sent to {session.session_id}")
            else:
                # Fallback: Try SSH notifier
                ssh_notifier_path = os.path.expanduser("~/.termius_higherself/scripts/termius_ssh_notifier.py")
                if os.path.exists(ssh_notifier_path):
                    subprocess.run([
                        "python3", ssh_notifier_path, "send",
                        "--message", message,
                        "--type", "info"
                    ], capture_output=True, timeout=10)
                    logger.info(f"SSH notification sent to {session.session_id}")
                else:
                    logger.warning(f"No notifier found at {simple_notifier_path} or {ssh_notifier_path}")

        except Exception as e:
            logger.error(f"Error sending notification: {e}")

        # Always log the message as fallback
        logger.info(f"Terminal notification for {session.session_id}: {message}")
    
    def _add_to_history(self, notification: Dict[str, Any]) -> None:
        """Add notification to history."""
        self.notification_history.append(notification)
        
        # Keep only the most recent notifications
        if len(self.notification_history) > self.max_history:
            self.notification_history = self.notification_history[-self.max_history:]
    
    async def get_notification_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent notification history."""
        return self.notification_history[-limit:]
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of active terminal sessions."""
        return [
            {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "host": session.host,
                "environment": session.environment,
                "last_activity": session.last_activity.isoformat(),
                "active": session.active
            }
            for session in self.active_sessions.values()
        ]


# Global service instance
termius_notification_service = TermiusNotificationService()
