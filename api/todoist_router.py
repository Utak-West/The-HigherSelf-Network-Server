"""
Todoist API Router for The HigherSelf Network Server

This module provides REST API endpoints for Todoist integration,
supporting task management across three business entities:
- 7Space Art Gallery and Wellness Center
- AM Consulting
- Higher Self Network server administration
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel

from integrations.todoist.models import (
    BusinessEntity,
    ProjectCreationRequest,
    TaskAnalytics,
    TaskCreationRequest,
    TodoistIntegrationConfig,
    TodoistProject,
    TodoistTask,
)
from integrations.todoist.service import TodoistService
from integrations.todoist.webhooks import TodoistWebhookHandler
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/todoist",
    tags=["todoist"],
    responses={404: {"description": "Not found"}},
)


# Dependency to get Todoist service
async def get_todoist_service() -> TodoistService:
    """Get configured Todoist service instance."""
    config = TodoistIntegrationConfig(
        api_token=settings.TODOIST_API_TOKEN,
        webhook_secret=settings.TODOIST_WEBHOOK_SECRET,
    )
    return TodoistService(config)


# Response models
class TaskCreationResponse(BaseModel):
    """Response model for task creation."""
    task: TodoistTask
    message: str


class ProjectCreationResponse(BaseModel):
    """Response model for project creation."""
    project: TodoistProject
    message: str


class AnalyticsResponse(BaseModel):
    """Response model for analytics."""
    analytics: TaskAnalytics
    business_entity: BusinessEntity


class WebhookResponse(BaseModel):
    """Response model for webhook processing."""
    status: str
    event: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ServerEventRequest(BaseModel):
    """Request model for server event task creation."""
    event_type: str
    event_data: Dict[str, Any]
    business_entity: BusinessEntity


# Task management endpoints
@router.post("/tasks", response_model=TaskCreationResponse)
async def create_task(
    task_request: TaskCreationRequest,
    background_tasks: BackgroundTasks,
    todoist_service: TodoistService = Depends(get_todoist_service)
):
    """
    Create a new task in Todoist with HSN-specific enhancements.
    
    This endpoint supports:
    - Business entity-specific project assignment
    - HSN operational tags (energy level, time duration, device type)
    - Automated label assignment
    - Integration with server monitoring
    """
    try:
        async with todoist_service:
            task = await todoist_service.create_task(task_request)
            
            # Log task creation for analytics
            background_tasks.add_task(
                _log_task_creation,
                task.id,
                task_request.business_entity,
                task_request.automation_source
            )
            
            return TaskCreationResponse(
                task=task,
                message=f"Task created successfully: {task.content}"
            )
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")


@router.get("/tasks", response_model=List[TodoistTask])
async def get_tasks(
    project_id: Optional[str] = None,
    label: Optional[str] = None,
    filter_expr: Optional[str] = None,
    business_entity: Optional[BusinessEntity] = None,
    todoist_service: TodoistService = Depends(get_todoist_service)
):
    """
    Get tasks with optional filtering by project, label, or business entity.
    
    Supports HSN-specific filtering:
    - Business entity filtering
    - Energy level filtering
    - Time duration filtering
    - Device type filtering
    """
    try:
        async with todoist_service:
            # If business entity is specified, get the corresponding project
            if business_entity and not project_id:
                project_id = todoist_service.config.default_project_ids.get(business_entity)
            
            tasks = await todoist_service.get_tasks(
                project_id=project_id,
                label=label,
                filter_expr=filter_expr
            )
            
            return tasks
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tasks: {str(e)}")


@router.post("/tasks/from-server-event", response_model=TaskCreationResponse)
async def create_task_from_server_event(
    event_request: ServerEventRequest,
    background_tasks: BackgroundTasks,
    todoist_service: TodoistService = Depends(get_todoist_service)
):
    """
    Create task automatically from server events.
    
    This endpoint enables automated task creation from:
    - System monitoring alerts
    - Deployment events
    - Error notifications
    - Performance warnings
    - Security incidents
    """
    try:
        async with todoist_service:
            task = await todoist_service.create_task_from_server_event(
                event_type=event_request.event_type,
                event_data=event_request.event_data,
                business_entity=event_request.business_entity
            )
            
            if not task:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No automation rule found for event: {event_request.event_type}"
                )
            
            return TaskCreationResponse(
                task=task,
                message=f"Automated task created from {event_request.event_type}: {task.content}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create task from server event: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Server event task creation failed: {str(e)}"
        )


# Project management endpoints
@router.post("/projects", response_model=ProjectCreationResponse)
async def create_project(
    project_request: ProjectCreationRequest,
    todoist_service: TodoistService = Depends(get_todoist_service)
):
    """
    Create a new project in Todoist.
    
    Supports business entity-specific project creation with:
    - Standardized naming conventions
    - Business entity tagging
    - Color coding by entity type
    """
    try:
        async with todoist_service:
            project = await todoist_service.create_project(project_request)
            
            return ProjectCreationResponse(
                project=project,
                message=f"Project created successfully: {project.name}"
            )
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=f"Project creation failed: {str(e)}")


@router.get("/projects", response_model=List[TodoistProject])
async def get_projects(
    todoist_service: TodoistService = Depends(get_todoist_service)
):
    """Get all projects."""
    try:
        async with todoist_service:
            projects = await todoist_service.get_projects()
            return projects
    except Exception as e:
        logger.error(f"Failed to get projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve projects: {str(e)}")


# Analytics endpoints
@router.get("/analytics/{business_entity}", response_model=AnalyticsResponse)
async def get_business_entity_analytics(
    business_entity: BusinessEntity,
    days_back: int = 30,
    todoist_service: TodoistService = Depends(get_todoist_service)
):
    """
    Get analytics for a specific business entity.
    
    Provides insights into:
    - Task completion rates
    - Priority distribution
    - Energy level optimization
    - Time duration patterns
    - Automation effectiveness
    """
    try:
        async with todoist_service:
            analytics = await todoist_service.get_business_entity_analytics(
                business_entity=business_entity,
                days_back=days_back
            )
            
            return AnalyticsResponse(
                analytics=analytics,
                business_entity=business_entity
            )
    except Exception as e:
        logger.error(f"Failed to get analytics for {business_entity}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Analytics retrieval failed: {str(e)}"
        )


# Webhook endpoint
@router.post("/webhook", response_model=WebhookResponse)
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    todoist_service: TodoistService = Depends(get_todoist_service)
):
    """
    Handle incoming Todoist webhooks.
    
    Processes webhook events for:
    - Task lifecycle events (created, updated, completed, deleted)
    - Project events
    - Real-time synchronization
    - Automation triggers
    """
    try:
        async with todoist_service:
            webhook_handler = TodoistWebhookHandler(
                todoist_service=todoist_service,
                webhook_secret=settings.TODOIST_WEBHOOK_SECRET
            )
            
            result = await webhook_handler.process_webhook(request)
            
            return WebhookResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


# Utility endpoints
@router.post("/initialize")
async def initialize_hsn_workspace(
    todoist_service: TodoistService = Depends(get_todoist_service)
):
    """
    Initialize HSN workspace with business entity projects and labels.
    
    This endpoint sets up:
    - Business entity projects (7Space, AM Consulting, HSN)
    - Standard HSN operational labels
    - Default configurations
    """
    try:
        async with todoist_service:
            project_ids = await todoist_service.initialize_hsn_workspace()
            
            return {
                "message": "HSN workspace initialized successfully",
                "project_ids": project_ids
            }
    except Exception as e:
        logger.error(f"Failed to initialize HSN workspace: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Workspace initialization failed: {str(e)}"
        )


@router.get("/sync/monitoring")
async def sync_with_monitoring(
    background_tasks: BackgroundTasks,
    todoist_service: TodoistService = Depends(get_todoist_service)
):
    """
    Sync with HSN server monitoring systems.
    
    Creates tasks automatically from:
    - System alerts
    - Performance warnings
    - Security notifications
    - Deployment status
    """
    try:
        async with todoist_service:
            sync_summary = await todoist_service.sync_with_server_monitoring()
            
            return {
                "message": "Monitoring sync completed",
                "summary": sync_summary
            }
    except Exception as e:
        logger.error(f"Monitoring sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring sync failed: {str(e)}")


# Background task functions
async def _log_task_creation(
    task_id: str, 
    business_entity: Optional[BusinessEntity], 
    automation_source: Optional[str]
):
    """Log task creation for analytics."""
    logger.info(f"Task created - ID: {task_id}, Entity: {business_entity}, Source: {automation_source}")
    # Additional analytics logging would go here
