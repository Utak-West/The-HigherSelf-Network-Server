# Rewards & Bounties - Notion AI Mapping Script

## Database Overview
The Rewards & Bounties database manages incentive programs, loyalty rewards, and community bounties across all business entities, encouraging engagement and participation.

## Required Properties

Create or update the following properties in your Rewards & Bounties database:

1. **Reward Name** (Title property)
   - Description: Name of the reward or bounty
   - Type: Title

2. **Reward ID** (Text property)
   - Description: Unique reward identifier
   - Type: Text
   - Format: "RWD-" followed by 8 random alphanumeric characters

3. **Description** (Text property)
   - Description: Detailed description of the reward
   - Type: Rich Text

4. **Reward Type** (Select property)
   - Description: Type of reward or bounty
   - Type: Select
   - Options:
     - Loyalty Reward
     - Community Bounty
     - Referral Bonus
     - Achievement Badge
     - Discount
     - Free Product/Service
     - Early Access
     - Special Event
     - Cash Reward

5. **Status** (Select property)
   - Description: Current status
   - Type: Select
   - Options:
     - Active
     - Inactive
     - Seasonal
     - Limited Time
     - Expired
     - Draft

6. **Points Value** (Number property)
   - Description: Points required/awarded (if applicable)
   - Type: Number
   - Format: Number

7. **Monetary Value** (Number property)
   - Description: Cash value in USD (if applicable)
   - Type: Number
   - Format: Currency (USD)

8. **Business Entity** (Relation property)
   - Description: Related business entity
   - Type: Relation
   - Related to: Business Entities Registry

9. **Eligibility Criteria** (Rich Text property)
   - Description: Requirements to earn this reward
   - Type: Rich Text

10. **Start Date** (Date property)
    - Description: When the reward becomes available
    - Type: Date
    - Include time: Yes

11. **End Date** (Date property)
    - Description: When the reward expires
    - Type: Date
    - Include time: Yes

12. **Redemption Count** (Number property)
    - Description: How many times this reward has been redeemed
    - Type: Number
    - Format: Number

13. **Maximum Redemptions** (Number property)
    - Description: Maximum number of redemptions allowed
    - Type: Number
    - Format: Number

14. **Related Products** (Relation property)
    - Description: Products or services related to this reward
    - Type: Relation
    - Related to: Products & Services

15. **Target Audience** (Multi-select property)
    - Description: Who this reward is for
    - Type: Multi-select
    - Options:
      - All Clients
      - VIP Clients
      - New Clients
      - Community Members
      - Staff
      - Partners
      - Specific Segment

16. **Redemption Instructions** (Text property)
    - Description: How to redeem the reward
    - Type: Rich Text

17. **Redemption Code** (Text property)
    - Description: Code used for redemption (if applicable)
    - Type: Text

18. **Image** (Files property)
    - Description: Visual representation of the reward
    - Type: Files & Media

19. **Supabase ID** (Text property)
    - Description: ID in Supabase database
    - Type: Text

20. **Last Synced** (Date property)
    - Description: Last synchronization timestamp
    - Type: Date
    - Include time: Yes

## Automation Setup

Add the following automations to this database:

### 1. New Reward Creation

When a new record is created:
- Generate a unique Reward ID if empty
- If Redemption Code is empty and needed, generate a unique code
- Create a task to promote the new reward
- If Status is "Active", add to relevant marketing campaigns

### 2. Status Management

When Status changes:
- If changed to "Active", check Start Date and set to current date if empty
- If changed to "Expired", update any related marketing materials
- If changed to "Limited Time", ensure End Date is set

### 3. Redemption Tracking

When Redemption Count changes:
- If reaches Maximum Redemptions, automatically set Status to "Expired"
- Update any dashboards or reports with new redemption data
- If a high-value reward is redeemed, create notification task

### 4. Date Management

When End Date is reached:
- Automatically set Status to "Expired"
- Create task to evaluate reward effectiveness
- Consider creating a replacement reward

### 5. Sync Trigger

When any field is updated:
- Update the Last Synced field with the current date and time
- Mark the record for synchronization with Supabase

## Views to Create

1. **All Rewards** (Default view)
   - Show all rewards and bounties
   - Sort: Status (Active first), then Start Date (newest first)

2. **Active Rewards**
   - Filter: Status = "Active" OR Status = "Limited Time"
   - Sort: End Date (soonest first)

3. **By Business Entity**
   - Group by: Business Entity
   - Sort: Status (Active first), then Reward Name (A-Z)

4. **By Reward Type**
   - Group by: Reward Type
   - Sort: Status (Active first), then Monetary Value (highest first)

5. **Expiring Soon**
   - Filter: Status = "Active" AND End Date is within the next 30 days
   - Sort: End Date (soonest first)

6. **Performance Analysis**
   - Sort: Redemption Count (highest first)
   - Properties to show prominently: Redemption Count, Maximum Redemptions, Monetary Value

7. **Reward Calendar**
   - Calendar view by: Start Date to End Date
   - Filter: Status != "Expired" AND Status != "Draft"

## Sample Data

Add a few sample rewards if needed:

1. **Refer a Friend Bonus**
   - Reward Type: Referral Bonus
   - Status: Active
   - Points Value: 500
   - Monetary Value: $50.00
   - Business Entity: The Connection Practice
   - Eligibility Criteria: "Existing clients who refer a new client who books a consultation"
   - Target Audience: All Clients

2. **Early Access to New Art Collection**
   - Reward Type: Early Access
   - Status: Limited Time
   - Business Entity: Art Gallery
   - Eligibility Criteria: "VIP clients who have purchased art worth $1000+ in the past year"
   - Target Audience: VIP Clients
   - Start Date: (next month)
   - End Date: (next month + 2 weeks)

## Relationships with Other Databases

This database has relationships with:
- Business Entities Registry (many-to-one)
- Products & Services (many-to-many)
- Community Hub (many-to-many)
- Marketing Campaigns (many-to-many)

## Sync Configuration

Add these formulas to help with synchronization:

1. **Needs Sync** (Formula property)
   - Formula: `prop("Last Modified") > prop("Last Synced")`
   - Output: Checkbox

2. **Redemption Percentage** (Formula property)
   - Formula: `if(empty(prop("Maximum Redemptions")) or prop("Maximum Redemptions") = 0, 0, round(prop("Redemption Count") / prop("Maximum Redemptions") * 100))`
   - Output: Number

3. **Days Remaining** (Formula property)
   - Formula: `if(empty(prop("End Date")), "No End Date", if(dateBetween(now(), prop("End Date"), "days") < 0, "Expired", dateBetween(now(), prop("End Date"), "days")))`
   - Output: Text
