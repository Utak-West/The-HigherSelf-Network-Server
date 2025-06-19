# N8N Integration Guide - The HigherSelf Network Server

## Overview

This guide provides comprehensive setup instructions for integrating N8N with The HigherSelf Network Server. N8N offers powerful workflow automation with advanced logic, data transformation, and custom code execution capabilities.

## Prerequisites

- N8N instance deployed (self-hosted or cloud)
- HigherSelf Network Server deployed and running
- Notion API access configured
- N8N credentials configured for external services

## N8N Installation (Self-Hosted)

### Docker Installation

```bash
# Create N8N directory
mkdir -p /opt/n8n
cd /opt/n8n

# Create docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'
services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your_secure_password
      - N8N_HOST=YOUR_N8N_DOMAIN
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://YOUR_N8N_DOMAIN:5678/
      - GENERIC_TIMEZONE=America/New_York
    volumes:
      - n8n_data:/home/node/.n8n
    restart: unless-stopped

volumes:
  n8n_data:
EOF

# Start N8N
docker-compose up -d
```

## Credentials Setup

### 1. HigherSelf API Credentials

In N8N, create credentials for HigherSelf API:

1. Go to **Credentials** → **Create New**
2. Select **HTTP Header Auth**
3. Configure:
   - **Name**: HigherSelf API
   - **Header Name**: Authorization
   - **Header Value**: Bearer YOUR_HIGHERSELF_API_KEY

### 2. Notion API Credentials

1. Go to **Credentials** → **Create New**
2. Select **Notion API**
3. Configure:
   - **API Key**: Your Notion integration token
   - **Database IDs**: Configure for each business entity

### 3. Email Credentials

1. Go to **Credentials** → **Create New**
2. Select **SMTP**
3. Configure your email provider settings

## The 7 Space N8N Workflows

### 1. Gallery Contact Form Processing

**Workflow Name**: `The7Space_ContactForm_Processing`

#### Workflow Structure:

