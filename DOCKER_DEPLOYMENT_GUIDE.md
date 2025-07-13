# Higher Self Network Server - Complete Docker Deployment Guide

## Overview

This comprehensive guide addresses all critical issues identified in the Higher Self Network Server analysis and provides production-ready Docker deployment configurations.

## Critical Issues Addressed

### ✅ Resolved Issues
- **Redis Connection Failures:** Proper Redis Cloud configuration
- **Missing Dependencies:** Complete dependency installation in Docker image
- **Environment Variable Loading:** Proper .env file handling in containers
- **Pydantic V2 Compatibility:** Updated configurations
- **Service Integration:** Complete orchestration setup

## Prerequisites

### System Requirements
- **Docker:** 20.10+ with Docker Compose V2
- **Memory:** 8GB RAM minimum, 16GB recommended
- **Storage:** 50GB available space
- **CPU:** 4 cores minimum, 8 cores recommended

### Required Credentials
- Notion API Token with database access
- Redis Cloud connection string and password
- Supabase project URL and API keys
- OpenAI/Anthropic API keys
- Linear API token (optional)

## Quick Start

### 1. Environment Setup
```bash
# Clone repository
git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git
cd The-HigherSelf-Network-Server

# Copy environment template
cp .env.example .env.production

# Edit production environment variables
nano .env.production
```

### 2. Critical Configuration Updates

#### Redis Configuration Fix
```bash
# In .env.production, ensure Redis Cloud configuration:
REDIS_URI=redis://redis-18441.c280.us-central1-2.gce.redns.redis-cloud.com:18441
REDIS_PASSWORD=your_redis_cloud_password
REDIS_SSL=true
REDIS_TIMEOUT=10
REDIS_MAX_CONNECTIONS=20
```

#### Supabase Configuration
```bash
# Reactivate Supabase project and configure:
SUPABASE_URL=https://mmmtfmulvmvtxybwxxrr.supabase.co
SUPABASE_API_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 3. Production Deployment
```bash
# Build and deploy production environment
docker-compose -f docker-compose.production.yml up -d

# Verify deployment
docker-compose -f docker-compose.production.yml ps
docker-compose -f docker-compose.production.yml logs -f
```

## Docker Configuration Files

### Production Docker Compose
The production configuration includes:
- **Multi-stage builds** for optimized images
- **Health checks** for all services
- **Proper networking** between containers
- **Volume management** for persistent data
- **Security hardening** with non-root users

### Development Environment
```bash
# Start development environment
docker-compose -f docker-compose.development.yml up -d

# Access development logs
docker-compose -f docker-compose.development.yml logs -f higherself-server
```

### Staging Environment
```bash
# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# Run integration tests
docker-compose -f docker-compose.staging.yml exec higherself-server python -m pytest tests/integration/
```

## Service Architecture

### Container Services
1. **higherself-server** - Main FastAPI application
2. **redis** - Redis Cloud proxy (development only)
3. **mongodb** - Document database
4. **neo4j** - Knowledge graph database
5. **nginx** - Reverse proxy and load balancer
6. **prometheus** - Metrics collection
7. **grafana** - Monitoring dashboard

### Network Configuration
- **higherself-network** - Internal container communication
- **monitoring-network** - Isolated monitoring stack
- **external-network** - External service access

## Critical Issue Resolutions

### 1. Redis Connection Fix
```yaml
# Environment variables properly loaded before Redis initialization
environment:
  - REDIS_URI=${REDIS_URI}
  - REDIS_PASSWORD=${REDIS_PASSWORD}
  - REDIS_SSL=${REDIS_SSL}
depends_on:
  - redis-health-check
```

### 2. Missing Dependencies Resolution
```dockerfile
# All critical dependencies included in Dockerfile
RUN pip install --no-cache-dir \
    pymongo==4.6.1 \
    motor==3.3.2 \
    celery==5.3.4 \
    python-consul==1.1.0 \
    pytesseract==0.3.10 \
    google-cloud-vision==3.4.5
```

### 3. Environment Variable Loading
```dockerfile
# Proper environment loading in container startup
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]
```

## Health Checks and Monitoring

### Application Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Service Dependencies
```yaml
depends_on:
  redis:
    condition: service_healthy
  mongodb:
    condition: service_healthy
  neo4j:
    condition: service_healthy
```

## Security Configuration

### Non-Root User Setup
```dockerfile
# Create non-root user
RUN groupadd -r higherself && useradd -r -g higherself higherself
USER higherself
```

### Secrets Management
```yaml
secrets:
  notion_api_token:
    external: true
  redis_password:
    external: true
  openai_api_key:
    external: true
```

## Deployment Commands

### Production Deployment
```bash
# 1. Prepare environment
./scripts/prepare-production.sh

# 2. Deploy services
docker-compose -f docker-compose.production.yml up -d

# 3. Verify deployment
./scripts/verify-deployment.sh

# 4. Run health checks
./scripts/health-check.sh
```

### Scaling Commands
```bash
# Scale application instances
docker-compose -f docker-compose.production.yml up -d --scale higherself-server=3

