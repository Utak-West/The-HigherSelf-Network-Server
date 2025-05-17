# MongoDB Integration Guide

This guide explains how to set up and use MongoDB with The HigherSelf Network Server.

## Overview

MongoDB is used in The HigherSelf Network Server for:

1. **Agent State Management** - Storing agent state, configuration, and runtime data
2. **Workflow Execution** - Tracking workflow instances and their execution state
3. **Task Management** - Managing tasks assigned to agents and users
4. **System Health Monitoring** - Storing system health metrics and logs
5. **Agent Communication Patterns** - Storing communication patterns between agents
6. **API Integration Management** - Managing API integrations with external services

## Setup Instructions

### 1. Configure Environment Variables

Add the following environment variables to your `.env` file:

```
# MongoDB Configuration
MONGODB_URI=mongodb://username:password@localhost:27017/higherselfnetwork
MONGODB_DB_NAME=higherselfnetwork
MONGODB_USERNAME=higherself_app
MONGODB_PASSWORD=secure_password_here
MONGODB_ENABLED=true
```

For MongoDB Atlas or other cloud providers, use the connection string they provide:

```
MONGODB_URI=mongodb+srv://username:password@cluster0.mongodb.net/higherselfnetwork
```

### 2. Initialize MongoDB Collections

Run the MongoDB setup utility to create all required collections and indexes:

```bash
# Using Docker
docker-compose run --rm windsurf-agent python -m tools.mongo_db_setup

# Using Python directly
python -m tools.mongo_db_setup
```

This will create the following collections:

- `agents` - Agent registry and configuration
- `workflows` - Workflow definitions
- `workflow_instances` - Workflow execution instances
- `tasks` - Tasks assigned to agents or users
- `agent_communication` - Communication patterns between agents
- `api_integrations` - API integration configurations
- `system_health` - System health metrics and logs

### 3. Verify MongoDB Connection

You can verify the MongoDB connection by checking the logs when starting the server:

```bash
docker-compose up
```

Look for log messages like:

```
INFO: Connected to MongoDB at mongodb://localhost:27017/higherselfnetwork
```

## Using MongoDB in Your Code

### MongoDB Service

The MongoDB service provides a simple interface for interacting with MongoDB:

```python
from services.mongodb_service import mongo_service

# Insert a document
document_id = mongo_service.insert_one("collection_name", {"key": "value"})

# Find a document
document = mongo_service.find_one("collection_name", {"key": "value"})

# Update a document
mongo_service.update_one("collection_name", {"key": "value"}, {"new_key": "new_value"})

# Delete a document
mongo_service.delete_one("collection_name", {"key": "value"})
```

For asynchronous operations:

```python
# Insert a document asynchronously
document_id = await mongo_service.async_insert_one("collection_name", {"key": "value"})

# Find a document asynchronously
document = await mongo_service.async_find_one("collection_name", {"key": "value"})
```

### MongoDB Repositories

For a higher-level interface, use the MongoDB repositories:

```python
from repositories import mongo_repository_factory

# Get a repository for a specific collection
agent_repo = mongo_repository_factory.get_agent_repository()

# Find an agent by ID
agent = agent_repo.find_by_id("agent_id")

# Find agents by status
active_agents = agent_repo.find_by_status("active")

# Save an agent
agent_id = agent_repo.save(agent)
```

For asynchronous operations:

```python
# Find an agent by ID asynchronously
agent = await agent_repo.async_find_by_id("agent_id")

# Save an agent asynchronously
agent_id = await agent_repo.async_save(agent)
```

## MongoDB Models

The MongoDB models are defined in `models/mongodb_models.py`:

```python
from models.mongodb_models import AgentDocument, WorkflowDocument

# Create a new agent
agent = AgentDocument(
    name="Agent Name",
    agent_type="assistant",
    capabilities=["text_generation", "task_execution"],
    status="active"
)

# Create a new workflow
workflow = WorkflowDocument(
    name="Workflow Name",
    workflow_type="automation",
    steps=[{"name": "Step 1", "action": "do_something"}],
    required_agents=["agent_id"]
)
```

## MongoDB and Notion Integration

The HigherSelf Network Server uses both MongoDB and Notion for different purposes:

- **Notion** - Used for structured data, content management, and user-facing databases
- **MongoDB** - Used for system state, agent communication, and high-frequency operations

Data can be synchronized between MongoDB and Notion using the database sync service:

```python
from services.database_sync_service import DatabaseSyncService

sync_service = DatabaseSyncService()
await sync_service.sync_notion_to_mongodb("collection_name", "notion_database_id")
```

## Troubleshooting

### Connection Issues

If you're having trouble connecting to MongoDB:

1. Check that MongoDB is running:
   ```bash
   docker-compose ps
   ```

2. Verify your connection string:
   ```bash
   mongo "mongodb://username:password@localhost:27017/higherselfnetwork"
   ```

3. Check for authentication issues:
   ```bash
   # In MongoDB shell
   use higherselfnetwork
   db.auth("username", "password")
   ```

### Data Issues

If you're having trouble with data:

1. Check that collections exist:
   ```bash
   # In MongoDB shell
   show collections
   ```

2. Check document structure:
   ```bash
   # In MongoDB shell
   db.collection_name.findOne()
   ```

3. Run the setup script again:
   ```bash
   python -m tools.mongo_db_setup
   ```

## Best Practices

1. **Use Repositories** - Always use the repository classes for data access
2. **Validate Data** - Use Pydantic models to validate data before storing
3. **Handle Errors** - Always handle MongoDB errors in your code
4. **Use Indexes** - Create indexes for frequently queried fields
5. **Use Transactions** - Use transactions for operations that modify multiple documents
6. **Monitor Performance** - Monitor MongoDB performance using the system health collection
