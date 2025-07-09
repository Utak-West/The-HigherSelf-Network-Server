"""
Todoist Webhook Handler for The HigherSelf Network Server

This module handles incoming webhooks from Todoist and processes them
for integration with HSN server operations and business workflows.
"""

import hashlib
import hmac
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request

from .models import BusinessEntity, TodoistWebhookEvent
from .service import TodoistService

logger = logging.getLogger(__name__)


class TodoistWebhookHandler:
    """
    Handler for Todoist webhook events with HSN-specific processing.
    """
    
    def __init__(self, todoist_service: TodoistService, webhook_secret: Optional[str] = None):
        self.todoist_service = todoist_service
        self.webhook_secret = webhook_secret
        
        # Event handlers mapping
        self.event_handlers = {
            "item:added": self._handle_task_added,
            "item:updated": self._handle_task_updated,
            "item:completed": self._handle_task_completed,
            "item:deleted": self._handle_task_deleted,
            "project:added": self._handle_project_added,
            "project:updated": self._handle_project_updated,
            "project:deleted": self._handle_project_deleted,
        }
    
    def verify_webhook_signature(self, request_body: bytes, signature: str) -> bool:
        """
        Verify webhook signature for security.
        
        Args:
            request_body: Raw request body bytes
            signature: X-Todoist-Hmac-SHA256 header value
        
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping signature verification")
            return True
        
        try:
            # Calculate expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                request_body,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def process_webhook(self, request: Request) -> Dict[str, Any]:
        """
        Process incoming Todoist webhook.
        
        Args:
            request: FastAPI request object
        
        Returns:
            Processing result summary
        """
        # Get request body and signature
        body = await request.body()
        signature = request.headers.get("X-Todoist-Hmac-SHA256", "")
        
        # Verify signature
        if not self.verify_webhook_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse webhook data
        try:
            webhook_data = json.loads(body.decode('utf-8'))
            event = TodoistWebhookEvent(**webhook_data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse webhook data: {e}")
            raise HTTPException(status_code=400, detail="Invalid webhook data")
        
        # Process event
        result = await self._process_event(event)
        
        logger.info(f"Processed Todoist webhook event: {event.event_name}")
        return result
    
    async def _process_event(self, event: TodoistWebhookEvent) -> Dict[str, Any]:
        """
        Process a specific webhook event.
        
        Args:
            event: Parsed webhook event
        
        Returns:
            Processing result
        """
        handler = self.event_handlers.get(event.event_name)
        if not handler:
            logger.warning(f"No handler for event type: {event.event_name}")
            return {"status": "ignored", "event": event.event_name}
        
        try:
            result = await handler(event)
            return {"status": "processed", "event": event.event_name, "result": result}
        except Exception as e:
            logger.error(f"Error processing event {event.event_name}: {e}")
            return {"status": "error", "event": event.event_name, "error": str(e)}
    
    async def _handle_task_added(self, event: TodoistWebhookEvent) -> Dict[str, Any]:
        """Handle task added event."""
        task_data = event.event_data
        
        # Extract business entity from labels or project
        business_entity = self._extract_business_entity(task_data)
        
        # Log task creation for analytics
        logger.info(f"Task added: {task_data.get('content')} (Entity: {business_entity})")
        
        # Trigger any follow-up automations
        await self._trigger_task_automations(task_data, "task_added", business_entity)
        
        return {"task_id": task_data.get("id"), "business_entity": business_entity}
    
    async def _handle_task_updated(self, event: TodoistWebhookEvent) -> Dict[str, Any]:
        """Handle task updated event."""
        task_data = event.event_data
        business_entity = self._extract_business_entity(task_data)
        
        logger.info(f"Task updated: {task_data.get('content')} (Entity: {business_entity})")
        
        return {"task_id": task_data.get("id"), "business_entity": business_entity}
    
    async def _handle_task_completed(self, event: TodoistWebhookEvent) -> Dict[str, Any]:
        """Handle task completed event."""
        task_data = event.event_data
        business_entity = self._extract_business_entity(task_data)
        
        # Log completion for analytics
        logger.info(f"Task completed: {task_data.get('content')} (Entity: {business_entity})")
        
        # Trigger completion automations
        await self._trigger_task_automations(task_data, "task_completed", business_entity)
        
        return {"task_id": task_data.get("id"), "business_entity": business_entity}
    
    async def _handle_task_deleted(self, event: TodoistWebhookEvent) -> Dict[str, Any]:
        """Handle task deleted event."""
        task_data = event.event_data
        
        logger.info(f"Task deleted: {task_data.get('id')}")
        
        return {"task_id": task_data.get("id")}
    
    async def _handle_project_added(self, event: TodoistWebhookEvent) -> Dict[str, Any]:
        """Handle project added event."""
        project_data = event.event_data
        
        logger.info(f"Project added: {project_data.get('name')}")
        
        return {"project_id": project_data.get("id")}
    
    async def _handle_project_updated(self, event: TodoistWebhookEvent) -> Dict[str, Any]:
        """Handle project updated event."""
        project_data = event.event_data
        
        logger.info(f"Project updated: {project_data.get('name')}")
        
        return {"project_id": project_data.get("id")}
    
    async def _handle_project_deleted(self, event: TodoistWebhookEvent) -> Dict[str, Any]:
        """Handle project deleted event."""
        project_data = event.event_data
        
        logger.info(f"Project deleted: {project_data.get('id')}")
        
        return {"project_id": project_data.get("id")}
    
    def _extract_business_entity(self, task_data: Dict[str, Any]) -> Optional[BusinessEntity]:
        """
        Extract business entity from task data.
        
        Args:
            task_data: Task data from webhook
        
        Returns:
            BusinessEntity if found, None otherwise
        """
        labels = task_data.get("labels", [])
        
        # Check for business entity labels
        for label in labels:
            if label == "7space":
                return BusinessEntity.SEVEN_SPACE
            elif label == "am_consulting":
                return BusinessEntity.AM_CONSULTING
            elif label == "hsn":
                return BusinessEntity.HIGHER_SELF_NETWORK
        
        # Check project mapping
        project_id = task_data.get("project_id")
        if project_id:
            for entity, pid in self.todoist_service.config.default_project_ids.items():
                if pid == project_id:
                    return entity
        
        return None
    
    async def _trigger_task_automations(
        self, 
        task_data: Dict[str, Any], 
        trigger_type: str,
        business_entity: Optional[BusinessEntity]
    ):
        """
        Trigger follow-up automations based on task events.
        
        Args:
            task_data: Task data from webhook
            trigger_type: Type of trigger (task_added, task_completed, etc.)
            business_entity: Business entity context
        """
        if not business_entity:
            return
        
        # Find matching automation rules
        for rule in self.todoist_service.config.automation_rules:
            if (rule.trigger_type == "webhook" and
                rule.business_entity == business_entity and
                rule.trigger_config.get("webhook_event") == trigger_type and
                rule.is_active):
                
                try:
                    # Execute automation rule
                    await self._execute_automation_rule(rule, task_data)
                    logger.info(f"Executed automation rule: {rule.name}")
                except Exception as e:
                    logger.error(f"Failed to execute automation rule {rule.name}: {e}")
    
    async def _execute_automation_rule(
        self, 
        rule: Any, 
        task_data: Dict[str, Any]
    ):
        """
        Execute a specific automation rule.
        
        Args:
            rule: Automation rule to execute
            task_data: Task data for context
        """
        # This would implement the actual automation logic
        # For now, we'll log the execution
        logger.info(f"Executing automation rule: {rule.name} for task: {task_data.get('content')}")
        
        # Example: Create follow-up task, send notification, update external system, etc.
        # Implementation would depend on the specific rule configuration
