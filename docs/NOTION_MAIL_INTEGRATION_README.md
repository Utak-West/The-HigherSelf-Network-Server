# HigherSelf Network Server - Notion Mail Integration

## Overview

The Notion Mail Integration provides automated email classification and workflow automation for the HigherSelf Network Server's multi-entity business structure. This system intelligently categorizes incoming emails and triggers appropriate business workflows for The 7 Space (191 contacts), AM Consulting (1,300 contacts), and HigherSelf Core (1,300 contacts).

## ✅ Implementation Status

### **COMPLETED COMPONENTS**

#### 🔧 Core Service Implementation
- ✅ **NotionMailIntegrationService** - Complete email classification and workflow automation service
- ✅ **Email Classification Engine** - AI-powered classification with business rule validation
- ✅ **Business Entity Boundary Enforcement** - Strict separation between business entities
- ✅ **Workflow Automation Integration** - Seamless integration with existing workflow systems

#### 📋 Email Classification Configuration
- ✅ **8 Classification Categories** - All categories implemented with JSON configurations:
  1. **A.M. Consulting** (Priority 1, Blue) - Business consulting emails
  2. **The HigherSelf Network** (Priority 2, Green) - Community platform emails
  3. **The 7 Space | Art Gallery** (Priority 3, Purple) - Art gallery operations
  4. **The 7 Space | Wellness Center** (Priority 4, Orange) - Wellness services
  5. **Technical** (Priority 5, Red) - System/technical communications
  6. **HigherSelf** (Priority 6, Teal) - Core nonprofit operations
  7. **Personal** (Priority 7, Yellow) - Personal communications
  8. **Other** (Priority 8, Gray) - Uncategorized emails

#### 🌐 API Endpoints
- ✅ **Health Check** - `/notion-mail/health` - Service status and configuration
- ✅ **Email Classification** - `/notion-mail/classify` - Classify individual emails
- ✅ **Workflow Processing** - `/notion-mail/workflow` - Manual workflow triggers
- ✅ **Category Information** - `/notion-mail/categories` - Get all categories and config
- ✅ **Statistics** - `/notion-mail/stats` - Performance metrics and statistics
- ✅ **Webhook Endpoint** - `/notion-mail/webhook/email-received` - Email provider integration

#### 🧪 Testing & Validation
- ✅ **Comprehensive Test Suite** - Full test coverage for all classification scenarios
- ✅ **Validation Script** - Complete deployment validation and health checks
- ✅ **Business Entity Boundary Tests** - Ensures strict entity separation
- ✅ **Performance Testing** - Classification speed and accuracy validation

#### ⚙️ Configuration & Deployment
- ✅ **Environment Configuration** - Production and development templates
- ✅ **Docker Integration** - Seamless VM deployment configuration
- ✅ **Secrets Management** - AWS Secrets Manager integration
- ✅ **Monitoring Integration** - Prometheus metrics and Grafana dashboards

## 🏗️ Architecture

### Email Classification Flow
```
Incoming Email → Business Rules Check → AI Classification → Entity Validation → Workflow Trigger
```

### Business Entity Mapping
- **AM Consulting** → `am_consulting` entity (4-hour response SLA)
- **The 7 Space Gallery/Wellness** → `the_7_space` entity (24-hour response SLA)
- **HigherSelf Network/Core** → `higherself_core` entity (12-hour response SLA)

### Classification Confidence Thresholds
| Category | Target Accuracy | Confidence Threshold | Expected Daily Volume |
|----------|----------------|---------------------|----------------------|
| A.M. Consulting | 95% | 0.95 | 15 emails |
| The HigherSelf Network | 95% | 0.95 | 20 emails |
| The 7 Space \| Art Gallery | 92% | 0.92 | 8 emails |
| The 7 Space \| Wellness Center | 88% | 0.88 | 4 emails |
| Technical | 90% | 0.90 | 10 emails |
| HigherSelf | 85% | 0.85 | 6 emails |
| Personal | 80% | 0.80 | 25 emails |
| Other | 70% | 0.70 | 30 emails |

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Copy and configure environment variables
cp .env.vm.production.template .env.vm.production

# Set required variables
NOTION_API_TOKEN=your_notion_api_token
OPENAI_API_KEY=your_openai_api_key
ENABLE_EMAIL_AUTO_CLASSIFICATION=true
ENABLE_EMAIL_WORKFLOW_AUTOMATION=true
EMAIL_CLASSIFICATION_CONFIDENCE_THRESHOLD=0.7
```

### 2. Deploy with Docker
```bash
# Build and deploy VM production environment
docker-compose -f docker-compose.vm.yml up -d

