#!/bin/bash

# HigherSelf Network Server - Terragrunt Deployment Script
# Enterprise-grade deployment with Gruntwork integration

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Default values
ENVIRONMENT="${1:-development}"
ACTION="${2:-apply}"
MODULE="${3:-all}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${NC}"
    echo "Usage: $0 [development|staging|production] [apply|destroy|plan] [module|all]"
    exit 1
fi

# Validate action
if [[ ! "$ACTION" =~ ^(apply|destroy|plan|init)$ ]]; then
    echo -e "${RED}Error: Invalid action '$ACTION'${NC}"
    echo "Usage: $0 [development|staging|production] [apply|destroy|plan|init] [module|all]"
    exit 1
fi

echo -e "${BLUE}🚀 HigherSelf Network Server - Terragrunt Deployment${NC}"
echo -e "${BLUE}Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "${BLUE}Action: ${YELLOW}$ACTION${NC}"
echo -e "${BLUE}Module: ${YELLOW}$MODULE${NC}"
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

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"
    
    # Check if terragrunt is installed
    if ! command -v terragrunt &> /dev/null; then
        print_error "Terragrunt is not installed"
        echo "Please install Terragrunt: https://terragrunt.gruntwork.io/docs/getting-started/install/"
        exit 1
    fi
    
    # Check if terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed"
        echo "Please install Terraform: https://www.terraform.io/downloads.html"
        exit 1
    fi
    
    # Check if AWS CLI is installed and configured
    if ! command -v aws &> /dev/null; then
        print_warning "AWS CLI is not installed"
        echo "Please install AWS CLI for full functionality: https://aws.amazon.com/cli/"
    else
        # Check AWS credentials
        if ! aws sts get-caller-identity &> /dev/null; then
            print_warning "AWS credentials not configured"
            echo "Please configure AWS credentials: aws configure"
        else
            print_status "AWS credentials configured"
        fi
    fi
    
    print_status "Prerequisites check completed"
}

# Function to set environment variables
set_environment_variables() {
    echo -e "${BLUE}Setting environment variables...${NC}"
    
    export ENVIRONMENT="$ENVIRONMENT"
    export AWS_REGION="${AWS_REGION:-us-east-1}"
    export DOCKER_HOST="${DOCKER_HOST:-unix:///var/run/docker.sock}"
    
    # Load environment-specific variables if they exist
    if [[ -f ".env.$ENVIRONMENT" ]]; then
        print_info "Loading environment variables from .env.$ENVIRONMENT"
        set -a  # automatically export all variables
        source ".env.$ENVIRONMENT"
        set +a
    elif [[ -f ".env" ]]; then
        print_info "Loading environment variables from .env"
        set -a
        source ".env"
        set +a
    fi
    
    print_status "Environment variables set"
}

# Function to validate required environment variables
validate_environment_variables() {
    echo -e "${BLUE}Validating environment variables...${NC}"
    
    local required_vars=()
    local missing_vars=()
    
    # Environment-specific required variables
    case $ENVIRONMENT in
        "production")
            required_vars=("PRODUCTION_DOMAIN" "GRAFANA_ADMIN_PASSWORD" "NOTION_API_TOKEN")
            ;;
        "staging")
            required_vars=("STAGING_DOMAIN" "GRAFANA_ADMIN_PASSWORD" "NOTION_API_TOKEN")
            ;;
        "development")
            required_vars=("NOTION_API_TOKEN")
            ;;
    esac
    
    # Check for missing variables
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables for $ENVIRONMENT:"
        printf '%s\n' "${missing_vars[@]}"
        echo ""
        echo "Please set these variables in .env.$ENVIRONMENT or as environment variables"
        exit 1
    fi
    
    print_status "Environment variables validation passed"
}

# Function to initialize Terragrunt
initialize_terragrunt() {
    echo -e "${BLUE}Initializing Terragrunt...${NC}"
    
    local terragrunt_dir="terragrunt/environments/$ENVIRONMENT"
    
    if [[ ! -d "$terragrunt_dir" ]]; then
        print_error "Terragrunt environment directory not found: $terragrunt_dir"
        exit 1
    fi
    
    cd "$terragrunt_dir"
    
    # Initialize Terragrunt
    if terragrunt init; then
        print_status "Terragrunt initialization completed"
    else
        print_error "Terragrunt initialization failed"
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
}

