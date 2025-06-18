# 🚀 HigherSelf Network Server - Termius Implementation Guide

## ⚡ Quick Start (30 Minutes to Operational)

### Prerequisites Checklist
- [ ] Termius Pro subscription active
- [ ] SSH keys generated for each environment
- [ ] AWS CLI configured with appropriate profiles
- [ ] Docker and Docker Compose running locally
- [ ] HigherSelf Network Server repository cloned

---

## 🎯 Phase 1: Development Environment (30 minutes)

### Step 1: Import Development Configuration (5 minutes)

1. **Open Termius Pro**
2. **Create New Vault**: "HigherSelf Development"
3. **Import Host Configuration**:
   ```bash
   # Copy the development host configuration
   cp termius-setup/hosts-development.json ~/termius-import/
   ```
4. **In Termius**: Settings → Import → Select `hosts-development.json`

### Step 2: Set Up SSH Keys (10 minutes)

1. **Generate Development SSH Key**:
   ```bash
   # Generate ED25519 key for development
   ssh-keygen -t ed25519 -f ~/.ssh/higherself_dev_ed25519 -C "higherself-development"
   
   # Add to SSH agent
   ssh-add ~/.ssh/higherself_dev_ed25519
   
   # Copy public key (add to your local authorized_keys if needed)
   cat ~/.ssh/higherself_dev_ed25519.pub
   ```

2. **Import Key to Termius**:
   - Go to Keychain in Termius
   - Add New Key → Import from file
   - Select `~/.ssh/higherself_dev_ed25519`
   - Name: "HigherSelf Development Key"

### Step 3: Configure Port Forwarding (5 minutes)

1. **Import Port Forwarding Rules**:
   ```bash
   # Import the port forwarding configuration
   cp termius-setup/port-forwarding-rules.json ~/termius-import/
   ```

2. **In Termius**:
   - Go to Port Forwarding
   - Import configuration
   - Enable "Development Full Stack" group

### Step 4: Import Docker Snippets (5 minutes)

1. **Import Snippet Library**:
   ```bash
   # Copy Docker snippets
   cp termius-setup/snippets-docker.json ~/termius-import/
   ```

2. **In Termius**:
   - Go to Snippets
   - Import → Select `snippets-docker.json`
   - Verify snippets are available

### Step 5: Test Development Setup (5 minutes)

1. **Connect to Development Host**:
   - Select "HigherSelf Development (Local Docker)"
   - Connect (should auto-start port forwarding)

2. **Run Essential Snippets**:
   ```bash
   # Start the stack
   Run snippet: "🚀 Start HigherSelf Stack"
   
   # Wait 30 seconds, then check health
   Run snippet: "🏥 Complete Health Check"
   
   # Test quick access
   Run snippet: "⚡ Quick Service Test"
   ```

3. **Verify Access**:
   - Open browser: http://localhost:8000/health
   - Should see HigherSelf API health response
   - Port forwarding should show active connections

---

## 🎯 Phase 2: Staging Environment (1 hour)

### Step 1: AWS Integration Setup (20 minutes)

1. **Configure AWS Secrets Manager**:
   ```bash
   # Create IAM policy for Termius
   aws iam create-policy --policy-name TermiusSecretsAccess \
     --policy-document file://termius-setup/iam-policy.json
   
   # Create secrets for staging
   aws secretsmanager create-secret \
     --name higherself/staging/ssh-keys/main-key \
     --description "HigherSelf staging SSH key"
   
   # Generate and store staging SSH key
   ssh-keygen -t ed25519 -f ~/.ssh/higherself_staging_ed25519 -C "higherself-staging"
   aws secretsmanager put-secret-value \
     --secret-id higherself/staging/ssh-keys/main-key \
     --secret-string file://~/.ssh/higherself_staging_ed25519
   ```

2. **Configure AWS Profiles**:
   ```bash
   # Add staging profile to AWS config
   aws configure set profile.higherself-staging.region us-east-1
   aws configure set profile.higherself-staging.role_arn arn:aws:iam::STAGING-ACCOUNT:role/TermiusAccess
   ```

### Step 2: Import Staging Configuration (15 minutes)

1. **Update Host Addresses**:
   ```bash
   # Edit staging hosts configuration with your actual server addresses
   nano termius-setup/hosts-staging.json
   # Update: bastion-staging.higherself.com with your actual bastion host
   # Update: staging.higherself.internal with your actual staging server
   ```

2. **Import Staging Hosts**:
   - In Termius: Create new vault "HigherSelf Staging"
   - Import `hosts-staging.json`
   - Configure SSH keys from AWS Secrets Manager

### Step 3: Import Terraform Snippets (10 minutes)

1. **Import Infrastructure Snippets**:
   ```bash
   cp termius-setup/snippets-terraform.json ~/termius-import/
   ```

2. **In Termius**:
   - Import terraform snippets
   - Update paths in snippets to match your repository location

### Step 4: Test Staging Access (15 minutes)

1. **Test Bastion Connection**:
   - Connect to "HigherSelf Staging Bastion Host"
   - Verify SSH key authentication works

2. **Test Port Forwarding**:
   - Enable staging port forwarding rules
   - Test access to staging services

3. **Run Infrastructure Snippets**:
   ```bash
   # Test Terraform staging operations
   Run snippet: "📋 Plan Staging Deployment"
   ```

