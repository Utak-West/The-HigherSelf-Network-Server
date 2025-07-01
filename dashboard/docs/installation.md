# Master Business Operations Dashboard - Installation and Deployment Guide

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Local Development Setup](#local-development-setup)
4. [Database Setup](#database-setup)
5. [Environment Configuration](#environment-configuration)
6. [Running the Application](#running-the-application)
7. [Production Deployment](#production-deployment)
8. [Docker Deployment](#docker-deployment)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Monitoring and Maintenance](#monitoring-and-maintenance)
11. [Troubleshooting](#troubleshooting)
12. [Security Considerations](#security-considerations)

## Introduction

The Master Business Operations Dashboard is a comprehensive multi-tenant dashboard application designed to manage and monitor operations across three business entities: A.M. Consulting, The 7 Space, and HigherSelf Network. This guide provides detailed instructions for installing, configuring, and deploying the application in various environments.

## System Requirements

### Minimum Hardware Requirements

- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB available space
- **Network**: Broadband internet connection

### Software Requirements

- **Node.js**: v20.x or later
- **MySQL**: v8.0 or later
- **Redis**: v6.x or later
- **Docker**: v20.x or later (for containerized deployment)
- **Docker Compose**: v2.x or later
- **Git**: v2.x or later

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/master-dashboard.git
cd master-dashboard
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Set Up Environment Variables

Copy the example environment file and modify it with your local configuration:

```bash
cp .env.example .env
```

Edit the `.env` file with your local database credentials and other configuration options.

## Database Setup

### 1. Create MySQL Database

```bash
mysql -u root -p
```

```sql
CREATE DATABASE master_dashboard;
CREATE USER 'dashboard_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON master_dashboard.* TO 'dashboard_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 2. Run Database Migrations

```bash
npm run db:migrate
```

### 3. Seed Initial Data (Optional)

```bash
npm run db:seed
```

## Environment Configuration

The application uses environment variables for configuration. Below are the key variables that need to be set:

### Core Configuration

```
# Application
NODE_ENV=development
PORT=3000
API_URL=http://localhost:3000
FRONTEND_URL=http://localhost:5173
LOG_LEVEL=info

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=dashboard_user
DB_PASSWORD=your_secure_password
DB_NAME=master_dashboard

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Authentication
JWT_SECRET=your_jwt_secret_key
JWT_EXPIRATION=24h
REFRESH_TOKEN_EXPIRATION=7d
```

### Integration Configuration

```
# A.M. Consulting Integration
AM_CONSULTING_API_URL=https://api.amconsulting.example.com
AM_CONSULTING_API_KEY=your_am_consulting_api_key

# The 7 Space Integration
SEVEN_SPACE_API_URL=https://api.7space.example.com
SEVEN_SPACE_API_KEY=your_seven_space_api_key

# HigherSelf Network Integration
HIGHERSELF_API_URL=https://api.higherself.example.com
HIGHERSELF_API_KEY=your_higherself_api_key
```

## Running the Application

### Development Mode

To run the application in development mode with hot reloading:

#### Backend

```bash
npm run dev:backend
```

#### Frontend

```bash
npm run dev:frontend
```

### Production Mode

To build and run the application in production mode:

#### Build

```bash
npm run build
```

#### Start

```bash
npm start
```

## Production Deployment

### Option 1: Traditional Deployment

1. **Prepare the Server**

   Install Node.js, MySQL, and Redis on your server:

   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install -y nodejs npm mysql-server redis-server
   ```

2. **Clone and Set Up the Application**

   ```bash
   git clone https://github.com/yourusername/master-dashboard.git
   cd master-dashboard
   npm install --production
   ```

3. **Configure Environment**

   ```bash
   cp .env.example .env.production
   # Edit .env.production with your production settings
   ```

4. **Build the Application**

   ```bash
   npm run build
   ```

5. **Set Up Process Manager (PM2)**

   ```bash
   npm install -g pm2
   pm2 start ecosystem.config.js --env production
   pm2 save
   pm2 startup
   ```

### Option 2: Using Docker (Recommended)

See the [Docker Deployment](#docker-deployment) section below.

## Docker Deployment

### 1. Build Docker Images

```bash
docker-compose build
```

### 2. Configure Environment

Create a `.env.production` file with your production environment variables.

### 3. Start the Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Verify Deployment

```bash
docker-compose ps
```

### 5. View Logs

```bash
docker-compose logs -f
```

## CI/CD Pipeline

The repository includes a GitHub Actions workflow for continuous integration and deployment. The workflow performs the following steps:

1. **Test**: Runs linting and automated tests
2. **Build**: Builds the frontend and backend applications
3. **Deploy to Staging**: Deploys to the staging environment when changes are pushed to the `develop` branch
4. **Deploy to Production**: Deploys to the production environment when changes are pushed to the `main` branch

### Required Secrets

To use the CI/CD pipeline, you need to set up the following secrets in your GitHub repository:

- `DOCKER_HUB_USERNAME`: Your Docker Hub username
- `DOCKER_HUB_TOKEN`: Your Docker Hub access token
- `STAGING_HOST`: Hostname of your staging server
- `STAGING_USERNAME`: SSH username for the staging server
- `STAGING_SSH_KEY`: SSH private key for the staging server
- `PRODUCTION_HOST`: Hostname of your production server
- `PRODUCTION_USERNAME`: SSH username for the production server
- `PRODUCTION_SSH_KEY`: SSH private key for the production server

## Monitoring and Maintenance

### Health Checks

The application provides health check endpoints to monitor system status:

- `/api/monitoring/health`: Returns the current health status of the system
- `/api/monitoring/alerts`: Returns recent system alerts

### Database Backups

Set up automated database backups:

```bash
# Add to crontab
0 2 * * * /path/to/backup-script.sh
```

Example backup script (`backup-script.sh`):

```bash
#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/path/to/backups"
mysqldump -u dashboard_user -p'your_secure_password' master_dashboard > "$BACKUP_DIR/master_dashboard_$TIMESTAMP.sql"
gzip "$BACKUP_DIR/master_dashboard_$TIMESTAMP.sql"
```

### Log Rotation

Configure log rotation to manage log files:

```
/path/to/master-dashboard/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
}
```

## Troubleshooting

### Common Issues

#### Database Connection Errors

- Verify database credentials in the `.env` file
- Check that the MySQL service is running
- Ensure the database user has the correct permissions

```bash
# Check MySQL status
sudo systemctl status mysql

# Verify connection
mysql -u dashboard_user -p'your_secure_password' -e "SHOW DATABASES;"
```

#### Redis Connection Issues

- Verify Redis is running
- Check Redis connection settings in the `.env` file

```bash
# Check Redis status
sudo systemctl status redis

# Test Redis connection
redis-cli ping
```

#### Application Startup Failures

- Check the application logs for errors
- Verify all required environment variables are set
- Ensure the correct Node.js version is installed

```bash
# View logs
tail -f logs/app.log

# Check Node.js version
node -v
```

## Security Considerations

### 1. API Keys and Secrets

- Never commit API keys or secrets to the repository
- Use environment variables for all sensitive information
- Rotate API keys and secrets regularly

### 2. Database Security

- Use strong passwords for database users
- Limit database user permissions to only what is necessary
- Enable SSL for database connections in production

### 3. Network Security

- Use HTTPS for all production traffic
- Configure proper CORS settings
- Implement rate limiting for API endpoints

### 4. Authentication and Authorization

- Use secure JWT practices
- Implement proper role-based access control
- Set appropriate token expiration times

### 5. Regular Updates

- Keep all dependencies updated
- Apply security patches promptly
- Conduct regular security audits

