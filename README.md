# The HigherSelf Network Server: Notion Integration

**Version:** 1.0.0  
**Date:** May 9, 2025  
**Created for:** The HigherSelf Network  

## Overview

This repository contains The HigherSelf Network Server system optimized for Notion integration and automation. It establishes Notion as the central hub for data management, workflow tracking, and automation for The HigherSelf Network, supporting the operations of The Connection Practice and The 7 Space.

The system follows the Pydantic AI framework for data validation and includes a robust agent architecture that interacts with various external systems while maintaining Notion as the single source of truth for operational data.

## Core Features

- **Centralized Notion Database Integration:** Aligns with the 16 Notion database structures defined in the specifications
- **Pydantic Model Framework:** All data structures use Pydantic for validation and serialization
- **Agent-based Architecture:** Modular agents with specific responsibilities and capabilities
- **Webhook Support:** Endpoints for third-party system integration
- **State Machine Workflow Tracking:** Structured workflow instances with history logging
- **Extensible Design:** Easy to add new agents and integrations

## Notion Database Structure (16-Database Design)

### Core Operational Databases
1. **Business Entities Registry**: List of business entities using the system
2. **Contacts & Profiles**: Unified customer/contact database
3. **Community Hub**: Community member profiles and engagement tracking
4. **Products & Services**: Catalog of available products and services
5. **Active Workflow Instances**: Currently active workflow instances
6. **Marketing Campaigns**: Marketing initiatives and performance tracking
7. **Feedback & Surveys**: Customer feedback and survey responses
8. **Rewards & Bounties**: Incentive programs and achievements
9. **Master Tasks**: Centralized task management system

### Agent & System Support Databases

1. **Agent Communication Patterns**: Patterns for agent interaction
2. **Agent Registry**: Inventory of available agents and their capabilities
3. **API Integrations Catalog**: Catalog of integrated external services
4. **Data Transformations Registry**: Data mapping configurations
5. **Notifications Templates**: Templates for notifications
6. **Use Cases Library**: Documented use cases for reference
7. **Workflows Library**: Template workflows that can be instantiated

## Automation Flows & Agents

The system implements the following key automation flows using specialized agents:

1. **Lead Capture & Initial Processing**: Consolidates leads from Typeform, Snov.io, Userfeedback, and other sources.
   - Implemented by `LeadCaptureAgent` and `TaskManagementAgent`

2. **Retreat Booking Management**: Automates the booking process for retreats via Amelia.
   - Implemented by `BookingAgent` and `TaskManagementAgent`

3. **Art Sale & Fulfillment**: Manages WooCommerce orders, especially for art products.
   - Implemented by `BookingAgent` (handles orders too) and `TaskManagementAgent`

4. **Marketing Email Campaign**: Manages email campaigns through Beehiiv.
   - Implemented by `MarketingCampaignAgent` and `LeadCaptureAgent`

5. **Automated Task Management**: Creates and assigns tasks based on workflow events.
   - Implemented by `TaskManagementAgent`

6. **Community Engagement**: Handles Circle.so community interactions and member management.
   - Implemented by `CommunityEngagementAgent` and `TaskManagementAgent`

7. **Content Creation & Distribution**: Manages content lifecycle from idea to publication.
   - Implemented by `ContentLifecycleAgent` and `MarketingCampaignAgent`

8. **Audience Analysis & Segmentation**: Creates and manages audience segments for targeted content.
   - Implemented by `AudienceSegmentationAgent` and `MarketingCampaignAgent`

All agents maintain Notion as the central hub for data storage and processing.

## Agent Types

The system currently includes the following agent types:

1. **Lead Capture Agent (`LeadCaptureAgent`)**: Captures leads from sources like Typeform and website forms, with optional HubSpot CRM synchronization
2. **Booking Detection Agent (`BookingAgent`)**: Processes retreat bookings from Amelia, creating and managing workflow instances

Additional agents can be implemented following the same pattern by extending the `BaseAgent` class.

## Core Integration Points

- **Notion API:** Central data storage and workflow tracking
- **TypeForm:** Lead capture from forms
- **HubSpot:** CRM synchronization
- **Amelia:** Booking and scheduling system
- **Additional support planned for:** Airtable, WooCommerce, Plaud Transcription, TutorLM

