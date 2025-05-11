# Master Tasks Database - Notion AI Mapping Script

## Database Overview
The Master Tasks Database centralizes all actionable tasks across the organization, whether generated from workflows, agents, or manually created by team members.

## Required Properties

Create or update the following properties in your Master Tasks Database:

1. **Task Name** (Title property)
   - Description: Clear, actionable task name
   - Type: Title

2. **Task ID** (Text property)
   - Description: Unique task identifier
   - Type: Text
   - Format: "TASK-" followed by 8 random alphanumeric characters

3. **Status** (Select property)
   - Description: Current task status
   - Type: Select
   - Options:
     - To Do
     - In Progress
     - On Hold
     - Done
     - Cancelled

4. **Description** (Text property)
   - Description: Detailed task description
   - Type: Rich Text

5. **Priority** (Select property)
   - Description: Task priority level
   - Type: Select
   - Options:
     - Low
     - Medium
     - High
     - Urgent

6. **Due Date** (Date property)
   - Description: When the task is due
   - Type: Date
   - Include time: Yes

7. **Assigned To** (Person property)
   - Description: Person responsible for the task
   - Type: Person

8. **Related Workflow Instance** (Relation property)
   - Description: Associated workflow instance
   - Type: Relation
   - Related to: Workflow Instances

9. **Related Business Entity** (Relation property)
   - Description: Related business entity
   - Type: Relation
   - Related to: Business Entities Registry

10. **Created By** (Text property)
    - Description: Who created the task (person or agent)
    - Type: Text

11. **Created Date** (Date property)
    - Description: When the task was created
    - Type: Date
    - Include time: Yes

12. **Last Edited Date** (Date property)
    - Description: When the task was last edited
    - Type: Date
    - Include time: Yes

13. **Completed Date** (Date property)
    - Description: When the task was completed
    - Type: Date
    - Include time: Yes

14. **Tags** (Multi-select property)
    - Description: Categorization tags
    - Type: Multi-select
    - Options:
      - Client-facing
      - Internal
      - Technical
      - Creative
      - Administrative
      - Financial
      - Marketing
      - Urgent
      - Follow-up

15. **Estimated Time** (Number property)
    - Description: Estimated time to complete (minutes)
    - Type: Number
    - Format: Number

16. **Actual Time** (Number property)
    - Description: Actual time spent (minutes)
    - Type: Number
    - Format: Number

17. **Dependencies** (Relation property)
    - Description: Tasks that must be completed first
    - Type: Relation
    - Related to: Master Tasks Database (self-relation)

18. **Subtasks** (Relation property)
    - Description: Child tasks of this task
    - Type: Relation
    - Related to: Master Tasks Database (self-relation)

19. **Notes** (Text property)
    - Description: Additional notes or progress updates
    - Type: Rich Text

20. **Source** (Select property)
    - Description: How the task was created
    - Type: Select
    - Options:
      - Manual
      - Workflow
      - Agent
      - System
      - Integration

21. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

22. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. New Task Creation

When a new record is created:
- Generate a unique Task ID if empty
- Set Created Date to current date and time if empty
- If Source is "Workflow" or "Agent", automatically set appropriate Tags
- Send notification to Assigned To person

### 2. Status Change Actions

When Status changes:
- If changed to "In Progress", update Last Edited Date
- If changed to "Done", set Completed Date to current date and time
- If changed to "Done" and part of a workflow, notify the workflow instance
- If changed to "Cancelled", add a note requesting cancellation reason

### 3. Due Date Management

When Due Date is within 24 hours:
- Send reminder to Assigned To person
- If Priority is not "Urgent" or "High", consider updating it

### 4. Dependency Management

When Dependencies is updated:
- Check if all dependencies are completed
- If yes, notify Assigned To that the task is ready to start
- If no, ensure Status is not "In Progress"

### 5. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Tasks** (Default view)
   - Show all tasks
   - Sort: Due Date (soonest first), then Priority (highest first)

2. **My Tasks**
   - Filter: Assigned To = @CurrentUser AND Status != "Done" AND Status != "Cancelled"
   - Sort: Due Date (soonest first), then Priority (highest first)

3. **By Status**
   - Board view grouped by: Status
   - Sort within columns: Due Date (soonest first), then Priority (highest first)

4. **By Business Entity**
   - Group by: Related Business Entity
   - Filter: Status != "Done" AND Status != "Cancelled"
   - Sort: Due Date (soonest first)

5. **Due Today**
   - Filter: Due Date is today AND Status != "Done" AND Status != "Cancelled"
   - Sort: Priority (highest first)

6. **Overdue**
   - Filter: Due Date is before today AND Status != "Done" AND Status != "Cancelled"
   - Sort: Due Date (oldest first), then Priority (highest first)

7. **Recently Completed**
   - Filter: Status = "Done"
   - Sort: Completed Date (newest first)
   - Limit to last 30 days

8. **Calendar View**
   - Calendar by: Due Date
   - Filter: Status != "Done" AND Status != "Cancelled"
   - Color by: Priority

## Sample Data

Add a few sample tasks if needed:

1. **Follow up with Jane Smith about retreat booking**
   - Status: To Do
   - Priority: Medium
   - Due Date: (tomorrow)
   - Assigned To: (appropriate team member)
   - Related Business Entity: The 7 Space
   - Tags: Client-facing, Follow-up
   - Source: Workflow

2. **Update website with new art collection**
   - Status: In Progress
   - Priority: High
   - Due Date: (this week)
   - Assigned To: (appropriate team member)
   - Related Business Entity: Art Gallery
   - Tags: Marketing, Creative
   - Source: Manual

## Relationships with Other Databases

This database has relationships with:
- Workflow Instances (many-to-one)
- Business Entities Registry (many-to-one)
- Master Tasks Database (self-relation for dependencies and subtasks)
- Feedback & Surveys (many-to-one)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Days Until Due** (Formula property)
   - Formula: `if(empty(prop("Due Date")), "No Due Date", if(dateBetween(now(), prop("Due Date"), "days") < 0, "Overdue", dateBetween(now(), prop("Due Date"), "days")))`
   - Output: Text

3. **Completion Time** (Formula property)
   - Formula: `if(prop("Status") = "Done", dateBetween(prop("Created Date"), prop("Completed Date"), "hours"), "Not Completed")`
   - Output: Text
