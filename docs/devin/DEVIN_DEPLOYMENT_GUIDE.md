# Devin Deployment Guide - The HigherSelf Network Server

This guide provides comprehensive instructions for deploying The HigherSelf Network Server specifically for Devin AI integration.

## Overview

The HigherSelf Network Server is now fully configured for Devin deployment with:
- Single-branch repository structure (main only)
- Docker-based deployment system
- Automated validation and testing
- Comprehensive monitoring and logging

## Quick Start for Devin

### Prerequisites
- Docker and Docker Compose installed
- Git repository access
- Basic understanding of containerized applications

### 1. Repository Setup
```bash
# Clone the repository
git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git
cd The-HigherSelf-Network-Server

# Verify single-branch structure
git branch -a
# Should show only main branch
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# The .env file is pre-configured with test defaults for Devin
# No manual editing required for basic deployment
```

### 3. Quick Validation
```bash
# Run quick validation to ensure environment is ready
python3 devin_quick_validation.py

# Expected output: 90%+ success rate
```

### 4. Automated Deployment
```bash
# Option 1: Use Devin-specific deployment script
python3 devin_deploy.py

# Option 2: Use standard deployment script
./scripts/deploy.sh --env dev --build

# Option 3: Manual Docker deployment
docker-compose up -d --build
```

### 5. Verification
```bash
# Check container status
docker-compose ps

# Test API health
curl http://localhost:8000/health

# Run comprehensive tests
python3 run_tests.py
```

## Deployment Architecture

### Container Services
- **windsurf-agent**: Main application server (Port 8000)
- **nginx**: Reverse proxy and load balancer (Ports 80, 443)
- **mongodb**: Database service (Port 27017)
- **redis**: Caching and message queue (Port 6379)
- **consul**: Service discovery (Port 8500)
- **prometheus**: Metrics collection (Port 9090)
- **grafana**: Monitoring dashboard (Port 3000)

### Key Features
- **Health Checks**: All services have built-in health monitoring
- **Auto-restart**: Services automatically restart on failure
- **Volume Persistence**: Data persists across container restarts
- **Logging**: Centralized logging with rotation
- **Security**: Non-root user execution, secure defaults

## Configuration Details

### Environment Variables
The system uses these key environment variables:
```bash
# Core Configuration
TEST_MODE=True                    # Enables test mode for Devin
DISABLE_WEBHOOKS=True            # Disables external webhooks
ENVIRONMENT=development          # Sets deployment environment

# API Configuration
NOTION_API_TOKEN=test_notion_token    # Test token for development
WEBHOOK_SECRET=test_webhook_secret    # Test webhook secret

# Database Configuration
MONGODB_URI=mongodb://mongodb:27017/higherselfnetwork
REDIS_URI=redis://redis:6379/0

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=INFO
```

### Docker Compose Configuration
The deployment uses multiple Docker Compose files:
- `docker-compose.yml`: Base configuration
- `docker-compose.staging.yml`: Staging overrides
- `docker-compose.prod.yml`: Production overrides

## Devin-Specific Features

### 1. Automated Testing
```bash
# Quick validation (30 seconds)
python3 devin_quick_validation.py

# Comprehensive setup and testing (2-5 minutes)
python3 devin_automated_setup.py

# Full deployment with validation
python3 devin_deploy.py
```

### 2. Test Mode Configuration
The system automatically configures test mode with:
- Mock external API calls
- Disabled webhooks
- Test database connections
- Safe default values

### 3. Single-Branch Structure
- Only `main` branch exists
- All features merged into main
- Simplified CI/CD pipeline
- No branch conflicts

### 4. Monitoring and Logging
- Real-time health monitoring
- Structured JSON logging
- Performance metrics
- Error tracking and alerting

## Troubleshooting

### Common Issues

#### 1. Container Startup Failures
```bash
# Check container logs
docker-compose logs -f windsurf-agent

# Restart specific service
docker-compose restart windsurf-agent

# Rebuild and restart
docker-compose down && docker-compose up -d --build
```

#### 2. Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep :8000

# Stop conflicting services
sudo systemctl stop apache2  # or nginx, if running locally
```

#### 3. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod +x scripts/deploy.sh
```

#### 4. Database Connection Issues
```bash
# Check MongoDB status
docker-compose exec mongodb mongosh --eval "db.runCommand('ping')"

# Check Redis status
docker-compose exec redis redis-cli ping
```

### Validation Commands
```bash
# System validation
python3 devin_quick_validation.py

# Docker validation
docker-compose config
docker-compose ps

# API validation
curl -f http://localhost:8000/health
curl -f http://localhost:8000/api/status

# Service validation
curl -f http://localhost:9090/metrics  # Prometheus
curl -f http://localhost:3000/api/health  # Grafana
```

## Performance Optimization

### Resource Allocation
- **CPU**: 2-4 cores recommended
- **Memory**: 4-8 GB RAM minimum
- **Storage**: 20 GB minimum for logs and data
- **Network**: Stable internet connection for external APIs

### Scaling Configuration
```bash
# Scale specific services
docker-compose up -d --scale celery-worker=3

# Monitor resource usage
docker stats

# Optimize for production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Security Considerations

### Default Security Features
- Non-root container execution
- Secure environment variable handling
- Network isolation between services
- Regular security updates

### Production Security
- SSL/TLS certificates required
- Firewall configuration
- Regular backup procedures
- Access logging and monitoring

## Support and Maintenance

### Regular Maintenance
```bash
# Update containers
docker-compose pull
docker-compose up -d

# Clean up unused resources
docker system prune -f

# Backup data
docker-compose exec mongodb mongodump --out /backup
```

### Monitoring
- Health endpoints: `/health`, `/api/status`
- Metrics: Prometheus at `:9090`
- Dashboards: Grafana at `:3000`
- Logs: `docker-compose logs -f`

## Next Steps

After successful deployment:
1. Configure external integrations (if needed)
2. Set up monitoring alerts
3. Configure backup procedures
4. Review security settings
5. Plan scaling strategy

For additional support, refer to:
- `DEVIN_COMPREHENSIVE_SETUP_GUIDE.md`
- `DEVIN_REPOSITORY_NOTES.md`
- `docs/deployment/README.md`
