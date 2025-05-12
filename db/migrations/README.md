# <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/graph-24.svg" alt="Graph" width="24" height="24" /> Database Migration Scripts <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/globe-24.svg" alt="Globe" width="24" height="24" />

This directory contains SQL migration scripts for setting up and maintaining the Supabase database schema for The HigherSelf Network Server.

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/checklist-24.svg" alt="Checklist" width="20" height="20" /> Overview

These migration scripts create the necessary tables, indexes, and relationships in Supabase to align with the 16 Notion databases used in The HigherSelf Network system.

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/file-directory-24.svg" alt="Directory" width="20" height="20" /> Migration Files

- **01_create_core_tables.sql**: Creates the 9 core operational database tables
- **02_create_agent_support_tables.sql**: Creates the 7 agent and system support database tables

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/rocket-24.svg" alt="Rocket" width="20" height="20" /> Running Migrations

The migrations can be run using the `supabase_db_setup.py` tool:

```bash
python -m tools.supabase_db_setup
```

This tool will:
1. Connect to your Supabase project
2. Execute each migration script in order
3. Verify that all tables were created successfully

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/tools-24.svg" alt="Tools" width="20" height="20" /> Table Structure

The migration scripts create 16 tables that correspond to the 16 Notion databases:

### <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/organization-24.svg" alt="Organization" width="18" height="18" /> Core Operational Tables

1. `business_entities` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/organization-24.svg" alt="Organization" width="16" height="16" /> Business Entities Registry
2. `contacts_profiles` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/people-24.svg" alt="People" width="16" height="16" /> Contacts & Profiles
3. `community_members` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/globe-24.svg" alt="Globe" width="16" height="16" /> Community Hub
4. `products_services` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/package-24.svg" alt="Package" width="16" height="16" /> Products & Services
5. `workflow_instances` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/gear-24.svg" alt="Gear" width="16" height="16" /> Workflow Instances
6. `marketing_campaigns` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/megaphone-24.svg" alt="Megaphone" width="16" height="16" /> Marketing Campaigns
7. `feedback_surveys` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/graph-24.svg" alt="Graph" width="16" height="16" /> Feedback & Surveys
8. `rewards_bounties` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/trophy-24.svg" alt="Trophy" width="16" height="16" /> Rewards & Bounties
9. `tasks` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/check-24.svg" alt="Check" width="16" height="16" /> Master Tasks Database

### <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/robot-24.svg" alt="Robot" width="18" height="18" /> Agent & System Support Tables

10. `agent_communication_patterns` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/sync-24.svg" alt="Sync" width="16" height="16" /> Agent Communication Patterns
11. `agents` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/robot-24.svg" alt="Robot" width="16" height="16" /> Agent Registry
12. `api_integrations` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/plug-24.svg" alt="Plug" width="16" height="16" /> API Integrations Catalog
13. `data_transformations` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/sync-24.svg" alt="Sync" width="16" height="16" /> Data Transformations Registry
14. `notification_templates` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/mail-24.svg" alt="Mail" width="16" height="16" /> Notifications Templates
15. `use_cases` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/checklist-24.svg" alt="Checklist" width="16" height="16" /> Use Cases Library
16. `workflows` - <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/pencil-24.svg" alt="Pencil" width="16" height="16" /> Workflows Library

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/checklist-24.svg" alt="Checklist" width="20" height="20" /> Common Table Structure

Each table includes:

- <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/key-24.svg" alt="Key" width="16" height="16" /> Primary key (`id` as UUID)
- <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/link-24.svg" alt="Link" width="16" height="16" /> Notion page ID reference (`notion_page_id`)
- <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/clock-24.svg" alt="Clock" width="16" height="16" /> Creation and update timestamps (`created_at`, `updated_at`)
- <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/pencil-24.svg" alt="Pencil" width="16" height="16" /> Table-specific fields that match the Notion database properties

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/plus-24.svg" alt="Plus" width="20" height="20" /> Adding New Migrations

When adding new migrations:

1. Create a new SQL file with a sequential number prefix (e.g., `03_add_new_fields.sql`)
2. Include clear comments explaining the purpose of the migration
3. Test the migration on a development database before running in production

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/reply-24.svg" alt="Reply" width="20" height="20" /> Rollback

These migrations do not include automatic rollback functionality. If you need to roll back changes:

1. Create a new migration script with the rollback operations
2. Execute it using the same tool

For a complete reset, you can use the Supabase dashboard to drop all tables and rerun the migrations.

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/sync-24.svg" alt="Sync" width="20" height="20" /> Relationship with Notion Databases

These tables are designed to mirror the structure of the Notion databases while optimizing for SQL database performance. The synchronization between Notion and Supabase is handled by the `database_sync_service.py` service.
