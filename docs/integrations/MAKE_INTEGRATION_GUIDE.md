# Make.com Integration Guide - The HigherSelf Network Server

## Overview

This guide provides comprehensive setup instructions for integrating Make.com (formerly Integromat) with The HigherSelf Network Server. Make.com offers visual workflow automation with powerful data processing, conditional logic, and extensive app integrations.

## Prerequisites

- Active Make.com account (Pro plan recommended for advanced features)
- HigherSelf Network Server deployed and running
- Notion API access configured
- Make.com webhook URLs configured

## Make.com Account Setup

### 1. Organization and Team Setup

1. **Create Organization**
   - Go to Make.com dashboard
   - Create organization: "HigherSelf Network"
   - Add team members with appropriate permissions

2. **Configure Connections**
   - Set up connections for all required services
   - Test each connection before building scenarios

### 2. Webhook Configuration

Create webhook endpoints for each business entity:

| Business Entity | Webhook URL | Purpose |
|-----------------|-------------|---------|
| **The 7 Space** | `https://hook.integromat.com/YOUR_HOOK_ID/the7space` | Gallery & wellness automation |
| **AM Consulting** | `https://hook.integromat.com/YOUR_HOOK_ID/amconsulting` | Business consulting workflows |
| **HigherSelf Core** | `https://hook.integromat.com/YOUR_HOOK_ID/higherself` | Community platform automation |

## The 7 Space Make.com Scenarios

### 1. Gallery Contact Form to Notion and Workflow Automation

**Scenario Name**: `The7Space - Contact Form Processing`

#### Scenario Structure:

