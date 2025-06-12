#!/usr/bin/env python3
"""
Example script demonstrating the Enhanced Workflow State Machine with advanced transitions.

This script sets up a sample workflow with both standard and enhanced transitions
and executes them for comparison.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from colorama import Fore, Style, init

# Add parent directory to path to allow importing from the server codebase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.notion_db_models import WorkflowInstance
from services.notion_service import NotionService
from workflow.enhanced_transitions import EnhancedStateMachine, TransitionResult
from workflow.state_machine import StateTransition, WorkflowState, WorkflowStateMachine
from workflow.transitions import TransitionType, create_simple_condition

# Initialize colorama for colored terminal output
init(autoreset=True)


def print_header(message: str) -> None:
    """Print a header message in blue."""
    print(Fore.BLUE + Style.BRIGHT + "\n" + message)


def print_success(message: str) -> None:
    """Print a success message in green."""
    print(Fore.GREEN + message)


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    print(Fore.YELLOW + message)


def print_error(message: str) -> None:
    """Print an error message in red."""
    print(Fore.RED + Style.BRIGHT + message)


def print_info(message: str) -> None:
    """Print an info message in cyan."""
    print(Fore.CYAN + message)


def print_transition_result(
    title: str, result: Union[TransitionResult, Tuple[bool, Optional[WorkflowInstance]]]
) -> None:
    """Print a transition result."""
    print_header(title)

    if isinstance(result, TransitionResult):
        # Enhanced transition result
        success = result.success
        from_state = result.from_state
        to_state = result.to_state
        error = result.error
        retry = result.retry_recommended
    else:
        # Standard transition result
        success, instance = result
        from_state = instance.current_state if instance else None
        to_state = None  # Not tracked in standard result
        error = None  # Not tracked in standard result
        retry = False  # Not supported in standard transitions

    if success:
        print_success("✓ Transition successful")
        if from_state and to_state:
            print_success(f"  State changed: {from_state} -> {to_state}")
    else:
        print_error("✗ Transition failed")
        if error:
            print_error(f"  Error: {error}")
        if retry:
            print_warning(f"  Retry recommended")

    print("")


async def setup_test_workflow() -> WorkflowStateMachine:
    """Set up a test workflow state machine."""
    print_header("Setting up test workflow...")

    # Define states
    states = {
        "start": WorkflowState(
            name="start",
            description="Initial state",
            available_transitions=["to_processing", "to_review"],
            agent_assignments=[{"agent_id": "agent1", "priority": 1}],
            required_data_points=["customer_id"],
        ),
        "processing": WorkflowState(
            name="processing",
            description="Processing the order",
            available_transitions=["to_review", "to_approved", "to_rejected"],
            agent_assignments=[{"agent_id": "agent2", "priority": 1}],
            required_data_points=["order_details"],
        ),
        "review": WorkflowState(
            name="review",
            description="Order under review",
            available_transitions=["to_approved", "to_rejected", "to_processing"],
            agent_assignments=[{"agent_id": "agent3", "priority": 1}],
            required_data_points=["review_notes"],
        ),
        "approved": WorkflowState(
            name="approved",
            description="Order approved",
            is_terminal=True,
            agent_assignments=[],
            required_data_points=["approval_date"],
        ),
        "rejected": WorkflowState(
            name="rejected",
            description="Order rejected",
            is_terminal=True,
            agent_assignments=[],
            required_data_points=["rejection_reason"],
        ),
    }

    # Define transitions
    transitions = [
        StateTransition(
            from_state="start",
            to_state="processing",
            name="to_processing",
            description="Move to processing state",
            conditions=[],
            triggers=[],
        ),
        StateTransition(
            from_state="start",
            to_state="review",
            name="to_review",
            description="Move directly to review state",
            conditions=[],
            triggers=[],
        ),
        StateTransition(
            from_state="processing",
            to_state="review",
            name="to_review",
            description="Move to review state",
            conditions=[],
            triggers=[],
        ),
        StateTransition(
            from_state="processing",
            to_state="approved",
            name="to_approved",
            description="Approve the order directly",
            conditions=[],
            triggers=[],
        ),
        StateTransition(
            from_state="processing",
            to_state="rejected",
            name="to_rejected",
            description="Reject the order directly",
            conditions=[],
            triggers=[],
        ),
        StateTransition(
            from_state="review",
            to_state="approved",
            name="to_approved",
            description="Approve the order after review",
            conditions=[],
            triggers=[],
        ),
        StateTransition(
            from_state="review",
            to_state="rejected",
            name="to_rejected",
            description="Reject the order after review",
            conditions=[],
            triggers=[],
        ),
        StateTransition(
            from_state="review",
            to_state="processing",
            name="to_processing",
            description="Send back to processing",
            conditions=[],
            triggers=[],
        ),
    ]

    # Create a mock NotionService that doesn't actually connect to Notion
    class MockNotionService(NotionService):
        def __init__(self):
            # Skip actual Notion initialization
            self._client = None
            self._notion_token = "mock_token"
            self.instances = {}

        async def create_page(self, instance):
            # Store the instance locally
            instance_id = instance.instance_id
            instance.page_id = f"mock_page_{instance_id}"
            self.instances[instance_id] = instance
            return instance.page_id

        async def update_page(self, instance):
            # Update the instance locally
            self.instances[instance.instance_id] = instance
            return True

        async def query_database(self, model_class, filter_conditions):
            # Return instances based on the filter
            # Simplified implementation, just return all
            return list(self.instances.values())

    # Create the workflow
    workflow = WorkflowStateMachine(
        workflow_id="test_workflow",
        name="Test Workflow",
        description="A test workflow for demonstrating enhanced transitions",
        states=states,
        transitions=transitions,
        initial_state="start",
        notion_service=MockNotionService(),
    )

    print_success("✓ Workflow setup complete")
    return workflow


async def setup_enhanced_transitions(
    workflow: WorkflowStateMachine,
) -> List[StateTransition]:
    """
    Set up enhanced transitions with conditional routing and retry logic.

    Returns the enhanced transitions, but doesn't modify the original workflow.
    """
    print_header("Setting up enhanced transitions...")

    from workflow.transitions import ConditionOperator, TransitionCondition

    # Create enhanced transitions based on the original ones
    enhanced_transitions = []

    # Add conditional routing transition
    conditional_transition = StateTransition(
        from_state="start",
        to_state="processing",  # Default target
        name="conditional_routing",
        description="Route based on order value",
        condition_groups=[
            {
                "conditions": [
                    {
                        "name": "check_order_value",
                        "description": "Check if order value is high",
                        "field_path": "order_value",
                        "operator": ConditionOperator.GREATER_THAN,
                        "expected_value": 1000,
                    }
                ],
                "operator": "AND",
            }
        ],
        conditional_routing={
            "order_value > 1000": "review",  # High value orders go to review
            "order_value < 100": "rejected",  # Low value orders rejected
        },
        retry_count=2,
        retry_delay_seconds=5,
        exponential_backoff=True,
        transition_priority=1,
    )
    enhanced_transitions.append(conditional_transition)

    # Add a transition with pre/post actions
    action_transition = StateTransition(
        from_state="processing",
        to_state="approved",
        name="approve_with_actions",
        description="Approve with pre/post actions",
        precondition_actions=["validate_order", "check_inventory"],
        postcondition_actions=["send_confirmation_email", "update_inventory"],
        timeout_seconds=30,
        retry_count=3,
        transition_priority=1,
    )
    enhanced_transitions.append(action_transition)

    print_success("✓ Enhanced transitions setup complete")
    return enhanced_transitions


async def run_standard_workflow(workflow: WorkflowStateMachine) -> None:
    """Run a workflow using standard transitions."""
    print_header("Running standard workflow...")

    # Create a new workflow instance
    instance = await workflow.create_instance(
        business_entity_id="customer123",
        context_data={
            "customer_id": "customer123",
            "order_details": {"product_id": "prod456", "quantity": 1},
            "order_value": 500,
        },
    )

    print_info(f"Created workflow instance: {instance.instance_id}")
    print_info(f"Initial state: {instance.current_state}")

    # Execute a simple transition
    result = await workflow.transition(
        instance_id=instance.instance_id,
        transition_name="to_processing",
        agent_id="agent1",
        action_description="Processing the order",
        transition_data={"processing_timestamp": datetime.now().isoformat()},
    )

    print_transition_result("Standard Transition Result:", result)

    # Get the updated instance
    instance = await workflow.get_instance(instance.instance_id)

    # Complete the workflow with another transition
    result = await workflow.transition(
        instance_id=instance.instance_id,
        transition_name="to_approved",
        agent_id="agent2",
        action_description="Approving the order",
        transition_data={"approval_date": datetime.now().isoformat()},
    )

    print_transition_result("Final Standard Transition Result:", result)

    # Get the updated instance again
    instance = await workflow.get_instance(instance.instance_id)
    print_info(f"Final state: {instance.current_state}")
    print_info(f"Status: {instance.status}")


async def run_enhanced_workflow(
    workflow: WorkflowStateMachine, enhanced_transitions: List[StateTransition]
) -> None:
    """Run a workflow using enhanced transitions."""
    print_header("Running enhanced workflow...")

    # Create the enhanced state machine wrapper
    enhanced = EnhancedStateMachine(workflow)

    # Create a new workflow instance
    instance = await workflow.create_instance(
        business_entity_id="customer456",
        context_data={
            "customer_id": "customer456",
            "order_details": {"product_id": "prod789", "quantity": 2},
            "order_value": 1200,  # High value order should trigger conditional routing
        },
    )

    print_info(f"Created workflow instance: {instance.instance_id}")
    print_info(f"Initial state: {instance.current_state}")

    # Find the conditional routing transition
    conditional_transition = next(
        (t for t in enhanced_transitions if t.name == "conditional_routing"), None
    )

    if conditional_transition:
        # Temporarily add this transition to the workflow
        # In a real system, you would properly register these transitions
        workflow.transitions.append(conditional_transition)

        # Execute conditional transition with retry support
        result = await enhanced.transition_with_retry(
            instance_id=instance.instance_id,
            transition_name="conditional_routing",
            agent_id="agent1",
            action_description="Processing with conditional routing",
            transition_data={"routing_timestamp": datetime.now().isoformat()},
        )

        print_transition_result("Enhanced Conditional Transition Result:", result)

        # Remove the temporary transition
        workflow.transitions.remove(conditional_transition)

    # Get the updated instance
    instance = await workflow.get_instance(instance.instance_id)
    print_info(f"Current state after conditional routing: {instance.current_state}")

    # Dynamic agent assignment
    assigned_agent = await enhanced.assign_agent_to_state(instance)
    print_info(f"Dynamically assigned agent: {assigned_agent}")

    # Complete the workflow using a standard transition
    if instance.current_state == "review":
        result = await enhanced.enhanced_transition(
            instance_id=instance.instance_id,
            transition_name="to_approved",
            agent_id=assigned_agent or "agent3",
            action_description="Approving after review",
            transition_data={
                "approval_date": datetime.now().isoformat(),
                "review_notes": "High value order approved",
            },
        )

        print_transition_result("Final Enhanced Transition Result:", result)

    # Get the final instance state
    instance = await workflow.get_instance(instance.instance_id)
    print_info(f"Final state: {instance.current_state}")
    print_info(f"Status: {instance.status}")


async def main():
    """Main function."""
    print_header("===== Enhanced Workflow Example =====")

    # Setup
    workflow = await setup_test_workflow()
    enhanced_transitions = await setup_enhanced_transitions(workflow)

    # Generate visualization
    mermaid = await workflow.visualize()
    print_header("Workflow Visualization:")
    print(mermaid)

    # Run standard workflow
    await run_standard_workflow(workflow)

    # Run enhanced workflow
    await run_enhanced_workflow(workflow, enhanced_transitions)

    print_header("===== Example Completed =====")


if __name__ == "__main__":
    asyncio.run(main())
