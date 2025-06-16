#!/bin/bash

# HigherSelf Network Server - Terraform Deployment Script
# Enterprise-grade automated deployment with validation and monitoring

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
ACTION="${2:-apply}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${NC}"
    echo "Usage: $0 [development|staging|production] [apply|destroy|plan]"
    exit 1
fi

# Validate action
if [[ ! "$ACTION" =~ ^(apply|destroy|plan)$ ]]; then
    echo -e "${RED}Error: Invalid action '$ACTION'${NC}"
    echo "Usage: $0 [development|staging|production] [apply|destroy|plan]"
    exit 1
fi

echo -e "${BLUE}🚀 HigherSelf Network Server - Terraform Deployment${NC}"
echo -e "${BLUE}Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "${BLUE}Action: ${YELLOW}$ACTION${NC}"
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

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${BLUE}Waiting for $service_name to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            print_status "$service_name is ready"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_warning "$service_name may not be ready yet (timeout after ${max_attempts} attempts)"
    return 1
}

# Pre-deployment checks
echo -e "${BLUE}Running pre-deployment checks...${NC}"

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

# Change to terraform directory
cd "$TERRAFORM_DIR"

# Check if Terraform is initialized
if [[ ! -d ".terraform" ]]; then
    print_warning "Terraform not initialized. Running initialization..."
    if ! bash "$TERRAFORM_DIR/init.sh" "$ENVIRONMENT"; then
        print_error "Terraform initialization failed"
        exit 1
    fi
fi

# Select workspace
if terraform workspace list | grep -q "$ENVIRONMENT"; then
    terraform workspace select "$ENVIRONMENT"
    print_status "Selected workspace: $ENVIRONMENT"
else
    print_error "Workspace '$ENVIRONMENT' not found. Run init.sh first."
    exit 1
fi

# Production safety check
if [[ "$ENVIRONMENT" == "production" && "$ACTION" == "apply" ]]; then
    echo -e "${YELLOW}⚠ PRODUCTION DEPLOYMENT WARNING ⚠${NC}"
    echo "You are about to deploy to PRODUCTION environment."
    echo "Please ensure:"
    echo "1. All passwords have been changed from defaults"
    echo "2. SSL certificates are properly configured"
    echo "3. IP restrictions are properly set"
    echo "4. Backup procedures are in place"
    echo "5. Monitoring alerts are configured"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
fi

# Destruction safety check
if [[ "$ACTION" == "destroy" ]]; then
    echo -e "${RED}⚠ DESTRUCTION WARNING ⚠${NC}"
    echo "You are about to DESTROY the $ENVIRONMENT environment."
    echo "This will remove all containers, volumes, and data."
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Destruction cancelled."
        exit 0
    fi
fi

# Execute Terraform action
echo ""
echo -e "${BLUE}Executing Terraform $ACTION...${NC}"

case $ACTION in
    "plan")
        if terraform plan -var-file="$ENV_FILE"; then
            print_status "Terraform plan completed successfully"
        else
            print_error "Terraform plan failed"
            exit 1
        fi
        ;;
    "apply")
        if terraform apply -var-file="$ENV_FILE" -auto-approve; then
            print_status "Terraform apply completed successfully"
        else
            print_error "Terraform apply failed"
            exit 1
        fi
        
        # Post-deployment validation
        echo ""
        echo -e "${BLUE}Running post-deployment validation...${NC}"
        
        # Wait for services to be ready
        wait_for_service "HigherSelf Network Server" "http://localhost:8000/health"
        wait_for_service "Prometheus" "http://localhost:9090/-/ready"
        wait_for_service "Grafana" "http://localhost:3000/api/health"
        wait_for_service "Consul" "http://localhost:8500/v1/status/leader"
        
        # Display service information
        echo ""
        echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
        echo ""
        echo -e "${BLUE}Service Endpoints:${NC}"
        echo "• Main Application: http://localhost:8000"
        echo "• Health Check: http://localhost:8000/health"
        echo "• API Documentation: http://localhost:8000/docs"
        echo "• Prometheus: http://localhost:9090"
        echo "• Grafana: http://localhost:3000 (admin/admin)"
        echo "• Consul: http://localhost:8500"
        echo ""
        
        # Show resource usage
        echo -e "${BLUE}Resource Usage:${NC}"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" | head -10
        echo ""
        
        # Show logs command
        echo -e "${BLUE}Useful Commands:${NC}"
        echo "• View logs: docker-compose logs -f windsurf-agent"
        echo "• Check status: docker ps"
        echo "• Monitor resources: docker stats"
        echo "• Stop services: terraform destroy -var-file=\"$ENV_FILE\""
        ;;
    "destroy")
        if terraform destroy -var-file="$ENV_FILE" -auto-approve; then
            print_status "Terraform destroy completed successfully"
            echo ""
            echo -e "${GREEN}Environment $ENVIRONMENT has been destroyed.${NC}"
        else
            print_error "Terraform destroy failed"
            exit 1
        fi
        ;;
esac

# Show Terraform outputs
if [[ "$ACTION" == "apply" ]]; then
    echo ""
    echo -e "${BLUE}Terraform Outputs:${NC}"
    terraform output
fi

echo ""
echo -e "${GREEN}Deployment script completed successfully!${NC}"
