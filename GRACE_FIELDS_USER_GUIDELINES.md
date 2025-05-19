# Grace Fields Orchestrator - User Guidelines

This document provides comprehensive guidelines for configuring and using the Grace Fields orchestrator agent in The HigherSelf Network Server. Grace Fields serves as the central orchestration layer that coordinates all agent activities and complex workflows across the system.

## 1. Operational Parameters in Augment Settings

### 1.1 Response Formatting Standards

Grace Fields must adhere to the following response formatting standards:

```json
{
  "message_type": "event_routing",
  "sender": {
    "agent_id": "GRACE_ORCHESTRATOR",
    "agent_name": "Grace Fields"
  },
  "recipient": {
    "agent_id": "<TARGET_AGENT_ID>",
    "agent_name": "<TARGET_AGENT_NAME>"
  },
  "message_id": "<UUID>",
  "timestamp": "<ISO8601_TIMESTAMP>",
  "priority": "<PRIORITY_LEVEL>",
  "payload": {
    "event_type": "<EVENT_TYPE>",
    "tracking_id": "<TRACKING_ID>",
    "data": {},
    "context": {},
    "expected_response": {}
  }
}
```

#### Key Parameters:

- **message_type**: Must be descriptive of the action (e.g., "event_routing", "error_notification")
- **priority**: Must be one of: "low", "normal", "high", "critical"
- **tracking_id**: Must be preserved across the entire event lifecycle for traceability

### 1.2 Error Handling Protocols

Grace Fields implements a multi-tiered error handling approach:

