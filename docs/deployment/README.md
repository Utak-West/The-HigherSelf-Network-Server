# The HigherSelf Network Server Deployment Guide

This guide provides detailed instructions for deploying The HigherSelf Network Server, adhering to the core principle of maintaining Notion as the central hub for all operations.

There are two deployment options:
1. **Docker Deployment** - Recommended for most environments
2. **Traditional Deployment** - For environments without Docker support

## Docker Deployment

### Prerequisites for Docker Deployment

- Docker and Docker Compose installed
- Access to The HigherSelf Network Server with sudo privileges
- Notion API integration token with appropriate permissions

### Docker Deployment Steps

#### 1. Clone the Repository

```bash
# Navigate to desired location
cd /opt
sudo git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git the-higherself-network-server
cd the-higherself-network-server
```

#### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the environment file with your specific values
nano .env
```

Ensure the following variables are properly configured:
- `NOTION_API_TOKEN`: Your Notion integration API token
- `NOTION_PARENT_PAGE_ID`: ID of the parent page for database creation
- `WEBHOOK_SECRET`: Secret for securing webhook endpoints
- All other required API credentials for integrated services

#### 3. Configure SSL Certificates

Create directories for SSL certificates:

```bash
mkdir -p deployment/ssl
```

You can either:
1. Copy existing SSL certificates into this directory, or
2. Use Let's Encrypt with Certbot to generate certificates:

```bash
sudo certbot certonly --standalone -d agent-api.thehigherselfnetwork.com
sudo cp /etc/letsencrypt/live/agent-api.thehigherselfnetwork.com/fullchain.pem deployment/ssl/
sudo cp /etc/letsencrypt/live/agent-api.thehigherselfnetwork.com/privkey.pem deployment/ssl/
sudo chmod -R 755 deployment/ssl/
```

#### 4. Deploy with Docker Compose

For development:
```bash
# Start all services in development mode
./deploy.sh --env dev --build
```

For staging:
```bash
# Start all services in staging mode
./deploy.sh --env staging --build
```

For production:
```bash
# Start all services in production mode
./deploy.sh --env prod --build
```

#### 5. Verify Deployment

```bash
# Check if containers are running
docker-compose ps

# View logs for the agent container
docker-compose logs -f windsurf-agent

# Test the API
curl http://localhost:8000/health
```

## Traditional Deployment

### Prerequisites for Traditional Deployment

- Ubuntu 20.04 LTS or later
- Python 3.10+
- Nginx
- Systemd
- Access to The HigherSelf Network Server with sudo privileges
- Notion API integration token with appropriate permissions

### Traditional Deployment Steps

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system dependencies
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx
```

### 2. Application Installation

```bash
# Create application directory
sudo mkdir -p /opt/the-higherself-network-server
sudo chown -R higherself:higherself /opt/the-higherself-network-server

# Clone the repository
cd /opt/the-higherself-network-server
git clone https://github.com/the-higherself-network/The-HigherSelf-Network-Server.git .

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit the environment file with appropriate values
nano .env
```

Make sure to configure the following environment variables:
- `NOTION_API_TOKEN`: Your Notion integration API token
- `NOTION_PARENT_PAGE_ID`: ID of the parent page for database creation
- All other required API credentials for connected services

### 4. Notion Database Setup

```bash
# Activate the virtual environment
source venv/bin/activate

# Run the database setup utility
python -m tools.notion_db_setup

# Add the generated database IDs to your .env file
cat .env.notion >> .env
```

### 5. Service Configuration

```bash
# Copy the systemd service file
sudo cp deployment/windsurf-agent.service /etc/systemd/system/

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable windsurf-agent
sudo systemctl start windsurf-agent
```

### 6. Nginx Configuration

```bash
# Copy the Nginx configuration
sudo cp deployment/nginx.conf /etc/nginx/sites-available/windsurf-agent.conf

# Create symbolic link to enable the site
sudo ln -s /etc/nginx/sites-available/windsurf-agent.conf /etc/nginx/sites-enabled/

# Test the configuration
sudo nginx -t

# If the test is successful, reload Nginx
sudo systemctl reload nginx
```

### 7. SSL Certificate Setup

```bash
# Obtain SSL certificate with Let's Encrypt
sudo certbot --nginx -d agent-api.thehigherselfnetwork.com
```

### 8. Verify Deployment

Check if the service is running properly:

```bash
sudo systemctl status windsurf-agent
```

Verify the API is accessible:

```bash
curl https://agent-api.thehigherselfnetwork.com/health
```

## Monitoring and Maintenance

### Viewing Logs

```bash
# View application logs
sudo journalctl -u windsurf-agent -f

# View Nginx access logs
sudo tail -f /var/log/nginx/access.log

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Restarting Services

```bash
# Restart the application service
sudo systemctl restart windsurf-agent

# Restart Nginx
sudo systemctl restart nginx
```

### Updating the Application

```bash
# Navigate to the application directory
cd /opt/the-higherself-network-server

# Pull the latest changes
git pull

# Activate the virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Restart the service
sudo systemctl restart windsurf-agent
```

## Security Considerations

1. **API Token Security**: Ensure that the `.env` file has restricted permissions:
   ```bash
   chmod 600 /opt/the-higherself-network-server/.env
   ```

2. **Webhook Security**: All webhook endpoints are protected with the shared secret defined in the `WEBHOOK_SECRET` environment variable. Ensure this is a strong, unique value.

3. **Regular Updates**: Keep the server and all dependencies updated regularly to patch security vulnerabilities.

4. **Firewall Configuration**: Configure the server firewall to only allow necessary connections:
   ```bash
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw allow 22
   sudo ufw enable
   ```

## Docker Container Maintenance

### Viewing Logs

```bash
# View logs for a specific service
docker-compose logs -f windsurf-agent
docker-compose logs -f nginx

# View logs with timestamps
docker-compose logs -f --timestamps
```

### Updating the Application

When new code is pushed to the repository:

```bash
# Pull the latest changes
git pull

# Rebuild and restart the containers
./deploy.sh --env prod --build
```

### Managing Containers

```bash
# Restart a specific service
docker-compose restart windsurf-agent

# Stop all services
docker-compose down

# Start all services
docker-compose up -d
```

### Backup and Restore

```bash
# Backup the environment file
cp .env .env.backup.$(date +%Y%m%d)

# Backup the logs directory
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

## Important Notes

- All agents, automations, and webhook endpoints must operate exclusively on The HigherSelf Network Server
- Notion remains the central data hub for all operations
- All API tokens and sensitive credentials must be managed securely using environment variables
- Regularly backup the environment configuration file and any custom modifications
- For Docker deployments, use the provided deploy.sh script for consistent deployments
