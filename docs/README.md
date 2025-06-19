# HigherSelf Network Server - Documentation Index

## Overview

Welcome to The HigherSelf Network Server documentation. This enterprise automation platform serves three business entities (The 7 Space, A.M. Consulting, and HigherSelf Core) with comprehensive Docker orchestration, Terragrunt infrastructure management, and multi-environment deployment capabilities.

## Quick Start

### 🚀 Get Started in 5 Minutes

```bash
# 1. Clone and setup
git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git
cd The-HigherSelf-Network-Server

# 2. Initialize environment
./scripts/init-volumes.sh development
cp .env.development.template .env.development
# Edit .env.development with your API keys

# 3. Deploy
./scripts/manage-environments.sh setup development

# 4. Verify
./scripts/health-check.sh all console
```

### 📋 Prerequisites Checklist

- [ ] Docker (v20.10+) and Docker Compose (v2.0+)
- [ ] Notion API Token
- [ ] OpenAI API Key
- [ ] SMTP Credentials (for email)
- [ ] AWS Account (for production)

## 📚 Documentation Structure

### Core Guides

| Document | Description | Audience |
|----------|-------------|----------|
| [**Comprehensive Deployment Guide**](./COMPREHENSIVE_DEPLOYMENT_GUIDE.md) | Complete deployment instructions for all environments | DevOps, Developers |
| [**Environment Setup Guide**](./ENVIRONMENT_SETUP_GUIDE.md) | Environment configuration and management | Developers, Admins |
| [**Docker Deployment Guide**](./deployment/DOCKER_DEPLOYMENT.md) | Docker-specific deployment instructions | DevOps Engineers |
| [**GHCR Integration Guide**](./GHCR_INTEGRATION_GUIDE.md) | GitHub Container Registry integration and CI/CD | DevOps, CI/CD Engineers |
| [**Terraform Integration Guide**](./TERRAFORM_INTEGRATION_GUIDE.md) | Infrastructure as Code with Terragrunt | Infrastructure Teams |

### Configuration References

| Document | Description | Use Case |
|----------|-------------|----------|
| [**Network Configuration**](../deployment/networking/network-config.yml) | Network topology and security settings | Network configuration |
| [**Volume Management**](../deployment/volumes/volume-management.yml) | Data persistence and backup strategies | Data management |
| [**Health Check Configuration**](../deployment/health-checks/health-check-config.yml) | Service monitoring and health checks | Monitoring setup |
| [**External Services Integration**](../deployment/external-services/integration-config.yml) | API integrations and external services | Integration setup |

### Business Entity Documentation

| Entity | Contacts | Documentation | Priority |
|--------|----------|---------------|----------|
| **A.M. Consulting** | 1,300 | Business consulting workflows | High |
| **The 7 Space** | 191 | Art gallery and wellness center | Medium |
| **HigherSelf Core** | 1,300 | Community platform workflows | High |

## 🛠️ Management Scripts

### Core Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| [`manage-environments.sh`](../scripts/manage-environments.sh) | Environment management | `./scripts/manage-environments.sh switch development` |
| [`docker-terragrunt-deploy.sh`](../scripts/docker-terragrunt-deploy.sh) | Integrated deployment | `./scripts/docker-terragrunt-deploy.sh production deploy all` |
| [`health-check.sh`](../scripts/health-check.sh) | Health monitoring | `./scripts/health-check.sh all detailed` |
| [`test-deployment.sh`](../scripts/test-deployment.sh) | Deployment testing | `./scripts/test-deployment.sh development all` |

### Specialized Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| [`init-volumes.sh`](../scripts/init-volumes.sh) | Volume initialization | `./scripts/init-volumes.sh development` |
| [`volume-backup.sh`](../scripts/volume-backup.sh) | Backup management | `./scripts/volume-backup.sh backup all full` |
| [`network-manager.sh`](../scripts/network-manager.sh) | Network management | `./scripts/network-manager.sh status all` |
| [`external-services.sh`](../scripts/external-services.sh) | External API testing | `./scripts/external-services.sh test all` |
| [`ghcr-manager.sh`](../scripts/ghcr-manager.sh) | GHCR image management | `./scripts/ghcr-manager.sh build latest` |
| [`test-ghcr-integration.sh`](../scripts/test-ghcr-integration.sh) | GHCR integration testing | `./scripts/test-ghcr-integration.sh all` |

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    HigherSelf Network Server                │
├─────────────────────────────────────────────────────────────┤
│  Business Entities                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ The 7 Space │ │A.M.Consult. │ │ HigherSelf Core     │   │
│  │ 191 contacts│ │1,300 contacts│ │ 1,300 contacts      │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Application Layer                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ FastAPI     │ │ Celery      │ │ Health Checks       │   │
│  │ Server      │ │ Workers     │ │ & Monitoring        │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ MongoDB     │ │ Redis       │ │ Consul              │   │
│  │ Database    │ │ Cache       │ │ Service Discovery   │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ Docker      │ │ Nginx       │ │ Prometheus/Grafana  │   │
│  │ Containers  │ │ Load Bal.   │ │ Monitoring          │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### External Integrations

