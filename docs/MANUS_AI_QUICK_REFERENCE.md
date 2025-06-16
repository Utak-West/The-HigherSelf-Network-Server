# Manus AI Quick Reference: The HigherSelf Network Server

## System Overview

**The HigherSelf Network Server** is an enterprise-grade proprietary automation platform serving The HigherSelf Network community with ethical, human-centered technology.

### Core Architecture
- **Language**: Python 3.10+ with FastAPI
- **Central Hub**: Notion (16 interconnected databases)
- **AI Framework**: Named agent personalities with specialized capabilities
- **Integration Pattern**: Hub-and-spoke with bidirectional synchronization
- **Deployment**: Docker containers with enterprise infrastructure

---

## Named Agent Personalities

| Agent | Role | Personality | Primary Function |
|-------|------|-------------|------------------|
| **Grace Fields** | Master Orchestrator | Harmonious & Coordinating | System coordination, customer service excellence |
| **Nyra** | Lead Capture Specialist | Intuitive & Responsive | Lead processing, qualification, nurturing |
| **Solari** | Booking & Order Manager | Clear & Luminous | Appointment scheduling, order management |
| **Ruvo** | Task Orchestrator | Grounded & Task-driven | Project coordination, deadline management |
| **Liora** | Marketing Strategist | Elegant & Strategic | Campaign management, performance tracking |
| **Sage** | Community Curator | Warm & Connected | Community engagement, relationship building |
| **Elan** | Content Choreographer | Creative & Adaptive | Content creation, distribution management |
| **Zevi** | Audience Analyst | Analytical & Sharp | Data analysis, audience segmentation |
| **Atlas** | Knowledge Specialist | Knowledgeable & Resourceful | RAG-enhanced knowledge retrieval |

---

## Key Technical Components

### Database Architecture (16 Databases)

**Core Operations:**
1. Business Entities Registry
2. Contacts & Profiles  
3. Community Hub
4. Products & Services

**Workflow Management:**
5. Active Workflows
6. Marketing Campaigns
7. Master Tasks
8. Feedback & Surveys
9. Rewards & Bounties

**Agent & System Support:**
10. Agent Communication
11. Agent Registry
12. API Integrations
13. Data Transformations
14. Notification Templates
15. Use Cases Library
16. Workflows Library

### Technology Stack

**Core Platform:**
- FastAPI with Uvicorn/Gunicorn
- Pydantic v2 for data validation
- Async/await throughout
- Docker containerization

**Data Layer:**
- Notion (central hub)
- Redis (caching/messaging)
- MongoDB (document storage)
- Supabase (vector storage)
- Enterprise DB support (PostgreSQL, MySQL, etc.)

**AI & ML:**
- OpenAI, Anthropic (primary providers)
- Hugging Face Pro (specialized NLP)
- sentence-transformers (local embeddings)
- Custom RAG pipeline

---

## Integration Ecosystem

### Production-Ready Integrations

**AI & NLP:**
- Hugging Face Pro (advanced NLP processing)
- MCP Tools (standardized AI interfaces)
- OpenAI & Anthropic (premium AI capabilities)

**Business Operations:**
- Notion (central data hub)
- Typeform (form data collection)
- WooCommerce (e-commerce)
- Amelia (appointment booking)

**Community & Content:**
- Circle.so/BetterMode (community platforms)
- Beehiiv (newsletter marketing)
- The7Space (WordPress management)

**Specialized Workflows:**
- CapCut-Pipit (video editing + payments)
- GoHighLevel (CRM with multi-account support)
- Zapier/N8N (workflow automation)

### Integration Patterns

**Data Flow:**
```
External Event → Webhook → Agent Processing → Notion Storage
Notion Update → Agent Notification → External System Sync
```

**Service Architecture:**
- Base service classes with common functionality
- Integration Manager for centralized lifecycle management
- Health monitoring and automatic failover
- Standardized authentication and error handling

---

## Workflow Orchestration

### Grace Fields Coordination Levels

**Level 1 - Standard Delegation (1-2 agents):**
- Routine requests handled by single agent
- Standard resolution procedures
- Automated response generation

**Level 2 - Multi-Agent Coordination (3-4 agents):**
- Complex issues requiring specialists
- Cross-functional collaboration
- Escalation decision making

