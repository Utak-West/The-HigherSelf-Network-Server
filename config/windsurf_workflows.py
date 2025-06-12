"""
Windsurf Workflow Configuration Module.
Loads and provides access to workflow definitions and settings from .windsurf/workflows.json
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WindsurfWorkflowConfig:
    """Manages Windsurf workflow configurations and settings."""

    def __init__(self):
        self.workflows = {}
        self.settings = {}
        self.loaded = False
        self._load_config()

    def _load_config(self) -> None:
        """Load workflow configurations from .windsurf/workflows.json."""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                ".windsurf",
                "workflows.json",
            )

            if not os.path.exists(config_path):
                logger.warning(f"Windsurf workflow config not found at {config_path}")
                return

            with open(config_path, "r") as f:
                config = json.load(f)

            # Process workflows
            self.workflows = {w["id"]: w for w in config.get("workflows", [])}

            # Load settings
            self.settings = config.get("settings", {})

            self.loaded = True
            logger.info(
                f"Loaded {len(self.workflows)} workflows from Windsurf configuration"
            )

        except Exception as e:
            logger.error(f"Error loading Windsurf workflow configuration: {str(e)}")

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a workflow definition by ID."""
        return self.workflows.get(workflow_id)

    def get_all_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Get all workflow definitions."""
        return self.workflows

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value with optional default."""
        return self.settings.get(key, default)

    def get_workflows_for_agent(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get all workflows that have the specified agent as an owner."""
        return [
            workflow
            for workflow in self.workflows.values()
            if agent_type in workflow.get("agentOwners", [])
        ]

    def get_available_states(self, workflow_id: str) -> List[str]:
        """Get all available states for a workflow."""
        workflow = self.get_workflow(workflow_id)
        if workflow:
            return workflow.get("states", [])
        return []

    def is_valid_transition(
        self, workflow_id: str, from_state: str, to_state: str
    ) -> bool:
        """Check if a state transition is valid for the given workflow."""
        # This is a simplified implementation
        # A more complete implementation would check the actual transition rules
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False

        states = workflow.get("states", [])
        return from_state in states and to_state in states


# Create a singleton instance
windsurf_workflows = WindsurfWorkflowConfig()


def get_workflow_config() -> WindsurfWorkflowConfig:
    """Get the singleton workflow config instance."""
    return windsurf_workflows
