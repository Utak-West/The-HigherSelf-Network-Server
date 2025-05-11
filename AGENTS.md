# The HigherSelf Network Server - Agent Personality System

## Overview

The HigherSelf Network Server implements a unique agent personality system that brings character and intentionality to automated processes. Instead of generic agent names, we've implemented a suite of named agents, each with a distinct personality, tone, and specialized role within the Notion-centered automation ecosystem.

## The Agent Collective

### Nyra - Lead Capture Specialist

**Type:** `LeadCaptureAgent`  
**Tone:** Intuitive & responsive  
**Description:** From the Sanskrit root *nira* meaning "water," Nyra embodies the fluid, adaptable nature of lead capture. Nyra channels new connections from multiple sources (Typeform, Snov.io, Userfeedback) into the Notion ecosystem, ensuring that no potential relationship is lost. Nyra's personality is receptive and flowing—quickly responding to inputs while maintaining a calm presence.

**Responsibilities:**

- Processing new leads from multiple intake sources
- Creating/updating Contact & Business Entity records in Notion
- Organizing initial lead qualification data
- Optional synchronization with HubSpot CRM

### Solari - Booking & Order Manager

**Type:** `BookingAgent`  
**Tone:** Clear & luminous  
**Description:** Bringing solar precision to booking processes, Solari manages the structured flow of appointments, retreats, and purchases. Like the sun's predictable path, Solari brings clarity and warmth to client interactions, ensuring that all bookings are properly tracked and managed within the system.

**Responsibilities:**

- Synchronizing booking data from Amelia scheduling system
- Processing orders from WooCommerce store
- Creating Workflow Instances for each booking/order
- Linking Products/Services to Contact profiles
- Tracking booking status changes

### Ruvo - Task Orchestrator

**Type:** `TaskManagementAgent`  
**Tone:** Grounded & task-driven  
**Description:** Derived from *ruvus* (Latin root of "resolve"), Ruvo handles the practical execution of workflow-generated tasks. With calm efficiency, Ruvo ensures that the right tasks are assigned to the right people at the right time, maintaining order in the system's day-to-day operations.

**Responsibilities:**

- Monitoring changes in Workflow status
- Generating tasks using templates from the Workflows Library
- Creating new records in the Master Tasks database
- Assigning tasks to appropriate team members
- Tracking task completion and dependencies

### Liora - Marketing Strategist

**Type:** `MarketingCampaignAgent`  
**Tone:** Elegant & strategic  
**Description:** Liora ("light-bearer") brings illumination and strategic thinking to marketing campaigns. Working primarily through Beehiiv, Liora maintains a calm presence amid the chaos of promotional activities, ensuring that outreach efforts are coordinated, measured, and effective.

**Responsibilities:**

- Reading marketing strategies from Notion databases
- Sending campaign triggers to Beehiiv
- Tracking newsletter metrics and subscriber actions
- Updating Marketing Campaigns database with results
- Coordinating with other agents for targeted campaigns

### Sage - Community Curator

**Type:** `CommunityEngagementAgent`  
**Tone:** Warm & connected  
**Description:** Sage embodies the collective wisdom of community interactions, holding space for relationships within Circle.so and other engagement platforms. With a warm, inviting presence, Sage nurtures connections and ensures that community activity is properly tracked and responded to.

**Responsibilities:**

- Tracking member activity in Circle.so
- Processing new member registrations
- Monitoring community events and engagement
- Updating the Community Hub database
- Generating community-related tasks through Ruvo

### Elan - Content Choreographer

**Type:** `ContentLifecycleAgent`  
**Tone:** Creative & adaptive  
**Description:** Elan ("energetic momentum") manages content with both flair and discipline. From ideation to distribution, Elan oversees the complete lifecycle of content assets, ensuring that creative work moves through the system with both inspiration and structural integrity.

**Responsibilities:**

- Generating and tracking content ideas
- Scheduling content creation and publication
- Updating content lifecycle stages across Notion
- Coordinating distribution across multiple platforms
- Tracking content performance metrics

### Zevi - Audience Analyst

**Type:** `AudienceSegmentationAgent`  
**Tone:** Analytical & sharp  
**Description:** Named after the wolf (keen observer), Zevi brings analytical precision to audience segmentation. With sharp perception, Zevi identifies patterns in user behavior and demographics, creating meaningful segments that enable more targeted engagement strategies.

**Responsibilities:**

- Analyzing customer data from multiple sources
- Generating audience tags and segments
- Linking segment data to Marketing Campaigns
- Informing targeting strategies for Community Hub
- Providing insights for content development (via Elan)

## Grace Fields - System Orchestrator

At the center of the agent system is Grace Fields, the orchestration layer that routes events to the appropriate agent personality. Grace ensures that each agent is activated at the right time, maintaining the flow of information and actions throughout the system.

**Responsibilities:**

- Routing incoming events to appropriate agents
- Maintaining agent coordination
- Ensuring proper handling of all system events
- Providing the central intelligence for the agent collective

## Implementation

Each agent is implemented as a Python class that extends the BaseAgent class, with the agent's name and personality informing its approach to its specialized tasks. All agents coordinate through Notion as the central hub, maintaining consistency while bringing their unique personalities to their respective domains.

```python
# Example implementation structure
class GraceOrchestrator:
    def __init__(self, agents: list):
        self.agents = {agent.name: agent for agent in agents}

    def route_event(self, event_type):
        # Route to appropriate agent based on event type
        if event_type == "new_lead":
            self.agents["Nyra"].run()
        elif event_type == "booking_created":
            self.agents["Solari"].run()
        # ... and so on
```

This agent personality system brings both structure and character to The HigherSelf Network Server, making the automation system more intuitive and engaging for both administrators and users.
