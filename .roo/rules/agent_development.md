# HigherSelf Agent Developer

## Description
Specialized mode for developing and testing HigherSelf Network agents

## Instructions
- Follow the Pydantic AI framework rigorously
- Ensure all agents inherit from BaseAgent
- Implement required abstract methods: process_event() and check_health()
- Maintain single responsibility principle for each agent
- Use configuration over code - store behavior configs in Notion
- Ensure idempotent operations for safe retries
- Register agents in the Agent Registry database
- Log actions in Active Workflow Instances database
- Create tasks in Master Tasks Database as needed
- Maintain accurate workflow state information

## Capabilities
- Read and analyze existing agent implementations
- Generate new agent code following established patterns
- Create unit tests for agent functionality
- Implement webhook handlers with proper Pydantic models
- Document agent capabilities and event handling

## Agent Template

```python
"""
{agent_name} - {agent_description}

This agent is responsible for {primary_responsibility}.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent
from models.base import AgentCapability, ApiPlatform
from models.notion_db_models import WorkflowInstance


class {agent_class_name}(BaseAgent):
    """
    {agent_name} - {agent_description}

    {agent_personality_description}
    """

    def __init__(self, notion_client=None, **kwargs):
        agent_id = kwargs.get("agent_id", "{agent_id}")
        description = "{agent_description}"
        super().__init__(
            agent_id=agent_id,
            name="{agent_name}",
            description=description,
            notion_service=notion_client,
            capabilities=[{agent_capabilities}],
            apis_utilized=[{agent_apis}],
            business_entities=[{business_entities}],
            **kwargs
        )
        self.agent_type = "{agent_type}"
        self.tone = "{agent_tone}"

    async def run(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        {run_method_description}

        Args:
            event_data: {event_data_description}

        Returns:
            Dict containing processing results and any created entity IDs
        """
        self.logger.info(f"{agent_name} processing {agent_type} event: {event_data.get('{event_key}', 'unknown')}")

        # Implementation logic here

        return {"status": "processed", "message": "{success_message}"}

    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an event received by this agent.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Processing result
        """
        # Map event types to handler methods
        event_handlers = {
            # Add event types and handlers here
        }

        handler = event_handlers.get(event_type)
        if not handler:
            self.logger.warning(f"Unsupported event type for {agent_name}: {event_type}")
            return {"status": "error", "message": f"Unsupported event type: {event_type}"}

        try:
            return await handler(event_data)
        except Exception as e:
            self.logger.error(f"Error processing {event_type}: {e}")
            return {"status": "error", "message": str(e)}

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.

        Returns:
            Dict containing health status information
        """
        try:
            # Perform health checks here
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id,
                "name": self.name,
                "version": self.version,
                "details": {
                    "apis_connected": True,
                    "notion_connected": True
                }
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id,
                "name": self.name,
                "version": self.version,
                "error": str(e)
            }
```
