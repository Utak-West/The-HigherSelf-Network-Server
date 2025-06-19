# The HigherSelf Network Server - VM Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying The HigherSelf Network Server to a virtual machine environment with support for all three business entities:

- **The 7 Space** (191 contacts) - Art Gallery & Wellness Center
- **AM Consulting** (1,300 contacts) - Business Consulting
- **HigherSelf Core** (1,300 contacts) - Community Platform

## VM Requirements

### Minimum System Requirements
- **OS**: Ubuntu 20.04 LTS or newer (recommended)
- **CPU**: 4 cores (8 cores recommended)
- **RAM**: 8GB (16GB recommended for optimal performance)
- **Storage**: 50GB SSD (100GB+ recommended)
- **Network**: Static IP address with internet connectivity

### Recommended VM Specifications
- **CPU**: 8 cores @ 2.4GHz+
- **RAM**: 16GB
- **Storage**: 100GB SSD with backup storage
- **Network**: 1Gbps connection
- **Backup**: Automated daily backups configured

## Pre-Deployment Setup

### 1. VM Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git unzip htop

# Create deployment user (optional)
sudo useradd -m -s /bin/bash higherself
sudo usermod -aG sudo higherself
sudo su - higherself
```

### 2. Network Configuration

```bash
# Configure static IP (edit netplan configuration)
sudo nano /etc/netplan/00-installer-config.yaml

# Example configuration:
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - YOUR_VM_IP/24
      gateway4: YOUR_GATEWAY_IP
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4

# Apply network configuration
sudo netplan apply
```

### 3. DNS Configuration

```bash
# Add DNS records for your domain
# A record: higherself.yourdomain.com -> YOUR_VM_IP
# CNAME records for subdomains:
# api.yourdomain.com -> higherself.yourdomain.com
# dashboard.yourdomain.com -> higherself.yourdomain.com
```

## Deployment Process

### 1. Clone Repository

```bash
# Clone the repository
git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git
cd The-HigherSelf-Network-Server

# Make deployment script executable
chmod +x deploy-vm.sh
```

### 2. Configure Environment

```bash
# Copy VM environment template
cp .env.vm.production.template .env.vm.production

# Edit configuration with your actual values
nano .env.vm.production
```

**Critical Configuration Items:**

```bash
# VM Configuration
VM_IP=YOUR_ACTUAL_VM_IP
VM_HOSTNAME=higherself.yourdomain.com

# Notion API Configuration
NOTION_API_TOKEN=secret_your_actual_notion_token
NOTION_PARENT_PAGE_ID=your_actual_parent_page_id

# Database Passwords (generate secure passwords)
MONGODB_PASSWORD=your_secure_mongodb_password
MONGODB_ROOT_PASSWORD=your_secure_mongodb_root_password
REDIS_PASSWORD=your_secure_redis_password

# Security Keys (generate secure keys)
JWT_SECRET_KEY=your_secure_jwt_secret
WEBHOOK_SECRET=your_secure_webhook_secret
SECRETS_ENCRYPTION_KEY=your_secure_encryption_key

# Grafana Admin Password
GRAFANA_ADMIN_PASSWORD=your_secure_grafana_password

# Business Entity Database IDs
NOTION_THE7SPACE_CONTACTS_DB=your_the7space_contacts_db_id
NOTION_AMCONSULTING_CONTACTS_DB=your_amconsulting_contacts_db_id
NOTION_HIGHERSELF_CONTACTS_DB=your_higherself_contacts_db_id
```

### 3. Deploy to VM

```bash
# Run full deployment (requires sudo)
sudo ./deploy-vm.sh deploy
```

The deployment script will:
- ✅ Install Docker and Docker Compose
- ✅ Configure firewall rules
- ✅ Set up SSL certificates
- ✅ Create data directories
- ✅ Build and start all services
- ✅ Configure monitoring and logging

### 4. Verify Deployment

```bash
# Check service status
sudo ./deploy-vm.sh status

# View service logs
sudo ./deploy-vm.sh logs

# Test health endpoints
curl http://YOUR_VM_IP/health
curl http://YOUR_VM_IP:9090/-/ready
curl http://YOUR_VM_IP:3000/api/health
```

## Service Access Points

### Primary Services

| Service | URL | Purpose | Credentials |
|---------|-----|---------|-------------|
| **Main Application** | http://YOUR_VM_IP | API and web interface | - |
| **Grafana Dashboard** | http://YOUR_VM_IP:3000 | Analytics and monitoring | admin/your_grafana_password |
| **Prometheus** | http://YOUR_VM_IP:9090 | Metrics collection | - |
| **Consul** | http://YOUR_VM_IP:8500 | Service discovery | - |

### Database Services

| Service | Connection | Purpose | Credentials |
|---------|------------|---------|-------------|
| **MongoDB** | YOUR_VM_IP:27017 | Primary database | higherself_user/your_mongodb_password |
| **Redis** | YOUR_VM_IP:6379 | Cache and queues | your_redis_password |

### Integration Endpoints

| Platform | Webhook URL | Purpose |
|----------|-------------|---------|
| **Zapier** | http://YOUR_VM_IP/api/webhooks/zapier | Zapier automation |
| **N8N** | http://YOUR_VM_IP/api/webhooks/n8n | N8N workflow automation |
| **Make.com** | http://YOUR_VM_IP/api/webhooks/make | Make.com scenarios |

## Security Configuration

### 1. Firewall Rules

The deployment automatically configures UFW firewall:

```bash
# View current firewall status
sudo ufw status

# Allow additional IPs if needed
sudo ufw allow from YOUR_OFFICE_IP to any port 22
sudo ufw allow from YOUR_HOME_IP to any port 22

