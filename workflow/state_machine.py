"""
State Machine implementation for the Advanced Agentic Workflow Engine.

This module provides a LangGraph-inspired state machine for orchestrating
complex workflows between specialized agents. All state data is persisted
in Notion databases, maintaining it as the central hub for all workflow data.
"""

import asyncio
import functools
import random
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from pydantic import BaseModel, Field, field_validator, logger, loguru

from knowledge import SemanticSearch, get_semantic_search
from models.notion_db_models import WorkflowInstance
from services.notion_service import NotionService
from workflow.transitions import ConditionGroup, TransitionCondition, TransitionTrigger

# Type variable for state data
T = TypeVar('T')


class AgentAssignment(BaseModel):
    """
    Defines how agents are assigned to a workflow state.
    Supports both static assignments and dynamic rules.
    """
    agent_id: Optional[str] = None
    agent_role: Optional[str] = None
    assignment_rule: Optional[str] = None
    fallback_agent_ids: List[str] = Field(default_factory=list)
    priority: int = 1
    selection_strategy: str = "first_available"  # first_available, round_robin, load_balancing
    context_dependent: bool = False
    context_condition: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = None

@field_validator('selection_strategy', mode='before')    def validate_selection_strategy(cls, v):
        valid_strategies = ['first_available', 'round_robin', 'load_balancing', 'semantic_match']
        if v not in valid_strategies:
            raise ValueError(f"Strategy must be one of {valid_strategies}")
        return v


class StateTimeout(BaseModel):
    """
    Defines timeout behavior for a workflow state.
    """
    duration_seconds: int
    action: str = "transition"  # transition, retry, alert, fail
    transition_on_timeout: Optional[str] = None
    max_retries: int = 0
    alert_message: Optional[str] = None
    escalation_agent_id: Optional[str] = None


class ErrorHandling(BaseModel):
    """
    Defines error handling behavior for a workflow state.
    """
    retry_count: int = 0
    retry_delay_seconds: int = 60
    exponential_backoff: bool = False
    failure_transition: Optional[str] = None
    error_handlers: Dict[str, str] = Field(default_factory=dict)  # error_type -> handler_function
    fallback_agent_id: Optional[str] = None