- **Notion API** - Workspace and database management
- **OpenAI API** - AI-powered features and automation
- **HuggingFace API** - Additional ML capabilities
- **SMTP Services** - Email notifications and communication
- **Cloud Storage** - AWS S3, Azure Blob, Google Cloud Storage
- **Webhooks** - Real-time event processing

## 🌍 Environment Configuration

### Development Environment
- **Purpose**: Local development and testing
- **Features**: Hot reload, debug logging, simplified security
- **Database**: Local MongoDB and Redis instances
- **Secrets**: Environment file based

### Staging Environment
- **Purpose**: Pre-production testing and validation
- **Features**: Production-like configuration, performance testing
- **Database**: Isolated staging databases
- **Secrets**: Vault-based secrets management

### Production Environment
- **Purpose**: Live deployment serving real users
- **Features**: High availability, enterprise security, monitoring
- **Database**: Production-grade with backups and replication
- **Secrets**: AWS Secrets Manager integration

## 🔧 Configuration Examples

### Basic Environment Setup

```bash
# Development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
MULTI_ENTITY_MODE=true
PRIMARY_BUSINESS_ENTITY=the_7_space

# API Keys (replace with actual values)
NOTION_API_TOKEN=secret_your_token_here
OPENAI_API_KEY=your_openai_api_key
```

### Business Entity Configuration

```bash
# The 7 Space (Art Gallery/Wellness)
THE_7_SPACE_ENABLED=true
THE_7_SPACE_CONTACT_COUNT=191
THE_7_SPACE_NOTION_WORKSPACE=your_workspace_id

# A.M. Consulting (Business Consulting)
AM_CONSULTING_ENABLED=true
AM_CONSULTING_CONTACT_COUNT=1300
AM_CONSULTING_NOTION_WORKSPACE=your_workspace_id

# HigherSelf Core (Community Platform)
HIGHERSELF_CORE_ENABLED=true
HIGHERSELF_CORE_CONTACT_COUNT=1300
HIGHERSELF_CORE_NOTION_WORKSPACE=your_workspace_id
```

## 🚀 Deployment Scenarios

### Scenario 1: Local Development

```bash
# Quick setup for development
./scripts/manage-environments.sh switch development
./scripts/manage-environments.sh setup development
./scripts/test-deployment.sh development all
```

### Scenario 2: Staging Deployment

```bash
# Deploy to staging with full testing
./scripts/docker-terragrunt-deploy.sh staging deploy all
./scripts/test-deployment.sh staging integration
./scripts/health-check.sh detailed json
```

### Scenario 3: Production Deployment

```bash
# Production deployment with infrastructure
cd terragrunt/environments/production
terragrunt run-all apply
./scripts/docker-terragrunt-deploy.sh production deploy all
./scripts/test-deployment.sh production security
```

## 📊 Monitoring and Health Checks

### Health Check Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/health` | Overall system health | 200 OK with status details |
| `/health/ready` | Readiness probe | 200 OK when ready to serve |
| `/health/live` | Liveness probe | 200 OK when application is alive |
| `/health/database` | Database connectivity | 200 OK when DB is accessible |
| `/health/external` | External services | 200 OK when APIs are reachable |

### Monitoring Stack

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Health Checks**: Automated service monitoring
- **Log Aggregation**: Centralized logging with rotation

## 🔒 Security Considerations

### Development Security
- Simplified authentication for ease of development
- Debug endpoints enabled
- Relaxed network policies

### Staging Security
- Production-like security configuration
- Vault-based secrets management
- Network isolation and firewalls

### Production Security
- Enterprise-grade security hardening
- AWS Secrets Manager integration
- SSL/TLS encryption
- Rate limiting and DDoS protection
- Audit logging and compliance monitoring

## 🆘 Troubleshooting

### Common Issues

| Issue | Solution | Reference |
|-------|----------|-----------|
| Container health check failures | Check logs and restart services | [Health Check Guide](./COMPREHENSIVE_DEPLOYMENT_GUIDE.md#troubleshooting) |
| Network connectivity problems | Recreate networks and test connectivity | [Network Management](../scripts/network-manager.sh) |
| External API connection issues | Validate credentials and test endpoints | [External Services](../scripts/external-services.sh) |
| Volume and data problems | Reinitialize volumes and check permissions | [Volume Management](../scripts/init-volumes.sh) |

### Debug Commands

```bash
# Check overall system health
./scripts/health-check.sh all detailed

# Test external service connections
./scripts/external-services.sh troubleshoot

# Monitor network performance
./scripts/network-manager.sh monitor

# Run comprehensive deployment tests
./scripts/test-deployment.sh development all console
```

## 📞 Support and Resources

### Getting Help

1. **Check the logs**: `docker-compose logs -f [service-name]`
2. **Run health checks**: `./scripts/health-check.sh all detailed`
3. **Test external services**: `./scripts/external-services.sh status all`
4. **Review configuration**: Check environment files and Docker Compose configuration

### Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Terragrunt Documentation](https://terragrunt.gruntwork.io/)
- [Notion API Documentation](https://developers.notion.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `./scripts/test-deployment.sh development all`
5. Submit a pull request

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Maintainer**: HigherSelf Network Team
