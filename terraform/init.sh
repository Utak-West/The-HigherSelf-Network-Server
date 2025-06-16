#!/bin/bash

# HigherSelf Network Server - Terraform Initialization Script
# Enterprise-grade infrastructure deployment automation

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$SCRIPT_DIR"

# Default environment
ENVIRONMENT="${1:-development}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${NC}"
    echo "Usage: $0 [development|staging|production]"
    exit 1
fi

echo -e "${BLUE}🚀 HigherSelf Network Server - Terraform Initialization${NC}"
echo -e "${BLUE}Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check Terraform
if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed or not in PATH"
    echo "Please install Terraform: https://www.terraform.io/downloads.html"
    exit 1
fi
print_status "Terraform found: $(terraform version | head -n1)"

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    echo "Please start Docker daemon"
    exit 1
fi
print_status "Docker found and running"

# Check if we're in the right directory
if [[ ! -f "$TERRAFORM_DIR/main.tf" ]]; then
    print_error "main.tf not found in $TERRAFORM_DIR"
    echo "Please run this script from the terraform directory"
    exit 1
fi

# Check environment file
ENV_FILE="$TERRAFORM_DIR/environments/$ENVIRONMENT.tfvars"
if [[ ! -f "$ENV_FILE" ]]; then
    print_error "Environment file not found: $ENV_FILE"
    exit 1
fi
print_status "Environment configuration found: $ENV_FILE"

# Change to terraform directory
cd "$TERRAFORM_DIR"

# Initialize Terraform
echo ""
echo -e "${BLUE}Initializing Terraform...${NC}"
if terraform init; then
    print_status "Terraform initialized successfully"
else
    print_error "Terraform initialization failed"
    exit 1
fi

# Create or select workspace
echo ""
echo -e "${BLUE}Setting up Terraform workspace...${NC}"
if terraform workspace list | grep -q "$ENVIRONMENT"; then
    terraform workspace select "$ENVIRONMENT"
    print_status "Selected existing workspace: $ENVIRONMENT"
else
    terraform workspace new "$ENVIRONMENT"
    print_status "Created new workspace: $ENVIRONMENT"
fi

# Validate configuration
echo ""
echo -e "${BLUE}Validating Terraform configuration...${NC}"
if terraform validate; then
    print_status "Configuration is valid"
else
    print_error "Configuration validation failed"
    exit 1
fi

# Plan deployment
echo ""
echo -e "${BLUE}Planning deployment...${NC}"
if terraform plan -var-file="$ENV_FILE" -out="$ENVIRONMENT.tfplan"; then
    print_status "Deployment plan created successfully"
else
    print_error "Deployment planning failed"
    exit 1
fi

# Show next steps
echo ""
echo -e "${GREEN}🎉 Terraform initialization completed successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Review the deployment plan:"
echo -e "   ${YELLOW}terraform show $ENVIRONMENT.tfplan${NC}"
echo ""
echo "2. Apply the configuration:"
echo -e "   ${YELLOW}terraform apply $ENVIRONMENT.tfplan${NC}"
echo ""
echo "3. Or run the deployment script:"
echo -e "   ${YELLOW}./deploy.sh $ENVIRONMENT${NC}"
echo ""

# Environment-specific instructions
case $ENVIRONMENT in
    "development")
        echo -e "${BLUE}Development Environment Notes:${NC}"
        echo "• Services will be available on localhost"
        echo "• Default passwords are used (change for other environments)"
        echo "• Monitoring is enabled for testing"
        ;;
    "staging")
        echo -e "${BLUE}Staging Environment Notes:${NC}"
        echo "• SSL is enabled - ensure certificates are in place"
        echo "• Production-like configuration for testing"
        echo "• Auto-scaling is enabled for testing"
        ;;
    "production")
        echo -e "${YELLOW}Production Environment Warnings:${NC}"
        print_warning "Change all default passwords before deployment"
        print_warning "Configure SSL certificates"
        print_warning "Review and restrict allowed_ips"
        print_warning "Set up monitoring alerts"
        print_warning "Configure backup storage"
        ;;
esac

echo ""
echo -e "${BLUE}Service Endpoints (after deployment):${NC}"
echo "• Main Application: http://localhost:8000"
echo "• Health Check: http://localhost:8000/health"
echo "• Prometheus: http://localhost:9090"
echo "• Grafana: http://localhost:3000 (admin/admin)"
echo "• Consul: http://localhost:8500"
echo ""

# Check for environment variables
echo -e "${BLUE}Environment Variables Check:${NC}"
ENV_VARS=("TF_VAR_notion_token" "TF_VAR_openai_api_key" "TF_VAR_huggingface_token")

for var in "${ENV_VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
        print_warning "$var is not set"
    else
        print_status "$var is configured"
    fi
done

if [[ "$ENVIRONMENT" == "production" ]]; then
    PROD_VARS=("TF_VAR_mongodb_root_password" "TF_VAR_mongodb_app_password" "TF_VAR_redis_password" "TF_VAR_grafana_admin_password")
    
    for var in "${PROD_VARS[@]}"; do
        if [[ -z "${!var}" ]]; then
            print_warning "$var should be set for production"
        else
            print_status "$var is configured"
        fi
    done
fi

echo ""
echo -e "${GREEN}Ready to deploy HigherSelf Network Server!${NC}"
