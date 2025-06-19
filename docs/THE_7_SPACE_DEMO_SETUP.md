# The 7 Space Demo Environment Setup Guide

## Overview

This guide will help you set up a complete Docker-based demo environment for The 7 Space, featuring:

- **191 Real Contacts** from The 7 Space Notion database
- **Business Entity Segmentation** (The 7 Space focused)
- **Workflow Automation** for artists, gallery visitors, wellness clients
- **Lead Scoring & Qualification** system
- **Task Management** with automated follow-ups
- **Comprehensive Monitoring** with Grafana dashboards

## Prerequisites

1. **Docker & Docker Compose** installed and running
2. **Notion API Access** with your integration token
3. **The 7 Space Notion Database** with 191 contacts
4. **8GB RAM** minimum for optimal performance
5. **10GB Disk Space** for containers and data

## Quick Start

### 1. Configure Environment

Copy the demo environment template:
```bash
cp .env.demo.template .env.demo
```

Edit `.env.demo` with your actual credentials:
```bash
# Required - Replace with your actual values
NOTION_API_TOKEN=secret_your_actual_notion_token_here
NOTION_PARENT_PAGE_ID=your_actual_parent_page_id_here

# The 7 Space specific databases
NOTION_THE7SPACE_CONTACTS_DB=your_the7space_contacts_database_id
NOTION_CONTACTS_PROFILES_DB=your_contacts_profiles_database_id
NOTION_ACTIVE_WORKFLOW_INSTANCES_DB=your_workflow_instances_database_id
NOTION_TASKS_DB=your_tasks_database_id
```

### 2. Deploy Demo Environment

Run the automated deployment script:
```bash
./deploy-demo.sh deploy
```

This will:
- ✅ Check prerequisites
- ✅ Create demo directories
- ✅ Build Docker images
- ✅ Start all services
- ✅ Wait for health checks
- ✅ Display access information

### 3. Access Demo Services

Once deployed, access these services:

| Service | URL | Credentials |
|---------|-----|-------------|
| **The 7 Space Demo App** | http://localhost:8000 | - |
| **Grafana Dashboard** | http://localhost:3001 | admin/demo_admin_2024 |
| **Prometheus Metrics** | http://localhost:9091 | - |
| **Consul Service Discovery** | http://localhost:8501 | - |
| **MongoDB** | localhost:27018 | demo_user/demo_password |
| **Redis** | localhost:6380 | demo_redis_password |

## Demo Features

### Contact Management
- **191 Real Contacts** from The 7 Space
- **Automatic Classification**: Artists, Gallery Visitors, Wellness Clients, etc.
- **Lead Scoring**: 0-100 scoring based on engagement and type
- **Business Entity Isolation**: Only The 7 Space contacts visible

### Workflow Automation
- **Welcome Sequences**: Personalized for each contact type
- **Artist Onboarding**: Portfolio review, studio visits, exhibition planning
- **Wellness Consultation**: Automated booking and follow-up
- **Gallery Visitor Follow-up**: Event invitations and engagement
- **Event Management**: Registration, reminders, post-event surveys

### Task Management
- **Automated Task Creation**: Based on contact actions and workflows
- **Priority Scoring**: Urgent, High, Medium, Low priorities
- **Assignment Logic**: Tasks routed to appropriate team members
- **Follow-up Scheduling**: Automated reminders and escalations

### Lead Qualification
- **Scoring Algorithm**: Multi-factor lead scoring
- **Qualification Thresholds**: 75+ for qualified, 85+ for priority
- **Automated Routing**: High-value leads get immediate attention
- **Engagement Tracking**: Email opens, website visits, event attendance

## Monitoring & Analytics

### Grafana Dashboards
Access comprehensive dashboards at http://localhost:3001:

1. **The 7 Space Overview**: Key metrics and KPIs
2. **Contact Analytics**: Lead sources, types, scoring distribution
3. **Workflow Performance**: Automation success rates, completion times
4. **Task Management**: Task creation, completion, backlog analysis
5. **System Health**: Application performance, database metrics

### Key Metrics Tracked
- **Contact Acquisition**: New contacts by source and type
- **Lead Conversion**: Scoring improvements and qualification rates
- **Workflow Efficiency**: Automation success and completion rates
- **Task Performance**: Creation, assignment, and completion metrics
- **Engagement Analytics**: Email opens, website visits, event attendance

