# Data Transformations Registry - Notion AI Mapping Script

## Database Overview
The Data Transformations Registry documents all data transformation rules and mappings used to convert data between different systems and formats, ensuring consistent data handling across integrations.

## Required Properties

Create or update the following properties in your Data Transformations Registry database:

1. **Transformation Name** (Title property)
   - Description: Name of the data transformation
   - Type: Title

2. **Transformation ID** (Text property)
   - Description: Unique transformation identifier
   - Type: Text
   - Format: "TRANSFORM-" followed by 8 random alphanumeric characters

3. **Description** (Text property)
   - Description: Detailed description of the transformation
   - Type: Rich Text

4. **Source Format** (Select property)
   - Description: Original data format
   - Type: Select
   - Options:
     - JSON
     - XML
     - CSV
     - HTML
     - Plain Text
     - Database Record
     - API Response
     - Form Data
     - Custom

5. **Target Format** (Select property)
   - Description: Resulting data format
   - Type: Select
   - Options:
     - JSON
     - XML
     - CSV
     - HTML
     - Plain Text
     - Database Record
     - API Request
     - Notion Page
     - Custom

6. **Transformation Logic** (Text property)
   - Description: Code or logic for the transformation
   - Type: Rich Text

7. **Sample Input** (Text property)
   - Description: Example input data
   - Type: Rich Text

8. **Sample Output** (Text property)
   - Description: Example output data
   - Type: Rich Text

9. **Source System** (Select property)
   - Description: System providing the data
   - Type: Select
   - Options:
     - Notion
     - HubSpot
     - Typeform
     - Airtable
     - WooCommerce
     - Amelia
     - Circle
     - Website
     - Manual Input
     - Custom

10. **Target System** (Select property)
    - Description: System receiving the data
    - Type: Select
    - Options:
      - Notion
      - HubSpot
      - Typeform
      - Airtable
      - WooCommerce
      - Amelia
      - Circle
      - Website
      - Email
      - Custom

11. **Status** (Select property)
    - Description: Current status of the transformation
    - Type: Select
    - Options:
      - Active
      - Deprecated
      - In Development
      - Testing
      - Archived

12. **Version** (Text property)
    - Description: Version of the transformation
    - Type: Text

13. **Business Entities** (Relation property)
    - Description: Business entities using this transformation
    - Type: Relation
    - Related to: Business Entities Registry

14. **Agents Using** (Relation property)
    - Description: Agents that use this transformation
    - Type: Relation
    - Related to: Agent Registry

15. **Related API Integrations** (Relation property)
    - Description: API integrations using this transformation
    - Type: Relation
    - Related to: API Integrations Catalog

16. **Created Date** (Date property)
    - Description: When the transformation was created
    - Type: Date
    - Include time: Yes

17. **Last Updated** (Date property)
    - Description: When the transformation was last updated
    - Type: Date
    - Include time: Yes

18. **Owner** (Person property)
    - Description: Person responsible for this transformation
    - Type: Person

19. **Tags** (Multi-select property)
    - Description: Categorization tags
    - Type: Multi-select
    - Options:
      - Core
      - CRM
      - E-commerce
      - Booking
      - Marketing
      - Content
      - Payment
      - Communication
      - Analytics

20. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

21. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. New Transformation Creation

When a new record is created:
- Generate a unique Transformation ID if empty
- Set Created Date to current date and time
- Set Status to "In Development" if empty
- Create a task in Master Tasks Database for transformation review

### 2. Status Change Actions

When Status changes:
- If changed to "Active", update Last Updated to current date and time
- If changed to "Deprecated", create tasks to update dependent agents
- If changed to "Testing", create test workflow instances

### 3. Version Management

When Version is updated:
- Update Last Updated to current date and time
- Create documentation update task
- Notify agents using this transformation

### 4. Usage Tracking

When Agents Using is updated:
- Update a usage count formula
- If transformation is used by critical agents, update Tags to include "Core"

### 5. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Transformations** (Default view)
   - Show all data transformations
   - Sort: Status (Active first), then Transformation Name (A-Z)

2. **Active Transformations**
   - Filter: Status = "Active"
   - Sort: Transformation Name (A-Z)

3. **By Source System**
   - Group by: Source System
   - Sort: Transformation Name (A-Z)

4. **By Target System**
   - Group by: Target System
   - Sort: Transformation Name (A-Z)

5. **By Business Entity**
   - Group by: Business Entities
   - Sort: Transformation Name (A-Z)

6. **Development Pipeline**
   - Filter: Status = "In Development" OR Status = "Testing"
   - Sort: Last Updated (newest first)

7. **Documentation View**
   - Properties to show prominently: Transformation Name, Description, Source Format, Target Format, Transformation Logic, Sample Input, Sample Output
   - Sort: Transformation Name (A-Z)

## Sample Data

Add a few sample data transformations if needed:

1. **Typeform Lead to Notion Contact**
   - Source Format: JSON
   - Target Format: Database Record
   - Source System: Typeform
   - Target System: Notion
   - Status: Active
   - Description: "Transforms lead data from Typeform submissions into Notion Contact records"
   - Sample Input: (JSON example of Typeform submission)
   - Sample Output: (JSON example of Notion database item)

2. **WooCommerce Order to Workflow Instance**
   - Source Format: API Response
   - Target Format: Database Record
   - Source System: WooCommerce
   - Target System: Notion
   - Status: Active
   - Description: "Converts WooCommerce order data into a workflow instance for order fulfillment"
   - Sample Input: (JSON example of WooCommerce order)
   - Sample Output: (JSON example of workflow instance)

## Relationships with Other Databases

This database has relationships with:
- Business Entities Registry (many-to-many)
- Agent Registry (many-to-many)
- API Integrations Catalog (many-to-many)
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
   - Formula: `length(prop("Agents Using"))`
   - Output: Number
