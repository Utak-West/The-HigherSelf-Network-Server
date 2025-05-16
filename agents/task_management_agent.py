"""Task Management Agent for The HigherSelf Network.

This agent creates and manages tasks in:
- Notion (Master Tasks Database - central hub)
- Google Calendar or other calendar systems
- Optional integration with Trello

All tasks are created, tracked, and updated in Notion as the central hub.
This agent supports templated task creation, workflow-driven task generation,
and task status management.
"""

import asyncio
import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from utils.logging_utils import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

from agents.base_agent import BaseAgent
from models.base import AgentCapability, ApiPlatform
from models.notion_db_models import BusinessEntity, Task, WorkflowInstance
from models.task_models import (
    TaskCategory,
    TaskPriority,
    TaskReminder,
    TaskSource,
    TaskStatus,
    TaskTemplate,
)
from services.notion_service import NotionService


class TaskManagementAgent(BaseAgent):
    """Agent that creates and manages tasks from workflow triggers.

    This agent specializes in task management across Notion, Google Calendar,
    and optionally Trello. It handles task creation, assignment, status updates,
    and integration with workflow events.

    Uses Notion as the central hub for all task data, with synchronization to
    other platforms as needed.
    """

    def __init__(
        self,
        agent_id: str = "TaskManagementAgent",
        name: str = "Task Management Agent",
        description: str = "Creates and manages tasks from workflow triggers",
        version: str = "1.0.0",
        business_entities: Optional[List[str]] = None,
        api_keys: Optional[Dict[str, str]] = None,
        notion_service: Optional[NotionService] = None,
    ):
        """Initialize the Task Management Agent.

        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name
            description: Agent description and responsibilities
            version: Agent version
            business_entities: List of business entity IDs this agent is associated with
            api_keys: Dictionary of API keys for various services
            notion_service: NotionService instance or None to create from environment
        """
        capabilities = [
            AgentCapability.TASK_CREATION,
            AgentCapability.TASK_MANAGEMENT,
            AgentCapability.WORKFLOW_MANAGEMENT,
            AgentCapability.WORKFLOW_ORCHESTRATION,
        ]

        apis_utilized = [ApiPlatform.NOTION, ApiPlatform.HUBSPOT]

        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            version=version,
            capabilities=capabilities,
            apis_utilized=apis_utilized,
            business_entities=business_entities,
            notion_service=notion_service,
        )

        # Set up API credentials
        self.api_keys = api_keys or {}

        # Retrieve API keys from environment if not provided
        api_key_names = ["GOOGLE_CALENDAR_API_KEY", "TRELLO_API_KEY"]

        for key_name in api_key_names:
            env_value = os.environ.get(key_name)
            if key_name not in self.api_keys and env_value:
                self.api_keys[key_name] = env_value

        self.logger.info(
            f"Task Management Agent {self.agent_id} v{self.version} initialized"
        )

    async def create_task_from_template(
        self,
        template_id: str,
        workflow_instance_id: Optional[str] = None,
        override_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a task from a template in Notion.

        Creates a new task based on a predefined template, allowing for overrides of
        specific parameters. The task is created in Notion as the central hub.

        Args:
            template_id: The ID of the template to use
            workflow_instance_id: Optional workflow instance this task belongs to
            override_params: Optional dictionary of parameters to override from the template

        Returns:
            Dict[str, Any]: Dictionary with task creation results including:
                status: 'success' or 'error'
                task_id: ID of the created task (if successful)
                title: Title of the created task (if successful)
                due_date: ISO formatted due date (if applicable)
        """
        self.logger.info(f"Creating task from template '{template_id}'")

        # Get template from Notion
        notion_svc = await self.notion_service
        template = await notion_svc.get_task_template(template_id)

        if not template:
            error_msg = f"Template '{template_id}' not found"
            self.logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        # Apply override parameters if provided
        if override_params:
            for key, value in override_params.items():
                if hasattr(template, key):
                    setattr(template, key, value)

        # Calculate due date if offset is specified
        due_date = None
        if template.due_date_offset_days is not None:
            due_date = datetime.now() + timedelta(days=template.due_date_offset_days)

        # Get workflow instance if provided
        workflow_instance = None
        if workflow_instance_id:
            workflow_instance = await notion_svc.get_workflow_instance(
                workflow_instance_id
            )

        # Create task in Notion
        task = Task(
            title=template.name,
            description=template.description,
            priority=template.priority.value,
            status=TaskStatus.NOT_STARTED.value,
            category=template.category.value,
            due_date=due_date,
            assigned_to=template.default_assignee,
            created_by=self.agent_id,
            source=template.source.value,
            business_entity_id=template.business_entity_id,
            workflow_instance_id=workflow_instance_id if workflow_instance else None,
            estimated_minutes=template.estimated_minutes,
            checklist_items=template.checklist_items,
            additional_data=template.additional_data,
        )

        task_id = await notion_svc.create_page(task)

        # Create reminder if specified
        if template.reminder_days_before and due_date:
            remind_at = due_date - timedelta(days=template.reminder_days_before)

            reminder = TaskReminder(
                task_id=task_id,
                remind_at=remind_at,
                channel="notion",  # Default to Notion
                recipient=template.default_assignee or "default",
            )

            await notion_svc.create_task_reminder(reminder)

        # Log to workflow instance if provided
        if workflow_instance:
            await self.log_action(
                workflow_instance=workflow_instance,
                action=f"Created task '{template.name}'",
                details={"task_id": task_id, "template_id": template_id},
            )

        self.logger.info(
            f"Created task '{task_id}' in Notion from template '{template_id}'"
        )

        return {
            "status": "success",
            "task_id": task_id,
            "title": template.name,
            "due_date": due_date.isoformat() if due_date else None,
        }

    async def create_task(
        self,
        title: str,
        description: str,
        business_entity_id: str,
        category: TaskCategory = TaskCategory.ADMIN,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[date] = None,
        assigned_to: Optional[str] = None,
        workflow_instance_id: Optional[str] = None,
        source: TaskSource = TaskSource.MANUAL,
        checklist_items: Optional[List[str]] = None,
        reminder_days_before: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new task directly in Notion.

        Creates a task with the specified parameters in Notion as the central hub.
        Optionally adds reminders and links to workflow instances.

        Args:
            title: Task title
            description: Task description
            business_entity_id: ID of the business entity this task belongs to
            category: Task category (default: ADMIN)
            priority: Task priority (default: MEDIUM)
            due_date: Optional due date for the task
            assigned_to: Optional user ID or name to assign the task to
            workflow_instance_id: Optional workflow instance this task belongs to
            source: Task source (default: MANUAL)
            checklist_items: Optional list of checklist item descriptions
            reminder_days_before: Optional number of days before due date to send reminder

        Returns:
            Dict[str, Any]: Dictionary with task creation results including:
                status: 'success' or 'error'
                task_id: ID of the created task (if successful)
                title: Title of the created task (if successful)
                due_date: ISO formatted due date (if applicable)
        """
        if not title:
            raise ValueError("Task title cannot be empty")
        if not description:
            raise ValueError("Task description cannot be empty")
        if not business_entity_id:
            raise ValueError("Business entity ID cannot be empty")

        self.logger.info(
            f"Creating task '{title}' for business entity '{business_entity_id}'"
        )

        notion_svc = await self.notion_service

        # Get workflow instance if provided
        workflow_instance = None
        if workflow_instance_id:
            workflow_instance = await notion_svc.get_workflow_instance(
                workflow_instance_id
            )

        # Create task in Notion
        task = Task(
            title=title,
            description=description,
            priority=priority.value,
            status=TaskStatus.NOT_STARTED.value,
            category=category.value,
            due_date=due_date,
            assigned_to=assigned_to,
            created_by=self.agent_id,
            source=source.value,
            business_entity_id=business_entity_id,
            workflow_instance_id=workflow_instance_id if workflow_instance else None,
            checklist_items=checklist_items or [],
        )

        task_id = await notion_svc.create_page(task)

        # Create reminder if specified
        if reminder_days_before and due_date:
            remind_at = datetime.combine(due_date, datetime.min.time()) - timedelta(
                days=reminder_days_before
            )

            reminder = TaskReminder(
                task_id=task_id,
                remind_at=remind_at,
                channel="notion",  # Default to Notion
                recipient=assigned_to or "default",
            )

            await notion_svc.create_task_reminder(reminder)

        # Log to workflow instance if provided
        if workflow_instance:
            await self.log_action(
                workflow_instance=workflow_instance,
                action=f"Created task '{title}'",
                details={"task_id": task_id},
            )

        self.logger.info(f"Created task '{task_id}' in Notion with title '{title}'")

        return {
            "status": "success",
            "task_id": task_id,
            "title": title,
            "due_date": due_date.isoformat() if due_date else None,
        }

    async def update_task_status(
        self, task_id: str, status: TaskStatus, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a task's status in Notion.

        Updates the status of an existing task and optionally adds a comment.
        Also handles workflow instance updates if the task is part of a workflow.

        Args:
            task_id: ID of the task to update
            status: New status to set
            comment: Optional comment to add to the task

        Returns:
            Dict[str, Any]: Dictionary with status update results including:
                status: 'success' or 'error'
                task_id: ID of the updated task
                previous_status: Previous status value
                new_status: New status value
        """
        if not task_id:
            raise ValueError("Task ID cannot be empty")
        if not status:
            raise ValueError("Status cannot be None")

        self.logger.info(f"Updating task '{task_id}' status to '{status.value}'")

        notion_svc = await self.notion_service
        task = await notion_svc.get_task(task_id)

        if not task:
            error_msg = f"Task '{task_id}' not found"
            self.logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        previous_status = task.status
        task.status = status.value
        task.last_updated = datetime.now()

        if comment:
            if not task.comments:
                task.comments = []

            task.comments.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "author": self.agent_id,
                    "text": comment,
                }
            )

        await notion_svc.update_page(task)

        # If task is completed, check if it's part of a workflow and update accordingly
        if status == TaskStatus.COMPLETED and task.workflow_instance_id:
            workflow_instance = await notion_svc.get_workflow_instance(
                task.workflow_instance_id
            )
            if workflow_instance:
                await self.log_action(
                    workflow_instance=workflow_instance,
                    action=f"Completed task '{task.title}'",
                    details={"task_id": task_id, "previous_status": previous_status},
                )

        self.logger.info(
            f"Updated task '{task_id}' status from '{previous_status}' to '{status.value}'"
        )

        return {
            "status": "success",
            "task_id": task_id,
            "previous_status": previous_status,
            "new_status": status.value,
        }

    async def assign_task(
        self, task_id: str, assignee: str, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Assign a task to someone in Notion.

        Updates the assignee of an existing task and optionally adds a comment.
        Also handles workflow instance updates if the task is part of a workflow.

        Args:
            task_id: ID of the task to assign
            assignee: User ID or name to assign the task to
            comment: Optional comment to add to the task

        Returns:
            Dict[str, Any]: Dictionary with assignment results including:
                status: 'success' or 'error'
                task_id: ID of the updated task
                previous_assignee: Previous assignee value
                new_assignee: New assignee value
        """
        if not task_id:
            raise ValueError("Task ID cannot be empty")
        if not assignee:
            raise ValueError("Assignee cannot be empty")

        self.logger.info(f"Assigning task '{task_id}' to '{assignee}'")

        notion_svc = await self.notion_service
        task = await notion_svc.get_task(task_id)

        if not task:
            error_msg = f"Task '{task_id}' not found"
            self.logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        previous_assignee = task.assigned_to
        task.assigned_to = assignee
        task.last_updated = datetime.now()

        if comment:
            if not task.comments:
                task.comments = []

            task.comments.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "author": self.agent_id,
                    "text": comment,
                }
            )

        await notion_svc.update_page(task)

        # Log to workflow instance if part of a workflow
        if task.workflow_instance_id:
            workflow_instance = await notion_svc.get_workflow_instance(
                task.workflow_instance_id
            )
            if workflow_instance:
                await self.log_action(
                    workflow_instance=workflow_instance,
                    action=f"Assigned task '{task.title}' to {assignee}",
                    details={
                        "task_id": task_id,
                        "previous_assignee": previous_assignee,
                    },
                )

        self.logger.info(f"Assigned task '{task_id}' to '{assignee}'")

        return {
            "status": "success",
            "task_id": task_id,
            "previous_assignee": previous_assignee,
            "new_assignee": assignee,
        }

    async def process_workflow_event(
        self, workflow_instance_id: str, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a workflow event and create appropriate tasks.

        Handles workflow events by creating relevant tasks based on templates
        configured for the specific workflow and event type. All tasks are
        created in Notion as the central hub.

        Args:
            workflow_instance_id: ID of the workflow instance
            event_type: Type of event that occurred
            event_data: Dictionary with event data

        Returns:
            Dict[str, Any]: Dictionary with processing results including:
                status: 'success' or 'error'
                workflow_instance_id: ID of the workflow instance
                event_type: Type of event processed
                tasks_created: Number of tasks created
                tasks: List of created tasks (if any)
        """
        if not workflow_instance_id:
            raise ValueError("Workflow instance ID cannot be empty")
        if not event_type:
            raise ValueError("Event type cannot be empty")

        self.logger.info(
            f"Processing workflow event '{event_type}' for instance '{workflow_instance_id}'"
        )

        notion_svc = await self.notion_service
        workflow_instance = await notion_svc.get_workflow_instance(workflow_instance_id)

        if not workflow_instance:
            error_msg = f"Workflow instance '{workflow_instance_id}' not found"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
            }

        # Look up task templates for this workflow and event type
        templates = await notion_svc.get_task_templates_for_workflow(
            workflow_id=workflow_instance.workflow_id, event_type=event_type
        )

        if not templates:
            self.logger.info(
                f"No task templates found for workflow '{workflow_instance.workflow_id}' and event '{event_type}'"
            )
            return {
                "status": "success",
                "workflow_instance_id": workflow_instance_id,
                "event_type": event_type,
                "tasks_created": 0,
            }

        # Create tasks from templates
        created_tasks = []
        for template in templates:
            override_params = {
                "due_date_offset_days": self._calculate_offset(template, event_data)
            }

            task_result = await self.create_task_from_template(
                template_id=template.id,
                workflow_instance_id=workflow_instance_id,
                override_params=override_params,
            )

            if task_result.get("status") == "success":
                created_tasks.append(
                    {
                        "task_id": task_result.get("task_id"),
                        "title": task_result.get("title"),
                        "template_id": template.id,
                    }
                )

        await self.log_action(
            workflow_instance=workflow_instance,
            action=f"Created {len(created_tasks)} tasks for event {event_type}",
            details={"tasks": created_tasks},
        )

        self.logger.info(
            f"Created {len(created_tasks)} tasks for workflow instance '{workflow_instance_id}'"
        )

        return {
            "status": "success",
            "workflow_instance_id": workflow_instance_id,
            "event_type": event_type,
            "tasks_created": len(created_tasks),
            "tasks": created_tasks,
        }

    def _calculate_offset(
        self, template: TaskTemplate, event_data: Dict[str, Any]
    ) -> Optional[int]:
        """Calculate due date offset based on template and event data.

        Args:
            template: The task template being used
            event_data: Dictionary with event data

        Returns:
            Optional[int]: Number of days to offset the due date, or None if
                no offset should be applied
        """
        # Example: For a booking event, calculate based on event date
        if template.source == TaskSource.BOOKING and "event_date" in event_data:
            try:
                event_date = datetime.fromisoformat(event_data["event_date"])
                days_until_event = (event_date - datetime.now()).days

                # Set due date based on event timing
                if days_until_event > 7:
                    return days_until_event - 7  # One week before
                elif days_until_event > 1:
                    return days_until_event - 1  # One day before
                else:
                    return 0  # Due immediately
            except (ValueError, TypeError):
                pass

        # Default to template's setting
        return template.due_date_offset_days

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an event received by this agent.

        Routes events to appropriate handlers based on the event type.

        Args:
            event_type: Type of event to process
            event_data: Dictionary with event data

        Returns:
            Dict[str, Any]: Result of event processing
        """
        event_handlers = {
            "create_task_from_template": self.create_task_from_template,
            "create_task": self.create_task,
            "update_task_status": self.update_task_status,
            "assign_task": self.assign_task,
            "process_workflow_event": self.process_workflow_event,
        }

        handler = event_handlers.get(event_type)
        if not handler:
            error_msg = f"Unsupported event type: '{event_type}'"
            self.logger.warning(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "supported_events": list(event_handlers.keys()),
            }

        try:
            return await handler(**event_data)
        except Exception as e:
            self.logger.error(f"Error processing {event_type}: {e}")
            error_msg = f"Error processing event '{event_type}': {str(e)}"
            self.logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    async def check_health(self) -> Dict[str, Any]:
        """Check the health status of this agent.

        Tests connection to Notion API and checks for availability of
        other configured APIs.

        Returns:
            Dict[str, Any]: Health check results including:
                agent_id: ID of this agent
                status: 'healthy' or 'degraded'
                checks: Dictionary with individual health check results
                timestamp: ISO formatted timestamp of the health check
        """
        health_checks = {
            "notion_api": False,
            "google_calendar_api": False,
            "trello_api": False,
        }

        # Check Notion API
        try:
            notion_svc = await self.notion_service
            await notion_svc.query_database(Task, limit=1)
            health_checks["notion_api"] = True
        except Exception as e:
            error_msg = f"Notion API health check failed: {e}"
            self.logger.error(error_msg)
            health_checks["notion_api"] = False

        # Check other APIs based on available keys
        health_checks["google_calendar_api"] = (
            "GOOGLE_CALENDAR_API_KEY" in self.api_keys
        )
        health_checks["trello_api"] = "TRELLO_API_KEY" in self.api_keys

        return {
            "agent_id": self.agent_id,
            "status": "healthy" if all(health_checks.values()) else "degraded",
            "checks": health_checks,
            "timestamp": datetime.now().isoformat(),
        }
