# The 7 Space Automated Deployment Guide

## Overview

This comprehensive guide provides step-by-step instructions for deploying The 7 Space Art Gallery & Wellness Center automation platform using the HigherSelf Network Server infrastructure. The deployment system is designed for enterprise-grade reliability, security, and scalability.

## Quick Start

### Prerequisites Checklist

Before starting the deployment, ensure you have:

- [ ] Docker and Docker Compose installed
- [ ] Terragrunt installed (for infrastructure management)
- [ ] Git repository access
- [ ] Production environment variables configured
- [ ] SSL certificates (if using HTTPS)
- [ ] Backup storage configured
- [ ] Monitoring tools access

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git
cd "The HigherSelf Network Server"

# Copy and configure environment file
cp .env.the7space.production.template .env.the7space.production

# Edit the environment file with your production values
nano .env.the7space.production
```

### 2. Configure Production Environment

Edit `.env.the7space.production` and update these critical values:

```bash
# Database passwords
MONGODB_PASSWORD=your_secure_mongodb_password
REDIS_PASSWORD=your_secure_redis_password

# API keys
NOTION_API_TOKEN=your_notion_api_token
OPENAI_API_KEY=your_openai_api_key

# The 7 Space specific configuration
THE_7_SPACE_WORDPRESS_URL=https://the7space.com
THE_7_SPACE_WORDPRESS_API_KEY=your_wordpress_api_key

# Security
WEBHOOK_SECRET=your_secure_webhook_secret
JWT_SECRET_KEY=your_secure_jwt_secret

# Notification settings
SMTP_USERNAME=your_email@domain.com
SMTP_PASSWORD=your_email_password
```

### 3. Deploy Infrastructure

```bash
# Deploy infrastructure with Terragrunt
./deploy-the7space-production.sh infrastructure

# Or deploy everything at once
./deploy-the7space-production.sh deploy
```

### 4. Verify Deployment

```bash
# Run comprehensive verification
./verify-the7space-deployment.sh

# Run specific checks
./verify-the7space-deployment.sh health
./verify-the7space-deployment.sh integrations
```

## Detailed Deployment Process

### Phase 1: Infrastructure Preparation

#### 1.1 Terragrunt Infrastructure Deployment

```bash
cd terragrunt/environments/the7space-production
terragrunt init
terragrunt plan
terragrunt apply
```

This deploys:
- AWS infrastructure (if using cloud deployment)
- Networking configuration
- Security groups and policies
- Storage volumes
- Load balancers

#### 1.2 Secrets Management Setup

```bash
# Configure AWS Secrets Manager (if using AWS)
aws secretsmanager create-secret \
  --name "the7space/production/mongodb-password" \
  --secret-string "your_secure_password"

# Or configure Vault (if using Vault)
vault kv put secret/the7space/production \
  mongodb_password="your_secure_password"
```

### Phase 2: Application Deployment

#### 2.1 Build Docker Images

```bash
# Build The 7 Space production image
docker build \
  --build-arg ENVIRONMENT=production \
  --build-arg BUSINESS_ENTITY=the_7_space \
  -t thehigherselfnetworkserver:the7space-production .
```

#### 2.2 Deploy Services

```bash
# Deploy all services
docker-compose -f docker-compose.the7space.prod.yml up -d

# Check service status
docker-compose -f docker-compose.the7space.prod.yml ps
```

#### 2.3 Initialize Database

```bash
# Wait for MongoDB to be ready
docker-compose -f docker-compose.the7space.prod.yml exec the7space-mongodb \
  mongosh --eval "db.adminCommand('ping')"

# Initialize application database
docker-compose -f docker-compose.the7space.prod.yml exec the7space-app \
  python manage.py migrate
```

### Phase 3: Configuration and Integration

#### 3.1 Configure The 7 Space Business Entity

```bash
# Set primary business entity
docker-compose -f docker-compose.the7space.prod.yml exec the7space-app \
  python manage.py configure_business_entity \
  --entity=the_7_space \
  --contact_count=191 \
  --enable_gallery=true \
  --enable_wellness=true
```

#### 3.2 Setup Notion Integration

```bash
# Test Notion connectivity
curl -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  https://api.notion.com/v1/users/me

# Sync initial contact data
docker-compose -f docker-compose.the7space.prod.yml exec the7space-app \
  python manage.py sync_notion_contacts --business_entity=the_7_space
```

#### 3.3 Configure WordPress Integration

```bash
# Install WordPress plugin
# Upload deployment/siteground/wordpress-plugin/ to WordPress site

# Test WordPress API connectivity
curl https://the7space.com/wp-json/wp/v2/

# Configure webhook endpoints
curl -X POST https://the7space.com/wp-json/the7space/v1/configure \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://api.the7space.com/webhooks/wordpress"}'
```

### Phase 4: Monitoring and Observability

#### 4.1 Configure Prometheus

```bash
# Verify Prometheus configuration
docker-compose -f docker-compose.the7space.prod.yml exec the7space-prometheus \
  promtool check config /etc/prometheus/prometheus.yml

# Check targets
curl http://localhost:9090/api/v1/targets
```

#### 4.2 Setup Grafana Dashboards

```bash
# Import The 7 Space dashboard
curl -X POST http://admin:$GRAFANA_ADMIN_PASSWORD@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @deployment/grafana/the7space/dashboards/the7space-overview.json
```

#### 4.3 Configure Alerting

```bash
# Test alert configuration
curl -X POST http://localhost:9090/-/reload

# Verify alert rules
curl http://localhost:9090/api/v1/rules
```

## Verification and Testing

### Automated Verification

```bash
# Run full verification suite
./verify-the7space-deployment.sh

