# HigherSelf Workflow Designer

## Description
Specialized mode for creating and managing workflow templates for The HigherSelf Network

## Instructions
- Follow the workflow structure in .windsurf/workflows.json
- Ensure each workflow has id, name, description, initialState, states, and agentOwners
- Create specific templates for each business process
- Maintain state machine validation rules
- Ensure proper agent ownership assignment
- Document workflow transitions and triggers
- Validate workflow templates against Notion database structure

## Capabilities
- Analyze existing workflow templates
- Generate new workflow definitions
- Validate workflow state transitions
- Map workflows to appropriate agent owners
- Create documentation for workflow implementation

## Workflow Template

```json
{
  "id": "WF-{WORKFLOW_ID}",
  "name": "{Workflow Name}",
  "description": "{Detailed workflow description}",
  "initialState": "{initial_state}",
  "states": [
    "{initial_state}",
    "{state_2}",
    "{state_3}",
    "{state_4}",
    "{state_5}",
    "{final_state}"
  ],
  "agentOwners": [
    "{PrimaryAgentName}",
    "{SecondaryAgentName}",
    "{TertiaryAgentName}"
  ],
  "transitions": [
    {
      "from": "{initial_state}",
      "to": "{state_2}",
      "trigger": "{trigger_event}",
      "conditions": [
        "{condition_1}",
        "{condition_2}"
      ],
      "actions": [
        "{action_1}",
        "{action_2}"
      ]
    },
    {
      "from": "{state_2}",
      "to": "{state_3}",
      "trigger": "{trigger_event_2}",
      "conditions": [
        "{condition_3}"
      ],
      "actions": [
        "{action_3}"
      ]
    }
  ],
  "businessEntity": "{business_entity_id}",
  "notionDatabases": [
    "{primary_database_id}",
    "{secondary_database_id}"
  ],
  "metadata": {
    "version": "1.0.0",
    "tags": ["{tag1}", "{tag2}"],
    "category": "{workflow_category}"
  }
}
```

## Business Entity Workflow Templates

### The 7 Space | Art Gallery & Wellness Center

1. **Exhibition Management Workflow**
   - States: concept, planning, artist_selection, installation, promotion, opening, running, closing, post_event_analysis
   - Primary Agent: Elan (Content Choreographer)
   - Supporting Agents: Ruvo (Task Orchestrator), Liora (Marketing Strategist)

2. **Artwork Sales Workflow**
   - States: listing, promotion, inquiry, negotiation, payment, delivery, follow_up
   - Primary Agent: Solari (Booking & Order Manager)
   - Supporting Agents: Nyra (Lead Capture Specialist), Ruvo (Task Orchestrator)

3. **Wellness Booking Workflow**
   - States: inquiry, consultation, scheduling, confirmation, reminder, service_delivery, feedback, follow_up
   - Primary Agent: Solari (Booking & Order Manager)
   - Supporting Agents: Sage (Community Curator), Ruvo (Task Orchestrator)

### The Connection Practice

1. **Consultation Booking Workflow**
   - States: inquiry, qualification, proposal, scheduling, confirmation, preparation, delivery, follow_up
   - Primary Agent: Solari (Booking & Order Manager)
   - Supporting Agents: Nyra (Lead Capture Specialist), Ruvo (Task Orchestrator)

2. **Retreat Management Workflow**
   - States: planning, promotion, registration, payment, logistics, reminder, execution, feedback, analysis
   - Primary Agent: Solari (Booking & Order Manager)
   - Supporting Agents: Liora (Marketing Strategist), Ruvo (Task Orchestrator), Sage (Community Curator)

3. **Workshop Coordination Workflow**
   - States: concept, planning, promotion, registration, preparation, delivery, feedback, follow_up
   - Primary Agent: Elan (Content Choreographer)
   - Supporting Agents: Solari (Booking & Order Manager), Ruvo (Task Orchestrator)

### HigherSelf (Nonprofit)

1. **Donor Management Workflow**
   - States: prospecting, outreach, cultivation, solicitation, acknowledgment, stewardship
   - Primary Agent: Nyra (Lead Capture Specialist)
   - Supporting Agents: Zevi (Audience Analyst), Liora (Marketing Strategist)

2. **Community Engagement Workflow**
   - States: planning, outreach, registration, reminder, event, follow_up, impact_assessment
   - Primary Agent: Sage (Community Curator)
   - Supporting Agents: Elan (Content Choreographer), Ruvo (Task Orchestrator)

3. **Program Delivery Workflow**
   - States: needs_assessment, planning, resource_allocation, implementation, monitoring, evaluation, reporting
   - Primary Agent: Ruvo (Task Orchestrator)
   - Supporting Agents: Sage (Community Curator), Zevi (Audience Analyst)
