# HigherSelf Network Server - Comprehensive Deployment Guide

## Overview

This guide provides complete instructions for deploying The HigherSelf Network Server enterprise automation platform across all environments (development, staging, production) with full Docker orchestration, Terragrunt infrastructure management, and multi-business entity support.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Environment Setup](#environment-setup)
4. [Infrastructure Deployment](#infrastructure-deployment)
5. [Application Deployment](#application-deployment)
6. [Service Configuration](#service-configuration)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Business Entity Configuration](#business-entity-configuration)
9. [External Services Integration](#external-services-integration)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Docker** (v20.10+) and **Docker Compose** (v2.0+)
- **Terraform** (v1.0+) and **Terragrunt** (v0.45+)
- **AWS CLI** (v2.0+) - for production deployments
- **Git** (v2.30+)
- **Node.js** (v18+) - for development tools
- **Python** (v3.9+) - for application runtime

### Required Accounts & API Keys

- **Notion API Token** - For workspace integration
- **OpenAI API Key** - For AI-powered features
- **AWS Account** - For production infrastructure (optional for dev)
- **SMTP Credentials** - For email notifications
- **Domain Names** - For production deployment

## Quick Start

### 1. Clone and Initialize

```bash
# Clone the repository
git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git
cd The-HigherSelf-Network-Server

# Initialize volumes and directory structure
./scripts/init-volumes.sh development

# Set up environment configuration
cp .env.development.template .env.development
# Edit .env.development with your actual API keys and configuration
```

### 2. Configure Environment

```bash
# Use the environment management script
./scripts/manage-environments.sh switch development
./scripts/manage-environments.sh validate development
```

### 3. Deploy with Docker

```bash
# Option 1: Standard Docker Compose
docker-compose up -d

# Option 2: Environment-specific deployment
./scripts/docker-terragrunt-deploy.sh development deploy all

# Option 3: Manual step-by-step
./scripts/manage-environments.sh setup development
```

### 4. Verify Deployment

```bash
# Check service health
./scripts/health-check.sh all console

# Test external services
./scripts/external-services.sh status all

# Monitor network status
./scripts/network-manager.sh status all
```

## Environment Setup

### Development Environment

```bash
# 1. Initialize development environment
./scripts/init-volumes.sh development

# 2. Configure environment variables
cp .env.development .env
# Edit .env with your development API keys

# 3. Start services
docker-compose up -d

# 4. Verify health
curl http://localhost:8000/health
```

### Staging Environment

```bash
# 1. Switch to staging
./scripts/manage-environments.sh switch staging

# 2. Deploy infrastructure (if using Terragrunt)
cd terragrunt/environments/staging
terragrunt run-all apply

# 3. Deploy application
./scripts/docker-terragrunt-deploy.sh staging deploy all

# 4. Run integration tests
./scripts/health-check.sh detailed json
```

### Production Environment

```bash
# 1. Configure AWS credentials
aws configure

# 2. Deploy secrets management
cd terragrunt/modules/secrets-manager
terragrunt apply

# 3. Deploy full infrastructure
./scripts/docker-terragrunt-deploy.sh production deploy all

# 4. Verify production deployment
./scripts/health-check.sh all console
./scripts/external-services.sh validate all
```

## Infrastructure Deployment

### Using Terragrunt (Recommended)

```bash
# 1. Navigate to environment directory
cd terragrunt/environments/production

# 2. Initialize Terragrunt
terragrunt run-all init

# 3. Plan deployment
terragrunt run-all plan

# 4. Apply infrastructure
terragrunt run-all apply

# 5. Verify deployment
terragrunt run-all show
```

### Using Docker Compose Only

```bash
# 1. Create networks
./scripts/network-manager.sh create all

# 2. Initialize volumes
./scripts/init-volumes.sh production

# 3. Deploy services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. Verify deployment
docker-compose ps
```

## Application Deployment

### Multi-Environment Deployment

```bash
# Development
./scripts/docker-terragrunt-deploy.sh development deploy containers

# Staging
./scripts/docker-terragrunt-deploy.sh staging deploy containers

# Production
./scripts/docker-terragrunt-deploy.sh production deploy containers
```

### Service-Specific Deployment

```bash
# Deploy only infrastructure
./scripts/docker-terragrunt-deploy.sh production infrastructure

# Deploy only secrets
./scripts/docker-terragrunt-deploy.sh production secrets

# Deploy only monitoring
./scripts/docker-terragrunt-deploy.sh production monitoring
```

## Service Configuration

### Core Services

1. **HigherSelf Server** (Main Application)
   - Port: 8000 (HTTP), 8443 (HTTPS)
   - Health: `/health`
   - API Docs: `/docs`

2. **MongoDB** (Primary Database)
   - Port: 27017 (internal)
   - Health: MongoDB ping command
   - Backup: Automated daily

3. **Redis** (Cache & Message Broker)
   - Port: 6379 (internal)
   - Health: Redis ping command
   - Persistence: AOF + RDB

4. **Consul** (Service Discovery)
   - Port: 8500 (internal)
   - UI: Available in development
   - Health: Consul members

### Monitoring Services

1. **Prometheus** (Metrics Collection)
   - Port: 9090 (internal)
   - Retention: Environment-specific
   - Targets: All services

2. **Grafana** (Visualization)
   - Port: 3000 (internal)
   - Default Login: admin/admin (dev)
   - Dashboards: Pre-configured

3. **Nginx** (Reverse Proxy)
   - Ports: 80 (HTTP), 443 (HTTPS)
   - Load Balancing: Round-robin
   - SSL: Production only

## Monitoring & Health Checks

### Automated Health Monitoring

```bash
# Comprehensive health check
./scripts/health-check.sh all detailed

# Service-specific checks
./scripts/health-check.sh core console
./scripts/health-check.sh monitoring json

# Continuous monitoring
watch -n 30 './scripts/health-check.sh quick console'
```

### Manual Health Verification

```bash
# Application health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/database

# External services health
curl http://localhost:8000/health/external

# Business entities health
curl http://localhost:8000/health/entities
```

### Performance Monitoring

```bash
# Network performance
./scripts/network-manager.sh monitor

# Service performance
./scripts/health-check.sh detailed html > health-report.html

# External services performance
./scripts/external-services.sh benchmark all
```

## Business Entity Configuration

### The 7 Space (191 contacts)

```bash
# Configure Notion workspace
export THE_7_SPACE_NOTION_WORKSPACE="your_workspace_id"
export THE_7_SPACE_CONTACTS_DB="your_contacts_db_id"

# Test entity-specific endpoints
curl -H "X-Business-Entity: the_7_space" http://localhost:8000/health
```

### A.M. Consulting (1,300 contacts)

```bash
# Configure Notion workspace
export AM_CONSULTING_NOTION_WORKSPACE="your_workspace_id"
export AM_CONSULTING_CONTACTS_DB="your_contacts_db_id"

# Test entity-specific endpoints
curl -H "X-Business-Entity: am_consulting" http://localhost:8000/health
```

### HigherSelf Core (1,300 contacts)

```bash
# Configure Notion workspace
export HIGHERSELF_CORE_NOTION_WORKSPACE="your_workspace_id"
export HIGHERSELF_CORE_CONTACTS_DB="your_contacts_db_id"

# Test entity-specific endpoints
curl -H "X-Business-Entity: higherself_core" http://localhost:8000/health
```

## External Services Integration

### Notion API Setup

```bash
# 1. Configure API token
export NOTION_API_TOKEN="secret_your_token_here"

# 2. Test connectivity
./scripts/external-services.sh test notion

# 3. Validate database access
./scripts/external-services.sh validate notion
```

### OpenAI API Setup

```bash
# 1. Configure API key
export OPENAI_API_KEY="your_openai_api_key"

# 2. Test connectivity
./scripts/external-services.sh test openai

# 3. Benchmark performance
./scripts/external-services.sh benchmark openai
```

### SMTP Configuration

```bash
# 1. Configure SMTP settings
export SMTP_HOST="smtp.gmail.com"
export SMTP_USERNAME="your_email@gmail.com"
export SMTP_PASSWORD="your_app_password"

# 2. Test email service
./scripts/external-services.sh test smtp
```

## Backup & Recovery

### Automated Backups

```bash
# Configure backup schedule
./scripts/volume-backup.sh backup all full

# List available backups
./scripts/volume-backup.sh list

# Verify backup integrity
./scripts/volume-backup.sh verify latest
```

### Manual Backup

```bash
# Backup specific service
./scripts/volume-backup.sh backup mongodb full

# Backup with custom location
BACKUP_LOCATION=s3://my-backup-bucket ./scripts/volume-backup.sh backup all full
```

## Troubleshooting

### Common Issues

1. **Container Health Check Failures**
   ```bash
   # Check container logs
   docker-compose logs higherself-server
   
   # Restart unhealthy services
   docker-compose restart higherself-server
   
   # Full health diagnosis
   ./scripts/health-check.sh detailed console
   ```

2. **Network Connectivity Issues**
   ```bash
   # Test network connectivity
   ./scripts/network-manager.sh test all
   
   # Recreate networks
   ./scripts/network-manager.sh remove all
   ./scripts/network-manager.sh create all
   ```

3. **External Service Connection Problems**
   ```bash
   # Troubleshoot connections
   ./scripts/external-services.sh troubleshoot
   
   # Validate credentials
   ./scripts/external-services.sh validate all
   ```

4. **Volume and Data Issues**
   ```bash
   # Reinitialize volumes
   ./scripts/init-volumes.sh development true
   
   # Check volume status
   docker volume ls
   docker volume inspect higherself-network-server_mongodb_data_dev
   ```

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart with debug mode
docker-compose down
docker-compose up -d

# View debug logs
docker-compose logs -f higherself-server
```

### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check network performance
./scripts/network-manager.sh monitor

# Benchmark external services
./scripts/external-services.sh benchmark all
```

## Next Steps

1. **Configure your specific API keys** in the environment files
2. **Set up Notion databases** using the provided database IDs
3. **Configure domain names** for production deployment
4. **Set up monitoring alerts** for production environments
5. **Configure automated backups** for production data
6. **Review security settings** for production deployment

## Support

For additional support:
- Review the [Environment Setup Guide](./ENVIRONMENT_SETUP_GUIDE.md)
- Check the [Terraform Integration Guide](./TERRAFORM_INTEGRATION_GUIDE.md)
- Consult the [API Documentation](./API_DOCUMENTATION.md)
- Review service logs: `docker-compose logs -f [service-name]`
