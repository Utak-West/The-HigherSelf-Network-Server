# The HigherSelf Network Server Deployment Guide

This guide provides comprehensive instructions for deploying The HigherSelf Network Server beyond just updating your ENV file with credentials.

## Table of Contents

- [Notion Integration Setup](#notion-integration-setup)
- [Database Setup](#database-setup)
- [SSL Certificate Setup](#ssl-certificate-setup)
- [Third-Party API Credentials](#third-party-api-credentials)
- [Server Configuration](#server-configuration)
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

## Third-Party API Credentials

Configure all required third-party API credentials in your `.env` file:

- **Core Services:**
  - HubSpot, TypeForm, Airtable, Amelia, WooCommerce

- **Community & Content Platforms:**
  - Circle.so, Beehiiv

- **AI & Development:**
  - Hugging Face, OpenAI, Anthropic
  - Softr, MoneyPrinterTurbo

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
```

## Server Configuration

Set these essential server configuration variables in your `.env` file:

```
LOG_LEVEL=INFO
SERVER_PORT=8000
WEBHOOK_SECRET=your_webhook_secret_here
```

For testing/development:

```
TEST_MODE=false
DISABLE_WEBHOOKS=true
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

3. **Configure SSL (for production):**
   - Set up SSL certificates
   - Configure Nginx

4. **Deploy:**
   - Choose Docker or traditional deployment
   - Start services
   - Verify deployment

5. **Monitor:**
   - Check logs
   - Test API endpoints

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
