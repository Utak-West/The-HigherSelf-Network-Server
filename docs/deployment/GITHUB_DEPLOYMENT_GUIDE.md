# The HigherSelf Network Server - GitHub Deployment Guide

This guide explains how to use the GitHub Actions workflows to automatically deploy The HigherSelf Network Server to your Ubuntu virtual machine. Following this setup ensures that **Notion remains the central hub for all data and workflows** throughout the deployment process.

## Overview

The deployment system includes:

1. **GitHub Actions workflows** that automatically build, test, and deploy the application
2. **Docker containers** that package the application and all dependencies
3. **Notion integration** to track deployments and maintain Notion as the central hub

## Setup Instructions

### Step 1: Configure GitHub Secrets

Add the following secrets to your GitHub repository (Settings > Secrets and variables > Actions):

```
# VM Deployment Secrets
VM_HOST             # Your Ubuntu VM's IP address or hostname
VM_USER             # SSH username for your VM (typically "ubuntu")
VM_SSH_KEY          # The private SSH key for connecting to your VM

# Notion Integration Secrets (Central Hub)
NOTION_API_TOKEN    # Your Notion API token
NOTION_DEPLOYMENT_DATABASE_ID  # Notion database ID for tracking deployments
NOTION_TEST_RESULTS_DATABASE_ID  # Notion database ID for test results

# For Testing
TEST_NOTION_API_TOKEN  # Can be the same as your main token or a test account
TEST_NOTION_CLIENTS_DATABASE_ID
TEST_NOTION_PRODUCTS_DATABASE_ID
TEST_NOTION_ORDERS_DATABASE_ID
TEST_NOTION_APPOINTMENTS_DATABASE_ID
TEST_NOTION_BOOKINGS_DATABASE_ID
TEST_NOTION_FEEDBACK_DATABASE_ID
TEST_NOTION_TUTORING_DATABASE_ID
TEST_NOTION_WORKFLOW_DATABASE_ID
```

### Step 2: Set Up SSH Access to Your VM

1. Generate an SSH key pair if you don't already have one:
   ```bash
   ssh-keygen -t rsa -b 4096 -C "github-deploy"
   ```

2. Copy the public key to your VM:
   ```bash
   ssh-copy-id -i ~/.ssh/id_rsa.pub ubuntu@your-vm-ip
   ```

3. Add the private key as a GitHub secret (VM_SSH_KEY)

### Step 3: Initial VM Setup

Connect to your VM and prepare it for deployment:

```bash
# Connect to your VM
ssh ubuntu@your-vm-ip

# Create the deployment directory
mkdir -p ~/higherself-network-server

# Make sure Docker and Docker Compose are installed
# (The deployment script will install these if needed)
```

### Step 4: Trigger Your First Deployment

You can trigger the deployment in several ways:

1. **Automatic**: Push changes to the `main` branch
2. **Manual**: Go to the "Actions" tab in your GitHub repository, select the "Docker Build and Deploy" workflow, and click "Run workflow"

## How It Works

### Docker Build and Deploy Workflow

This workflow:
1. Builds a Docker image of The HigherSelf Network Server
2. Runs security scans on the image
3. Pushes the image to GitHub Container Registry
4. Updates Notion with the deployment status

### Notion Integration Tests

This workflow:
1. Tests the connection to Notion API
2. Verifies that all services can properly synchronize with Notion
3. Updates Notion with the test results

### VM Deployment

The deployment process:
1. Connects to your VM via SSH
2. Pulls the latest code from GitHub
3. Preserves your environment variables and configurations
4. Builds and starts the Docker containers
5. Verifies the deployment was successful
6. Updates Notion with the final status

## Maintaining Notion as the Central Hub

The deployment system maintains Notion as the central data and workflow hub by:

1. Updating deployment status in your Notion database
2. Ensuring all integrated services (TypeForm, WooCommerce, Acuity, etc.) sync their data with Notion
3. Preserving Notion database IDs in your environment configuration
4. Running integration tests to verify Notion connectivity

## Troubleshooting

### Deployment Failures

If a deployment fails:
1. Check the GitHub Actions logs for error messages
2. Verify your VM is accessible via SSH
3. Check if Docker is running properly on your VM
4. Ensure your Notion API token is valid

### Notion Integration Issues

If you have issues with Notion integration:
1. Check your Notion API token
2. Verify the database IDs in your environment configuration
3. Run the integration tests manually to diagnose issues

## Advanced Configuration

### Custom Deployment Settings

You can customize the deployment process by modifying:
1. The `.github/workflows/docker-build-deploy.yml` file for GitHub Actions configuration
2. The `deployment/deploy-to-vm.sh` script for VM deployment settings

### Additional Notion Integrations

To add more Notion integrations:
1. Add new database IDs to your environment configuration
2. Update the service integrations to sync with these databases
3. Modify the integration tests to verify the new connections

Remember: Notion serves as the central hub for all data and workflows in The HigherSelf Network ecosystem.
