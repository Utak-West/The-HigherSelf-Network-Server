# Zapier Integration Guide - The HigherSelf Network Server

## Overview

This guide provides comprehensive setup instructions for integrating Zapier with The HigherSelf Network Server across all three business entities. Zapier will automate workflows between your applications and the HigherSelf platform.

## Prerequisites

- Active Zapier account (Pro plan recommended for multi-step Zaps)
- HigherSelf Network Server deployed and running
- Notion API access configured
- Business entity databases set up

## Integration Architecture

### Webhook Endpoints

| Business Entity | Webhook URL | Purpose |
|-----------------|-------------|---------|
| **The 7 Space** | `http://YOUR_VM_IP/api/webhooks/zapier/the7space` | Gallery & wellness automation |
| **AM Consulting** | `http://YOUR_VM_IP/api/webhooks/zapier/amconsulting` | Business consulting workflows |
| **HigherSelf Core** | `http://YOUR_VM_IP/api/webhooks/zapier/higherself` | Community platform automation |
| **Universal** | `http://YOUR_VM_IP/api/webhooks/zapier/universal` | Cross-entity workflows |

### Authentication

All Zapier webhooks use API key authentication:
- **Header**: `Authorization: Bearer YOUR_API_KEY`
- **API Key**: Found in your HigherSelf admin panel under Integrations > API Keys

## The 7 Space Zapier Automations

### 1. Contact Form Submission → Notion → Workflow Automation

**Trigger**: New form submission from The 7 Space website
**Actions**: Create Notion contact → Trigger workflow automation

#### Setup Steps:

1. **Create New Zap**
   - Trigger: Webhook by Zapier
   - Event: Catch Hook
   - Webhook URL: `http://YOUR_VM_IP/api/webhooks/zapier/the7space/contact-form`

2. **Add Notion Action**
   - App: Notion
   - Action: Create Database Item
   - Database: The 7 Space Contacts Database
   - Properties mapping:
     ```json
     {
       "Name": "{{name}}",
       "Email": "{{email}}",
       "Phone": "{{phone}}",
       "Interest": "{{interest}}",
       "Lead Source": "Website Contact Form",
       "Contact Type": "Gallery Visitor",
       "Created Date": "{{current_date}}",
       "Lead Score": 50
     }
     ```

3. **Add HigherSelf Workflow Trigger**
   - App: Webhooks by Zapier
   - Action: POST
   - URL: `http://YOUR_VM_IP/api/workflows/trigger`
   - Headers:
     ```json
     {
       "Authorization": "Bearer YOUR_API_KEY",
       "Content-Type": "application/json"
     }
     ```
   - Data:
     ```json
     {
       "business_entity": "the_7_space",
       "contact_id": "{{notion_page_id}}",
       "contact_email": "{{email}}",
       "contact_type": "gallery_visitor",
       "lead_source": "website_contact",
       "trigger_event": "contact_created",
       "metadata": {
         "form_source": "website",
         "interest": "{{interest}}"
       }
     }
     ```

### 2. Event Registration → Calendar Booking → Email Sequence

**Trigger**: New event registration
**Actions**: Create calendar booking → Send confirmation → Start follow-up sequence

#### Setup Steps:

1. **Create New Zap**
   - Trigger: Webhook by Zapier
   - Event: Catch Hook
   - Webhook URL: `http://YOUR_VM_IP/api/webhooks/zapier/the7space/event-registration`

2. **Add Google Calendar Action**
   - App: Google Calendar
   - Action: Create Detailed Event
   - Calendar: The 7 Space Events
   - Event Details:
     ```
     Title: {{event_name}} - {{attendee_name}}
     Start Date: {{event_date}}
     End Date: {{event_end_date}}
     Description: Event registration for {{attendee_name}} ({{attendee_email}})
     Attendees: {{attendee_email}}
     ```

3. **Add Email Confirmation**
   - App: Email by Zapier
   - Action: Send Outbound Email
   - To: `{{attendee_email}}`
   - Subject: `Your registration for {{event_name}} is confirmed!`
   - Body: Use The 7 Space event confirmation template

4. **Add Follow-up Workflow**
   - App: Webhooks by Zapier
   - Action: POST
   - URL: `http://YOUR_VM_IP/api/workflows/trigger`
   - Data:
     ```json
     {
       "business_entity": "the_7_space",
       "contact_email": "{{attendee_email}}",
       "contact_type": "event_attendee",
       "trigger_event": "event_registered",
       "workflow_name": "the7space_event_followup",
       "metadata": {
         "event_name": "{{event_name}}",
         "event_date": "{{event_date}}",
         "calendar_event_id": "{{calendar_event_id}}"
       }
     }
     ```

