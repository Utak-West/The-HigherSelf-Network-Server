# HigherSelf Network Server - Terraform Infrastructure

Enterprise-grade Infrastructure as Code (IaC) for the HigherSelf Network Server automation platform.

## 🏗️ Architecture Overview

This Terraform configuration provides:

- **Container Orchestration**: Docker-based service deployment
- **Service Discovery**: Consul for dynamic service registration
- **Data Persistence**: MongoDB and Redis with persistent volumes
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Load Balancing**: Nginx reverse proxy with SSL termination
- **Environment Management**: Development, Staging, and Production configurations
- **Auto-scaling**: Configurable horizontal scaling for production workloads

## 📁 Directory Structure

```
terraform/
├── main.tf                    # Main Terraform configuration
├── variables.tf               # Variable definitions
├── outputs.tf                 # Output definitions
├── services.tf                # Docker service configurations
├── README.md                  # This file
├── environments/              # Environment-specific configurations
│   ├── development.tfvars     # Development environment
│   ├── staging.tfvars         # Staging environment
│   └── production.tfvars      # Production environment
├── modules/                   # Reusable Terraform modules
│   ├── networking/            # Network configuration modules
│   ├── compute/               # Compute resource modules
│   ├── database/              # Database configuration modules
│   ├── monitoring/            # Monitoring stack modules
│   └── security/              # Security configuration modules
└── providers/                 # Cloud provider configurations
    ├── aws/                   # AWS-specific configurations
    ├── gcp/                   # Google Cloud configurations
    └── azure/                 # Azure configurations
```

## 🚀 Quick Start

### Prerequisites

1. **Terraform**: Version 1.0 or higher
2. **Docker**: Docker Engine running locally
3. **Environment Variables**: Set up your integration tokens

### Installation

1. **Initialize Terraform**:
   ```bash
   cd terraform
   terraform init
   ```

2. **Select Environment**:
   ```bash
   # For development
   terraform workspace new development
   terraform workspace select development
   
   # For staging
   terraform workspace new staging
   terraform workspace select staging
   
   # For production
   terraform workspace new production
   terraform workspace select production
   ```

3. **Plan Deployment**:
   ```bash
   # Development
   terraform plan -var-file="environments/development.tfvars"
   
   # Staging
   terraform plan -var-file="environments/staging.tfvars"
   
   # Production
   terraform plan -var-file="environments/production.tfvars"
   ```

4. **Deploy Infrastructure**:
   ```bash
   # Development
   terraform apply -var-file="environments/development.tfvars"
   
   # Staging
   terraform apply -var-file="environments/staging.tfvars"
   
   # Production
   terraform apply -var-file="environments/production.tfvars"
   ```

## 🔧 Configuration

### Environment Variables

Set these environment variables or add them to your `.env` file:

```bash
# Integration Tokens
export TF_VAR_notion_token="your_notion_token"
export TF_VAR_openai_api_key="your_openai_key"
export TF_VAR_huggingface_token="your_huggingface_token"

# Database Passwords (Production)
export TF_VAR_mongodb_root_password="your_secure_root_password"
export TF_VAR_mongodb_app_password="your_secure_app_password"
export TF_VAR_redis_password="your_secure_redis_password"
export TF_VAR_grafana_admin_password="your_secure_grafana_password"
```

### SSL Configuration

For production deployments, place your SSL certificates in:
- `./deployment/ssl/prod_cert.pem`
- `./deployment/ssl/prod_key.pem`

## 📊 Monitoring

### Service Endpoints

After deployment, access these services:

- **Main Application**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Consul**: http://localhost:8500

### Resource Monitoring

Monitor resource usage with:
```bash
# Container status
docker ps

# Resource usage
docker stats

# Logs
docker-compose logs -f windsurf-agent
```

## 🔒 Security

### Production Security Checklist

- [ ] Update all default passwords
- [ ] Configure SSL certificates
- [ ] Restrict IP access in `allowed_ips`
- [ ] Set up proper firewall rules
- [ ] Enable audit logging
- [ ] Configure backup encryption
- [ ] Set up intrusion detection
- [ ] Regular security updates

### Network Security

- All services communicate through isolated Docker network
- External access controlled via Nginx reverse proxy
- SSL/TLS encryption for all external communications
- Service-to-service authentication via Consul

## 💾 Backup & Recovery

### Automated Backups

Backups are configured per environment:
- **Development**: Weekly backups, 7-day retention
- **Staging**: Daily backups, 30-day retention
- **Production**: Daily backups, 90-day retention

### Manual Backup

```bash
# MongoDB backup
docker exec higherself-mongodb-production mongodump --out /backup

# Redis backup
docker exec higherself-redis-production redis-cli BGSAVE
```

## 🔄 Scaling

### Horizontal Scaling

Production environment supports auto-scaling:
- **Minimum replicas**: 3
- **Maximum replicas**: 10
- **CPU threshold**: 70%

### Manual Scaling

```bash
# Scale windsurf-agent service
terraform apply -var="min_replicas=5" -var-file="environments/production.tfvars"
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 8000, 27017, 6379, 9090, 3000, 8500 are available
2. **Docker Permissions**: Ensure Docker daemon is accessible
3. **SSL Certificates**: Verify certificate paths and permissions
4. **Environment Variables**: Check all required variables are set

### Debug Commands

```bash
# Check Terraform state
terraform show

# Validate configuration
terraform validate

# Check Docker containers
docker ps -a

# View container logs
docker logs <container_name>
```

## 📈 Performance Optimization

### Resource Tuning

Adjust resource limits in `variables.tf` based on your workload:
- CPU limits
- Memory limits
- Storage allocation
- Network bandwidth

### Database Optimization

- MongoDB: Adjust WiredTiger cache size
- Redis: Configure memory policies
- Connection pooling optimization

## 🔄 CI/CD Integration

### GitHub Actions

Example workflow for automated deployment:

```yaml
name: Deploy HigherSelf Network Server
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v1
      - name: Terraform Apply
        run: |
          cd terraform
          terraform init
          terraform apply -auto-approve -var-file="environments/production.tfvars"
```

## 📞 Support

For enterprise support and advanced configurations, contact the HigherSelf Network team.

## 📄 License

This infrastructure configuration is part of the HigherSelf Network Server enterprise automation platform.
