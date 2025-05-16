"""Base agent implementation for The HigherSelf Network Server.

Provides common functionality for all agents in the network, including registration,
logging, task management, and standard interfaces for event processing.
"""

import asyncio
import json
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

from utils.logging_utils import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

from models.base import AgentCapability, ApiPlatform
from models.notion_db_models import Agent, Task, WorkflowInstance
from services.notion_service import NotionService


class BaseAgent(ABC):
    """Abstract base class for all agents in the HigherSelf network.

    Provides common functionality, enforces implementation of required methods,
    and standardizes agent management operations across the platform.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        version: str = "1.0.0",
        capabilities: Optional[List[AgentCapability]] = None,
        apis_utilized: Optional[List[ApiPlatform]] = None,
        business_entities: Optional[List[str]] = None,
        notion_service: Optional[NotionService] = None,
    ):
        """Initialize the base agent with core attributes.

        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name for this agent
            description: Detailed description of agent responsibilities
            version: Semantic version string (e.g., "1.0.0")
            capabilities: List of agent capabilities from AgentCapability enum
            apis_utilized: List of API platforms utilized from ApiPlatform enum
            business_entities: List of business entity IDs this agent is associated with
            notion_service: NotionService instance or None to create from environment

        Raises:
            ValueError: If agent_id is empty or invalid
        """
        if not agent_id:
            raise ValueError("Agent ID cannot be empty")
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.version = version
        self.capabilities = capabilities or []
        self.apis_utilized = apis_utilized or []
        self.business_entities = business_entities or []

        # Set up logger for this agent
        self.logger = logger.bind(agent_id=agent_id)

        # Initialize Notion service if provided, otherwise create from environment
        self._notion_service = notion_service

        # Keep track of this agent's Notion page ID if registered
        self.notion_page_id = None

        self.logger.info(
            f"Agent {self.agent_id} ({self.name}) v{self.version} initialized"
        )

    @property
    async def notion_service(self) -> NotionService:
        """Get or create the Notion service.

        Lazily initializes the Notion service if it hasn't been created yet.

        Returns:
            NotionService: The Notion service instance

        Raises:
            EnvironmentError: If environment variables for Notion API are missing
        """
        if self._notion_service is None:
            self._notion_service = NotionService.from_env()
        return self._notion_service

    async def register_in_notion(self) -> Optional[str]:
        """Register this agent in the Agent Registry Notion database.

        Creates a new record in the Agent Registry database or updates an existing one.
        This ensures the agent's metadata is properly tracked in the central registry.

        Returns:
            str: Notion page ID of the created/updated agent record

        Raises:
            Exception: If registration fails due to Notion API errors
        """
        notion_svc = await self.notion_service

        # Check if agent already exists
        filter_conditions = {
            "property": "agent_id",
            "rich_text": {"equals": self.agent_id},
        }

        existing_agents = await notion_svc.query_database(Agent, filter_conditions)

        if existing_agents:
            agent_record = existing_agents[0]
            self.notion_page_id = agent_record.page_id
            self.logger.info(
                f"Agent {self.agent_id} already registered in Notion with page ID: {self.notion_page_id}"
            )

            # Update the existing record
            agent_record.name = self.name
            agent_record.description = self.description
            agent_record.version = self.version
            agent_record.capabilities = self.capabilities
            agent_record.primary_apis_utilized = self.apis_utilized
            agent_record.business_entity_association = self.business_entities

            await notion_svc.update_page(agent_record)
            return self.notion_page_id

        # Create new agent record
        agent_record = Agent(
            agent_id=self.agent_id,
            name=self.name,
            description=self.description,
            version=self.version,
            status=self.get_status(),
            capabilities=self.capabilities,
            primary_apis_utilized=self.apis_utilized,
            business_entity_association=self.business_entities,
            runtime_environment="Docker (HigherSelf Network Server)",
            source_code_location=f"The HigherSelf Network Server/{self.agent_id}",
        )

        self.notion_page_id = await notion_svc.create_page(agent_record)
        self.logger.info(
            f"Registered agent {self.agent_id} in Notion with page ID: {self.notion_page_id}"
        )

        return self.notion_page_id

    def get_status(self) -> str:
        """Get the current status of this agent.

        Returns:
            str: The current status ("Deployed", "Inactive", "Error", etc.)
        """
        return "Deployed"

    async def log_action(
        self,
        workflow_instance: WorkflowInstance,
        action: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log an action in the workflow instance history.

        Records an action performed by this agent in the workflow's history log,
        which is stored in Notion. The action includes a timestamp and the agent ID.

        Args:
            workflow_instance: The workflow instance to log to
            action: Description of the action performed
            details: Optional dictionary of additional details about the action

        Returns:
            bool: True if logging was successful, False otherwise

        Raises:
            ValueError: If workflow_instance is None or invalid
        """
        if not workflow_instance:
            raise ValueError("Cannot log action: workflow_instance cannot be None")
        notion_svc = await self.notion_service

        # Add agent identifier to the log entry
        action = f"[{self.agent_id}] {action}"

        # Handle None details
        details_dict = details or {}

        return await notion_svc.append_to_history_log(
            workflow_instance, action, details_dict
        )

    async def update_workflow_state(
        self,
        workflow_instance: WorkflowInstance,
        new_state: str,
        action_description: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update a workflow instance's state and log the transition.

        Changes the workflow state and records the transition in the history log.
        Updates the last_transition_date to the current time.

        Args:
            workflow_instance: The workflow instance to update
            new_state: The new state to set for the workflow
            action_description: Description of why the state is changing
            details: Optional dictionary with additional details about the transition

        Returns:
            bool: True if update was successful, False otherwise

        Raises:
            ValueError: If workflow_instance is None or new_state is empty
        """
        if not workflow_instance:
            raise ValueError("Cannot update workflow: workflow_instance cannot be None")
        if not new_state:
            raise ValueError("Cannot update workflow: new_state cannot be empty")
        notion_svc = await self.notion_service

        # Update the instance's state
        workflow_instance.current_state = new_state
        workflow_instance.last_transition_date = datetime.now()
        workflow_instance.add_history_entry(
            action=f"[{self.agent_id}] {action_description}", details=details or {}
        )

        # Update the instance in Notion
        return await notion_svc.update_page(workflow_instance)

    async def create_task(
        self,
        workflow_instance: WorkflowInstance,
        task_name: str,
        description: str,
        assigned_to: Optional[str] = None,
        due_date: Optional[datetime] = None,
        priority: str = "Medium",
    ) -> Task:
        """Create a task in the Master Tasks Database.

        Creates a new task associated with a workflow instance and logs the
        task creation in the workflow history.

        Args:
            workflow_instance: Related workflow instance the task belongs to
            task_name: Clear, descriptive name of the task
            description: Detailed task description and instructions
            assigned_to: Optional user ID or name to assign the task to
            due_date: Optional deadline for task completion
            priority: Task priority level ("Low", "Medium", "High", "Urgent")

        Returns:
            Task: Created Task object with populated metadata

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if not workflow_instance:
            raise ValueError("Cannot create task: workflow_instance cannot be None")
        if not task_name:
            raise ValueError("Cannot create task: task_name cannot be empty")
        notion_svc = await self.notion_service

        return await notion_svc.create_task_from_workflow(
            workflow_instance=workflow_instance,
            task_name=task_name,
            description=description,
            assigned_to=assigned_to,
            due_date=due_date,
            priority=priority,
        )

    @abstractmethod
    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an event received by this agent.

        This method must be implemented by all agent subclasses to handle
        different types of events relevant to the agent's responsibilities.

        Args:
            event_type: Type of event to process
            event_data: Dictionary containing event parameters and data

        Returns:
            Dict[str, Any]: Processing result with status and relevant data

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Agents must implement process_event method")

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check the health status of this agent.

        Performs a comprehensive health check of the agent and its dependencies.
        This method must be implemented by all agent subclasses.

        Returns:
            Dict[str, Any]: Health check result containing at minimum:
                - status: "healthy", "degraded", or "unhealthy"
                - timestamp: ISO format timestamp of the check
                - details: Additional health information specific to the agent

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Agents must implement check_health method")
