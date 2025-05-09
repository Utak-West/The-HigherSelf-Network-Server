# The HigherSelf Network Server Quick Reference Guide

## Core Principle

> **Notion serves as the central data and workflow management hub** for all operations within The HigherSelf Network, including The Connection Practice and The 7 Space.

## Integration Service Map

```
┌───────────────────────────────────────────────────────────────────┐
│                 THE HIGHERSELF NETWORK SERVER                      │
│                                                                   │
│  ┌─────────────┐     ┌──────────────────┐     ┌──────────────┐   │
│  │ API Server  │────▶│Integration Manager│────▶│Notion Service│   │
│  └─────────────┘     └──────────────────┘     └──────┬───────┘   │
│         ▲                      │                      │           │
│         │                      │                      │           │
│         │                      ▼                      ▼           │
│  ┌─────────────┐     ┌──────────────────┐     ┌──────────────┐   │
│  │  Webhooks   │     │  Base Service    │     │    NOTION    │   │
│  └─────────────┘     └──────────────────┘     │  DATABASES   │   │
│                              │                └──────────────┘   │
│                              │                                   │
│                              ▼                                   │
│     ┌────────────────────────────────────────────────┐          │
│     │              Service Integrations               │          │
│     │  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │          │
│     │  │ TypeForm │ │WooCommerce│ │    Acuity    │    │          │
│     │  └──────────┘ └──────────┘ └──────────────┘    │          │
│     │  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │          │
│     │  │  Amelia  │ │UserFeedback│ │    TutorLM   │    │          │
│     │  └──────────┘ └──────────┘ └──────────────┘    │          │
│     │  ┌───────────────────────────────────────┐     │          │
│     │  │          AI Providers                 │     │          │
│     │  │   (OpenAI, Anthropic, etc.)          │     │          │
│     │  └───────────────────────────────────────┘     │          │
│     └────────────────────────────────────────────────┘          │
└───────────────────────────────────────────────────────────────────┘
```

## Quick Start Guide

### 1. Environment Setup

Copy the example environment file and configure with your API credentials:

```bash
cp deployment/.env.example .env
nano .env
```

Essential variables:
- `NOTION_API_TOKEN`: Your Notion integration token
- `NOTION_*_DATABASE_ID`: IDs for each Notion database
- `SERVICE_*`: API credentials for each integrated service

### 2. Running the Server

**Using Docker (recommended):**
```bash
docker-compose up -d
```

**Direct Python execution:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### 3. Essential Endpoints

- `GET /health`: Check system status
- `POST /api/webhooks/{service_name}`: Webhook receivers
- `GET /api/status/{service_name}`: Check service status
- `POST /api/notion/sync`: Manually trigger Notion sync

## Notion Database Structure

| Database | Purpose | Key Properties |
|----------|---------|---------------|
| Clients | Central client repository | Contact info, Relations to other DBs |
| Products | Products and services | Price, Type, Status |
| Orders | Purchase transactions | Client, Products, Status |
| Appointments | Scheduled sessions | Client, Date/Time, Service Type |
| Feedback | User comments/ratings | Client, Content, Sentiment |
| Active Workflow Instances | Process tracking | Current State, Status, History Log |

## Data Flow Overview

All integrations follow this pattern to maintain Notion as the central hub:

1. **Incoming Data:** 
   ```
   External Service → Service Integration → Integration Manager → Notion
   ```

2. **Outgoing Data:**
   ```
   Notion → Integration Manager → Service Integration → External Service
   ```

3. **Bidirectional Sync:**
   - All records contain `notion_page_id` reference
   - Records in external systems contain `notion_managed: true` metadata
   - Timestamps track last synchronization

## Common Commands

**View service status:**
```bash
curl http://localhost:8000/health
```

**Trigger Notion synchronization:**
```bash
curl -X POST http://localhost:8000/api/notion/sync
```

**Deploy updates:**
```bash
./deployment/github-docker-deploy.sh
```

## Troubleshooting

| Issue | Check |
|-------|-------|
| Service connection failures | Verify API credentials in .env |
| Webhook errors | Check webhook secret keys and signatures |
| Notion sync failures | Confirm database IDs and API token permissions |
| Missing data | Check logs in the /logs directory |

## Support Resources

- Training Manual: See `documentation/TRAINING_MANUAL.md`
- API Documentation: [https://api.thehigherself.network/docs](https://api.thehigherself.network/docs)
- GitHub Repository: [https://github.com/Utak-West/The-HigherSelf-Network-Server](https://github.com/Utak-West/The-HigherSelf-Network-Server)
- Support Email: [support@thehigherself.network](mailto:support@thehigherself.network)