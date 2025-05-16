---
trigger: model_decision
description: when working on our automation servers and with any agents
---

# Higher Self Network Server Rules

## Agent System Rules

1. **Agent Autonomy Boundaries**: Agents should only operate within their designated domains and responsibilities (Lead Capture, Booking, Task Management, etc.). Never allow one agent to override another agent's domain without explicit authorization.

2. **State Machine Compliance**: All workflow implementations must follow state machine patterns with clear stages, transitions, and validation checks.

3. **Agent Communication Security**: All inter-agent communications should use the authorized Agent Communication Patterns from the registry database. No direct agent-to-agent communications outside of established patterns.

4. **Named Agent Personalities**: Preserve the unique personality traits of each agent (Nyra, Solari, Ruvo, etc.) in all communications to maintain consistent brand voice.

5. **Graceful Degradation**: Implement fallback mechanisms so agents can operate with limited functionality when dependent services are unavailable.

## Notion Database Integrity Rules

1. **Schema Consistency**: Maintain strict adherence to the 16-database schema design. All database modifications must preserve referential integrity.

2. **Real-time Sync Protection**: Implement optimistic locking or versioning to prevent data corruption during concurrent updates to Notion databases.

3. **Data Validation**: All data entering the system through any channel must be validated against Pydantic models before storage in Notion.

4. **Audit Trail Requirements**: Maintain comprehensive logging of all database operations for audit purposes.

## Integration Security Rules

1. **API Key Management**: Never hardcode API keys in the codebase. Use environment variables and secure storage for all integration credentials.

2. **Webhook Authentication**: All incoming webhooks must be properly authenticated using the appropriate security mechanisms for each platform (Circle.so, Beehiiv, etc.).

3. **Rate Limiting Compliance**: Implement rate limiting for all outgoing API calls to prevent service disruptions and respect external API limits.

4. **Data Residency**: Sensitive data processing should prioritize local embedding providers over external ones when privacy concerns exist.

## Softr Integration Rules

1. **Interface Consistency**: All Softr templates must maintain consistent UI/UX patterns across different business applications (art gallery, wellness center, consultancy).

2. **Authentication Flow**: Implement proper authentication flows for staff-agent interactions through Softr interfaces.

3. **Staff Permission Boundaries**: Enforce strict permission controls limiting staff access to only the agents and data relevant to their roles.

## Deployment and Operation Rules

1. **Environment Isolation**: Maintain strict separation between development, testing, and production environments with appropriate configuration for each.

2. **Health Monitoring**: Implement comprehensive health checks for all agents and services with automated alerts for anomalies.

3. **Fallback Providers**: Maintain automatic fallback mechanisms for embedding providers to ensure system reliability.

4. **Testing Mode Controls**: Use testing mode appropriately to prevent accidental interactions with production systems during development.

## Hugging Face Integration Rules

1. **Model Selection Governance**: Follow the established intelligent model selection process for choosing appropriate Hugging Face models based on task requirements.

2. **Processing Optimization**: Balance between speed and quality based on the specific NLP task requirements when using Hugging Face models.

3. **Fine-tuning Guidance**: Any fine-tuning of Hugging Face models must follow the optimization plan guidelines.

## Business Logic Rules

1. **Workflow Instantiation**: When creating new workflow instances, always follow the templates defined in the Workflows Library.

2. **Entity Relationship Integrity**: Maintain proper relationships between Business Entities, Contacts, Products, and other core operational databases.

3. **Task Prioritization**: Task Management agent must prioritize tasks according to consistent business rules across all business types.

4. **Audience Segmentation Logic**: Ensure audience segmentation follows established patterns for marketing campaign targeting.
