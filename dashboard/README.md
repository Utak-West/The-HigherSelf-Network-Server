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

## Gaming Features

### Agent Command Center

Transform your AI agents into gaming characters with real-time performance visualization:

- **Character Progression**: Each agent gains XP and levels based on task completion
- **Performance Metrics**: Real-time success rates, response times, and efficiency scores
- **Achievement System**: Unlock badges and milestones for exceptional performance
- **Status Indicators**: Live activity feeds with gaming-style status effects

### 3D Network Topology

Immersive visualization of your infrastructure:

```
    ╭─────────╮     ╭─────────╮     ╭─────────╮
    │ MongoDB │────▶│ FastAPI │────▶│ React   │
    │ Cluster │     │ Server  │     │ Gaming  │
    ╰─────────╯     ╰─────────╯     ╰─────────╯
         ▲               ▲               ▲
         │               │               │
    ╭─────────╮     ╭─────────╮     ╭─────────╮
    │  Redis  │     │ Socket  │     │ Three.js│
    │  Cache  │     │   IO    │     │ Engine  │
    ╰─────────╯     ╰─────────╯     ╰─────────╯
```

### Multi-Tenant Gaming Environments

Each business entity operates as a distinct gaming realm:

- **A.M. Consulting Realm**: Conflict resolution missions, practitioner guilds
- **The 7 Space Arena**: Event management campaigns, visitor engagement quests
- **HigherSelf Network Hub**: Community building adventures, platform optimization challenges

### Real-Time Gaming Mechanics

- **Live Leaderboards**: Agent performance rankings with competitive elements
- **Mission Control**: Task assignment with quest-like interfaces
- **Resource Management**: System monitoring with RPG-style resource bars
- **Team Coordination**: Multi-agent collaboration with guild mechanics

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
