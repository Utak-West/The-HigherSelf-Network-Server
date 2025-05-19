# The HigherSelf Network Server Development Guidelines

## Project Overview
The HigherSelf Network Server is an intelligent automation platform for art galleries, wellness centers, and consultancy businesses, using a modular agent-based architecture with Notion as the central hub.

## Key Components
- Modular agent system with specialized personalities
- 16 interconnected Notion databases
- Workflow state machines for business processes
- Airtable integration for operations dashboards
- RAG capabilities for knowledge management

## Development Standards
- Follow Pydantic AI framework rigorously
- Use type hints consistently
- Document all agent capabilities and event handling
- Handle API rate limits appropriately
- Provide detailed logs for troubleshooting
- Keep agent logic modular and replaceable

## Common Commands
- `python -m pytest tests/` - Run all tests
- `docker-compose up -d` - Start all services
- `python scripts/sync_notion.py` - Manually trigger Notion sync
- `python scripts/generate_agent.py --name AgentName` - Generate agent boilerplate

## File Structure
- `agents/` - Agent implementations
- `api/` - API endpoints and server
- `config/` - Configuration management
- `db/` - Database models and migrations
- `docs/` - Documentation

## Agent System Architecture

The HigherSelf Network Server uses a modular agent-based architecture with specialized agent personalities:

1. **Nyra (Lead Capture Specialist)** - Intuitive & Responsive
   - Captures leads from various sources
   - Handles lead enrichment and qualification
   - Manages contact records in Notion

2. **Solari (Booking & Order Manager)** - Clear & Luminous
   - Processes retreat bookings from Amelia
   - Handles WooCommerce orders
   - Creates and manages workflow instances

3. **Ruvo (Task Orchestrator)** - Grounded & Task-driven
   - Creates, assigns, and tracks tasks
   - Manages workflow-generated tasks
   - Updates the Master Tasks database

4. **Liora (Marketing Strategist)** - Elegant & Strategic
   - Manages email campaigns through Beehiiv
   - Handles audience targeting
   - Tracks campaign performance

5. **Sage (Community Curator)** - Warm & Connected
   - Handles community member interactions in Circle.so
   - Tracks engagement metrics
   - Manages member profiles

6. **Elan (Content Choreographer)** - Creative & Adaptive
   - Manages content lifecycle
   - Handles content distribution
   - Tracks content performance

7. **Zevi (Audience Analyst)** - Analytical & Sharp
   - Analyzes customer data
   - Creates and manages audience segments
   - Provides insights for targeted marketing

8. **Atlas (Knowledge Retrieval Specialist)** - Comprehensive & Precise
   - Manages the RAG system
   - Retrieves relevant knowledge
   - Enhances AI responses with context

9. **Grace Fields (Master Orchestrator)** - Harmonious & Coordinating
   - Routes events to appropriate agents
   - Manages multi-agent workflows
   - Maintains system coordination

## Business Entities

The HigherSelf Network Server supports multiple business entities:

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
