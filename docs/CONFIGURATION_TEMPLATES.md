# HigherSelf Network Server - Configuration Templates

## Overview

This document provides ready-to-use configuration templates for implementing external service integrations following the established best practices in the HigherSelf Network Server. These templates are based on the successful VirtualBox deployment and multi-entity production environment.

## Environment Configuration Templates

### Production VM Environment Template

```bash
# .env.vm.production.template
# HigherSelf Network Server - VM Production Configuration

# =============================================================================
# CORE APPLICATION SETTINGS
# =============================================================================
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
TESTING_MODE=false
VM_DEPLOYMENT=true
MULTI_ENTITY_MODE=true

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4

# =============================================================================
# BUSINESS ENTITY CONFIGURATION
# =============================================================================
# Business Priority Order: AM Consulting > The 7 Space > HigherSelf Core
BUSINESS_PRIORITY_ORDER=am_consulting,the_7_space,higherself_core

# Contact Counts
AM_CONSULTING_CONTACTS=1300
THE_7_SPACE_CONTACTS=191
HIGHERSELF_CORE_CONTACTS=1300

# Entity-Specific Database IDs
NOTION_THE7SPACE_CONTACTS_DB=your_the7space_contacts_db_id
NOTION_AMCONSULTING_CONTACTS_DB=your_amconsulting_contacts_db_id
NOTION_HIGHERSELF_CONTACTS_DB=your_higherself_contacts_db_id

# =============================================================================
# EXTERNAL SERVICE INTEGRATIONS
# =============================================================================

# Notion Integration
NOTION_API_TOKEN=secret_from_aws_secrets_manager
NOTION_PARENT_PAGE_ID=your_notion_parent_page_id
NOTION_INTEGRATION_ENABLED=true

# OpenAI Integration
OPENAI_API_KEY=secret_from_aws_secrets_manager
OPENAI_ORGANIZATION_ID=your_openai_org_id
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000

# Email Service Configuration
ENABLE_EMAIL_AUTOMATION=true
EMAIL_PROVIDER=smtp
SMTP_HOST=your_smtp_host
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=secret_from_aws_secrets_manager

# Calendar Integration
ENABLE_CALENDAR_INTEGRATION=true
CALENDAR_PROVIDER=google
GOOGLE_CALENDAR_CLIENT_ID=your_google_calendar_client_id
GOOGLE_CALENDAR_CLIENT_SECRET=secret_from_aws_secrets_manager

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
MONGODB_URI=mongodb://higherself_user:${MONGODB_PASSWORD}@mongodb-vm:27017/higherself_production
MONGODB_DB_NAME=higherself_production
MONGODB_USERNAME=higherself_user
MONGODB_PASSWORD=secret_from_aws_secrets_manager

REDIS_URI=redis://:${REDIS_PASSWORD}@redis-vm:6379/0
REDIS_PASSWORD=secret_from_aws_secrets_manager

# =============================================================================
# MONITORING AND OBSERVABILITY
# =============================================================================
ENABLE_PROMETHEUS=true
ENABLE_GRAFANA=true
ENABLE_CONSUL=true
GRAFANA_ADMIN_PASSWORD=secret_from_aws_secrets_manager

# Consul Configuration
CONSUL_HTTP_ADDR=consul-vm:8500
CONSUL_DATACENTER=higherself-vm

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================
WEBHOOK_SECRET=secret_from_aws_secrets_manager
JWT_SECRET_KEY=secret_from_aws_secrets_manager
ENCRYPTION_KEY=secret_from_aws_secrets_manager

# SSL Configuration
SSL_ENABLED=true
SSL_CERT_PATH=/app/ssl/cert.pem
SSL_KEY_PATH=/app/ssl/key.pem

# =============================================================================
# AWS INTEGRATION
# =============================================================================
AWS_REGION=us-east-1
AWS_SECRETS_MANAGER_ENABLED=true
AWS_SECRET_NAME_PREFIX=higherself-network-server

# =============================================================================
# WORKFLOW AUTOMATION
# =============================================================================
WORKFLOW_AUTOMATION_ENABLED=true
AUTO_TASK_CREATION=true
AUTO_FOLLOWUP_ENABLED=true
LEAD_SCORING_ENABLED=true
LEAD_SCORE_THRESHOLD=75
PRIORITY_THRESHOLD=85

# Response Time Configuration (hours)
THE7SPACE_RESPONSE_TIME=24
AMCONSULTING_RESPONSE_TIME=4
HIGHERSELF_RESPONSE_TIME=12

# =============================================================================
# INTEGRATION PLATFORM SETTINGS
# =============================================================================
# Zapier Integration
ZAPIER_ENABLED=false
ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/YOUR_HOOK_ID/

# N8N Integration
N8N_ENABLED=false
N8N_WEBHOOK_URL=http://YOUR_N8N_DOMAIN:5678/webhook/

# Make.com Integration
MAKE_ENABLED=false
MAKE_WEBHOOK_URL=https://hook.integromat.com/YOUR_HOOK_ID/

# GoHighLevel Integration (disabled for VM deployment)
GOHIGHLEVEL_ENABLED=false
GOHIGHLEVEL_API_KEY=your_ghl_api_key_here
GOHIGHLEVEL_LOCATION_ID=your_ghl_location_id_here
```