```json
{
  "scenario": {
    "name": "The7Space - Contact Form Processing",
    "flow": [
      {
        "id": 1,
        "module": "webhook",
        "version": 1,
        "parameters": {
          "hook": "YOUR_THE7SPACE_HOOK_ID",
          "maxResults": 1
        },
        "mapper": {},
        "metadata": {
          "designer": {
            "x": 0,
            "y": 0
          }
        }
      },
      {
        "id": 2,
        "module": "builtin:BasicFeeder",
        "version": 1,
        "parameters": {},
        "mapper": {
          "array": "{{1.name}}; {{1.email}}; {{1.phone}}; {{1.interest}}"
        },
        "metadata": {
          "designer": {
            "x": 300,
            "y": 0
          }
        }
      },
      {
        "id": 3,
        "module": "util:SetVariables",
        "version": 1,
        "parameters": {},
        "mapper": {
          "variables": [
            {
              "name": "contactType",
              "value": "{{if(contains(lower(1.interest); \"artist\"); \"artist\"; if(contains(lower(1.interest); \"wellness\"); \"wellness_client\"; \"gallery_visitor\"))}}"
            },
            {
              "name": "leadScore",
              "value": "{{50 + if(1.phone; 10; 0) + if(contains(lower(1.interest); \"purchase\"); 20; 0)}}"
            },
            {
              "name": "priority",
              "value": "{{if(leadScore > 75; \"High\"; if(leadScore > 60; \"Medium\"; \"Low\"))}}"
            }
          ]
        },
        "metadata": {
          "designer": {
            "x": 600,
            "y": 0
          }
        }
      },
      {
        "id": 4,
        "module": "notion:CreateDatabaseItem",
        "version": 1,
        "parameters": {
          "databaseId": "THE7SPACE_CONTACTS_DATABASE_ID"
        },
        "mapper": {
          "properties": {
            "Name": {
              "type": "title",
              "title": [
                {
                  "type": "text",
                  "text": {
                    "content": "{{1.name}}"
                  }
                }
              ]
            },
            "Email": {
              "type": "email",
              "email": "{{1.email}}"
            },
            "Phone": {
              "type": "phone_number",
              "phone_number": "{{1.phone}}"
            },
            "Interest": {
              "type": "rich_text",
              "rich_text": [
                {
                  "type": "text",
                  "text": {
                    "content": "{{1.interest}}"
                  }
                }
              ]
            },
            "Contact Type": {
              "type": "select",
              "select": {
                "name": "{{3.contactType}}"
              }
            },
            "Lead Score": {
              "type": "number",
              "number": "{{3.leadScore}}"
            },
            "Lead Source": {
              "type": "select",
              "select": {
                "name": "Website Contact Form"
              }
            },
            "Priority": {
              "type": "select",
              "select": {
                "name": "{{3.priority}}"
              }
            },
            "Created Date": {
              "type": "date",
              "date": {
                "start": "{{formatDate(now; \"YYYY-MM-DD\")}}"
              }
            }
          }
        },
        "metadata": {
          "designer": {
            "x": 900,
            "y": 0
          }
        }
      },
      {
        "id": 5,
        "module": "http:ActionSendData",
        "version": 3,
        "parameters": {},
        "mapper": {
          "url": "http://YOUR_VM_IP/api/workflows/trigger",
          "method": "POST",
          "headers": [
            {
              "name": "Authorization",
              "value": "Bearer YOUR_HIGHERSELF_API_KEY"
            },
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ],
          "body": {
            "business_entity": "the_7_space",
            "contact_id": "{{4.id}}",
            "contact_email": "{{1.email}}",
            "contact_type": "{{3.contactType}}",
            "lead_source": "website_contact",
            "trigger_event": "contact_created",
            "metadata": {
              "lead_score": "{{3.leadScore}}",
              "priority": "{{3.priority}}",
              "interest": "{{1.interest}}"
            }
          }
        },
        "metadata": {
          "designer": {
            "x": 1200,
            "y": 0
          }
        }
      },
      {
        "id": 6,
        "module": "email:ActionSendEmail",
        "version": 3,
        "parameters": {
          "account": "YOUR_EMAIL_CONNECTION"
        },
        "mapper": {
          "to": "{{1.email}}",
          "subject": "Welcome to The 7 Space Community! 🎨",
          "html": "<h2>Dear {{1.name}},</h2><p>Thank you for your interest in The 7 Space! We're thrilled to have you join our vibrant community of artists, wellness enthusiasts, and creative souls.</p><h3>What makes The 7 Space special:</h3><ul><li>Contemporary art gallery featuring local and international artists</li><li>Wellness center with meditation, yoga, and healing services</li><li>Community events, workshops, and creative gatherings</li><li>A space where art and wellness intersect</li></ul><p>Based on your interest in <strong>{{1.interest}}</strong>, we'll be in touch soon with personalized recommendations.</p><p>Warm regards,<br>The 7 Space Team</p>",
          "attachments": []
        },
        "metadata": {
          "designer": {
            "x": 1500,
            "y": 0
          }
        }
      }
    ]
  }
}
```

### 2. Artist Portfolio Review and Exhibition Planning

**Scenario Name**: `The7Space - Artist Portfolio Review`

#### Advanced Features:
- Portfolio analysis with scoring
- Automated curator assignment
- Exhibition opportunity assessment
- Follow-up scheduling

