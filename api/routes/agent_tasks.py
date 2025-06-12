"""
Agent Tasks API Routes

This module provides API endpoints for managing agent tasks and integrating with Notion.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from config.settings import settings
from services.agent_manager import get_agent_manager
from tools.notion_agent_tasks import AgentTask, NotionTasksManager

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


# Models
class TaskParameters(BaseModel):
    """Model for task parameters."""

    class Config:
        extra = "allow"  # Allow extra fields


class TaskRequest(BaseModel):
    """Model for task request."""

    agent_id: str
    task_type: str
    priority: str = "medium"
    due_date: Optional[str] = None
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None


class TaskResponse(BaseModel):
    """Model for task response."""

    task_id: str
    agent_id: str
    task_type: str
    status: str
    result: Optional[str] = None
    created_at: str
    notion_url: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Model for feedback request."""

    rating: int
    comments: Optional[str] = None


# Routes
@router.post("/run", response_model=TaskResponse)
async def run_agent_task(request: TaskRequest) -> Dict[str, Any]:
    """
    Run an agent task and create a Notion entry.

    Args:
        request: The task request.

    Returns:
        The task response.
    """
    # Generate a unique task ID
    task_id = f"task_{uuid.uuid4().hex[:8]}"

    # Create the agent task
    task = AgentTask(
        task_id=task_id,
        agent_id=request.agent_id,
        task_type=request.task_type,
        priority=request.priority,
        due_date=request.due_date,
        description=request.description,
        parameters=request.parameters,
        created_by=request.created_by,
        created_at=datetime.now().isoformat(),
    )

    # Create the task in Notion
    notion_manager = NotionTasksManager()
    try:
        notion_page_id = notion_manager.create_task(task)
        task.notion_page_id = notion_page_id
    except Exception as e:
        # Log the error but continue processing
        print(f"Error creating Notion task: {e}")

    # Process the task with the appropriate agent
    agent_manager = get_agent_manager()
    try:
        result = await agent_manager.process_task(
            agent_id=request.agent_id,
            task_type=request.task_type,
            parameters=request.parameters,
            description=request.description,
        )

        # Update the task with the result
        task.result = result
        task.status = "completed"

        # Update the Notion task
        if task.notion_page_id:
            notion_manager.update_task_result(task.task_id, result)

    except Exception as e:
        # Handle task processing error
        error_message = f"Error processing task: {str(e)}"
        task.result = error_message
        task.status = "failed"

        # Update the Notion task with the error
        if task.notion_page_id:
            notion_manager.update_task_result(task.task_id, error_message, "failed")

        # Raise HTTP exception
        raise HTTPException(status_code=500, detail=error_message)

    # Prepare the response
    response = {
        "task_id": task.task_id,
        "agent_id": task.agent_id,
        "task_type": task.task_type,
        "status": task.status,
        "result": task.result,
        "created_at": task.created_at,
    }

    # Add Notion URL if available
    if task.notion_page_id:
        response[
            "notion_url"
        ] = f"https://notion.so/{task.notion_page_id.replace('-', '')}"

    return response


@router.post("/tasks/{task_id}/feedback")
async def submit_feedback(task_id: str, feedback: FeedbackRequest) -> Dict[str, str]:
    """
    Submit feedback for a task.

    Args:
        task_id: The ID of the task.
        feedback: The feedback request.

    Returns:
        A success message.
    """
    # Validate the rating
    if feedback.rating < 1 or feedback.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    # Update the feedback in Notion
    notion_manager = NotionTasksManager()
    try:
        notion_manager.update_feedback(task_id, feedback.rating, feedback.comments)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating feedback: {str(e)}"
        )

    return {"message": "Feedback submitted successfully"}


@router.get("/tasks/recent", response_model=List[Dict[str, Any]])
async def get_recent_tasks(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent tasks.

    Args:
        limit: The maximum number of tasks to return.

    Returns:
        A list of recent tasks.
    """
    notion_manager = NotionTasksManager()
    try:
        tasks = notion_manager.get_recent_tasks(limit)
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting recent tasks: {str(e)}"
        )


@router.get("/status/{agent_id}")
async def get_agent_status(agent_id: str) -> Dict[str, Any]:
    """
    Get the status of an agent.

    Args:
        agent_id: The ID of the agent.

    Returns:
        The agent status.
    """
    agent_manager = get_agent_manager()
    try:
        status = await agent_manager.get_agent_status(agent_id)
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting agent status: {str(e)}"
        )
