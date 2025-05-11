# Products & Services - Notion AI Mapping Script

## Database Overview
The Products & Services database is a catalog of all offerings across all business entities, including physical products, services, courses, retreats, and art pieces.

## Required Properties

Create or update the following properties in your Products & Services database:

1. **Name** (Title property)
   - Description: Product or service name
   - Type: Title

2. **Product ID** (Text property)
   - Description: Unique product identifier
   - Type: Text
   - Format: "PROD-" followed by 8 random alphanumeric characters

3. **Type** (Select property)
   - Description: Type of offering
   - Type: Select
   - Options:
     - Course
     - Retreat
     - Workshop
     - Consultation
     - Art Piece
     - Digital Product
     - Physical Product
     - Membership
     - Service

4. **Description** (Text property)
   - Description: Detailed description
   - Type: Rich Text

5. **Price** (Number property)
   - Description: Price in USD
   - Type: Number
   - Format: Currency (USD)

6. **Status** (Select property)
   - Description: Current status
   - Type: Select
   - Options:
     - Active
     - Inactive
     - Coming Soon
     - Discontinued
     - Seasonal

7. **Inventory Count** (Number property)
   - Description: Current inventory (for physical products)
   - Type: Number
   - Format: Number

8. **Business Entity** (Relation property)
   - Description: Related business entity
   - Type: Relation
   - Related to: Business Entities Registry

9. **Integration System** (Select property)
   - Description: External system integration
   - Type: Select
   - Options:
     - WooCommerce
     - Amelia
     - Acuity
     - Shopify
     - Manual
     - None

10. **External ID** (Text property)
    - Description: ID in external system
    - Type: Text

11. **Images** (Files property)
    - Description: Product images
    - Type: Files & Media

12. **Booking Link** (URL property)
    - Description: Direct link to book/purchase
    - Type: URL

13. **Duration Minutes** (Number property)
    - Description: Duration in minutes (for services)
    - Type: Number
    - Format: Number

14. **Categories** (Multi-select property)
    - Description: Product categories
    - Type: Multi-select
    - Options: (customize based on your offerings)
      - Wellness
      - Art
      - Education
      - Consulting
      - Digital
      - Physical

15. **Tags** (Multi-select property)
    - Description: Tags for filtering
    - Type: Multi-select
    - Options: (customize based on your needs)
      - Featured
      - Bestseller
      - New
      - Sale
      - Limited Edition

16. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

17. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. New Product Creation

When a new record is created:
- Generate a unique Product ID if empty
- Create a task in Master Tasks Database for product setup
- If Integration System is not "None", create a workflow instance for system integration

### 2. Inventory Management

When Inventory Count changes:
- If drops below 5 and Status is "Active", create a restock task
- If changes to 0, set Status to "Out of Stock"
- If changes from 0 to a positive number, set Status to "Active"

### 3. Status Change Actions

When Status changes:
- If changed to "Active", check if it should be featured in Marketing Campaigns
- If changed to "Discontinued", update any related workflow instances
- If changed to "Coming Soon", create marketing preparation tasks

### 4. External System Sync

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase
- If Integration System is set, trigger sync with that external system

## Views to Create

1. **All Products & Services** (Default view)
   - Show all offerings
   - Sort: Name (A-Z)

2. **Active Offerings**
   - Filter: Status = "Active"
   - Sort: Name (A-Z)

3. **By Business Entity**
   - Group by: Business Entity
   - Sort: Name (A-Z)

4. **By Type**
   - Group by: Type
   - Sort: Name (A-Z)

5. **Inventory Management**
   - Filter: Type = "Physical Product" OR Type = "Art Piece"
   - Sort: Inventory Count (lowest first)
   - Properties to show prominently: Inventory Count, Status

6. **Services Calendar**
   - Filter: Type = "Service" OR Type = "Consultation" OR Type = "Workshop" OR Type = "Retreat"
   - Calendar view by: (relevant date field)

## Sample Data

Add a few sample products if needed:

1. **Wellness Retreat: Mountain Sanctuary**
   - Type: Retreat
   - Price: $1,200.00
   - Status: Active
   - Business Entity: The 7 Space
   - Duration Minutes: 4320 (3 days)
   - Categories: Wellness
   - Tags: Featured

2. **Abstract Landscape Painting**
   - Type: Art Piece
   - Price: $450.00
   - Status: Active
   - Inventory Count: 1
   - Business Entity: Art Gallery
   - Categories: Art
   - Tags: Limited Edition

3. **Business Strategy Consultation**
   - Type: Consultation
   - Price: $200.00
   - Status: Active
   - Business Entity: The Connection Practice
   - Duration Minutes: 60
   - Categories: Consulting
   - Tags: Bestseller

## Relationships with Other Databases

This database has relationships with:
- Business Entities Registry (many-to-one)
- Workflow Instances (one-to-many)
- Feedback & Surveys (one-to-many)
- Marketing Campaigns (many-to-many)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Price Tier** (Formula property)
   - Formula: `if(prop("Price") < 100, "Budget", if(prop("Price") < 500, "Standard", "Premium"))`
   - Output: Text

3. **Is Physical** (Formula property)
   - Formula: `contains(prop("Type"), "Physical Product") or contains(prop("Type"), "Art Piece")`
   - Output: Checkbox