class WorkflowState(BaseModel, Generic[T]):
    """
    Represents a single state in a workflow state machine.
    All state information is persisted in Notion.
    """
    name: str
    description: str
    is_terminal: bool = False
    available_transitions: List[str] = Field(default_factory=list)
    agent_assignments: List[AgentAssignment] = Field(default_factory=list)
    required_data_points: List[str] = Field(default_factory=list)
    entry_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    exit_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    timeout: Optional[StateTimeout] = None
    error_handling: Optional[ErrorHandling] = None
    state_data: Optional[T] = None
    max_time_in_state_seconds: Optional[int] = None
    auto_transition_after_seconds: Optional[int] = None
    auto_transition_to: Optional[str] = None

    class Config:
        frozen = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Notion storage."""
        return {
            "name": self.name,
            "description": self.description,
            "is_terminal": self.is_terminal,
            "available_transitions": self.available_transitions,
            "agent_assignments": [assignment.dict() for assignment in self.agent_assignments],
            "required_data_points": self.required_data_points,
            "entry_conditions": self.entry_conditions,
            "exit_conditions": self.exit_conditions,
            "timeout": self.timeout.dict() if self.timeout else None,
            "error_handling": self.error_handling.dict() if self.error_handling else None,
            "max_time_in_state_seconds": self.max_time_in_state_seconds,
            "auto_transition_after_seconds": self.auto_transition_after_seconds,
            "auto_transition_to": self.auto_transition_to
        }


class TransitionResult(BaseModel):
    """
    Result of a state transition attempt.
    """
    success: bool
    instance: Optional[WorkflowInstance] = None
    error: Optional[str] = None
    transition: Optional[str] = None
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    agent_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    retry_count: int = 0
    retry_recommended: bool = False
    retry_after_seconds: Optional[int] = None
    fallback_transition: Optional[str] = None


class StateTransition(BaseModel):
    """
    Represents a transition between workflow states.
    Conditions and triggers determine when transitions occur.
    """
    from_state: str
    to_state: str
    name: str
    description: str
    conditions: List[Union[Dict[str, Any], str]] = Field(default_factory=list)
    condition_groups: List[Dict[str, Any]] = Field(default_factory=list)
    triggers: List[Union[Dict[str, Any], str]] = Field(default_factory=list)
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    retry_delay_seconds: int = 60
    exponential_backoff: bool = False
    transition_handler: Optional[str] = None
    transition_priority: int = 1
    requires_approval: bool = False
    approval_roles: List[str] = Field(default_factory=list)
    precondition_actions: List[str] = Field(default_factory=list)
    postcondition_actions: List[str] = Field(default_factory=list)
    failure_actions: List[str] = Field(default_factory=list)
    conditional_routing: Dict[str, str] = Field(default_factory=dict)  # condition -> to_state

    class Config:
        frozen = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Notion storage."""
        return {
            "from_state": self.from_state,
            "to_state": self.to_state,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "condition_groups": self.condition_groups,
            "triggers": self.triggers,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "retry_delay_seconds": self.retry_delay_seconds,
            "exponential_backoff": self.exponential_backoff,
            "transition_handler": self.transition_handler,
            "transition_priority": self.transition_priority,
            "requires_approval": self.requires_approval,
            "approval_roles": self.approval_roles,
            "precondition_actions": self.precondition_actions,
            "postcondition_actions": self.postcondition_actions,
            "failure_actions": self.failure_actions,
            "conditional_routing": self.conditional_routing
        }

    async def evaluate_conditions(
        self,
        instance: WorkflowInstance,
        condition_evaluator: Optional[Callable] = None
    ) -> bool:
        """
        Evaluate all conditions for this transition.

        Args:
            instance: The workflow instance
            condition_evaluator: Optional custom condition evaluator

        Returns:
            True if all conditions are met, False otherwise
        """
        # If no conditions, transition is always allowed
        if not self.conditions and not self.condition_groups:
            return True

        if condition_evaluator:
            # Use custom evaluator if provided
            return await condition_evaluator(self, instance)

        # Default condition evaluation
        context_data = instance.context_data

        # Process individual conditions
        condition_results = []
        for condition in self.conditions:
            if isinstance(condition, str):
                # String reference to condition - would need to be looked up
                # For now, just log that we can't evaluate it
                logger.warning(f"String condition reference '{condition}' cannot be evaluated directly")
                condition_results.append(False)
            elif isinstance(condition, dict):
                # Convert dict to TransitionCondition
                try:
                    from workflow.transitions import TransitionCondition
                    cond = TransitionCondition.from_dict(condition)
                    condition_results.append(cond.is_satisfied(context_data))
                except Exception as e:
                    logger.error(f"Error evaluating condition: {e}")
                    condition_results.append(False)

        # Process condition groups
        group_results = []
        for group in self.condition_groups:
            try:
                from workflow.transitions import ConditionGroup
                group_obj = ConditionGroup.from_dict(group)
                group_results.append(group_obj.is_satisfied(context_data))
            except Exception as e:
                logger.error(f"Error evaluating condition group: {e}")
                group_results.append(False)

        # Both individual conditions and condition groups must be satisfied
        # If either list is empty, its result is True
        conditions_satisfied = all(condition_results) if condition_results else True
        groups_satisfied = all(group_results) if group_results else True

        return conditions_satisfied and groups_satisfied

    def get_dynamic_target_state(self, instance: WorkflowInstance) -> Optional[str]:
        """
        Determine the target state based on conditional routing.

        Args:
            instance: The workflow instance

        Returns:
            Target state name or None to use the default to_state
        """
        if not self.conditional_routing:
            return None

        context_data = instance.context_data

        # Try each condition in the conditional routing
        for condition_str, target_state in self.conditional_routing.items():
            try:
                # Parse condition as a field path and expected value
                field_path, operator, expected_value = self._parse_condition_string(condition_str)

                # Get the actual value
                actual_value = self._get_field_value(context_data, field_path)

                # Compare based on operator
                if self._compare_values(actual_value, operator, expected_value):
                    return target_state
            except Exception as e:
                logger.error(f"Error evaluating conditional routing '{condition_str}': {e}")

        return None

    def _parse_condition_string(self, condition_str: str) -> Tuple[str, str, Any]:
        """Parse a condition string into field path, operator, and expected value."""
        # Very simple parser - in production, use a more robust solution
        parts = condition_str.split()
        if len(parts) < 3:
            raise ValueError(f"Invalid condition format: {condition_str}")

        field_path = parts[0]
        operator = parts[1]
        # Join the rest as the expected value
        expected_value = " ".join(parts[2:])

        # Try to convert expected value to appropriate type
        try:
            if expected_value.lower() == "true":
                expected_value = True
            elif expected_value.lower() == "false":
                expected_value = False
            elif expected_value.isdigit():
                expected_value = int(expected_value)
            elif expected_value.replace(".", "", 1).isdigit():
                expected_value = float(expected_value)
        except:
            pass

        return field_path, operator, expected_value

    def _get_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get the value from a nested dictionary using dot notation."""
        path_parts = field_path.split(".")
        current = data

        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def _compare_values(self, actual: Any, operator: str, expected: Any) -> bool:
        """Compare values based on operator."""
        if operator == "==":
            return actual == expected
        elif operator == "!=":
            return actual != expected
        elif operator == ">":
            return actual > expected if actual is not None else False
        elif operator == "<":
            return actual < expected if actual is not None else False
        elif operator == ">=":
            return actual >= expected if actual is not None else False
        elif operator == "<=":
            return actual <= expected if actual is not None else False
        elif operator == "in":
            return actual in expected if expected is not None else False
        elif operator == "not_in":
            return actual not in expected if expected is not None else True
        elif operator == "contains":
            return expected in actual if actual is not None else False
        elif operator == "not_contains":
            return expected not in actual if actual is not None else True
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False


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
