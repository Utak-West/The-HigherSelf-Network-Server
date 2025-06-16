# Grace Fields - Agent Orchestration Protocol

## Overview

Grace Fields is the Master Orchestrator of The HigherSelf Network Server, responsible for coordinating the activities of all specialized agent personalities. This document outlines the orchestration protocol that Grace Fields implements to ensure harmonious operation across multiple business entities.

## Core Responsibilities

Grace Fields serves as the central intelligence of The HigherSelf Network Server with the following core responsibilities:

1. **Event Routing**: Intelligently route events to the appropriate specialized agent based on event type, content, and business context
2. **Workflow Orchestration**: Manage multi-step workflows involving multiple agents
3. **Business Entity Awareness**: Maintain awareness of different business entities and their specific requirements
4. **System Coordination**: Ensure all agents work together harmoniously
5. **Error Recovery**: Implement fallback mechanisms when primary agents cannot process events
6. **Performance Optimization**: Monitor and optimize system performance

## Business Entity Awareness

Grace Fields maintains awareness of the following business entities:

1. **The 7 Space | Art Gallery & Wellness Center**
   - Downtown Newark-based venue
   - Revenue streams: art sales, wellness services, event space rentals
   - Primary workflows: Exhibition Management, Artwork Sales, Wellness Booking

2. **The Connection Practice**
   - Consultancy led by Altagracia Montilla
   - Revenue streams: retreats, workshops, speaking engagements
   - Primary workflows: Consultation Booking, Retreat Management, Workshop Coordination

3. **HigherSelf (Nonprofit)**
   - Community service organization led by Utak West
   - Services: direct community support, professional wellness and creative services
   - Primary workflows: Donor Management, Community Engagement, Program Delivery

## Interaction Protocol

### Event Routing Logic

Grace Fields uses a sophisticated multi-layered routing approach:

1. **Direct Routing**: Route events to agents based on explicit event type mappings
2. **Business Entity Routing**: Route events to agents specialized for specific business entities
3. **Capability-based Routing**: Route events based on required capabilities
4. **Pattern-based Routing**: Route events based on event type patterns
5. **Dynamic Discovery**: Ask each agent if they can handle an unknown event type
6. **AI-based Routing**: Use AI to determine the most appropriate agent for complex events

### Workflow Orchestration

Grace Fields manages complex workflows through:

1. **Workflow Patterns**: Predefined sequences of agent actions
2. **State Tracking**: Maintain the state of active workflows
3. **Conditional Branching**: Route workflows based on intermediate results
4. **Parallel Processing**: Execute independent workflow steps concurrently
5. **Error Handling**: Recover from failures in workflow steps

### Response Format

Grace Fields ensures consistent response formats across all agents:

```json
{
  "status": "processed|error",
  "message": "Human-readable description",
  "tracking_id": "unique-tracking-id",
  "agent_results": {
    "agent_name": {
      "status": "processed|error",
      "message": "Agent-specific message",
      "data": {}
    }
  },
  "workflow_info": {
    "workflow_id": "workflow-id",
    "current_step": 2,
    "total_steps": 5,
    "status": "active|completed|error"
  },
  "business_entity": "7space|connection_practice|higherself_nonprofit",
  "processing_time": 1.25
}
```

## Agent Capabilities

Grace Fields coordinates the following specialized agents:

1. **Nyra (Lead Capture Specialist)**
   - Captures leads from various sources
   - Handles lead enrichment and qualification
   - Manages contact records in Notion

2. **Solari (Booking & Order Manager)**
   - Processes retreat bookings from Amelia
   - Handles WooCommerce orders
   - Creates and manages workflow instances

3. **Ruvo (Task Orchestrator)**
   - Creates, assigns, and tracks tasks
   - Manages workflow-generated tasks
   - Updates the Master Tasks database

4. **Liora (Marketing Strategist)**
   - Manages email campaigns through Beehiiv
   - Handles audience targeting
   - Tracks campaign performance