---

## 🎯 Phase 3: Production Security (2 hours)

### Step 1: Production Security Setup (45 minutes)

1. **Generate Production SSH Keys**:
   ```bash
   # Generate production key with strong passphrase
   ssh-keygen -t ed25519 -f ~/.ssh/higherself_prod_ed25519 -C "higherself-production"
   
   # Store in AWS Secrets Manager with encryption
   aws secretsmanager create-secret \
     --name higherself/production/ssh-keys/main-key \
     --description "HigherSelf production SSH key - CRITICAL" \
     --kms-key-id alias/higherself-production-secrets
   ```

2. **Configure MFA and Approval Workflows**:
   - Set up MFA requirement for production access
   - Configure approval workflows in your organization
   - Set up session recording and audit logging

### Step 2: Import Production Configuration (30 minutes)

1. **Update Production Hosts**:
   ```bash
   # Edit production configuration with actual server addresses
   nano termius-setup/hosts-production.json
   # Update all production server addresses
   # Configure security settings
   ```

2. **Import with Security Settings**:
   - Create "HigherSelf Production" vault with maximum security
   - Import production hosts
   - Configure restricted access and audit logging

### Step 3: Session Logging Setup (30 minutes)

1. **Configure CloudWatch Logging**:
   ```bash
   # Create CloudWatch log group
   aws logs create-log-group --log-group-name /higherself/termius/sessions
   
   # Set retention policy
   aws logs put-retention-policy \
     --log-group-name /higherself/termius/sessions \
     --retention-in-days 2555
   ```

2. **Enable Session Recording**:
   - Configure Termius to record all production sessions
   - Set up real-time monitoring and alerting
   - Test emergency access procedures

### Step 4: Test Production Access (15 minutes)

1. **Test Emergency Access**:
   - Verify MFA requirements work
   - Test approval workflow (if configured)
   - Verify session logging is active

2. **Document Access Procedures**:
   - Create runbook for production access
   - Document emergency procedures
   - Train team on security protocols

---

## 🔧 Advanced Configuration

### Custom Snippet Creation

1. **Create Custom Snippets**:
   ```bash
   # Example: Custom health check for your specific setup
   {
     "id": "custom-health-check",
     "name": "🏥 Custom HigherSelf Health Check",
     "command": "curl -s http://localhost:8000/health && mongosh --eval 'db.stats()' && redis-cli info"
   }
   ```

### Team Collaboration Setup

1. **Share Configurations**:
   - Export vault configurations
   - Share snippet libraries with team
   - Set up team access controls

2. **Mobile Access Configuration**:
   - Install Termius on mobile devices
   - Configure emergency access from mobile
   - Test mobile connectivity

---

## 🚨 Troubleshooting

### Common Issues and Solutions

1. **SSH Key Authentication Fails**:
   ```bash
   # Check SSH agent
   ssh-add -l
   
   # Re-add key if needed
   ssh-add ~/.ssh/higherself_dev_ed25519
   
   # Test connection manually
   ssh -i ~/.ssh/higherself_dev_ed25519 user@host
   ```

2. **Port Forwarding Not Working**:
   ```bash
   # Check for port conflicts
   lsof -i :8000
   
   # Kill conflicting processes
   kill -9 $(lsof -t -i:8000)
   
   # Restart port forwarding in Termius
   ```

3. **AWS Secrets Manager Access Issues**:
   ```bash
   # Verify AWS credentials
   aws sts get-caller-identity
   
   # Test secrets access
   aws secretsmanager get-secret-value --secret-id higherself/staging/ssh-keys/main-key
   ```

4. **Docker Services Not Starting**:
   ```bash
   # Check Docker status
   docker ps
   
   # Check logs
   docker-compose logs
   
   # Restart services
   docker-compose down && docker-compose up -d
   ```

---

## ✅ Success Verification

### Development Environment Checklist
- [ ] Can connect to localhost via Termius
- [ ] Port forwarding active for all services (8000, 27017, 6379, 3000, 9090, 8500)
- [ ] Docker snippets work correctly
- [ ] Health checks pass
- [ ] Can access Grafana at http://localhost:3000

### Staging Environment Checklist
- [ ] Can connect to staging bastion host
- [ ] Port forwarding works through bastion
- [ ] Terraform snippets execute successfully
- [ ] AWS integration functional
- [ ] Session logging active

### Production Environment Checklist
- [ ] MFA required for production access
- [ ] Session recording enabled
- [ ] Approval workflows configured
- [ ] Emergency access procedures documented
- [ ] Audit logging functional

---

## 📞 Support and Next Steps

### Immediate Support
- Check Termius documentation: https://termius.com/documentation
- Review AWS Secrets Manager setup
- Verify SSH key configurations

### Optimization Opportunities
- Set up automated health monitoring
- Configure additional monitoring dashboards
- Implement automated backup procedures
- Expand snippet libraries for specific workflows

### Team Training
- Schedule team training sessions
- Create internal documentation
- Set up regular security reviews
- Plan disaster recovery procedures

---

**🎉 Congratulations! Your HigherSelf Network Server Termius integration is now operational!**

For additional support or advanced configurations, refer to the individual configuration files in the `termius-setup/` directory.
