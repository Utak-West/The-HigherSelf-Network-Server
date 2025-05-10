"""
Workflow package for the Advanced Agentic Workflow Engine.

This package implements a LangGraph-inspired state machine for orchestrating
complex workflows between specialized agents, while maintaining Notion
as the central hub for all workflow data and state.
"""

from workflow.state_machine import WorkflowStateMachine, WorkflowState, StateTransition
from workflow.transitions import TransitionCondition, TransitionTrigger

__all__ = [
    'WorkflowStateMachine',
    'WorkflowState',
    'StateTransition',
    'TransitionCondition',
    'TransitionTrigger'
]