## Business Entity Configuration

### The 7 Space Focus
The demo is configured specifically for The 7 Space with:

**Contact Types:**
- Artists (portfolio review, exhibition planning)
- Gallery Visitors (follow-up, event invitations)
- Wellness Clients (consultation booking, program enrollment)
- Event Attendees (post-event engagement)
- Workshop Participants (skill development tracking)
- Community Members (ongoing engagement)
- Collectors (VIP treatment, acquisition opportunities)
- Curators (collaboration opportunities)

**Lead Sources:**
- Gallery visits (highest intent)
- Website contact forms
- Social media engagement
- Event registrations
- Workshop sign-ups
- Artist referrals
- Wellness inquiries

### Workflow Sequences

**Artist Onboarding (4-step sequence):**
1. Welcome email with portfolio submission request
2. Curator task creation for portfolio review
3. Studio visit scheduling
4. Exhibition opportunity discussion

**Wellness Consultation (3-step sequence):**
1. Wellness program introduction email
2. Consultation booking task creation
3. Follow-up reminder after 24 hours

**Gallery Visitor Follow-up (2-step sequence):**
1. Thank you email with upcoming events
2. Re-engagement follow-up after 1 week

## Management Commands

### Service Management
```bash
# Start demo environment
./deploy-demo.sh start

# Stop demo environment
./deploy-demo.sh stop

# Restart demo environment
./deploy-demo.sh restart

# View service logs
./deploy-demo.sh logs

# Check service status
./deploy-demo.sh status

# Rebuild and restart
./deploy-demo.sh rebuild

# Complete cleanup
./deploy-demo.sh cleanup
```

### Docker Compose Commands
```bash
# View running services
docker-compose -f docker-compose.demo.yml ps

# View logs for specific service
docker-compose -f docker-compose.demo.yml logs -f the7space-demo

# Execute commands in containers
docker-compose -f docker-compose.demo.yml exec the7space-demo bash
docker-compose -f docker-compose.demo.yml exec mongodb-demo mongosh

# Scale services (if needed)
docker-compose -f docker-compose.demo.yml up -d --scale the7space-demo=2
```

## Troubleshooting

### Common Issues

**1. Services not starting:**
```bash
# Check Docker is running
docker info

# Check available resources
docker system df

# View detailed logs
./deploy-demo.sh logs
```

**2. Notion API connection issues:**
```bash
# Verify API token in .env.demo
grep NOTION_API_TOKEN .env.demo

# Test API connection
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Notion-Version: 2022-06-28" \
     https://api.notion.com/v1/users/me
```

**3. Database connection issues:**
```bash
# Check MongoDB status
docker-compose -f docker-compose.demo.yml exec mongodb-demo mongosh --eval "db.runCommand('ping')"

# Check Redis status
docker-compose -f docker-compose.demo.yml exec redis-demo redis-cli ping
```

### Performance Optimization

**For better performance:**
1. Allocate more memory to Docker (8GB+ recommended)
2. Use SSD storage for Docker volumes
3. Close unnecessary applications
4. Monitor resource usage with `docker stats`

## Next Steps

### Production Deployment
Once the demo is validated:

1. **Scale Configuration**: Update for production load
2. **Security Hardening**: Implement production security measures
3. **Backup Strategy**: Configure automated backups
4. **Monitoring Alerts**: Set up alerting for critical metrics
5. **Load Balancing**: Configure for high availability

### Business Entity Expansion
To add AM Consulting and HigherSelf:

1. **Update Configuration**: Enable additional entities in config
2. **Database Segmentation**: Create separate collections/schemas
3. **Workflow Customization**: Add entity-specific workflows
4. **Contact Migration**: Import contacts for new entities
5. **Dashboard Updates**: Add entity-specific dashboards

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review service logs: `./deploy-demo.sh logs`
3. Check service status: `./deploy-demo.sh status`
4. Verify configuration in `.env.demo`

The demo environment provides a complete preview of the production system with real data and workflows, demonstrating the full capabilities of The HigherSelf Network Server for The 7 Space business operations.
