# The HigherSelf Network Server - Project Structure

This document outlines the complete structure of The HigherSelf Network Server codebase, highlighting key files and directories and their purposes.

## Root Directory

- `main.py` - Main entry point for the application
- `README.md` - Project documentation and overview
- `requirements.txt` - Python dependencies
- `.env.example` - Example environment configuration file
- `STRUCTURE.md` - This file, documenting the project structure

## Key Directories and Files

### `/agents` - Agent Implementations

- `base_agent.py` - Base agent class with common functionality
- `lead_capture_agent.py` - Processes leads from various sources
- `booking_agent.py` - Handles bookings from Amelia and orders from WooCommerce
- `task_management_agent.py` - Creates and manages tasks
- `marketing_campaign_agent.py` - Manages email campaigns via Beehiiv
- `community_engagement_agent.py` - Handles Circle.so community interaction
- `content_lifecycle_agent.py` - Manages content creation and distribution
- `audience_segmentation_agent.py` - Creates and manages audience segments
- `__init__.py` - Registers all agents

### `/api` - API Endpoints and Webhook Handlers

- `server.py` - FastAPI server configuration
- `webhooks.py` - General webhook handlers
- `webhooks_circleso.py` - Circle.so webhook handlers
- `webhooks_beehiiv.py` - Beehiiv webhook handlers
- `__init__.py` - API module initialization

### `/config` - Configuration Files

- `notion_databases.py` - 16-database Notion structure configuration
- `testing_mode.py` - Testing mode configuration for development

### `/docs` - Documentation Files

- `AGENT_DEVELOPMENT.md` - Guide for developing new agents
- `AUTOMATION_FLOWS.md` - Detailed documentation of automation flows
- `WORKFLOWS.md` - Documentation of workflow definitions

### `/models` - Data Models

- `base.py` - Base models and enums
- `notion_db_models.py` - Original Notion database models
- `notion_db_models_extended.py` - Extended models for the 16-database structure
- `content_models.py` - Models for content management
- `audience_models.py` - Models for audience segmentation
- `task_models.py` - Models for task management
- `__init__.py` - Registers all models

### `/services` - Service Integrations

- `notion_service.py` - Notion API integration
- `integration_manager.py` - Manager for all external integrations

### `/tools` - Utility Scripts

- `validate_notion_structure.py` - Validates the 16-database Notion structure
- `test_automation_flows.py` - Tests automation flows with mock data
- `toggle_testing_mode.py` - Enables/disables testing mode for development

### `/utils` - Shared Utilities

- `api_decorators.py` - Decorators for API error handling and testing mode
- `logging_utils.py` - Utilities for consistent logging

### `/visualizations` - Visual Representations

- `architecture.html` - HTML visualization of the system architecture

### `/logs` - Log Files

- `windsurf_agents.log` - Application log file

### `/data` - Persistent Data Storage

- Used for local data storage when needed

## Notion Database Structure

The system uses a 16-database structure in Notion as the central hub:

### Core Operational Databases

1. Business Entities Registry DB
2. Contacts & Profiles DB
3. Community Hub DB
4. Products & Services DB
5. Active Workflow Instances DB
6. Marketing Campaigns DB
7. Feedback & Surveys DB
8. Rewards & Bounties DB
9. Master Tasks Database

### Agent & System Support Databases

1. Agent Communication Patterns DB
2. Agent Registry DB
3. API Integrations Catalog DB
4. Data Transformations Registry DB
5. Notifications Templates DB
6. Use Cases Library DB
7. Workflows Library DB

## Automation Flows

The system implements 8 key automation flows:

1. Lead Capture & Initial Processing
2. Retreat Booking Management
3. Art Sale & Fulfillment
4. Marketing Email Campaign
5. Automated Task Management
6. Community Engagement
7. Content Creation & Distribution 
8. Audience Analysis & Segmentation

Each flow is implemented using a combination of agents, webhook handlers, and Notion database operations, with all data centralized in Notion.
