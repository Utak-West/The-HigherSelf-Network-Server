"""
Transition definitions for the Advanced Agentic Workflow Engine.

This module provides the building blocks for defining transitions between
workflow states, including conditions and triggers. All transition data
is persisted in Notion, maintaining it as the central hub.
"""

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Union, Set
from pydantic import BaseModel, Field
from loguru import logger

from models.notion_db_models import WorkflowInstance


class TransitionType(str, Enum):
    """Types of workflow transitions."""
    AUTOMATIC = "automatic"  # Occurs automatically when conditions are met
    MANUAL = "manual"        # Requires explicit trigger from an agent or user
    SCHEDULED = "scheduled"  # Occurs at a scheduled time
    EVENT_DRIVEN = "event_driven"  # Triggered by an external event


class TransitionTrigger(BaseModel):
    """
    Defines a trigger that can cause a workflow transition.
    All trigger data is stored in Notion.
    """
    name: str
    description: str
    trigger_type: TransitionType
    event_types: List[str] = Field(default_factory=list)
    scheduled_time: Optional[datetime] = None
    schedule_frequency: Optional[str] = None  # cron-like expression
    agent_roles_allowed: List[str] = Field(default_factory=list)
    manual_prompt_template: Optional[str] = None
    
    class Config:
        frozen = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the trigger to a dictionary for storage in Notion."""
        return {
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type.value,
            "event_types": self.event_types,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "schedule_frequency": self.schedule_frequency,
            "agent_roles_allowed": self.agent_roles_allowed,
            "manual_prompt_template": self.manual_prompt_template
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransitionTrigger":
        """Create a trigger from a dictionary stored in Notion."""
        if "scheduled_time" in data and data["scheduled_time"]:
            if isinstance(data["scheduled_time"], str):
                data["scheduled_time"] = datetime.fromisoformat(data["scheduled_time"])
        
        return cls(
            name=data["name"],
            description=data["description"],
            trigger_type=TransitionType(data["trigger_type"]),
            event_types=data.get("event_types", []),
            scheduled_time=data.get("scheduled_time"),
            schedule_frequency=data.get("schedule_frequency"),
            agent_roles_allowed=data.get("agent_roles_allowed", []),
            manual_prompt_template=data.get("manual_prompt_template")
        )
    
    async def is_triggered(
        self, 
        instance: WorkflowInstance,
        current_time: Optional[datetime] = None,
        event_type: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        agent_role: Optional[str] = None
    ) -> bool:
        """
        Check if this trigger is activated based on the current context.
        
        Args:
            instance: The workflow instance
            current_time: Current time (for scheduled triggers)
            event_type: Event type (for event-driven triggers)
            event_data: Event data (for event-driven triggers)
            agent_role: Role of the agent/user (for manual triggers)
            
        Returns:
            True if triggered, False otherwise
        """
        current_time = current_time or datetime.now()
        
        if self.trigger_type == TransitionType.SCHEDULED:
            if self.scheduled_time and current_time >= self.scheduled_time:
                return True
            
            if self.schedule_frequency:
                # Very basic cron-like implementation
                # In a production system, use a proper cron parser
                # This simplified version just checks daily execution time
                # Format: "HH:MM" for daily execution at that time
                time_match = re.match(r"(\d{2}):(\d{2})", self.schedule_frequency)
                if time_match:
                    hour, minute = map(int, time_match.groups())
                    scheduled_today = current_time.replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )
                    
                    # Check if it's time and not already triggered today
                    last_trigger = instance.context_data.get(f"last_trigger_{self.name}")
                    if last_trigger:
                        last_trigger = datetime.fromisoformat(last_trigger)
                        # If already triggered today, don't trigger again
                        if last_trigger.date() == current_time.date():
                            return False
                    
                    # Trigger if current time is past the scheduled time
                    return current_time >= scheduled_today
        
        elif self.trigger_type == TransitionType.EVENT_DRIVEN:
            if event_type and event_type in self.event_types:
                return True
        
        elif self.trigger_type == TransitionType.MANUAL:
            if agent_role and agent_role in self.agent_roles_allowed:
                return True
        
        # AUTOMATIC triggers always return True as they're condition-based
        elif self.trigger_type == TransitionType.AUTOMATIC:
            return True
        
        return False


class ConditionOperator(str, Enum):
    """Operators for condition evaluation."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    REGEX_MATCH = "regex_match"


