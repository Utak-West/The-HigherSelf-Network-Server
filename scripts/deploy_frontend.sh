#!/bin/bash
# Deploy the frontend to a web server

# Configuration
FRONTEND_DIR="frontend"
DEPLOY_DIR="/var/www/agent-portal"
BACKUP_DIR="/var/www/backups/agent-portal"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  The HigherSelf Network Agent Portal    ${NC}"
echo -e "${GREEN}  Frontend Deployment Script             ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}Warning: Not running as root. You may need sudo privileges to deploy to $DEPLOY_DIR${NC}"
fi

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
  echo -e "${RED}Error: Frontend directory '$FRONTEND_DIR' not found${NC}"
  exit 1
fi

# Create deploy directory if it doesn't exist
if [ ! -d "$DEPLOY_DIR" ]; then
  echo -e "Creating deployment directory: $DEPLOY_DIR"
  mkdir -p "$DEPLOY_DIR"
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to create deployment directory${NC}"
    exit 1
  fi
fi

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
  echo -e "Creating backup directory: $BACKUP_DIR"
  mkdir -p "$BACKUP_DIR"
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to create backup directory${NC}"
    exit 1
  fi
fi

# Backup existing deployment if it exists
if [ -d "$DEPLOY_DIR" ] && [ "$(ls -A $DEPLOY_DIR)" ]; then
  echo -e "Backing up existing deployment to $BACKUP_DIR/backup_$TIMESTAMP"
  mkdir -p "$BACKUP_DIR/backup_$TIMESTAMP"
  cp -r "$DEPLOY_DIR"/* "$BACKUP_DIR/backup_$TIMESTAMP/"
  if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Backup may have failed${NC}"
  else
    echo -e "${GREEN}Backup completed successfully${NC}"
  fi
fi

# Deploy the frontend
echo -e "Deploying frontend to $DEPLOY_DIR"
cp -r "$FRONTEND_DIR"/* "$DEPLOY_DIR/"
if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Deployment failed${NC}"
  exit 1
fi

# Set permissions
echo -e "Setting permissions"
chmod -R 755 "$DEPLOY_DIR"
if [ $? -ne 0 ]; then
  echo -e "${YELLOW}Warning: Failed to set permissions${NC}"
fi

# Update API URL if provided
if [ ! -z "$1" ]; then
  API_URL=$1
  echo -e "Updating API URL to: $API_URL"
  sed -i "s|const API_BASE_URL = '.*'|const API_BASE_URL = '$API_URL'|g" "$DEPLOY_DIR/app.js"
  if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Failed to update API URL${NC}"
  fi
fi

# Update Notion URL if provided
if [ ! -z "$2" ]; then
  NOTION_URL=$2
  echo -e "Updating Notion Dashboard URL to: $NOTION_URL"
  sed -i "s|const NOTION_DASHBOARD_URL = '.*'|const NOTION_DASHBOARD_URL = '$NOTION_URL'|g" "$DEPLOY_DIR/app.js"
  if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Failed to update Notion Dashboard URL${NC}"
  fi
fi

# Print success message
echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  Deployment Completed Successfully!     ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "The Agent Portal has been deployed to: ${GREEN}$DEPLOY_DIR${NC}"
echo -e "You can access it at: ${GREEN}http://your-server/agent-portal/${NC}"
echo ""
echo -e "If you need to update the API URL, run:"
echo -e "  ${YELLOW}$0 http://your-api-url/api/v1${NC}"
echo ""
echo -e "If you need to update both API URL and Notion URL, run:"
echo -e "  ${YELLOW}$0 http://your-api-url/api/v1 https://notion.so/your-database${NC}"
echo ""

exit 0