## Installation

### Prerequisites

- Python 3.10+
- Access to The HigherSelf Network Server
- Notion API credentials
- API keys for integrated services

### Setup

1. Clone the repository to The HigherSelf Network Server:

```bash
git clone <repository_url> higherself-network-server
cd higherself-network-server
```

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

1. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Configure environment variables:

```bash
cp .env.example .env
```

Edit the `.env` file with your API credentials and database IDs.

## Configuration

The system requires several Notion database IDs and API credentials to function. These should be set in the `.env` file:

### Required Notion Database IDs

- `NOTION_BUSINESS_ENTITIES_DB`: Business Entities Registry
- `NOTION_CONTACTS_PROFILES_DB`: Contacts & Profiles
- `NOTION_COMMUNITY_HUB_DB`: Community Hub
- `NOTION_PRODUCTS_SERVICES_DB`: Products & Services
- `NOTION_ACTIVE_WORKFLOW_INSTANCES_DB`: Active Workflow Instances
- `NOTION_MARKETING_CAMPAIGNS_DB`: Marketing Campaigns
- `NOTION_FEEDBACK_SURVEYS_DB`: Feedback & Surveys
- `NOTION_REWARDS_BOUNTIES_DB`: Rewards & Bounties
- `NOTION_MASTER_TASKS_DB`: Master Tasks
- `NOTION_AGENT_COMMUNICATION_DB`: Agent Communication Patterns
- `NOTION_AGENT_REGISTRY_DB`: Agent Registry
- `NOTION_API_INTEGRATIONS_DB`: API Integrations Catalog
- `NOTION_DATA_TRANSFORMATIONS_DB`: Data Transformations Registry
- `NOTION_NOTIFICATIONS_TEMPLATES_DB`: Notifications Templates
- `NOTION_USE_CASES_DB`: Use Cases Library
- `NOTION_WORKFLOWS_LIBRARY_DB`: Workflows Library

### API Credentials

- `NOTION_API_TOKEN`: Your Notion integration API token
- API keys for third-party services (TypeForm, HubSpot, Amelia, etc.)

## Running the System

Start the server with:

```bash
python main.py
```

The API server will start on port 8000 by default (configurable via `SERVER_PORT` environment variable).

## API Endpoints

- **Typeform Webhook:** `/webhooks/typeform`
- **Website Form Submission:** `/api/forms/submit`
- **Workflow Instance Details:** `/workflows/{instance_id}`
- **Health Check:** `/health`

## Architecture

The HigherSelf Network Server implements a hub-and-spoke architecture with Notion as the central hub. All agents operate independently but coordinate through a structured set of 16 interconnected Notion databases.

### Components

1. **Models (`/models`)**: Pydantic models defining data structures
2. **Services (`/services`)**: Service classes for external API interactions
3. **Agents (`/agents`)**: Agent implementations with specific responsibilities
4. **API (`/api`)**: FastAPI server for external communication

### Data Flow

1. External events trigger webhook calls to the API
2. Events are processed by appropriate agents
3. Agents create or update records in Notion via the NotionService
4. Workflow instances track the state of business processes
5. History logs maintain a complete audit trail

## Development

### Adding a New Agent

1. Create a new file in the `agents` directory
2. Extend the `BaseAgent` class
3. Implement the required abstract methods
4. Register the agent in `agents/__init__.py`
5. Add initialization in `main.py`

### Extending Integrations

To add support for a new integration:

1. Add the API platform to `ApiPlatform` enum in `models/base.py`
2. Create new Pydantic models for the integration's data structures
3. Implement a new agent or extend an existing one
4. Add webhook endpoints if needed

## Security Considerations

- API tokens are loaded from environment variables
- Webhook endpoints use a shared secret for authentication
- Access to Notion is controlled via the integration permissions
- All sensitive data is logged securely

## Deployment

The system is designed to run on The HigherSelf Network Server. Follow proper deployment practices:

1. Use a process manager (like systemd, PM2, or Supervisor)
2. Set up proper logging
3. Configure a reverse proxy (like Nginx)
4. Implement monitoring and alerting

## Support

For questions or support, contact The HigherSelf Network team.

## License

Proprietary - The HigherSelf Network