```json
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "parameters": {
        "path": "the7space/contact-form",
        "httpMethod": "POST",
        "responseMode": "responseNode"
      }
    },
    {
      "name": "Validate Data",
      "type": "n8n-nodes-base.function",
      "position": [450, 300],
      "parameters": {
        "functionCode": "// Validate required fields\nconst requiredFields = ['name', 'email'];\nconst missingFields = [];\n\nfor (const field of requiredFields) {\n  if (!items[0].json[field]) {\n    missingFields.push(field);\n  }\n}\n\nif (missingFields.length > 0) {\n  throw new Error(`Missing required fields: ${missingFields.join(', ')}`);\n}\n\n// Classify contact type based on interest\nlet contactType = 'gallery_visitor';\nconst interest = items[0].json.interest?.toLowerCase() || '';\n\nif (interest.includes('artist') || interest.includes('exhibition')) {\n  contactType = 'artist';\n} else if (interest.includes('wellness') || interest.includes('meditation')) {\n  contactType = 'wellness_client';\n} else if (interest.includes('event') || interest.includes('workshop')) {\n  contactType = 'event_attendee';\n}\n\n// Calculate initial lead score\nlet leadScore = 50; // Base score\n\nif (items[0].json.phone) leadScore += 10;\nif (items[0].json.company) leadScore += 15;\nif (interest.includes('purchase') || interest.includes('commission')) leadScore += 20;\n\nreturn [{\n  json: {\n    ...items[0].json,\n    contactType,\n    leadScore,\n    businessEntity: 'the_7_space',\n    leadSource: 'website_contact',\n    createdAt: new Date().toISOString()\n  }\n}];"
      }
    },
    {
      "name": "Create Notion Contact",
      "type": "n8n-nodes-base.notion",
      "position": [650, 300],
      "parameters": {
        "operation": "create",
        "resource": "databasePage",
        "databaseId": "THE7SPACE_CONTACTS_DATABASE_ID",
        "properties": {
          "Name": "={{$json.name}}",
          "Email": "={{$json.email}}",
          "Phone": "={{$json.phone}}",
          "Interest": "={{$json.interest}}",
          "Contact Type": "={{$json.contactType}}",
          "Lead Source": "Website Contact Form",
          "Lead Score": "={{$json.leadScore}}",
          "Business Entity": "The 7 Space",
          "Created Date": "={{$json.createdAt}}"
        }
      },
      "credentials": {
        "notionApi": "Notion API"
      }
    },
    {
      "name": "Trigger Workflow",
      "type": "n8n-nodes-base.httpRequest",
      "position": [850, 300],
      "parameters": {
        "url": "http://YOUR_VM_IP/api/workflows/trigger",
        "method": "POST",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "business_entity",
              "value": "the_7_space"
            },
            {
              "name": "contact_id",
              "value": "={{$node['Create Notion Contact'].json.id}}"
            },
            {
              "name": "contact_email",
              "value": "={{$json.email}}"
            },
            {
              "name": "contact_type",
              "value": "={{$json.contactType}}"
            },
            {
              "name": "lead_source",
              "value": "website_contact"
            },
            {
              "name": "trigger_event",
              "value": "contact_created"
            }
          ]
        }
      },
      "credentials": {
        "httpHeaderAuth": "HigherSelf API"
      }
    },
    {
      "name": "Send Confirmation Email",
      "type": "n8n-nodes-base.emailSend",
      "position": [1050, 300],
      "parameters": {
        "toEmail": "={{$json.email}}",
        "subject": "Welcome to The 7 Space Community!",
        "message": "Dear {{$json.name}},\n\nThank you for your interest in The 7 Space! We're excited to connect with you.\n\nBased on your interest in {{$json.interest}}, we'll be in touch soon with personalized information and upcoming events that might interest you.\n\nWarm regards,\nThe 7 Space Team",
        "options": {
          "allowUnauthorizedCerts": false
        }
      },
      "credentials": {
        "smtp": "SMTP Credentials"
      }
    },
    {
      "name": "Success Response",
      "type": "n8n-nodes-base.respondToWebhook",
      "position": [1250, 300],
      "parameters": {
        "responseBody": "{\n  \"success\": true,\n  \"message\": \"Contact created successfully\",\n  \"contactId\": \"{{$node['Create Notion Contact'].json.id}}\"\n}",
        "options": {
          "responseCode": 200
        }
      }
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [
          {
            "node": "Validate Data",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Validate Data": {
      "main": [
        [
          {
            "node": "Create Notion Contact",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Create Notion Contact": {
      "main": [
        [
          {
            "node": "Trigger Workflow",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Trigger Workflow": {
      "main": [
        [
          {
            "node": "Send Confirmation Email",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Send Confirmation Email": {
      "main": [
        [
          {
            "node": "Success Response",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

### 2. Artist Portfolio Review Workflow

**Workflow Name**: `The7Space_Artist_Portfolio_Review`

#### Key Features:
- Automated portfolio analysis
- Curator task assignment
- Follow-up scheduling
- Exhibition opportunity assessment

```json
{
  "nodes": [
    {
      "name": "Portfolio Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "the7space/artist-portfolio",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Analyze Portfolio",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "// Analyze portfolio submission\nconst portfolio = items[0].json;\n\n// Calculate artist score based on submission quality\nlet artistScore = 60; // Base score\n\nif (portfolio.portfolio_url) artistScore += 15;\nif (portfolio.artist_statement) artistScore += 10;\nif (portfolio.exhibition_history) artistScore += 15;\nif (portfolio.education) artistScore += 10;\nif (portfolio.awards) artistScore += 10;\n\n// Determine priority based on score\nlet priority = 'Medium';\nif (artistScore >= 85) priority = 'High';\nif (artistScore < 70) priority = 'Low';\n\n// Set review timeline\nconst reviewDays = priority === 'High' ? 3 : priority === 'Medium' ? 7 : 14;\nconst dueDate = new Date();\ndueDate.setDate(dueDate.getDate() + reviewDays);\n\nreturn [{\n  json: {\n    ...portfolio,\n    artistScore,\n    priority,\n    reviewDueDate: dueDate.toISOString(),\n    contactType: 'artist',\n    businessEntity: 'the_7_space'\n  }\n}];"
      }
    },
    {
      "name": "Create Curator Task",
      "type": "n8n-nodes-base.notion",
      "parameters": {
        "operation": "create",
        "resource": "databasePage",
        "databaseId": "THE7SPACE_TASKS_DATABASE_ID",
        "properties": {
          "Task Name": "Portfolio Review: {{$json.artist_name}}",
          "Assignee": "Curator",
          "Priority": "={{$json.priority}}",
          "Status": "To Do",
          "Due Date": "={{$json.reviewDueDate}}",
          "Description": "Review portfolio submission from {{$json.artist_name}}. Artist Score: {{$json.artistScore}}/100. Portfolio: {{$json.portfolio_url}}",
          "Contact Email": "={{$json.email}}",
          "Business Entity": "The 7 Space"
        }
      }
    },
    {
      "name": "Send Artist Acknowledgment",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "toEmail": "={{$json.email}}",
        "subject": "Portfolio Received - The 7 Space",
        "message": "Dear {{$json.artist_name}},\n\nThank you for submitting your portfolio to The 7 Space. We have received your submission and our curatorial team will review it within {{$json.priority === 'High' ? '3 business days' : $json.priority === 'Medium' ? '1 week' : '2 weeks'}}.\n\nWe appreciate your interest in exhibiting with us and will be in touch soon.\n\nBest regards,\nThe 7 Space Curatorial Team"
      }
    }
  ]
}
```

## AM Consulting N8N Workflows

### 1. Lead Qualification and Scoring

**Workflow Name**: `AMConsulting_Lead_Qualification`

#### Advanced Lead Scoring Logic:

```javascript
// Advanced lead scoring function
function calculateLeadScore(leadData) {
  let score = 30; // Base score
  
  // Company size scoring
  const companySize = leadData.company_size?.toLowerCase() || '';
  if (companySize.includes('enterprise') || companySize.includes('1000+')) score += 25;
  else if (companySize.includes('medium') || companySize.includes('100-999')) score += 15;
  else if (companySize.includes('small') || companySize.includes('10-99')) score += 10;
  
  // Budget scoring
  const budget = parseInt(leadData.budget) || 0;
  if (budget >= 100000) score += 30;
  else if (budget >= 50000) score += 20;
  else if (budget >= 25000) score += 15;
  else if (budget >= 10000) score += 10;
  
  // Industry scoring (high-value industries)
  const industry = leadData.industry?.toLowerCase() || '';
  const highValueIndustries = ['technology', 'finance', 'healthcare', 'manufacturing'];
  if (highValueIndustries.some(ind => industry.includes(ind))) score += 15;
  
  // Timeline urgency
  const timeline = leadData.timeline?.toLowerCase() || '';
  if (timeline.includes('immediate') || timeline.includes('asap')) score += 20;
  else if (timeline.includes('month')) score += 15;
  else if (timeline.includes('quarter')) score += 10;
  
  // Lead source quality
  const leadSource = leadData.lead_source?.toLowerCase() || '';
  if (leadSource.includes('referral')) score += 20;
  else if (leadSource.includes('linkedin')) score += 15;
  else if (leadSource.includes('website')) score += 10;
  
  return Math.min(score, 100); // Cap at 100
}
```

### 2. Client Onboarding Automation

**Workflow Name**: `AMConsulting_Client_Onboarding`

#### Features:
- Project setup automation
- Milestone creation
- Team assignment
- Welcome package delivery
- Kickoff meeting scheduling

## HigherSelf Core N8N Workflows

### 1. Community Member Engagement Tracking

**Workflow Name**: `HigherSelf_Engagement_Tracking`

#### Engagement Scoring Algorithm:

```javascript
// Community engagement scoring
function calculateEngagementScore(memberData, activities) {
  let score = 0;
  
  // Activity scoring
  activities.forEach(activity => {
    switch(activity.type) {
      case 'post_created': score += 10; break;
      case 'comment_made': score += 5; break;
      case 'event_attended': score += 15; break;
      case 'content_shared': score += 8; break;
      case 'profile_updated': score += 3; break;
      case 'login': score += 1; break;
    }
  });
  
  // Consistency bonus (regular activity)
  const daysSinceJoin = (new Date() - new Date(memberData.join_date)) / (1000 * 60 * 60 * 24);
  const activeDays = new Set(activities.map(a => a.date.split('T')[0])).size;
  const consistencyRatio = activeDays / daysSinceJoin;
  
  if (consistencyRatio > 0.5) score *= 1.2; // 20% bonus for high consistency
  else if (consistencyRatio > 0.3) score *= 1.1; // 10% bonus for medium consistency
  
  return Math.round(score);
}
```

## Error Handling and Monitoring

### 1. Global Error Handler

Create a global error handling workflow:

```json
{
  "name": "Global Error Handler",
  "nodes": [
    {
      "name": "Error Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "error-handler",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Log Error",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "// Log error details\nconst error = items[0].json;\nconsole.log('N8N Workflow Error:', {\n  workflow: error.workflow,\n  node: error.node,\n  error: error.error,\n  timestamp: new Date().toISOString()\n});\n\nreturn items;"
      }
    },
    {
      "name": "Send Alert Email",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "toEmail": "admin@yourdomain.com",
        "subject": "N8N Workflow Error Alert",
        "message": "Workflow Error Details:\n\nWorkflow: {{$json.workflow}}\nNode: {{$json.node}}\nError: {{$json.error}}\nTimestamp: {{$json.timestamp}}"
      }
    }
  ]
}
```

### 2. Health Check Workflow

```json
{
  "name": "Health Check",
  "nodes": [
    {
      "name": "Schedule",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "triggerTimes": {
          "item": [
            {
              "mode": "everyMinute",
              "minute": 15
            }
          ]
        }
      }
    },
    {
      "name": "Check HigherSelf API",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://YOUR_VM_IP/health",
        "method": "GET"
      }
    },
    {
      "name": "Check Response",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{$json.status}}",
              "operation": "equal",
              "value2": "healthy"
            }
          ]
        }
      }
    }
  ]
}
```

## Testing and Validation

### 1. Workflow Testing

```bash
# Test The 7 Space contact form
curl -X POST http://YOUR_N8N_DOMAIN:5678/webhook/the7space/contact-form \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Artist",
    "email": "artist@test.com",
    "interest": "Exhibition Opportunity",
    "phone": "555-1234"
  }'

# Test AM Consulting lead capture
curl -X POST http://YOUR_N8N_DOMAIN:5678/webhook/amconsulting/lead-capture \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "email": "ceo@testcompany.com",
    "company": "Test Corp",
    "company_size": "100-999",
    "budget": "75000",
    "timeline": "Next Quarter"
  }'
```

### 2. Performance Monitoring

Monitor N8N performance:
- Execution times
- Success/failure rates
- Resource usage
- Queue lengths

Your N8N integration is now configured with advanced workflows for all three business entities!
