# Contact Workflow Automation System - Complete Guide

## Overview

The Contact Workflow Automation System is a comprehensive, intelligent automation platform that leverages your enriched Notion contact data to deliver personalized, business entity-specific engagement workflows. Built on the foundation of your 191 enriched contacts, this system provides targeted automation for The 7 Space, AM Consulting, and HigherSelf core platform.

## 🎯 Key Features

### Intelligent Contact Classification
- **Contact Types**: Artists, Gallery Contacts, Business Contacts, Potential Clients, Academic Contacts, Media Contacts, General Contacts
- **Lead Sources**: Website, Event, Referral
- **Business Entity Routing**: Automatic routing to The 7 Space, AM Consulting, or HigherSelf Core

### Multi-Channel Automation
- **Notifications**: Real-time alerts via Termius integration
- **Task Creation**: Automated task generation in Notion
- **Email Sequences**: Personalized engagement templates
- **Follow-up Scheduling**: Intelligent timing based on contact type and lead source

### Business Entity-Specific Workflows
- **The 7 Space**: Artist discovery, gallery inquiries, wellness programs
- **AM Consulting**: Lead qualification, consultation booking, proposal follow-up
- **HigherSelf Core**: Community onboarding, content engagement, platform introduction

## 🏗️ System Architecture

### Core Components

1. **Contact Workflow Automation Service** (`services/contact_workflow_automation.py`)
   - Main workflow processing engine
   - Contact classification and routing
   - Action execution and scheduling

2. **Workflow Orchestrator** (`services/workflow_orchestrator.py`)
   - Coordinates complex workflow sequences
   - Manages workflow state and transitions
   - Provides analytics and reporting

3. **Business Entity Workflows** (`config/business_entity_workflows.py`)
   - Entity-specific workflow templates
   - Customizable action sequences
   - Performance metrics tracking

4. **Engagement Templates** (`templates/contact_engagement_templates.py`)
   - Personalized email templates
   - Dynamic content generation
   - Multi-level personalization

5. **API Endpoints** (`api/contact_workflow_webhooks.py`)
   - RESTful API for workflow management
   - Webhook integration capabilities
   - Real-time status monitoring

## 🚀 Getting Started

### 1. Deploy the System

Run the deployment script to set up all components:

```bash
python3 tools/deploy_contact_workflows.py
```

This will:
- ✅ Validate environment configuration
- ✅ Initialize core services
- ✅ Configure business entity workflows
- ✅ Set up engagement templates
- ✅ Validate Notion database connections
- ✅ Test workflow execution
- ✅ Validate API endpoints

### 2. Start the Server

The workflow system is automatically integrated with the main server:

```bash
python3 main.py
```

### 3. Enable Contact Monitoring

Start real-time contact monitoring:

```bash
curl -X POST http://localhost:8000/contact-workflows/start-monitoring
```

## 📊 API Endpoints

### Manual Workflow Trigger
```bash
POST /contact-workflows/trigger
```

Manually trigger workflows for testing or special circumstances.

**Request Body:**
```json
{
  "contact_email": "artist@example.com",
  "contact_types": ["Artist"],
  "lead_source": "Website",
  "business_entities": ["The 7 Space"],
  "trigger_event": "manual_trigger"
}
```

### New Contact Registration
```bash
POST /contact-workflows/new-contact
```

Register new contacts and trigger welcome workflows.

**Request Body:**
```json
{
  "email": "newcontact@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "contact_types": ["Business Contact"],
  "lead_source": "Referral",
  "business_entities": ["AM Consulting"]
}
```

### Workflow Status
```bash
GET /contact-workflows/status
```

Get system status and analytics.

**Response:**
```json
{
  "active_workflows": 12,
  "total_contacts_processed": 191,
  "recent_executions": [...],
  "system_status": "operational"
}
```

### Available Templates
```bash
GET /contact-workflows/templates
```

Get all available workflow templates and configurations.

## 🎨 Business Entity Workflows

### The 7 Space Workflows

#### Artist Discovery Workflow
**Triggers**: Artist or Gallery Contact types
**Actions**:
1. Notify gallery curator (immediate)
2. Create portfolio review task (2 hours)
3. Send artist welcome email (24 hours)
4. Research social media presence (48 hours)

#### Wellness Inquiry Workflow
**Triggers**: General contacts interested in wellness
**Actions**:
1. Notify wellness coordinator (immediate)
2. Send wellness program information (4 hours)
3. Schedule consultation booking task (6 hours)