**Level 3 - Full Network Response (5+ agents):**
- High-impact situations
- All-hands coordination
- Executive notification

**Level 4 - Human Escalation:**
- Issues requiring human judgment
- Legal or compliance matters
- VIP customer concerns

### Common Workflow Patterns

**Lead-to-Customer Journey:**
Nyra (capture) → Ruvo (tasks) → Solari (booking) → Grace Fields (coordination)

**Marketing Campaign Flow:**
Zevi (analysis) → Liora (strategy) → Elan (content) → Sage (distribution)

**Knowledge Support Chain:**
Atlas (retrieval) → Grace Fields (coordination) → All Agents (enhanced responses)

---

## RAG Knowledge System

### Atlas Agent Capabilities
- Semantic search across organizational knowledge
- Multi-source content indexing (Notion, web, voice)
- Context-aware response generation
- Source citation and traceability

### Vector Storage Architecture
- Supabase with pgvector extension
- Multiple chunking strategies (simple, sentence, paragraph, semantic)
- Similarity search with configurable thresholds
- Metadata indexing and filtering

### Knowledge Sources
- 16 Notion databases
- Web content via Crawl4AI
- Voice commands through Aqua Voice
- Document processing with OCR

---

## Deployment & Operations

### Container Architecture
- **windsurf-agent**: Main application
- **celery-worker**: Background tasks
- **celery-beat**: Scheduled tasks
- **nginx**: Reverse proxy with SSL
- **mongodb**: Document storage
- **redis**: Caching and messaging
- **consul**: Service discovery
- **prometheus/grafana**: Monitoring

### Critical Environment Variables
```bash
NOTION_API_TOKEN=your_notion_token
NOTION_PARENT_PAGE_ID=parent_page_id
WEBHOOK_SECRET=secure_webhook_secret
REDIS_URI=redis://redis:6379/0
MONGODB_URI=mongodb://mongodb:27017/higherselfnetwork
```

### Health Monitoring
- `/health` endpoint for service status
- Redis and MongoDB connection checks
- Agent registration verification
- Integration health monitoring

---

## Security & Best Practices

### Security Framework
- API key management with rotation
- Webhook signature verification
- SSL/TLS for all communications
- Role-based access control
- Data encryption in transit and at rest

### Development Standards
- Pydantic data validation throughout
- Comprehensive error handling
- Structured logging with context
- Type hints and documentation
- Async/await patterns

### Monitoring & Observability
- Structured logging with correlation IDs
- Metrics collection and alerting
- Performance monitoring
- Health checks and automatic recovery

---

## Common Operations

### System Health Check
```bash
curl http://localhost:8000/health
docker-compose logs -f
docker stats
```

### Service Management
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f windsurf-agent

# Restart specific service
docker-compose restart windsurf-agent
```

### Database Operations
```bash
# Initialize Notion databases
python -m tools.notion_db_setup

# Backup configuration
cp .env .env.backup-$(date +%Y%m%d)

# Export Notion data
python -m tools.notion_backup
```

---

## Troubleshooting Quick Guide

### Common Issues

**Notion Connection Fails:**
- Check `NOTION_API_TOKEN` validity
- Verify integration permissions
- Test network connectivity

**Agents Not Processing:**
- Check agent registration in Notion
- Verify workflow templates exist
- Review agent communication logs

**Integration Failures:**
- Validate webhook endpoints
- Check external service credentials
- Review API rate limits

**Performance Issues:**
- Monitor resource utilization
- Check database query performance
- Review caching effectiveness

### Log Analysis
```bash
# Application logs
tail -f logs/app.log

# Container logs
docker-compose logs -f

# Specific service logs
docker-compose logs -f windsurf-agent
```

---

## Business Context

### Target Markets
- Creative & Artistic Services
- Wellness & Health Organizations  
- Professional Consulting Firms
- Educational & Training Providers
- Design & Renovation Services
- Technology & Digital Services

### Core Values
- **Community**: Technology enhances human connections
- **Ecosystem**: Comprehensive integration support
- **Spirit**: Ethical practices with transparency

### Competitive Advantages
- Named agent personalities with distinct characteristics
- Community-focused design philosophy
- Multi-database enterprise support
- Sophisticated workflow orchestration
- Ethical data practices with full transparency

---

This quick reference provides Manus AI with essential knowledge for effective collaboration with The HigherSelf Network Server ecosystem.
