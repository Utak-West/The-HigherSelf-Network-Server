# The HigherSelf Network Server Deployment Guide

This guide provides detailed instructions for deploying the Windsurf Agent Network on The HigherSelf Network Server, adhering to the core principle of maintaining Notion as the central hub for all operations.

## Prerequisites

- Ubuntu 20.04 LTS or later
- Python 3.10+
- Nginx
- Systemd
- Access to The HigherSelf Network Server with sudo privileges
- Notion API integration token with appropriate permissions

## Deployment Steps

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

## Important Notes

- All Windsurf agents, automations, and webhook endpoints must operate exclusively on this server
- Notion remains the central data hub for all operations
- All API tokens and sensitive credentials must be managed securely using environment variables
- Regularly backup the environment configuration file and any custom modifications
