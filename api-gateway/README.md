# Higher Self Network - API Gateway

A headless API Gateway for The Higher Self Network, providing a unified interface for integrating with Notion databases and Softr interfaces.

## Features

- RESTful API endpoints following state machine workflow patterns
- Integration with Notion databases
- Caching layer to reduce API calls and costs
- Comprehensive logging and error handling
- Authentication and authorization
- Rate limiting protection

## Architecture

This API Gateway implements a headless architecture that sits between your Notion databases and client applications:

```
Notion Databases → API Gateway → Softr Interfaces/External Clients
```

## Workflows Implemented

- [x] Gallery Exhibit Management Workflow
- [ ] Wellness Service Booking Workflow
- [ ] Consultation Project Management Workflow
- [ ] Multi-Channel Marketing Campaign Workflow
- [ ] Content Creation and Distribution Workflow
- [ ] Staff Permission Management Workflow
- [ ] Agent Communication Security Workflow
- [ ] Softr Interface Publishing Workflow

## Getting Started

### Prerequisites

- Node.js 14.x or higher
- NPM 6.x or higher
- Notion API Key and database IDs

### Installation

1. Clone the repository (if not already done)
2. Create a .env file from the example:
   ```bash
   cp .env.example .env
   ```
3. Edit the .env file with your Notion API key and database IDs
4. Install dependencies:
   ```bash
   cd api-gateway
   npm install
   ```
5. Start the development server:
   ```bash
   npm run dev
   ```

### Running in Production

For production deployment, consider using a process manager like PM2:

```bash
npm install -g pm2
pm2 start src/index.js --name "higher-self-api"
```

## API Documentation

### Gallery Exhibit Management API

#### Get All Exhibits
```
GET /api/v1/gallery/exhibits
```
Query parameters:
- `state`: Filter by exhibit state (proposed, reviewed, scheduled, installed, active, archived)
- `artist`: Filter by artist name
- `featured`: Filter for featured exhibits (true/false)

#### Get Exhibit by ID
```
GET /api/v1/gallery/exhibits/:id
```

#### Create New Exhibit
```
POST /api/v1/gallery/exhibits
```
Request body example:
```json
{
  "title": "Nature in Abstract",
  "artist": "Jane Smith",
  "description": "A series exploring natural forms through abstract expression",
  "mediums": ["Oil", "Canvas"],
  "dimensions": "24\" x 36\"",
  "price": 1200,
  "images": ["https://example.com/image1.jpg"],
  "proposedStartDate": "2025-06-15",
  "proposedEndDate": "2025-07-15",
  "featuredPiece": false,
  "contactInformation": {
    "email": "jane@example.com",
    "phone": "555-123-4567",
    "website": "https://janesmith.com"
  }
}
```

#### Update Exhibit
```
PUT /api/v1/gallery/exhibits/:id
```
Request body: Same structure as create, all fields optional

#### Transition Exhibit State
```
POST /api/v1/gallery/exhibits/:id/transition
```
Request body example:
```json
{
  "currentState": "proposed",
  "newState": "reviewed",
  "notes": "Approved by gallery committee"
}
```

#### Archive Exhibit
```
DELETE /api/v1/gallery/exhibits/:id
```

## Compliance with Server Rules

This API Gateway implementation adheres to the Higher Self Network Server Rules:

### Agent System Rules
- State Machine Compliance: All workflows follow state machine patterns with clear stages and transitions
- Graceful Orchestration: Integration with Grace Fields Master Orchestrator for workflow management
- Graceful Degradation: Error handling and fallback mechanisms are implemented

### Notion Database Integrity Rules
- Schema Consistency: API validates data against models before storage
- Audit Trail: Comprehensive logging of all operations

### Integration Security Rules
- API Key Management: Uses environment variables for all credentials
- Rate Limiting: Implemented for all endpoints

## Next Steps

1. Add authentication middleware
2. Implement the Wellness Service Booking Workflow
3. Add Redis caching layer
4. Configure CORS for Softr domains
5. Implement webhook functionality for real-time updates

## License

Proprietary - The Higher Self Network
