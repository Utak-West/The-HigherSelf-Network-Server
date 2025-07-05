# Enhanced Business-Specific Productivity Snippets

## 🎯 Overview

This enhanced snippets collection integrates seamlessly with The HigherSelf Network Server infrastructure, providing comprehensive technical management capabilities alongside existing business operations. The collection now includes **102 total snippets** (60 new + 42 original) organized across business entities and technical domains.

## 📊 Snippet Categories & Counts

### Business Entities
- **The 7 Space** (!7 prefix): 12 snippets (7 original + 5 technical)
- **A.M. Consulting** (!am prefix): 12 snippets (7 original + 5 technical)  
- **HigherSelf** (!hs prefix): 11 snippets (6 original + 5 technical)

### Technical Infrastructure
- **HigherSelf Network** (!hsn prefix): 22 snippets (10 original + 12 enhanced)
- **1Password Integration** (!1p prefix): 8 snippets (NEW)
- **Termius Integration** (!term prefix): 10 snippets (NEW)

### Cross-Business Operations
- **Cross-Business** (!x prefix): 13 snippets (3 original + 10 enhanced)
- **Business Operations**: 6 snippets (4 original + 2 enhanced)
- **Integrations**: 8 snippets (2 original + 6 enhanced)

## 🚀 Key Features

### 🔐 Security-First Design
- **1Password CLI Integration**: All sensitive data retrieved via `op read` commands
- **Environment Variable Placeholders**: Uses `${VAR_NAME}` for configuration
- **Credential Rotation**: Built-in API key and secret rotation procedures
- **Audit Logging**: Comprehensive security audit and compliance monitoring

### 🎤 Voice Control Integration
- **Termius Voice Commands**: Voice-activated server management
- **Natural Language Triggers**: "Start server", "Check status", "Deploy"
- **Automated Responses**: Real-time feedback and status updates
- **Session Recording**: Full audit trail of voice-activated operations

### 📊 Comprehensive Monitoring
- **Grafana Dashboards**: Pre-configured monitoring dashboards
- **Prometheus Metrics**: Real-time system and business metrics
- **Health Checks**: Multi-level health monitoring (system, database, integrations)
- **Performance Analytics**: Cross-business performance tracking

### 🤖 Agent Management
- **7 Named Personalities**: Nyra, Solari, Ruvo, Liora, Sage, Elan, Zevi
- **Agent Health Monitoring**: Individual agent status and performance
- **Automated Restart**: Self-healing agent management
- **Communication Tracking**: Inter-agent communication monitoring

## 🛠️ Technical Infrastructure Snippets

### Server Management (!hsn prefix)
```bash
!hsnstatus      # Complete server status overview
!hsndocker      # Docker deployment and management
!hsnmigrate     # Database migrations and setup
!hsnagents      # Agent personality management
!hsnmonitor     # Monitoring dashboard access
!hsnsecurity    # Security and credential management
```

### Database Operations
```bash
!hsnnotion      # Notion database synchronization
!hsnvector      # Vector database queries
!7backup        # The 7 Space data backup
!ambackup       # A.M. Consulting data backup
!hsbackup       # HigherSelf data backup
```

### Monitoring & Analytics
```bash
!7monitor       # The 7 Space monitoring dashboard
!amdata         # A.M. Consulting analytics
!hsanalytics    # HigherSelf community analytics
!xperformance   # Cross-business performance metrics
!analytics      # Comprehensive business analytics
```

## 🔑 1Password Integration (!1p prefix)

### Credential Management
```bash
!1papi          # Retrieve API keys securely
!1pdb           # Database credentials
!1pssh          # SSH key management
!1pinject       # Environment file injection
!1pservice      # Service account tokens
!1pwebhook      # Webhook secrets
!1pmonitor      # Monitoring credentials
!1pemergency    # Emergency access procedures
```

### Usage Example
```bash
# Secure API call with 1Password
curl -H "Authorization: Bearer $(op read 'op://HigherSelf/HSN-API/token')" \
  http://localhost:8000/api/status
```

## 🖥️ Termius Integration (!term prefix)

### Voice-Activated Commands
```bash
!termvoicestart    # "Start HigherSelf Server"
!termvoicestop     # "Stop HigherSelf Server"  
!termvoicestatus   # "Check Server Status"
!termvoicedeploy   # "Deploy Server"
!termvoicelogs     # "Show Server Logs"
```

### SSH Management
```bash
!termserver     # SSH connection profile
!termtunnel     # SSH tunnel management
!termtransfer   # File transfer operations
!termsession    # Session management with tmux
!termmonitor    # Integrated monitoring dashboard
```

## 🔄 Cross-Business Operations (!x prefix)

