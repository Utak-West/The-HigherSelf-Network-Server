# CapCut and Pipit Integration Guide

This document provides detailed information about the integration between CapCut (video editing platform) and Pipit (payment processing service) for The HigherSelf Network Server.

## Overview

The integration allows users to:

1. Export edited videos from CapCut directly to The HigherSelf Network platform
2. Process payments through Pipit for premium video features or services
3. Store video metadata and transaction information in Notion as the central hub
4. Track the status of video exports and payments

## Architecture

The integration follows the central hub architecture of The HigherSelf Network Server, with Notion serving as the central data store. All interactions with CapCut and Pipit are managed through dedicated service classes, and all data is synchronized with Notion.

```
┌─────────┐     ┌───────────────────────────┐     ┌────────┐
│  CapCut │────▶│ The HigherSelf Network    │────▶│ Pipit  │
└─────────┘     │ Server                    │     └────────┘
                │                           │
                │  ┌─────────────────────┐  │
                │  │ Notion (Central Hub)│  │
                │  └─────────────────────┘  │
                └───────────────────────────┘
```

## Prerequisites

To use this integration, you need:

1. A CapCut account with API access
2. A Pipit account with API access
3. The HigherSelf Network Server with Notion integration configured

## Configuration

Add the following environment variables to your `.env` file:

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

## API Endpoints

### CapCut Endpoints

#### Export Video from CapCut

```http
POST /api/capcut-pipit/capcut/export
```

Request body:
```json
{
  "project_id": "cc-proj-123456789",
  "format": "mp4",
  "quality": "full_hd",
  "callback_url": "https://api.thehigherself.network/api/capcut/webhook",
  "business_entity_id": "the_connection_practice",
  "include_metadata": true,
  "watermark": false
}
```

Response:
```json
{
  "status": "success",
  "message": "Video export started successfully",
  "export_id": "export-123456789",
  "content_id": "notion-page-id-123456789",
  "estimated_completion_time": "2023-08-01T12:30:00Z"
}
```

#### Check Export Status

```http
GET /api/capcut-pipit/capcut/exports/{export_id}
```

Response:
```json
{
  "status": "success",
  "export_id": "export-123456789",
  "export_status": "completed",
  "content_id": "notion-page-id-123456789",
  "video_url": "https://cdn.capcut.com/videos/123456789.mp4",
  "progress": 100,
  "metadata": {
    "title": "My Video",
    "description": "A description of my video",
    "duration": 60.5,
    "width": 1080,
    "height": 1920,
    "format": "mp4",
    "quality": "full_hd",
    "frame_rate": 30,
    "size_bytes": 10485760,
    "created_at": "2023-08-01T12:00:00Z",
    "tags": ["mindfulness", "meditation"],
    "effects": ["transition", "filter"],
    "audio_tracks": ["background_music", "voiceover"]
  }
}
```

#### CapCut Webhook

```http
POST /api/capcut-pipit/capcut/webhook
```

This endpoint receives notifications from CapCut when an export is completed or fails.

### Pipit Endpoints

#### Create Payment

```http
POST /api/capcut-pipit/pipit/payments
```

Request body:
```json
{
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
  "success_url": "https://thehigherself.network/payment/success",
  "cancel_url": "https://thehigherself.network/payment/cancel",
  "business_entity_id": "the_connection_practice"
}
```

Response:
```json
{
  "status": "success",
  "message": "Payment created successfully",
  "payment_id": "pay-123456789",
  "payment_url": "https://checkout.pipit.com/pay/123456789",
  "transaction_id": "notion-page-id-123456789"
}
```

#### Check Payment Status

```http
GET /api/capcut-pipit/pipit/payments/{payment_id}
```

Response:
```json
{
  "status": "success",
  "payment_id": "pay-123456789",
  "payment_status": "completed",
  "transaction_id": "notion-page-id-123456789",
  "amount": 29.99,
  "currency": "usd",
  "customer_email": "customer@example.com",
  "created_at": "2023-08-01T12:00:00Z",
  "updated_at": "2023-08-01T12:05:00Z"
}
```

#### Pipit Webhook

```http
POST /api/capcut-pipit/pipit/webhook
```

This endpoint receives notifications from Pipit when a payment is completed, failed, or refunded.

### Video Transaction Endpoints

#### Create Transaction

```http
POST /api/capcut-pipit/transactions
```

Request body:
```json
{
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
```

Response:
```json
{
  "status": "success",
  "message": "Transaction created successfully",
  "transaction_id": "notion-page-id-123456789",
  "payment_url": "https://checkout.pipit.com/pay/123456789"
}
```

#### Check Transaction Status

```http
GET /api/capcut-pipit/transactions/{transaction_id}
```

Response:
```json
{
  "status": "success",
  "transaction_id": "notion-page-id-123456789",
  "transaction_status": "completed",
  "payment_status": "completed",
  "video_id": "vid-987654321",
  "features": [
    {
      "feature_id": "feat-001",
      "feature_type": "export_4k",
      "name": "4K Export",
      "description": "Export video in 4K resolution",
      "price": 29.99
    }
  ],
  "amount": 29.99,
  "currency": "usd",
  "created_at": "2023-08-01T12:00:00Z",
  "updated_at": "2023-08-01T12:05:00Z"
}
```

## Notion Integration

The integration uses two Notion databases:

1. **Video Content Database**: Stores information about videos exported from CapCut
2. **Video Transactions Database**: Stores information about payments processed through Pipit

All data is synchronized with Notion as the central hub, ensuring a single source of truth for all video and transaction data.

## Error Handling

The integration includes comprehensive error handling for all API calls and webhooks. Errors are logged and stored in Notion for troubleshooting.

## Security

The integration implements the following security measures:

1. API key authentication for all endpoints
2. Webhook signature verification for CapCut and Pipit webhooks
3. HTTPS for all API calls
4. Secure storage of API keys and secrets in environment variables

## Logging

All integration activities are logged using the Loguru logger, providing detailed information for troubleshooting and auditing.

## Testing

To test the integration, you can use the provided API endpoints with test credentials from CapCut and Pipit.

## Support

For support with this integration, please contact The HigherSelf Network support team.