```json
{
  "scenario": {
    "name": "The7Space - Artist Portfolio Review",
    "flow": [
      {
        "id": 1,
        "module": "webhook",
        "version": 1,
        "parameters": {
          "hook": "YOUR_PORTFOLIO_HOOK_ID"
        }
      },
      {
        "id": 2,
        "module": "util:SetVariables",
        "version": 1,
        "parameters": {},
        "mapper": {
          "variables": [
            {
              "name": "artistScore",
              "value": "{{60 + if(1.portfolio_url; 15; 0) + if(1.artist_statement; 10; 0) + if(1.exhibition_history; 15; 0) + if(1.education; 10; 0) + if(1.awards; 10; 0)}}"
            },
            {
              "name": "reviewPriority",
              "value": "{{if(artistScore >= 85; \"High\"; if(artistScore >= 70; \"Medium\"; \"Low\"))}}"
            },
            {
              "name": "reviewDays",
              "value": "{{if(reviewPriority = \"High\"; 3; if(reviewPriority = \"Medium\"; 7; 14))}}"
            },
            {
              "name": "curatorAssignment",
              "value": "{{if(contains(lower(1.medium); \"painting\"); \"Senior Curator - Paintings\"; if(contains(lower(1.medium); \"sculpture\"); \"Senior Curator - Sculpture\"; \"General Curator\"))}}"
            }
          ]
        }
      },
      {
        "id": 3,
        "module": "notion:CreateDatabaseItem",
        "version": 1,
        "parameters": {
          "databaseId": "THE7SPACE_TASKS_DATABASE_ID"
        },
        "mapper": {
          "properties": {
            "Task Name": {
              "type": "title",
              "title": [
                {
                  "type": "text",
                  "text": {
                    "content": "Portfolio Review: {{1.artist_name}}"
                  }
                }
              ]
            },
            "Assignee": {
              "type": "select",
              "select": {
                "name": "{{2.curatorAssignment}}"
              }
            },
            "Priority": {
              "type": "select",
              "select": {
                "name": "{{2.reviewPriority}}"
              }
            },
            "Status": {
              "type": "select",
              "select": {
                "name": "To Do"
              }
            },
            "Due Date": {
              "type": "date",
              "date": {
                "start": "{{formatDate(addDays(now; 2.reviewDays); \"YYYY-MM-DD\")}}"
              }
            },
            "Description": {
              "type": "rich_text",
              "rich_text": [
                {
                  "type": "text",
                  "text": {
                    "content": "Review portfolio submission from {{1.artist_name}}. Artist Score: {{2.artistScore}}/100. Medium: {{1.medium}}. Portfolio URL: {{1.portfolio_url}}"
                  }
                }
              ]
            }
          }
        }
      }
    ]
  }
}
```

### 3. Event Registration and Management

**Scenario Name**: `The7Space - Event Registration Management`

#### Features:
- Calendar integration
- Automated confirmations
- Waitlist management
- Post-event follow-up

## AM Consulting Make.com Scenarios

### 1. Lead Qualification and CRM Integration

**Scenario Name**: `AMConsulting - Lead Qualification Pipeline`

#### Advanced Lead Scoring Logic:

