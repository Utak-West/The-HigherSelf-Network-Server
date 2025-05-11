# Workflows Library - Notion AI Mapping Script

## Database Overview
The Workflows Library contains definitions of all business workflows that can be instantiated by the system, serving as templates for workflow instances and documenting the business processes.

## Required Properties

Create or update the following properties in your Workflows Library database:

1. **Workflow Name** (Title property)
   - Description: Name of the workflow
   - Type: Title

2. **Workflow ID** (Text property)
   - Description: Unique workflow identifier
   - Type: Text
   - Format: "WF-" followed by 8 random alphanumeric characters

3. **Description** (Text property)
   - Description: Detailed description of the workflow
   - Type: Rich Text

4. **Status** (Select property)
   - Description: Current status of the workflow
   - Type: Select
   - Options:
     - Draft
     - Implemented
     - Active
     - Deprecated
     - Under Review

5. **Business Entities** (Relation property)
   - Description: Business entities this workflow applies to
   - Type: Relation
   - Related to: Business Entities Registry

6. **Trigger Type** (Select property)
   - Description: What initiates this workflow
   - Type: Select
   - Options:
     - Manual
     - Form Submission
     - API Call
     - Scheduled
     - Event
     - Database Change
     - External System

7. **Trigger Conditions** (Text property)
   - Description: Specific conditions that trigger this workflow
   - Type: Rich Text

8. **Workflow Steps** (Text property)
   - Description: Detailed steps in JSON or structured format
   - Type: Rich Text

9. **Required Integrations** (Relation property)
   - Description: API integrations needed for this workflow
   - Type: Relation
   - Related to: API Integrations Catalog

10. **Related Use Cases** (Relation property)
    - Description: Use cases implemented by this workflow
    - Type: Relation
    - Related to: Use Cases Library

11. **Active Instances Count** (Number property)
    - Description: Number of currently active instances
    - Type: Number
    - Format: Number

12. **Total Instances Count** (Number property)
    - Description: Total number of instances created
    - Type: Number
    - Format: Number

13. **Average Completion Time** (Number property)
    - Description: Average time to complete (hours)
    - Type: Number
    - Format: Number

14. **Success Rate** (Number property)
    - Description: Percentage of successful completions
    - Type: Number
    - Format: Percent

15. **Version** (Text property)
    - Description: Current version of the workflow
    - Type: Text

16. **Created Date** (Date property)
    - Description: When the workflow was created
    - Type: Date
    - Include time: Yes

17. **Last Updated** (Date property)
    - Description: When the workflow was last updated
    - Type: Date
    - Include time: Yes

18. **Owner** (Person property)
    - Description: Person responsible for this workflow
    - Type: Person

19. **Required Agents** (Relation property)
    - Description: Agents needed for this workflow
    - Type: Relation
    - Related to: Agent Registry

20. **Data Schema** (Text property)
    - Description: Schema for workflow data payload
    - Type: Rich Text

21. **Tags** (Multi-select property)
    - Description: Categorization tags
    - Type: Multi-select
    - Options:
      - Client Onboarding
      - Lead Nurturing
      - Order Processing
      - Content Creation
      - Booking Management
      - Feedback Collection
      - Reporting
      - Administrative

22. **Documentation URL** (URL property)
    - Description: Link to detailed documentation
    - Type: URL

23. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

24. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. New Workflow Creation

When a new record is created:
- Generate a unique Workflow ID if empty
- Set Created Date to current date and time
- Set Status to "Draft" if empty
- Create a task in Master Tasks Database for workflow review

### 2. Status Change Actions

When Status changes:
- If changed to "Implemented", update Last Updated to current date and time
- If changed to "Active", notify business entities using this workflow
- If changed to "Deprecated", create tasks to update dependent systems
- If changed to "Under Review", create review tasks

### 3. Version Management

When Version is updated:
- Update Last Updated to current date and time
- Create documentation update task
- Notify stakeholders about the new version

### 4. Performance Monitoring

When Active Instances Count, Success Rate, or Average Completion Time changes:
- Update performance dashboards
- If Success Rate drops below 90%, create an alert task

### 5. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Workflows** (Default view)
   - Show all workflows
   - Sort: Status (Active first), then Workflow Name (A-Z)

2. **Active Workflows**
   - Filter: Status = "Active"
   - Sort: Workflow Name (A-Z)

3. **By Business Entity**
   - Group by: Business Entities
   - Sort: Workflow Name (A-Z)

4. **By Trigger Type**
   - Group by: Trigger Type
   - Sort: Workflow Name (A-Z)

5. **Development Pipeline**
   - Filter: Status = "Draft" OR Status = "Under Review"
   - Sort: Last Updated (newest first)

6. **Performance Dashboard**
   - Filter: Status = "Active"
   - Sort: Success Rate (lowest first)
   - Properties to show prominently: Active Instances Count, Total Instances Count, Average Completion Time, Success Rate

7. **Documentation View**
   - Properties to show prominently: Workflow Name, Description, Workflow Steps, Data Schema, Trigger Conditions
   - Sort: Workflow Name (A-Z)

## Sample Data

Add a few sample workflows if needed:

1. **Lead Nurturing Process**
   - Trigger Type: Form Submission
   - Status: Active
   - Business Entities: The Connection Practice, The 7 Space
   - Description: "Automated process to nurture leads from initial contact to qualified prospect"
   - Workflow Steps: (Structured steps for lead nurturing)
   - Tags: Lead Nurturing

2. **Art Purchase Fulfillment**
   - Trigger Type: Event
   - Status: Active
   - Business Entities: Art Gallery
   - Description: "End-to-end process for fulfilling art purchases including payment processing, packaging, and shipping"
   - Workflow Steps: (Structured steps for art purchase fulfillment)
   - Tags: Order Processing

## Relationships with Other Databases

This database has relationships with:
- Business Entities Registry (many-to-many)
- API Integrations Catalog (many-to-many)
- Use Cases Library (many-to-many)
- Agent Registry (many-to-many)
- Workflow Instances (one-to-many)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Days Since Updated** (Formula property)
   - Formula: `dateBetween(prop("Last Updated"), now(), "days")`
   - Output: Number

3. **Integration Count** (Formula property)
   - Formula: `length(prop("Required Integrations"))`
   - Output: Number
