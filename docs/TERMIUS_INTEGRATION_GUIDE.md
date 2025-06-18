# Termius Integration Guide for HigherSelf Network Server

## Overview

This comprehensive guide covers the complete integration between Termius and GitHub Actions for the HigherSelf Network Server, providing real-time build notifications, deployment monitoring, and automated terminal management.

## Table of Contents

1. [Quick Setup](#quick-setup)
2. [GitHub Actions Integration](#github-actions-integration)
3. [Termius Configuration](#termius-configuration)
4. [Monitoring & Notifications](#monitoring--notifications)
5. [Advanced Features](#advanced-features)
6. [Troubleshooting](#troubleshooting)

## Quick Setup

### 1. Run the Setup Script

```bash
# Navigate to the project root
cd /path/to/The-HigherSelf-Network-Server

# Run the Termius integration setup
chmod +x scripts/termius/setup_termius_integration.sh
./scripts/termius/setup_termius_integration.sh
```

### 2. Configure GitHub Token

```bash
# Edit the GitHub configuration
nano ~/.termius_higherself/github_config.sh

# Set your GitHub token
export GITHUB_TOKEN="your_github_personal_access_token"
```

### 3. Test the Integration

```bash
# Test the monitoring system
~/.termius_higherself/scripts/termius_monitor.sh test

# Start continuous monitoring
~/.termius_higherself/scripts/start_monitor.sh
```

## GitHub Actions Integration

### Webhook Configuration

1. **Add Repository Secret**:
   - Go to your GitHub repository settings
   - Navigate to Secrets and Variables → Actions
   - Add `TERMIUS_WEBHOOK_URL` with your webhook endpoint

2. **Webhook Endpoint**:
   ```
   Local: http://localhost:8000/api/termius/webhooks/github-actions
   Production: https://your-domain.com/api/termius/webhooks/github-actions
   ```

### Supported Workflow Events

The integration automatically captures and displays:

- ✅ **Workflow Success**: Build completed successfully
- ❌ **Workflow Failure**: Build failed with error details
- ⚠️ **Workflow Cancelled**: Build was cancelled
- 🔄 **Workflow In Progress**: Real-time build status
- 🚀 **Deployment Events**: Staging and production deployments
- 🔒 **Security Scans**: Vulnerability scan results

### Notification Format

```
══════════════════════════════════════════════════════════════
✅ HigherSelf Network Server - Enhanced CI/CD Pipeline
══════════════════════════════════════════════════════════════
Status: SUCCESS
Branch: main
Commit: abc12345
Message: feat: Add Termius integration for real-time monitoring
Environment: production
Image: ghcr.io/utak-west/higherself-network-server:latest
Actor: Utak-West
Time: 14:30:25 UTC

Detailed Status:
  • Pre-flight: ✓ success
  • Quality Checks: ✓ success
  • Test Suite: ✓ success
  • Build: ✓ success
  • Security Scan: ✓ success
  • Deploy: ✓ success

View Details: https://github.com/Utak-West/The-HigherSelf-Network-Server/actions/runs/123456
══════════════════════════════════════════════════════════════
```

## Termius Configuration

### Connection Profiles

#### 1. Development Environment
```yaml
Name: HigherSelf-Dev
Host: localhost
Port: 22
Username: your-username
Environment: development
Tags: higherself, development, local
Startup Commands:
  - cd /path/to/project
  - source venv/bin/activate
  - ~/.termius_higherself/scripts/start_monitor.sh
```

#### 2. Monitoring Terminal
```yaml
Name: HigherSelf-Monitor
Host: localhost
Port: 22
Username: your-username
Environment: monitoring
Tags: higherself, monitoring, github-actions
Startup Commands:
  - ~/.termius_higherself/scripts/start_build_monitor.sh
```

#### 3. Production Environment
```yaml
Name: HigherSelf-Production
Host: your-production-server.com
Port: 22
Username: ubuntu
Environment: production
Tags: higherself, production, aws
SSH Key: HigherSelf Network Server Key
Jump Host: bastion-host (if applicable)
```

### Terminal Layouts

#### Development Layout
- **Terminal 1**: Code development and git operations
- **Terminal 2**: Local server monitoring (`npm run dev` or `python main.py`)
- **Terminal 3**: GitHub Actions monitoring
- **Terminal 4**: Log monitoring (`tail -f logs/app.log`)

#### Deployment Layout
- **Terminal 1**: Terragrunt planning (`terragrunt plan`)
- **Terminal 2**: Deployment execution (`terragrunt apply`)
- **Terminal 3**: AWS resource monitoring
- **Terminal 4**: Application health checks

### Custom Snippets

```bash
# Quick deployment commands
hs-deploy-staging: cd /opt/higherself && ./deploy.sh staging
hs-deploy-prod: cd /opt/higherself && ./deploy.sh production
hs-logs: tail -f /var/log/higherself/*.log
hs-status: systemctl status higherself-* && docker ps

# Terragrunt workflow snippets
tg-plan-all: terragrunt run-all plan
tg-apply-all: terragrunt run-all apply
tg-destroy-dev: cd dev && terragrunt destroy
aws-secrets-sync: ./scripts/sync-secrets.sh

# GitHub Actions monitoring
gh-actions-status: gh run list --limit 10
gh-actions-logs: gh run view --log
gh-actions-rerun: gh run rerun
```

## Monitoring & Notifications

### Real-time Build Status Monitor

```bash
# Start the build status monitor
python3 ~/.termius_higherself/scripts/build_status_monitor.py \
    --token $GITHUB_TOKEN \
    --owner Utak-West \
    --repo The-HigherSelf-Network-Server \
    --interval 30
```

Features:
- Real-time workflow status updates
- Detailed job-level monitoring
- Color-coded status indicators
- Duration tracking
- Actor and commit information

### Terminal Session Management

```bash
# Register a terminal session for notifications
curl -X POST http://localhost:8000/api/termius/sessions/register \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "unique-session-id",
    "user_id": "your-username",
    "host": "localhost",
    "environment": "development"
  }'

# Get active sessions
curl http://localhost:8000/api/termius/sessions

# Get notification history
curl http://localhost:8000/api/termius/notifications/history?limit=20
```

### Custom Notifications

```bash
# Send custom notification
curl -X POST http://localhost:8000/api/termius/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Deployment to staging completed successfully",
    "status": "success",
    "environment": "staging"
  }'
```

## Advanced Features

### Team Collaboration

1. **Shared Connection Profiles**:
   - Export connection profiles from Termius
   - Share with team members via secure channels
   - Use team vaults for SSH keys and credentials

2. **Role-Based Access**:
   ```yaml
   Admin: Full access to all environments
   Developer: Access to development and staging
   DevOps: Full access with deployment permissions
   Viewer: Read-only access to logs and monitoring
   ```

3. **Notification Filtering**:
   - Environment-specific notifications
   - User-specific filtering
   - Priority-based alerts

### Integration with CI/CD Pipeline

The GitHub Actions workflow automatically:
1. Builds and tests the application
2. Runs security scans
3. Deploys to staging/production
4. Sends notifications to registered Termius sessions
5. Updates deployment status in Notion

### Webhook Security

```bash
# Generate webhook secret
openssl rand -hex 32

# Verify webhook signatures (implemented in the API)
# The webhook endpoint validates GitHub signatures for security
```

## Troubleshooting

### Common Issues

1. **GitHub Token Permissions**:
   ```bash
   # Required scopes for GitHub token:
   - repo (full repository access)
   - workflow (workflow access)
   - read:org (organization read access)
   ```

2. **Webhook Connectivity**:
   ```bash
   # Test webhook endpoint
   curl -X POST http://localhost:8000/api/termius/test/notification

   # Check webhook logs
   tail -f ~/.termius_higherself/logs/webhook.log
   ```

3. **Python Dependencies**:
   ```bash
   # Reinstall dependencies
   pip3 install -r ~/.termius_higherself/requirements.txt
   ```

4. **SSH Connection Issues**:
   ```bash
   # Debug SSH connection
   ssh -vvv user@host

   # Check key permissions
   chmod 600 ~/.ssh/higherself_network_server
   chmod 700 ~/.ssh/
   ```

### Log Files

- Monitor logs: `~/.termius_higherself/logs/monitor.log`
- Webhook logs: `~/.termius_higherself/logs/webhook.log`
- Build monitor logs: `~/.termius_higherself/logs/build_monitor.log`

### Support Commands

```bash
# Check service status
curl http://localhost:8000/api/termius/status

# View active terminal sessions
curl http://localhost:8000/api/termius/sessions

# Test notification system
~/.termius_higherself/scripts/termius_monitor.sh test

# Restart monitoring services
pkill -f termius_monitor && ~/.termius_higherself/scripts/start_monitor.sh
```

## Next Steps

1. **Enhanced Monitoring**: Integrate with AWS CloudWatch and Grafana
2. **Mobile Notifications**: Extend to Termius mobile apps
3. **Slack Integration**: Add Slack notifications alongside Termius
4. **Custom Dashboards**: Create web-based monitoring dashboards
5. **Automated Responses**: Implement automated incident response

For additional support, refer to the main project documentation or create an issue in the GitHub repository.