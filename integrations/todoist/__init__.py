"""
Todoist Integration for The HigherSelf Network Server

This module provides comprehensive Todoist integration for task management
across three business entities:
- 7Space Art Gallery and Wellness Center
- AM Consulting
- Higher Self Network server administration

Features:
- Automated task creation from server events
- Business entity-specific project management
- Webhook integration for real-time updates
- IFTTT automation support
- Comprehensive tagging and filtering system
"""

from .models import *
from .service import TodoistService
from .webhooks import TodoistWebhookHandler

__version__ = "1.0.0"
__all__ = [
    "TodoistService",
    "TodoistWebhookHandler",
    "TodoistTask",
    "TodoistProject",
    "TodoistLabel",
    "BusinessEntity",
    "TaskPriority",
    "TaskStatus",
]