# Verify deployment
docker-compose -f docker-compose.vm.yml ps
```

### 3. Validate Installation
```bash
# Run validation script
python scripts/validate_notion_mail_integration.py

# Check API health
curl http://localhost:8000/notion-mail/health
```

## 📡 API Usage

### Classify Email
```bash
curl -X POST "http://localhost:8000/notion-mail/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_email": "ceo@businesscorp.com",
    "sender_name": "Business CEO",
    "subject": "Strategic Consulting Proposal",
    "body": "We need consulting services for business transformation...",
    "message_id": "unique_message_id"
  }'
```

### Get Categories
```bash
curl "http://localhost:8000/notion-mail/categories"
```

### View Statistics
```bash
curl "http://localhost:8000/notion-mail/stats"
```

## 🔧 Configuration

### Email Classification Rules
Each category has a JSON configuration file in `config/email_classification/`:
- Keywords for content matching
- Domain patterns for sender validation
- Business rules for confidence scoring
- Exclusion rules for boundary enforcement

### Business Entity Workflows
Integration with existing workflow automation:
- **AM Consulting**: Lead qualification, proposal follow-up, consultation booking
- **The 7 Space**: Artist discovery, exhibition inquiries, wellness session booking
- **HigherSelf Core**: Community onboarding, content engagement, platform features

### Response Time SLAs
- **AM Consulting**: 4 hours (highest priority)
- **The 7 Space**: 24 hours (gallery and wellness)
- **HigherSelf Core**: 12 hours (network and nonprofit)

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
python -m pytest tests/test_notion_mail_integration.py -v

# Run specific test category
python -m pytest tests/test_notion_mail_integration.py::TestNotionMailIntegrationService::test_email_classification_am_consulting -v
```

### Validation Checklist
- [ ] All 8 classification categories working correctly
- [ ] Business entity boundaries strictly enforced
- [ ] Workflow automation triggers functioning
- [ ] API endpoints accessible and responsive
- [ ] Configuration files loaded and valid
- [ ] Performance meets target thresholds

## 📊 Monitoring

### Prometheus Metrics
- Email classification requests per category
- Classification confidence scores
- Workflow automation success rates
- Response time performance

### Grafana Dashboards
- Real-time classification statistics
- Business entity performance metrics
- SLA compliance monitoring
- Error rate tracking

## 🔒 Security

### Secrets Management
- Notion API tokens stored in AWS Secrets Manager
- OpenAI API keys encrypted and rotated
- Webhook secrets for secure email provider integration

### Business Entity Isolation
- Strict separation between AM Consulting, The 7 Space, and HigherSelf Core
- No cross-contamination of contact data or workflows
- Entity-specific access controls and permissions

## 🚨 Troubleshooting

### Common Issues

#### Classification Accuracy Low
1. Check classification configuration files
2. Verify AI provider API connectivity
3. Review business rule configurations
4. Validate training data quality

#### Workflow Automation Not Triggering
1. Verify confidence thresholds are met
2. Check business entity mapping
3. Validate workflow service connectivity
4. Review background task processing

#### API Endpoints Not Responding
1. Check service health status
2. Verify environment configuration
3. Review Docker container logs
4. Validate network connectivity

### Debug Commands
```bash
# Check service logs
docker logs higherself-server-vm

# Validate configuration
python scripts/validate_notion_mail_integration.py

# Test classification manually
python -c "
from services.notion_mail_integration import *
import asyncio
# Test classification code here
"
```

## 📈 Performance Optimization

### Classification Speed
- Average processing time: <500ms per email
- Concurrent processing support
- Caching for frequent patterns
- Optimized AI model usage

### Scalability
- Horizontal scaling support
- Load balancing capabilities
- Database connection pooling
- Background task processing

## 🔄 Maintenance

### Regular Tasks
- Monitor classification accuracy
- Review and update business rules
- Rotate API keys and secrets
- Update AI model configurations
- Backup classification data

### Updates and Improvements
- Add new classification categories as needed
- Refine business rules based on performance
- Optimize AI prompts for better accuracy
- Enhance workflow automation triggers

## 📞 Support

For technical support or questions about the Notion Mail Integration:

1. **Check Documentation**: Review this README and related docs
2. **Run Validation**: Use the validation script to identify issues
3. **Review Logs**: Check application and service logs
4. **Test Configuration**: Verify environment and classification configs

The Notion Mail Integration is now fully implemented and ready for production use with the HigherSelf Network Server multi-entity business structure.
