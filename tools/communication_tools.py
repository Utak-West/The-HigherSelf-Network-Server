"""
Communication and workflow tools for LangChain agents.
"""

import json
from datetime import datetime
from typing import Any, Dict, Type

from langchain.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field

from services.redis_service import redis_service


class AgentMessageInput(BaseModel):
    target_agent: str = Field(
        description="Target agent name (Nyra, Solari, Ruvo, Liora, Sage, Elan, Zevi, Grace, Atlas)"
    )
    message: str = Field(description="Message content")
    priority: str = Field(
        default="normal", description="Message priority: low, normal, high, urgent"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context data"
    )


class AgentCommunicationTool(BaseTool):
    name = "send_agent_message"
    description = "Send a message to another agent in the network. Useful for coordination, delegation, or information sharing."
    args_schema: Type[BaseModel] = AgentMessageInput

    def __init__(self, sender_agent: str):
        super().__init__()
        self.sender_agent = sender_agent

    def _run(
        self,
        target_agent: str,
        message: str,
        priority: str = "normal",
        context: Dict[str, Any] = None,
    ) -> str:
        """Send message to another agent via Redis pub/sub."""
        try:
            if context is None:
                context = {}

            message_data = {
                "from": self.sender_agent,
                "to": target_agent,
                "message": message,
                "priority": priority,
                "context": context,
                "timestamp": datetime.utcnow().isoformat(),
                "message_id": f"{self.sender_agent}_{target_agent}_{int(datetime.utcnow().timestamp())}",
            }

            # Publish to agent-specific channel
            channel = f"higherself:agents:{target_agent.lower()}"
            redis_service.publish(channel, json.dumps(message_data))

            # Also store in a general message queue for persistence
            redis_service.lpush("higherself:messages:queue", json.dumps(message_data))

            logger.info(
                f"Message sent from {self.sender_agent} to {target_agent} (priority: {priority})"
            )
            return f"Message sent to {target_agent} successfully"

        except Exception as e:
            logger.error(
                f"Error sending message from {self.sender_agent} to {target_agent}: {e}"
            )
            return f"Error sending message: {str(e)}"

    async def _arun(
        self,
        target_agent: str,
        message: str,
        priority: str = "normal",
        context: Dict[str, Any] = None,
    ) -> str:
        """Async version."""
        return self._run(target_agent, message, priority, context)


class WorkflowTriggerInput(BaseModel):
    workflow_name: str = Field(description="Workflow name to trigger")
    context: Dict[str, Any] = Field(description="Workflow context data")
    priority: str = Field(
        default="normal", description="Workflow priority: low, normal, high, urgent"
    )
    scheduled_time: str = Field(
        default="", description="Optional scheduled execution time (ISO format)"
    )


class WorkflowTriggerTool(BaseTool):
    name = "trigger_workflow"
    description = "Trigger a workflow with context data. Useful for starting automated processes or complex multi-step operations."
    args_schema: Type[BaseModel] = WorkflowTriggerInput

    def __init__(self, triggering_agent: str = "unknown"):
        super().__init__()
        self.triggering_agent = triggering_agent

    def _run(
        self,
        workflow_name: str,
        context: Dict[str, Any],
        priority: str = "normal",
        scheduled_time: str = "",
    ) -> str:
        """Trigger a workflow."""
        try:
            workflow_data = {
                "workflow": workflow_name,
                "context": context,
                "priority": priority,
                "triggered_by": self.triggering_agent,
                "timestamp": datetime.utcnow().isoformat(),
                "scheduled_time": scheduled_time,
                "workflow_id": f"{workflow_name}_{int(datetime.utcnow().timestamp())}",
            }

            # Add to workflow queue based on priority
            queue_name = f"higherself:workflows:{priority}"
            redis_service.lpush(queue_name, json.dumps(workflow_data))

            # Also add to general workflow tracking
            redis_service.hset(
                f"higherself:workflow_tracking:{workflow_data['workflow_id']}",
                mapping={
                    "status": "queued",
                    "data": json.dumps(workflow_data),
                    "created_at": workflow_data["timestamp"],
                },
            )

            logger.info(
                f"Workflow '{workflow_name}' triggered by {self.triggering_agent} (priority: {priority})"
            )
            return f"Triggered workflow: {workflow_name} (ID: {workflow_data['workflow_id']})"

        except Exception as e:
            logger.error(f"Error triggering workflow '{workflow_name}': {e}")
            return f"Error triggering workflow: {str(e)}"

    async def _arun(
        self,
        workflow_name: str,
        context: Dict[str, Any],
        priority: str = "normal",
        scheduled_time: str = "",
    ) -> str:
        """Async version."""
        return self._run(workflow_name, context, priority, scheduled_time)


class TaskCreationInput(BaseModel):
    title: str = Field(description="Task title")
    description: str = Field(description="Task description")
    assignee: str = Field(description="Agent or person to assign the task to")
    priority: str = Field(
        default="medium", description="Task priority: low, medium, high, urgent"
    )
    due_date: str = Field(
        default="",
        description="Due date (ISO format or relative like 'tomorrow', 'next week')",
    )
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional task context"
    )


