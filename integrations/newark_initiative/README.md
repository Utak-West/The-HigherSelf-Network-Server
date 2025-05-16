# Newark Well Initiative Integration

This document explains how to integrate the Newark Well specialized agents with the HigherSelf Network Server.

## Overview

The Newark Well initiative introduces five specialized agents to support wellness, crisis intervention, and homelessness outreach programs in the City of Newark:

1. **Grace Fields** - Orchestration Agent
2. **Cora** - Knowledge Management Agent
3. **Cassia** - Wellness Coordinator Agent
4. **Terra** - Outreach Coordinator Agent
5. **Vesta** - Program Evaluator Agent

These agents work together to provide comprehensive support for Newark's wellness programs through the HigherSelf Network Server infrastructure.

## Integration Steps

### 1. Configuration

Add the following environment variables to your server configuration:

```env
# Knowledge Management Agent (Cora)
NEWARK_KNOWLEDGE_DB_ID=your-notion-knowledge-db-id
NEWARK_TRAINING_MATERIALS_ID=your-notion-training-materials-db-id

# Wellness Coordinator Agent (Cassia)
NEWARK_WELLNESS_RESOURCES_ID=your-notion-wellness-resources-db-id
NEWARK_WELLNESS_CHECKINS_ID=your-notion-wellness-checkins-db-id

# Outreach Coordinator Agent (Terra)
NEWARK_CLIENT_INTERACTIONS_ID=your-notion-client-interactions-db-id
NEWARK_SERVICE_PROVIDERS_ID=your-notion-service-providers-db-id
NEWARK_RESOURCE_AVAILABILITY_ID=your-notion-resource-availability-db-id

# Program Evaluator Agent (Vesta)
NEWARK_PROGRAM_METRICS_ID=your-notion-program-metrics-db-id
NEWARK_REPORT_CONFIGS_ID=your-notion-report-configurations-db-id
NEWARK_REPORT_OUTPUTS_ID=your-notion-report-outputs-db-id

# General settings
NEWARK_API_ENABLED=True
NEWARK_LOG_LEVEL=INFO
```

### 2. Add Router to Server

Modify your main `app.py` file to include the Newark API router:

```python
from fastapi import FastAPI
from server_protocols.newark_api_integration import newark_router

app = FastAPI(
    title="HigherSelf Network Server",
    description="API for the HigherSelf Network Server with Newark Initiative integration",
    version="1.0.0"
)

# Include the Newark router
app.include_router(newark_router, prefix="/api/newark", tags=["Newark Initiative"])
```

### 3. Import Required Files

Copy the Newark Well protocol files to your server's module directory:

```
├── server_protocols/
│   ├── newark_agent_protocol.py
│   ├── newark_orchestration.py (Grace Fields)
│   ├── newark_knowledge_agent.py (Cora)
│   ├── newark_wellness_agent.py (Cassia)
│   ├── newark_outreach_agent.py (Terra)
│   ├── newark_evaluation_agent.py (Vesta)
│   ├── newark_api_integration.py
│   └── newark_config.py
```

### 4. Initialize Newark Agents at Server Startup

Add the following code to your server's startup sequence:

```python
from server_protocols.newark_config import NewarkConfig
from server_protocols.newark_api_integration import get_agents

async def startup_event():
    # Check if Newark integration is enabled
    if os.getenv("NEWARK_API_ENABLED", "False").lower() == "true":
        if NewarkConfig.is_configured():
            # Initialize Newark agents
            await get_agents()
            logger.info("Newark Well initiative agents initialized successfully")
        else:
            logger.warning("Newark agents not properly configured. Newark functionality disabled.")

app.add_event_handler("startup", startup_event)
```

## API Endpoints

Once integrated, the following endpoints will be available:

### Knowledge Management (Cora)
- `POST /api/newark/knowledge/training-material` - Add new training material
- `GET /api/newark/knowledge/training-materials` - List training materials
- `GET /api/newark/knowledge/training-material/{material_id}` - Get specific material
- `PUT /api/newark/knowledge/training-material/{material_id}` - Update material

### Wellness Coordination (Cassia)
- `POST /api/newark/wellness/check-in` - Process a wellness check-in
- `POST /api/newark/wellness/resource-request` - Request wellness resources
- `GET /api/newark/wellness/resources` - List wellness resources
- `POST /api/newark/wellness/schedule-session` - Schedule a wellness session

### Outreach Coordination (Terra)
- `POST /api/newark/outreach/client-interaction` - Log client interaction
- `POST /api/newark/outreach/service-referral` - Create service referral
- `GET /api/newark/outreach/resources` - Get outreach resources
- `POST /api/newark/outreach/planning` - Create outreach plan

### Program Evaluation (Vesta)
- `POST /api/newark/evaluation/report` - Generate evaluation report
- `POST /api/newark/evaluation/metrics` - Update program metrics
- `GET /api/newark/evaluation/program-stats` - Get program statistics
- `GET /api/newark/evaluation/trends` - Analyze program trends

### System
- `GET /api/newark/health` - Check health status of all agents

## Agent Architecture

```ascii
┌─────────────────────────────────────────────────────────────┐
│                  HigherSelf Network Server                   │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Endpoints                     │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                         Grace Fields Agent                   │
└───┬───────────────────┬───────────────────┬─────────────────┘
    │                   │                   │                  │
    ▼                   ▼                   ▼                  ▼
┌─────────┐       ┌──────────┐       ┌──────────┐      ┌──────────┐
│  Cora   │       │  Cassia  │       │  Terra   │      │  Vesta   │
│Knowledge│       │ Wellness │       │ Outreach │      │ Program  │
│ Agent   │       │  Agent   │       │  Agent   │      │Evaluator │
└─────────┘       └──────────┘       └──────────┘      └──────────┘
```

## Additional Information

- All agents use Notion as their data store
- Access control is integrated with the HigherSelf Network Server's authentication system
- Specialized agents can be extended or modified as needed
- For detailed information, refer to the Newark Well initiative documentation at `/Users/utakwest/Desktop/HigherSelf/HigherSelf Initiatives/Newark Well/`