```json
{
  "scenario": {
    "name": "AMConsulting - Lead Qualification Pipeline",
    "flow": [
      {
        "id": 1,
        "module": "webhook",
        "version": 1,
        "parameters": {
          "hook": "YOUR_AMCONSULTING_HOOK_ID"
        }
      },
      {
        "id": 2,
        "module": "util:SetVariables",
        "version": 1,
        "parameters": {},
        "mapper": {
          "variables": [
            {
              "name": "companySizeScore",
              "value": "{{if(contains(lower(1.company_size); \"enterprise\") or contains(lower(1.company_size); \"1000+\"); 25; if(contains(lower(1.company_size); \"medium\") or contains(lower(1.company_size); \"100-999\"); 15; if(contains(lower(1.company_size); \"small\") or contains(lower(1.company_size); \"10-99\"); 10; 5)))}}"
            },
            {
              "name": "budgetScore",
              "value": "{{if(parseNumber(1.budget) >= 100000; 30; if(parseNumber(1.budget) >= 50000; 20; if(parseNumber(1.budget) >= 25000; 15; if(parseNumber(1.budget) >= 10000; 10; 5))))}}"
            },
            {
              "name": "industryScore",
              "value": "{{if(contains(lower(1.industry); \"technology\") or contains(lower(1.industry); \"finance\") or contains(lower(1.industry); \"healthcare\"); 15; 5)}}"
            },
            {
              "name": "timelineScore",
              "value": "{{if(contains(lower(1.timeline); \"immediate\") or contains(lower(1.timeline); \"asap\"); 20; if(contains(lower(1.timeline); \"month\"); 15; if(contains(lower(1.timeline); \"quarter\"); 10; 5)))}}"
            },
            {
              "name": "sourceScore",
              "value": "{{if(contains(lower(1.lead_source); \"referral\"); 20; if(contains(lower(1.lead_source); \"linkedin\"); 15; if(contains(lower(1.lead_source); \"website\"); 10; 5)))}}"
            },
            {
              "name": "totalScore",
              "value": "{{30 + companySizeScore + budgetScore + industryScore + timelineScore + sourceScore}}"
            },
            {
              "name": "leadGrade",
              "value": "{{if(totalScore >= 90; \"A\"; if(totalScore >= 75; \"B\"; if(totalScore >= 60; \"C\"; \"D\")))}}"
            },
            {
              "name": "assignedConsultant",
              "value": "{{if(leadGrade = \"A\"; \"Senior Partner\"; if(leadGrade = \"B\"; \"Senior Consultant\"; \"Junior Consultant\"))}}"
            }
          ]
        }
      },
      {
        "id": 3,
        "module": "notion:CreateDatabaseItem",
        "version": 1,
        "parameters": {
          "databaseId": "AMCONSULTING_CONTACTS_DATABASE_ID"
        },
        "mapper": {
          "properties": {
            "Company Name": {
              "type": "title",
              "title": [
                {
                  "type": "text",
                  "text": {
                    "content": "{{1.company}}"
                  }
                }
              ]
            },
            "Contact Name": {
              "type": "rich_text",
              "rich_text": [
                {
                  "type": "text",
                  "text": {
                    "content": "{{1.name}}"
                  }
                }
              ]
            },
            "Email": {
              "type": "email",
              "email": "{{1.email}}"
            },
            "Industry": {
              "type": "select",
              "select": {
                "name": "{{1.industry}}"
              }
            },
            "Company Size": {
              "type": "select",
              "select": {
                "name": "{{1.company_size}}"
              }
            },
            "Budget": {
              "type": "number",
              "number": "{{parseNumber(1.budget)}}"
            },
            "Lead Score": {
              "type": "number",
              "number": "{{2.totalScore}}"
            },
            "Lead Grade": {
              "type": "select",
              "select": {
                "name": "{{2.leadGrade}}"
              }
            },
            "Assigned Consultant": {
              "type": "select",
              "select": {
                "name": "{{2.assignedConsultant}}"
              }
            },
            "Status": {
              "type": "select",
              "select": {
                "name": "New Lead"
              }
            }
          }
        }
      },
      {
        "id": 4,
        "module": "gohighlevel:CreateContact",
        "version": 1,
        "parameters": {
          "connection": "YOUR_GHL_CONNECTION"
        },
        "mapper": {
          "firstName": "{{1.name}}",
          "email": "{{1.email}}",
          "phone": "{{1.phone}}",
          "companyName": "{{1.company}}",
          "tags": ["{{2.leadGrade}}-Grade", "{{1.industry}}", "AMConsulting"],
          "customFields": {
            "lead_score": "{{2.totalScore}}",
            "budget": "{{1.budget}}",
            "timeline": "{{1.timeline}}"
          }
        }
      }
    ]
  }
}
```

### 2. Client Onboarding and Project Setup

**Scenario Name**: `AMConsulting - Client Onboarding Automation`

#### Features:
- Project creation in Notion
- Milestone setup
- Team assignment
- Welcome package delivery
- Kickoff meeting scheduling

## HigherSelf Core Make.com Scenarios

### 1. Community Member Engagement Tracking

**Scenario Name**: `HigherSelf - Member Engagement Analytics`

#### Engagement Scoring System:

