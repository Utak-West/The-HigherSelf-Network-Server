#!/bin/bash

# HigherSelf Network Server - Terraform-Integrated Deployment Script
# Enterprise-grade deployment with Infrastructure as Code

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"
ENVIRONMENT="${1:-development}"
ACTION="${2:-apply}"

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

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    print_error "Invalid environment '$ENVIRONMENT'"
    echo "Usage: $0 [development|staging|production] [apply|destroy|plan]"
    exit 1
fi

# Validate action
if [[ ! "$ACTION" =~ ^(apply|destroy|plan)$ ]]; then
    print_error "Invalid action '$ACTION'"
    echo "Usage: $0 [development|staging|production] [apply|destroy|plan]"
    exit 1
fi

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check if Terraform directory exists
if [[ ! -d "$TERRAFORM_DIR" ]]; then
    print_error "Terraform directory not found: $TERRAFORM_DIR"
    echo "Please ensure Terraform configuration is set up"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    echo "Please start Docker Desktop or Docker daemon"
    exit 1
fi
print_status "Docker is running"

# Check Terraform
if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed"
    echo "Please install Terraform: https://www.terraform.io/downloads.html"
    exit 1
fi
print_status "Terraform found: $(terraform version | head -n1)"

# Change to terraform directory
cd "$TERRAFORM_DIR"

# Check if Terraform is initialized
if [[ ! -d ".terraform" ]]; then
    print_warning "Terraform not initialized. Initializing now..."
    if ! terraform init; then
        print_error "Terraform initialization failed"
        exit 1
    fi
    print_status "Terraform initialized"
fi

# Check environment file
ENV_FILE="environments/$ENVIRONMENT.tfvars"
if [[ ! -f "$ENV_FILE" ]]; then
    print_error "Environment file not found: $ENV_FILE"
    exit 1
fi
print_status "Environment configuration found: $ENV_FILE"

# Create or select workspace
echo ""
echo -e "${BLUE}Managing Terraform workspace...${NC}"
if terraform workspace list | grep -q "$ENVIRONMENT"; then
    terraform workspace select "$ENVIRONMENT"
    print_status "Selected workspace: $ENVIRONMENT"
else
    terraform workspace new "$ENVIRONMENT"
    print_status "Created workspace: $ENVIRONMENT"
fi

# Production safety check
if [[ "$ENVIRONMENT" == "production" && "$ACTION" == "apply" ]]; then
    echo -e "${YELLOW}⚠ PRODUCTION DEPLOYMENT WARNING ⚠${NC}"
    echo "You are about to deploy to PRODUCTION environment."
    echo ""
    echo "Pre-deployment checklist:"
    echo "□ All passwords changed from defaults"
    echo "□ SSL certificates configured"
    echo "□ IP restrictions properly set"
    echo "□ Backup procedures in place"
    echo "□ Monitoring alerts configured"
    echo "□ Integration tokens set as environment variables"
    echo ""
    read -p "Have you completed the checklist above? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Please complete the production checklist before deploying."
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
            print_status "Infrastructure deployed successfully"
        else
            print_error "Terraform apply failed"
            exit 1
        fi
        
        # Post-deployment validation
        echo ""
        echo -e "${BLUE}Running post-deployment validation...${NC}"
        
        # Wait for services to be ready
        echo "Waiting for services to start..."
        sleep 10
        
        # Health checks
        HEALTH_CHECKS=(
            "http://localhost:8000/health:HigherSelf Network Server"
            "http://localhost:9090/-/ready:Prometheus"
            "http://localhost:3000/api/health:Grafana"
            "http://localhost:8500/v1/status/leader:Consul"
        )
        
        for check in "${HEALTH_CHECKS[@]}"; do
            IFS=':' read -r url service <<< "$check"
            echo -n "Checking $service... "
            
            max_attempts=15
            attempt=1
            
            while [ $attempt -le $max_attempts ]; do
                if curl -f -s "$url" > /dev/null 2>&1; then
                    print_status "$service is ready"
                    break
                fi
                
                if [ $attempt -eq $max_attempts ]; then
                    print_warning "$service may not be ready yet"
                    break
                fi
                
                echo -n "."
                sleep 2
                ((attempt++))
            done
        done
        
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
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | head -8
        echo ""
        
        # Show useful commands
        echo -e "${BLUE}Useful Commands:${NC}"
        echo "• View logs: docker logs <container_name>"
        echo "• Check status: docker ps"
        echo "• Monitor resources: docker stats"
        echo "• Terraform outputs: terraform output"
        echo "• Stop services: ./terraform-deploy.sh $ENVIRONMENT destroy"
        ;;
    "destroy")
        if terraform destroy -var-file="$ENV_FILE" -auto-approve; then
            print_status "Infrastructure destroyed successfully"
            echo ""
            echo -e "${GREEN}Environment $ENVIRONMENT has been destroyed.${NC}"
        else
            print_error "Terraform destroy failed"
            exit 1
        fi
        ;;
esac

# Show Terraform outputs for apply action
if [[ "$ACTION" == "apply" ]]; then
    echo ""
    echo -e "${BLUE}Terraform Outputs:${NC}"
    terraform output -json | jq -r '
        to_entries[] | 
        select(.key | test("quick_start_guide|service_endpoints|monitoring_urls")) |
        "\(.key): \(.value.value)"
    ' 2>/dev/null || terraform output
fi

echo ""
echo -e "${GREEN}Terraform deployment script completed successfully!${NC}"

# Environment-specific post-deployment notes
case $ENVIRONMENT in
    "development")
        echo ""
        echo -e "${BLUE}Development Environment Notes:${NC}"
        echo "• All services are running locally"
        echo "• Default passwords are in use"
        echo "• Monitoring is enabled for testing"
        echo "• SSL is disabled for local development"
        ;;
    "staging")
        echo ""
        echo -e "${BLUE}Staging Environment Notes:${NC}"
        echo "• Production-like configuration active"
        echo "• SSL is enabled - ensure certificates are valid"
        echo "• Auto-scaling is enabled for testing"
        echo "• Use this environment for integration testing"
        ;;
    "production")
        echo ""
        echo -e "${BLUE}Production Environment Notes:${NC}"
        echo "• Enterprise-grade security is active"
        echo "• Monitor the system closely for the first 24 hours"
        echo "• Set up alerting for critical metrics"
        echo "• Verify backup procedures are working"
        echo "• Review logs regularly for any issues"
        ;;
esac
