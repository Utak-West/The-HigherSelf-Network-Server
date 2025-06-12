#!/bin/bash
# The HigherSelf Network Server - Remote Deployment Script
# Deploys the application to an Ubuntu VM while maintaining Notion as the central hub

set -e

# Configuration
VM_USER=${VM_USER:-"ubuntu"}
VM_HOST=${VM_HOST:-"your-vm-ip-or-hostname"}
VM_SSH_KEY=${VM_SSH_KEY:-"~/.ssh/id_rsa"}
DEPLOY_DIR=${DEPLOY_DIR:-"/home/ubuntu/higherself-network-server"}
GITHUB_REPO="Utak-West/The-HigherSelf-Network-Server"

# Log to both console and file
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> deployment-log.txt
}

log "Starting deployment to VM: $VM_HOST"
log "IMPORTANT: Ensuring Notion remains the central hub for all data and workflows"

# Check if SSH key exists
if [ ! -f "$VM_SSH_KEY" ]; then
  log "ERROR: SSH key not found at $VM_SSH_KEY"
  exit 1
fi

# Create remote deployment script
cat > remote-deploy.sh << 'EOF'
#!/bin/bash
set -e

DEPLOY_DIR="$1"
GITHUB_REPO="$2"

# Log to both console and file
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$DEPLOY_DIR/deployment-log.txt"
}

log "Starting deployment on VM"

# Ensure directory exists
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# Backup .env file if it exists
if [ -f ".env" ]; then
  log "Backing up .env file"
  cp .env .env.backup
fi

# Pull latest code
if [ -d .git ]; then
  log "Updating existing repository"
  git pull origin main
else
  log "Cloning repository"
  git clone "https://github.com/$GITHUB_REPO.git" .
fi

# Restore .env file
if [ -f ".env.backup" ]; then
  log "Restoring .env file"
  cp .env.backup .env
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  log "Installing Docker"
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker $USER
  # Need to reload groups
  newgrp docker
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
  log "Installing Docker Compose"
  sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
fi

# Build and start containers
log "Building and starting Docker containers"
docker-compose down
docker-compose build
docker-compose up -d

# Check if deployment was successful
log "Checking deployment status"
if docker-compose ps | grep -q "Up"; then
  log "Deployment successful!"

  # Update Notion about successful deployment if possible
  if [ -f ".env" ] && grep -q "NOTION_API_TOKEN" .env; then
    log "Updating Notion about successful deployment"
    # This would be an actual API call to Notion in a production environment
  fi
else
  log "Deployment failed!"
  docker-compose logs
  exit 1
fi

log "Deployment completed!"
EOF

# Make remote script executable
chmod +x remote-deploy.sh

# Copy remote script to VM
log "Copying deployment script to VM"
scp -i "$VM_SSH_KEY" remote-deploy.sh "$VM_USER@$VM_HOST:/tmp/remote-deploy.sh"

# Execute remote script
log "Executing deployment script on VM"
ssh -i "$VM_SSH_KEY" "$VM_USER@$VM_HOST" "bash /tmp/remote-deploy.sh $DEPLOY_DIR $GITHUB_REPO"

# Clean up
rm remote-deploy.sh

log "Deployment to VM completed!"
exit 0
