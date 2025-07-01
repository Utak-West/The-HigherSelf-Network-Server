# Master Business Operations Dashboard

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A comprehensive multi-tenant dashboard application designed to manage and monitor operations across three business entities: A.M. Consulting, The 7 Space, and HigherSelf Network.

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Development](#-development)
- [Deployment](#-deployment)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

- **Multi-tenant Architecture**: Manage multiple business entities from a single dashboard
- **Real-time Metrics**: Monitor key performance indicators and business metrics in real-time
- **Business Integrations**:
  - A.M. Consulting: Conflict management, practitioner scheduling, and revenue tracking
  - The 7 Space: Exhibitions, events, wellness programs, and visitor analytics
  - HigherSelf Network: Community management, platform usage, and network metrics
- **User Management**: Role-based access control with customizable permissions
- **System Monitoring**: Comprehensive health checks and performance monitoring
- **Responsive Design**: Fully responsive interface that works on desktop, tablet, and mobile devices
- **Dark/Light Mode**: Support for both dark and light themes

## 🏗 Architecture

The Master Business Operations Dashboard is built on a modern, scalable architecture:

- **Frontend**: React-based SPA with responsive design and real-time updates
- **Backend**: Node.js/Express RESTful API with comprehensive business logic
- **Database**: Multi-tenant MySQL database with tenant isolation
- **Caching**: Redis for high-performance caching and session management
- **Containerization**: Docker and Docker Compose for consistent deployment
- **CI/CD**: GitHub Actions for automated testing and deployment

### System Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  React Frontend │────▶│  Express API    │────▶│  MySQL Database │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Redis Cache    │     │  Integrations   │     │  Monitoring     │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 🛠 Tech Stack

### Frontend
- **Framework**: React 18
- **State Management**: Redux Toolkit
- **UI Library**: Material-UI
- **Charts**: Chart.js / D3.js
- **API Client**: Axios
- **Build Tool**: Vite

### Backend
- **Runtime**: Node.js
- **Framework**: Express.js
- **Authentication**: JWT
- **Validation**: Joi
- **Logging**: Winston
- **Testing**: Jest

### Database
- **Primary Database**: MySQL 8
- **Caching**: Redis 6
- **ORM**: Custom database utility

### DevOps
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: Custom monitoring service

## 🚀 Getting Started

### Prerequisites

- Node.js (v20.x or later)
- MySQL (v8.0 or later)
- Redis (v6.x or later)
- Docker & Docker Compose (for containerized deployment)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/master-dashboard.git
   cd master-dashboard
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Set up the database:
   ```bash
   npm run db:migrate
   npm run db:seed  # Optional: Add sample data
   ```

5. Start the development server:
   ```bash
   npm run dev
   ```

6. Open your browser and navigate to `http://localhost:5173`

## 💻 Development

### Project Structure

```
master-dashboard/
├── .github/            # GitHub Actions workflows
├── backend/            # Backend API code
│   ├── config/         # Configuration files
│   ├── middleware/     # Express middleware
│   ├── routes/         # API routes
│   ├── services/       # Business logic
│   └── server.js       # Main server file
├── database/           # Database migrations and seeds
├── docker/             # Docker configuration files
├── docs/               # Documentation
├── frontend/           # React frontend code
│   ├── public/         # Static assets
│   ├── src/            # Source code
│   │   ├── components/ # React components
│   │   ├── contexts/   # React contexts
│   │   ├── hooks/      # Custom hooks
│   │   ├── lib/        # Utility functions
│   │   ├── pages/      # Page components
│   │   └── App.jsx     # Main App component
│   └── index.html      # HTML template
├── scripts/            # Utility scripts
├── .env.example        # Example environment variables
├── docker-compose.yml  # Docker Compose configuration
├── package.json        # Project dependencies
└── README.md           # This file
```

### Available Scripts

- `npm run dev` - Start the development server
- `npm run build` - Build the production version
- `npm start` - Start the production server
- `npm test` - Run tests
- `npm run lint` - Run linting
- `npm run db:migrate` - Run database migrations
- `npm run db:seed` - Seed the database with sample data

## 🌐 Deployment

### Using Docker (Recommended)

1. Build the Docker images:
   ```bash
   docker-compose build
   ```

2. Start the services:
   ```bash
   docker-compose up -d
   ```

3. Access the dashboard at `http://localhost:3000`

### Traditional Deployment

1. Build the frontend:
   ```bash
   npm run build:frontend
   ```

2. Build the backend:
   ```bash
   npm run build:backend
   ```

3. Start the server:
   ```bash
   npm start
   ```

### CI/CD Pipeline

The repository includes GitHub Actions workflows for continuous integration and deployment:

- **CI**: Runs on every pull request to `main` and `develop` branches
- **CD**: Deploys to staging on pushes to `develop` and to production on pushes to `main`

See [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) for details.

## 📚 Documentation

Comprehensive documentation is available in the `docs` directory:

- [Installation Guide](docs/installation.md) - Detailed installation instructions
- [API Documentation](docs/api.md) - API endpoints and usage
- [User Guide](docs/user-guide.md) - Guide for end users

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built with ❤️ by [Your Name/Organization]

