"""
Workflow State Machine Engine for The HigherSelf Network Server.

This module provides a robust workflow engine using state machines, featuring
validation of workflow definitions, enforcement of valid state transitions,
workflow history maintenance, and support for custom transition handlers.
"""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator

# Import needed services and models
from services.notion_service import NotionService


class WorkflowState(str, Enum):
    """Base workflow states."""

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ON_HOLD = "on_hold"


class WorkflowTransitionResult(BaseModel):
    """Result of a workflow state transition."""

    success: bool
    new_state: Optional[str] = None
    error: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    """Definition of a workflow including states and transitions."""

    name: str
    description: str = ""
    states: List[str]
    initial_state: str
    transitions: Dict[str, List[str]]  # from_state -> [to_states]

    def validate(self) -> bool:
        """Validate workflow definition integrity."""
        # Initial state must be in states
        if self.initial_state not in self.states:
            return False

        # All transition states must exist in states
        for from_state, to_states in self.transitions.items():
            if from_state not in self.states:
                return False

            for to_state in to_states:
                if to_state not in self.states:
                    return False

        return True


class WorkflowHistoryEntry(BaseModel):
    """An entry in the workflow history."""

    timestamp: datetime = Field(default_factory=datetime.now)
    from_state: str
    to_state: str
    reason: str
    agent: str
    details: Dict[str, Any] = Field(default_factory=dict)


class WorkflowInstance(BaseModel):
    """Instance of a running workflow."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    definition_name: str
    current_state: str
    data: Dict[str, Any] = Field(default_factory=dict)
    history: List[WorkflowHistoryEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    notion_page_id: Optional[str] = None

    def record_transition(
        self,
        from_state: str,
        to_state: str,
        reason: str,
        agent: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Record a state transition in the workflow history."""
        self.history.append(
            WorkflowHistoryEntry(
                from_state=from_state,
                to_state=to_state,
                reason=reason,
                agent=agent,
                details=details or {},
            )
        )
        self.current_state = to_state
        self.updated_at = datetime.now()


class TransitionHandler:
    """
    Base class for custom transition handlers.

    Implement this to add custom logic during state transitions.
    """

    async def handle_transition(
        self,
        instance: WorkflowInstance,
        from_state: str,
        to_state: str,
        context: Dict[str, Any],
    ) -> bool:
        """
        Handle a transition between states.

        Args:
            instance: The workflow instance
            from_state: The state transitioning from
            to_state: The state transitioning to
            context: Additional context for the transition

        Returns:
            bool: True if transition is allowed, False otherwise
        """
        return True


