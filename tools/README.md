# Windsurf Agent Network Utilities

This directory contains utility scripts for setting up and maintaining the Windsurf Agent Network for The HigherSelf Network.

## Available Utilities

### Notion Database Setup

The `notion_db_setup.py` script initializes all required Notion databases for the agent system, ensuring Notion serves as the central hub for all operations as required by The HigherSelf Network.

#### Features

- **Automatic Database Creation**: Creates all 10 standardized databases required by the system
- **Idempotent Operation**: Safely detects existing databases to prevent duplication
- **Environment Variable Generation**: Automatically generates database IDs for configuration
- **Validation & Verification**: Validates API connection and verifies database access
- **User-Friendly Output**: Provides clear, colored status messages during operation

#### Prerequisites

Before running this utility, ensure you have:

1. A Notion integration created at [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. An integration token with appropriate permissions
3. A parent page in your Notion workspace where databases will be created
4. The Notion integration added to the parent page (share the page with your integration)

#### Usage

1. Set up the required environment variables in your `.env` file:

   ```bash
   NOTION_API_TOKEN=secret_your_token_here
   NOTION_PARENT_PAGE_ID=your_parent_page_id_here
   ```

2. Run the database setup utility:

   ```bash
   python -m tools.notion_db_setup
   ```

3. The utility will:

   - Validate your API token and parent page ID
   - Create all required databases
   - Verify database access
   - Generate a `.env.notion` file with all database IDs

4. Add the generated variables to your main `.env` file:

   ```bash
   cat .env.notion >> .env
   ```

#### Troubleshooting

### Permission Issues

- Ensure your Notion integration has been shared with the parent page
- Verify the integration has "Insert content" and "Update content" capabilities

### Invalid Parent Page ID

- The parent page ID should be the UUID portion of the Notion page URL
- Make sure the page exists and is accessible to your integration

### Rate Limit Errors

- If you encounter rate limit errors, wait a few minutes before retrying

## Additional Utilities

Future utilities will be added to this directory to support various aspects of the Windsurf Agent Network, such as:

- Database verification and health checks
- Data migration tools
- Workflow validation utilities
- Agent communication testing tools

All utilities will maintain the core principles of keeping Notion as the central data hub and utilizing Pydantic models for data validation.
