# Marketing Campaigns - Notion AI Mapping Script

## Database Overview
The Marketing Campaigns database tracks all marketing initiatives across business entities, including email campaigns, social media campaigns, events, and other promotional activities.

## Required Properties

Create or update the following properties in your Marketing Campaigns database:

1. **Campaign Name** (Title property)
   - Description: Name of the marketing campaign
   - Type: Title

2. **Campaign ID** (Text property)
   - Description: Unique campaign identifier
   - Type: Text
   - Format: "CAMP-" followed by 8 random alphanumeric characters

3. **Description** (Text property)
   - Description: Detailed campaign description
   - Type: Rich Text

4. **Status** (Select property)
   - Description: Current campaign status
   - Type: Select
   - Options:
     - Draft
     - Scheduled
     - Active
     - Paused
     - Completed
     - Cancelled

5. **Business Entity** (Relation property)
   - Description: Related business entity
   - Type: Relation
   - Related to: Business Entities Registry

6. **Campaign Type** (Select property)
   - Description: Type of marketing campaign
   - Type: Select
   - Options:
     - Email
     - Social Media
     - Event
     - Content
     - Paid Advertising
     - Partnership
     - Promotion
     - PR

7. **Start Date** (Date property)
   - Description: Campaign start date
   - Type: Date
   - Include time: Yes

8. **End Date** (Date property)
   - Description: Campaign end date
   - Type: Date
   - Include time: Yes

9. **Target Audience** (Multi-select property)
   - Description: Target audience segments
   - Type: Multi-select
   - Options:
     - All Clients
     - Active Clients
     - Former Clients
     - Leads
     - Community Members
     - VIP
     - New Subscribers
     - Custom Segment

10. **Channels** (Multi-select property)
    - Description: Marketing channels used
    - Type: Multi-select
    - Options:
      - Email
      - Instagram
      - Facebook
      - Twitter
      - LinkedIn
      - TikTok
      - YouTube
      - Blog
      - Website
      - In-person

11. **Budget** (Number property)
    - Description: Campaign budget
    - Type: Number
    - Format: Currency (USD)

12. **Content Pieces** (Relation property)
    - Description: Related content items
    - Type: Relation
    - Related to: (Content database, if available)

13. **Performance Metrics** (Rich Text property)
    - Description: Campaign metrics in JSON format
    - Type: Rich Text

14. **Goals** (Rich Text property)
    - Description: Campaign goals and KPIs
    - Type: Rich Text

15. **Related Products** (Relation property)
    - Description: Products featured in campaign
    - Type: Relation
    - Related to: Products & Services

16. **Owner** (Person property)
    - Description: Campaign owner
    - Type: Person

17. **Workflow Instance** (Relation property)
    - Description: Related workflow instance
    - Type: Relation
    - Related to: Workflow Instances

18. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

19. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. Campaign Creation

When a new record is created:
- Generate a unique Campaign ID if empty
- Create a workflow instance for campaign execution
- Create initial tasks for campaign planning

### 2. Status Change Actions

When Status changes:
- If changed to "Scheduled", create reminder tasks for launch
- If changed to "Active", update workflow instance status
- If changed to "Completed", trigger performance analysis
- If changed to "Cancelled", cancel all related tasks

### 3. Date Management

When Start Date or End Date changes:
- Update related tasks with new deadlines
- If Start Date is today and Status is "Scheduled", change Status to "Active"
- If End Date is today and Status is "Active", change Status to "Completed"

### 4. Performance Tracking

When Performance Metrics is updated:
- Parse the JSON data to extract key metrics
- If campaign is underperforming, create alert task
- Update dashboard with latest metrics

### 5. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Campaigns** (Default view)
   - Show all campaigns
   - Sort: Start Date (newest first)

2. **Active Campaigns**
   - Filter: Status = "Active" OR Status = "Scheduled"
   - Sort: Start Date (soonest first)

3. **By Business Entity**
   - Group by: Business Entity
   - Sort: Start Date (newest first)

4. **By Campaign Type**
   - Group by: Campaign Type
   - Sort: Start Date (newest first)

5. **Campaign Calendar**
   - Calendar view by: Start Date
   - Filter: Status != "Cancelled" AND Status != "Completed"

6. **Performance Analysis**
   - Filter: Status = "Completed"
   - Sort: End Date (newest first)
   - Properties to show prominently: Performance Metrics, Goals

7. **Campaign Pipeline**
   - Board view by: Status
   - Sort within columns: Start Date (soonest first)

## Sample Data

Add a few sample campaigns if needed:

1. **Spring Wellness Retreat Promotion**
   - Campaign Type: Email
   - Status: Active
   - Business Entity: The 7 Space
   - Target Audience: Active Clients, Leads
   - Channels: Email, Instagram, Facebook
   - Start Date: (current month)
   - End Date: (current month + 2 weeks)

2. **New Art Collection Launch**
   - Campaign Type: Event
   - Status: Scheduled
   - Business Entity: Art Gallery
   - Target Audience: VIP, Community Members
   - Channels: Email, Instagram, In-person
   - Start Date: (next month)
   - End Date: (next month + 1 day)

## Relationships with Other Databases

This database has relationships with:
- Business Entities Registry (many-to-one)
- Products & Services (many-to-many)
- Workflow Instances (one-to-one)
- Contacts & Profiles (many-to-many, via audience segments)
- Community Hub (many-to-many, via audience segments)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Campaign Duration** (Formula property)
   - Formula: `dateBetween(prop("Start Date"), prop("End Date"), "days")`
   - Output: Number

3. **Campaign Status Color** (Formula property)
   - Formula: `if(prop("Status") = "Active", "green", if(prop("Status") = "Scheduled", "blue", if(prop("Status") = "Draft", "gray", if(prop("Status") = "Completed", "purple", "red"))))`
   - Output: Text