### Development Environment Template

```bash
# .env.development.template
# HigherSelf Network Server - Development Configuration

ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
TESTING_MODE=true
VM_DEPLOYMENT=false
MULTI_ENTITY_MODE=false

# Use The 7 Space for development
DEFAULT_BUSINESS_ENTITY=the_7_space
NOTION_THE7SPACE_CONTACTS_DB=your_dev_contacts_db_id

# Simplified integrations for development
NOTION_API_TOKEN=your_dev_notion_token
OPENAI_API_KEY=your_dev_openai_key

# Local database configuration
MONGODB_URI=mongodb://localhost:27017/higherselfnetwork_dev
REDIS_URI=redis://localhost:6379/0

# Disable external services in development
ENABLE_EMAIL_AUTOMATION=false
ENABLE_CALENDAR_INTEGRATION=false
WEBHOOK_SECRET=dev_webhook_secret_123
```

## Docker Compose Templates

### Multi-Entity Production Template

```yaml
# docker-compose.vm.production.yml
version: '3.8'

services:
  higherself-server:
    image: thehigherselfnetworkserver:vm-production
    container_name: higherself-server-vm
    ports:
      - "80:8000"
      - "443:8443"
    environment:
      - RUNNING_IN_CONTAINER=true
      - PYTHONUNBUFFERED=1
      - ENVIRONMENT=production
      - VM_DEPLOYMENT=true
      - MULTI_ENTITY_MODE=true
    env_file:
      - .env.vm.production
    volumes:
      - ./logs/vm:/app/logs
      - ./data/vm:/app/data
      - ./config:/app/config:ro
      - ./ssl:/app/ssl:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 30s
      retries: 5
      start_period: 90s
    restart: unless-stopped
    depends_on:
      mongodb-vm:
        condition: service_healthy
      redis-vm:
        condition: service_healthy
      consul-vm:
        condition: service_healthy
    networks:
      - higherself-vm-network
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=8000"
      - "prometheus.path=/metrics"
      - "vm.deployment=production"
      - "business.entities=the_7_space,am_consulting,higherself_core"
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  mongodb-vm:
    image: mongo:6.0
    container_name: higherself-mongodb-vm
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGODB_ROOT_PASSWORD}
      MONGO_INITDB_DATABASE: higherself_production
    volumes:
      - mongodb_vm_data:/data/db
      - ./scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s
    restart: unless-stopped
    networks:
      - higherself-vm-network
    labels:
      - "vm.service=database"

  redis-vm:
    image: redis:7-alpine
    container_name: higherself-redis-vm
    ports:
      - "6379:6379"
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_vm_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 20s
    restart: unless-stopped
    networks:
      - higherself-vm-network
    labels:
      - "vm.service=cache"

volumes:
  mongodb_vm_data:
    name: higherself_vm_mongodb_data
    driver: local
  redis_vm_data:
    name: higherself_vm_redis_data
    driver: local

networks:
  higherself-vm-network:
    driver: bridge
    name: higherself-vm-network
    ipam:
      config:
        - subnet: 172.20.0.0/16
    labels:
      - "vm.network=production"
      - "business.entities=multi"
```