```json
{
  "scenario": {
    "name": "HigherSelf - Member Engagement Analytics",
    "flow": [
      {
        "id": 1,
        "module": "webhook",
        "version": 1,
        "parameters": {
          "hook": "YOUR_HIGHERSELF_ENGAGEMENT_HOOK_ID"
        }
      },
      {
        "id": 2,
        "module": "util:SetVariables",
        "version": 1,
        "parameters": {},
        "mapper": {
          "variables": [
            {
              "name": "activityScore",
              "value": "{{if(1.activity_type = \"post_created\"; 10; if(1.activity_type = \"comment_made\"; 5; if(1.activity_type = \"event_attended\"; 15; if(1.activity_type = \"content_shared\"; 8; if(1.activity_type = \"profile_updated\"; 3; 1)))))}}"
            },
            {
              "name": "engagementLevel",
              "value": "{{if(1.total_score >= 100; \"High\"; if(1.total_score >= 50; \"Medium\"; \"Low\"))}}"
            },
            {
              "name": "recommendedActions",
              "value": "{{if(engagementLevel = \"High\"; \"Invite to VIP events, Consider for community leadership\"; if(engagementLevel = \"Medium\"; \"Send personalized content, Invite to workshops\"; \"Send re-engagement campaign, Offer onboarding support\"))}}"
            }
          ]
        }
      },
      {
        "id": 3,
        "module": "notion:UpdateDatabaseItem",
        "version": 1,
        "parameters": {
          "databaseId": "HIGHERSELF_MEMBERS_DATABASE_ID",
          "pageId": "{{1.member_id}}"
        },
        "mapper": {
          "properties": {
            "Engagement Score": {
              "type": "number",
              "number": "{{1.total_score + 2.activityScore}}"
            },
            "Engagement Level": {
              "type": "select",
              "select": {
                "name": "{{2.engagementLevel}}"
              }
            },
            "Last Activity": {
              "type": "date",
              "date": {
                "start": "{{formatDate(now; \"YYYY-MM-DD\")}}"
              }
            },
            "Recommended Actions": {
              "type": "rich_text",
              "rich_text": [
                {
                  "type": "text",
                  "text": {
                    "content": "{{2.recommendedActions}}"
                  }
                }
              ]
            }
          }
        }
      }
    ]
  }
}
```

## Error Handling and Monitoring

### 1. Global Error Handler Scenario

**Scenario Name**: `Global - Error Handler`

```json
{
  "scenario": {
    "name": "Global - Error Handler",
    "flow": [
      {
        "id": 1,
        "module": "webhook",
        "version": 1,
        "parameters": {
          "hook": "YOUR_ERROR_HANDLER_HOOK_ID"
        }
      },
      {
        "id": 2,
        "module": "util:SetVariables",
        "version": 1,
        "parameters": {},
        "mapper": {
          "variables": [
            {
              "name": "errorSeverity",
              "value": "{{if(contains(lower(1.error); \"critical\") or contains(lower(1.error); \"fatal\"); \"Critical\"; if(contains(lower(1.error); \"warning\"); \"Warning\"; \"Info\"))}}"
            },
            {
              "name": "alertRequired",
              "value": "{{if(errorSeverity = \"Critical\"; true; false)}}"
            }
          ]
        }
      },
      {
        "id": 3,
        "module": "notion:CreateDatabaseItem",
        "version": 1,
        "parameters": {
          "databaseId": "ERROR_LOG_DATABASE_ID"
        },
        "mapper": {
          "properties": {
            "Error Message": {
              "type": "title",
              "title": [
                {
                  "type": "text",
                  "text": {
                    "content": "{{1.error}}"
                  }
                }
              ]
            },
            "Scenario": {
              "type": "rich_text",
              "rich_text": [
                {
                  "type": "text",
                  "text": {
                    "content": "{{1.scenario}}"
                  }
                }
              ]
            },
            "Severity": {
              "type": "select",
              "select": {
                "name": "{{2.errorSeverity}}"
              }
            },
            "Timestamp": {
              "type": "date",
              "date": {
                "start": "{{formatDate(now; \"YYYY-MM-DD HH:mm:ss\")}}"
              }
            }
          }
        }
      },
      {
        "id": 4,
        "module": "email:ActionSendEmail",
        "version": 3,
        "parameters": {
          "account": "YOUR_EMAIL_CONNECTION"
        },
        "filter": {
          "conditions": [
            [
              {
                "a": "{{2.alertRequired}}",
                "o": "boolean:equal",
                "b": "true"
              }
            ]
          ]
        },
        "mapper": {
          "to": "admin@yourdomain.com",
          "subject": "🚨 Critical Error in Make.com Scenario",
          "html": "<h2>Critical Error Alert</h2><p><strong>Scenario:</strong> {{1.scenario}}</p><p><strong>Error:</strong> {{1.error}}</p><p><strong>Timestamp:</strong> {{formatDate(now; \"YYYY-MM-DD HH:mm:ss\")}}</p><p>Please investigate immediately.</p>"
        }
      }
    ]
  }
}
```

