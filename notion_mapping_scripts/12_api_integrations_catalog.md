# API Integrations Catalog - Notion AI Mapping Script

## Database Overview
The API Integrations Catalog documents all external API integrations used by the system, providing a central repository of API configurations, credentials references, and usage information.

## Required Properties

Create or update the following properties in your API Integrations Catalog database:

1. **Integration Name** (Title property)
   - Description: Name of the API integration
   - Type: Title

2. **Integration ID** (Text property)
   - Description: Unique integration identifier
   - Type: Text
   - Format: "INT-" followed by 8 random alphanumeric characters

3. **Description** (Text property)
   - Description: Detailed description of the integration
   - Type: Rich Text

4. **API Platform** (Select property)
   - Description: Platform or service being integrated
   - Type: Select
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
     - CIRCLE_API
     - BEEHIIV_API
     - CUSTOM_API

5. **Status** (Select property)
   - Description: Current status of the integration
   - Type: Select
   - Options:
     - Active
     - Deprecated
     - Planned
     - Under Test

6. **API Version** (Text property)
   - Description: Version of the API being used
   - Type: Text

7. **Auth Method** (Select property)
   - Description: Authentication method
   - Type: Select
   - Options:
     - API Key
     - OAuth
     - Bearer Token
     - Basic Auth
     - Custom

8. **API Key Reference** (Text property)
   - Description: Secure reference to API credentials (never the actual key)
   - Type: Text

9. **Base URL** (URL property)
   - Description: Base URL for API calls
   - Type: URL

10. **Documentation URL** (URL property)
    - Description: Link to API documentation
    - Type: URL

11. **Business Entities** (Relation property)
    - Description: Business entities using this integration
    - Type: Relation
    - Related to: Business Entities Registry

12. **Agents Using** (Relation property)
    - Description: Agents that use this integration
    - Type: Relation
    - Related to: Agent Registry

13. **Rate Limits** (Text property)
    - Description: API rate limits and quotas
    - Type: Rich Text

14. **Endpoints Used** (Text property)
    - Description: List of endpoints being used
    - Type: Rich Text

15. **Data Mapping** (Relation property)
    - Description: Data transformations for this API
    - Type: Relation
    - Related to: Data Transformations Registry

16. **Implementation Notes** (Text property)
    - Description: Technical notes about implementation
    - Type: Rich Text

17. **Last Tested** (Date property)
    - Description: When the integration was last tested
    - Type: Date
    - Include time: Yes

18. **Owner** (Person property)
    - Description: Person responsible for this integration
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

### 1. New Integration Creation

When a new record is created:
- Generate a unique Integration ID if empty
- Set Status to "Planned" if empty
- Create a task in Master Tasks Database for integration setup
- Notify the Owner about the new integration

### 2. Status Change Actions

When Status changes:
- If changed to "Active", update Last Tested to current date and time
- If changed to "Deprecated", create tasks to update dependent agents
- If changed to "Under Test", create testing tasks

### 3. API Version Management

When API Version is updated:
- Create documentation update task
- Notify agents using this integration
- Schedule a test of the integration

### 4. Usage Tracking

When Agents Using is updated:
- Update a usage count formula
- If integration is used by critical agents, update Tags to include "Core"

### 5. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Integrations** (Default view)
   - Show all API integrations
   - Sort: Status (Active first), then Integration Name (A-Z)

2. **Active Integrations**
   - Filter: Status = "Active"
   - Sort: Integration Name (A-Z)

3. **By API Platform**
   - Group by: API Platform
   - Sort: Integration Name (A-Z)

4. **By Business Entity**
   - Group by: Business Entities
   - Sort: Integration Name (A-Z)

5. **By Agent Usage**
   - Group by: Agents Using
   - Sort: Integration Name (A-Z)

6. **Development Pipeline**
   - Filter: Status = "Planned" OR Status = "Under Test"
   - Sort: API Platform (A-Z)

7. **Documentation View**
   - Properties to show prominently: Integration Name, Description, API Platform, Base URL, Documentation URL, Endpoints Used, Implementation Notes
   - Sort: Integration Name (A-Z)

## Sample Data

Add a few sample API integrations if needed:

1. **Notion API Integration**
   - API Platform: NOTION_API
   - Status: Active
   - API Version: "2021-08-16"
   - Auth Method: Bearer Token
   - API Key Reference: "env:NOTION_API_TOKEN"
   - Base URL: "https://api.notion.com"
   - Business Entities: All business entities
   - Tags: Core

2. **WooCommerce Integration for Art Gallery**
   - API Platform: WOOCOMMERCE_API
   - Status: Active
   - API Version: "v3"
   - Auth Method: OAuth
   - API Key Reference: "env:WOOCOMMERCE_CONSUMER_KEY,WOOCOMMERCE_CONSUMER_SECRET"
   - Base URL: "https://artgallery.example.com/wp-json/wc/v3"
   - Business Entities: Art Gallery
   - Tags: E-commerce

## Relationships with Other Databases

This database has relationships with:
- Business Entities Registry (many-to-many)
- Agent Registry (many-to-many)
- Data Transformations Registry (many-to-many)
- Workflows Library (many-to-many)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Days Since Tested** (Formula property)
   - Formula: `if(empty(prop("Last Tested")), "Never Tested", dateBetween(prop("Last Tested"), now(), "days"))`
   - Output: Number

3. **Usage Count** (Formula property)
   - Formula: `length(prop("Agents Using"))`
   - Output: Number
