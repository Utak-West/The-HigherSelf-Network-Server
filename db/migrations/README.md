# Database Migration Scripts

This directory contains SQL migration scripts for setting up and maintaining the Supabase database schema for The HigherSelf Network Server.

## Overview

These migration scripts create the necessary tables, indexes, and relationships in Supabase to align with the 16 Notion databases used in The HigherSelf Network system.

## Migration Files

- **01_create_core_tables.sql**: Creates the 9 core operational database tables
- **02_create_agent_support_tables.sql**: Creates the 7 agent and system support database tables

## Running Migrations

The migrations can be run using the `supabase_db_setup.py` tool:

```bash
python -m tools.supabase_db_setup
```

This tool will:
1. Connect to your Supabase project
2. Execute each migration script in order
3. Verify that all tables were created successfully

## Table Structure

The migration scripts create 16 tables that correspond to the 16 Notion databases:

### Core Operational Tables

1. `business_entities` - Business Entities Registry
2. `contacts_profiles` - Contacts & Profiles
3. `community_members` - Community Hub
4. `products_services` - Products & Services
5. `workflow_instances` - Workflow Instances
6. `marketing_campaigns` - Marketing Campaigns
7. `feedback_surveys` - Feedback & Surveys
8. `rewards_bounties` - Rewards & Bounties
9. `tasks` - Master Tasks Database

### Agent & System Support Tables

10. `agent_communication_patterns` - Agent Communication Patterns
11. `agents` - Agent Registry
12. `api_integrations` - API Integrations Catalog
13. `data_transformations` - Data Transformations Registry
14. `notification_templates` - Notifications Templates
15. `use_cases` - Use Cases Library
16. `workflows` - Workflows Library

## Common Table Structure

Each table includes:

- Primary key (`id` as UUID)
- Notion page ID reference (`notion_page_id`)
- Creation and update timestamps (`created_at`, `updated_at`)
- Table-specific fields that match the Notion database properties

## Adding New Migrations

When adding new migrations:

1. Create a new SQL file with a sequential number prefix (e.g., `03_add_new_fields.sql`)
2. Include clear comments explaining the purpose of the migration
3. Test the migration on a development database before running in production

## Rollback

These migrations do not include automatic rollback functionality. If you need to roll back changes:

1. Create a new migration script with the rollback operations
2. Execute it using the same tool

For a complete reset, you can use the Supabase dashboard to drop all tables and rerun the migrations.

## Relationship with Notion Databases

These tables are designed to mirror the structure of the Notion databases while optimizing for SQL database performance. The synchronization between Notion and Supabase is handled by the `database_sync_service.py` service.