### 3. Artist Portfolio Submission → Curator Review → Exhibition Planning

**Trigger**: Artist portfolio submission
**Actions**: Create curator task → Send acknowledgment → Start review workflow

#### Setup Steps:

1. **Create New Zap**
   - Trigger: Webhook by Zapier
   - Event: Catch Hook
   - Webhook URL: `http://YOUR_VM_IP/api/webhooks/zapier/the7space/artist-portfolio`

2. **Add Notion Task Creation**
   - App: Notion
   - Action: Create Database Item
   - Database: The 7 Space Tasks Database
   - Properties:
     ```json
     {
       "Task Name": "Portfolio Review: {{artist_name}}",
       "Assignee": "Curator",
       "Priority": "High",
       "Status": "To Do",
       "Due Date": "{{date_plus_3_days}}",
       "Description": "Review portfolio submission from {{artist_name}}. Portfolio link: {{portfolio_url}}",
       "Contact": "{{artist_email}}",
       "Business Entity": "The 7 Space"
     }
     ```

3. **Add Artist Acknowledgment Email**
   - App: Email by Zapier
   - Action: Send Outbound Email
   - To: `{{artist_email}}`
   - Subject: `Portfolio received - The 7 Space`
   - Body: Artist acknowledgment template

4. **Add Review Workflow Trigger**
   - App: Webhooks by Zapier
   - Action: POST
   - URL: `http://YOUR_VM_IP/api/workflows/trigger`
   - Data:
     ```json
     {
       "business_entity": "the_7_space",
       "contact_email": "{{artist_email}}",
       "contact_type": "artist",
       "trigger_event": "portfolio_submitted",
       "workflow_name": "the7space_artist_onboarding",
       "metadata": {
         "portfolio_url": "{{portfolio_url}}",
         "artist_medium": "{{medium}}",
         "task_id": "{{notion_task_id}}"
       }
     }
     ```

## AM Consulting Zapier Automations

### 1. Lead Capture → Qualification → CRM Integration

**Trigger**: New lead from website or referral
**Actions**: Score lead → Create CRM record → Assign to consultant

#### Setup Steps:

1. **Create New Zap**
   - Trigger: Webhook by Zapier
   - Event: Catch Hook
   - Webhook URL: `http://YOUR_VM_IP/api/webhooks/zapier/amconsulting/lead-capture`

2. **Add Lead Scoring**
   - App: Webhooks by Zapier
   - Action: POST
   - URL: `http://YOUR_VM_IP/api/leads/score`
   - Data:
     ```json
     {
       "business_entity": "am_consulting",
       "contact_data": {
         "email": "{{email}}",
         "company": "{{company}}",
         "industry": "{{industry}}",
         "company_size": "{{company_size}}",
         "budget": "{{budget}}",
         "timeline": "{{timeline}}",
         "lead_source": "{{lead_source}}"
       }
     }
     ```

3. **Add Notion Contact Creation**
   - App: Notion
   - Action: Create Database Item
   - Database: AM Consulting Contacts Database
   - Properties:
     ```json
     {
       "Name": "{{name}}",
       "Email": "{{email}}",
       "Company": "{{company}}",
       "Industry": "{{industry}}",
       "Lead Score": "{{calculated_score}}",
       "Lead Source": "{{lead_source}}",
       "Status": "New Lead",
       "Assigned Consultant": "{{assigned_consultant}}",
       "Created Date": "{{current_date}}"
     }
     ```

4. **Add CRM Integration (GoHighLevel)**
   - App: Webhooks by Zapier
   - Action: POST
   - URL: GoHighLevel API endpoint
   - Headers: GoHighLevel API authentication
   - Data: Contact information for CRM

### 2. Client Onboarding → Project Setup → Milestone Tracking

**Trigger**: New client signed contract
**Actions**: Create project → Set milestones → Send welcome package

#### Setup Steps:

1. **Create New Zap**
   - Trigger: Webhook by Zapier
   - Event: Catch Hook
   - Webhook URL: `http://YOUR_VM_IP/api/webhooks/zapier/amconsulting/client-onboarding`

2. **Add Project Creation**
   - App: Notion
   - Action: Create Database Item
   - Database: AM Consulting Projects Database
   - Properties:
     ```json
     {
       "Project Name": "{{project_name}}",
       "Client": "{{client_name}}",
       "Start Date": "{{start_date}}",
       "End Date": "{{end_date}}",
       "Budget": "{{budget}}",
       "Status": "Active",
       "Consultant": "{{assigned_consultant}}",
       "Project Type": "{{project_type}}"
     }
     ```

