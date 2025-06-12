"""
MongoDB Repository Factory for The HigherSelf Network Server.

This module provides a factory for creating MongoDB repositories,
making it easy to get the appropriate repository for a given model type.
"""

from typing import Any, Dict, Optional, Type, TypeVar

from loguru import logger

from models.mongodb_models import (AgentCommunicationDocument, AgentDocument,
                                   ApiIntegrationDocument, MongoBaseModel,
                                   SystemHealthDocument, TaskDocument,
                                   WorkflowDocument, WorkflowInstanceDocument)
from repositories.mongodb_repository import (AgentCommunicationRepository,
                                             AgentRepository,
                                             ApiIntegrationRepository,
                                             MongoRepository,
                                             SystemHealthRepository,
                                             TaskRepository,
                                             WorkflowInstanceRepository,
                                             WorkflowRepository)

# Type variable for repository generic type
T = TypeVar("T", bound=MongoBaseModel)


class MongoRepositoryFactory:
    """Factory for creating MongoDB repositories."""

    _instance = None
    _repositories: Dict[str, Any] = {}

    def __new__(cls):
        """Singleton pattern to ensure only one instance of the factory exists."""
        if cls._instance is None:
            cls._instance = super(MongoRepositoryFactory, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the factory with repository instances."""
        # Create repository instances
        self._repositories = {
            "agent": AgentRepository(),
            "workflow": WorkflowRepository(),
            "workflow_instance": WorkflowInstanceRepository(),
            "task": TaskRepository(),
            "agent_communication": AgentCommunicationRepository(),
            "api_integration": ApiIntegrationRepository(),
            "system_health": SystemHealthRepository(),
        }

        # Map model classes to repository types
        self._model_to_repo = {
            AgentDocument: "agent",
            WorkflowDocument: "workflow",
            WorkflowInstanceDocument: "workflow_instance",
            TaskDocument: "task",
            AgentCommunicationDocument: "agent_communication",
            ApiIntegrationDocument: "api_integration",
            SystemHealthDocument: "system_health",
        }

        logger.info("MongoDB repository factory initialized")

    def get_repository(self, repo_type: str) -> Optional[MongoRepository]:
        """
        Get a repository by type name.

        Args:
            repo_type: Repository type name (e.g., "agent", "workflow")

        Returns:
            Repository instance or None if not found
        """
        if repo_type not in self._repositories:
            logger.warning(f"Repository type '{repo_type}' not found")
            return None

        return self._repositories[repo_type]

    def get_repository_for_model(
        self, model_class: Type[T]
    ) -> Optional[MongoRepository[T]]:
        """
        Get a repository for a model class.

        Args:
            model_class: Model class to get repository for

        Returns:
            Repository instance or None if not found
        """
        if model_class not in self._model_to_repo:
            logger.warning(
                f"No repository found for model class '{model_class.__name__}'"
            )
            return None

        repo_type = self._model_to_repo[model_class]
        return self._repositories[repo_type]

    def get_agent_repository(self) -> AgentRepository:
        """Get the agent repository."""
        return self._repositories["agent"]

    def get_workflow_repository(self) -> WorkflowRepository:
        """Get the workflow repository."""
        return self._repositories["workflow"]

    def get_workflow_instance_repository(self) -> WorkflowInstanceRepository:
        """Get the workflow instance repository."""
        return self._repositories["workflow_instance"]

    def get_task_repository(self) -> TaskRepository:
        """Get the task repository."""
        return self._repositories["task"]

    def get_agent_communication_repository(self) -> AgentCommunicationRepository:
        """Get the agent communication repository."""
        return self._repositories["agent_communication"]

    def get_api_integration_repository(self) -> ApiIntegrationRepository:
        """Get the API integration repository."""
        return self._repositories["api_integration"]

    def get_system_health_repository(self) -> SystemHealthRepository:
        """Get the system health repository."""
        return self._repositories["system_health"]


# For easy import and use throughout the application
mongo_repository_factory = MongoRepositoryFactory()