1. **Error Detection**:
   - Timeout monitoring for non-responsive agents
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
  "error": "<ERROR_MESSAGE>",
  "status": "error",
  "agent": "<FAILED_AGENT_NAME>",
  "tracking_id": "<TRACKING_ID>",
  "severity": "<ERROR_SEVERITY>",
  "recovery_attempted": true|false,
  "fallback_result": {}
}
```

### 1.3 Authentication Requirements

Grace Fields requires the following authentication mechanisms:

1. **Inter-Agent Communication**:
   - All messages must include the sender's agent_id
   - Messages must be signed with the agent's API key
   - X-Agent-ID and X-Target-Agent-ID headers must be present in API requests

2. **External System Authentication**:
   - Webhook requests must include the WEBHOOK_SECRET
   - API requests must include a valid API key in the X-API-Key header
   - JWT authentication for user-initiated requests

### 1.4 Rate Limiting Considerations

Grace Fields implements rate limiting to prevent system overload:

1. **Default Limits**:
   - 60 requests per minute for regular users
   - 120 requests per minute for business accounts
   - 300 requests per minute for admin users
   - 600 requests per minute for API clients

2. **Burst Handling**:
   - Burst capacity of 20 requests
   - Redis-based rate limiting with sliding window algorithm
   - Automatic throttling during high-load periods

3. **Prioritization**:
   - Critical messages bypass rate limiting
   - High-priority messages get preferential processing

## 2. Roo Code Settings

### 2.1 Event Routing Configuration

Grace Fields routes events to specialized agents using the following mechanisms:

1. **Direct Mapping**:
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

2. **Pattern-Based Routing**:
   - Extracts domain from event type (e.g., "lead_capture" → "lead")
   - Maps domains to agents (e.g., "lead" → "Nyra")
   - Automatically adds successful mappings to the routing map

3. **Capability-Based Routing**:
   - Routes based on required_capability in event data
   - Uses agent_capabilities registry to find capable agents
   - Selects the most appropriate agent based on capability match

4. **Business Entity Routing**:
   - Routes based on business_entity_id in event data
   - Matches agents specifically configured for that business entity

### 2.2 Fallback Mechanisms

When primary routing fails, Grace Fields uses these fallback mechanisms:

1. **Agent Fallback Chains**:
   ```python
   fallbacks = {
       "Nyra": ["Solari", "Zevi"],  # Lead capture fallbacks
       "Solari": ["Nyra", "Ruvo"],  # Booking fallbacks
       "Ruvo": ["Solari", "Liora"],  # Task fallbacks
       "Elan": ["Liora", "Sage"],   # Content fallbacks
       "Sage": ["Elan", "Zevi"],    # Community fallbacks
       "Zevi": ["Liora", "Nyra"],   # Audience fallbacks
       "Liora": ["Elan", "Zevi"]    # Marketing fallbacks
   }
   ```

2. **AI Router Fallback**:
   - When no agent can handle an event, delegates to AI router
   - AI router uses content analysis to determine the best agent
   - Adds successful routing to the routing map for future use

3. **Circuit Breaking**:
   - Temporarily prevents routing to agents experiencing persistent issues
   - Automatically routes to fallback agents during circuit break periods

### 2.3 Security Validation

Grace Fields enforces these security validations for inter-agent communication:

1. **Message Validation**:
   - Validates message structure against AgentMessage schema
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

1. **Standard Log Format**:
   ```
   [TIMESTAMP] [LOG_LEVEL] [COMPONENT] [TRACKING_ID] Message
   ```

2. **Required Log Events**:
   - Event receipt from external systems
   - Event routing decisions
   - Agent processing start/end
   - Error conditions and recovery attempts
   - Workflow transitions

3. **Log Storage**:
   - All logs written to application log file
   - Critical events stored in Notion for auditability
   - Error logs sent to monitoring system

## 3. Context Management Settings

### 3.1 Conversation History Management

Grace Fields maintains conversation history with users through:

1. **Session Management**:
   - User sessions tracked with unique session IDs
   - Session context maintained in Redis with TTL
   - Session data includes user preferences and interaction history

2. **Conversation Context**:
   - Previous messages stored in conversation context
   - Context includes entity recognition results
   - Intent tracking across multiple interactions

3. **Context Pruning**:
   - Older context entries pruned based on relevance
   - Critical context preserved for longer periods
   - Context size limited to prevent memory issues

### 3.2 State Persistence with Redis

Grace Fields uses Redis for state persistence between sessions:

1. **Cache Hierarchy**:
   - L1 Cache (60s TTL): Agent state, temporary data
   - L2 Cache (300s TTL): Notion data, API responses
   - L3 Cache (3600s TTL): Vector embeddings, stable data
   - Permanent Cache (86400s TTL): Configuration, reference data

2. **Key Structures**:
   - Agent state: `agent:{agent_id}:state`
   - Session data: `session:{session_id}:data`
   - Workflow state: `workflow:{workflow_id}:state`
   - Event tracking: `event:{tracking_id}:status`

3. **Pub/Sub Channels**:
   - Agent notifications: `agent:{agent_id}:notifications`
   - System events: `system:events`
   - Workflow transitions: `workflow:{workflow_id}:transitions`

### 3.3 MongoDB Integration

Grace Fields uses MongoDB for long-term data storage:

1. **Collection Structure**:
   - `agents`: Agent configuration and state
   - `workflows`: Workflow definitions
   - `workflow_instances`: Active workflow instances
   - `agent_communication`: Communication logs
   - `system_health`: System metrics and status
   - `tasks`: Task assignments and status

2. **Document Schemas**:
   - All documents include `id`, `created_at`, and `updated_at` fields
   - History tracking with `history_log` array in relevant collections
   - Pydantic models for validation before storage

3. **Synchronization**:
   - Two-way sync between MongoDB and Notion
   - Changes in either system propagated to the other
   - Conflict resolution with timestamp-based precedence

### 3.4 Workflow Tracking

Grace Fields tracks workflows across multiple agent interactions:

1. **Workflow State Machine**:
   - Workflows defined as state machines with valid transitions
   - Current state stored in Redis and MongoDB
   - State transitions validated against workflow definition

2. **Multi-Agent Workflows**:
   - Workflows can span multiple agents
   - Transition triggers defined in workflow configuration
   - Agent handoffs managed by Grace Fields

3. **Workflow History**:
   - All state transitions recorded with timestamp, agent, and reason
   - Complete workflow history available for auditing
   - Analytics on workflow performance and bottlenecks

## 4. Tool Recommendations

### 4.1 VSCode Extensions for Python/Pydantic Development

1. **Essential Extensions**:
   - **Python** (ms-python.python): Python language support
   - **Pylance** (ms-python.vscode-pylance): Static type checking
   - **Pydantic** (ms-python.vscode-pylance): Pydantic schema support
   - **autoDocstring** (njpwerner.autodocstring): Python docstring generation

2. **Recommended Extensions**:
   - **Python Test Explorer** (littlefoxteam.vscode-python-test-adapter): Test discovery and execution
   - **Python Indent** (kevinrose.vscode-python-indent): Smart Python indentation
   - **Python Type Hint** (njqdev.vscode-python-typehint): Type hint suggestions
   - **Redis** (cweijan.vscode-redis-client): Redis database client

3. **Configuration Settings**:
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

1. **GitHub Actions Workflows**:
   - **docker-build-deploy.yml**: Build and deploy Docker containers
   - **notion-integration-test.yml**: Test Notion integration
   - **update-architecture.yml**: Update architecture documentation

2. **Docker Deployment**:
   - Docker Compose for local development
   - GitHub Container Registry for image storage
   - Automated security scanning with Trivy

3. **Monitoring Integration**:
   - Prometheus for metrics collection
   - Grafana for visualization
   - Consul for service discovery

### 4.3 Testing Frameworks

1. **Unit Testing**:
   - pytest for test execution
   - pytest-asyncio for async test support
   - pytest-mock for mocking dependencies

2. **Integration Testing**:
   - httpx for API testing
   - TestClient from FastAPI for endpoint testing
   - Mock services for external dependencies

3. **Test Configuration**:
   ```
   TEST_MODE=true
   DISABLE_WEBHOOKS=true
   MONGODB_URI=mongodb://localhost:27017/test_db
   REDIS_URI=redis://localhost:6379/1
   ```

### 4.4 Monitoring Tools

1. **Redis Monitoring**:
   - Redis Commander: Web-based Redis management
   - Prometheus Redis Exporter: Metrics collection
   - Grafana Redis Dashboard: Visualization

2. **MongoDB Monitoring**:
   - MongoDB Compass: GUI for database management
   - Prometheus MongoDB Exporter: Metrics collection
   - Grafana MongoDB Dashboard: Visualization

3. **System Monitoring**:
   - Prometheus for metrics collection
   - Grafana for dashboards
   - Loki for log aggregation

## 5. Implementation Guidelines

### 5.1 Initialization and Configuration

When initializing Grace Fields, follow these steps:

1. **Environment Setup**:
   - Ensure all required environment variables are set in `.env`
   - Configure Redis and MongoDB connections
   - Set up Notion integration with proper permissions

2. **Agent Initialization**:
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

3. **Configuration Validation**:
   - Verify all agent capabilities are registered
   - Validate workflow definitions
   - Test connections to all required services

### 5.2 Event Processing Flow

The standard event processing flow through Grace Fields:

1. **Event Reception**:
   - External event received via API or webhook
   - Event validated against schema
   - Tracking ID assigned if not present

2. **Event Classification**:
   - Event type identified
   - Priority determined
   - Business entity extracted

3. **Agent Selection**:
   - Appropriate agent selected using routing mechanisms
   - Agent availability checked
   - Fallbacks identified

4. **Event Dispatch**:
   - Event formatted for selected agent
   - Dispatched with appropriate context
   - Timeout monitoring started

5. **Response Handling**:
   - Agent response received and validated
   - Results processed and stored
   - Workflow transitions triggered if needed

### 5.3 Performance Optimization

To optimize Grace Fields performance:

1. **Caching Strategy**:
   - Implement tiered caching for frequently accessed data
   - Cache agent routing decisions
   - Store workflow state in Redis for fast access

2. **Asynchronous Processing**:
   - Use async/await for all I/O operations
   - Implement parallel processing where possible
   - Use task queues for background processing

3. **Resource Management**:
   - Implement connection pooling for databases
   - Use circuit breakers to prevent cascading failures
   - Implement graceful degradation for high-load scenarios

### 5.4 Security Best Practices

Follow these security best practices:

1. **Credential Management**:
   - Store all credentials in environment variables
   - Rotate API keys regularly
   - Use different keys for development and production

2. **Input Validation**:
   - Validate all input against Pydantic models
   - Implement strict type checking
   - Sanitize user input to prevent injection attacks

3. **Access Control**:
   - Implement role-based access control
   - Validate permissions for all operations
   - Log all access attempts for auditing

## 6. Troubleshooting Guide

### 6.1 Common Issues and Solutions

1. **Agent Communication Failures**:
   - Check message bus connection
   - Verify agent is properly initialized
   - Check for permission issues

2. **Routing Errors**:
   - Verify event type is registered
   - Check agent availability
   - Inspect event data for required fields

3. **Performance Issues**:
   - Check Redis connection and performance
   - Monitor MongoDB query performance
   - Look for memory leaks in long-running processes

### 6.2 Diagnostic Tools

1. **Log Analysis**:
   - Use loguru for structured logging
   - Filter logs by tracking ID to follow event flow
   - Check error logs for exceptions

2. **Monitoring Dashboards**:
   - Use Grafana dashboards to monitor system health
   - Set up alerts for critical metrics
   - Track agent performance over time

3. **Debug Mode**:
   - Enable debug logging for detailed information
   - Use interactive debugging in development
   - Implement trace logging for complex workflows

### 6.3 Support Resources

1. **Documentation**:
   - Refer to GRACE_ORCHESTRATOR_ROADMAP.md for architecture details
   - Check AGENTS.md for agent-specific information
   - Review API documentation for endpoint details

2. **Community Support**:
   - GitHub Issues for bug reports
   - Discussion forums for general questions
   - Stack Overflow for technical issues

3. **Professional Support**:
   - Contact the development team for critical issues
   - Schedule regular maintenance reviews
   - Engage consultants for complex customizations
