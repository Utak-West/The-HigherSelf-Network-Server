# Agent Registry - Notion AI Mapping Script

## Database Overview
The Agent Registry database catalogs all intelligent agents in the system, tracking their capabilities, status, and relationships with business entities and APIs.

## Required Properties

Create or update the following properties in your Agent Registry database:

1. **Agent Name** (Title property)
   - Description: Name of the agent
   - Type: Title

2. **Agent ID** (Text property)
   - Description: Unique agent identifier
   - Type: Text
   - Format: Typically follows a pattern like "LEAD_CAPTURE_AGENT"

3. **Description** (Text property)
   - Description: Detailed description of the agent's purpose and functionality
   - Type: Rich Text

4. **Version** (Text property)
   - Description: Current version of the agent
   - Type: Text
   - Format: Semantic versioning (e.g., "1.0.0")

5. **Status** (Select property)
   - Description: Current operational status
   - Type: Select
   - Options:
     - Deployed
     - Development
     - Inactive
     - Deprecated

6. **Capabilities** (Multi-select property)
   - Description: What the agent can do
   - Type: Multi-select
   - Options:
     - Booking Detection
     - Client Communication
     - Lead Processing
     - CRM Sync
     - Inventory Management
     - Task Creation
     - Workflow Management
     - Notification Dispatch
     - Content Generation
     - Learning Content Management
     - Transcription Processing

7. **Primary APIs Utilized** (Multi-select property)
   - Description: External APIs the agent uses
   - Type: Multi-select
   - Options:
     - NOTION_API
     - HUBSPOT_API
     - TYPEFORM_API
     - AIRTABLE_API
     - AMELIA_API
     - WOOCOMMERCE_API
     - TUTORLM_API
     - STRIPE_API
     - PLAUD_API

8. **Business Entity Association** (Relation property)
   - Description: Business entities this agent works with
   - Type: Relation
   - Related to: Business Entities Registry

9. **Runtime Environment** (Select property)
   - Description: Where the agent runs
   - Type: Select
   - Options:
     - Docker (HigherSelf Network Server)
     - Serverless

10. **Source Code Location** (Text property)
    - Description: Where to find the agent's code
    - Type: Text

11. **Last Execution** (Date property)
    - Description: When the agent last ran
    - Type: Date
    - Include time: Yes

12. **Execution Count** (Number property)
    - Description: How many times the agent has run
    - Type: Number
    - Format: Number

13. **Success Rate** (Number property)
    - Description: Percentage of successful executions
    - Type: Number
    - Format: Percent

14. **Communication Patterns** (Relation property)
    - Description: Communication patterns this agent uses
    - Type: Relation
    - Related to: Agent Communication Patterns

15. **API Integrations** (Relation property)
    - Description: Specific API integrations used
    - Type: Relation
    - Related to: API Integrations Catalog

16. **Data Transformations** (Relation property)
    - Description: Data transformations this agent performs
    - Type: Relation
    - Related to: Data Transformations Registry

17. **Workflows** (Relation property)
    - Description: Workflows this agent participates in
    - Type: Relation
    - Related to: Workflows Library

18. **Owner** (Person property)
    - Description: Person responsible for this agent
    - Type: Person

19. **Documentation URL** (URL property)
    - Description: Link to detailed documentation
    - Type: URL

20. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

21. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. New Agent Registration

When a new record is created:
- Set Status to "Development" if empty
- Create a task in Master Tasks Database for agent review
- Notify the Owner about the new agent

### 2. Status Change Actions

When Status changes:
- If changed to "Deployed", update Version if needed
- If changed to "Deprecated", create tasks to update dependent workflows
- If changed to "Inactive", check and update related Business Entity Associations

### 3. Performance Monitoring

When Execution Count or Success Rate changes:
- If Success Rate drops below 95%, create an alert task
- Update performance dashboards
- Log the change in a monitoring system

### 4. Version Management

When Version is updated:
- Create documentation update task
- Notify stakeholders about the new version
- Create testing tasks if needed

### 5. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Agents** (Default view)
   - Show all agents
   - Sort: Status (Deployed first), then Agent Name (A-Z)

2. **Active Agents**
   - Filter: Status = "Deployed"
   - Sort: Agent Name (A-Z)

3. **By Business Entity**
   - Group by: Business Entity Association
   - Sort: Agent Name (A-Z)

4. **By Capability**
   - Group by: Capabilities
   - Sort: Agent Name (A-Z)

5. **Development Pipeline**
   - Filter: Status = "Development"
   - Sort: Version (A-Z)

6. **Performance Dashboard**
   - Filter: Status = "Deployed"
   - Sort: Success Rate (lowest first)
   - Properties to show prominently: Execution Count, Success Rate, Last Execution

7. **API Usage View**
   - Group by: Primary APIs Utilized
   - Sort: Agent Name (A-Z)

## Sample Data

Add a few sample agents if needed:

1. **Lead Capture Agent**
   - Agent ID: LEAD_CAPTURE_AGENT
   - Description: "Processes leads from various sources and creates appropriate workflow instances"
   - Version: "1.2.0"
   - Status: Deployed
   - Capabilities: Lead Processing, CRM Sync, Task Creation
   - Primary APIs Utilized: NOTION_API, HUBSPOT_API, TYPEFORM_API
   - Business Entity Association: The Connection Practice, The 7 Space
   - Runtime Environment: Docker (HigherSelf Network Server)

2. **Booking Agent**
   - Agent ID: BOOKING_AGENT
   - Description: "Manages bookings and appointments across platforms"
   - Version: "1.0.1"
   - Status: Deployed
   - Capabilities: Booking Detection, Client Communication, Task Creation
   - Primary APIs Utilized: NOTION_API, AMELIA_API, WOOCOMMERCE_API
   - Business Entity Association: The 7 Space, Art Gallery
   - Runtime Environment: Docker (HigherSelf Network Server)

## Relationships with Other Databases

This database has relationships with:
- Business Entities Registry (many-to-many)
- Agent Communication Patterns (one-to-many)
- API Integrations Catalog (many-to-many)
- Data Transformations Registry (many-to-many)
- Workflows Library (many-to-many)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Days Since Last Execution** (Formula property)
   - Formula: `if(empty(prop("Last Execution")), "Never Executed", dateBetween(prop("Last Execution"), now(), "days"))`
   - Output: Text

3. **API Count** (Formula property)
   - Formula: `length(prop("Primary APIs Utilized"))`
   - Output: Number
