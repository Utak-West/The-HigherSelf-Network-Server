"""
Enhanced Agent Framework for The HigherSelf Network Server.

This module provides an improved agent framework with protocol-based
capabilities, enhanced logging, dynamic capability registration, and
activity tracking.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Set, TypeVar
from uuid import uuid4

from pydantic import BaseModel

# Import existing models and services as needed
from services.notion_service import NotionService

# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)


class AgentCapability(Protocol):
    """Protocol defining a capability that agents can utilize."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute this capability with the given context."""
        ...


class AgentMetrics(BaseModel):
    """Metrics tracked for agent performance and activity."""

    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_execution_time_ms: float = 0
    last_execution_timestamp: Optional[datetime] = None
    average_execution_time_ms: float = 0
    capabilities_used: Dict[str, int] = {}  # capability_name -> usage_count
    errors_by_type: Dict[str, int] = {}  # error_type -> count

    def record_execution(self, capability_name: str, duration_ms: float, success: bool):
        """Record a capability execution."""
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1

        self.total_execution_time_ms += duration_ms
        self.last_execution_timestamp = datetime.now()
        self.average_execution_time_ms = (
            self.total_execution_time_ms / self.total_executions
        )

        # Track capability usage
        if capability_name in self.capabilities_used:
            self.capabilities_used[capability_name] += 1
        else:
            self.capabilities_used[capability_name] = 1

    def record_error(self, error_type: str):
        """Record an error by type."""
        if error_type in self.errors_by_type:
            self.errors_by_type[error_type] += 1
        else:
            self.errors_by_type[error_type] = 1


class BaseAgent(ABC):
    """
    Enhanced base agent with capability registry and improved logging.

    This implementation improves the agent architecture by:
    1. Formalizing the capability pattern
    2. Adding structured logging
    3. Supporting dynamic capability registration
    4. Providing activity tracking
    """

    def __init__(self, name: str, notion_client=None, logger=None, **kwargs):
        self.id = str(uuid4())
        self.name = name
        self.notion_client = notion_client
        self.capabilities: Dict[str, AgentCapability] = {}
        self.logger = logger or logging.getLogger(f"agent.{name.lower()}")
        self.metrics = AgentMetrics()
        # IDs of agents this agent depends on
        self.dependencies: Set[str] = set()
        self._initialize_capabilities()
        self.logger.info(f"Agent {name} initialized with ID {self.id}")

    def _initialize_capabilities(self) -> None:
        """Initialize agent capabilities. Override in subclasses."""
        pass

    def register_capability(self, name: str, capability: AgentCapability) -> None:
        """Register a new capability with this agent."""
        self.capabilities[name] = capability
        self.logger.debug(f"Registered capability: {name}")

    async def use_capability(
        self, name: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use a registered capability with performance tracking."""
        if name not in self.capabilities:
            self.logger.error(f"Capability {name} not available")
            raise ValueError(f"Capability {name} not available for agent {self.name}")

        self.logger.debug(f"Using capability: {name}")

        # Track execution time
        start_time = datetime.now()
        success = False
        result = {}

        try:
            result = await self.capabilities[name].execute(context)
            success = True
            return result
        except Exception as e:
            self.logger.error(f"Error executing capability {name}: {str(e)}")
            self.metrics.record_error(type(e).__name__)
            raise
        finally:
            # Calculate duration and update metrics
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.record_execution(name, duration_ms, success)

    def register_dependency(self, agent_id: str) -> None:
        """Register another agent as a dependency."""
        self.dependencies.add(agent_id)
        self.logger.debug(f"Registered dependency on agent: {agent_id}")

    @abstractmethod
    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an event received by this agent."""
        pass

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check the health status of this agent."""
        pass

    async def log_activity(self, activity_type: str, details: Dict[str, Any]) -> None:
        """Log agent activity to Notion for audit and tracking."""
        if not self.notion_client:
            self.logger.warning("Cannot log activity: No Notion client available")
            return

        try:
            # Structure the activity for Notion
            activity = {
                "Agent": self.name,
                "Type": activity_type,
                "Timestamp": datetime.now().isoformat(),
                "Details": json.dumps(details),
                "Status": "Completed",
            }

            # Log to Notion Agent Communication database
            await self.notion_client.create_page(
                database_id="agent_communication_database_id", properties=activity
            )

            self.logger.info(f"Logged activity: {activity_type}")
        except Exception as e:
            self.logger.error(f"Failed to log activity: {str(e)}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics as a dictionary."""
        metrics_dict = self.metrics.dict()
        metrics_dict.update(
            {
                "agent_id": self.id,
                "agent_name": self.name,
                "capability_count": len(self.capabilities),
                "dependencies": list(self.dependencies),
            }
        )
        return metrics_dict

    async def reset_metrics(self) -> None:
        """Reset the agent's metrics."""
        self.metrics = AgentMetrics()
        self.logger.info(f"Reset metrics for agent {self.name}")


class AgentManager:
    """
    Manages a group of agents, handles agent discovery, registration,
    and communication.
    """

    def __init__(self, notion_service: Optional[NotionService] = None):
        self.agents: Dict[str, BaseAgent] = {}
        self.notion_service = notion_service
        self.logger = logging.getLogger("agent.manager")

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the manager."""
        self.agents[agent.id] = agent
        self.logger.info(f"Registered agent {agent.name} with ID {agent.id}")

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def get_all_agents(self) -> List[BaseAgent]:
        """Get all registered agents."""
        return list(self.agents.values())

    async def dispatch_event(
        self, agent_id: str, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch an event to a specific agent."""
        agent = self.get_agent(agent_id)
        if not agent:
            self.logger.error(f"Cannot dispatch event: Agent {agent_id} not found")
            raise ValueError(f"Agent {agent_id} not found")

        self.logger.debug(f"Dispatching event {event_type} to agent {agent.name}")
        return await agent.process_event(event_type, event_data)

    async def broadcast_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Broadcast an event to all agents."""
        self.logger.debug(
            f"Broadcasting event {event_type} to {len(self.agents)} agents"
        )

        results = {}
        for agent_id, agent in self.agents.items():
            try:
                result = await agent.process_event(event_type, event_data)
                results[agent_id] = result
            except Exception as e:
                self.logger.error(
                    f"Error processing event {event_type} by agent {agent.name}: "
                    f"{str(e)}"
                )
                results[agent_id] = {"error": str(e)}

        return {"results": results}

    async def check_all_health(self) -> Dict[str, Dict[str, Any]]:
        """Check the health of all agents."""
        health_results = {}
        for agent_id, agent in self.agents.items():
            try:
                health = await agent.check_health()
                health_results[agent_id] = health
            except Exception as e:
                self.logger.error(
                    f"Error checking health of agent {agent.name}: {str(e)}"
                )
                health_results[agent_id] = {"status": "error", "error": str(e)}

        return health_results

    async def synchronize_with_notion(self) -> int:
        """Synchronize the agent registry with Notion."""
        if not self.notion_service:
            self.logger.warning("Cannot synchronize: No Notion service available")
            return 0

        try:
            # For each registered agent, ensure it's in Notion
            sync_count = 0
            for agent in self.agents.values():
                # Check if agent implements the register_in_notion method
                if hasattr(agent, "register_in_notion") and callable(
                    getattr(agent, "register_in_notion")
                ):
                    await agent.register_in_notion()
                    sync_count += 1

            self.logger.info(f"Synchronized {sync_count} agents with Notion")
            return sync_count
        except Exception as e:
            self.logger.error(f"Error synchronizing agents with Notion: {str(e)}")
            raise
