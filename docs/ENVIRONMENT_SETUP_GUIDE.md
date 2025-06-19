# HigherSelf Network Server - Environment Setup Guide

## Overview

This guide covers the comprehensive environment configuration system for The HigherSelf Network Server enterprise automation platform. The system supports three business entities (The 7 Space, A.M. Consulting, and HigherSelf Core) across multiple deployment environments.

## Environment Structure

### Available Environments

1. **Development** (`development`)
   - Local development with hot reload
   - Simplified secrets management
   - Debug logging enabled
   - All business entities enabled for testing

2. **Staging** (`staging`)
   - Pre-production testing environment
   - Production-like configuration
   - Performance and load testing enabled
   - Vault-based secrets management

3. **Production** (`production`)
   - Live deployment environment
   - AWS Secrets Manager integration
   - Enterprise security features
   - High availability configuration

## Quick Start

### 1. Environment Management Script

Use the provided environment management script for easy switching:

```bash
# Make script executable (if not already)
chmod +x scripts/manage-environments.sh

# Switch to development environment
./scripts/manage-environments.sh switch development

# Validate environment configuration
./scripts/manage-environments.sh validate development

# Set up environment with Docker
./scripts/manage-environments.sh setup development

# Check environment status
./scripts/manage-environments.sh status
```

### 2. Manual Environment Setup

#### Development Environment

```bash
# Copy and configure development environment
cp .env.development .env

# Edit the file with your actual values
nano .env

# Required changes:
# - NOTION_API_TOKEN: Your Notion integration token
# - OPENAI_API_KEY: Your OpenAI API key
# - MONGODB_PASSWORD: Choose a secure password
# - All NOTION_*_DB variables: Your Notion database IDs

# Start development environment
docker-compose up -d
```

#### Staging Environment

```bash
# Copy and configure staging environment
cp .env.staging .env

# Edit with staging-specific values
nano .env

# Start staging environment
docker-compose -f docker-compose.yml up -d
```

#### Production Environment

```bash
# Production uses AWS Secrets Manager
# Configure secrets first using Terragrunt
cd terragrunt/modules/secrets-manager
terragrunt apply

# Copy production environment template
cp .env.production .env

# Start production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Environment Configuration Details

### Business Entity Configuration

Each environment supports multi-entity configuration:

```bash
# Multi-entity mode
MULTI_ENTITY_MODE=true
BUSINESS_ENTITY_ISOLATION=true

# Primary entity (determines priority)
PRIMARY_BUSINESS_ENTITY=the_7_space  # or am_consulting, higherself_core

# Entity enablement
THE_7_SPACE_ENABLED=true
AM_CONSULTING_ENABLED=true
HIGHERSELF_CORE_ENABLED=true
```

### Database Configuration

Environment-specific database settings:

```bash
# Development
MONGODB_DB_NAME=higherself_dev
MONGODB_CACHE_SIZE=1

# Staging
MONGODB_DB_NAME=higherself_staging
MONGODB_CACHE_SIZE=2

# Production
MONGODB_DB_NAME=higherself_production
MONGODB_CACHE_SIZE=4
```

### Secrets Management

#### Development
- Uses environment files (`.env.development`)
- Simple password-based authentication
- Local Vault instance (optional)

#### Staging
- Vault-based secrets management
- Encrypted secrets at rest
- Secrets rotation enabled

#### Production
- AWS Secrets Manager integration
- Enterprise-grade encryption
- Automated secrets rotation
- Compliance logging

## Docker Compose Configuration

### File Structure

```
docker-compose.yml              # Base configuration
docker-compose.override.yml     # Development overrides (auto-loaded)
docker-compose.prod.yml         # Production overrides
docker-compose.unified.yml      # Complete unified configuration
```

### Environment-Specific Deployment

```bash
# Development (uses override automatically)
docker-compose up -d

# Staging
ENVIRONMENT=staging docker-compose up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Service Configuration

### Core Services

1. **higherself-server**: Main application
2. **celery-worker**: Background task processing
3. **celery-beat**: Task scheduling
4. **mongodb**: Primary database
5. **redis**: Cache and message broker
6. **consul**: Service discovery
7. **nginx**: Reverse proxy
8. **prometheus**: Metrics collection
9. **grafana**: Monitoring dashboard
10. **vault**: Secrets management (optional)

