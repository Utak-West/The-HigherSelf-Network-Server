# BetterMode Integration Guide

This guide provides comprehensive documentation for integrating BetterMode with The HigherSelf Network Server.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Configuration](#configuration)
4. [API Integration](#api-integration)
5. [Webhooks](#webhooks)
6. [Data Models](#data-models)
7. [Migration from Circle.so](#migration-from-circleso)
8. [Redis Integration](#redis-integration)
9. [MongoDB Integration](#mongodb-integration)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)

## Overview

BetterMode is a community platform designed for businesses and organizations. It offers extensive customization options, robust API, and advanced features for community engagement. This integration replaces Circle.so as the primary community platform for The HigherSelf Network Server.

Key features of the BetterMode integration:

- Member management
- Activity tracking
- Event scheduling
- Direct messaging
- Content publishing
- Webhook processing
- Data synchronization with Notion

## Prerequisites

Before setting up the BetterMode integration, you need:

1. A BetterMode account with admin access
2. BetterMode API token
3. BetterMode network ID
4. BetterMode webhook secret (optional, but recommended for security)

## Configuration

### Environment Variables

Add the following environment variables to your `.env` file:

```
# BetterMode Community Platform
BETTERMODE_API_TOKEN=your_bettermode_api_token
BETTERMODE_NETWORK_ID=your_bettermode_network_id
BETTERMODE_WEBHOOK_SECRET=your_bettermode_webhook_secret
BETTERMODE_API_URL=https://app.bettermode.com/api/graphql
```

You can use the provided `.env.bettermode.example` file as a template.

### Integration Manager Configuration

The BetterMode integration is enabled by default in the Integration Manager. You can control this with the following environment variable:

```
INTEGRATION_ENABLE_BETTERMODE=true
```

To disable the legacy Circle.so integration:

```
INTEGRATION_ENABLE_CIRCLE=false
```

## API Integration

The BetterMode integration uses GraphQL API for all interactions. The `BetterModeService` class in `services/bettermode_service.py` provides methods for interacting with the BetterMode API.

### Key API Methods

- `get_member(member_id)`: Get a member by ID
- `get_member_by_email(email)`: Get a member by email
- `send_direct_message(recipient_id, message)`: Send a direct message to a member
- `create_post(space_id, content, title, author_id)`: Create a post in a space

### Example: Getting a Member

```python
from services.bettermode_service import get_bettermode_service

async def get_member_info(member_id):
    bettermode_service = await get_bettermode_service()
    member = await bettermode_service.get_member(member_id)
    return member
```

## Webhooks

BetterMode webhooks are processed by the `api/webhooks_bettermode.py` module. The following webhook endpoints are available:

- `/webhooks/bettermode/member`: Handles member events (creation, updates)
- `/webhooks/bettermode/activity`: Handles activity events (posts, comments, reactions)
- `/webhooks/bettermode/event`: Handles event creation and updates

### Webhook Security

Webhooks are secured using signature verification. BetterMode sends a signature in the `X-BetterMode-Signature` header, which is verified using the webhook secret.

### Setting Up Webhooks in BetterMode

1. Go to your BetterMode admin dashboard
2. Navigate to Settings > Integrations > Webhooks
3. Add a new webhook with the following URL: `https://your-server.com/webhooks/bettermode/member`
4. Select the events you want to receive (e.g., `member.created`, `member.updated`)
5. Generate a webhook secret and save it in your environment variables
6. Repeat for activity and event webhooks

## Data Models

The BetterMode integration uses Pydantic models defined in `models/bettermode_models.py`:

- `BetterModeIntegrationConfig`: Configuration for BetterMode integration
- `BetterModeMember`: Represents a member in BetterMode
- `BetterModeSpace`: Represents a space in BetterMode
- `BetterModePost`: Represents a post in BetterMode
- `BetterModeComment`: Represents a comment in BetterMode
- `BetterModeReaction`: Represents a reaction in BetterMode
- `BetterModeEvent`: Represents an event in BetterMode
- `BetterModeWebhookPayload`: Represents a webhook payload from BetterMode

### Database Schema

The database schema has been updated to include BetterMode-specific fields:

```sql
CREATE TABLE IF NOT EXISTS community_members (
    -- Existing fields
    bettermode_member_id TEXT,
    circle_member_id TEXT,
    primary_platform TEXT DEFAULT 'BetterMode',
    -- Other fields
);
```

## Migration from Circle.so

A migration script is provided to help migrate data from Circle.so to BetterMode. The script is located at `scripts/migrate_circleso_to_bettermode.py`.

### Running the Migration Script

```bash
python scripts/migrate_circleso_to_bettermode.py --batch-size 100 --max-members 1000
```

### Migration Options

- `--batch-size`: Number of members to process per batch (default: 100)
- `--max-members`: Maximum number of members to migrate (default: all)
- `--circle-token`: Circle.so API token (can also be set via environment variable)
- `--circle-community-id`: Circle.so community ID (can also be set via environment variable)
- `--bettermode-token`: BetterMode API token (can also be set via environment variable)
- `--bettermode-network-id`: BetterMode network ID (can also be set via environment variable)
- `--notion-token`: Notion API token (can also be set via environment variable)

## Redis Integration

The BetterMode integration works with Redis for caching and rate limiting:

### Caching

Member data is cached in Redis to reduce API calls to BetterMode:

```
bettermode:member:{member_id} -> Member data (JSON)
```

### Rate Limiting

API calls to BetterMode are rate-limited using Redis:

```
bettermode:ratelimit:{endpoint} -> Rate limit counter
```

## MongoDB Integration

The BetterMode integration works with MongoDB for storing webhook events and activity data:

### Webhook Events

Webhook events are stored in MongoDB for audit and debugging:

```
bettermode_webhook_events:
  - event_type: "member.created"
  - timestamp: ISODate("2023-01-01T00:00:00Z")
  - data: { ... }
```

### Activity Data

Member activity data is stored in MongoDB for analytics:

```
bettermode_member_activities:
  - member_id: "123"
  - activity_type: "post"
  - timestamp: ISODate("2023-01-01T00:00:00Z")
  - data: { ... }
```

## Testing

### Unit Tests

Unit tests for the BetterMode integration are located in `tests/services/test_bettermode_service.py` and `tests/api/test_webhooks_bettermode.py`.

### Manual Testing

You can manually test the BetterMode integration using the following steps:

1. Start the server: `python main.py`
2. Use the health check endpoint to verify the BetterMode service is running: `GET /health`
3. Test webhook endpoints using a tool like Postman or curl

### Testing in Development Mode

You can enable testing mode to simulate BetterMode API calls without making actual API requests:

```
TESTING_MODE=true
DISABLE_API_BETTERMODE=true
```

## Troubleshooting

### Common Issues

1. **Webhook Signature Verification Failed**
   - Check that the webhook secret is correctly set in both BetterMode and your environment variables
   - Verify that the webhook URL is correct

2. **API Authentication Failed**
   - Check that the API token is correctly set in your environment variables
   - Verify that the API token has the necessary permissions

3. **Member Not Found**
   - Check that the member exists in BetterMode
   - Verify that the member ID or email is correct

### Logging

The BetterMode integration uses the `loguru` logger for logging. You can adjust the log level in your environment variables:

```
LOG_LEVEL=DEBUG
```

### Support

For additional support, contact the BetterMode support team or refer to the [BetterMode API documentation](https://developers.bettermode.com/).
