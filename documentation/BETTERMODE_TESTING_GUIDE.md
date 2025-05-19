# BetterMode Integration Testing Guide

This guide provides instructions for testing the BetterMode integration with The HigherSelf Network Server.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setup](#setup)
3. [Testing the API Integration](#testing-the-api-integration)
4. [Testing Webhooks](#testing-webhooks)
5. [Testing Member Management](#testing-member-management)
6. [Testing Activity Tracking](#testing-activity-tracking)
7. [Testing Event Scheduling](#testing-event-scheduling)
8. [Testing Migration](#testing-migration)
9. [Automated Tests](#automated-tests)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

Before testing the BetterMode integration, you need:

1. A BetterMode account with admin access
2. BetterMode API token
3. BetterMode network ID
4. BetterMode webhook secret
5. The HigherSelf Network Server running locally or in a test environment

## Setup

### Environment Configuration

1. Create a `.env.test` file with the following variables:

```
# BetterMode Community Platform
BETTERMODE_API_TOKEN=your_bettermode_api_token
BETTERMODE_NETWORK_ID=your_bettermode_network_id
BETTERMODE_WEBHOOK_SECRET=your_bettermode_webhook_secret
BETTERMODE_API_URL=https://app.bettermode.com/api/graphql

# Integration Manager Configuration
INTEGRATION_ENABLE_BETTERMODE=true
INTEGRATION_ENABLE_CIRCLE=false

# Testing Configuration
TESTING_MODE=false
```

2. Start the server with the test environment:

```bash
python main.py --env .env.test
```

### Testing Mode

For testing without making actual API calls to BetterMode, you can enable testing mode:

```
TESTING_MODE=true
DISABLE_API_BETTERMODE=true
```

This will simulate API responses and allow you to test the integration without affecting your BetterMode community.

## Testing the API Integration

### Health Check

1. Verify that the BetterMode service is running:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "services": {
    "bettermode": {
      "status": "available",
      "initialized": true
    },
    ...
  }
}
```

### Testing the BetterMode Service

You can test the BetterMode service directly using the Python REPL:

```python
import asyncio
from services.bettermode_service import get_bettermode_service

async def test_bettermode():
    bettermode_service = await get_bettermode_service()
    is_valid = await bettermode_service.validate_connection()
    print(f"Connection valid: {is_valid}")

asyncio.run(test_bettermode())
```

## Testing Webhooks

### Setting Up Webhook Testing

1. Use a tool like [ngrok](https://ngrok.com/) to expose your local server to the internet:

```bash
ngrok http 8000
```

2. Configure webhooks in BetterMode to point to your ngrok URL:

```
https://<your-ngrok-url>/webhooks/bettermode/member
https://<your-ngrok-url>/webhooks/bettermode/activity
https://<your-ngrok-url>/webhooks/bettermode/event
```

### Testing Member Webhooks

1. Create a new member in BetterMode
2. Check the server logs for webhook processing:

```
INFO: Received BetterMode new member webhook for: test@example.com
```

3. Verify that the member is added to the Notion database

### Testing Activity Webhooks

1. Create a new post in BetterMode
2. Check the server logs for webhook processing:

```
INFO: Received BetterMode activity webhook for: test@example.com
```

3. Verify that the activity is tracked in the Notion database

### Testing Event Webhooks

1. Create a new event in BetterMode
2. Check the server logs for webhook processing:

```
INFO: Received BetterMode event webhook: Test Event
```

3. Verify that the event is scheduled in the Notion database

## Testing Member Management

### Getting a Member

Test retrieving a member from BetterMode:

```python
import asyncio
from services.bettermode_service import get_bettermode_service

async def test_get_member():
    bettermode_service = await get_bettermode_service()
    member = await bettermode_service.get_member("member_id")
    print(f"Member: {member}")

asyncio.run(test_get_member())
```

### Getting a Member by Email

Test retrieving a member by email:

```python
import asyncio
from services.bettermode_service import get_bettermode_service

async def test_get_member_by_email():
    bettermode_service = await get_bettermode_service()
    member = await bettermode_service.get_member_by_email("test@example.com")
    print(f"Member: {member}")

asyncio.run(test_get_member_by_email())
```

### Sending a Direct Message

Test sending a direct message to a member:

```python
import asyncio
from services.bettermode_service import get_bettermode_service

async def test_send_direct_message():
    bettermode_service = await get_bettermode_service()
    success = await bettermode_service.send_direct_message(
        "member_id",
        "Hello from The HigherSelf Network Server!"
    )
    print(f"Message sent: {success}")

asyncio.run(test_send_direct_message())
```

## Testing Activity Tracking

### Creating a Post

Test creating a post in a space:

```python
import asyncio
from services.bettermode_service import get_bettermode_service

async def test_create_post():
    bettermode_service = await get_bettermode_service()
    post_id = await bettermode_service.create_post(
        "space_id",
        "This is a test post from The HigherSelf Network Server.",
        "Test Post",
        "author_id"
    )
    print(f"Post created with ID: {post_id}")

asyncio.run(test_create_post())
```

## Testing Event Scheduling

Test the event scheduling functionality by creating an event in BetterMode and verifying that it's processed correctly by the Community Engagement Agent.

## Testing Migration

### Testing the Migration Script

1. Run the migration script with a small batch size:

```bash
python scripts/migrate_circleso_to_bettermode.py --batch-size 10 --max-members 10
```

2. Verify that members are migrated correctly:
   - Check the BetterMode admin dashboard
   - Check the Notion database
   - Check the server logs

### Testing with Real Data

For testing with real data, make sure to use a test environment and not your production BetterMode community.

## Automated Tests

### Running Unit Tests

Run the unit tests for the BetterMode integration:

```bash
pytest tests/services/test_bettermode_service.py
pytest tests/api/test_webhooks_bettermode.py
```

### Writing New Tests

When adding new features to the BetterMode integration, make sure to add corresponding tests.

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

### Debugging

For detailed debugging, enable debug logging:

```
LOG_LEVEL=DEBUG
```

This will provide more detailed logs about the BetterMode integration.

### Testing in Isolation

You can test the BetterMode service in isolation by creating a simple script:

```python
import asyncio
import os
from services.bettermode_service import BetterModeService
from models.bettermode_models import BetterModeIntegrationConfig

async def test_bettermode_isolated():
    config = BetterModeIntegrationConfig(
        api_token=os.environ.get("BETTERMODE_API_TOKEN"),
        network_id=os.environ.get("BETTERMODE_NETWORK_ID")
    )
    service = BetterModeService(config)
    
    # Test connection
    is_valid = await service.validate_connection()
    print(f"Connection valid: {is_valid}")
    
    # Add more tests as needed

asyncio.run(test_bettermode_isolated())
```

Save this as `test_bettermode_isolated.py` and run it:

```bash
python test_bettermode_isolated.py
```

This allows you to test the BetterMode service without the rest of the server.