class WorkflowEngine:
    """
    Enhanced workflow engine using state machines.

    This implementation:
    1. Validates workflow definitions
    2. Enforces valid state transitions
    3. Maintains workflow history
    4. Supports custom transition handlers
    """

    def __init__(
        self,
        notion_client: Optional[NotionService] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.notion_client = notion_client
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.transition_handlers: Dict[str, Dict[str, Callable]] = {}
        self.logger = logger or logging.getLogger("workflow.engine")
        self.active_workflows: Dict[str, WorkflowInstance] = {}

        # Database IDs for Notion integration
        self.active_workflows_db_id = "active_workflows_database_id"

    def register_workflow(self, definition: WorkflowDefinition) -> bool:
        """Register a workflow definition with the engine."""
        if not definition.validate():
            self.logger.error(f"Invalid workflow definition: {definition.name}")
            return False

        self.workflow_definitions[definition.name] = definition
        self.transition_handlers[definition.name] = {}
        self.logger.info(f"Registered workflow definition: {definition.name}")
        return True

    def register_transition_handler(
        self,
        workflow_name: str,
        from_state: str,
        to_state: str,
        handler: Callable[[Dict[str, Any]], Awaitable[bool]],
    ) -> bool:
        """Register a handler for a specific state transition."""
        if workflow_name not in self.workflow_definitions:
            self.logger.error(
                f"Cannot register handler: Unknown workflow '{workflow_name}'"
            )
            return False

        definition = self.workflow_definitions[workflow_name]

        # Validate states exist
        if from_state not in definition.states or to_state not in definition.states:
            self.logger.error(
                f"Cannot register handler: Invalid states '{from_state}' or '{to_state}'"
            )
            return False

        # Validate transition is allowed
        if to_state not in definition.transitions.get(from_state, []):
            self.logger.error(
                f"Cannot register handler: Transition from '{from_state}' to '{to_state}' not allowed"
            )
            return False

        # Register the handler
        transition_key = f"{from_state}:{to_state}"
        if workflow_name not in self.transition_handlers:
            self.transition_handlers[workflow_name] = {}

        self.transition_handlers[workflow_name][transition_key] = handler
        self.logger.info(
            f"Registered transition handler for {workflow_name}: {from_state} -> {to_state}"
        )
        return True

    async def create_workflow(
        self, definition_name: str, initial_data: Dict[str, Any] = None
    ) -> Optional[WorkflowInstance]:
        """Create a new workflow instance."""
        if definition_name not in self.workflow_definitions:
            self.logger.error(f"Unknown workflow definition: {definition_name}")
            return None

        definition = self.workflow_definitions[definition_name]

        # Create the instance
        now = datetime.now()
        instance = WorkflowInstance(
            id=str(uuid.uuid4()),
            definition_name=definition_name,
            current_state=definition.initial_state,
            data=initial_data or {},
            created_at=now,
            updated_at=now,
        )

        # Save to Notion if available
        if self.notion_client:
            try:
                # Create entry in Active Workflows database
                notion_data = {
                    "Name": f"{definition_name} - {instance.id[:8]}",
                    "Status": definition.initial_state,
                    "Start Date": now.isoformat(),
                    "Data": json.dumps(initial_data or {}),
                }

                response = await self.notion_client.create_page(
                    database_id=self.active_workflows_db_id, properties=notion_data
                )

                # Store Notion page ID in instance data
                instance.notion_page_id = response.get("id")

            except Exception as e:
                self.logger.error(f"Failed to create workflow in Notion: {str(e)}")

        # Add to active workflows
        self.active_workflows[instance.id] = instance
        self.logger.info(
            f"Created workflow instance {instance.id} of type {definition_name}"
        )

        return instance

    async def transition_workflow(
        self,
        instance: WorkflowInstance,
        to_state: str,
        reason: str,
        agent: str,
        transition_data: Dict[str, Any] = None,
    ) -> WorkflowTransitionResult:
        """Transition a workflow to a new state."""
        definition_name = instance.definition_name

        if definition_name not in self.workflow_definitions:
            return WorkflowTransitionResult(
                success=False, error=f"Unknown workflow definition: {definition_name}"
            )

        definition = self.workflow_definitions[definition_name]

        # Check if transition is allowed
        from_state = instance.current_state
        if to_state not in definition.transitions.get(from_state, []):
            return WorkflowTransitionResult(
                success=False,
                error=f"Invalid transition from {from_state} to {to_state}",
            )

        # Execute transition handler if registered
        transition_key = f"{from_state}:{to_state}"
        handler = self.transition_handlers.get(definition_name, {}).get(transition_key)

        if handler:
            # Prepare context for handler
            context = {
                "instance": instance,
                "from_state": from_state,
                "to_state": to_state,
                "reason": reason,
                "agent": agent,
                "transition_data": transition_data or {},
            }

            try:
                handler_success = await handler(context)

                if not handler_success:
                    return WorkflowTransitionResult(
                        success=False,
                        error=f"Transition handler rejected transition to {to_state}",
                    )
            except Exception as e:
                return WorkflowTransitionResult(
                    success=False, error=f"Transition handler failed: {str(e)}"
                )

        # Record the transition
        instance.record_transition(from_state, to_state, reason, agent, transition_data)

        # Update data if provided
        if transition_data:
            instance.data.update(transition_data)

        # Update in Notion
        if self.notion_client and instance.notion_page_id:
            try:
                await self.notion_client.update_page(
                    page_id=instance.notion_page_id,
                    properties={
                        "Status": to_state,
                        "Data": json.dumps(instance.data),
                        "Last Updated": instance.updated_at.isoformat(),
                    },
                )
            except Exception as e:
                self.logger.warning(f"Failed to update workflow in Notion: {str(e)}")

        # Update active workflows cache
        self.active_workflows[instance.id] = instance

        return WorkflowTransitionResult(
            success=True, new_state=to_state, data=instance.data
        )

    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowInstance]:
        """Get a workflow instance by ID."""
        # Check in-memory cache first
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]

        # Otherwise try to fetch from Notion if client is available
        if self.notion_client:
            try:
                # Query for the instance
                filter_conditions = {
                    "property": "ID",
                    "rich_text": {"equals": workflow_id},
                }

                pages = await self.notion_client.query_database(
                    self.active_workflows_db_id, filter_conditions
                )

                if pages and len(pages) > 0:
                    page = pages[0]

                    # Extract workflow data from page
                    properties = page.get("properties", {})

                    # Extract state from Status
                    status_prop = properties.get("Status", {})
                    current_state = status_prop.get("select", {}).get("name", "unknown")

                    # Extract data JSON
                    data_prop = properties.get("Data", {})
                    data_text = (
                        data_prop.get("rich_text", [{}])[0]
                        .get("text", {})
                        .get("content", "{}")
                    )
                    try:
                        data = json.loads(data_text)
                    except:
                        data = {}

                    # Extract definition name from Name
                    name_prop = properties.get("Name", {})
                    name_text = (
                        name_prop.get("title", [{}])[0]
                        .get("text", {})
                        .get("content", "")
                    )
                    definition_name = (
                        name_text.split(" - ")[0] if " - " in name_text else "unknown"
                    )

                    # Create workflow instance
                    instance = WorkflowInstance(
                        id=workflow_id,
                        definition_name=definition_name,
                        current_state=current_state,
                        data=data,
                        notion_page_id=page.get("id"),
                        created_at=datetime.fromisoformat(
                            page.get("created_time", datetime.now().isoformat())
                        ),
                        updated_at=datetime.fromisoformat(
                            page.get("last_edited_time", datetime.now().isoformat())
                        ),
                    )

                    # Add to cache
                    self.active_workflows[workflow_id] = instance
                    return instance

            except Exception as e:
                self.logger.error(
                    f"Error fetching workflow {workflow_id} from Notion: {str(e)}"
                )

        return None

    async def get_active_workflows(
        self, definition_name: Optional[str] = None, state: Optional[str] = None
    ) -> List[WorkflowInstance]:
        """
        Get active workflow instances, optionally filtered by definition name or state.

        Args:
            definition_name: Optional workflow definition name to filter by
            state: Optional workflow state to filter by

        Returns:
            List of matching workflow instances
        """
        # Filter the in-memory workflows
        result = []
        for workflow in self.active_workflows.values():
            if definition_name and workflow.definition_name != definition_name:
                continue

            if state and workflow.current_state != state:
                continue

            result.append(workflow)

        return result

    async def get_workflow_history(
        self, workflow_id: str
    ) -> Optional[List[WorkflowHistoryEntry]]:
        """Get the history of a workflow instance."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None

        return workflow.history

    async def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow instance.

        Note: This will remove it from active workflows, but history may be retained
        in Notion depending on configuration.
        """
        # Remove from in-memory cache
        if workflow_id in self.active_workflows:
            instance = self.active_workflows.pop(workflow_id)

            # Delete from Notion if available
            if self.notion_client and instance.notion_page_id:
                try:
                    await self.notion_client.archive_page(instance.notion_page_id)
                    self.logger.info(f"Archived workflow {workflow_id} in Notion")
                except Exception as e:
                    self.logger.error(f"Error archiving workflow in Notion: {str(e)}")
                    return False

            self.logger.info(f"Deleted workflow instance {workflow_id}")
            return True

        return False

    def get_workflow_definition(
        self, definition_name: str
    ) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by name."""
        return self.workflow_definitions.get(definition_name)

    def get_all_workflow_definitions(self) -> List[WorkflowDefinition]:
        """Get all registered workflow definitions."""
        return list(self.workflow_definitions.values())

    async def export_workflow_to_json(self, workflow_id: str) -> Optional[str]:
        """Export a workflow instance to JSON for archiving or sharing."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None

        # Convert to JSON-serializable dict
        export_data = {
            "id": workflow.id,
            "definition_name": workflow.definition_name,
            "current_state": workflow.current_state,
            "data": workflow.data,
            "history": [entry.model_dump() for entry in workflow.history],
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat(),
        }

        return json.dumps(export_data, indent=2)

    async def import_workflow_from_json(
        self, json_data: str
    ) -> Optional[WorkflowInstance]:
        """Import a workflow instance from JSON."""
        try:
            data = json.loads(json_data)

            # Validate required fields
            required_fields = ["id", "definition_name", "current_state"]
            for field in required_fields:
                if field not in data:
                    self.logger.error(
                        f"Missing required field '{field}' in workflow JSON"
                    )
                    return None

            # Validate definition exists
            if data["definition_name"] not in self.workflow_definitions:
                self.logger.error(
                    f"Unknown workflow definition: {data['definition_name']}"
                )
                return None

            # Create workflow instance
            instance = WorkflowInstance(
                id=data["id"],
                definition_name=data["definition_name"],
                current_state=data["current_state"],
                data=data.get("data", {}),
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
            )

            # Add history if available
            if "history" in data and isinstance(data["history"], list):
                for entry_data in data["history"]:
                    instance.history.append(WorkflowHistoryEntry(**entry_data))

            # Add to active workflows
            self.active_workflows[instance.id] = instance

            # Optionally sync to Notion
            if self.notion_client:
                try:
                    notion_data = {
                        "Name": f"{instance.definition_name} - {instance.id[:8]}",
                        "Status": instance.current_state,
                        "Start Date": instance.created_at.isoformat(),
                        "Data": json.dumps(instance.data),
                    }

                    response = await self.notion_client.create_page(
                        database_id=self.active_workflows_db_id, properties=notion_data
                    )

                    instance.notion_page_id = response.get("id")

                except Exception as e:
                    self.logger.error(
                        f"Failed to create imported workflow in Notion: {str(e)}"
                    )

            return instance

        except Exception as e:
            self.logger.error(f"Error importing workflow from JSON: {str(e)}")
            return None


