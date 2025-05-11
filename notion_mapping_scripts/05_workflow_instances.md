# Workflow Instances - Notion AI Mapping Script

## Database Overview
The Workflow Instances database tracks active business processes across all entities, serving as the central operational hub for monitoring and managing workflows in real-time.

## Required Properties

Create or update the following properties in your Workflow Instances database:

1. **Instance Name** (Title property)
   - Description: Descriptive name of the workflow instance
   - Type: Title

2. **Instance ID** (Text property)
   - Description: Unique instance identifier
   - Type: Text
   - Format: "INST-" followed by 8 random alphanumeric characters

3. **Workflow** (Relation property)
   - Description: Related workflow definition
   - Type: Relation
   - Related to: Workflows Library

4. **Status** (Select property)
   - Description: Current status
   - Type: Select
   - Options:
     - Active
     - Completed
     - Error
     - On Hold
     - Cancelled

5. **Current Step** (Text property)
   - Description: Current workflow step
   - Type: Text

6. **Business Entity** (Relation property)
   - Description: Related business entity
   - Type: Relation
   - Related to: Business Entities Registry

7. **Contact** (Relation property)
   - Description: Related contact
   - Type: Relation
   - Related to: Contacts & Profiles

8. **Start Date** (Date property)
   - Description: When the workflow started
   - Type: Date
   - Include time: Yes

9. **End Date** (Date property)
   - Description: When the workflow ended (if completed)
   - Type: Date
   - Include time: Yes

10. **Step History** (Rich Text property)
    - Description: Log of step transitions (JSON format)
    - Type: Rich Text

11. **Data Payload** (Rich Text property)
    - Description: Workflow data in JSON format
    - Type: Rich Text

12. **Related Tasks** (Relation property)
    - Description: Tasks associated with this workflow
    - Type: Relation
    - Related to: Master Tasks Database

13. **Priority** (Select property)
    - Description: Workflow priority
    - Type: Select
    - Options:
      - Low
      - Medium
      - High
      - Urgent

14. **Assigned Agent** (Relation property)
    - Description: Agent responsible for this workflow
    - Type: Relation
    - Related to: Agent Registry

15. **Source System** (Select property)
    - Description: System that initiated the workflow
    - Type: Select
    - Options:
      - Notion
      - Website
      - WooCommerce
      - Amelia
      - Acuity
      - Typeform
      - Manual
      - Other

16. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

17. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. New Workflow Initialization

When a new record is created:
- Generate a unique Instance ID if empty
- Set Start Date to current date and time if empty
- Set Status to "Active" if empty
- Create initial tasks based on workflow definition
- Add first step to Step History

### 2. Step Progression

When Current Step changes:
- Update Step History with the new step and timestamp
- Create or update tasks based on the new step requirements
- If step is a terminal step, set Status to "Completed" and set End Date

### 3. Status Change Actions

When Status changes:
- If changed to "Completed", set End Date to current date and time
- If changed to "Error", create a task for technical review
- If changed to "On Hold", notify relevant stakeholders
- If changed to "Cancelled", cancel all related open tasks

### 4. Task Management

When Related Tasks is updated:
- Check if all required tasks for the current step are completed
- If yes, suggest the next step based on workflow definition

### 5. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Workflows** (Default view)
   - Show all workflow instances
   - Sort: Start Date (newest first)

2. **Active Workflows**
   - Filter: Status = "Active"
   - Sort: Priority (highest first), then Start Date (oldest first)

3. **By Business Entity**
   - Group by: Business Entity
   - Filter: Status = "Active" OR Status = "On Hold"
   - Sort: Start Date (newest first)

4. **By Workflow Type**
   - Group by: Workflow (relation)
   - Sort: Start Date (newest first)

5. **Needs Attention**
   - Filter: Status = "Error" OR (Status = "Active" AND Priority = "Urgent")
   - Sort: Start Date (oldest first)

6. **Recently Completed**
   - Filter: Status = "Completed"
   - Sort: End Date (newest first)
   - Limit to last 30 days

7. **Timeline View**
   - Timeline by: Start Date to End Date
   - Group by: Business Entity

## Sample Data

Add a few sample workflow instances if needed:

1. **Lead Nurturing: Jane Smith**
   - Workflow: Lead Nurturing Process
   - Status: Active
   - Current Step: "Initial Contact"
   - Business Entity: The Connection Practice
   - Contact: (relation to Jane Smith)
   - Priority: Medium

2. **Art Purchase Fulfillment: Abstract Landscape**
   - Workflow: Art Sale Fulfillment
   - Status: Active
   - Current Step: "Packaging"
   - Business Entity: Art Gallery
   - Priority: High

## Relationships with Other Databases

This database has relationships with:
- Workflows Library (many-to-one)
- Business Entities Registry (many-to-one)
- Contacts & Profiles (many-to-one)
- Master Tasks Database (one-to-many)
- Agent Registry (many-to-one)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Duration Days** (Formula property)
   - Formula: `if(empty(prop("End Date")), dateBetween(prop("Start Date"), now(), "days"), dateBetween(prop("Start Date"), prop("End Date"), "days"))`
   - Output: Number

3. **SLA Status** (Formula property)
   - Formula: `if(prop("Status") = "Completed", "Met", if(prop("Duration Days") > 7, "Overdue", "Within SLA"))`
   - Output: Text