# Scale worker processes
docker-compose -f docker-compose.production.yml up -d --scale celery-worker=5
```

## Troubleshooting

### Common Issues

#### Redis Connection Failures
```bash
# Check Redis connectivity
docker-compose exec higherself-server python -c "
import redis
import os
r = redis.from_url(os.getenv('REDIS_URI'), password=os.getenv('REDIS_PASSWORD'))
print(r.ping())
"
```

#### Missing Dependencies
```bash
# Verify all dependencies installed
docker-compose exec higherself-server pip list | grep -E "(pymongo|motor|celery)"
```

#### Environment Variables
```bash
# Check environment loading
docker-compose exec higherself-server env | grep -E "(REDIS|NOTION|SUPABASE)"
```

### Log Analysis
```bash
# Application logs
docker-compose logs -f higherself-server

# Redis connection logs
docker-compose logs redis

# System resource usage
docker stats
```

## Performance Optimization

### Resource Limits
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

### Caching Strategy
```yaml
volumes:
  - redis_data:/data
  - app_cache:/app/cache
```

## Backup and Recovery

### Database Backups
```bash
# MongoDB backup
docker-compose exec mongodb mongodump --out /backup/mongodb

# Neo4j backup
docker-compose exec neo4j neo4j-admin backup --to=/backup/neo4j
```

### Application State Backup
```bash
# Backup application data
docker-compose exec higherself-server python scripts/backup_application_state.py
```

## Next Steps

1. **Deploy to staging environment** for testing
2. **Run integration tests** to verify all services
3. **Configure monitoring alerts** for production
4. **Set up automated backups** and disaster recovery
5. **Implement CI/CD pipeline** for automated deployments

This guide provides a complete solution for deploying the Higher Self Network Server with all critical issues resolved and production-ready configurations.

## 📋 **DEPLOYMENT FILES CREATED**

### Core Docker Configuration
- **`Dockerfile.production`** - Multi-stage production Docker image with all dependencies
- **`docker-compose.production.yml`** - Production environment orchestration
- **`docker-compose.development.yml`** - Development environment with debugging tools
- **`docker-compose.staging.yml`** - Staging environment with testing capabilities
- **`docker-entrypoint.sh`** - Critical environment loading and health check script

### Deployment Scripts
- **`scripts/deploy-production.sh`** - Automated production deployment with validation
- **`scripts/health-check.sh`** - Comprehensive health verification script
- **`.env.production.template`** - Production environment configuration template

### Quick Deployment Commands

#### Production Deployment
```bash
# 1. Configure environment
cp .env.production.template .env.production
# Edit .env.production with your credentials

# 2. Make scripts executable
chmod +x scripts/deploy-production.sh scripts/health-check.sh docker-entrypoint.sh

# 3. Deploy to production
./scripts/deploy-production.sh

# 4. Verify deployment
./scripts/health-check.sh
```

#### Development Environment
```bash
# Start development environment
docker-compose -f docker-compose.development.yml up -d

# View logs
docker-compose -f docker-compose.development.yml logs -f
```

#### Staging Environment
```bash
# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# Run integration tests
docker-compose -f docker-compose.staging.yml exec integration-tests pytest
```

## 🔧 **CRITICAL ISSUES RESOLVED**

### ✅ Redis Connection Configuration
- **Problem:** Connection to localhost:6379 instead of Redis Cloud
- **Solution:** Proper Redis Cloud URI configuration in docker-entrypoint.sh
- **Verification:** Health check script validates Redis connectivity

### ✅ Missing Dependencies Installation
- **Problem:** pymongo, motor, celery, python-consul, pytesseract, google-cloud-vision missing
- **Solution:** Explicit installation in Dockerfile.production
- **Verification:** Health check script validates all dependencies

### ✅ Environment Variable Loading
- **Problem:** .env files not loaded during container initialization
- **Solution:** docker-entrypoint.sh loads environment before service startup
- **Verification:** Environment validation in entrypoint script

### ✅ Pydantic V2 Compatibility
- **Problem:** Deprecated V1 patterns causing warnings
- **Solution:** Updated configurations and proper dependency versions
- **Verification:** No deprecation warnings in container logs

## 🚀 **DEPLOYMENT VERIFICATION CHECKLIST**

After deployment, verify the following:

- [ ] All containers are running and healthy
- [ ] Redis Cloud connection is working
- [ ] All critical dependencies are installed
- [ ] MongoDB and Neo4j connections are established
- [ ] API endpoints are responding
- [ ] Agent system is initialized
- [ ] External API connections (Notion, Supabase) are working
- [ ] Monitoring dashboards are accessible
- [ ] SSL/TLS certificates are configured
- [ ] Backup systems are operational

## 📊 **MONITORING AND MAINTENANCE**

### Access Points
- **Application:** http://localhost:8000
- **Health Check:** http://localhost:8000/health
- **Grafana Dashboard:** http://localhost:3000
- **Prometheus Metrics:** http://localhost:9090

### Maintenance Commands
```bash
# View application logs
docker-compose -f docker-compose.production.yml logs -f higherself-server

# Scale application
docker-compose -f docker-compose.production.yml up -d --scale higherself-server=3

# Update deployment
./scripts/deploy-production.sh

# Backup data
docker-compose -f docker-compose.production.yml exec mongodb mongodump --archive > backup.archive
```

This comprehensive Docker deployment solution addresses all identified critical issues and provides a production-ready Higher Self Network Server deployment.
