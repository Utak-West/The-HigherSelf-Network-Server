# Agent Communication Patterns - Notion AI Mapping Script

## Database Overview
The Agent Communication Patterns database defines how agents communicate with each other in the system, documenting message formats, protocols, and patterns for reliable agent-to-agent interactions.

## Required Properties

Create or update the following properties in your Agent Communication Patterns database:

1. **Pattern Name** (Title property)
   - Description: Name of the communication pattern
   - Type: Title

2. **Description** (Text property)
   - Description: Detailed description of the pattern
   - Type: Rich Text

3. **Source Agent** (Relation property)
   - Description: Agent that initiates the communication
   - Type: Relation
   - Related to: Agent Registry

4. **Target Agent** (Relation property)
   - Description: Agent that receives the communication
   - Type: Relation
   - Related to: Agent Registry

5. **Message Format** (Text property)
   - Description: Structure of the message (often JSON schema)
   - Type: Rich Text

6. **Communication Protocol** (Select property)
   - Description: Protocol used for communication
   - Type: Select
   - Options:
     - HTTP
     - Message Queue
     - WebSocket
     - Direct Function Call
     - Database Event
     - Webhook
     - Custom

7. **Sample Payload** (Text property)
   - Description: Example message payload in JSON format
   - Type: Rich Text

8. **Active Workflows Using** (Relation property)
   - Description: Workflows that use this pattern
   - Type: Relation
   - Related to: Workflows Library

9. **Version** (Text property)
   - Description: Version of the communication pattern
   - Type: Text

10. **Status** (Select property)
    - Description: Current status of the pattern
    - Type: Select
    - Options:
      - Active
      - Deprecated
      - In Development
      - Testing
      - Archived

11. **Created Date** (Date property)
    - Description: When the pattern was created
    - Type: Date
    - Include time: Yes

12. **Last Updated** (Date property)
    - Description: When the pattern was last updated
    - Type: Date
    - Include time: Yes

13. **Success Criteria** (Text property)
    - Description: How to determine if communication was successful
    - Type: Rich Text

14. **Error Handling** (Text property)
    - Description: How errors are handled in this pattern
    - Type: Rich Text

15. **Timeout Settings** (Number property)
    - Description: Timeout in seconds
    - Type: Number
    - Format: Number

16. **Required Permissions** (Multi-select property)
    - Description: Permissions needed for this communication
    - Type: Multi-select
    - Options:
      - Read
      - Write
      - Execute
      - Admin
      - System

17. **Tags** (Multi-select property)
    - Description: Categorization tags
    - Type: Multi-select
    - Options:
      - Core
      - Business Logic
      - Data Sync
      - Notification
      - Monitoring
      - Security

18. **Documentation URL** (URL property)
    - Description: Link to detailed documentation
    - Type: URL

19. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

20. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. New Pattern Creation

When a new record is created:
- Set Created Date to current date and time
- Set Status to "In Development"
- Create a task in Master Tasks Database for pattern review
- Notify relevant developers or technical staff

### 2. Status Change Actions

When Status changes:
- If changed to "Active", update Last Updated to current date and time
- If changed to "Deprecated", create tasks to update dependent workflows
- If changed to "Testing", create test workflow instances

### 3. Version Management

When Version is updated:
- Update Last Updated to current date and time
- Create documentation update task
- Notify agents and workflows using this pattern

### 4. Usage Tracking

When Active Workflows Using is updated:
- Update a usage count formula
- If pattern is used by critical workflows, update Tags to include "Core"

### 5. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Patterns** (Default view)
   - Show all communication patterns
   - Sort: Status (Active first), then Pattern Name (A-Z)

2. **Active Patterns**
   - Filter: Status = "Active"
   - Sort: Pattern Name (A-Z)

3. **By Source Agent**
   - Group by: Source Agent
   - Sort: Pattern Name (A-Z)

4. **By Target Agent**
   - Group by: Target Agent
   - Sort: Pattern Name (A-Z)

5. **By Protocol**
   - Group by: Communication Protocol
   - Sort: Pattern Name (A-Z)

6. **Development & Testing**
   - Filter: Status = "In Development" OR Status = "Testing"
   - Sort: Last Updated (newest first)

7. **Documentation View**
   - Properties to show prominently: Pattern Name, Description, Message Format, Sample Payload, Success Criteria, Error Handling
   - Sort: Pattern Name (A-Z)

## Sample Data

Add a few sample communication patterns if needed:

1. **Lead Capture to Task Creation**
   - Source Agent: Lead Capture Agent
   - Target Agent: Task Management Agent
   - Communication Protocol: HTTP
   - Status: Active
   - Message Format: (JSON schema for lead data)
   - Sample Payload: (Example JSON with lead information)

2. **Booking Confirmation Notification**
   - Source Agent: Booking Agent
   - Target Agent: Notification Agent
   - Communication Protocol: Message Queue
   - Status: Active
   - Message Format: (JSON schema for booking notification)
   - Sample Payload: (Example JSON with booking details)

## Relationships with Other Databases

This database has relationships with:
- Agent Registry (many-to-one for Source Agent)
- Agent Registry (many-to-one for Target Agent)
- Workflows Library (many-to-many)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Days Since Updated** (Formula property)
   - Formula: `dateBetween(prop("Last Updated"), now(), "days")`
   - Output: Number

3. **Usage Count** (Formula property)
   - Formula: `length(prop("Active Workflows Using"))`
   - Output: Number
