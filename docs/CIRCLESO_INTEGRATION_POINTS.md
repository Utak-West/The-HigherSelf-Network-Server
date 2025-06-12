# Circle.so Integration Points in The HigherSelf Network Server

This document identifies all Circle.so integration points in the codebase that need to be updated when migrating to BetterMode.

## API and Webhook Handlers

### 1. `api/webhooks_circleso.py`

This file contains webhook handlers for Circle.so events:
- `/new_member` - Handles new member registrations
- `/member_activity` - Handles member activity events
- `/event` - Handles community events

These webhook handlers interact with the `CommunityEngagementAgent` to process events and update Notion databases.

## Agent Implementation

### 2. `agents/community_engagement_agent.py`

The `CommunityEngagementAgent` class is responsible for:
- Processing new community members from Circle.so
- Tracking member activity
- Scheduling community events
- Sending notifications to community members

This agent interacts with Circle.so and maintains Notion as the central data hub.

## Configuration and Environment Variables

### 3. `.env.example`

Contains Circle.so API credentials:
```
# Circle.so Community Platform
CIRCLE_API_TOKEN=your_circle_api_token
CIRCLE_COMMUNITY_ID=your_circle_community_id
```

### 4. `services/integration_manager.py`

Contains configuration for enabling/disabling Circle.so integration:
```python
class IntegrationManagerConfig(BaseModel):
    # ...
    enable_circle: bool = True
    # ...
```

## Data Models

### 5. `models/notion_db_models_extended.py`

Contains the `CommunityMember` model used to represent Circle.so community members:
```python
class CommunityMember(BaseModel):
    """
    Represents a member in the Community Hub DB.
    This tracks community engagement and membership details.
    """
    member_id: str = Field(
        default_factory=lambda: f"MEMBER-{uuid4().hex[:8]}",
        description="Unique member ID",
    )
    # ...
```

### 6. `db/migrations/01_create_core_tables.sql`

Contains database schema for community members:
```sql
CREATE TABLE IF NOT EXISTS community_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts_profiles(id),
    username TEXT UNIQUE,
    display_name TEXT,
    membership_level TEXT,
    join_date TIMESTAMPTZ,
    last_active_date TIMESTAMPTZ,
    engagement_score INTEGER,
    interests JSONB DEFAULT '[]'::JSONB,
    badges JSONB DEFAULT '[]'::JSONB,
    circle_member_id TEXT,
    discord_user_id TEXT,
    slack_user_id TEXT,
    custom_fields JSONB DEFAULT '{}'::JSONB,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Server Configuration

### 7. `api/server.py`

Includes the Circle.so webhook router:
```python
from api.webhooks_circleso import router as circleso_router
# ...
app.include_router(circleso_router)
```

## Agent Personalities

### 8. `agents/agent_personalities.py`

Contains references to Circle.so in the Sage agent personality:
```python
async def run(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle community member interactions in Circle.so, tracking engagement
    and managing member profiles in the Community Hub database.
    """
    # ...
```

## Documentation

### 9. `SAGE_COMMUNITY_ROADMAP.md`

Contains references to Circle.so in the community roadmap:
```markdown
- **Member Synchronization**: Maintaining consistent member records between systems
- **Discussion Management**: Monitoring and moderating Circle.so discussions
- **Event Integration**: Publishing and managing community events within Circle.so
- **Space Management**: Organizing and maintaining community spaces and groups
- **Content Publishing**: Distributing content through appropriate Circle.so spaces
```

### 10. `AGENTS.md`

Contains references to Circle.so in the agent descriptions:
```markdown
**Type:** `CommunityEngagementAgent`
**Tone:** Warm & connected
**Description:** Sage embodies the collective wisdom of community interactions, holding space for relationships within Circle.so and other engagement platforms.
```

These integration points will need to be updated when migrating from Circle.so to BetterMode.