class TransitionCondition(BaseModel):
    """
    Defines a condition that must be met for a workflow transition.
    All condition data is stored in Notion.
    """
    name: str
    description: str
    field_path: str  # Path to the field in the context data
    operator: ConditionOperator
    expected_value: Optional[Any] = None
    case_sensitive: bool = False
    
    class Config:
        frozen = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the condition to a dictionary for storage in Notion."""
        return {
            "name": self.name,
            "description": self.description,
            "field_path": self.field_path,
            "operator": self.operator.value,
            "expected_value": json.dumps(self.expected_value) if self.expected_value is not None else None,
            "case_sensitive": self.case_sensitive
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransitionCondition":
        """Create a condition from a dictionary stored in Notion."""
        expected_value = data.get("expected_value")
        if expected_value is not None and isinstance(expected_value, str):
            try:
                expected_value = json.loads(expected_value)
            except json.JSONDecodeError:
                # If not valid JSON, keep as string
                pass
        
        return cls(
            name=data["name"],
            description=data["description"],
            field_path=data["field_path"],
            operator=ConditionOperator(data["operator"]),
            expected_value=expected_value,
            case_sensitive=data.get("case_sensitive", False)
        )
    
    def _get_field_value(self, data: Dict[str, Any]) -> Any:
        """Get the value from a nested dictionary using dot notation."""
        path_parts = self.field_path.split(".")
        current = data
        
        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def is_satisfied(self, context_data: Dict[str, Any]) -> bool:
        """
        Check if the condition is satisfied based on the context data.
        
        Args:
            context_data: The workflow context data
            
        Returns:
            True if condition is satisfied, False otherwise
        """
        field_value = self._get_field_value(context_data)
        
        # For string comparisons, handle case sensitivity
        if isinstance(field_value, str) and isinstance(self.expected_value, str) and not self.case_sensitive:
            field_value = field_value.lower()
            expected = self.expected_value.lower()
        else:
            expected = self.expected_value
        
        if self.operator == ConditionOperator.EQUALS:
            return field_value == expected
        
        elif self.operator == ConditionOperator.NOT_EQUALS:
            return field_value != expected
        
        elif self.operator == ConditionOperator.GREATER_THAN:
            return field_value > expected if field_value is not None else False
        
        elif self.operator == ConditionOperator.LESS_THAN:
            return field_value < expected if field_value is not None else False
        
        elif self.operator == ConditionOperator.CONTAINS:
            if isinstance(field_value, (list, tuple, set)):
                return expected in field_value
            elif isinstance(field_value, str):
                return expected in field_value
            elif isinstance(field_value, dict):
                return expected in field_value
            return False
        
        elif self.operator == ConditionOperator.NOT_CONTAINS:
            if isinstance(field_value, (list, tuple, set)):
                return expected not in field_value
            elif isinstance(field_value, str):
                return expected not in field_value
            elif isinstance(field_value, dict):
                return expected not in field_value
            return True
        
        elif self.operator == ConditionOperator.EXISTS:
            return field_value is not None
        
        elif self.operator == ConditionOperator.NOT_EXISTS:
            return field_value is None
        
        elif self.operator == ConditionOperator.REGEX_MATCH:
            if not isinstance(field_value, str) or not isinstance(expected, str):
                return False
            try:
                return bool(re.match(expected, field_value))
            except re.error:
                return False
        
        return False


class ConditionGroup(BaseModel):
    """
    A group of conditions with a logical operator (AND/OR).
    All condition groups are stored in Notion.
    """
    conditions: List[TransitionCondition]
    operator: str = "AND"  # AND or OR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the condition group to a dictionary for storage in Notion."""
        return {
            "conditions": [c.to_dict() for c in self.conditions],
            "operator": self.operator
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConditionGroup":
        """Create a condition group from a dictionary stored in Notion."""
        conditions = [
            TransitionCondition.from_dict(c) for c in data.get("conditions", [])
        ]
        return cls(
            conditions=conditions,
            operator=data.get("operator", "AND")
        )
    
    def is_satisfied(self, context_data: Dict[str, Any]) -> bool:
        """
        Check if the condition group is satisfied.
        
        Args:
            context_data: The workflow context data
            
        Returns:
            True if the group is satisfied, False otherwise
        """
        if not self.conditions:
            return True
        
        if self.operator == "AND":
            return all(c.is_satisfied(context_data) for c in self.conditions)
        else:  # OR
            return any(c.is_satisfied(context_data) for c in self.conditions)


def create_simple_condition(
    field: str,
    operator: Union[str, ConditionOperator],
    value: Any,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> TransitionCondition:
    """
    Create a simple transition condition.
    
    Args:
        field: Field to check in context data
        operator: Condition operator
        value: Expected value
        name: Optional name
        description: Optional description
        
    Returns:
        TransitionCondition
    """
    if isinstance(operator, str):
        operator = ConditionOperator(operator)
    
    return TransitionCondition(
        name=name or f"Condition_{field}_{operator.value}",
        description=description or f"Check if {field} {operator.value} {value}",
        field_path=field,
        operator=operator,
        expected_value=value
    )


def create_simple_trigger(
    trigger_type: Union[str, TransitionType],
    name: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> TransitionTrigger:
    """
    Create a simple transition trigger.
    
    Args:
        trigger_type: Type of trigger
        name: Optional name
        description: Optional description
        **kwargs: Additional trigger properties
        
    Returns:
        TransitionTrigger
    """
    if isinstance(trigger_type, str):
        trigger_type = TransitionType(trigger_type)
    
    return TransitionTrigger(
        name=name or f"Trigger_{trigger_type.value}",
        description=description or f"{trigger_type.value.capitalize()} trigger",
        trigger_type=trigger_type,
        **kwargs
    )