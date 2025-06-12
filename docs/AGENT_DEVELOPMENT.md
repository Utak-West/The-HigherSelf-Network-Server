# Agent Development Guide

This document provides guidance on developing new agents for The HigherSelf Network Server, following The HigherSelf Network's core principles.

## Agent Architecture

All agents in the system inherit from the `BaseAgent` abstract base class, which provides common functionality:

- Notion integration
- Workflow state management
- History logging
- Task creation
- Health checking

## Creating a New Agent

To create a new agent:

1. Create a new file in the `agents` directory
2. Define a class that inherits from `BaseAgent`
3. Implement the required abstract methods
4. Register the agent in `agents/__init__.py`
5. Initialize the agent in `main.py`

### Required Methods

Each agent must implement:

- `process_event(event_type, event_data)` - Process incoming events
- `check_health()` - Check the agent's health status

### Example Agent Implementation

```python
from agents.base_agent import BaseAgent
from models.base import AgentCapability, ApiPlatform

class MyCustomAgent(BaseAgent):
    def __init__(
        self,
        agent_id: str = "CustomAgent_001",
        name: str = "Custom Process Agent",
        description: str = "Handles custom processes",
        version: str = "1.0.0",
        business_entities: List[str] = None
    ):
        capabilities = [
            AgentCapability.WORKFLOW_MANAGEMENT,
            AgentCapability.TASK_CREATION
        ]

        apis_utilized = [
            ApiPlatform.NOTION,
            ApiPlatform.HUBSPOT
        ]

        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            version=version,
            capabilities=capabilities,
            apis_utilized=apis_utilized,
            business_entities=business_entities
        )

    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation here
        pass

    async def check_health(self) -> Dict[str, Any]:
        # Implementation here
        pass
```

## Agent Modularity

Follow these principles when developing agents:

1. **Single Responsibility**: Each agent should have a specific, well-defined purpose
2. **Configuration over Code**: Drive agent behavior through configurations stored in Notion
3. **Idempotent Operations**: Ensure operations can be safely retried
4. **Standardized Logging**: Log all significant actions to the workflow history
5. **Error Handling**: Gracefully handle and report errors

## Integrating with Notion

All agents must:

1. Register themselves in the Agent Registry database
2. Log actions in the Active Workflow Instances database
3. Create tasks in the Master Tasks Database as needed
4. Maintain accurate workflow state information

## Webhook Integration

When creating an agent that responds to webhook events:

1. Define a clear webhook payload model with Pydantic
2. Add an endpoint in `api/server.py` to handle the webhook
3. Process the webhook in a background task to prevent timeouts
4. Use proper authentication for webhook security

## Testing Agents

To test an agent:

1. Create unit tests for specific agent functionality
2. Use mock Notion responses for testing
3. Test event handling with different event types
4. Ensure idempotent behavior with duplicate events

## Deployment

All agents should be deployed on The HigherSelf Network Server, configured with:

1. Proper environment variables for API credentials
2. Logging configured to the standard format
3. Proper monitoring for agent health
4. Connection to the central notification system

## Best Practices

1. Follow the Pydantic AI framework rigorously
2. Document all agent capabilities and event handling
3. Use type hints consistently
4. Handle API rate limits
5. Provide detailed logs for troubleshooting
6. Keep agent logic modular and replaceable
