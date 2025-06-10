# The HigherSelf Network Server - Comprehensive Zapier Ecosystem Guide

This guide provides comprehensive instructions for implementing a complete Zapier ecosystem for The HigherSelf Network Server, including Tables, Interfaces, Chatbots, Canvases, and Agents across three core areas: Connection Practice Components, Seven Space Integration, and Network Core Functions.

## Table of Contents

1. [Overview](#overview)
2. [Implementation Plan](#implementation-plan)
3. [N8N Integration](#n8n-integration)
   - [Setting Up N8N](#setting-up-n8n)
   - [Creating N8N Workflows](#creating-n8n-workflows)
   - [N8N Agent Examples](#n8n-agent-examples)
4. [Zapier Integration](#zapier-integration)
   - [Setting Up Zapier](#setting-up-zapier)
   - [Creating Zapier Zaps](#creating-zapier-zaps)
   - [Zapier Agent Examples](#zapier-agent-examples)
5. [Server-Side Implementation](#server-side-implementation)
   - [Service Layer](#service-layer)
   - [API Endpoints](#api-endpoints)
   - [Agent Extensions](#agent-extensions)
6. [Security Considerations](#security-considerations)
7. [Testing and Deployment](#testing-and-deployment)

## Overview

The HigherSelf Network Server uses a sophisticated agent system with named personalities (Nyra, Solari, Ruvo, Liora, Sage, Elan, Zevi, and GraceOrchestrator) that maintain Notion as the central hub for all data and workflows. This integration extends that architecture to include N8N and Zapier as additional automation platforms while preserving the core design principles.

## Implementation Plan

1. Create a workflow platform service layer
2. Implement N8N-specific service
3. Implement Zapier-specific service
4. Create API endpoints for external workflow platforms
5. Update Integration Manager to include workflow platforms
6. Create agent extensions for workflow platforms
7. Update environment configuration
8. Create documentation and examples

## N8N Integration

### Setting Up N8N

1. **Install N8N** (if self-hosting):

   ```bash
   npm install n8n -g
   ```

2. **Start N8N**:

   ```bash
   n8n start
   ```

3. **Access the N8N interface** (default: <http://localhost:5678>)

4. **Configure environment variables**:
   - Create a `.env` file in your N8N directory
   - Add necessary API keys and credentials

### Creating N8N Workflows

#### Basic Workflow Structure

All N8N workflows should follow this general structure to maintain compatibility with your server:

1. **Trigger Node** (Webhook, Schedule, etc.)
2. **Data Validation & Transformation**
3. **Notion Operations**
4. **Business Logic**
5. **Callback to Server**

#### Authentication

For secure communication between your server and N8N:

1. Use webhook secrets for incoming webhooks
2. Use API keys for outgoing requests
3. Store credentials securely in N8N's credential store

### N8N Agent Examples

#### Lead Capture Agent (Nyra)

```yaml
1. Webhook Trigger Node
   - Endpoint: /n8n/webhooks/lead-capture
   - Method: POST
   - Authentication: Bearer Token

2. Function Node - Data Validation
   - Validate incoming lead data
   - Transform to standard format

3. Notion Node - Check for Existing Contact
   - Query Contacts & Profiles DB
   - Check if lead already exists

4. IF Node - New or Existing Contact
   - If new: Create new contact
   - If existing: Update existing contact

5. Notion Node - Create/Update Contact
   - Create or update contact in Notion

6. Notion Node - Create Workflow Instance
   - Create workflow instance in Active Workflow Instances DB

7. Notion Node - Create Tasks
   - Create initial tasks in Master Tasks DB

8. HTTP Request Node - Notify Server
   - Send confirmation back to your server
   - Include Notion page IDs
```

#### Booking Agent (Solari)

```yaml
1. Webhook Trigger Node
   - Endpoint: /n8n/webhooks/booking
   - Method: POST
   - Authentication: Bearer Token

2. Function Node - Data Validation
   - Validate booking data
   - Transform to standard format

3. Notion Node - Check for Existing Contact
   - Query Contacts & Profiles DB
   - Check if contact already exists

4. Notion Node - Create/Update Contact
   - Create or update contact in Notion

5. Notion Node - Create Booking Record
   - Create booking record in appropriate DB

6. Notion Node - Create Workflow Instance
   - Create workflow instance for booking process

7. Notion Node - Create Tasks
   - Create pre-booking tasks

8. HTTP Request Node - Notify Server
   - Send confirmation back to your server
```

## Zapier Integration

### Setting Up Zapier

1. **Create or log in to your Zapier account**
2. **Create a new Zap**
3. **Configure authentication**:
   - Set up Notion integration
   - Configure webhook authentication

### Creating Zapier Zaps

#### Basic Zap Structure

All Zapier Zaps should follow this general structure:

1. **Trigger** (Webhook, Schedule, etc.)
2. **Data Transformation** (Code by Zapier)
3. **Notion Operations**
4. **Business Logic**
5. **Callback to Server**

### Zapier Agent Examples

#### Lead Capture Agent (Nyra) - Zapier Version

```yaml
1. Webhook Trigger
   - URL: Provided by Zapier
   - Method: POST

2. Code by Zapier
   - Validate and transform lead data

3. Notion - Find Records
   - Search for existing contact

4. Path A (New Contact)
   - Notion - Create Record in Contacts & Profiles DB
   - Notion - Create Workflow Instance
   - Notion - Create Tasks

5. Path B (Existing Contact)
   - Notion - Update Record in Contacts & Profiles DB
   - Notion - Create Workflow Instance
   - Notion - Create Tasks

6. Webhook
   - Send confirmation to your server
```

#### Task Management Agent (Ruvo)

```yaml
1. Schedule Trigger
   - Run daily to check for tasks

2. Notion - Find Records
   - Search for tasks due today

3. Filter
   - Filter for tasks that need attention

4. For Each Task
   - Notion - Get task details
   - Determine next action

5. Path A (Notification Needed)
   - Email - Send notification
   - Slack - Send message

6. Path B (Task Update Needed)
   - Notion - Update task status
```

## Server-Side Implementation

### Service Layer

Create these service files to manage external workflow platforms:

1. **workflow_platform_service.py** - Base service for workflow platforms
2. **n8n_service.py** - N8N-specific service implementation
3. **zapier_service.py** - Zapier-specific service implementation

### API Endpoints

Create these API endpoints to handle callbacks from N8N and Zapier:

1. **/api/external/n8n/callback** - Handle callbacks from N8N workflows
2. **/api/external/zapier/callback** - Handle callbacks from Zapier Zaps

### Agent Extensions

Extend your agent system to work with workflow platforms:

1. **workflow_platform_agent_mixin.py** - Mixin for agents to work with workflow platforms
2. Update **base_agent.py** to include the workflow platform mixin

### Environment Configuration

Update your environment configuration to include workflow platform settings:

```env
# Workflow Platform Settings
ENABLE_N8N=true
N8N_API_KEY=your_n8n_api_key
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/endpoint
N8N_WEBHOOK_SECRET=your_n8n_webhook_secret

ENABLE_ZAPIER=true
ZAPIER_API_KEY=your_zapier_api_key
ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/your-zapier-webhook
ZAPIER_WEBHOOK_SECRET=your_zapier_webhook_secret
```

## Security Considerations

1. **Authentication**
   - Use webhook secrets or API keys for authentication
   - Store credentials securely in N8N and Zapier
   - Implement signature verification for all webhooks
   - Use HTTPS for all communications
   - Rotate API keys and secrets regularly

2. **Data Validation**
   - Validate all incoming data before processing
   - Implement proper error handling
   - Sanitize data to prevent injection attacks
   - Validate data types and formats
   - Implement schema validation using Pydantic models

3. **Rate Limiting**
   - Implement rate limiting to prevent abuse
   - Monitor API usage
   - Set up alerts for unusual activity
   - Implement exponential backoff for retries
   - Add circuit breakers for failing services

4. **Access Control**
   - Implement role-based access control
   - Limit access to sensitive operations
   - Audit all access to sensitive data
   - Implement IP whitelisting for critical endpoints

## Testing and Deployment

### Testing

1. **Unit Testing**
   - Test each service and endpoint individually
   - Use mock data to simulate workflow platform interactions

2. **Integration Testing**
   - Test the full flow from workflow platform to server and back
   - Verify data integrity throughout the process

3. **Security Testing**
   - Test authentication mechanisms
   - Verify signature validation
   - Check for common vulnerabilities

### Deployment

1. **Development Environment**
   - Deploy to development environment first
   - Test with real but non-critical data
   - Verify all components work together

2. **Production Environment**
   - Deploy to production after thorough testing
   - Monitor closely during initial deployment
   - Have rollback plan ready

3. **Documentation**
   - Update documentation with deployment details
   - Create user guides for staff
   - Document troubleshooting procedures

## Implementation Code Examples

### Workflow Platform Service

```python
# services/workflow_platform_service.py
"""
Workflow Platform Service for The HigherSelf Network Server.

This service manages integration with external workflow platforms like N8N and Zapier,
ensuring proper data flow between these platforms and Notion as the central hub.
"""

import os
import json
import hmac
import hashlib
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from models.base import ApiPlatform
from services.notion_service import NotionService


class WorkflowPlatformConfig(BaseModel):
    """Configuration for workflow platforms."""
    platform_name: str
    platform_type: str  # "n8n" or "zapier"
    webhook_url: Optional[str] = None
    api_key: Optional[str] = None
    enabled: bool = True
    webhook_secret: Optional[str] = None


class WorkflowPlatformService:
    """
    Service for managing external workflow platforms like N8N and Zapier.
    Ensures proper data flow between these platforms and Notion as the central hub.
    """

    def __init__(
        self,
        platform_config: WorkflowPlatformConfig,
        notion_service: Optional[NotionService] = None
    ):
        """
        Initialize the workflow platform service.

        Args:
            platform_config: Configuration for the workflow platform
            notion_service: NotionService instance or None to create from environment
        """
        self.config = platform_config
        self.notion_service = notion_service or NotionService.from_env()
        self.logger = logger.bind(service=f"{platform_config.platform_name}Service")

        self.logger.info(f"Initialized {platform_config.platform_name} workflow platform service")

    async def send_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an event to the workflow platform.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Response from the workflow platform
        """
        # Implementation details for sending events to the workflow platform
        pass

    async def process_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a callback from the workflow platform.

        Args:
            callback_data: Callback data from the workflow platform

        Returns:
            Processing result
        """
        # Implementation details for processing callbacks from the workflow platform
        pass

    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify the signature of a webhook payload.

        Args:
            payload: Raw webhook payload
            signature: Signature header from the webhook

        Returns:
            True if signature is valid, False otherwise
        """
        # Implementation details for signature verification
        pass
```

### N8N Service Implementation

```python
# services/n8n_service.py
"""
N8N Service for The HigherSelf Network Server.

This service manages integration with N8N workflows,
ensuring proper data flow between N8N and Notion as the central hub.
"""

import os
import json
import hmac
import hashlib
import aiohttp
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from loguru import logger

from models.base import ApiPlatform
from services.workflow_platform_service import WorkflowPlatformService, WorkflowPlatformConfig


class N8NService(WorkflowPlatformService):
    """
    Service for managing N8N workflows.
    Ensures proper data flow between N8N and Notion as the central hub.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        webhook_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        enabled: bool = True,
        **kwargs
    ):
        """
        Initialize the N8N service.

        Args:
            api_key: N8N API key
            webhook_url: N8N webhook URL
            webhook_secret: Secret for webhook authentication
            enabled: Whether the N8N integration is enabled
        """
        config = WorkflowPlatformConfig(
            platform_name="N8N",
            platform_type="n8n",
            api_key=api_key or os.environ.get("N8N_API_KEY"),
            webhook_url=webhook_url or os.environ.get("N8N_WEBHOOK_URL"),
            webhook_secret=webhook_secret or os.environ.get("N8N_WEBHOOK_SECRET"),
            enabled=enabled
        )

        super().__init__(platform_config=config, **kwargs)

        self.session = None

    async def initialize(self):
        """Initialize the N8N service."""
        self.session = aiohttp.ClientSession()
        self.logger.info("N8N service initialized")

    async def close(self):
        """Close the N8N service."""
        if self.session:
            await self.session.close()
        self.logger.info("N8N service closed")

    async def send_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an event to N8N.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Response from N8N
        """
        if not self.config.webhook_url:
            self.logger.warning("No webhook URL configured for N8N")
            return {"success": False, "message": "No webhook URL configured"}

        if not self.config.enabled:
            self.logger.info("N8N integration is disabled")
            return {"success": False, "message": "Integration is disabled"}

        if not self.session:
            await self.initialize()

        # Prepare the payload
        payload = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": event_data
        }

        # Add signature if webhook secret is configured
        headers = {
            "Content-Type": "application/json"
        }

        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        try:
            # Send the request to N8N
            async with self.session.post(
                self.config.webhook_url,
                json=payload,
                headers=headers
            ) as response:
                response_data = await response.json()

                if response.status >= 400:
                    self.logger.error(f"Error sending event to N8N: {response_data}")
                    return {
                        "success": False,
                        "message": f"Error sending event to N8N: {response.status}",
                        "data": response_data
                    }

                self.logger.info(f"Successfully sent event to N8N: {event_type}")
                return {
                    "success": True,
                    "message": "Event sent successfully",
                    "data": response_data
                }
        except Exception as e:
            self.logger.error(f"Error sending event to N8N: {e}")
            return {
                "success": False,
                "message": f"Error sending event to N8N: {str(e)}"
            }
```

### API Endpoints for External Workflow Platforms

```python
# api/external_workflows.py
"""
API endpoints for external workflow platforms like N8N and Zapier.
"""

import os
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Header, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

from services.n8n_service import N8NService
from services.zapier_service import ZapierService
from services.notion_service import NotionService
from config.testing_mode import is_api_disabled, TestingMode


# Response model for webhook endpoints
class WebhookResponse(BaseModel):
    """Standard response format for webhook endpoints."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# Initialize router
router = APIRouter(prefix="/external", tags=["external-workflows"])

# Initialize services
notion_service = NotionService.from_env()
n8n_service = N8NService(notion_service=notion_service)
zapier_service = ZapierService(notion_service=notion_service)


@router.post("/n8n/callback", response_model=WebhookResponse)
async def n8n_callback(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle callbacks from N8N workflows.

    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks

    Returns:
        WebhookResponse with success status and message
    """
    try:
        # Parse request body
        body = await request.json()

        # Process the callback
        result = await n8n_service.process_callback(body)

        return WebhookResponse(
            success=True,
            message="Successfully processed N8N callback",
            data=result
        )
    except Exception as e:
        logger.error(f"Error processing N8N callback: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing callback: {str(e)}")
```

## Next Steps

1. **Implement the services** outlined in this guide
2. **Create N8N workflows** for each agent personality
3. **Set up Zapier Zaps** for complementary automation
4. **Test the integration** thoroughly
5. **Deploy to production** when ready
6. **Train staff** on using the new automation capabilities

## Conclusion

By integrating N8N and Zapier with The HigherSelf Network Server, you can extend your automation capabilities while maintaining Notion as the central hub for all data and workflows. This approach gives you the flexibility to leverage the strengths of each platform while ensuring data consistency and process integrity.

Remember that all integrations should follow these core principles:

1. Notion remains the central hub for all data and workflows
2. All agents maintain consistent personalities and capabilities
3. Security and data integrity are paramount
4. Proper error handling and logging are essential

With this implementation, you'll have a powerful, flexible automation system that can adapt to your evolving business needs while maintaining the structured, centralized approach of The HigherSelf Network Server.
