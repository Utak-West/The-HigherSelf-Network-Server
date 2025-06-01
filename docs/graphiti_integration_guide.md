# Graphiti Integration Guide

## Overview

Graphiti is a temporal knowledge graph memory layer that has been integrated into The HigherSelf Network Server to enhance AI agents' ability to maintain context and relationships across conversations and business operations. This integration provides sophisticated memory capabilities that go beyond traditional RAG approaches.

## What is Graphiti?

Graphiti is a framework for building and querying temporally-aware knowledge graphs, specifically designed for AI agents operating in dynamic environments. Unlike traditional retrieval-augmented generation (RAG) methods, Graphiti continuously integrates user interactions, structured and unstructured enterprise data, and external information into a coherent, queryable graph.

### Key Features

- **Real-Time Incremental Updates**: Immediate integration of new data episodes without batch recomputation
- **Bi-Temporal Data Model**: Explicit tracking of event occurrence and ingestion times
- **Efficient Hybrid Retrieval**: Combines semantic embeddings, keyword (BM25), and graph traversal
- **Custom Entity Definitions**: Flexible ontology creation through Pydantic models
- **Scalability**: Efficiently manages large datasets with parallel processing

## Architecture Integration

### Components

```
The HigherSelf Network Server
├── Graphiti Service (services/graphiti_service.py)
│   ├── Episode Management
│   ├── Search Operations
│   ├── Agent Context Retrieval
│   └── Health Monitoring
├── Graphiti Models (models/graphiti_models.py)
│   ├── Episode Requests/Responses
│   ├── Search Requests/Responses
│   ├── Agent Context Models
│   └── Health Status Models
├── Graphiti Utils (utils/graphiti_utils.py)
│   ├── Episode Creation Helpers
│   ├── Search Request Builders
│   ├── Entity Extraction
│   └── Configuration Validation
└── Integration Points
    ├── Redis (Caching)
    ├── MongoDB (Metadata Storage)
    ├── Neo4j (Knowledge Graph)
    └── OpenAI (LLM & Embeddings)
```

### Data Flow

1. **Agent Interactions** → Episodes → Graphiti Knowledge Graph
2. **Search Queries** → Hybrid Search → Cached Results → Agent Context
3. **Memory Updates** → Temporal Relationships → Enhanced Agent Responses

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# ==== GRAPHITI CONFIGURATION ====
# Neo4j connection for Graphiti temporal knowledge graph
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here
NEO4J_DATABASE=neo4j

# OpenAI API for Graphiti LLM and embeddings
OPENAI_API_KEY=your_openai_api_key_here

# Graphiti cache settings
GRAPHITI_CACHE_TTL=300
GRAPHITI_ENABLED=true

# Optional: Alternative LLM providers for Graphiti
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GROQ_API_KEY=your_groq_api_key_here
# GOOGLE_API_KEY=your_google_api_key_here
```

### Prerequisites

1. **Neo4j Database**: Install and run Neo4j 5.26 or higher
2. **OpenAI API Key**: Required for LLM inference and embeddings
3. **Python Dependencies**: Graphiti-core is included in requirements.txt

## Usage Examples

### Basic Episode Creation

```python
from services.graphiti_service import graphiti_service
from models.graphiti_models import GraphitiAgentName, GraphitiBusinessContext

# Add a text episode
episode_uuid = await graphiti_service.add_episode(
    name="Nyra_lead_capture_20250129",
    episode_body="New lead: Sarah Johnson interested in wellness coaching",
    agent_name=GraphitiAgentName.NYRA,
    business_context=GraphitiBusinessContext.WELLNESS_CENTER
)
```

### Searching the Knowledge Graph

```python
# Search for relevant information
results = await graphiti_service.search(
    query="Sarah Johnson wellness coaching",
    agent_name=GraphitiAgentName.GRACE,
    business_context=GraphitiBusinessContext.WELLNESS_CENTER,
    limit=10
)

for result in results:
    print(f"Fact: {result.fact}")
    print(f"Score: {result.score}")
```

### Agent Context Retrieval

```python
# Get contextual information for an agent
context = await graphiti_service.get_agent_context(
    agent_name="Nyra",
    business_context="wellness_center",
    limit=20
)

print(f"Search results: {len(context['search_results'])}")
print(f"Recent episodes: {len(context['recent_episodes'])}")
```

### Using Utility Functions

```python
from utils.graphiti_utils import (
    create_episode_from_agent_interaction,
    create_structured_episode,
    format_search_results_for_agent
)

# Create episode from agent interaction
episode = create_episode_from_agent_interaction(
    agent_name="Solari",
    interaction_content="Booking confirmed for Marcus Chen",
    business_context="art_gallery",
    interaction_type="booking_confirmation"
)

