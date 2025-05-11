# Database Synchronization Guide

This guide explains how to set up and use the database synchronization system for The HigherSelf Network Server, which aligns and syncs the 16 Notion databases with Supabase.

## Overview

The HigherSelf Network Server uses two database systems:

1. **Notion Databases**: The primary user-facing databases where most data entry and management happens
2. **Supabase**: A PostgreSQL database that provides more powerful querying, analytics, and integration capabilities

The synchronization system ensures that data is kept consistent between these two systems, allowing you to leverage the strengths of both platforms.

## Database Structure

The system includes 16 interconnected databases:

### Core Operational Databases

1. **Business Entities Registry** - Central registry of all business entities
2. **Contacts & Profiles** - Customer and contact information
3. **Community Hub** - Community member data
4. **Products & Services** - Product and service catalog
5. **Workflow Instances** - Active workflow instances
6. **Marketing Campaigns** - Marketing campaign data
7. **Feedback & Surveys** - Customer feedback and survey responses
8. **Rewards & Bounties** - Reward and bounty programs
9. **Master Tasks Database** - Centralized task management

### Agent & System Support Databases

10. **Agent Communication Patterns** - Communication patterns between agents
11. **Agent Registry** - Registry of all agents in the system
12. **API Integrations Catalog** - Catalog of API integrations
13. **Data Transformations Registry** - Registry of data transformation rules
14. **Notifications Templates** - Templates for notifications
15. **Use Cases Library** - Library of use cases
16. **Workflows Library** - Library of workflow definitions

## Setup Instructions

### 1. Configure Environment Variables

Add the following environment variables to your `.env` file:

```
# Supabase Configuration
SUPABASE_URL=https://mmmtfmulvmvtxybwxxrr.supabase.co
SUPABASE_API_KEY=your_supabase_api_key
SUPABASE_PROJECT_ID=mmmtfmulvmvtxybwxxrr
```

You can obtain your Supabase API key from the Supabase dashboard under Project Settings > API.

### 2. Create Supabase Tables

Run the database setup script to create the necessary tables in Supabase:

```bash
python -m tools.supabase_db_setup
```

This script will:
- Create all 16 tables in Supabase
- Set up the appropriate relationships between tables
- Create indexes for better performance
- Verify that all tables were created successfully

### 3. Initial Synchronization

Perform an initial synchronization to populate Supabase with data from Notion:

```bash
python -m tools.sync_databases --direction notion_to_supabase
```

This will copy all data from Notion to Supabase, establishing the initial state.

## Usage

### Manual Synchronization

You can manually trigger synchronization using the `sync_databases.py` tool:

```bash
# Sync in both directions (default)
python -m tools.sync_databases

# Sync from Notion to Supabase only
python -m tools.sync_databases --direction notion_to_supabase

# Sync from Supabase to Notion only
python -m tools.sync_databases --direction supabase_to_notion

# Sync only a specific model
python -m tools.sync_databases --model BusinessEntity

# Sync only records updated since a specific time
python -m tools.sync_databases --since 2023-07-15T00:00:00
```

### Automated Synchronization

For production environments, it's recommended to set up automated synchronization using a scheduled task or cron job:

```bash
# Example cron job (runs every hour)
0 * * * * cd /path/to/project && python -m tools.sync_databases >> /var/log/sync.log 2>&1
```

## How It Works

The synchronization system works as follows:

1. **Bidirectional Sync**: Changes can be made in either Notion or Supabase and will be synchronized to the other system.

2. **ID Tracking**: Each record maintains references to its counterpart in the other system:
   - Notion records have a `supabase_id` field
   - Supabase records have a `notion_page_id` field

3. **Conflict Resolution**: When conflicts occur (changes to the same record in both systems), the system uses the following rules:
   - The record with the most recent `updated_at` timestamp wins
   - If timestamps are identical, Notion takes precedence as the primary user interface

4. **Error Handling**: Synchronization errors are logged and can be reviewed. Failed synchronizations will be retried in the next sync cycle.

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Ensure all required environment variables are set in your `.env` file

2. **Permission Issues**
   - Verify that your Supabase API key has the necessary permissions
   - Check that your Notion integration has access to all required databases

3. **Sync Failures**
   - Check the logs for specific error messages
   - Verify network connectivity to both Notion and Supabase APIs

### Resetting Synchronization

If you need to reset the synchronization state:

```bash
# Clear Supabase tables and resync from Notion
python -m tools.supabase_db_setup --reset
python -m tools.sync_databases --direction notion_to_supabase
```

## Advanced Usage

### Custom Field Mappings

The synchronization system supports custom field mappings between Notion properties and Supabase columns. These mappings are defined in the `services/database_sync_service.py` file.

### Data Transformations

You can define custom data transformations to be applied during synchronization. This is useful for:
- Converting data formats
- Enriching data with additional information
- Filtering sensitive information

### Partial Synchronization

For large databases, you can perform partial synchronization by:
- Syncing only specific models
- Using time-based filters
- Implementing custom filters based on your business logic

## Security Considerations

1. **API Keys**: Store API keys securely and never commit them to version control
2. **Data Privacy**: Be mindful of data privacy regulations when synchronizing personal data
3. **Access Control**: Implement appropriate access controls in both Notion and Supabase

## Support

If you encounter issues with the database synchronization system, please:
1. Check the logs for specific error messages
2. Review this documentation for troubleshooting steps
3. Contact the development team for assistance