### Single Entity Development Template

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  the7space-dev:
    image: thehigherselfnetworkserver:dev
    container_name: the7space-dev-app
    ports:
      - "8000:8000"
    environment:
      - RUNNING_IN_CONTAINER=true
      - PYTHONUNBUFFERED=1
      - ENVIRONMENT=development
      - DEFAULT_BUSINESS_ENTITY=the_7_space
    env_file:
      - .env.development
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - .:/app:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    restart: unless-stopped
    depends_on:
      - mongodb-dev
      - redis-dev
    networks:
      - higherself-dev-network
    labels:
      - "dev.entity=the_7_space"
      - "dev.contacts=191"

  mongodb-dev:
    image: mongo:6.0
    container_name: higherself-mongodb-dev
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: higherselfnetwork_dev
    volumes:
      - mongodb_dev_data:/data/db
    networks:
      - higherself-dev-network

  redis-dev:
    image: redis:7-alpine
    container_name: higherself-redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
    networks:
      - higherself-dev-network

volumes:
  mongodb_dev_data:
  redis_dev_data:

networks:
  higherself-dev-network:
    driver: bridge
```

## Terragrunt Configuration Templates

### Secrets Manager Module Template

```hcl
# terragrunt/modules/secrets-manager/terragrunt.hcl
terraform {
  source = "git::https://github.com/gruntwork-io/terraform-aws-secrets-manager.git//modules/secrets-manager?ref=v0.1.0"
}

include "root" {
  path = find_in_parent_folders()
}

inputs = {
  secrets = {
    # Core API Tokens
    notion_api_token = {
      description = "Notion API token for HigherSelf Network Server integration"
      secret_string = get_env("NOTION_API_TOKEN", "")
      recovery_window_in_days = 7
    }
    
    openai_api_key = {
      description = "OpenAI API key for AI services"
      secret_string = get_env("OPENAI_API_KEY", "")
      recovery_window_in_days = 7
    }
    
    # Database Credentials
    mongodb_password = {
      description = "MongoDB password for application database"
      generate_secret_string = {
        password_length = 32
        exclude_characters = "\"@/\\"
      }
      recovery_window_in_days = 30
    }
    
    redis_password = {
      description = "Redis password for caching layer"
      generate_secret_string = {
        password_length = 32
        exclude_characters = "\"@/\\"
      }
      recovery_window_in_days = 30
    }
    
    # Email Service Credentials
    smtp_password = {
      description = "SMTP password for email automation"
      secret_string = get_env("SMTP_PASSWORD", "")
      recovery_window_in_days = 7
    }
    
    # Security Secrets
    webhook_secret = {
      description = "Webhook secret for secure API communications"
      generate_secret_string = {
        password_length = 64
        exclude_characters = "\"@/\\"
      }
      recovery_window_in_days = 7
    }
    
    jwt_secret_key = {
      description = "JWT secret key for authentication"
      generate_secret_string = {
        password_length = 64
        exclude_characters = "\"@/\\"
      }
      recovery_window_in_days = 30
    }
    
    # Monitoring Credentials
    grafana_admin_password = {
      description = "Grafana admin password for monitoring dashboard"
      secret_string = get_env("GRAFANA_ADMIN_PASSWORD", "")
      recovery_window_in_days = 30
    }
  }
}
```

These templates provide a solid foundation for implementing and deploying external service integrations following the proven patterns established in the HigherSelf Network Server production environment.