# Restrict database access to local network
sudo ufw delete allow 27017
sudo ufw delete allow 6379
sudo ufw allow from 192.168.1.0/24 to any port 27017
sudo ufw allow from 192.168.1.0/24 to any port 6379
```

### 2. SSL Certificate Setup

For production, replace self-signed certificates:

```bash
# Install Let's Encrypt certificates
sudo apt install certbot

# Generate certificates
sudo certbot certonly --standalone -d higherself.yourdomain.com

# Copy certificates to SSL directory
sudo cp /etc/letsencrypt/live/higherself.yourdomain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/higherself.yourdomain.com/privkey.pem ./ssl/key.pem

# Restart services to use new certificates
sudo ./deploy-vm.sh restart
```

### 3. Access Control

```bash
# Create additional admin users
sudo docker-compose -f docker-compose.vm.yml exec higherself-server python -m scripts.create_admin_user

# Configure IP whitelisting in .env.vm.production
ALLOWED_IPS=["YOUR_OFFICE_IP", "YOUR_HOME_IP", "YOUR_TEAM_IPS"]
```

## Performance Optimization

### 1. Resource Monitoring

```bash
# Monitor system resources
htop
docker stats

# Monitor disk usage
df -h
du -sh /opt/higherself/*

# Monitor network usage
iftop
```

### 2. Database Optimization

```bash
# MongoDB optimization
sudo docker-compose -f docker-compose.vm.yml exec mongodb-vm mongosh

# Create additional indexes for performance
db.contacts.createIndex({"business_entity": 1, "contact_type": 1})
db.contacts.createIndex({"lead_score": -1, "created_at": -1})
db.workflow_instances.createIndex({"status": 1, "next_execution": 1})

# Redis optimization - check memory usage
sudo docker-compose -f docker-compose.vm.yml exec redis-vm redis-cli info memory
```

### 3. Application Scaling

```bash
# Scale application containers
sudo docker-compose -f docker-compose.vm.yml up -d --scale higherself-server=2

# Configure load balancing in nginx
sudo nano deployment/nginx/vm/default.conf
```

## Backup and Recovery

### 1. Automated Backups

```bash
# Backup script is automatically configured
# View backup schedule
sudo crontab -l

# Manual backup
sudo ./scripts/backup-vm.sh

# Verify backups
ls -la ./backups/
```

### 2. Backup Configuration

```bash
# Configure cloud backup (optional)
# Edit .env.vm.production
CLOUD_BACKUP_ENABLED=true
CLOUD_BACKUP_PROVIDER=aws_s3
AWS_S3_BUCKET=your-backup-bucket
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
```

### 3. Recovery Procedures

```bash
# Restore from backup
sudo ./scripts/restore-vm.sh /path/to/backup

# Restore specific database
sudo docker-compose -f docker-compose.vm.yml exec mongodb-vm mongorestore --drop /backups/mongodb/latest
```

## Monitoring and Alerting

### 1. Grafana Dashboard Setup

1. Access Grafana at http://YOUR_VM_IP:3000
2. Login with admin/your_grafana_password
3. Import pre-configured dashboards:
   - HigherSelf Overview Dashboard
   - Business Entity Analytics
   - System Performance Metrics
   - Application Health Monitoring

### 2. Alert Configuration

```bash
# Configure email alerts in Grafana
# Go to Alerting > Notification channels
# Add email notification channel with your SMTP settings

# Set up critical alerts:
# - High CPU usage (>80%)
# - High memory usage (>90%)
# - Database connection failures
# - Application health check failures
```

### 3. Log Management

```bash
# View application logs
sudo docker-compose -f docker-compose.vm.yml logs -f higherself-server

# View system logs
sudo journalctl -u docker -f

# Configure log rotation
sudo nano /etc/logrotate.d/higherself
```

## Maintenance Procedures

### 1. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
sudo ./deploy-vm.sh update

# Update application code
git pull origin main
sudo ./deploy-vm.sh restart
```

### 2. Health Checks

```bash
# Daily health check script
#!/bin/bash
curl -f http://YOUR_VM_IP/health || echo "Application health check failed"
curl -f http://YOUR_VM_IP:9090/-/ready || echo "Prometheus health check failed"
curl -f http://YOUR_VM_IP:3000/api/health || echo "Grafana health check failed"
```

### 3. Performance Tuning

```bash
# Monitor and optimize based on usage patterns
# Check slow queries in MongoDB
db.setProfilingLevel(2, { slowms: 100 })
db.system.profile.find().sort({ts: -1}).limit(5)

# Optimize Redis memory usage
redis-cli config set maxmemory-policy allkeys-lru
redis-cli config rewrite
```

## Troubleshooting

### Common Issues

**1. Services not starting:**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check available resources
df -h
free -h

# Check service logs
sudo ./deploy-vm.sh logs
```

**2. Database connection issues:**
```bash
# Test MongoDB connection
sudo docker-compose -f docker-compose.vm.yml exec mongodb-vm mongosh

# Test Redis connection
sudo docker-compose -f docker-compose.vm.yml exec redis-vm redis-cli ping
```

**3. Network connectivity issues:**
```bash
# Check firewall rules
sudo ufw status

# Test port connectivity
telnet YOUR_VM_IP 80
telnet YOUR_VM_IP 3000
```

**4. SSL certificate issues:**
```bash
# Check certificate validity
openssl x509 -in ./ssl/cert.pem -text -noout

# Renew Let's Encrypt certificates
sudo certbot renew
```

## Next Steps

After successful deployment:

1. **Configure Business Entity Data Import**
2. **Set up Automation Platform Integrations**
3. **Configure Monitoring Alerts**
4. **Test Backup and Recovery Procedures**
5. **Optimize Performance Based on Usage**

Your VM deployment is now ready for production use with all three business entities!