# Function to deploy specific module
deploy_module() {
    local module_name="$1"
    local module_dir="terragrunt/modules/$module_name"
    
    echo -e "${PURPLE}Deploying module: $module_name${NC}"
    
    if [[ ! -d "$module_dir" ]]; then
        print_error "Module directory not found: $module_dir"
        return 1
    fi
    
    cd "$module_dir"
    
    case $ACTION in
        "plan")
            terragrunt plan
            ;;
        "apply")
            terragrunt apply
            ;;
        "destroy")
            terragrunt destroy
            ;;
        "init")
            terragrunt init
            ;;
    esac
    
    cd "$PROJECT_ROOT"
}

# Function to deploy environment
deploy_environment() {
    local env_dir="terragrunt/environments/$ENVIRONMENT"
    
    echo -e "${PURPLE}Deploying environment: $ENVIRONMENT${NC}"
    
    cd "$env_dir"
    
    case $ACTION in
        "plan")
            terragrunt run-all plan
            ;;
        "apply")
            terragrunt run-all apply
            ;;
        "destroy")
            terragrunt run-all destroy
            ;;
        "init")
            terragrunt run-all init
            ;;
    esac
    
    cd "$PROJECT_ROOT"
}

# Function to show deployment summary
show_deployment_summary() {
    echo ""
    echo -e "${GREEN}🎉 Deployment Summary${NC}"
    echo -e "${BLUE}Environment: ${YELLOW}$ENVIRONMENT${NC}"
    echo -e "${BLUE}Action: ${YELLOW}$ACTION${NC}"
    echo -e "${BLUE}Module: ${YELLOW}$MODULE${NC}"
    echo ""
    
    if [[ "$ACTION" == "apply" ]]; then
        echo -e "${BLUE}Next Steps:${NC}"
        echo "1. Verify services are running: docker ps"
        echo "2. Check application health: curl http://localhost:8000/health"
        echo "3. Monitor logs: docker-compose logs -f"
        echo "4. Access monitoring: http://localhost:3000 (Grafana)"
        echo ""
        
        echo -e "${BLUE}Useful Commands:${NC}"
        echo "• Plan changes: $0 $ENVIRONMENT plan"
        echo "• Apply changes: $0 $ENVIRONMENT apply"
        echo "• Destroy environment: $0 $ENVIRONMENT destroy"
        echo "• Deploy specific module: $0 $ENVIRONMENT apply [module-name]"
    fi
}

# Main execution
main() {
    check_prerequisites
    set_environment_variables
    validate_environment_variables
    
    # Initialize if needed
    if [[ "$ACTION" == "init" ]] || [[ ! -d "terragrunt/environments/$ENVIRONMENT/.terragrunt-cache" ]]; then
        initialize_terragrunt
    fi
    
    # Deploy based on module specification
    if [[ "$MODULE" == "all" ]]; then
        deploy_environment
    else
        deploy_module "$MODULE"
    fi
    
    show_deployment_summary
}

# Production safety check
if [[ "$ENVIRONMENT" == "production" && "$ACTION" == "apply" ]]; then
    echo -e "${YELLOW}⚠ PRODUCTION DEPLOYMENT WARNING ⚠${NC}"
    echo "You are about to deploy to PRODUCTION environment."
    echo "This will affect live services and real users."
    echo ""
    read -p "Type 'DEPLOY TO PRODUCTION' to continue: " -r
    if [[ ! $REPLY == "DEPLOY TO PRODUCTION" ]]; then
        echo "Production deployment cancelled."
        exit 0
    fi
fi

# Destruction safety check
if [[ "$ACTION" == "destroy" ]]; then
    echo -e "${RED}⚠ DESTRUCTION WARNING ⚠${NC}"
    echo "You are about to DESTROY the $ENVIRONMENT environment."
    echo "This will remove all infrastructure and data."
    echo ""
    read -p "Type 'DESTROY $ENVIRONMENT' to continue: " -r
    if [[ ! $REPLY == "DESTROY $ENVIRONMENT" ]]; then
        echo "Destruction cancelled."
        exit 0
    fi
fi

# Execute main function
main "$@"
