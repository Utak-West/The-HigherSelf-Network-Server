# 🏗️ MetroPower Dashboard - Tucker Branch

<div align="center">
  <img src="frontend/assets/images/metropower-logo.png" alt="MetroPower Logo" width="200"/>

  **Professional Workforce Management Dashboard**

  *Streamline your electrical construction operations with real-time employee tracking, project assignments, and comprehensive reporting tools.*

  [![Vercel](https://img.shields.io/badge/Deploy-Vercel-black?logo=vercel)](https://vercel.com)
  [![Node.js](https://img.shields.io/badge/Node.js-18+-green?logo=node.js)](https://nodejs.org)
  [![License](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)
</div>

---

## 🎯 Overview

MetroPower Dashboard is a comprehensive workforce management system designed specifically for MetroPower's Tucker Branch operations. Built to handle the complexities of electrical construction workforce management, it provides real-time visibility into employee assignments, project tracking, and operational oversight.

### ✨ Key Features

- **🔄 Real-time Employee Tracking** - Live updates on employee status and assignments
- **📋 Project-based Workforce Allocation** - Organize teams by projects and locations
- **🖱️ Interactive Drag-and-Drop Interface** - Intuitive assignment management
- **📊 Comprehensive Reporting** - Export capabilities (Excel, CSV, PDF)
- **🔐 Role-based Access Control** - Secure authentication and authorization
- **📱 Responsive Design** - Works seamlessly on desktop and mobile devices
- **⚡ Real-time Notifications** - Instant updates via WebSocket connections
- **📈 Analytics Dashboard** - Workforce insights and performance metrics

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ ([Download](https://nodejs.org))
- **npm** 8+ (comes with Node.js)
- **Git** ([Download](https://git-scm.com))

### 🛠️ Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git
   cd MetroPower-Dashboard
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

5. **Access the application**
   - Dashboard: `http://localhost:3001`
   - API Docs: `http://localhost:3001/api-docs`
   - Health Check: `http://localhost:3001/health`

### 🔑 Default Login Credentials

- **Email**: `Antoine.Harrell@metropower.com`
- **Password**: `password`

## 🏗️ Architecture

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) | User interface and interactions |
| **Backend** | Node.js, Express.js | API server and business logic |
| **Database** | PostgreSQL / In-memory | Data persistence |
| **Real-time** | Socket.IO | Live updates and notifications |
| **Authentication** | JWT | Secure user sessions |
| **File Processing** | ExcelJS, PDFKit | Document generation |
| **Deployment** | Vercel | Cloud hosting platform |

### Project Structure

```
MetroPower-Dashboard/
├── 📁 api/                    # Vercel serverless functions
│   ├── index.js              # Main API handler
│   └── debug.js              # Debug endpoint
├── 📁 backend/               # Express.js backend
│   ├── server.js             # Main server file
│   ├── src/                  # Source code
│   │   ├── routes/           # API routes
│   │   ├── middleware/       # Custom middleware
│   │   ├── config/           # Configuration files
│   │   └── utils/            # Utility functions
│   └── package.json          # Backend dependencies
├── 📁 frontend/              # Static frontend files
│   ├── index.html            # Main HTML file
│   ├── css/                  # Stylesheets
│   ├── js/                   # JavaScript files
│   └── assets/               # Images, icons, etc.
├── 📁 scripts/               # Build and utility scripts
├── 📁 uploads/               # File upload directory
├── 📁 exports/               # Export files directory
├── vercel.json               # Vercel configuration
├── package.json              # Root package.json
└── .env.example              # Environment variables template
```

## 🚀 Deployment

### Vercel Deployment (Recommended)

This application is optimized for Vercel deployment with serverless functions.

#### Quick Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Utak-West/The-HigherSelf-Network-Server&project-name=metropower-dashboard&repository-name=metropower-dashboard&root-directory=MetroPower-Dashboard)

#### Manual Deployment

1. **Connect to Vercel**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Import your GitHub repository
   - Set root directory to `MetroPower-Dashboard`

2. **Configure Environment Variables**
   ```env
   NODE_ENV=production
   JWT_SECRET=your-super-secret-jwt-key
   APP_NAME=MetroPower Dashboard
   COMPANY_NAME=MetroPower
   BRANCH_NAME=Tucker Branch
   CORS_ORIGIN=https://your-app.vercel.app
   ```

3. **Deploy**
   - Click "Deploy" and wait for completion
   - Your app will be available at `https://your-app.vercel.app`

For detailed deployment instructions, see [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)

## 📚 Documentation

- **[Deployment Guide](VERCEL_DEPLOYMENT.md)** - Complete Vercel deployment instructions
- **[Deployment Checklist](DEPLOYMENT_CHECKLIST.md)** - Step-by-step deployment checklist
- **[Quick Start Guide](VERCEL_READY.md)** - Fast deployment summary

## 🧪 Testing

### Run Configuration Tests
```bash
node scripts/test-vercel-config.js
```

### Build for Production
```bash
npm run vercel-build
```

### Local Testing
```bash
npm test
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ENV` | Environment mode | `development` |
| `PORT` | Server port | `3001` |
| `JWT_SECRET` | JWT signing secret | Required |
| `DATABASE_URL` | PostgreSQL connection string | Optional |
| `CORS_ORIGIN` | Allowed CORS origins | `http://localhost:3000` |

See [.env.example](.env.example) for complete configuration options.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software owned by **The HigherSelf Network**. All rights reserved.

## 🆘 Support

- **Documentation**: Check the `/docs` directory
- **Issues**: Create a GitHub issue
- **Email**: Contact the development team

---

<div align="center">
  <p><strong>Built with ❤️ by The HigherSelf Network</strong></p>
  <p>Empowering MetroPower's workforce management operations</p>
</div>
