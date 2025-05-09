# API and Webhook Integration Guide

This document details the API endpoints and webhook integrations for the Windsurf Agent Network, which serves The HigherSelf Network's Notion-centric operations.

## API Server

The system includes a FastAPI-based server that provides webhook endpoints for external system integration. All API interactions maintain Notion as the central hub for data and workflow management.

### Server Configuration

The API server runs on port 8000 by default (configurable via `SERVER_PORT` environment variable) and includes CORS middleware for secure cross-origin requests.

## Available Endpoints

### Health Check

```http
GET /health
```

Provides health status of all agents in the system.

### Lead Capture Endpoints

#### TypeForm Webhook

```http
POST /webhooks/typeform
```

Receives form submissions from TypeForm and processes them through the `LeadCaptureAgent`.

**Query Parameters:**

- `business_entity_id` - ID of the business entity (required)
- `workflow_id` - ID of the workflow to instantiate (required)
- `sync_to_hubspot` - Whether to sync the lead to HubSpot (default: true)

**Headers:**

- `X-Webhook-Secret` - Webhook authentication secret

#### Website Form Submission

```http
POST /api/forms/submit
```

Processes website form submissions and creates workflow instances.

**Request Body:**

```json
{
  "form_id": "contact_form_001",
  "business_entity_id": "The Connection Practice",
  "workflow_id": "TCP_WORKFLOW_001",
  "form_data": {
    "email": "client@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "+1234567890",
    "interests": ["retreat", "coaching"]
  },
  "sync_to_hubspot": true
}
```

### Booking Endpoints

#### Amelia Webhook

```http
POST /webhooks/amelia
```

Receives booking events from Amelia and processes them through the `BookingAgent`.

**Query Parameters:**

- `business_entity_id` - ID of the business entity (optional, defaults to "The Connection Practice")
- `workflow_id` - ID of the workflow to instantiate (required for new bookings)

**Headers:**

- `X-Webhook-Secret` - Webhook authentication secret

**Request Body for New Booking:**

```json
{
  "event_type": "new_booking",
  "booking": {
    "booking_id": "amelia_booking_123",
    "customer_id": "cust_456",
    "service_id": "service_001",
    "appointment_id": "appt_789",
    "status": "approved",
    "created_at": "2025-05-09T12:00:00Z",
    "starts_at": "2025-05-15T09:00:00Z",
    "ends_at": "2025-05-15T17:00:00Z",
    "customer_info": {
      "email": "client@example.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "phone": "+1234567890"
    },
    "payment_info": {
      "status": "paid",
      "amount": 499.00,
      "currency": "USD"
    }
  }
}
```

**Request Body for Status Update:**

```json
{
  "event_type": "booking_status_update",
  "booking_id": "amelia_booking_123",
  "status": "paid",
  "additional_data": {
    "payment_amount": 499.00,
    "transaction_id": "tx_abc123"
  }
}
```

### Workflow Management

#### Get Workflow Instance

```http
GET /workflows/{instance_id}
```

Retrieves details of a specific workflow instance.

## Webhook Security

All webhook endpoints are protected with a shared secret. The secret must be provided in the `X-Webhook-Secret` header, and must match the value in the `WEBHOOK_SECRET` environment variable.

## Setting Up Integrations

### TypeForm Integration

1. In your TypeForm dashboard, navigate to the form you want to integrate
2. Go to Connect → Webhooks
3. Enter the webhook URL: `https://your-server.com/webhooks/typeform?business_entity_id=YOUR_ENTITY&workflow_id=YOUR_WORKFLOW`
4. Set the webhook secret
5. Ensure the form includes fields for email, name, and other required information

### Amelia Integration

1. Configure Amelia to send webhook notifications for new bookings and status changes
2. Set the webhook URL: `https://your-server.com/webhooks/amelia?workflow_id=YOUR_WORKFLOW`
3. Configure the webhook payload format to match the expected format
4. Set the webhook secret

## Handling Webhook Responses

All webhook endpoints respond with a standardized format:

```json
{
  "status": "success|error|duplicate",
  "message": "Descriptive message",
  "data": {
    // Additional data specific to the response
  }
}
```

- `success` - The webhook was processed successfully
- `error` - An error occurred processing the webhook
- `duplicate` - The webhook was recognized as a duplicate of a previously processed event

## Cross-Platform Data Flow

All data received through webhooks flows into Notion as the central hub:

1. Webhook data is received and validated
2. The appropriate agent processes the data
3. A workflow instance is created or updated in Notion
4. The full history is maintained in the Notion database
5. Optional synchronization with other platforms (HubSpot, etc.) occurs
6. Any required tasks are created in the Master Tasks Database

This ensures that Notion remains the single source of truth while allowing seamless integration with external platforms.

## Rate Limiting

The API implements rate limiting to prevent abuse. Clients should handle 429 responses appropriately by backing off and retrying.
