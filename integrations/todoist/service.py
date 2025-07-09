"""
Todoist Service for The HigherSelf Network Server

This service provides comprehensive Todoist integration including:
- Task and project management
- Business entity-specific workflows
- Automated task creation from server events
- IFTTT integration support
- Analytics and reporting
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import aiohttp
from pydantic import ValidationError

from .models import (
    BusinessEntity,
    HSNTaskAutomation,
    ProjectCreationRequest,
    TaskAnalytics,
    TaskCreationRequest,
    TodoistIntegrationConfig,
    TodoistLabel,
    TodoistProject,
    TodoistSyncResponse,
    TodoistTask,
    TodoistWebhookEvent,
)

logger = logging.getLogger(__name__)


class TodoistAPIError(Exception):
    """Custom exception for Todoist API errors."""
    pass


class TodoistService:
    """
    Main service class for Todoist integration with HSN operations.
    """
    
    def __init__(self, config: TodoistIntegrationConfig):
        self.config = config
        self.base_url = "https://api.todoist.com/rest/v2"
        self.sync_url = "https://api.todoist.com/sync/v9"
        self.session: Optional[aiohttp.ClientSession] = None
        self._sync_token = "*"
        
        # Business entity project mappings
        self.business_projects = {
            BusinessEntity.SEVEN_SPACE: "7Space Art Gallery & Wellness Center",
            BusinessEntity.AM_CONSULTING: "AM Consulting Projects",
            BusinessEntity.HIGHER_SELF_NETWORK: "HSN Server Administration"
        }
        
        # Standard HSN labels for operational efficiency
        self.hsn_labels = [
            # Energy levels
            "high_energy", "medium_energy", "low_energy", "creative_energy",
            # Time durations
            "2_minutes", "5_minutes", "15_minutes", "30_minutes", "1_hour", "2_hours",
            # Device types
            "computer", "phone", "tablet", "offline",
            # Business entities
            "7space", "am_consulting", "hsn",
            # HSN operations
            "hsn_admin", "hsn_development", "hsn_integration", "hsn_monitoring",
            # Technology stack
            "api_work", "database", "docker", "fastapi", "github",
            # Workflow types
            "urgent", "important", "routine", "waiting_for", "follow_up",
            # Communication
            "email", "phone_call", "meeting", "documentation"
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.config.api_token}",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        use_sync_api: bool = False
    ) -> Dict[str, Any]:
        """Make authenticated request to Todoist API."""
        if not self.session:
            raise TodoistAPIError("Service not initialized. Use async context manager.")
        
        base_url = self.sync_url if use_sync_api else self.base_url
        url = f"{base_url}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url, params=data) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                async with self.session.request(method, url, json=data) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Todoist API request failed: {e}")
            raise TodoistAPIError(f"API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Todoist API request: {e}")
            raise TodoistAPIError(f"Unexpected error: {e}")
    
    async def initialize_hsn_workspace(self) -> Dict[str, str]:
        """
        Initialize HSN workspace with business entity projects and labels.
        Returns mapping of business entities to project IDs.
        """
        logger.info("Initializing HSN Todoist workspace...")
        
        # Create business entity projects
        project_ids = {}
        for entity, project_name in self.business_projects.items():
            try:
                project = await self.create_project(ProjectCreationRequest(
                    name=project_name,
                    business_entity=entity,
                    color="blue" if entity == BusinessEntity.HIGHER_SELF_NETWORK else "green"
                ))
                project_ids[entity] = project.id
                logger.info(f"Created project for {entity.value}: {project.id}")
            except Exception as e:
                logger.error(f"Failed to create project for {entity.value}: {e}")
        
        # Create HSN operational labels
        await self._create_hsn_labels()
        
        # Update config with project IDs
        self.config.default_project_ids.update(project_ids)
        
        return project_ids
    
    async def _create_hsn_labels(self):
        """Create standard HSN labels for operational efficiency."""
        existing_labels = await self.get_labels()
        existing_names = {label.name for label in existing_labels}
        
        for label_name in self.hsn_labels:
            if label_name not in existing_names:
                try:
                    await self.create_label(TodoistLabel(name=label_name))
                    logger.info(f"Created label: {label_name}")
                except Exception as e:
                    logger.warning(f"Failed to create label {label_name}: {e}")
    
    async def create_task(self, task_request: TaskCreationRequest) -> TodoistTask:
        """Create a new task with HSN-specific enhancements."""
        # Auto-assign project based on business entity
        if not task_request.project_id and task_request.business_entity:
            task_request.project_id = self.config.default_project_ids.get(
                task_request.business_entity
            )
        
        # Add HSN-specific labels
        hsn_labels = []
        if task_request.business_entity:
            hsn_labels.append(task_request.business_entity.value)
        if task_request.energy_level:
            hsn_labels.append(task_request.energy_level.value)
        if task_request.time_duration:
            hsn_labels.append(task_request.time_duration.value)
        if task_request.device_type:
            hsn_labels.append(task_request.device_type.value)
        
        # Merge with existing labels
        all_labels = list(set(task_request.labels + hsn_labels))
        
        # Prepare API payload
        payload = {
            "content": task_request.content,
            "project_id": task_request.project_id,
            "labels": all_labels,
            "priority": task_request.priority.value
        }
        
        # Add optional fields
        if task_request.description:
            payload["description"] = task_request.description
        if task_request.due_string:
            payload["due_string"] = task_request.due_string
        if task_request.due_date:
            payload["due_date"] = task_request.due_date
        if task_request.section_id:
            payload["section_id"] = task_request.section_id
        if task_request.parent_id:
            payload["parent_id"] = task_request.parent_id
        
        response = await self._make_request("POST", "tasks", payload)
        
        # Convert to HSN task model
        task = TodoistTask(
            **response,
            business_entity=task_request.business_entity,
            energy_level=task_request.energy_level,
            time_duration=task_request.time_duration,
            device_type=task_request.device_type,
            server_event_id=task_request.server_event_id,
            automation_source=task_request.automation_source
        )
        
        logger.info(f"Created task: {task.content} (ID: {task.id})")
        return task
    
    async def get_tasks(
        self, 
        project_id: Optional[str] = None,
        label: Optional[str] = None,
        filter_expr: Optional[str] = None
    ) -> List[TodoistTask]:
        """Get tasks with optional filtering."""
        params = {}
        if project_id:
            params["project_id"] = project_id
        if label:
            params["label"] = label
        if filter_expr:
            params["filter"] = filter_expr
        
        response = await self._make_request("GET", "tasks", params)
        return [TodoistTask(**task) for task in response]
    
    async def create_project(self, project_request: ProjectCreationRequest) -> TodoistProject:
        """Create a new project."""
        payload = {
            "name": project_request.name,
            "color": project_request.color or "blue",
            "is_favorite": project_request.is_favorite,
            "view_style": project_request.view_style
        }
        
        if project_request.parent_id:
            payload["parent_id"] = project_request.parent_id
        
        response = await self._make_request("POST", "projects", payload)
        
        project = TodoistProject(
            **response,
            business_entity=project_request.business_entity
        )
        
        logger.info(f"Created project: {project.name} (ID: {project.id})")
        return project
    
    async def get_projects(self) -> List[TodoistProject]:
        """Get all projects."""
        response = await self._make_request("GET", "projects")
        return [TodoistProject(**project) for project in response]
    
    async def create_label(self, label: TodoistLabel) -> TodoistLabel:
        """Create a new label."""
        payload = {"name": label.name}
        if label.color:
            payload["color"] = label.color
        if label.order is not None:
            payload["order"] = label.order
        if label.is_favorite:
            payload["is_favorite"] = label.is_favorite
        
        response = await self._make_request("POST", "labels", payload)
        return TodoistLabel(**response)
    
    async def get_labels(self) -> List[TodoistLabel]:
        """Get all labels."""
        response = await self._make_request("GET", "labels")
        return [TodoistLabel(**label) for label in response]

    async def create_task_from_server_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        business_entity: BusinessEntity
    ) -> Optional[TodoistTask]:
        """
        Create task automatically from server events.

        Args:
            event_type: Type of server event (e.g., 'alert', 'deployment', 'error')
            event_data: Event data containing details
            business_entity: Business entity context

        Returns:
            Created task or None if no automation rule matches
        """
        # Find matching automation rule
        automation_rule = None
        for rule in self.config.automation_rules:
            if (rule.trigger_type == "server_event" and
                rule.business_entity == business_entity and
                rule.trigger_config.get("event_type") == event_type and
                rule.is_active):
                automation_rule = rule
                break

        if not automation_rule:
            logger.debug(f"No automation rule found for event: {event_type}")
            return None

        # Create task from template
        task_template = automation_rule.task_template.copy()

        # Replace placeholders in content and description
        content = task_template.content.format(**event_data)
        description = task_template.description
        if description:
            description = description.format(**event_data)

        # Create task request
        task_request = TaskCreationRequest(
            content=content,
            description=description,
            project_id=task_template.project_id,
            labels=task_template.labels,
            priority=task_template.priority,
            business_entity=business_entity,
            energy_level=task_template.energy_level,
            time_duration=task_template.time_duration,
            device_type=task_template.device_type,
            automation_source=f"server_event:{event_type}",
            server_event_id=event_data.get("event_id", str(uuid4()))
        )

        try:
            task = await self.create_task(task_request)

            # Update automation rule stats
            automation_rule.last_triggered = datetime.now()
            automation_rule.trigger_count += 1

            logger.info(f"Created automated task from {event_type}: {task.content}")
            return task

        except Exception as e:
            logger.error(f"Failed to create automated task from {event_type}: {e}")
            return None

    async def get_business_entity_analytics(
        self,
        business_entity: BusinessEntity,
        days_back: int = 30
    ) -> TaskAnalytics:
        """
        Generate analytics for a specific business entity.

        Args:
            business_entity: Business entity to analyze
            days_back: Number of days to look back for analytics

        Returns:
            TaskAnalytics object with performance metrics
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Get project ID for business entity
        project_id = self.config.default_project_ids.get(business_entity)
        if not project_id:
            raise ValueError(f"No project found for business entity: {business_entity}")

        # Get all tasks for the project
        tasks = await self.get_tasks(project_id=project_id)

        # Filter tasks by date range
        filtered_tasks = []
        for task in tasks:
            if task.created_at and task.created_at >= start_date:
                filtered_tasks.append(task)

        # Calculate metrics
        total_tasks = len(filtered_tasks)
        completed_tasks = sum(1 for task in filtered_tasks if task.is_completed)
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0.0

        # Analyze by priority
        tasks_by_priority: Dict[str, int] = {}
        for task in filtered_tasks:
            priority_name = f"priority_{task.priority.value}"
            tasks_by_priority[priority_name] = tasks_by_priority.get(priority_name, 0) + 1

        # Analyze by energy level (from labels)
        tasks_by_energy: Dict[str, int] = {}
        energy_levels = ["high_energy", "medium_energy", "low_energy", "creative_energy"]
        for task in filtered_tasks:
            for energy in energy_levels:
                if energy in task.labels:
                    tasks_by_energy[energy] = tasks_by_energy.get(energy, 0) + 1
                    break

        # Analyze by duration (from labels)
        tasks_by_duration: Dict[str, int] = {}
        durations = ["2_minutes", "5_minutes", "15_minutes", "30_minutes", "1_hour", "2_hours"]
        for task in filtered_tasks:
            for duration in durations:
                if duration in task.labels:
                    tasks_by_duration[duration] = tasks_by_duration.get(duration, 0) + 1
                    break

        return TaskAnalytics(
            business_entity=business_entity,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            completion_rate=completion_rate,
            tasks_by_priority=tasks_by_priority,
            tasks_by_energy_level=tasks_by_energy,
            tasks_by_duration=tasks_by_duration,
            period_start=start_date,
            period_end=end_date
        )

    async def sync_with_server_monitoring(self) -> Dict[str, Any]:
        """
        Sync with HSN server monitoring systems to create tasks for alerts.

        Returns:
            Summary of sync operation
        """
        sync_summary = {
            "tasks_created": 0,
            "alerts_processed": 0,
            "errors": []
        }

        # This would integrate with your monitoring system
        # For now, we'll create a placeholder implementation

        # Example: Check for system alerts and create tasks
        monitoring_events = [
            {
                "event_type": "system_alert",
                "event_id": str(uuid4()),
                "severity": "high",
                "message": "High CPU usage detected on HSN server",
                "timestamp": datetime.now().isoformat(),
                "server": "hsn-main"
            }
        ]

        for event in monitoring_events:
            try:
                task = await self.create_task_from_server_event(
                    event_type=event["event_type"],
                    event_data=event,
                    business_entity=BusinessEntity.HIGHER_SELF_NETWORK
                )
                if task:
                    sync_summary["tasks_created"] += 1
                sync_summary["alerts_processed"] += 1
            except Exception as e:
                sync_summary["errors"].append(f"Failed to process event {event['event_id']}: {e}")

        return sync_summary
