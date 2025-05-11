# Notifications Templates - Notion AI Mapping Script

## Database Overview
The Notifications Templates database stores templates for all automated notifications sent by the system, ensuring consistent messaging across different channels and business entities.

## Required Properties

Create or update the following properties in your Notifications Templates database:

1. **Template Name** (Title property)
   - Description: Name of the notification template
   - Type: Title

2. **Template ID** (Text property)
   - Description: Unique template identifier
   - Type: Text
   - Format: "NOTIF-" followed by 8 random alphanumeric characters

3. **Description** (Text property)
   - Description: Purpose and usage of the template
   - Type: Rich Text

4. **Channel** (Select property)
   - Description: Notification delivery channel
   - Type: Select
   - Options:
     - Email
     - SMS
     - Slack
     - Push Notification
     - In-App
     - WhatsApp
     - Discord
     - Custom

5. **Content Template** (Text property)
   - Description: The actual template content with placeholders
   - Type: Rich Text

6. **Subject Template** (Text property)
   - Description: Subject line template (for email)
   - Type: Text

7. **Supported Placeholders** (Text property)
   - Description: List of placeholders that can be used in this template
   - Type: Rich Text

8. **Business Entities** (Relation property)
   - Description: Business entities using this template
   - Type: Relation
   - Related to: Business Entities Registry

9. **Trigger Event** (Select property)
   - Description: Event that triggers this notification
   - Type: Select
   - Options:
     - New Lead
     - Booking Confirmation
     - Booking Reminder
     - Order Confirmation
     - Shipping Update
     - Payment Received
     - Task Assignment
     - Workflow Update
     - Survey Request
     - Custom Event

10. **Status** (Select property)
    - Description: Current status of the template
    - Type: Select
    - Options:
      - Active
      - Inactive
      - Draft
      - Testing
      - Archived

11. **Version** (Text property)
    - Description: Version of the template
    - Type: Text

12. **Created By** (Person property)
    - Description: Person who created the template
    - Type: Person

13. **Created Date** (Date property)
    - Description: When the template was created
    - Type: Date
    - Include time: Yes

14. **Last Updated** (Date property)
    - Description: When the template was last updated
    - Type: Date
    - Include time: Yes

15. **Last Sent** (Date property)
    - Description: When the template was last used
    - Type: Date
    - Include time: Yes

16. **Send Count** (Number property)
    - Description: How many times this template has been used
    - Type: Number
    - Format: Number

17. **Related Workflows** (Relation property)
    - Description: Workflows that use this template
    - Type: Relation
    - Related to: Workflows Library

18. **Sample Rendered Output** (Text property)
    - Description: Example of the template with placeholders filled
    - Type: Rich Text

19. **Tags** (Multi-select property)
    - Description: Categorization tags
    - Type: Multi-select
    - Options:
      - Transactional
      - Marketing
      - Reminder
      - Alert
      - Confirmation
      - Welcome
      - Follow-up
      - Feedback

20. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

21. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. New Template Creation

When a new record is created:
- Generate a unique Template ID if empty
- Set Created Date to current date and time
- Set Status to "Draft" if empty
- Create a task in Master Tasks Database for template review

### 2. Status Change Actions

When Status changes:
- If changed to "Active", update Last Updated to current date and time
- If changed to "Testing", create test notification tasks
- If changed to "Archived", check if any workflows still use this template

### 3. Version Management

When Version is updated:
- Update Last Updated to current date and time
- Create a task to update Sample Rendered Output
- Notify relevant stakeholders about the template update

### 4. Usage Tracking

When Send Count changes:
- Update analytics dashboards
- If Send Count reaches significant milestones (100, 1000, etc.), create a review task

### 5. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Templates** (Default view)
   - Show all notification templates
   - Sort: Status (Active first), then Template Name (A-Z)

2. **Active Templates**
   - Filter: Status = "Active"
   - Sort: Template Name (A-Z)

3. **By Channel**
   - Group by: Channel
   - Sort: Template Name (A-Z)

4. **By Business Entity**
   - Group by: Business Entities
   - Sort: Template Name (A-Z)

5. **By Trigger Event**
   - Group by: Trigger Event
   - Sort: Template Name (A-Z)

6. **Development Pipeline**
   - Filter: Status = "Draft" OR Status = "Testing"
   - Sort: Last Updated (newest first)

7. **Usage Analytics**
   - Sort: Send Count (highest first)
   - Properties to show prominently: Send Count, Last Sent, Channel

## Sample Data

Add a few sample notification templates if needed:

1. **Booking Confirmation Email**
   - Channel: Email
   - Trigger Event: Booking Confirmation
   - Status: Active
   - Subject Template: "Your {{service_name}} booking is confirmed!"
   - Content Template: "Hello {{client_name}},\n\nYour booking for {{service_name}} on {{booking_date}} at {{booking_time}} has been confirmed.\n\nWe look forward to seeing you!\n\nBest regards,\n{{business_name}} Team"
   - Business Entities: The 7 Space, Art Gallery
   - Tags: Confirmation, Transactional

2. **New Lead Notification**
   - Channel: Slack
   - Trigger Event: New Lead
   - Status: Active
   - Content Template: "New lead received!\nName: {{lead_name}}\nEmail: {{lead_email}}\nInterest: {{lead_interest}}\nSource: {{lead_source}}"
   - Business Entities: The Connection Practice
   - Tags: Alert

## Relationships with Other Databases

This database has relationships with:
- Business Entities Registry (many-to-many)
- Workflows Library (many-to-many)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Days Since Updated** (Formula property)
   - Formula: `dateBetween(prop("Last Updated"), now(), "days")`
   - Output: Number

3. **Days Since Last Sent** (Formula property)
   - Formula: `if(empty(prop("Last Sent")), "Never Sent", dateBetween(prop("Last Sent"), now(), "days"))`
   - Output: Text