5. **Sage (Community Curator)**
   - Handles community member interactions in Circle.so
   - Tracks engagement metrics
   - Manages member profiles

6. **Elan (Content Choreographer)**
   - Manages content lifecycle
   - Handles content distribution
   - Tracks content performance

7. **Zevi (Audience Analyst)**
   - Analyzes customer data
   - Creates and manages audience segments
   - Provides insights for targeted marketing

8. **Atlas (Knowledge Retrieval Specialist)**
   - Manages the RAG system
   - Retrieves relevant knowledge
   - Enhances AI responses with context

## Business Process Orchestration

Grace Fields orchestrates the following key business processes:

### Lead Capture & Nurturing

1. **Nyra** captures and qualifies leads
2. **Ruvo** creates follow-up tasks
3. **Liora** adds leads to appropriate marketing sequences
4. **Solari** handles booking requests that result from nurturing

### Booking & Order Processing

1. **Solari** processes initial booking or order
2. **Ruvo** creates preparation tasks
3. **Nyra** updates contact records
4. **Sage** handles post-booking community engagement

### Marketing Campaign Management

1. **Zevi** identifies target audience segments
2. **Liora** creates and executes campaigns
3. **Elan** develops campaign content
4. **Nyra** processes resulting leads

### Community Engagement

1. **Sage** manages community interactions
2. **Elan** creates community content
3. **Zevi** analyzes engagement patterns
4. **Liora** develops targeted community campaigns

### Content Creation & Distribution

1. **Elan** manages content creation
2. **Liora** handles content distribution
3. **Sage** shares content with community
4. **Zevi** analyzes content performance

## System Integration

Grace Fields maintains data harmony across platforms:

### Unified Data Management

- All agent activities are recorded in our proprietary database architecture
- Workflow states are tracked across integrated systems with transparency
- Business entity data is maintained with ethical data handling practices

### External Integrations

- WooCommerce for e-commerce
- Amelia for booking
- Circle.so for community
- Beehiiv for email marketing
- Airtable for operational dashboards

### Data Validation and Transformation

- Pydantic models ensure data integrity
- Transformation rules maintain consistency across systems
- Bidirectional sync keeps all systems in harmony

## Business Intelligence

Grace Fields provides business intelligence through:

1. **Performance Metrics**
   - Conversion rates by lead source
   - Task completion efficiency
   - Campaign performance by segment
   - Community engagement metrics

2. **Process Optimization**
   - Workflow bottleneck identification
   - Agent utilization analysis
   - Response time optimization
   - Error rate reduction

3. **Resource Allocation**
   - Task prioritization recommendations
   - Content focus suggestions
   - Marketing budget allocation insights
   - Community engagement opportunity identification

## Implementation Details

Grace Fields is implemented as the `GraceFields` class in the `agents/agent_personalities.py` file. The implementation includes:

1. **Event Routing Logic**: Sophisticated routing algorithms
2. **Workflow Management**: State machine for workflow orchestration
3. **Agent Registry**: Dynamic discovery of agent capabilities
4. **Message Bus Integration**: Inter-agent communication
5. **Health Monitoring**: System health checks and reporting

## Usage Examples

### Basic Event Routing

```python
# Route an event to the appropriate agent
result = await grace_fields.route_event("lead_capture", {
    "name": "John Doe",
    "email": "john@example.com",
    "source": "website_form",
    "business_entity_id": "7space"
})
```

### Workflow Orchestration

```python
# Start a lead nurturing workflow
result = await grace_fields.start_workflow_pattern("lead_nurturing", {
    "lead_id": "lead_123",
    "lead_name": "Jane Smith",
    "lead_email": "jane@example.com",
    "interest": "art_exhibition",
    "business_entity_id": "7space"
})
```

### Health Check

```python
# Check the health of all agents
health_status = await grace_fields.check_health()
```
