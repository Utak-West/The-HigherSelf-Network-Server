# Use Cases Library - Notion AI Mapping Script

## Database Overview
The Use Cases Library documents business scenarios and use cases supported by the system, providing a bridge between business requirements and technical implementation.

## Required Properties

Create or update the following properties in your Use Cases Library database:

1. **Use Case Title** (Title property)
   - Description: Title of the use case
   - Type: Title

2. **Use Case ID** (Text property)
   - Description: Unique use case identifier
   - Type: Text
   - Format: "UC-" followed by 8 random alphanumeric characters

3. **Description** (Text property)
   - Description: Detailed description of the use case
   - Type: Rich Text

4. **Business Value** (Text property)
   - Description: Value this use case provides to the business
   - Type: Rich Text

5. **Implementation Status** (Select property)
   - Description: Current implementation status
   - Type: Select
   - Options:
     - Planned
     - In Development
     - Implemented
     - Live
     - Deprecated
     - On Hold

6. **Business Entities** (Relation property)
   - Description: Business entities this use case applies to
   - Type: Relation
   - Related to: Business Entities Registry

7. **Related Workflows** (Relation property)
   - Description: Workflows that implement this use case
   - Type: Relation
   - Related to: Workflows Library

8. **Required Integrations** (Relation property)
   - Description: API integrations needed for this use case
   - Type: Relation
   - Related to: API Integrations Catalog

9. **User Stories** (Text property)
   - Description: User stories that describe this use case
   - Type: Rich Text

10. **Acceptance Criteria** (Text property)
    - Description: Criteria for successful implementation
    - Type: Rich Text

11. **Priority** (Select property)
    - Description: Business priority
    - Type: Select
    - Options:
      - Critical
      - High
      - Medium
      - Low
      - Nice to Have

12. **Complexity** (Select property)
    - Description: Implementation complexity
    - Type: Select
    - Options:
      - Simple
      - Moderate
      - Complex
      - Very Complex

13. **Estimated Effort** (Select property)
    - Description: Estimated implementation effort
    - Type: Select
    - Options:
      - Small (1-3 days)
      - Medium (1-2 weeks)
      - Large (2-4 weeks)
      - X-Large (1+ months)

14. **Stakeholders** (Person property)
    - Description: Key stakeholders for this use case
    - Type: Person
    - Allow multiple people: Yes

15. **Created Date** (Date property)
    - Description: When the use case was created
    - Type: Date
    - Include time: Yes

16. **Target Implementation Date** (Date property)
    - Description: Target date for implementation
    - Type: Date
    - Include time: No

17. **Actual Implementation Date** (Date property)
    - Description: When the use case was actually implemented
    - Type: Date
    - Include time: No

18. **Tags** (Multi-select property)
    - Description: Categorization tags
    - Type: Multi-select
    - Options:
      - Client Experience
      - Operational Efficiency
      - Revenue Generation
      - Cost Reduction
      - Compliance
      - Reporting
      - Integration
      - Automation

19. **Documentation URL** (URL property)
    - Description: Link to detailed documentation
    - Type: URL

20. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

21. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. New Use Case Creation

When a new record is created:
- Generate a unique Use Case ID if empty
- Set Created Date to current date and time
- Set Implementation Status to "Planned" if empty
- Create a task in Master Tasks Database for use case review

### 2. Status Change Actions

When Implementation Status changes:
- If changed to "In Development", create implementation planning tasks
- If changed to "Implemented", set Actual Implementation Date to current date
- If changed to "Live", notify stakeholders
- If changed to "On Hold", create a task to document the reason

### 3. Workflow Association

When Related Workflows is updated:
- If Implementation Status is "Planned" and workflows are added, suggest changing to "In Development"
- If all required workflows are implemented, suggest changing Implementation Status to "Implemented"

### 4. Priority Management

When Priority changes:
- If changed to "Critical" or "High", update related tasks' priorities
- If Target Implementation Date is empty, suggest setting one based on Priority

### 5. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Use Cases** (Default view)
   - Show all use cases
   - Sort: Implementation Status, then Priority (highest first)

2. **Implementation Roadmap**
   - Filter: Implementation Status = "Planned" OR Implementation Status = "In Development"
   - Sort: Priority (highest first), then Target Implementation Date (soonest first)

3. **By Business Entity**
   - Group by: Business Entities
   - Sort: Implementation Status, then Priority (highest first)

4. **By Status**
   - Group by: Implementation Status
   - Sort: Priority (highest first)

5. **High Priority**
   - Filter: Priority = "Critical" OR Priority = "High"
   - Sort: Implementation Status, then Target Implementation Date (soonest first)

6. **Recently Implemented**
   - Filter: Implementation Status = "Implemented" OR Implementation Status = "Live"
   - Sort: Actual Implementation Date (newest first)

7. **Effort vs. Value Matrix**
   - X-axis: Complexity
   - Y-axis: Priority
   - Color by: Implementation Status

## Sample Data

Add a few sample use cases if needed:

1. **Automated Lead Nurturing**
   - Description: "Automatically follow up with leads based on their interests and engagement"
   - Business Value: "Increase conversion rates and reduce manual follow-up work"
   - Implementation Status: Live
   - Business Entities: The Connection Practice, The 7 Space
   - Priority: High
   - Complexity: Moderate
   - Tags: Automation, Revenue Generation

2. **Integrated Art Purchase and Shipping**
   - Description: "End-to-end process for art purchases including payment processing and shipping coordination"
   - Business Value: "Streamline art sales process and improve customer experience"
   - Implementation Status: In Development
   - Business Entities: Art Gallery
   - Priority: Critical
   - Complexity: Complex
   - Tags: Client Experience, Operational Efficiency

## Relationships with Other Databases

This database has relationships with:
- Business Entities Registry (many-to-many)
- Workflows Library (many-to-many)
- API Integrations Catalog (many-to-many)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Implementation Delay** (Formula property)
   - Formula: `if(empty(prop("Target Implementation Date")) or empty(prop("Actual Implementation Date")), "N/A", dateBetween(prop("Target Implementation Date"), prop("Actual Implementation Date"), "days"))`
   - Output: Number

3. **Workflow Coverage** (Formula property)
   - Formula: `if(empty(prop("Related Workflows")), "0%", format(length(prop("Related Workflows")) / 3 * 100) + "%")`
   - Output: Text
