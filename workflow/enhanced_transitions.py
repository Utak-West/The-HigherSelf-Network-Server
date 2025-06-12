"""
Enhanced transitions for the Advanced Agentic Workflow Engine.

This module extends the workflow state machine with more sophisticated transition
capabilities including conditional routing, retry logic, error handling, and timeout management.
"""

import asyncio
import functools
import random
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from loguru import logger
from pydantic import BaseModel, Field

from knowledge import SemanticSearch, get_semantic_search
from models.notion_db_models import WorkflowInstance
from workflow.state_machine import StateTransition, WorkflowState, WorkflowStateMachine
from workflow.transitions import ConditionGroup, TransitionCondition, TransitionTrigger


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


class EnhancedStateMachine:
    """
    Extension class providing enhanced transition capabilities to the WorkflowStateMachine.
    """

    def __init__(self, state_machine: WorkflowStateMachine):
        """
        Initialize the enhanced state machine.

        Args:
            state_machine: Base WorkflowStateMachine to enhance
        """
        self.state_machine = state_machine
        self.logger = state_machine.logger

    async def enhanced_transition(
        self,
        instance_id: str,
        transition_name: str,
        agent_id: str,
        action_description: str = None,
        transition_data: Dict[str, Any] = None,
        retry_attempt: int = 0,
        condition_evaluator: Optional[Callable] = None,
    ) -> TransitionResult:
        """
        Enhanced transition method with conditional logic, retry support, and error handling.

        Args:
            instance_id: Workflow instance ID
            transition_name: Name of the transition to execute
            agent_id: ID of the agent executing the transition
            action_description: Optional description of the action
            transition_data: Optional data related to the transition
            retry_attempt: Current retry attempt (0 for first attempt)
            condition_evaluator: Optional custom condition evaluator

        Returns:
            TransitionResult with details about the transition
        """
        notion_svc = await self.state_machine.notion_service
        start_time = time.time()

        # Create initial result object
        result = TransitionResult(
            success=False,
            transition=transition_name,
            agent_id=agent_id,
            retry_count=retry_attempt,
        )

        try:
            # Get the instance
            instance = await self.state_machine.get_instance(instance_id)
            if not instance:
                result.error = f"Workflow instance {instance_id} not found"
                self.logger.error(result.error)
                return result

            result.instance = instance
            result.from_state = instance.current_state

            # Get current state
            current_state_name = instance.current_state
            current_state = self.state_machine.states.get(current_state_name)

            if not current_state:
                result.error = f"Current state '{current_state_name}' not found in workflow definition"
                self.logger.error(result.error)
                return result

            # Check if transition is valid from current state
            if transition_name not in current_state.available_transitions:
                result.error = f"Transition '{transition_name}' not available from state '{current_state_name}'"
                self.logger.error(result.error)
                return result

            # Find the transition
            transition = next(
                (
                    t
                    for t in self.state_machine.transitions
                    if t.name == transition_name
                ),
                None,
            )
            if not transition:
                result.error = (
                    f"Transition '{transition_name}' not found in workflow definition"
                )
                self.logger.error(result.error)
                return result

            # Check timeout settings from state or transition
            timeout_seconds = transition.timeout_seconds
            if (
                timeout_seconds is not None
                and time.time() - start_time > timeout_seconds
            ):
                result.error = f"Operation timed out after {timeout_seconds} seconds"
                result.retry_recommended = transition.retry_count > retry_attempt
                result.retry_after_seconds = 5
                self.logger.warning(result.error)
                return result

            # Evaluate conditions if transition has them
            if hasattr(transition, "evaluate_conditions"):
                conditions_met = await transition.evaluate_conditions(
                    instance, condition_evaluator
                )
                if not conditions_met:
                    result.error = (
                        f"Transition conditions not met for '{transition_name}'"
                    )
                    self.logger.warning(result.error)
                    return result

            # Check for dynamic routing
            target_state_name = transition.to_state
            if hasattr(transition, "get_dynamic_target_state"):
                dynamic_target = transition.get_dynamic_target_state(instance)
                if dynamic_target:
                    # Override the target state
                    target_state_name = dynamic_target
                    self.logger.info(
                        f"Dynamic routing: redirecting to '{target_state_name}' instead of '{transition.to_state}'"
                    )

            # Get target state
            target_state = self.state_machine.states.get(target_state_name)
            if not target_state:
                result.error = f"Target state '{target_state_name}' not found in workflow definition"
                self.logger.error(result.error)
                return result

            # Execute pre-transition actions if defined
            if hasattr(transition, "precondition_actions"):
                for action_name in transition.precondition_actions:
                    try:
                        self.logger.info(
                            f"Executing pre-transition action: {action_name}"
                        )
                        # Implement action handler mechanism
                    except Exception as e:
                        result.error = (
                            f"Error in pre-transition action '{action_name}': {str(e)}"
                        )
                        self.logger.error(result.error)
                        return result

            # Prepare the transition description
            if not action_description:
                action_description = f"Transitioned from {current_state_name} to {target_state_name} via {transition_name}"

            # Set the result's target state
            result.to_state = target_state_name

            # Update the instance state in Notion
            instance.current_state = target_state_name
            instance.last_transition_date = datetime.now()
            instance.add_history_entry(
                action=f"[{agent_id}] {action_description}", details=transition_data
            )

            # If target state is terminal, update status accordingly
            if target_state.is_terminal:
                instance.status = "Completed"

            # Update context data if provided
            if transition_data and isinstance(transition_data, dict):
                for key, value in transition_data.items():
                    instance.context_data[key] = value

            # Execute post-transition actions if defined
            if hasattr(transition, "postcondition_actions"):
                for action_name in transition.postcondition_actions:
                    try:
                        self.logger.info(
                            f"Executing post-transition action: {action_name}"
                        )
                        # Implement action handler mechanism
                    except Exception as e:
                        # Note: we continue even if post-actions fail, but log the error
                        self.logger.error(
                            f"Error in post-transition action '{action_name}': {str(e)}"
                        )

            # Update in Notion
            notion_success = await notion_svc.update_page(instance)

            if notion_success:
                # Update active instances cache
                self.state_machine.active_instances[instance_id] = target_state_name

                self.logger.info(
                    f"Transitioned instance {instance_id} from {current_state_name} to {target_state_name}"
                )

                # If terminal state, remove from active instances
                if target_state.is_terminal:
                    self.state_machine.active_instances.pop(instance_id, None)
                    self.logger.info(f"Workflow instance {instance_id} completed")

                result.success = True
                return result
            else:
                result.error = f"Failed to update workflow instance in Notion"
                result.retry_recommended = True
                self.logger.error(result.error)
                return result

        except Exception as e:
            result.error = f"Error during transition: {str(e)}"
            self.logger.exception(f"Unexpected error during transition: {e}")

            # Determine if we should retry
            max_retries = getattr(transition, "retry_count", 0)
            if retry_attempt < max_retries:
                result.retry_recommended = True

                # Calculate retry delay with optional exponential backoff
                base_delay = getattr(transition, "retry_delay_seconds", 60)
                use_backoff = getattr(transition, "exponential_backoff", False)

                if use_backoff:
                    retry_delay = base_delay * (2**retry_attempt)
                else:
                    retry_delay = base_delay

                result.retry_after_seconds = retry_delay
                self.logger.info(
                    f"Recommending retry in {retry_delay} seconds (attempt {retry_attempt+1}/{max_retries})"
                )

            return result

    async def transition_with_retry(
        self,
        instance_id: str,
        transition_name: str,
        agent_id: str,
        action_description: str = None,
        transition_data: Dict[str, Any] = None,
        condition_evaluator: Optional[Callable] = None,
    ) -> TransitionResult:
        """
        Transition with automatic retry support.

        Args:
            instance_id: Workflow instance ID
            transition_name: Name of the transition to execute
            agent_id: ID of the agent executing the transition
            action_description: Optional description of the action
            transition_data: Optional data related to the transition
            condition_evaluator: Optional custom condition evaluator

        Returns:
            TransitionResult with details about the transition
        """
        # Find the transition to get retry settings
        transition = next(
            (t for t in self.state_machine.transitions if t.name == transition_name),
            None,
        )
        if not transition:
            return TransitionResult(
                success=False,
                error=f"Transition '{transition_name}' not found in workflow definition",
                transition=transition_name,
                agent_id=agent_id,
            )

        retry_count = getattr(transition, "retry_count", 0)

        # First attempt
        result = await self.enhanced_transition(
            instance_id=instance_id,
            transition_name=transition_name,
            agent_id=agent_id,
            action_description=action_description,
            transition_data=transition_data,
            retry_attempt=0,
            condition_evaluator=condition_evaluator,
        )

        # If successful or no retries configured, return immediately
        if result.success or retry_count == 0:
            return result

        # Retry logic
        attempt = 0
        while attempt < retry_count and result.retry_recommended:
            attempt += 1

            # Wait before retry if specified
            if result.retry_after_seconds:
                await asyncio.sleep(result.retry_after_seconds)

            self.logger.info(
                f"Retrying transition '{transition_name}' (attempt {attempt+1}/{retry_count+1})"
            )

            # Execute retry
            result = await self.enhanced_transition(
                instance_id=instance_id,
                transition_name=transition_name,
                agent_id=agent_id,
                action_description=f"{action_description} (retry {attempt})"
                if action_description
                else f"Retry {attempt}",
                transition_data=transition_data,
                retry_attempt=attempt,
                condition_evaluator=condition_evaluator,
            )

            if result.success:
                break

        return result

    async def assign_agent_to_state(
        self, instance: WorkflowInstance, state_name: str = None
    ) -> Optional[str]:
        """
        Dynamically assign an agent to a workflow state based on rules.

        Args:
            instance: Workflow instance
            state_name: Optional state name (defaults to current state)

        Returns:
            Agent ID or None if no agent could be assigned
        """
        state_name = state_name or instance.current_state
        state = self.state_machine.states.get(state_name)

        if not state:
            self.logger.error(f"Cannot assign agent: state '{state_name}' not found")
            return None

        # Check for static agent assignments first
        static_assignments = [a for a in state.agent_assignments if a.agent_id]
        if static_assignments:
            # Sort by priority (lower number = higher priority)
            static_assignments.sort(key=lambda a: a.priority)
            # For now, just return the highest priority static assignment
            return static_assignments[0].agent_id

        # Check for role-based assignments
        role_assignments = [a for a in state.agent_assignments if a.agent_role]
        if role_assignments:
            # TODO: Implement role-based agent lookup
            self.logger.info(f"Role-based agent assignment not implemented")

        # Check for context-dependent assignments
        context_assignments = [
            a for a in state.agent_assignments if a.context_dependent
        ]
        if context_assignments:
            # Evaluate each context condition
            for assignment in context_assignments:
                # TODO: Implement context-based evaluation
                pass

        # Check for semantic matching if no other method worked
        semantic_assignments = [
            a
            for a in state.agent_assignments
            if a.selection_strategy == "semantic_match"
        ]
        if semantic_assignments:
            try:
                # Initialize semantic search
                semantic_search = get_semantic_search()
                await semantic_search.initialize()

                # Generate a query from the context data
                # This is a simplified approach - in a real system, you'd want a more
                # sophisticated context-to-query transformation
                context_str = str(instance.context_data)

                # TODO: Implement agent search via semantic matching
                # This would involve embedding agents' capabilities and matching
                # against the current context

            except Exception as e:
                self.logger.error(f"Error in semantic agent matching: {e}")

        # Default to the first fallback agent if all else fails
        for assignment in state.agent_assignments:
            if assignment.fallback_agent_ids:
                return assignment.fallback_agent_ids[0]

        self.logger.warning(f"No agent could be assigned for state '{state_name}'")
        return None