### Enhanced Collaboration
```bash
!xtech          # Technical integration status
!xsync          # Data synchronization
!xperformance   # Performance monitoring
!xsecurity      # Security auditing
!xbackup        # Coordinated backup
!xincident      # Incident response
!xcapacity      # Capacity planning
```

## 📋 Business Operations Enhancements

### Quality Assurance & Compliance
```bash
!quality        # Enhanced quality checklist
!compliance     # Compliance monitoring
!analytics      # Performance analytics
!emergency      # Emergency contacts with system status
```

### Client Management
```bash
!onboard        # Enhanced onboarding with technical setup
!weekreview     # Weekly review with technical metrics
```

## 🔗 Integration Enhancements

### External Service Management
```bash
!notion         # Notion API operations
!highlevel      # High Level CRM integration
!supabase       # Supabase database operations
!healthcheck    # Comprehensive health check
```

## 🚀 Getting Started

### 1. Import Snippets
```bash
# Import into Raycast
raycast://extensions/raycast/snippets/import?path=enhanced_business_technical_snippets.json

# Or manually import the JSON file through Raycast preferences
```

### 2. Configure 1Password
```bash
# Install 1Password CLI
brew install --cask 1password-cli

# Authenticate
op signin

# Test credential access
op read "op://HigherSelf/HSN-API/token"
```

### 3. Setup Termius Integration
```bash
# Configure SSH profiles in Termius
# Import voice control snippets
# Enable voice recognition in Termius settings
```

### 4. Verify Integration
```bash
# Test server connection
!hsnstatus

# Test monitoring access
!hsnmonitor

# Test voice control (in Termius)
"Check server status"
```

## 🔧 Environment Configuration

### Required Environment Variables
```bash
ENVIRONMENT=development|staging|production
HSN_API_KEY=${HSN_API_KEY}
NOTION_API_TOKEN=${NOTION_API_TOKEN}
MONGODB_URI=${MONGODB_URI}
GRAFANA_URL=http://localhost:3000
PROMETHEUS_URL=http://localhost:9090
```

### 1Password Vault Structure
```
HigherSelf/
├── HSN-API/token
├── Notion/api-token
├── MongoDB/username
├── MongoDB/password
├── Grafana/username
├── Grafana/password
├── SSH-Keys/higherself-server
└── Emergency/Access-Instructions/procedure
```

## 📊 Monitoring Integration

### Grafana Dashboards
- **Main Overview**: `http://localhost:3000/d/higherself-overview`
- **Agent Performance**: `http://localhost:3000/d/agent-performance`
- **Cross-Business**: `http://localhost:3000/d/cross-business-overview`
- **The 7 Space**: `http://localhost:3000/d/the7space-overview`
- **A.M. Consulting**: `http://localhost:3000/d/amconsulting-overview`
- **HigherSelf**: `http://localhost:3000/d/higherself-overview`

### Health Check Endpoints
- **Main Health**: `http://localhost:8000/health`
- **Database Health**: `http://localhost:8000/health/database`
- **Agent Health**: `http://localhost:8000/api/agents/health`
- **Integration Health**: `http://localhost:8000/health/integrations`

## 🎯 Usage Examples

### Daily Operations
```bash
# Morning server check
!hsnstatus
!hsnmonitor

# Client onboarding
!onboard
!quality

# Cross-business coordination
!xtech
!xperformance
```

### Emergency Response
```bash
# Incident response
!xincident
!emergency
!1pemergency

# System recovery
!hsndocker
!hsnmigrate
!healthcheck
```

### Weekly Review
```bash
# Business review
!weekreview
!analytics
!compliance

# Technical review
!xperformance
!xcapacity
!xsecurity
```

## 🔒 Security Best Practices

1. **Never hardcode credentials** - Always use 1Password integration
2. **Use environment-specific configurations** - Separate dev/staging/prod
3. **Enable audit logging** - Track all administrative actions
4. **Regular security audits** - Use `!xsecurity` for compliance checks
5. **Emergency access procedures** - Follow `!1pemergency` protocols

## 📞 Support & Troubleshooting

### Common Issues
- **1Password CLI not authenticated**: Run `op signin`
- **Server not responding**: Check `!hsnstatus` and `!hsndocker`
- **Voice control not working**: Verify Termius voice settings
- **Monitoring dashboards inaccessible**: Check `!1pmonitor` credentials

### Getting Help
- **Technical Issues**: Use `!emergency` for contact information
- **Integration Problems**: Run `!healthcheck` for diagnostics
- **Performance Issues**: Check `!xperformance` dashboard

---

**Total Snippets**: 102 (60 new technical + 42 original business)
**Security**: 1Password CLI integrated throughout
**Voice Control**: Termius voice command support
**Monitoring**: Comprehensive Grafana/Prometheus integration
**Cross-Business**: Enhanced collaboration and data synchronization