class ConditionEvaluator:
    """Utility class for evaluating workflow conditions."""

    @staticmethod
    def evaluate_condition(condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Evaluate a single condition against context data.

        Args:
            condition: Condition definition with field, operator, value
            context: Context data to evaluate against

        Returns:
            True if condition is satisfied, False otherwise
        """
        if not isinstance(condition, dict):
            return False

        field = condition.get("field")
        operator = condition.get("operator")
        expected_value = condition.get("value")

        if not field or not operator:
            return False

        # Get actual value from context using dot notation
        actual_value = ConditionEvaluator.get_field_value(context, field)

        # Compare values
        return ConditionEvaluator.compare_values(actual_value, operator, expected_value)

    @staticmethod
    def get_field_value(data: Dict[str, Any], field_path: str) -> Any:
        """Get a value from a nested dictionary using dot notation."""
        if not data or not field_path:
            return None

        parts = field_path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    @staticmethod
    def compare_values(actual: Any, operator: str, expected: Any) -> bool:
        """Compare values based on operator."""
        if operator == "eq":
            return actual == expected
        elif operator == "ne":
            return actual != expected
        elif operator == "gt":
            return actual > expected if actual is not None else False
        elif operator == "lt":
            return actual < expected if actual is not None else False
        elif operator == "gte":
            return actual >= expected if actual is not None else False
        elif operator == "lte":
            return actual <= expected if actual is not None else False
        elif operator == "in":
            return actual in expected if expected is not None else False
        elif operator == "not_in":
            return actual not in expected if expected is not None else True
        elif operator == "contains":
            return expected in actual if actual is not None else False
        elif operator == "starts_with":
            return actual.startswith(expected) if isinstance(actual, str) else False
        elif operator == "ends_with":
            return actual.endswith(expected) if isinstance(actual, str) else False
        elif operator == "exists":
            return actual is not None
        elif operator == "not_exists":
            return actual is None
        else:
            return False