class TaskCreationTool(BaseTool):
    name = "create_task"
    description = "Create a new task and assign it to an agent or person. Useful for delegating work or tracking follow-ups."
    args_schema: Type[BaseModel] = TaskCreationInput

    def __init__(self, creating_agent: str = "unknown"):
        super().__init__()
        self.creating_agent = creating_agent

    def _run(
        self,
        title: str,
        description: str,
        assignee: str,
        priority: str = "medium",
        due_date: str = "",
        context: Dict[str, Any] = None,
    ) -> str:
        """Create a new task."""
        try:
            if context is None:
                context = {}

            task_data = {
                "title": title,
                "description": description,
                "assignee": assignee,
                "priority": priority,
                "due_date": due_date,
                "context": context,
                "created_by": self.creating_agent,
                "created_at": datetime.utcnow().isoformat(),
                "status": "pending",
                "task_id": f"task_{int(datetime.utcnow().timestamp())}",
            }

            # Add to task queue
            redis_service.lpush("higherself:tasks:queue", json.dumps(task_data))

            # Store task details
            redis_service.hset(
                f"higherself:task:{task_data['task_id']}",
                mapping={
                    "data": json.dumps(task_data),
                    "status": "pending",
                    "created_at": task_data["created_at"],
                },
            )

            # Notify assignee if it's an agent
            if assignee in [
                "Nyra",
                "Solari",
                "Ruvo",
                "Liora",
                "Sage",
                "Elan",
                "Zevi",
                "Grace",
                "Atlas",
            ]:
                notification_data = {
                    "from": self.creating_agent,
                    "to": assignee,
                    "message": f"New task assigned: {title}",
                    "priority": priority,
                    "context": {
                        "task_id": task_data["task_id"],
                        "task_data": task_data,
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                }

                channel = f"higherself:agents:{assignee.lower()}"
                redis_service.publish(channel, json.dumps(notification_data))

            logger.info(
                f"Task '{title}' created by {self.creating_agent} and assigned to {assignee}"
            )
            return f"Created task: {title} (ID: {task_data['task_id']}) assigned to {assignee}"

        except Exception as e:
            logger.error(f"Error creating task '{title}': {e}")
            return f"Error creating task: {str(e)}"

    async def _arun(
        self,
        title: str,
        description: str,
        assignee: str,
        priority: str = "medium",
        due_date: str = "",
        context: Dict[str, Any] = None,
    ) -> str:
        """Async version."""
        return self._run(title, description, assignee, priority, due_date, context)


class NotificationInput(BaseModel):
    recipient: str = Field(description="Notification recipient (agent name or 'all')")
    message: str = Field(description="Notification message")
    notification_type: str = Field(
        default="info", description="Notification type: info, warning, error, success"
    )
    channels: list = Field(
        default_factory=lambda: ["redis"],
        description="Notification channels: redis, email, slack",
    )


class NotificationTool(BaseTool):
    name = "send_notification"
    description = "Send notifications to agents or external systems. Useful for alerts, updates, or important announcements."
    args_schema: Type[BaseModel] = NotificationInput

    def __init__(self, sending_agent: str = "unknown"):
        super().__init__()
        self.sending_agent = sending_agent

    def _run(
        self,
        recipient: str,
        message: str,
        notification_type: str = "info",
        channels: list = None,
    ) -> str:
        """Send a notification."""
        try:
            if channels is None:
                channels = ["redis"]

            notification_data = {
                "from": self.sending_agent,
                "to": recipient,
                "message": message,
                "type": notification_type,
                "channels": channels,
                "timestamp": datetime.utcnow().isoformat(),
                "notification_id": f"notif_{int(datetime.utcnow().timestamp())}",
            }

            # Send via Redis (always available)
            if "redis" in channels:
                if recipient == "all":
                    # Broadcast to all agents
                    redis_service.publish(
                        "higherself:notifications:broadcast",
                        json.dumps(notification_data),
                    )
                else:
                    # Send to specific recipient
                    channel = f"higherself:notifications:{recipient.lower()}"
                    redis_service.publish(channel, json.dumps(notification_data))

            # Store notification for tracking
            redis_service.hset(
                f"higherself:notification:{notification_data['notification_id']}",
                mapping={
                    "data": json.dumps(notification_data),
                    "sent_at": notification_data["timestamp"],
                },
            )

            logger.info(
                f"Notification sent from {self.sending_agent} to {recipient} (type: {notification_type})"
            )
            return f"Notification sent to {recipient} successfully"

        except Exception as e:
            logger.error(f"Error sending notification to {recipient}: {e}")
            return f"Error sending notification: {str(e)}"

    async def _arun(
        self,
        recipient: str,
        message: str,
        notification_type: str = "info",
        channels: list = None,
    ) -> str:
        """Async version."""
        return self._run(recipient, message, notification_type, channels)