### Health Checks

All services include comprehensive health checks:

```bash
# Check application health
curl http://localhost:8000/health

# Check individual service health
docker-compose ps
```

## Notion Integration Setup

### Required Notion Databases

Each environment needs these Notion databases configured:

1. **Core Operational Databases**
   - Business Entities Registry
   - Contacts & Profiles
   - Community Hub
   - Products & Services
   - Active Workflow Instances
   - Marketing Campaigns
   - Feedback & Surveys
   - Rewards & Bounties
   - Master Tasks

2. **Agent & System Support Databases**
   - Agent Communication Patterns
   - Agent Registry
   - API Integrations Catalog
   - Data Transformations Registry
   - Notifications Templates
   - Use Cases Library
   - Workflows Library

### Database ID Configuration

```bash
# Set in your environment file
NOTION_BUSINESS_ENTITIES_DB=your_database_id_here
NOTION_CONTACTS_PROFILES_DB=your_database_id_here
# ... (continue for all databases)
```

## External Service Integration

### Required API Keys

Configure these in your environment file:

```bash
# Core Services
NOTION_API_TOKEN=secret_your_token_here
OPENAI_API_KEY=your_openai_api_key

# Optional Services
HUGGINGFACE_API_KEY=your_huggingface_api_key
SOFTR_API_KEY=your_softr_api_key
STRIPE_API_KEY=your_stripe_api_key
```

### SMTP Configuration

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@domain.com
SMTP_PASSWORD=your_email_password
SMTP_USE_TLS=true
```

### Cloud Storage

```bash
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-storage-bucket
```

## Monitoring and Logging

### Log Configuration

```bash
# Development
JSON_LOGS=false
LOG_LEVEL=DEBUG
LOG_FILE=./logs/dev/application.log

# Production
JSON_LOGS=true
LOG_LEVEL=INFO
ENABLE_AUDIT_LOGGING=true
```

### Monitoring Stack

- **Prometheus**: Metrics collection (port 9090)
- **Grafana**: Visualization (port 3000)
- **Application logs**: Structured JSON logging
- **Health checks**: Automated service monitoring

## Troubleshooting

### Common Issues

1. **Environment file not found**
   ```bash
   # Create symlink to current environment
   ln -s .env.development .env
   ```

2. **Docker secrets not found (production)**
   ```bash
   # Deploy secrets using Terragrunt
   cd terragrunt/modules/secrets-manager
   terragrunt apply
   ```

3. **Service health check failures**
   ```bash
   # Check service logs
   docker-compose logs higherself-server
   
   # Restart unhealthy services
   docker-compose restart higherself-server
   ```

4. **Database connection issues**
   ```bash
   # Check MongoDB status
   docker-compose exec mongodb mongosh
   
   # Check Redis status
   docker-compose exec redis redis-cli ping
   ```

### Environment Validation

```bash
# Validate current environment
./scripts/manage-environments.sh validate development

# Check Docker Compose configuration
docker-compose config

# Test application health
curl -f http://localhost:8000/health
```

## Security Considerations

### Development
- Use test API keys only
- Simple passwords acceptable
- Debug endpoints enabled

### Staging
- Production-like security
- Encrypted secrets
- Security scanning enabled

### Production
- Enterprise-grade security
- AWS Secrets Manager
- Compliance logging
- Intrusion detection
- Rate limiting

## Next Steps

1. **Configure your environment file** with actual API keys and database IDs
2. **Set up Notion databases** using the provided scripts
3. **Deploy using Docker Compose** with your chosen environment
4. **Configure monitoring** and alerting for production
5. **Set up automated backups** for production data

For detailed deployment instructions, see:
- [Docker Deployment Guide](./deployment/DOCKER_DEPLOYMENT.md)
- [Terragrunt Integration Guide](./TERRAFORM_INTEGRATION_GUIDE.md)
- [Secrets Management Guide](./SECRETS_MANAGEMENT_GUIDE.md)
