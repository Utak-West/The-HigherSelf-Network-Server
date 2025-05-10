"""
State Machine implementation for the Advanced Agentic Workflow Engine.

This module provides a LangGraph-inspired state machine for orchestrating
complex workflows between specialized agents. All state data is persisted
in Notion databases, maintaining it as the central hub for all workflow data.
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Union, Set, Tuple
from pydantic import BaseModel, Field
from loguru import logger

from models.notion_db_models import WorkflowInstance
from services.notion_service import NotionService


class WorkflowState(BaseModel):
    """
    Represents a single state in a workflow state machine.
    All state information is persisted in Notion.
    """
    name: str
    description: str
    is_terminal: bool = False
    available_transitions: List[str] = Field(default_factory=list)
    agent_assignments: List[str] = Field(default_factory=list)
    required_data_points: List[str] = Field(default_factory=list)
    
    class Config:
        frozen = True


class StateTransition(BaseModel):
    """
    Represents a transition between workflow states.
    Conditions and triggers determine when transitions occur.
    """
    from_state: str
    to_state: str
    name: str
    description: str
    conditions: List[str] = Field(default_factory=list)
    triggers: List[str] = Field(default_factory=list)
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    transition_handler: Optional[str] = None
    
    class Config:
        frozen = True


class WorkflowStateMachine:
    """
    LangGraph-inspired state machine for orchestrating complex workflows.
    Stores all state and transition data in Notion databases.
    """
    
    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: str,
        states: Dict[str, WorkflowState],
        transitions: List[StateTransition],
        initial_state: str,
        notion_service: Optional[NotionService] = None
    ):
        """
        Initialize the workflow state machine.
        
        Args:
            workflow_id: Unique identifier for this workflow definition
            name: Human-readable name
            description: Workflow description
            states: Dictionary of workflow states keyed by state name
            transitions: List of state transitions
            initial_state: Name of the initial state
            notion_service: Optional NotionService instance or None to create from environment
        """
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.states = states
        self.transitions = transitions
        self.initial_state = initial_state
        self._notion_service = notion_service
        
        # Validate the state machine structure
        self._validate()
        
        # Track all running instances of this workflow
        self.active_instances: Dict[str, str] = {}  # instance_id -> current_state
        
        # Set up logger
        self.logger = logger.bind(workflow_id=workflow_id)
        self.logger.info(f"Workflow '{name}' initialized with {len(states)} states and {len(transitions)} transitions")
        
    def _validate(self):
        """Validate the state machine structure."""
        # Check that initial state exists
        if self.initial_state not in self.states:
            raise ValueError(f"Initial state '{self.initial_state}' not found in states")
        
        # Check that all transitions reference valid states
        for transition in self.transitions:
            if transition.from_state not in self.states:
                raise ValueError(f"Transition '{transition.name}' references unknown from_state '{transition.from_state}'")
            if transition.to_state not in self.states:
                raise ValueError(f"Transition '{transition.name}' references unknown to_state '{transition.to_state}'")
            
        # Check that all states have valid available transitions
        for state_name, state in self.states.items():
            for transition_name in state.available_transitions:
                if not any(t.name == transition_name for t in self.transitions):
                    raise ValueError(f"State '{state_name}' references unknown transition '{transition_name}'")
    
    @property
    async def notion_service(self) -> NotionService:
        """Get or create the Notion service."""
        if self._notion_service is None:
            self._notion_service = NotionService.from_env()
        return self._notion_service
    
    async def create_instance(
        self,
        business_entity_id: str,
        context_data: Dict[str, Any] = None,
        instance_id: Optional[str] = None
    ) -> WorkflowInstance:
        """
        Create a new instance of this workflow in Notion.
        
        Args:
            business_entity_id: Associated business entity ID
            context_data: Initial context data for the workflow
            instance_id: Optional instance ID, generated if not provided
            
        Returns:
            Created WorkflowInstance
        """
        notion_svc = await self.notion_service
        
        instance_id = instance_id or str(uuid.uuid4())
        now = datetime.now()
        
        # Create the workflow instance in Notion
        instance = WorkflowInstance(
            instance_id=instance_id,
            workflow_id=self.workflow_id,
            workflow_name=self.name,
            business_entity_id=business_entity_id,
            current_state=self.initial_state,
            status="Active",
            context_data=context_data or {},
            created_at=now,
            last_transition_date=now,
            history_log=[f"Workflow instance created in state: {self.initial_state}"]
        )
        
        instance_page_id = await notion_svc.create_page(instance)
        instance.page_id = instance_page_id
        
        # Add to active instances
        self.active_instances[instance_id] = self.initial_state
        
        self.logger.info(f"Created workflow instance {instance_id} in state {self.initial_state}")
        return instance
    
    async def get_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """
        Retrieve a workflow instance from Notion.
        
        Args:
            instance_id: Workflow instance ID
            
        Returns:
            WorkflowInstance if found, None otherwise
        """
        notion_svc = await self.notion_service
        
        # Query for the instance
        filter_conditions = {
            "property": "instance_id",
            "rich_text": {
                "equals": instance_id
            }
        }
        
        results = await notion_svc.query_database(WorkflowInstance, filter_conditions)
        
        if not results:
            self.logger.warning(f"Workflow instance {instance_id} not found")
            return None
        
        instance = results[0]
        
        # Update active instances cache
        self.active_instances[instance_id] = instance.current_state
        
        return instance
    
    async def transition(
        self,
        instance_id: str,
        transition_name: str,
        agent_id: str,
        action_description: str = None,
        transition_data: Dict[str, Any] = None
    ) -> Tuple[bool, WorkflowInstance]:
        """
        Transition a workflow instance to a new state in Notion.
        
        Args:
            instance_id: Workflow instance ID
            transition_name: Name of the transition to execute
            agent_id: ID of the agent executing the transition
            action_description: Optional description of the action
            transition_data: Optional data related to the transition
            
        Returns:
            Tuple of (success, updated instance)
        """
        notion_svc = await self.notion_service
        
        # Get the instance
        instance = await self.get_instance(instance_id)
        if not instance:
            return False, None
        
        # Get current state
        current_state_name = instance.current_state
        current_state = self.states.get(current_state_name)
        
        if not current_state:
            self.logger.error(f"Current state '{current_state_name}' not found in workflow definition")
            return False, instance
        
        # Check if transition is valid from current state
        if transition_name not in current_state.available_transitions:
            self.logger.error(f"Transition '{transition_name}' not available from state '{current_state_name}'")
            return False, instance
        
        # Find the transition
        transition = next((t for t in self.transitions if t.name == transition_name), None)
        if not transition:
            self.logger.error(f"Transition '{transition_name}' not found in workflow definition")
            return False, instance
        
        # Get target state
        target_state = self.states.get(transition.to_state)
        if not target_state:
            self.logger.error(f"Target state '{transition.to_state}' not found in workflow definition")
            return False, instance
        
        # Prepare the transition description
        if not action_description:
            action_description = f"Transitioned from {current_state_name} to {transition.to_state} via {transition_name}"
        
        # Update the instance state in Notion
        instance.current_state = transition.to_state
        instance.last_transition_date = datetime.now()
        instance.add_history_entry(
            action=f"[{agent_id}] {action_description}",
            details=transition_data
        )
        
        # If target state is terminal, update status accordingly
        if target_state.is_terminal:
            instance.status = "Completed"
        
        # Update context data if provided
        if transition_data and isinstance(transition_data, dict):
            for key, value in transition_data.items():
                instance.context_data[key] = value
        
        # Update in Notion
        success = await notion_svc.update_page(instance)
        
        if success:
            # Update active instances cache
            self.active_instances[instance_id] = transition.to_state
            
            self.logger.info(f"Transitioned instance {instance_id} from {current_state_name} to {transition.to_state}")
            
            # If terminal state, remove from active instances
            if target_state.is_terminal:
                self.active_instances.pop(instance_id, None)
                self.logger.info(f"Workflow instance {instance_id} completed")
        else:
            self.logger.error(f"Failed to transition instance {instance_id}")
        
        return success, instance
    
    async def get_active_instances(self) -> List[WorkflowInstance]:
        """
        Get all active instances of this workflow from Notion.
        
        Returns:
            List of active WorkflowInstance objects
        """
        notion_svc = await self.notion_service
        
        # Query for active instances of this workflow
        filter_conditions = {
            "and": [
                {
                    "property": "workflow_id",
                    "rich_text": {
                        "equals": self.workflow_id
                    }
                },
                {
                    "property": "status",
                    "select": {
                        "equals": "Active"
                    }
                }
            ]
        }
        
        instances = await notion_svc.query_database(WorkflowInstance, filter_conditions)
        
        # Update active instances cache
        for instance in instances:
            self.active_instances[instance.instance_id] = instance.current_state
        
        return instances
    
    async def visualize(self, instance_id: Optional[str] = None) -> str:
        """
        Generate a Mermaid diagram for this workflow.
        If instance_id is provided, highlights the current state.
        
        Args:
            instance_id: Optional workflow instance ID to highlight current state
            
        Returns:
            Mermaid diagram code
        """
        # Get current state if instance_id provided
        current_state = None
        if instance_id:
            instance = await self.get_instance(instance_id)
            if instance:
                current_state = instance.current_state
        
        # Generate diagram
        mermaid = "stateDiagram-v2\n"
        
        # Add states
        for state_name, state in self.states.items():
            if state.is_terminal:
                mermaid += f"    state \"{state_name}\" as {state_name.replace(' ', '_')}\n"
            elif current_state and state_name == current_state:
                mermaid += f"    state \"{state_name}\" as {state_name.replace(' ', '_')} <<highlight>>\n"
            else:
                mermaid += f"    state \"{state_name}\" as {state_name.replace(' ', '_')}\n"
        
        # Add transitions
        for transition in self.transitions:
            from_state = transition.from_state.replace(' ', '_')
            to_state = transition.to_state.replace(' ', '_')
            mermaid += f"    {from_state} --> {to_state}: {transition.name}\n"
        
        # Add start and end markers
        mermaid += f"    [*] --> {self.initial_state.replace(' ', '_')}\n"
        
        # Add end transitions for terminal states
        for state_name, state in self.states.items():
            if state.is_terminal:
                mermaid += f"    {state_name.replace(' ', '_')} --> [*]\n"
        
        return mermaid