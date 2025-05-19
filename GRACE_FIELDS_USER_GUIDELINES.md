# Grace Fields Orchestrator - User Guidelines

This document provides comprehensive guidelines for configuring and using the Grace Fields orchestrator agent in The HigherSelf Network Server. Grace Fields serves as the central orchestration layer that coordinates all agent activities and complex workflows across the system.

## Table of Contents

- [1. Operational Parameters](#1-operational-parameters)
  - [1.1 Response Formatting Standards](#11-response-formatting-standards)
  - [1.2 Error Handling Protocols](#12-error-handling-protocols)
  - [1.3 Authentication Requirements](#13-authentication-requirements)
  - [1.4 Rate Limiting Configuration](#14-rate-limiting-configuration)
- [2. Event Routing Configuration](#2-event-routing-configuration)
  - [2.1 Routing Mechanisms](#21-routing-mechanisms)
  - [2.2 Fallback Mechanisms](#22-fallback-mechanisms)
  - [2.3 Security Validation](#23-security-validation)
  - [2.4 Logging Requirements](#24-logging-requirements)
- [3. Context Management](#3-context-management)
  - [3.1 Conversation History Management](#31-conversation-history-management)
  - [3.2 Redis Configuration](#32-redis-configuration)
  - [3.3 MongoDB Integration](#33-mongodb-integration)
  - [3.4 Workflow Tracking](#34-workflow-tracking)
- [4. Development Tools](#4-development-tools)
  - [4.1 VSCode Configuration](#41-vscode-configuration)
  - [4.2 CI/CD Pipeline Tools](#42-cicd-pipeline-tools)
  - [4.3 Testing Frameworks](#43-testing-frameworks)
  - [4.4 Monitoring Tools](#44-monitoring-tools)
- [5. Implementation Guidelines](#5-implementation-guidelines)
  - [5.1 Initialization and Configuration](#51-initialization-and-configuration)
  - [5.2 Event Processing Flow](#52-event-processing-flow)
  - [5.3 Performance Optimization](#53-performance-optimization)
  - [5.4 Security Best Practices](#54-security-best-practices)
- [6. Troubleshooting](#6-troubleshooting)
  - [6.1 Common Issues and Solutions](#61-common-issues-and-solutions)
  - [6.2 Diagnostic Tools](#62-diagnostic-tools)
  - [6.3 Support Resources](#63-support-resources)

## 1. Operational Parameters

### 1.1 Response Formatting Standards

Grace Fields must adhere to the following response formatting standards for all agent communications:

```json
{
  "message_type": "event_routing",
  "sender": {
    "agent_id": "GRACE_ORCHESTRATOR",
    "agent_name": "Grace Fields"
  },
  "recipient": {
    "agent_id": "TARGET_AGENT_ID",
    "agent_name": "TARGET_AGENT_NAME"
  },
  "message_id": "UUID",
  "timestamp": "ISO8601_TIMESTAMP",
  "priority": "PRIORITY_LEVEL",
  "payload": {
    "event_type": "EVENT_TYPE",
    "tracking_id": "TRACKING_ID",
    "data": {},
    "context": {},
    "expected_response": {}
  }
}
```

#### Key Parameters

| Parameter | Description | Valid Values |
|-----------|-------------|--------------|
| `message_type` | Descriptive action identifier | `"event_routing"`, `"error_notification"`, `"status_update"`, `"workflow_transition"` |
| `priority` | Message priority level | `"low"`, `"normal"`, `"high"`, `"critical"` |
| `tracking_id` | Unique identifier for event tracing | UUID format, must be preserved across the entire event lifecycle |

### 1.2 Error Handling Protocols

Grace Fields implements a multi-tiered error handling approach:

1. **Error Detection**:
   - Timeout monitoring for non-responsive agents (default: 30s)
   - Error response analysis to categorize error types
   - Data validation before agent processing

2. **Recovery Strategies**:
   - Retry logic with exponential backoff for transient failures
   - Circuit breaking for agents experiencing persistent issues
   - Agent failover using the defined fallback chains
   - Event persistence in Redis for recovery

3. **Error Response Format**:

```json
{
  "error": "ERROR_MESSAGE",
  "status": "error",
  "agent": "FAILED_AGENT_NAME",
  "tracking_id": "TRACKING_ID",
  "severity": "ERROR_SEVERITY",
  "recovery_attempted": true|false,
  "fallback_result": {}
}
```

#### Error Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| `"warning"` | Non-critical issue | Log and continue |
| `"error"` | Recoverable error | Retry or use fallback |
| `"critical"` | System-level failure | Alert admin and halt processing |

### 1.3 Authentication Requirements

Grace Fields requires the following authentication mechanisms:

1. **Inter-Agent Communication**:
   - All messages must include the sender's `agent_id`
   - Messages must be signed with the agent's API key
   - `X-Agent-ID` and `X-Target-Agent-ID` headers must be present in API requests

2. **External System Authentication**:
   - Webhook requests must include the `WEBHOOK_SECRET` in the `X-Webhook-Secret` header
   - API requests must include a valid API key in the `X-API-Key` header
   - JWT authentication for user-initiated requests

### 1.4 Rate Limiting Configuration

Grace Fields implements rate limiting to prevent system overload:

**Default Limits**:

| User Type | Requests per Minute | Burst Capacity |
|-----------|---------------------|----------------|
| Regular users | 60 | 20 |
| Business accounts | 120 | 30 |
| Admin users | 300 | 50 |
| API clients | 600 | 100 |

**Rate Limiting Configuration**:

```json
{
  "rate_limiting": {
    "enabled": true,
    "algorithm": "sliding_window",
    "storage": "redis",
    "default_limit": 60,
    "default_period": 60,
    "burst_capacity": 20,
    "high_load_threshold": 0.8
  }
}
```

**Priority Handling**:

- Critical messages bypass rate limiting
- High-priority messages get preferential processing

## 2. Event Routing Configuration

### 2.1 Routing Mechanisms

Grace Fields routes events to specialized agents using the following mechanisms:

**Direct Mapping**:

```python
# Event routing map - maps event types to agent names
self.event_routing = {
    # Nyra - Lead Capture events
    "new_lead": "Nyra",
    "typeform_webhook": "Nyra",

    # Solari - Booking & Order events
    "booking_created": "Solari",
    "order_created": "Solari",

    # Ruvo - Task Management events
    "workflow_status_changed": "Ruvo",
    "task_needed": "Ruvo",

    # Additional mappings for other agents...
}
```

**Pattern-Based Routing**:

- Extracts domain from event type (e.g., "lead_capture" → "lead")
- Maps domains to agents (e.g., "lead" → "Nyra")
- Automatically adds successful mappings to the routing map

**Capability-Based Routing**:

- Routes based on `required_capability` in event data
- Uses `agent_capabilities` registry to find capable agents
- Selects the most appropriate agent based on capability match

**Business Entity Routing**:

- Routes based on `business_entity_id` in event data
- Matches agents specifically configured for that business entity

### 2.2 Fallback Mechanisms

When primary routing fails, Grace Fields uses these fallback mechanisms:

**Agent Fallback Chains**:

```python
fallbacks = {
    "Nyra": ["Solari", "Zevi"],    # Lead capture fallbacks
    "Solari": ["Nyra", "Ruvo"],    # Booking fallbacks
    "Ruvo": ["Solari", "Liora"],   # Task fallbacks
    "Elan": ["Liora", "Sage"],     # Content fallbacks
    "Sage": ["Elan", "Zevi"],      # Community fallbacks
    "Zevi": ["Liora", "Nyra"],     # Audience fallbacks
    "Liora": ["Elan", "Zevi"]      # Marketing fallbacks
}
```

**AI Router Fallback**:

- When no agent can handle an event, delegates to AI router
- AI router uses content analysis to determine the best agent
- Adds successful routing to the routing map for future use

**Circuit Breaking**:

- Temporarily prevents routing to agents experiencing persistent issues
- Automatically routes to fallback agents during circuit break periods
- Default circuit break threshold: 5 failures in 60 seconds

### 2.3 Security Validation

Grace Fields enforces these security validations for inter-agent communication:

1. **Message Validation**:
   - Validates message structure against `AgentMessage` schema
   - Ensures all required fields are present and properly formatted
   - Verifies sender has permission to communicate with recipient

2. **Permission Checks**:
   - Verifies agent has permission to perform requested actions
   - Checks against agent capability registry
   - Enforces business entity access controls

3. **Data Sanitization**:
   - Sanitizes all input data before processing
   - Validates against expected schemas
   - Removes potentially harmful content

### 2.4 Logging Requirements

All agent interactions must be logged with the following information:

**Standard Log Format**:

```text
[TIMESTAMP] [LOG_LEVEL] [COMPONENT] [TRACKING_ID] Message
```

**Required Log Events**:

- Event receipt from external systems
- Event routing decisions
- Agent processing start/end
- Error conditions and recovery attempts
- Workflow transitions

**Log Storage**:

- All logs written to application log file
- Critical events stored in Notion for auditability
- Error logs sent to monitoring system

## 3. Context Management

### 3.1 Conversation History Management

Grace Fields maintains conversation history with users through:

**Session Management**:

- User sessions tracked with unique session IDs
- Session context maintained in Redis with TTL
- Session data includes user preferences and interaction history

**Conversation Context**:

- Previous messages stored in conversation context
- Context includes entity recognition results
- Intent tracking across multiple interactions

**Context Pruning**:

- Older context entries pruned based on relevance
- Critical context preserved for longer periods
- Context size limited to prevent memory issues

### 3.2 Redis Configuration

Grace Fields uses Redis for state persistence between sessions:

**Cache Hierarchy**:

| Cache Level | TTL | Content Type |
|-------------|-----|--------------|
| L1 Cache | 60s | Agent state, temporary data |
| L2 Cache | 300s | Notion data, API responses |
| L3 Cache | 3600s | Vector embeddings, stable data |
| Permanent Cache | 86400s | Configuration, reference data |

**Key Structures**:

| Key Pattern | Purpose | Example |
|-------------|---------|---------|
| `agent:{agent_id}:state` | Agent state storage | `agent:nyra:state` |
| `session:{session_id}:data` | User session data | `session:usr_123:data` |
| `workflow:{workflow_id}:state` | Workflow state | `workflow:wf_456:state` |
| `event:{tracking_id}:status` | Event tracking | `event:evt_789:status` |

**Pub/Sub Channels**:

- Agent notifications: `agent:{agent_id}:notifications`
- System events: `system:events`
- Workflow transitions: `workflow:{workflow_id}:transitions`

### 3.3 MongoDB Integration

Grace Fields uses MongoDB for long-term data storage:

**Collection Structure**:

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| `agents` | Agent configuration and state | `agent_id`, `capabilities`, `status` |
| `workflows` | Workflow definitions | `workflow_id`, `states`, `transitions` |
| `workflow_instances` | Active workflow instances | `instance_id`, `workflow_id`, `current_state` |
| `agent_communication` | Communication logs | `message_id`, `sender`, `recipient`, `timestamp` |
| `system_health` | System metrics and status | `metric_name`, `value`, `timestamp` |
| `tasks` | Task assignments and status | `task_id`, `assigned_agent`, `status` |

**Document Schemas**:

- All documents include `id`, `created_at`, and `updated_at` fields
- History tracking with `history_log` array in relevant collections
- Pydantic models for validation before storage

**Synchronization**:

- Two-way sync between MongoDB and Notion
- Changes in either system propagated to the other
- Conflict resolution with timestamp-based precedence

### 3.4 Workflow Tracking

Grace Fields tracks workflows across multiple agent interactions:

**Workflow State Machine**:

- Workflows defined as state machines with valid transitions
- Current state stored in Redis and MongoDB
- State transitions validated against workflow definition

**Multi-Agent Workflows**:

- Workflows can span multiple agents
- Transition triggers defined in workflow configuration
- Agent handoffs managed by Grace Fields

**Workflow History**:

- All state transitions recorded with timestamp, agent, and reason
- Complete workflow history available for auditing
- Analytics on workflow performance and bottlenecks

## 4. Development Tools

### 4.1 VSCode Configuration

**Essential Extensions**:

| Extension | ID | Purpose |
|-----------|----|---------|
| Python | ms-python.python | Python language support |
| Pylance | ms-python.vscode-pylance | Static type checking |
| Pydantic | ms-python.vscode-pylance | Pydantic schema support |
| autoDocstring | njpwerner.autodocstring | Python docstring generation |

**Recommended Extensions**:

| Extension | ID | Purpose |
|-----------|----|---------|
| Python Test Explorer | littlefoxteam.vscode-python-test-adapter | Test discovery and execution |
| Python Indent | kevinrose.vscode-python-indent | Smart Python indentation |
| Python Type Hint | njqdev.vscode-python-typehint | Type hint suggestions |
| Redis | cweijan.vscode-redis-client | Redis database client |

**Configuration Settings**:

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.analysis.typeCheckingMode": "basic"
}
```

### 4.2 CI/CD Pipeline Tools

**GitHub Actions Workflows**:

| Workflow | Purpose | Key Features |
|----------|---------|--------------|
| docker-build-deploy.yml | Build and deploy containers | Auto-versioning, multi-stage builds |
| notion-integration-test.yml | Test Notion integration | API validation, mock responses |
| update-architecture.yml | Update documentation | Auto-generate diagrams |

**Docker Deployment**:

- Docker Compose for local development
- GitHub Container Registry for image storage
- Automated security scanning with Trivy

**Monitoring Integration**:

- Prometheus for metrics collection
- Grafana for visualization
- Consul for service discovery

### 4.3 Testing Frameworks

**Unit Testing**:

- pytest for test execution
- pytest-asyncio for async test support
- pytest-mock for mocking dependencies

**Integration Testing**:

- httpx for API testing
- TestClient from FastAPI for endpoint testing
- Mock services for external dependencies

**Test Configuration**:

```env
TEST_MODE=true
DISABLE_WEBHOOKS=true
MONGODB_URI=mongodb://localhost:27017/test_db
REDIS_URI=redis://localhost:6379/1
```

### 4.4 Monitoring Tools

**Redis Monitoring**:

| Tool | Purpose | Installation |
|------|---------|-------------|
| Redis Commander | Web-based Redis management | `npm install -g redis-commander` |
| Prometheus Redis Exporter | Metrics collection | Docker: `oliver006/redis_exporter` |
| Grafana Redis Dashboard | Visualization | Dashboard ID: 763 |

**MongoDB Monitoring**:

| Tool | Purpose | Installation |
|------|---------|-------------|
| MongoDB Compass | GUI for database management | Download from MongoDB website |
| Prometheus MongoDB Exporter | Metrics collection | Docker: `bitnami/mongodb-exporter` |
| Grafana MongoDB Dashboard | Visualization | Dashboard ID: 2583 |

**System Monitoring**:

- Prometheus for metrics collection
- Grafana for dashboards
- Loki for log aggregation

## 5. Implementation Guidelines

### 5.1 Initialization and Configuration

When initializing Grace Fields, follow these steps:

**Environment Setup**:

```env
# Required environment variables for Grace Fields
NOTION_API_KEY=secret_your_notion_api_key
REDIS_URI=redis://username:password@host:port
MONGODB_URI=mongodb+srv://username:password@host/database
WEBHOOK_SECRET=your_webhook_secret_key
AI_ROUTER_API_KEY=your_openai_or_anthropic_key
```

**Agent Initialization**:

```python
# Initialize all specialized agents
nyra = Nyra(notion_client=notion_service)
solari = Solari(notion_client=notion_service)
ruvo = Ruvo(notion_client=notion_service)
liora = Liora(notion_client=notion_service)
sage = Sage(notion_client=notion_service)
elan = Elan(notion_client=notion_service)
zevi = Zevi(notion_client=notion_service)

# Initialize message bus for inter-agent communication
message_bus = MessageBus(notion_service=notion_service)

# Initialize AI router
ai_router = AIRouter()
await ai_router.initialize()

# Create Grace Fields orchestrator with all agents
grace = create_grace_orchestrator(notion_service, message_bus)
grace.ai_router = ai_router
```

**Configuration Validation**:

- Verify all agent capabilities are registered
- Validate workflow definitions
- Test connections to all required services

### 5.2 Event Processing Flow

The standard event processing flow through Grace Fields follows this sequence:

**Event Reception**:

- External event received via API or webhook
- Event validated against schema
- Tracking ID assigned if not present

**Event Classification**:

- Event type identified
- Priority determined
- Business entity extracted

**Agent Selection**:

- Appropriate agent selected using routing mechanisms
- Agent availability checked
- Fallbacks identified

**Event Dispatch**:

- Event formatted for selected agent
- Dispatched with appropriate context
- Timeout monitoring started

**Response Handling**:

- Agent response received and validated
- Results processed and stored
- Workflow transitions triggered if needed

### 5.3 Performance Optimization

To optimize Grace Fields performance:

**Caching Strategy**:

| Data Type | Caching Approach | TTL |
|-----------|------------------|-----|
| Routing decisions | Redis L1 cache | 60s |
| Agent capabilities | Redis L2 cache | 300s |
| Workflow definitions | Redis L3 cache | 3600s |
| Reference data | Permanent cache | 86400s |

**Asynchronous Processing**:

- Use async/await for all I/O operations
- Implement parallel processing where possible
- Use task queues for background processing

**Resource Management**:

- Implement connection pooling for databases
- Use circuit breakers to prevent cascading failures
- Implement graceful degradation for high-load scenarios

### 5.4 Security Best Practices

Follow these security best practices:

**Credential Management**:

- Store all credentials in environment variables
- Rotate API keys every 90 days
- Use different keys for development and production

**Input Validation**:

- Validate all input against Pydantic models
- Implement strict type checking
- Sanitize user input to prevent injection attacks

**Access Control**:

- Implement role-based access control
- Validate permissions for all operations
- Log all access attempts for auditing

## 6. Troubleshooting

### 6.1 Common Issues and Solutions

**Agent Communication Failures**:

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Timeout errors | Network latency, agent overload | Increase timeout settings, implement retry logic |
| Authentication failures | Invalid API keys, expired tokens | Verify credentials, rotate keys if compromised |
| Message format errors | Schema mismatch, invalid data | Validate against Pydantic models before sending |

**Routing Errors**:

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Unknown event type | Missing routing entry | Add event type to routing map, use AI router fallback |
| Agent unavailable | Service down, circuit breaker open | Check agent health, use fallback chains |
| Missing required fields | Incomplete event data | Validate event data before routing |

**Performance Issues**:

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| High latency | Redis connection issues, network problems | Check Redis performance, optimize queries |
| Memory usage | Cache growth, memory leaks | Implement cache pruning, monitor memory usage |
| CPU spikes | Complex processing, infinite loops | Profile code, implement timeouts |

### 6.2 Diagnostic Tools

**Log Analysis**:

```python
# Enable detailed logging for Grace Fields
import logging
from loguru import logger

# Configure loguru with proper format
logger.configure(
    handlers=[
        {
            "sink": "logs/grace_fields.log",
            "format": "[{time:YYYY-MM-DD HH:mm:ss}] [{level}] [{module}:{function}:{line}] {message}",
            "level": "DEBUG",
            "rotation": "10 MB",
            "retention": "1 week",
        }
    ]
)

# Track specific events with context
logger.bind(tracking_id="evt-123456").info("Processing event")
```

**Monitoring Dashboards**:

- Use Grafana dashboards to monitor system health
- Set up alerts for critical metrics
- Track agent performance over time

**Debug Mode**:

- Enable debug logging for detailed information
- Use interactive debugging in development
- Implement trace logging for complex workflows

### 6.3 Support Resources

**Documentation**:

| Resource | Purpose | Location |
|----------|---------|----------|
| GRACE_ORCHESTRATOR_ROADMAP.md | Architecture details | `/documentation` |
| AGENTS.md | Agent-specific information | Repository root |
| API Documentation | Endpoint details | `/documentation/api` |

**Community Support**:

- GitHub Issues for bug reports
- Discussion forums for general questions
- Stack Overflow for technical issues (tag: `higherself-network`)

**Professional Support**:

- Contact the development team for critical issues
- Schedule regular maintenance reviews
- Engage consultants for complex customizations