### 2. Health Check and Monitoring

**Scenario Name**: `System - Health Check`

```json
{
  "scenario": {
    "name": "System - Health Check",
    "flow": [
      {
        "id": 1,
        "module": "util:BasicScheduler",
        "version": 1,
        "parameters": {
          "interval": 15,
          "unit": "minutes"
        }
      },
      {
        "id": 2,
        "module": "http:ActionSendData",
        "version": 3,
        "parameters": {},
        "mapper": {
          "url": "http://YOUR_VM_IP/health",
          "method": "GET",
          "timeout": 30
        }
      },
      {
        "id": 3,
        "module": "util:SetVariables",
        "version": 1,
        "parameters": {},
        "mapper": {
          "variables": [
            {
              "name": "isHealthy",
              "value": "{{if(2.status = \"healthy\"; true; false)}}"
            },
            {
              "name": "responseTime",
              "value": "{{2.responseTime}}"
            }
          ]
        }
      },
      {
        "id": 4,
        "module": "email:ActionSendEmail",
        "version": 3,
        "parameters": {
          "account": "YOUR_EMAIL_CONNECTION"
        },
        "filter": {
          "conditions": [
            [
              {
                "a": "{{3.isHealthy}}",
                "o": "boolean:equal",
                "b": "false"
              }
            ]
          ]
        },
        "mapper": {
          "to": "admin@yourdomain.com",
          "subject": "🚨 HigherSelf Server Health Check Failed",
          "html": "<h2>Server Health Alert</h2><p>The HigherSelf Network Server health check has failed.</p><p><strong>Response Time:</strong> {{3.responseTime}}ms</p><p><strong>Status:</strong> {{2.status}}</p><p>Please investigate immediately.</p>"
        }
      }
    ]
  }
}
```

## Testing and Validation

### 1. Scenario Testing

Test each scenario with sample data:

```bash
# Test The 7 Space contact form
curl -X POST https://hook.integromat.com/YOUR_HOOK_ID/the7space \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Gallery Visitor",
    "email": "visitor@test.com",
    "phone": "555-1234",
    "interest": "Contemporary Art Exhibition"
  }'

# Test AM Consulting lead capture
curl -X POST https://hook.integromat.com/YOUR_HOOK_ID/amconsulting \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "email": "john@testcorp.com",
    "company": "Test Corporation",
    "company_size": "100-999",
    "budget": "75000",
    "industry": "Technology",
    "timeline": "Next Quarter"
  }'

# Test HigherSelf member engagement
curl -X POST https://hook.integromat.com/YOUR_HOOK_ID/higherself \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "test_member_123",
    "activity_type": "post_created",
    "total_score": 65
  }'
```

### 2. Performance Monitoring

Monitor Make.com scenarios:
- Execution success rates
- Processing times
- Data throughput
- Error frequencies

## Best Practices

### 1. Scenario Organization
- Use clear naming conventions
- Group related scenarios in folders
- Document scenario purposes
- Version control scenario exports

### 2. Data Validation
- Validate input data before processing
- Use filters to handle edge cases
- Implement data transformation logic
- Test with various data formats

### 3. Error Recovery
- Implement retry logic for failed operations
- Use error handlers for critical scenarios
- Log errors for debugging
- Set up alerting for failures

Your Make.com integration is now configured with comprehensive automation scenarios for all three business entities!