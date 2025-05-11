# Feedback & Surveys - Notion AI Mapping Script

## Database Overview
The Feedback & Surveys database captures all customer feedback and survey responses, providing insights for business improvement and customer satisfaction tracking.

## Required Properties

Create or update the following properties in your Feedback & Surveys database:

1. **Title** (Title property)
   - Description: Descriptive title of the feedback or survey
   - Type: Title

2. **Feedback ID** (Text property)
   - Description: Unique feedback identifier
   - Type: Text
   - Format: "FDBK-" followed by 8 random alphanumeric characters

3. **Source** (Select property)
   - Description: Source of the feedback
   - Type: Select
   - Options:
     - Typeform
     - Email
     - Website
     - In-person
     - Phone
     - Social Media
     - Review Site
     - Other

4. **Contact** (Relation property)
   - Description: Related contact who provided feedback
   - Type: Relation
   - Related to: Contacts & Profiles

5. **Related Product/Service** (Relation property)
   - Description: Product or service the feedback is about
   - Type: Relation
   - Related to: Products & Services

6. **Related Workflow Instance** (Relation property)
   - Description: Workflow instance related to this feedback
   - Type: Relation
   - Related to: Workflow Instances

7. **Date Received** (Date property)
   - Description: When the feedback was received
   - Type: Date
   - Include time: Yes

8. **Business Entity** (Relation property)
   - Description: Related business entity
   - Type: Relation
   - Related to: Business Entities Registry

9. **Feedback Type** (Select property)
   - Description: Type of feedback
   - Type: Select
   - Options:
     - General Feedback
     - Product Review
     - Service Review
     - Suggestion
     - Complaint
     - Praise
     - Survey Response

10. **Rating** (Number property)
    - Description: Numerical rating (1-5 or 1-10)
    - Type: Number
    - Format: Number

11. **Feedback Content** (Text property)
    - Description: Actual feedback text
    - Type: Rich Text

12. **Sentiment** (Select property)
    - Description: Overall sentiment of feedback
    - Type: Select
    - Options:
      - Positive
      - Neutral
      - Negative
      - Mixed

13. **Status** (Select property)
    - Description: Processing status
    - Type: Select
    - Options:
      - New
      - In Review
      - Responded
      - Resolved
      - Archived

14. **Response** (Text property)
    - Description: Response to the feedback
    - Type: Rich Text

15. **Response Date** (Date property)
    - Description: When the response was sent
    - Type: Date
    - Include time: Yes

16. **Tags** (Multi-select property)
    - Description: Categorization tags
    - Type: Multi-select
    - Options:
      - Product Quality
      - Customer Service
      - Pricing
      - Delivery
      - Website
      - Staff
      - Facilities
      - Experience

17. **Action Items** (Relation property)
    - Description: Tasks created from this feedback
    - Type: Relation
    - Related to: Master Tasks Database

18. **External Reference ID** (Text property)
    - Description: ID in external system (e.g., Typeform)
    - Type: Text

19. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

20. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. New Feedback Processing

When a new record is created:
- Generate a unique Feedback ID if empty
- Set Date Received to current date and time if empty
- Set Status to "New"
- Analyze feedback content to suggest Sentiment and Tags
- Create a task for feedback review if Rating is below 4 or Sentiment is "Negative"

### 2. Status Change Actions

When Status changes:
- If changed to "In Review", assign to appropriate team member
- If changed to "Responded", ensure Response and Response Date are filled
- If changed to "Resolved", check if any Action Items are still open

### 3. Sentiment Analysis

When Feedback Content is updated:
- Use AI to analyze sentiment and suggest Sentiment value
- Extract key themes and suggest Tags
- If Sentiment is "Negative", create alert for immediate attention

### 4. Response Management

When Response is updated:
- Set Response Date to current date and time
- If Status is "New", change to "Responded"
- Create task to follow up if appropriate

### 5. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Feedback** (Default view)
   - Show all feedback entries
   - Sort: Date Received (newest first)

2. **Needs Attention**
   - Filter: Status = "New" OR (Status = "In Review" AND Sentiment = "Negative")
   - Sort: Date Received (oldest first)

3. **By Business Entity**
   - Group by: Business Entity
   - Sort: Date Received (newest first)

4. **By Product/Service**
   - Group by: Related Product/Service
   - Sort: Date Received (newest first)

5. **Sentiment Analysis**
   - Group by: Sentiment
   - Sort: Date Received (newest first)
   - Properties to show prominently: Rating, Tags

6. **Response Tracking**
   - Filter: Status = "New" OR Status = "In Review"
   - Sort: Date Received (oldest first)
   - Properties to show prominently: Status, Sentiment, Rating

7. **Feedback Dashboard**
   - Group by: Feedback Type
   - Sort: Date Received (newest first)
   - Show charts for Rating distribution and Sentiment breakdown

## Sample Data

Add a few sample feedback entries if needed:

1. **Retreat Feedback: Mountain Sanctuary**
   - Source: Typeform
   - Feedback Type: Service Review
   - Rating: 5
   - Sentiment: Positive
   - Business Entity: The 7 Space
   - Related Product/Service: (relation to Mountain Sanctuary retreat)
   - Feedback Content: "The retreat exceeded my expectations. The facilitators were excellent and the location was perfect for relaxation and reflection."
   - Status: Responded

2. **Website Navigation Issue**
   - Source: Website
   - Feedback Type: Suggestion
   - Rating: 3
   - Sentiment: Neutral
   - Business Entity: Art Gallery
   - Feedback Content: "I found it difficult to navigate to the online store from the main page. Consider adding a more prominent link."
   - Status: In Review

## Relationships with Other Databases

This database has relationships with:
- Contacts & Profiles (many-to-one)
- Products & Services (many-to-one)
- Workflow Instances (many-to-one)
- Business Entities Registry (many-to-one)
- Master Tasks Database (one-to-many)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Response Time** (Formula property)
   - Formula: `if(empty(prop("Response Date")), "Not Responded", dateBetween(prop("Date Received"), prop("Response Date"), "hours"))`
   - Output: Text

3. **Days Since Received** (Formula property)
   - Formula: `dateBetween(prop("Date Received"), now(), "days")`
   - Output: Number
