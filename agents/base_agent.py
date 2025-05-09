"""
Base agent implementation for the Windsurf Agent Network.
Provides common functionality for all agents in the network.
"""

import os
import json
import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Type
from datetime import datetime
from loguru import logger

from models.base import AgentCapability, ApiPlatform
from models.notion_db_models import Agent, WorkflowInstance, Task
from services.notion_service import NotionService


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Windsurf network.
    Provides common functionality and enforces implementation of required methods.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        version: str = "1.0.0",
        capabilities: List[AgentCapability] = None,
        apis_utilized: List[ApiPlatform] = None,
        business_entities: List[str] = None,
        notion_service: Optional[NotionService] = None
    ):
        """
        Initialize the base agent with core attributes.
        
        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name
            description: Agent description and responsibilities
            version: Agent version
            capabilities: List of agent capabilities
            apis_utilized: List of API platforms utilized
            business_entities: List of business entity IDs this agent is associated with
            notion_service: NotionService instance or None to create from environment
        """
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
        
        self.logger.info(f"Agent {agent_id} ({name}) initialized")
    
    @property
    async def notion_service(self) -> NotionService:
        """Get or create the Notion service."""
        if self._notion_service is None:
            self._notion_service = NotionService.from_env()
        return self._notion_service
    
    async def register_in_notion(self) -> str:
        """
        Register this agent in the Agent Registry Notion database.
        
        Returns:
            Notion page ID of the created/updated agent record
        """
        notion_svc = await self.notion_service
        
        # Check if agent already exists
        filter_conditions = {
            "property": "agent_id",
            "rich_text": {
                "equals": self.agent_id
            }
        }
        
        existing_agents = await notion_svc.query_database(Agent, filter_conditions)
        
        if existing_agents:
            agent_record = existing_agents[0]
            self.notion_page_id = agent_record.page_id
            self.logger.info(f"Agent {self.agent_id} already registered in Notion with page ID: {self.notion_page_id}")
            
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
            source_code_location=f"The HigherSelf Network Server/{self.agent_id}"
        )
        
        self.notion_page_id = await notion_svc.create_page(agent_record)
        self.logger.info(f"Registered agent {self.agent_id} in Notion with page ID: {self.notion_page_id}")
        
        return self.notion_page_id
    
    def get_status(self) -> str:
        """Get the current status of this agent."""
        return "Deployed"
    
    async def log_action(
        self, 
        workflow_instance: WorkflowInstance, 
        action: str, 
        details: Dict[str, Any] = None
    ) -> bool:
        """
        Log an action in the workflow instance history.
        
        Args:
            workflow_instance: The workflow instance to log to
            action: Description of the action
            details: Optional details about the action
            
        Returns:
            True if logging was successful
        """
        notion_svc = await self.notion_service
        
        # Add agent identifier to the log entry
        action = f"[{self.agent_id}] {action}"
        
        return await notion_svc.append_to_history_log(workflow_instance, action, details)
    
    async def update_workflow_state(
        self,
        workflow_instance: WorkflowInstance,
        new_state: str,
        action_description: str,
        details: Dict[str, Any] = None
    ) -> bool:
        """
        Update a workflow instance's state and log the transition.
        
        Args:
            workflow_instance: The workflow instance to update
            new_state: The new state
            action_description: Description of the state transition
            details: Optional details about the transition
            
        Returns:
            True if update was successful
        """
        notion_svc = await self.notion_service
        
        # Update the instance's state
        workflow_instance.current_state = new_state
        workflow_instance.last_transition_date = datetime.now()
        workflow_instance.add_history_entry(
            action=f"[{self.agent_id}] {action_description}",
            details=details
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
        priority: str = "Medium"
    ) -> Task:
        """
        Create a task in the Master Tasks Database.
        
        Args:
            workflow_instance: Related workflow instance
            task_name: Name of the task
            description: Task description
            assigned_to: Optional assignee
            due_date: Optional due date
            priority: Task priority
            
        Returns:
            Created Task
        """
        notion_svc = await self.notion_service
        
        return await notion_svc.create_task_from_workflow(
            workflow_instance=workflow_instance,
            task_name=task_name,
            description=description,
            assigned_to=assigned_to,
            due_date=due_date,
            priority=priority
        )
    
    @abstractmethod
    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an event received by this agent.
        
        Args:
            event_type: Type of event
            event_data: Event data
            
        Returns:
            Processing result
        """
        raise NotImplementedError("Agents must implement process_event method")
    
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.
        
        Returns:
            Health check result
        """
        raise NotImplementedError("Agents must implement check_health method")
