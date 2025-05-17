# The HigherSelf Network Server Deployment Guide

This guide provides comprehensive instructions for deploying The HigherSelf Network Server beyond just updating your ENV file with credentials.

## Table of Contents

- [Notion Integration Setup](#notion-integration-setup)
- [Database Setup](#database-setup)
- [MCP Tools & Services](#mcp-tools--services)
- [SSL Certificate Setup](#ssl-certificate-setup)
- [Third-Party API Credentials](#third-party-api-credentials)
- [Server Configuration](#server-configuration)
- [Monitoring Setup](#monitoring-setup)
- [Deployment Options](#deployment-options)
- [Directory Structure Requirements](#directory-structure-requirements)
- [Security Considerations](#security-considerations)
- [Summary of Deployment Process](#summary-of-deployment-process)

## Notion Integration Setup

**Critical Steps:**

- Create a Notion integration at <https://www.notion.so/my-integrations>
- Obtain a Notion API token with appropriate permissions
- Create a parent page in your Notion workspace where databases will be created
- Share the parent page with your integration (add the integration to the page)
- Set `NOTION_API_TOKEN` and `NOTION_PARENT_PAGE_ID` in your `.env` file

## Database Setup

### Notion Database Setup

```bash
# Using Docker
docker-compose build windsurf-agent
docker-compose run --rm windsurf-agent python -m tools.notion_db_setup

# Using Python directly
python -m tools.notion_db_setup
```

This will create 16 interconnected databases in your Notion workspace and update your `.env` file with their IDs. After running this, you need to:

```bash
# Add the generated database IDs to your .env file
cat .env.notion >> .env
```

### Supabase Database Setup (Optional but Recommended)

- Ensure you have a Supabase project set up
- Configure Supabase environment variables in your `.env` file:

  ```
  SUPABASE_URL=https://mmmtfmulvmvtxybwxxrr.supabase.co
  SUPABASE_API_KEY=your_supabase_api_key
  SUPABASE_PROJECT_ID=mmmtfmulvmvtxybwxxrr
  ```

- Run the Supabase database setup script:

  ```bash
  python -m tools.supabase_db_setup
  ```

- Perform initial synchronization:

  ```bash
  python -m tools.sync_databases --direction notion_to_supabase
  ```

### MongoDB & Redis Setup

Our system uses MongoDB for agent state and analytics, and Redis for caching:

- Both services are included in the Docker Compose setup
- For custom MongoDB setup, configure these environment variables:

  ```
  MONGODB_URI=mongodb://username:password@localhost:27017
  MONGODB_DB_NAME=higherselfnetwork
  ```

- For custom Redis setup:

  ```
  REDIS_URI=redis://localhost:6379/0
  REDIS_PASSWORD=your_redis_password
  ```

- Initialize MongoDB collections:

  ```bash
  # Using Docker
  docker-compose run --rm windsurf-agent python -m tools.mongo_db_setup
  
  # Directly
  python -m tools.mongo_db_setup
  ```

## SSL Certificate Setup

For secure deployment, you'll need SSL certificates:

```bash
# Create directory for SSL certificates
mkdir -p deployment/ssl
```

Options:

1. **Use existing certificates:**
   - Place your certificates in `deployment/ssl/fullchain.pem` and `deployment/ssl/privkey.pem`

2. **Generate with Let's Encrypt:**

   ```bash
   sudo certbot certonly --standalone -d agent-api.thehigherselfnetwork.com
   sudo cp /etc/letsencrypt/live/agent-api.thehigherselfnetwork.com/fullchain.pem deployment/ssl/
   sudo cp /etc/letsencrypt/live/agent-api.thehigherselfnetwork.com/privkey.pem deployment/ssl/
   sudo chmod -R 755 deployment/ssl/
   ```

## MCP Tools & Services

The Higher Self Network Server now includes a comprehensive MCP (Model Context Protocol) tools integration system:

### Available MCP Tools

1. **Memory Tool**: Agent memory storage and retrieval
2. **Web Browser Tool**: Web searching and content extraction
3. **Perplexity Tool**: Advanced question-answering with citations

### Service Mesh Configuration

We use Consul for service discovery and registration:

```
# Consul configuration
CONSUL_HTTP_ADDR=localhost:8500
CONSUL_DATACENTER=dc1
```

### Tool Registration & Usage

To register a custom MCP tool:

```python
from integrations.mcp_tools import mcp_tools_registry, MCPTool, ToolMetadata, ToolCapability

# Create tool metadata
metadata = ToolMetadata(
    name="your_tool_name",
    description="Your tool description",
    version="1.0.0",
    capabilities=[ToolCapability.SEARCH],
    # ... other metadata
)

# Create and register the tool
your_tool = MCPTool(
    metadata=metadata,
    handler=your_handler_function,
    is_async=True
)

# Register with registry
mcp_tools_registry.register_tool(your_tool)
```

For testing MCP tools via API:

```bash
curl -X POST http://localhost:8000/api/mcp_tools/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer AGENT_TOKEN" \
  -d '{"tool_name": "memory", "parameters": {"operation": "create", "content": "Test memory"}}'
```

## Third-Party API Credentials

Configure all required third-party API credentials in your `.env` file:

- **Core Services:**
  - HubSpot, TypeForm, Airtable, Amelia, WooCommerce

- **Community & Content Platforms:**
  - Circle.so, Beehiiv

- **AI & Development:**
  - Hugging Face, OpenAI, Anthropic
  - Perplexity, Google Search API

Example configuration:

```
# HubSpot
HUBSPOT_API_KEY=your_hubspot_api_key

# Circle.so Community Platform
CIRCLE_API_TOKEN=your_circle_api_token
CIRCLE_COMMUNITY_ID=your_circle_community_id

# AI Router Configuration
AI_ROUTER_DEFAULT_PROVIDER=openai
AI_ROUTER_DEFAULT_MODEL=gpt-4

# MCP Tools API Keys
PERPLEXITY_API_KEY=your_perplexity_api_key
SEARCH_API_KEY=your_google_search_api_key
SEARCH_ENGINE_ID=your_google_custom_search_engine_id
```

## Server Configuration

Set these essential server configuration variables in your `.env` file:

```
LOG_LEVEL=INFO
SERVER_PORT=8000
WEBHOOK_SECRET=your_webhook_secret_here

# Service URIs (if using custom infrastructure)
MONGODB_URI=mongodb://username:password@localhost:27017
REDIS_URI=redis://localhost:6379/0
CONSUL_HTTP_ADDR=localhost:8500
```

For testing/development:

```
TEST_MODE=false
DISABLE_WEBHOOKS=true
```

## Monitoring Setup

The system comes with built-in monitoring using Prometheus and Grafana:

### Accessing Monitoring Dashboards

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
  - Default login: admin / admin

### Available Dashboards

- **Agent Performance**: Agent task execution metrics and errors
- **MCP Tools Usage**: Tool usage statistics and performance
- **System Health**: CPU, memory, and network utilization

### Custom Metrics

To add custom metrics to your code:

```python
from prometheus_client import Counter, Histogram

YOUR_COUNTER = Counter('metric_name', 'Metric description', ['label1', 'label2'])
YOUR_COUNTER.labels(label1="value1", label2="value2").inc()
```

## Deployment Options

### Docker Deployment (Recommended)

1. Build and start containers:

   ```bash
   # For development
   docker-compose up -d
   # OR
   ./deploy.sh --env dev --build
   
   # For staging
   docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
   # OR
   ./deploy.sh --env staging --build
   
   # For production
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   # OR
   ./deploy.sh --env prod --build
   ```

2. Verify deployment:

   ```bash
   docker-compose ps
   docker-compose logs -f windsurf-agent
   curl http://localhost:8000/health
   ```

3. Deployed services include:

   - **Core Application**: FastAPI application server
   - **Celery Workers**: Background task processors
   - **MongoDB**: Document database for agent state and analytics
   - **Redis**: Caching and message broker
   - **Prometheus**: Metrics collection
   - **Grafana**: Metrics visualization
   - **Consul**: Service discovery and configuration

### Traditional Deployment

1. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up systemd service (for Linux servers):

   ```bash
   sudo cp deployment/windsurf-agent.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable windsurf-agent
   sudo systemctl start windsurf-agent
   ```

4. Set up Nginx as a reverse proxy:

   ```bash
   sudo cp deployment/nginx.conf /etc/nginx/sites-available/windsurf-agent.conf
   sudo ln -s /etc/nginx/sites-available/windsurf-agent.conf /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Directory Structure Requirements

Ensure these directories exist and have proper permissions:

```bash
mkdir -p logs
mkdir -p data
```

If using Docker, these are mounted as volumes.

## Security Considerations

- Restrict permissions on your `.env` file: `chmod 600 .env`
- Never commit `.env` to version control
- Use strong, unique values for `WEBHOOK_SECRET`
- Consider using Docker secrets for production deployments
- Ensure proper firewall rules are in place
- Regularly update dependencies and apply security patches

## Summary of Deployment Process

1. **Setup Environment:**
   - Clone repository
   - Copy `.env.example` to `.env`
   - Configure all required environment variables

2. **Initialize Databases:**
   - Run Notion database setup
   - (Optional) Run Supabase database setup and sync
   - Set up MongoDB collections
   - Configure Redis for caching

3. **Configure SSL (for production):**
   - Set up SSL certificates
   - Configure Nginx

4. **Deploy:**
   - Choose Docker or traditional deployment
   - Start all services (core app, Celery, MongoDB, Redis, Prometheus, Grafana, Consul)
   - Verify deployment

5. **Setup MCP Tools:**
   - Configure necessary API keys
   - Verify tool registration and availability

6. **Monitor:**
   - Check logs
   - Test API endpoints
   - View Grafana dashboards

## Troubleshooting

### Common Issues

1. **Database Setup Failures:**
   - Ensure Notion API token has sufficient permissions
   - Verify the parent page ID is correct
   - Check that the integration has been added to the parent page

2. **Container Startup Issues:**
   - Check Docker logs: `docker-compose logs -f`
   - Verify all required environment variables are set
   - Ensure ports are not already in use

3. **API Connection Problems:**
   - Verify third-party API credentials
   - Check network connectivity
   - Review firewall settings

### Viewing Logs

```bash
# Docker deployment
docker-compose logs -f windsurf-agent

# Traditional deployment
sudo journalctl -u windsurf-agent -f
```

## Maintenance

### Updating the Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart containers (Docker)
docker-compose down
docker-compose build
docker-compose up -d

# Update dependencies (Traditional)
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart windsurf-agent
```

### Backup Procedures

Regularly backup your:

- `.env` file
- Notion databases (export from Notion UI)
- Supabase database (if used)
- SSL certificates
