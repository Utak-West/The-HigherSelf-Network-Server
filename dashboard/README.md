# HigherSelf Gaming Operations Dashboard

A next-generation operations dashboard that transforms traditional business metrics into an immersive gaming experience. This system visualizes The HigherSelf Network Server's operations through interactive 3D environments, agent character representations, and real-time performance analytics with gaming aesthetics.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    GAMING OPERATIONS COMMAND CENTER             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   AGENT     │  │   SYSTEM    │  │  BUSINESS   │             │
│  │ CHARACTERS  │  │  TOPOLOGY   │  │  METRICS    │             │
│  │             │  │             │  │             │             │
│  │ ◉ Grace     │  │ ╭─────────╮ │  │ Revenue: ▲  │             │
│  │ ◉ Nyra      │  │ │ MongoDB │ │  │ Users: ▲▲   │             │
│  │ ◉ Booking   │  │ │ Redis   │ │  │ Tasks: ▲▲▲  │             │
│  │ ◉ RAG       │  │ │ FastAPI │ │  │             │             │
│  │ ◉ Video     │  │ ╰─────────╯ │  │ XP: 15,420  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

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

## Features

### Multi-Tenant Operations Dashboard
- **A.M. Consulting**: Conflict management, practitioner scheduling, revenue tracking
- **The 7 Space**: Exhibitions, events, wellness programs, visitor analytics
- **HigherSelf Network**: Community management, platform usage, network metrics

### Gaming-Style Visualizations
- Agent character representations with real-time performance metrics
- 3D network topology visualization
- Achievement and XP systems
- Interactive gaming UI elements

### Technical Features
- Real-time updates via Socket.IO
- Multi-tenant architecture with tenant isolation
- Role-based access control
- Responsive design with dark/light mode support
- Integration with existing HigherSelf Network services

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
