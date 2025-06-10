# Enhanced Automation Infrastructure

This document provides an overview of the enhancements made to the automation infrastructure of The HigherSelf Network Server. These enhancements focus on two key areas:

1. **Knowledge Hub with Semantic Search** - A unified system for embedding, storing, and searching content using vector representations.
2. **Advanced Workflow Engine** - An enhanced state machine with conditional transitions, dynamic agent assignment, and error handling.

## 1. Knowledge Hub and Semantic Search

The Knowledge Hub provides bidirectional synchronization between Notion and a vector database (Supabase with pgvector), enabling semantic search capabilities across your content.

### Key Components

- **Vector Database**: Uses pgvector extension in Supabase to store embeddings
- **Tiered Embedding Provider System**: Falls back to local embeddings if API providers are unavailable
- **Text Chunking**: Splits long text into appropriate segments for better search results
- **Semantic Search**: Find information based on meaning rather than exact keyword matches

### Usage

#### Initialize and Sync Notion Content

```python
from services.knowledge_service import get_knowledge_service

# Get the knowledge service
knowledge_service = get_knowledge_service()
await knowledge_service.initialize()

# Sync a specific Notion page
embedding_id = await knowledge_service.sync_notion_page_to_vector(
    page_id="your-notion-page-id"
)

# Or sync an entire database
embedding_ids = await knowledge_service.sync_notion_database_to_vector(
    database_id="your-notion-database-id"
)

# Or sync all configured databases
result = await knowledge_service.sync_all_notion_databases_to_vector()
```

#### Perform Semantic Search

```python
# Search across all content
results = await knowledge_service.semantic_search_notion(
    query="What is the process for onboarding new clients?",
    limit=5
)

# Search within specific databases
results = await knowledge_service.semantic_search_notion(
    query="marketing campaign design process",
    database_ids=["db1-id", "db2-id"],
    limit=10
)

# Process results
for result in results:
    print(f"Score: {result['score']}")
    print(f"Source: {result['source']}")
    print(f"Notion Page: {result.get('notion_title')}")
    print(f"Notion URL: {result.get('notion_url')}")
    print("-" * 40)
```

#### Batch Synchronization

Use the provided utility script to sync content:

```bash
# Sync all databases
python tools/sync_notion_to_vector.py

# Sync specific databases
python tools/sync_notion_to_vector.py --databases workflow_instances contacts_profiles

# Sync only content modified in the last day
python tools/sync_notion_to_vector.py --since 1d

# Force update even if content hasn't changed
python tools/sync_notion_to_vector.py --force
```

## 2. Advanced Workflow Engine

The workflow engine has been enhanced with advanced capabilities for managing complex agentic workflows.

### Key Features

- **Conditional Transitions**: Route workflows based on context data
- **Dynamic Agent Assignment**: Assign agents based on context, roles, or semantic matching
- **Error Handling**: Automatic retry mechanisms with exponential backoff
- **Timeout Management**: Handle long-running operations gracefully
- **Pre/Post Actions**: Execute actions before and after transitions

### Usage

#### Standard State Machine

For simple workflows, the standard state machine works well:

```python
from workflow.state_machine import WorkflowState, StateTransition, WorkflowStateMachine

# Define states and transitions
states = {
    "start": WorkflowState(name="start", description="Initial state", ...),
    "processing": WorkflowState(name="processing", description="Processing", ...),
    # ...more states
}

transitions = [
    StateTransition(from_state="start", to_state="processing", name="to_processing", ...),
    # ...more transitions
]

# Create state machine
workflow = WorkflowStateMachine(
    workflow_id="my_workflow",
    name="My Workflow",
    description="My workflow description",
    states=states,
    transitions=transitions,
    initial_state="start"
)

# Create an instance
instance = await workflow.create_instance(
    business_entity_id="entity-123",
    context_data={"key": "value"}
)

# Execute a transition
success, instance = await workflow.transition(
    instance_id=instance.instance_id,
    transition_name="to_processing",
    agent_id="agent-1",
    transition_data={"processed_at": datetime.now().isoformat()}
)
```

#### Enhanced State Machine

For complex workflows, use the enhanced state machine:

```python
from workflow.enhanced_transitions import EnhancedStateMachine, TransitionResult

# Create an enhanced wrapper around the standard state machine
enhanced = EnhancedStateMachine(workflow)

# Execute a transition with retry support
result = await enhanced.transition_with_retry(
    instance_id=instance.instance_id,
    transition_name="conditional_route",
    agent_id="agent-1",
    transition_data={"key": "value"}
)

# Check the result
if result.success:
    print(f"Transitioned from {result.from_state} to {result.to_state}")
else:
    print(f"Transition failed: {result.error}")
    if result.retry_recommended:
        print(f"Retry recommended after {result.retry_after_seconds} seconds")

# Dynamic agent assignment
agent_id = await enhanced.assign_agent_to_state(instance)
```

#### Advanced Transition Configuration

```python
# Conditional routing
transition = StateTransition(
    from_state="start",
    to_state="default_target",  # Default target
    name="conditional_route",
    condition_groups=[{
        "conditions": [
            {
                "field_path": "order_value",
                "operator": "greater_than",
                "expected_value": 1000
            }
        ],
        "operator": "AND"
    }],
    conditional_routing={
        "order_value > 1000": "high_value_review",
        "order_value < 100": "auto_approve"
    },
    retry_count=3,
    retry_delay_seconds=5,
    exponential_backoff=True
)
```

### Example

See `examples/enhanced_workflow_test.py` for a complete example of using the enhanced workflow capabilities.

## Integration Between Systems

These two systems can work together to create intelligent workflows:

1. Use semantic search to find relevant content for agent decision-making
2. Store workflow context data as embeddings for future reference
3. Use semantic matching for dynamic agent assignment based on context

Example of integration:

```python
from services.knowledge_service import get_knowledge_service
from workflow.enhanced_transitions import EnhancedStateMachine

# Initialize both systems
knowledge_service = get_knowledge_service()
await knowledge_service.initialize()
enhanced = EnhancedStateMachine(workflow)

# During a workflow transition, use semantic search to find relevant information
async def process_customer_request(instance_id, customer_query):
    # Get the workflow instance
    instance = await workflow.get_instance(instance_id)
    
    # Search for relevant content
    search_results = await knowledge_service.semantic_search_notion(
        query=customer_query,
        limit=3
    )
    
    # Add search results to the context data
    transition_data = {
        "search_results": [
            {"title": r.get("notion_title"), "score": r.get("score")}
            for r in search_results
        ],
        "customer_query": customer_query
    }
    
    # Execute the transition with the enhanced context
    result = await enhanced.transition_with_retry(
        instance_id=instance_id,
        transition_name="process_request",
        agent_id="agent-1",
        transition_data=transition_data
    )
    
    return result
```

## Deployment Considerations

1. **Vector Database**: Ensure your Supabase instance has the pgvector extension enabled
2. **Embedding Providers**: Configure API keys for OpenAI and/or Anthropic
3. **Local Fallback**: Install sentence-transformers for local embedding capabilities
4. **Regular Syncing**: Set up cron jobs to periodically sync Notion content to the vector database

## Next Steps

1. **Performance Optimization**: Tune chunking parameters for optimal search results
2. **Monitoring**: Add system to track vector store health and embedding provider performance
3. **UI Integration**: Create interfaces for semantic search and workflow visualization
4. **Agent Training**: Use the knowledge hub to train and improve agent capabilities