3. **Add Milestone Creation**
   - App: Multiple Notion actions for each milestone
   - Create milestone tasks with due dates and dependencies

4. **Add Welcome Email Sequence**
   - App: Webhooks by Zapier
   - Action: POST
   - URL: `http://YOUR_VM_IP/api/workflows/trigger`
   - Data:
     ```json
     {
       "business_entity": "am_consulting",
       "contact_email": "{{client_email}}",
       "contact_type": "client",
       "trigger_event": "client_onboarded",
       "workflow_name": "amconsulting_client_onboarding",
       "metadata": {
         "project_id": "{{project_id}}",
         "consultant": "{{assigned_consultant}}",
         "project_type": "{{project_type}}"
       }
     }
     ```

## HigherSelf Core Zapier Automations

### 1. Community Registration → Welcome Sequence → Engagement Tracking

**Trigger**: New community member registration
**Actions**: Create member profile → Send welcome series → Track engagement

#### Setup Steps:

1. **Create New Zap**
   - Trigger: Webhook by Zapier
   - Event: Catch Hook
   - Webhook URL: `http://YOUR_VM_IP/api/webhooks/zapier/higherself/member-registration`

2. **Add Member Profile Creation**
   - App: Notion
   - Action: Create Database Item
   - Database: HigherSelf Members Database
   - Properties:
     ```json
     {
       "Name": "{{name}}",
       "Email": "{{email}}",
       "Join Date": "{{current_date}}",
       "Member Type": "{{member_type}}",
       "Interests": "{{interests}}",
       "Status": "Active",
       "Engagement Score": 0,
       "Last Activity": "{{current_date}}"
     }
     ```

3. **Add Welcome Workflow**
   - App: Webhooks by Zapier
   - Action: POST
   - URL: `http://YOUR_VM_IP/api/workflows/trigger`
   - Data:
     ```json
     {
       "business_entity": "higherself_core",
       "contact_email": "{{email}}",
       "contact_type": "community_member",
       "trigger_event": "member_registered",
       "workflow_name": "higherself_member_onboarding",
       "metadata": {
         "member_type": "{{member_type}}",
         "interests": "{{interests}}",
         "referral_source": "{{referral_source}}"
       }
     }
     ```

## Error Handling and Monitoring

### 1. Error Handling in Zaps

Add error handling to each Zap:

```javascript
// Error handling filter
if (inputData.error) {
  // Send error notification
  return {
    error: true,
    message: inputData.error,
    timestamp: new Date().toISOString()
  };
}
```

### 2. Monitoring Webhook

Create a monitoring Zap:

1. **Trigger**: Schedule by Zapier (every 15 minutes)
2. **Action**: Check webhook health
   - URL: `http://YOUR_VM_IP/api/webhooks/health`
   - If unhealthy, send alert email

### 3. Retry Logic

Configure retry settings in Zapier:
- Enable automatic retries
- Set retry delay: 2 minutes
- Maximum retries: 3

## Testing Procedures

### 1. Test Each Integration

```bash
# Test The 7 Space contact form
curl -X POST http://YOUR_VM_IP/api/webhooks/zapier/the7space/contact-form \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "phone": "555-1234",
    "interest": "Gallery Visit"
  }'

# Test AM Consulting lead capture
curl -X POST http://YOUR_VM_IP/api/webhooks/zapier/amconsulting/lead-capture \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "email": "test@company.com",
    "company": "Test Corp",
    "industry": "Technology",
    "budget": "50000"
  }'

# Test HigherSelf member registration
curl -X POST http://YOUR_VM_IP/api/webhooks/zapier/higherself/member-registration \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Member",
    "email": "member@example.com",
    "member_type": "Premium",
    "interests": ["Personal Development", "Community"]
  }'
```

### 2. Validate Data Flow

1. Check Notion databases for new records
2. Verify workflow triggers in HigherSelf admin panel
3. Confirm email deliveries
4. Review task assignments

## Maintenance and Troubleshooting

### Common Issues

1. **Webhook timeouts**: Increase timeout settings in Zapier
2. **Authentication failures**: Verify API keys and permissions
3. **Data mapping errors**: Check field mappings and data types
4. **Rate limiting**: Implement delays between actions

### Monitoring Dashboard

Create a Zapier monitoring dashboard:
- Track successful vs. failed Zaps
- Monitor webhook response times
- Alert on consecutive failures

Your Zapier integrations are now configured for all three business entities with comprehensive automation workflows!
