# Business Entities Registry - Notion AI Mapping Script

## Database Overview
The Business Entities Registry is a core operational database that tracks all business entities in The HigherSelf Network, including The Connection Practice and The 7 Space.

## Required Properties

Create or update the following properties in your Business Entities Registry database:

1. **Name** (Title property)
   - Description: Business entity name
   - Type: Title

2. **Entity Type** (Select property)
   - Description: Type of business entity
   - Type: Select
   - Options:
     - CONSULTING_FIRM
     - ART_GALLERY
     - WELLNESS_CENTER

3. **API Keys Reference** (Text property)
   - Description: Secure reference to API credentials
   - Type: Text

4. **Primary Workflows** (Relation property)
   - Description: Workflows associated with this entity
   - Type: Relation
   - Related to: Workflows Library

5. **Active Agents** (Relation property)
   - Description: Agents active for this entity
   - Type: Relation
   - Related to: Agent Registry

6. **Integration Status** (Select property)
   - Description: Current integration status
   - Type: Select
   - Options:
     - Active
     - Inactive
     - Pending
     - Error

7. **Supabase ID** (Text property)
   - Description: ID in Supabase database
   - Type: Text

8. **Last Synced** (Date property)
   - Description: Last synchronization timestamp
   - Type: Date
   - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. New Entity Registration

When a new record is created:
- Create a related record in the Workflows Library for default workflows
- Create a related record in the Agent Registry for default agents
- Add a task in the Master Tasks Database to complete entity setup
- Set the Integration Status to "Pending"

### 2. Status Change Notification

When Integration Status changes to "Error":
- Send a notification to the technical team
- Create a task in the Master Tasks Database to investigate

### 3. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Entities** (Default view)
   - Show all entities
   - Group by Entity Type

2. **Active Entities**
   - Filter: Integration Status = "Active"
   - Sort: Name (A-Z)

3. **By Business Type**
   - Group by: Entity Type
   - Sort: Name (A-Z)

4. **Integration Issues**
   - Filter: Integration Status = "Error" or Integration Status = "Pending"
   - Sort: Last Synced (newest first)

## Sample Data

Add these sample entities if they don't already exist:

1. **The Connection Practice**
   - Entity Type: CONSULTING_FIRM
   - Integration Status: Active
   - API Keys Reference: "secure/connection-practice/api-keys"

2. **The 7 Space**
   - Entity Type: WELLNESS_CENTER
   - Integration Status: Active
   - API Keys Reference: "secure/7-space/api-keys"

3. **Art Gallery**
   - Entity Type: ART_GALLERY
   - Integration Status: Active
   - API Keys Reference: "secure/art-gallery/api-keys"

## Relationships with Other Databases

This database has relationships with:
- Contacts & Profiles (one-to-many)
- Products & Services (one-to-many)
- Workflow Instances (one-to-many)
- Agent Registry (many-to-many)
- Workflows Library (many-to-many)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Days Since Sync** (Formula property)
   - Formula: `dateBetween(prop("Last Synced"), now(), "days")`
   - Output: Number