# Create structured episode
booking_data = {
    "client_name": "Marcus Chen",
    "service": "Gallery Tour",
    "date": "2025-02-10",
    "status": "confirmed"
}

structured_episode = create_structured_episode(
    agent_name="Solari",
    data=booking_data,
    business_context="art_gallery",
    episode_type="booking"
)
```

## Agent Integration

### Grace Fields Orchestrator

Grace Fields uses Graphiti to:
- Maintain context across multi-agent workflows
- Track customer interactions and preferences
- Coordinate agent responses based on historical data
- Escalate issues with full context

### Specialized Agents

Each agent leverages Graphiti for:

- **Nyra (Lead Capture)**: Store lead information and interaction history
- **Solari (Booking)**: Track booking patterns and customer preferences
- **Ruvo (Task Management)**: Maintain task relationships and dependencies
- **Liora (Marketing)**: Analyze campaign effectiveness and audience insights
- **Sage (Community)**: Track community engagement and member relationships
- **Elan (Content)**: Maintain content lifecycle and performance data
- **Zevi (Audience)**: Store audience segmentation and behavior patterns
- **Atlas (RAG)**: Enhanced knowledge retrieval with temporal context

## Business Context Integration

### Multi-Business Support

Graphiti supports all business contexts:

- **Art Gallery**: Artist relationships, collector preferences, exhibition history
- **Wellness Center**: Client wellness journeys, treatment effectiveness, practitioner notes
- **Consultancy**: Project timelines, client requirements, solution effectiveness
- **Interior Design**: Design preferences, project evolution, client feedback
- **Luxury Renovations**: Material choices, contractor relationships, project timelines
- **Executive Wellness**: Executive preferences, wellness program effectiveness
- **Corporate Wellness**: Program rollouts, employee engagement, ROI tracking

### Cross-Business Insights

Graphiti enables insights across business units:
- Shared clients across services
- Cross-selling opportunities
- Resource optimization
- Unified customer experience

## Performance and Caching

### Redis Integration

- Search results cached for 5 minutes (configurable)
- Episode metadata cached for quick access
- Agent context cached to reduce query load

### MongoDB Integration

- Episode metadata stored for analytics
- Search logs for performance monitoring
- Agent interaction tracking

## Monitoring and Health

### Health Checks

```python
# Check service health
health = await graphiti_service.get_health_status()
print(f"Status: {health['status']}")
print(f"Connection: {health['connection_test']}")
```

### Configuration Validation

```python
from utils.graphiti_utils import validate_graphiti_config

# Validate configuration
validation = validate_graphiti_config()
if not validation["valid"]:
    for error in validation["errors"]:
        print(f"Error: {error}")
```

## Best Practices

### Episode Creation

1. **Descriptive Names**: Use clear, timestamped episode names
2. **Appropriate Types**: Use TEXT for conversations, JSON for structured data
3. **Business Context**: Always specify the relevant business context
4. **Agent Attribution**: Include the agent name for proper tracking

### Search Optimization

1. **Specific Queries**: Use specific terms rather than broad searches
2. **Context Filtering**: Filter by agent and business context when appropriate
3. **Result Limits**: Use reasonable limits to avoid performance issues
4. **Center Nodes**: Use center nodes for contextually relevant reranking

### Memory Management

1. **Regular Cleanup**: Implement cache clearing for outdated information
2. **Context Limits**: Limit context retrieval to relevant timeframes
3. **Structured Data**: Use structured episodes for complex data relationships

## Troubleshooting

### Common Issues

1. **Neo4j Connection**: Ensure Neo4j is running and accessible
2. **OpenAI API**: Verify API key is valid and has sufficient credits
3. **Memory Usage**: Monitor Neo4j memory usage for large datasets
4. **Cache Performance**: Monitor Redis performance and adjust TTL as needed

### Error Handling

The Graphiti service includes comprehensive error handling:
- Connection failures are logged and service continues without Graphiti
- Invalid episodes are rejected with clear error messages
- Search failures return empty results rather than crashing
- Health checks provide detailed status information

## Demo and Testing

Run the comprehensive demo:

```bash
python examples/graphiti_demo.py
```

This demo showcases:
- Basic episode creation and search
- Multi-agent workflow integration
- Health checking and validation
- Real-world business scenarios

## Future Enhancements

### Planned Features

1. **Custom Entity Types**: Support for domain-specific entities
2. **Advanced Analytics**: Temporal analysis and trend detection
3. **Multi-Modal Support**: Integration with image and document processing
4. **Workflow Automation**: Automatic episode creation from agent actions

### Integration Opportunities

1. **Notion Sync**: Bidirectional sync with Notion databases
2. **GoHighLevel**: CRM data integration for enhanced customer context
3. **External APIs**: Integration with business-specific data sources
4. **Real-time Updates**: WebSocket support for live knowledge graph updates