### AM Consulting Workflows

#### Lead Qualification Workflow
**Triggers**: Business Contact or Potential Client types
**Actions**:
1. Urgent notification to business development (immediate)
2. Create qualification task (1 hour)
3. Send consultation offer email (2 hours)
4. Company research task (4 hours)

#### Proposal Follow-up Workflow
**Triggers**: Post-consultation contacts
**Actions**:
1. Schedule follow-up call task (48 hours)
2. Send proposal follow-up email (72 hours)
3. Proposal optimization task (120 hours)

### HigherSelf Core Workflows

#### Community Onboarding Workflow
**Triggers**: General, Academic, or Media Contact types
**Actions**:
1. Notify community manager (immediate)
2. Send welcome email (1 hour)
3. Create onboarding task (24 hours)
4. Platform introduction email (1 week)

#### Content Engagement Workflow
**Triggers**: Existing community members
**Actions**:
1. Curate personalized content (24 hours)
2. Send content sharing email (72 hours)

## 📧 Engagement Templates

### Template Categories

1. **Welcome Sequences**
   - Artist welcome to The 7 Space
   - Business welcome to AM Consulting
   - Community welcome to HigherSelf

2. **Follow-up Communications**
   - Gallery inquiry responses
   - Consultation follow-ups
   - Event follow-ups

3. **Lead Source-Specific**
   - Event attendee follow-up
   - VIP referral welcome
   - Website visitor nurturing

### Personalization Levels

- **Basic**: Name and email only
- **Standard**: Include contact type and lead source
- **Advanced**: Full contact profile and behavior data
- **Premium**: AI-generated personalized content

## 🔄 Lead Source-Based Automation

### Website Leads
- **Response Time**: 12 hours
- **Follow-up Sequence**: Days 1, 7, 14
- **Focus**: Educational content and platform introduction

### Event Leads
- **Response Time**: 24 hours (hot leads: 4 hours)
- **Follow-up Sequence**: Days 1, 3, 7
- **Focus**: Personal connection and immediate value

### Referral Leads
- **Response Time**: 4 hours (VIP: 2 hours)
- **Follow-up Sequence**: Days 1, 2, 5
- **Focus**: Executive attention and premium treatment

## 📈 Analytics and Monitoring

### Workflow Metrics
- Total executions and success rates
- Average execution times
- Contact type performance breakdown
- Business entity effectiveness

### Engagement Tracking
- Email open and click rates
- Task completion rates
- Conversion metrics
- Response times

### System Health
- Active workflow monitoring
- Error tracking and alerting
- Performance optimization
- Database synchronization status

## 🔧 Configuration

### Environment Variables
```bash
NOTION_API_KEY=your_notion_api_key
NOTION_CONTACTS_PROFILES_DB=your_contacts_db_id
NOTION_ACTIVE_WORKFLOW_INSTANCES_DB=your_workflows_db_id
NOTION_TASKS_DB=your_tasks_db_id
```

### Workflow Customization

Workflows can be customized by modifying:
- `config/business_entity_workflows.py` - Workflow templates
- `templates/contact_engagement_templates.py` - Email templates
- `services/contact_workflow_automation.py` - Core logic

## 🚨 Troubleshooting

### Common Issues

1. **Workflows Not Triggering**
   - Check Notion API permissions
   - Verify database IDs in environment variables
   - Ensure contact monitoring is active

2. **Email Templates Not Personalizing**
   - Verify contact data completeness
   - Check template variable mappings
   - Review personalization rules

3. **Tasks Not Creating**
   - Validate Task Management Agent configuration
   - Check Notion Tasks database permissions
   - Review task creation logs

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger("workflow").setLevel(logging.DEBUG)
```

## 🔮 Future Enhancements

### Planned Features
- AI-powered content generation
- Advanced behavioral triggers
- Multi-channel communication (SMS, social media)
- Predictive lead scoring
- A/B testing for templates
- Integration with CRM systems

### Scalability Considerations
- Workflow queue management
- Distributed processing
- Performance optimization
- Advanced analytics dashboard

## 📞 Support

For technical support or questions:
- Review logs in `/logs/workflow_automation.log`
- Check Notion database activity
- Monitor API endpoint responses
- Contact system administrator

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Compatibility**: HigherSelf Network Server v2.0+
