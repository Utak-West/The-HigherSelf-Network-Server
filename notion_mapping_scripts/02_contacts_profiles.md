# Contacts & Profiles - Notion AI Mapping Script

## Database Overview
The Contacts & Profiles database is a core operational database that stores all contact information across all business entities, including clients, leads, partners, and other stakeholders.

## Required Properties

Create or update the following properties in your Contacts & Profiles database:

1. **Full Name** (Title property)
   - Description: Contact's full name
   - Type: Title

2. **Contact ID** (Text property)
   - Description: Unique contact identifier
   - Type: Text
   - Format: "CTCT-" followed by 8 random alphanumeric characters

3. **Email** (Email property)
   - Description: Email address
   - Type: Email

4. **Phone** (Phone property)
   - Description: Phone number
   - Type: Phone Number

5. **Contact Type** (Select property)
   - Description: Type of contact
   - Type: Select
   - Options:
     - Lead
     - Client
     - Partner
     - Vendor
     - Staff
     - Other

6. **Business Entity** (Relation property)
   - Description: Related business entity
   - Type: Relation
   - Related to: Business Entities Registry

7. **Lead Source** (Select property)
   - Description: How the contact was acquired
   - Type: Select
   - Options:
     - Website
     - Referral
     - Social Media
     - Event
     - Advertisement
     - Direct Contact
     - Other

8. **Status** (Select property)
   - Description: Current status of the contact
   - Type: Select
   - Options:
     - Active Lead
     - Qualified Lead
     - Active Client
     - Former Client
     - Inactive
     - Do Not Contact

9. **Tags** (Multi-select property)
   - Description: Tags for categorization
   - Type: Multi-select
   - Options: (customize based on your needs)
     - VIP
     - Needs Follow-up
     - Potential Upsell
     - New
     - Returning

10. **Date Added** (Date property)
    - Description: When the contact was added
    - Type: Date
    - Include time: Yes

11. **Last Interaction** (Date property)
    - Description: Date of last interaction
    - Type: Date
    - Include time: Yes

12. **Address** (Text property)
    - Description: Physical address
    - Type: Text

13. **City** (Text property)
    - Description: City
    - Type: Text

14. **State/Province** (Text property)
    - Description: State or province
    - Type: Text

15. **Country** (Select property)
    - Description: Country
    - Type: Select
    - Options: (add countries relevant to your business)

16. **Postal Code** (Text property)
    - Description: Postal/ZIP code
    - Type: Text

17. **Company** (Text property)
    - Description: Company name
    - Type: Text

18. **Job Title** (Text property)
    - Description: Job title
    - Type: Text

19. **Notes** (Text property)
    - Description: Additional notes
    - Type: Rich Text

20. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

21. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

22. **External IDs** (Rich Text property)
    - Description: IDs in external systems (JSON format)
    - Type: Rich Text

## Automation Setup

Add the following automations to this database:

### 1. New Lead Processing

When a new record is created:
- Set Date Added to current date and time
- Create a task in Master Tasks Database for lead follow-up
- If Contact Type is "Lead", create a workflow instance in Active Workflow Instances for lead nurturing

### 2. Status Change Workflow

When Status changes:
- If changed to "Qualified Lead", create a task for sales follow-up
- If changed to "Active Client", create onboarding workflow instance
- If changed to "Inactive", update related Community Member record (if exists)

### 3. Sync with Community Hub

When Email is updated:
- Check for matching record in Community Hub
- If found, update the email there as well
- If not found and Status is "Active Client", create a new Community Member record

### 4. External System Sync

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Contacts** (Default view)
   - Show all contacts
   - Sort: Full Name (A-Z)

2. **Active Leads**
   - Filter: Status = "Active Lead" or Status = "Qualified Lead"
   - Sort: Last Interaction (newest first)

3. **Active Clients**
   - Filter: Status = "Active Client"
   - Sort: Last Interaction (newest first)

4. **By Business Entity**
   - Group by: Business Entity
   - Sort: Full Name (A-Z)

5. **Needs Follow-up**
   - Filter: Tags contains "Needs Follow-up"
   - Sort: Last Interaction (oldest first)

6. **Recently Added**
   - Sort: Date Added (newest first)
   - Filter: Date Added is within the last 30 days

## Sample Data

Add a few sample contacts if needed:

1. **Jane Smith**
   - Email: jane.smith@example.com
   - Contact Type: Client
   - Status: Active Client
   - Business Entity: The Connection Practice
   - Lead Source: Website

2. **John Doe**
   - Email: john.doe@example.com
   - Contact Type: Lead
   - Status: Active Lead
   - Business Entity: The 7 Space
   - Lead Source: Social Media

## Relationships with Other Databases

This database has relationships with:
- Business Entities Registry (many-to-one)
- Community Hub (one-to-one)
- Workflow Instances (one-to-many)
- Feedback & Surveys (one-to-many)
- Marketing Campaigns (many-to-many)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Days Since Last Interaction** (Formula property)
   - Formula: `if(empty(prop("Last Interaction")), dateBetween(prop("Date Added"), now(), "days"), dateBetween(prop("Last Interaction"), now(), "days"))`
   - Output: Number
