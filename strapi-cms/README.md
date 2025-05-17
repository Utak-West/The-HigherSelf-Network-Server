# Higher Self Network Strapi CMS

A headless CMS implementation using Strapi to provide API capabilities for the most vital functions of the Higher Self Network Server, with a focus on supporting The 7 Space (Art Gallery & Wellness Center) operations.

## Overview

This Strapi implementation provides headless API capabilities for essential operational workflows including:

1. **Gallery Exhibit Management** - Managing art exhibits from planning to post-event analysis
2. **Wellness Service Booking** - Handling the complete lifecycle of wellness service bookings
3. **Consultation Project Management** - Managing consultancy projects through all stages
4. **Marketing Campaign Management** - Orchestrating multi-channel marketing campaigns
5. **Content Creation and Distribution** - Supporting the content lifecycle

## Compliance with Server Rules

This implementation strictly follows the Higher Self Network Server Rules:

### Agent System Rules
- Maintains agent autonomy boundaries with clear responsibilities
- Implements state machine patterns for all workflow implementations
- Supports secure agent communications through the API Gateway
- Preserves agent personalities in communications

### Notion Database Integrity
- Maintains schema consistency with the 16-database design
- Implements optimistic locking for real-time sync protection
- Validates data using Strapi's built-in validation
- Maintains comprehensive audit logging

### Integration Security
- Uses environment variables for all API keys and credentials
- Implements webhook authentication for all incoming webhooks
- Applies rate limiting for API calls
- Respects data residency requirements

### Softr Integration
- Maintains consistent UI/UX patterns via API-driven interfaces
- Supports proper authentication flows
- Enforces staff permission boundaries

## Content Types

The following content types are implemented:

- **Exhibit** - Art gallery exhibits
- **Artist** - Artists whose works are featured
- **Artwork** - Artworks displayed in the gallery
- **Wellness Service** - Wellness services offered
- **Practitioner** - Wellness practitioners
- **Booking** - Service booking management
- **Consultation** - Consultation project management
- **Campaign** - Marketing campaign management
- **Content** - Content creation and distribution
- **Workflow State** - States for workflow state machines
- **Workflow Transition** - Transitions between workflow states
- **Agent** - System agents with defined responsibilities

## State Machine Implementation

All content types that follow workflows implement state machine patterns with:

1. Defined states with clear boundaries
2. Validated transitions between states
3. Automated notifications for state changes
4. Comprehensive logging of transitions

## API Endpoints

Strapi automatically generates REST and GraphQL APIs for all content types. Additional custom endpoints include:

- `/webhooks/notion` - For Notion integration events
- `/webhooks/api-gateway` - For API Gateway communications
- `/webhooks/softr` - For Softr interface interactions

## Installation and Setup

1. Install dependencies:
   ```
   cd strapi-cms
   npm install
   ```

2. Copy environment variables:
   ```
   cp .env.example .env
   ```

3. Configure environment variables in `.env` file

4. Start development server:
   ```
   npm run develop
   ```

5. Build for production:
   ```
   npm run build
   npm run start
   ```

## Integration with Higher Self Network Server

This Strapi CMS integrates with other components of the Higher Self Network Server:

1. **API Gateway Integration** - Events from Strapi trigger appropriate workflows in the API Gateway
2. **Notion Synchronization** - Changes in Strapi content sync bidirectionally with Notion databases
3. **Agent Communications** - Strapi communicates with system agents through the appropriate channels
4. **Softr Interface Support** - APIs support Softr templates for public interfaces

## Security Considerations

Following the server rules for security:

1. All API keys must be stored in environment variables
2. Webhook endpoints require signature validation
3. Rate limiting is applied to all APIs
4. Authentication and authorization is strictly enforced
5. Audit logging tracks all system operations

## Extending the System

When extending this system, follow these guidelines:

1. Create new content types following the established patterns
2. Implement lifecycle hooks for state machine compliance
3. Configure proper relations between entities
4. Add appropriate webhooks for integration points
5. Maintain audit trails for all operations
6. Document your extensions thoroughly

## License

Copyright © 2025 Higher Self Network. All rights reserved.
