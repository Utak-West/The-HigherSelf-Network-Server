# The HigherSelf Network Server - Deployment and Training Guide

This document provides comprehensive instructions for deploying The HigherSelf Network Server and training staff on its operation and maintenance.

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Environment Setup](#environment-setup)
3. [Notion Integration Setup](#notion-integration-setup)
4. [Deployment Steps](#deployment-steps)
5. [Staff Training Guide](#staff-training-guide)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)

## Deployment Options

The HigherSelf Network Server can be deployed in several ways:

### 1. Docker Deployment (Recommended)

Docker provides the most consistent and isolated environment for running the server. This is the recommended approach for production deployments.

**Requirements:**
- Docker and Docker Compose installed
- Access to the Docker Hub registry
- 2GB RAM minimum, 4GB recommended
- 10GB disk space minimum

### 2. Direct Python Deployment

For development or testing, you can run the server directly with Python.

**Requirements:**
- Python 3.10 or higher
- pip package manager
- Virtual environment tool (venv, conda, etc.)
- 2GB RAM minimum
- 5GB disk space minimum

### 3. Cloud Deployment

For scalable production deployments, consider cloud platforms:

**Options:**
- AWS Elastic Container Service (ECS)
- Google Cloud Run
- Azure Container Instances
- Digital Ocean App Platform

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git
cd The-HigherSelf-Network-Server
```

### 2. Configure Environment Variables

Copy the example environment file and edit it with your specific values:

```bash
cp .env.example .env
nano .env
```

**Critical Variables to Configure:**

- `NOTION_API_TOKEN`: Your Notion integration API token
- `NOTION_PARENT_PAGE_ID`: ID of the parent page for database creation
- `WEBHOOK_SECRET`: Secret for securing webhook endpoints
- All API credentials for integrated services

### 3. SSL Certificate Setup (Production)

For production deployments, set up SSL certificates:

```bash
mkdir -p deployment/ssl
# Place your SSL certificates in this directory:
# - deployment/ssl/cert.pem
# - deployment/ssl/key.pem
```

You can use Let's Encrypt to generate free SSL certificates:

```bash
sudo apt-get install certbot
sudo certbot certonly --standalone -d your-domain.com
```

## Notion Integration Setup

The HigherSelf Network Server uses Notion as its central hub. Follow these steps to set up the Notion integration:

### 1. Create a Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Name it "HigherSelf Network Server"
4. Select the workspace where you want to create the databases
5. Set appropriate capabilities (Read content, Update content, Insert content)
6. Copy the "Internal Integration Token" and add it to your `.env` file as `NOTION_API_TOKEN`

### 2. Create a Parent Page

1. Create a new page in your Notion workspace
2. Share this page with your integration (click "Share" → select your integration)
3. Copy the page ID from the URL (the part after the workspace name and before the question mark)
4. Add this ID to your `.env` file as `NOTION_PARENT_PAGE_ID`

### 3. Initialize Notion Databases

Run the database setup utility to create all required databases:

```bash
# Using Docker
docker-compose run --rm windsurf-agent python -m tools.notion_db_setup

# Using Python directly
python -m tools.notion_db_setup
```

This will create 16 interconnected databases in your Notion workspace and update your `.env` file with their IDs.

## Deployment Steps

### Docker Deployment

1. **Build and start the containers:**

```bash
docker-compose up -d
```

2. **Verify the deployment:**

```bash
docker-compose ps
docker-compose logs -f
```

3. **For production deployment:**

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Direct Python Deployment

1. **Create and activate a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Run the server:**

```bash
python main.py
```

### Cloud Deployment

For AWS ECS deployment:

1. **Build and push the Docker image:**

```bash
aws ecr create-repository --repository-name higherself-network-server
aws ecr get-login-password | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.<region>.amazonaws.com
docker build -t <your-aws-account-id>.dkr.ecr.<region>.amazonaws.com/higherself-network-server:latest .
docker push <your-aws-account-id>.dkr.ecr.<region>.amazonaws.com/higherself-network-server:latest
```

2. **Create an ECS cluster and service using the AWS console or CLI**

## Staff Training Guide

### System Overview Training

1. **Introduction to The HigherSelf Network Server**
   - Architecture overview: Hub-and-spoke model with Notion as the central hub
   - Agent system: Named personalities and their responsibilities
   - Integration ecosystem: How external services connect to the system

2. **Notion as the Central Hub**
   - Tour of the 16 interconnected databases
   - Data flow between databases
   - How to view and interpret workflow instances

3. **Agent Personalities**
   - Nyra: Lead Capture Specialist
   - Solari: Booking & Order Manager
   - Ruvo: Task Orchestrator
   - Liora: Marketing Strategist
   - Sage: Community Curator
   - Elan: Content Choreographer
   - Zevi: Audience Analyst
   - Grace: System Orchestrator

### Operational Training

1. **Daily Operations**
   - Checking system health
   - Monitoring active workflows
   - Reviewing agent communications
   - Handling alerts and notifications

2. **Content Management**
   - Creating content requests
   - Monitoring content lifecycle
   - Approving and publishing content
   - Content performance tracking

3. **Customer Journey Management**
   - Lead capture process
   - Booking and order processing
   - Community engagement
   - Feedback collection and analysis

4. **Task Management**
   - Creating and assigning tasks
   - Task prioritization
   - Deadline management
   - Task completion and verification

### Technical Training (for IT Staff)

1. **System Maintenance**
   - Log monitoring and rotation
   - Database backups
   - Performance tuning
   - Security updates

2. **Troubleshooting**
   - Common error scenarios
   - Log analysis
   - Service recovery procedures
   - Escalation process

3. **Integration Management**
   - Adding new integrations
   - Updating API credentials
   - Testing integration health
   - Synchronization troubleshooting

## Monitoring and Maintenance

### Health Monitoring

1. **Check system health:**

```bash
curl http://localhost:8000/health
```

2. **View logs:**

```bash
# Docker deployment
docker-compose logs -f

# Direct Python deployment
tail -f logs/app.log
```

3. **Monitor resource usage:**

```bash
# Docker deployment
docker stats
```

### Backup Procedures

1. **Backup environment configuration:**

```bash
cp .env .env.backup-$(date +%Y%m%d)
```

2. **Backup Notion data:**
   - Use the Notion API to export database contents
   - Schedule regular exports using the provided backup script

```bash
python -m tools.notion_backup
```

### Maintenance Tasks

1. **Update the system:**

```bash
# Pull latest code
git pull

# Rebuild and restart containers
docker-compose down
docker-compose up -d
```

2. **Rotate API credentials:**

```bash
# Update credentials in .env file
nano .env

# Restart the server to apply changes
docker-compose restart
```

## Troubleshooting

### Common Issues

1. **Connection to Notion fails**
   - Check `NOTION_API_TOKEN` in .env file
   - Verify the integration has access to all pages
   - Check network connectivity to Notion API

2. **Webhook endpoints not receiving data**
   - Verify external services are configured to send to correct URLs
   - Check `WEBHOOK_SECRET` matches in both systems
   - Inspect webhook logs for signature verification failures

3. **Agents not processing events**
   - Check agent registration in Notion
   - Verify workflow templates exist
   - Inspect agent communication logs

### Getting Help

For additional support:

1. Check the documentation in the `docs/` directory
2. Review the GitHub repository issues
3. Contact the development team at support@higherself.network
