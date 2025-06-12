# Softr Integration Guide

This guide explains how to use the Softr integration to allow staff members to interface with agents in The HigherSelf Network Server.

## Overview

The Softr integration enables staff members to interact with agents through a user-friendly interface built with Softr. This allows non-technical staff to leverage the power of agents without needing to understand the underlying technical details.

Key features include:
- Staff authentication and authorization
- Agent interaction through a simple interface
- Tracking of interaction history
- Integration with workflow instances
- Webhook support for real-time updates

## Setup

### Prerequisites

1. A Softr account with admin access
2. A Softr application set up for your organization
3. The HigherSelf Network Server running with the Softr integration enabled

### Environment Variables

Add the following environment variables to your `.env` file:

```
# Softr Integration
SOFTR_API_KEY=your_softr_api_key
SOFTR_APP_ID=your_softr_app_id
SOFTR_API_URL=https://api.softr.io/v1
STAFF_API_KEY=your_staff_api_key
```

### Enabling the Integration

In your `config.json` file, ensure the Softr integration is enabled:

```json
{
  "integrations": {
    "softr": {
      "enabled": true
    }
  }
}
```

## Creating Staff Interfaces in Softr

### Setting Up Tables

Create the following tables in your Softr application:

1. **Staff Users**: Store information about staff members who can interact with agents
   - Fields: ID, Name, Email, Roles, API Key

2. **Agent Interactions**: Record interactions between staff and agents
   - Fields: ID, Staff ID, Agent ID, Request, Response, Status, Created At, Updated At

### Building the Interface

1. Create a new page in your Softr application
2. Add a form component for staff to submit requests to agents
3. Add a list component to display interaction history
4. Configure the form to send requests to the API endpoint

## API Endpoints

The following API endpoints are available for Softr integration:

### List Available Agents

```
GET /api/staff/agents
```

Returns a list of all available agents that staff can interact with.

**Headers:**
- `x-staff-id`: Staff member ID
- `x-api-key`: Staff API key

**Response:**
```json
{
  "agents": [
    {
      "id": "lead_capture_agent",
      "name": "Lead Capture Agent",
      "description": "Processes leads from various sources",
      "status": "active",
      "capabilities": ["lead_processing", "data_enrichment"]
    },
    ...
  ]
}
```

### Interact with an Agent

```
POST /api/staff/agents/{agent_id}/interact
```

Send a request to an agent and get a response.

**Headers:**
- `x-staff-id`: Staff member ID
- `x-api-key`: Staff API key

**Request Body:**
```json
{
  "staff_id": "staff_123",
  "agent_id": "lead_capture_agent",
  "request_type": "task",
  "content": "Process new lead from website form",
  "parameters": {
    "lead_name": "John Doe",
    "lead_email": "john@example.com"
  },
  "workflow_instance_id": "workflow_456"
}
```

**Response:**
```json
{
  "interaction": {
    "id": "interaction_789",
    "staff_id": "staff_123",
    "agent_id": "lead_capture_agent",
    "request": {
      "id": "request_123",
      "staff_id": "staff_123",
      "agent_id": "lead_capture_agent",
      "request_type": "task",
      "content": "Process new lead from website form",
      "parameters": {
        "lead_name": "John Doe",
        "lead_email": "john@example.com"
      },
      "created_at": "2023-06-15T10:30:00Z",
      "workflow_instance_id": "workflow_456"
    },
    "response": {
      "id": "response_456",
      "request_id": "request_123",
      "agent_id": "lead_capture_agent",
      "status": "success",
      "content": "Lead processed successfully",
      "data": {
        "processed_at": "2023-06-15T10:30:05Z"
      },
      "created_at": "2023-06-15T10:30:05Z"
    },
    "created_at": "2023-06-15T10:30:00Z",
    "updated_at": "2023-06-15T10:30:05Z",
    "status": "completed",
    "workflow_instance_id": "workflow_456"
  }
}
```

### Get Interaction History

```
GET /api/staff/interactions
```

Get the history of interactions between the staff member and agents.

**Headers:**
- `x-staff-id`: Staff member ID
- `x-api-key`: Staff API key

**Query Parameters:**
- `agent_id` (optional): Filter by agent ID

**Response:**
```json
{
  "interactions": [
    {
      "id": "interaction_789",
      "staff_id": "staff_123",
      "agent_id": "lead_capture_agent",
      "request": { ... },
      "response": { ... },
      "created_at": "2023-06-15T10:30:00Z",
      "updated_at": "2023-06-15T10:30:05Z",
      "status": "completed",
      "workflow_instance_id": "workflow_456"
    },
    ...
  ]
}
```

### Softr Webhook

```
POST /api/staff/webhooks/softr
```

Webhook endpoint for Softr events.

**Headers:**
- `x-signature`: Webhook signature for verification

**Request Body:**
```json
{
  "event_type": "new_staff_request",
  "data": {
    "staff_id": "staff_123",
    "agent_id": "lead_capture_agent",
    "request_type": "task",
    "content": "Process new lead from website form",
    "parameters": {
      "lead_name": "John Doe",
      "lead_email": "john@example.com"
    },
    "workflow_instance_id": "workflow_456"
  },
  "timestamp": "2023-06-15T10:30:00Z"
}
```

## Security Considerations

1. Always use HTTPS for all API requests
2. Keep API keys secure and rotate them regularly
3. Implement proper authentication for all staff users
4. Use webhook signatures to verify webhook requests
5. Limit staff permissions based on roles

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure staff ID and API key are correct
2. **Agent Not Found**: Verify the agent ID exists in the system
3. **Webhook Signature Mismatch**: Check webhook secret and signature calculation

### Logging

Enable debug logging to troubleshoot issues:

```
LOG_LEVEL=debug
```

## Examples

### Example: Processing a Lead

```javascript
// Softr frontend code
async function processLead() {
  const response = await fetch('/api/staff/agents/lead_capture_agent/interact', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-staff-id': 'staff_123',
      'x-api-key': 'your_api_key'
    },
    body: JSON.stringify({
      staff_id: 'staff_123',
      agent_id: 'lead_capture_agent',
      request_type: 'task',
      content: 'Process new lead from website form',
      parameters: {
        lead_name: document.getElementById('name').value,
        lead_email: document.getElementById('email').value
      }
    })
  });

  const result = await response.json();
  displayResult(result);
}
```
