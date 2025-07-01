# HigherSelf Operations Dashboard

An operations dashboard that uses gaming interface elements to provide intuitive monitoring and management of The HigherSelf Network Server. The gaming metaphors make complex agent interactions and system relationships more accessible to operators.

## System Architecture

The dashboard integrates with existing infrastructure to provide operational visibility:

**Agent Monitoring Layer**
- Visualizes agent communication patterns and collaboration workflows
- Displays real-time agent status and current task assignments
- Shows inter-agent dependencies and data sharing relationships

**System Infrastructure Layer**
- Maps connections between MongoDB, Redis, FastAPI, and other components
- Provides health monitoring for all system dependencies
- Visualizes data flow and processing pipelines

**Business Operations Layer**
- Tracks task completion and workflow progress across different business entities
- Monitors resource utilization and system performance
- Provides operational metrics relevant to each business unit

## Directory Structure

```
dashboard/
├── frontend/                 # React-based dashboard frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── contexts/        # React contexts (Auth, Organization, Theme)
│   │   ├── hooks/           # Custom React hooks
│   │   ├── lib/             # Utility libraries and API clients
│   │   ├── pages/           # Page components
│   │   └── assets/          # Static assets
│   └── public/              # Public assets
├── backend/                 # Express.js backend services
│   ├── routes/              # API route handlers
│   ├── middleware/          # Express middleware
│   ├── services/            # Business logic services
│   ├── config/              # Configuration files
│   └── models/              # Data models
├── gaming-ui/               # Gaming-style UI components and templates
│   ├── components/          # Gaming UI React components
│   ├── three-js/            # 3D visualization components
│   └── templates/           # HTML templates and guides
├── shared/                  # Shared utilities and types
│   ├── types/               # TypeScript type definitions
│   ├── utils/               # Shared utility functions
│   └── constants/           # Shared constants
└── docs/                    # Documentation
```

## Operational Features

### Agent Interaction Visualization

The dashboard provides clear visibility into how agents work together:

- **Communication Flow Mapping**: Visual representation of message exchanges between agents, showing collaboration patterns and information routing
- **Workflow Coordination Display**: Shows how agents hand off tasks, share resources, and coordinate on complex multi-step processes
- **Dependency Tracking**: Identifies which agents rely on others for data, tools, or processing capabilities
- **Collaboration Patterns**: Highlights frequent agent partnerships and team formations for different types of work

### System Infrastructure Monitoring

Real-time visibility into system health and performance:

- **Component Status Tracking**: Monitors the health of MongoDB, Redis, FastAPI, and other infrastructure components
- **Data Flow Visualization**: Shows how information moves through the system, from input sources to final outputs
- **Performance Bottleneck Identification**: Highlights system components under stress or experiencing delays
- **Resource Utilization Monitoring**: Tracks CPU, memory, and network usage across the infrastructure

### Multi-Tenant Operations Management

Separate operational views for different business entities:

- **A.M. Consulting Operations**: Focuses on conflict resolution workflows, practitioner scheduling, and client management processes
- **The 7 Space Management**: Emphasizes event coordination, space utilization, and visitor experience workflows
- **HigherSelf Network Administration**: Concentrates on community management, platform operations, and network health

### Practical Interface Elements

Gaming metaphors serve specific operational purposes:

- **Agent Status Indicators**: Clear visual representation of agent availability, current tasks, and operational health
- **Task Progress Tracking**: Visual progress indicators for ongoing work, showing completion status and estimated time remaining
- **System Health Dashboard**: Infrastructure monitoring presented through intuitive visual elements that make complex system states immediately understandable
- **Workflow Management**: Task assignment and coordination interfaces that simplify complex multi-agent operations

## Integration Points

### Backend Integration
- Integrates with existing FastAPI server
- Utilizes existing MongoDB and Redis infrastructure
- Leverages existing service layer architecture
- Maintains compatibility with current API structure

### Frontend Integration
- Replaces basic HTML frontend with modern React application
- Maintains compatibility with existing API endpoints
- Provides enhanced user experience with gaming elements

## Getting Started

See individual README files in each subdirectory for specific setup instructions.

## Architecture

The dashboard follows a modular architecture that integrates seamlessly with the existing HigherSelf Network Server infrastructure while providing enhanced visualization and management capabilities.
