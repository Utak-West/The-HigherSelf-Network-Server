# Docker Deployment Guide for The HigherSelf Network Server

This guide explains how to deploy the Windsurf Agent Network on The HigherSelf Network Server using Docker containers, while maintaining Notion as the central hub for all operations.

## Prerequisites

- Docker and Docker Compose installed on The HigherSelf Network Server
- Access to The HigherSelf Network Server with sudo privileges
- Notion API integration token with appropriate permissions
- Basic understanding of Docker and container technology

## Deployment Steps

### 1. Clone the Repository on The HigherSelf Network Server

```bash
# Navigate to desired location
cd /opt

# Clone the repository
sudo git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git the-higherself-network-server
cd the-higherself-network-server
```

### 2. Configure Environment Variables

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

### 3. Configure SSL Certificates

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

Update the Nginx configuration to use these certificates:

```bash
# Edit the Nginx configuration
nano deployment/nginx.conf
```

Add SSL configuration:

```nginx
server {
    listen 443 ssl;
    server_name agent-api.thehigherselfnetwork.com;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # Other SSL configuration...
    
    location / {
        proxy_pass http://windsurf-agent:8000;
        # Other proxy settings...
    }
}
```

### 4. Initialize Notion Databases

Since we need to run the database setup utility before deployment, we'll use Docker to run this step:

```bash
# Build the Docker image
docker-compose build windsurf-agent

# Run the database setup utility
docker-compose run --rm windsurf-agent python -m tools.notion_db_setup

# Add the generated database IDs to your .env file
cat .env.notion >> .env
```

### 5. Deploy with Docker Compose

```bash
# Start all services in detached mode
docker-compose up -d
```

This will start:
- The Windsurf Agent Network container
- Redis for caching (optional)
- Nginx as a reverse proxy

### 6. Verify Deployment

```bash
# Check if containers are running
docker-compose ps

# View logs for the agent container
docker-compose logs -f windsurf-agent

# Test the API
curl https://agent-api.thehigherselfnetwork.com/health
```

## Container Maintenance

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
docker-compose down
docker-compose build
docker-compose up -d
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

## Security Considerations

### 1. Environment Variables

Docker Compose uses the `.env` file for environment variables. Ensure:
- The file has restricted permissions: `chmod 600 .env`
- Never commit this file to version control
- Consider using Docker secrets for production deployments

### 2. Data Persistence

The Docker setup mounts:
- `./logs` for application logs
- `./.env` for environment variables
- Redis data is stored in a named volume

These persist across container restarts, but consider implementing backup procedures for critical data.

### 3. Network Security

The Docker Compose file creates an isolated bridge network for inter-container communication. Only Nginx exposes ports to the host network.

## Docker in Production

For production deployment on The HigherSelf Network Server:

1. **Use Docker Compose in Production Mode**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

2. **Set Up Monitoring**:
   ```bash
   # Install monitoring stack (optional)
   git clone https://github.com/stefanprodan/dockprom.git
   cd dockprom
   docker-compose up -d
   ```

3. **Container Orchestration**: For higher availability, consider:
   - Docker Swarm for simpler setups
   - Kubernetes for more complex environments

## Important Notes

- **Notion-Centric Architecture**: Despite containerization, Notion remains the central hub for all data and workflow management. The containers are simply hosting the agents that interact with Notion.

- **Server Specificity**: All Windsurf agents, automations, and webhook endpoints must operate exclusively on The HigherSelf Network Server, even when containerized.

- **Database Validation**: Regularly validate that your containers can access the Notion databases via the health check endpoint.

- **Graceful Shutdown**: The Docker containers are configured to restart automatically, but implement proper application shutdown handling in the code to ensure no data is lost during container lifecycle events.