# Run integration tests
python3 testing/the7space/test_deployment_integration.py

# Run validation script
python3 scripts/validate-the7space-deployment.py
```

### Manual Verification Checklist

#### Service Health
- [ ] All Docker containers running
- [ ] Application responding on port 8000
- [ ] Database connections established
- [ ] Redis cache operational
- [ ] Consul service discovery working

#### The 7 Space Functionality
- [ ] Contact management system operational
- [ ] Gallery workflow automation active
- [ ] Wellness center booking system working
- [ ] Artist onboarding workflows functional
- [ ] Visitor engagement automation running

#### Integrations
- [ ] Notion API connectivity verified
- [ ] WordPress plugin installed and configured
- [ ] OpenAI API integration working
- [ ] Email notifications functional
- [ ] Webhook endpoints responding

#### Performance
- [ ] Response times under 500ms
- [ ] Database queries optimized
- [ ] Cache hit rates above 90%
- [ ] Memory usage under 80%
- [ ] CPU usage under 70%

#### Security
- [ ] HTTPS enabled (if applicable)
- [ ] API authentication working
- [ ] Secrets properly encrypted
- [ ] File permissions secure
- [ ] Network access restricted

## Maintenance and Operations

### Daily Operations

#### Health Monitoring
```bash
# Check service health
./verify-the7space-deployment.sh health

# View service logs
docker-compose -f docker-compose.the7space.prod.yml logs -f

# Monitor resource usage
docker stats
```

#### Backup Procedures
```bash
# Backup MongoDB
docker-compose -f docker-compose.the7space.prod.yml exec the7space-mongodb \
  mongodump --out /backups/$(date +%Y%m%d_%H%M%S)

# Backup configuration
tar -czf config-backup-$(date +%Y%m%d).tar.gz \
  .env.the7space.production \
  docker-compose.the7space.prod.yml \
  deployment/
```

### Weekly Maintenance

#### Update and Restart Services
```bash
# Pull latest images
docker-compose -f docker-compose.the7space.prod.yml pull

# Restart services with zero downtime
docker-compose -f docker-compose.the7space.prod.yml up -d --no-deps the7space-app

# Verify deployment
./verify-the7space-deployment.sh
```

#### Performance Review
```bash
# Check Grafana dashboards
open http://localhost:3000

# Review Prometheus metrics
open http://localhost:9090

# Analyze logs for errors
docker-compose -f docker-compose.the7space.prod.yml logs --since 7d | grep ERROR
```

### Monthly Maintenance

#### Security Updates
```bash
# Update base images
docker-compose -f docker-compose.the7space.prod.yml build --pull

# Update dependencies
docker-compose -f docker-compose.the7space.prod.yml exec the7space-app \
  pip install --upgrade -r requirements.txt

# Security scan
docker scan thehigherselfnetworkserver:the7space-production
```

#### Capacity Planning
```bash
# Review resource usage trends
# Check database growth
# Analyze contact processing volumes
# Plan for scaling needs
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose -f docker-compose.the7space.prod.yml logs service-name

# Check resource usage
docker system df
df -h

# Restart service
docker-compose -f docker-compose.the7space.prod.yml restart service-name
```

#### Database Connection Issues
```bash
# Check MongoDB status
docker-compose -f docker-compose.the7space.prod.yml exec the7space-mongodb \
  mongosh --eval "db.adminCommand('ping')"

# Check Redis status
docker-compose -f docker-compose.the7space.prod.yml exec the7space-redis \
  redis-cli ping

# Restart database services
docker-compose -f docker-compose.the7space.prod.yml restart the7space-mongodb the7space-redis
```

#### Integration Failures
```bash
# Test Notion API
curl -H "Authorization: Bearer $NOTION_API_TOKEN" \
  https://api.notion.com/v1/users/me

# Test WordPress API
curl https://the7space.com/wp-json/wp/v2/

# Check API logs
docker-compose -f docker-compose.the7space.prod.yml logs the7space-app | grep -i "notion\|wordpress\|openai"
```

### Emergency Procedures

#### Service Recovery
```bash
# Stop all services
docker-compose -f docker-compose.the7space.prod.yml down

# Clean up resources
docker system prune -f

# Restore from backup
# ... restore procedures ...

# Restart services
docker-compose -f docker-compose.the7space.prod.yml up -d

# Verify recovery
./verify-the7space-deployment.sh
```

#### Rollback Procedures
```bash
# Rollback to previous version
git checkout previous-stable-tag

# Rebuild and deploy
./deploy-the7space-production.sh services

# Verify rollback
./verify-the7space-deployment.sh
```

## Support and Resources

### Documentation
- [The 7 Space Deployment Strategy](docs/THE_7_SPACE_AUTOMATED_DEPLOYMENT_STRATEGY.md)
- [SiteGround Integration Guide](deployment/siteground/the7space-wordpress-integration.md)
- [Health Check Configuration](deployment/health-checks/the7space-health-config.yml)

### Monitoring Dashboards
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Consul: http://localhost:8500

### Log Files
- Application logs: `logs/the7space/`
- Deployment logs: `logs/the7space-deployment-*.log`
- Verification logs: `logs/the7space-verification-*.log`

### Contact Information
- Technical Support: tech@the7space.com
- Emergency Contact: admin@the7space.com
- Documentation: https://github.com/Utak-West/The-HigherSelf-Network-Server

---

**Note**: This deployment guide ensures enterprise-grade automation platform standards while maintaining focus on The 7 Space's specific requirements and integration with the existing HigherSelf Network Server architecture.
