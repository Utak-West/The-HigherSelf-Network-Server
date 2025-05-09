# Workflow Management Guide

This document explains how workflows are managed in the Windsurf Agent Network, providing standardized processing for The HigherSelf Network's business operations.

## Workflow Structure

Workflows in the system follow a state machine model, with clearly defined states, transitions, and actions. This structure is stored in Notion and used by agents to process business events.

### Core Components

- **States**: Represent distinct phases in a business process
- **Transitions**: Define allowed movements between states
- **Actions**: Operations performed when entering states or during transitions
- **History**: Complete audit trail of all state changes and actions

## Workflow Definition Example

Below is an example of a retreat booking workflow definition:

```python
{
    "name": "Retreat Booking Process",
    "description": "End-to-end process for handling retreat bookings",
    "initial_state": "new_booking",
    "states": {
        "new_booking": {
            "description": "A new booking has been received",
            "entry_actions": [
                {
                    "type": "publish_event",
                    "params": {
                        "event_type": "send_email_notification",
                        "event_data": {
                            "notification_type": "email",
                            "data": {
                                "recipient_email": "{{processed_booking.client_details.email}}",
                                "template_id": "booking_confirmation"
                            }
                        }
                    }
                }
            ]
        },
        "payment_pending": {
            "description": "Payment is pending for the booking"
        },
        "payment_confirmed": {
            "description": "Payment has been confirmed"
        },
        // Additional states...
    },
    "transitions": [
        {
            "from_state": "new_booking",
            "to_state": "payment_pending",
            "event": "booking_processed"
        },
        {
            "from_state": "payment_pending",
            "to_state": "payment_confirmed",
            "event": "payment_received"
        },
        // Additional transitions...
    ]
}
```

## Workflow Instances

When a real-world event occurs (like a new booking or lead submission), a workflow instance is created:

1. The appropriate workflow definition is retrieved from Notion
2. A new instance is created in the Active Workflow Instances database
3. The instance starts in the defined initial state
4. As events occur, the state is updated according to allowed transitions
5. All actions and state changes are logged in the history

## Creating New Workflows

To create a new workflow:

1. Define the workflow in the Workflows Library Notion database:
   - Set a unique Workflow ID
   - Define all states and transitions
   - Specify the initial state
   - Associate with the relevant business entity

2. Ensure agents are configured to handle the workflow:
   - Update agent code if needed to handle any workflow-specific logic
   - Configure required integrations and notifications

## Workflow State Management

Agents are responsible for properly managing workflow state:

1. Updating the `Current State` field to reflect the new state
2. Updating `Last Transition Date`
3. Appending a descriptive entry to the `History Log` field
4. Setting appropriate status values (Active, Completed, Error)

Example history log entry:

```json
{
  "timestamp": "2025-05-09T12:34:56.789Z",
  "action": "[TCP_AGENT_001] Transitioned from payment_pending to payment_confirmed",
  "details": {
    "payment_amount": 499.99,
    "transaction_id": "tx_123456",
    "payment_method": "credit_card"
  }
}
```

## Tasks and Follow-ups

Workflows can generate tasks in the Master Tasks Database:

1. An agent determines a task is needed (e.g., manual review of a document)
2. The agent creates a task in the Master Tasks Database
3. The task is linked to the workflow instance
4. The task creation is logged in the workflow history
5. Notifications can be sent to assignees

## Error Handling

When errors occur in workflow processing:

1. The workflow instance state is not changed
2. The error is logged in the workflow history
3. The `Status` is set to "Error"
4. The `Error Message` field is populated
5. An alert can be triggered for operational staff

## Visualization

Workflow state machines can be visualized to aid understanding:

1. Create a diagram showing states and transitions
2. Store the visualization URL in the `Visualization URL` field
3. Reference the visualization in operational documentation

## Common Workflows

The system includes several standard workflows:

1. **Lead Processing** - Handling leads from various sources
2. **Retreat Booking** - Managing the end-to-end retreat booking process
3. **Art Sales** - Processing art sales and inventory updates
4. **Content Review** - Managing the review of AI-generated content

Additional workflows can be created as needed to support business operations.
