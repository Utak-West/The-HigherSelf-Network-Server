# Community Hub - Notion AI Mapping Script

## Database Overview
The Community Hub database tracks community members and their engagement across various platforms, serving as a central repository for community management.

## Required Properties

Create or update the following properties in your Community Hub database:

1. **Member Name** (Title property)
   - Description: Member's name
   - Type: Title

2. **Member ID** (Text property)
   - Description: Unique member identifier
   - Type: Text
   - Format: "MEMBER-" followed by 8 random alphanumeric characters

3. **Contact Profile** (Relation property)
   - Description: Related contact profile
   - Type: Relation
   - Related to: Contacts & Profiles

4. **Member Email** (Email property)
   - Description: Member's email address
   - Type: Email

5. **Join Date** (Date property)
   - Description: When the member joined
   - Type: Date
   - Include time: Yes

6. **Membership Level** (Select property)
   - Description: Level of membership
   - Type: Select
   - Options:
     - Standard
     - Premium
     - VIP
     - Founding Member
     - Trial

7. **Membership Status** (Select property)
   - Description: Current status
   - Type: Select
   - Options:
     - Active
     - Inactive
     - Pending
     - Expired
     - Suspended

8. **Primary Platform** (Select property)
   - Description: Main community platform
   - Type: Select
   - Options:
     - Circle.so
     - Discord
     - Slack
     - Facebook Group
     - Other

9. **Platform IDs** (Rich Text property)
   - Description: IDs on various platforms (JSON format)
   - Type: Rich Text

10. **Engagement Score** (Number property)
    - Description: Numeric score of engagement level
    - Type: Number
    - Format: 0-100

11. **Last Active Date** (Date property)
    - Description: Last activity date
    - Type: Date
    - Include time: Yes

12. **Interests** (Multi-select property)
    - Description: Member's interests
    - Type: Multi-select
    - Options: (customize based on your community)
      - Art
      - Wellness
      - Consulting
      - Spirituality
      - Business
      - Technology

13. **Badges** (Multi-select property)
    - Description: Earned badges/achievements
    - Type: Multi-select
    - Options:
      - Early Adopter
      - Content Creator
      - Event Participant
      - Mentor
      - Regular Contributor

14. **Business Entity** (Relation property)
    - Description: Related business entity
    - Type: Relation
    - Related to: Business Entities Registry

15. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

16. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. New Member Onboarding

When a new record is created:
- Set Join Date to current date and time if empty
- Create a task in Master Tasks Database for member welcome
- Create a workflow instance in Active Workflow Instances for member onboarding

### 2. Engagement Tracking

When Last Active Date is updated:
- Calculate and update Engagement Score based on activity frequency
- If Last Active Date is more than 30 days ago and Membership Status is "Active", create a re-engagement task

### 3. Status Change Actions

When Membership Status changes:
- If changed to "Inactive" or "Expired", update related Contact Profile status
- If changed to "Active" from another status, create a welcome back task

### 4. Platform Integration

When Platform IDs is updated:
- Parse the JSON to extract platform-specific IDs
- Update external systems via API integrations

### 5. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Members** (Default view)
   - Show all members
   - Sort: Member Name (A-Z)

2. **Active Members**
   - Filter: Membership Status = "Active"
   - Sort: Last Active Date (newest first)

3. **By Membership Level**
   - Group by: Membership Level
   - Sort: Member Name (A-Z)

4. **Engagement Dashboard**
   - Filter: Membership Status = "Active"
   - Sort: Engagement Score (highest first)
   - Properties to show prominently: Engagement Score, Last Active Date, Badges

5. **Recently Joined**
   - Sort: Join Date (newest first)
   - Filter: Join Date is within the last 30 days

6. **Needs Attention**
   - Filter: (Membership Status = "Active" AND Last Active Date is before 30 days ago) OR Membership Status = "Expired"
   - Sort: Last Active Date (oldest first)

## Sample Data

Add a few sample community members if needed:

1. **Sarah Johnson**
   - Member Email: sarah.j@example.com
   - Membership Level: Premium
   - Membership Status: Active
   - Primary Platform: Circle.so
   - Interests: Wellness, Spirituality
   - Business Entity: The 7 Space

2. **Michael Chen**
   - Member Email: m.chen@example.com
   - Membership Level: Standard
   - Membership Status: Active
   - Primary Platform: Discord
   - Interests: Art, Technology
   - Business Entity: Art Gallery

## Relationships with Other Databases

This database has relationships with:
- Contacts & Profiles (one-to-one)
- Business Entities Registry (many-to-one)
- Marketing Campaigns (many-to-many)
- Rewards & Bounties (many-to-many)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Days Since Active** (Formula property)
   - Formula: `dateBetween(prop("Last Active Date"), now(), "days")`
   - Output: Number

3. **Membership Age** (Formula property)
   - Formula: `dateBetween(prop("Join Date"), now(), "days")`
   - Output: Number
