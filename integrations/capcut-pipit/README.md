# CapCut and Pipit Integration

This integration connects CapCut (video editing platform) and Pipit (payment processing service) with The HigherSelf Network Server, enabling seamless video export and payment processing for premium video features.

## Features

- Export videos from CapCut directly to The HigherSelf Network platform
- Process payments through Pipit for premium video features
- Store video metadata and transaction information in Notion
- Track the status of video exports and payments
- Handle webhooks from both CapCut and Pipit

## Architecture

The integration follows the central hub architecture of The HigherSelf Network Server, with Notion serving as the central data store. All interactions with CapCut and Pipit are managed through dedicated service classes, and all data is synchronized with Notion.

## Components

- **CapCut Service**: Handles communication with the CapCut API for video export
- **Pipit Service**: Handles communication with the Pipit API for payment processing
- **API Router**: Provides endpoints for interacting with CapCut and Pipit
- **Notion Integration**: Stores video and transaction data in Notion databases

## Setup

1. Configure environment variables in `.env`:

```
# CapCut API Configuration
CAPCUT_API_KEY=your_capcut_api_key
CAPCUT_API_SECRET=your_capcut_api_secret
CAPCUT_BASE_URL=https://api.capcut.com/v1
CAPCUT_WEBHOOK_SECRET=your_capcut_webhook_secret

# Pipit API Configuration
PIPIT_API_KEY=your_pipit_api_key
PIPIT_API_SECRET=your_pipit_api_secret
PIPIT_BASE_URL=https://api.pipit.com/v1
PIPIT_WEBHOOK_SECRET=your_pipit_webhook_secret

# Notion Database IDs
NOTION_VIDEO_CONTENT_DB=your_notion_video_content_database_id
NOTION_VIDEO_TRANSACTIONS_DB=your_notion_video_transactions_database_id

# Integration Manager Configuration
ENABLE_CAPCUT=true
ENABLE_PIPIT=true
```

2. Create the required Notion databases:

- **Video Content Database**: Stores information about videos exported from CapCut
- **Video Transactions Database**: Stores information about payments processed through Pipit

3. Configure webhooks in CapCut and Pipit to point to your server's webhook endpoints:

- CapCut webhook: `https://your-server.com/api/capcut-pipit/capcut/webhook`
- Pipit webhook: `https://your-server.com/api/capcut-pipit/pipit/webhook`

## Usage

### Export a Video from CapCut

```python
import requests

response = requests.post(
    "https://your-server.com/api/capcut-pipit/capcut/export",
    headers={"x-api-key": "your_api_key"},
    json={
        "project_id": "cc-proj-123456789",
        "format": "mp4",
        "quality": "full_hd",
        "callback_url": "https://your-server.com/api/capcut-pipit/capcut/webhook",
        "business_entity_id": "the_connection_practice",
        "include_metadata": True,
        "watermark": False
    }
)

print(response.json())
```

### Process a Payment with Pipit

```python
import requests

response = requests.post(
    "https://your-server.com/api/capcut-pipit/pipit/payments",
    headers={"x-api-key": "your_api_key"},
    json={
        "amount": 29.99,
        "currency": "usd",
        "description": "Premium video features",
        "customer": {
            "email": "customer@example.com",
            "name": "John Doe"
        },
        "items": [
            {
                "id": "feat-001",
                "name": "4K Export",
                "description": "Export video in 4K resolution",
                "unit_price": 29.99,
                "feature_type": "export_4k"
            }
        ],
        "success_url": "https://your-server.com/payment/success",
        "cancel_url": "https://your-server.com/payment/cancel",
        "business_entity_id": "the_connection_practice"
    }
)

print(response.json())
```

### Create a Video Transaction

```python
import requests

response = requests.post(
    "https://your-server.com/api/capcut-pipit/transactions",
    headers={"x-api-key": "your_api_key"},
    json={
        "video_id": "vid-987654321",
        "customer_email": "customer@example.com",
        "customer_name": "John Doe",
        "transaction_type": "premium_feature",
        "features": [
            {
                "feature_id": "feat-001",
                "feature_type": "export_4k",
                "name": "4K Export",
                "description": "Export video in 4K resolution",
                "price": 29.99
            }
        ],
        "business_entity_id": "the_connection_practice"
    }
)

print(response.json())
```

## API Documentation

For detailed API documentation, see [CAPCUT_PIPIT_INTEGRATION.md](../../docs/CAPCUT_PIPIT_INTEGRATION.md).

## Error Handling

The integration includes comprehensive error handling for all API calls and webhooks. Errors are logged and stored in Notion for troubleshooting.

## Security

The integration implements the following security measures:

1. API key authentication for all endpoints
2. Webhook signature verification for CapCut and Pipit webhooks
3. HTTPS for all API calls
4. Secure storage of API keys and secrets in environment variables

## Testing

To test the integration, you can use the provided API endpoints with test credentials from CapCut and Pipit.

## Support

For support with this integration, please contact The HigherSelf Network support team.
