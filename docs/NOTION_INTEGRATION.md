# Notion Integration Guide

This document provides details on how The HigherSelf Network Server integrates with Notion as the central hub for data management, workflow tracking, and automation for The HigherSelf Network.

## Notion Database Structure

The system uses 16 structured Notion databases that form the backbone of the operational data:

1. **Business Entities Registry** - Tracks all business entities (The Connection Practice, The 7 Space)
2. **Agent Registry** - Catalogs all agents in the network with their capabilities
3. **Workflows Library** - Documents all workflow definitions
4. **Active Workflow Instances** - Tracks currently running workflow instances
5. **API Integrations Catalog** - Documents external API integrations
6. **Data Transformations Registry** - Documents data transformation patterns
7. **Use Cases Library** - Documents business use cases
8. **Notifications Templates** - Manages reusable notification templates
9. **Agent Communication Patterns** - Documents agent-to-agent communication
10. **Master Tasks Database** - Centralizes actionable tasks
11. **Contacts & Profiles DB** - Unified customer/contact database (this seems to be missing from the original list of 10 but is a core DB)
12. **Community Hub DB** - Community member profiles and engagement tracking (this seems to be missing from the original list of 10 but is a core DB)
13. **Products & Services DB** - Catalog of all available products and services (this seems to be missing from the original list of 10 but is a core DB)
14. **Marketing Campaigns DB** - Marketing initiatives and performance tracking (this seems to be missing from the original list of 10 but is a core DB)
15. **Feedback & Surveys DB** - Customer feedback and survey responses (this seems to be missing from the original list of 10 but is a core DB)
16. **Rewards & Bounties DB** - Incentive programs and achievements (this seems to be missing from the original list of 10 but is a core DB)

## Database Setup

The `tools/notion_db_setup.py` utility script can be used to create all required databases in Notion.

To use it:

1. Set your Notion API token in the `.env` file
2. Add a `NOTION_PARENT_PAGE_ID` environment variable with the ID of the parent page where databases will be created
3. Run the script:

```bash
python -m tools.notion_db_setup
```

This will create all the databases with the correct structure and write the database IDs to a `.env.notion` file.

## Pydantic Model Mapping

The system rigorously follows the Pydantic AI framework, with model definitions that precisely map to the Notion database structures. This ensures data validation, type safety, and consistent representation.

Key models:

- `BusinessEntity` - Maps to the Business Entities Registry database
- `Agent` - Maps to the Agent Registry database
- `Workflow` - Maps to the Workflows Library database
- `WorkflowInstance` - Maps to the Active Workflow Instances database

## Notion API Integration

The system interacts with Notion through the `NotionService` class, which provides methods to:

- Create, update, and query database records
- Map between Pydantic models and Notion properties
- Log workflow state transitions and actions
- Create tasks from workflow instances

All operations follow Notion's best practices and handle API rate limiting appropriately.

## Workflow History Logging

Each workflow instance maintains a comprehensive history log in Notion, tracking:

- State transitions
- Agent actions
- Timestamps
- Relevant data at each step

This creates a complete audit trail and enables operational visibility.

## Setting Up Relations

When setting up the Notion databases, you need to configure the relation properties correctly:

1. For the "Primary Workflows" relation in Business Entities, select the Workflows Library database
2. For the "Active Agents" relation in Business Entities, select the Agent Registry database
3. Follow similar patterns for all other relation properties

The database setup tool handles this automatically.

## Security Considerations

- No sensitive credentials are stored directly in Notion
- The `API Keys Reference` field only contains references to secure storage locations
- All Notion API tokens are stored in environment variables
- Access to the Notion workspace should be carefully managed
