#!/bin/bash

# ======================================================
# THE HIGHERSELF NETWORK SERVER - DOCKER-TERRAGRUNT INTEGRATION
# Enterprise deployment pipeline combining Infrastructure as Code with containerization
# ======================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
ENVIRONMENT="${1:-development}"
ACTION="${2:-deploy}"
COMPONENT="${3:-all}"

# Available environments and actions
ENVIRONMENTS=("development" "staging" "production")
ACTIONS=("deploy" "destroy" "plan" "status" "secrets" "infrastructure" "containers")
COMPONENTS=("all" "infrastructure" "secrets" "containers" "monitoring")

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "======================================================="
    echo "$1"
    echo "======================================================="
    echo -e "${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [ENVIRONMENT] [ACTION] [COMPONENT]"
    echo ""
    echo "Environments:"
    echo "  development    Local development environment"
    echo "  staging        Pre-production testing environment"
    echo "  production     Live production environment"
    echo ""
    echo "Actions:"
    echo "  deploy         Full deployment (infrastructure + containers)"
    echo "  destroy        Destroy environment"
    echo "  plan           Show deployment plan"
    echo "  status         Show environment status"
    echo "  secrets        Deploy/update secrets only"
    echo "  infrastructure Deploy infrastructure only"
    echo "  containers     Deploy containers only"
    echo ""
    echo "Components:"
    echo "  all            All components (default)"
    echo "  infrastructure Terragrunt infrastructure only"
    echo "  secrets        Secrets management only"
    echo "  containers     Docker containers only"
    echo "  monitoring     Monitoring stack only"
    echo ""
    echo "Examples:"
    echo "  $0 development deploy all"
    echo "  $0 staging plan infrastructure"
    echo "  $0 production secrets"
    echo "  $0 development status"
}

# Function to validate inputs
validate_inputs() {
    if [[ ! " ${ENVIRONMENTS[@]} " =~ " ${ENVIRONMENT} " ]]; then
        print_error "Invalid environment: $ENVIRONMENT"
        print_info "Available environments: ${ENVIRONMENTS[*]}"
        exit 1
    fi
    
    if [[ ! " ${ACTIONS[@]} " =~ " ${ACTION} " ]]; then
        print_error "Invalid action: $ACTION"
        print_info "Available actions: ${ACTIONS[*]}"
        exit 1
    fi
    
    if [[ ! " ${COMPONENTS[@]} " =~ " ${COMPONENT} " ]]; then
        print_error "Invalid component: $COMPONENT"
        print_info "Available components: ${COMPONENTS[*]}"
        exit 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_tools=()
    
    # Check required tools
    local required_tools=("docker" "docker-compose" "terragrunt" "terraform" "aws")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        else
            print_status "$tool is installed"
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        print_error "Missing required tools:"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    print_status "Docker daemon is running"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        print_warning "AWS credentials not configured (required for production)"
        if [[ "$ENVIRONMENT" == "production" ]]; then
            exit 1
        fi
    else
        print_status "AWS credentials configured"
    fi
}

# Function to load environment configuration
load_environment_config() {
    print_header "Loading Environment Configuration"
    
    # Set environment variable
    export ENVIRONMENT="$ENVIRONMENT"
    
    # Load environment-specific configuration
    local env_file="$PROJECT_ROOT/.env.$ENVIRONMENT"
    if [[ -f "$env_file" ]]; then
        print_info "Loading configuration from $env_file"
        set -a
        source "$env_file"
        set +a
        print_status "Environment configuration loaded"
    else
        print_warning "Environment file not found: $env_file"
        if [[ "$ENVIRONMENT" != "development" ]]; then
            print_error "Environment file required for $ENVIRONMENT"
            exit 1
        fi
    fi
    
    # Create symlink to current environment
    local current_env_file="$PROJECT_ROOT/.env"
    if [[ -L "$current_env_file" ]] || [[ -f "$current_env_file" ]]; then
        rm -f "$current_env_file"
    fi
    ln -s ".env.$ENVIRONMENT" "$current_env_file"
    print_status "Environment symlink created: .env -> .env.$ENVIRONMENT"
}

# Function to deploy secrets
deploy_secrets() {
    print_header "Deploying Secrets Management"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        print_info "Deploying AWS Secrets Manager configuration..."
        cd "$PROJECT_ROOT/terragrunt/modules/secrets-manager"
        terragrunt apply -auto-approve
        cd "$PROJECT_ROOT"
        print_status "AWS Secrets Manager deployed"
    elif [[ "$ENVIRONMENT" == "staging" ]]; then
        print_info "Deploying Vault configuration..."
        # Deploy Vault for staging
        docker-compose up -d vault
        print_status "Vault deployed for staging"
    else
        print_info "Development environment uses environment files for secrets"
        print_status "No additional secrets deployment needed"
    fi
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_header "Deploying Infrastructure"
    
    local terragrunt_env_dir="$PROJECT_ROOT/terragrunt/environments/$ENVIRONMENT"
    
    if [[ ! -d "$terragrunt_env_dir" ]]; then
        print_error "Terragrunt environment directory not found: $terragrunt_env_dir"
        exit 1
    fi
    
    cd "$terragrunt_env_dir"
    
    print_info "Initializing Terragrunt..."
    terragrunt run-all init
    
    if [[ "$ACTION" == "plan" ]]; then
        print_info "Planning infrastructure changes..."
        terragrunt run-all plan
    else
        print_info "Applying infrastructure changes..."
        terragrunt run-all apply -auto-approve
    fi
    
    cd "$PROJECT_ROOT"
    print_status "Infrastructure deployment completed"
}

# Function to deploy containers
deploy_containers() {
    print_header "Deploying Docker Containers"
    
    # Determine Docker Compose files
    local compose_files=("-f" "docker-compose.yml")
    
    case "$ENVIRONMENT" in
        "development")
            compose_files+=("-f" "docker-compose.override.yml")
            ;;
        "staging")
            # Use base configuration for staging
            ;;
        "production")
            compose_files+=("-f" "docker-compose.prod.yml")
            ;;
    esac
    
    print_info "Building Docker images..."
    docker-compose "${compose_files[@]}" build
    
    if [[ "$ACTION" == "plan" ]]; then
        print_info "Showing container configuration..."
        docker-compose "${compose_files[@]}" config
    else
        print_info "Starting containers..."
        docker-compose "${compose_files[@]}" up -d
        
        print_info "Waiting for services to be healthy..."
        sleep 30
        
        # Check service health
        check_service_health
    fi
    
    print_status "Container deployment completed"
}

# Function to check service health
check_service_health() {
    print_header "Checking Service Health"
    
    local health_checks=(
        "http://localhost:8000/health:Application"
        "http://localhost:9090/-/healthy:Prometheus"
        "http://localhost:3000/api/health:Grafana"
    )
    
    for check in "${health_checks[@]}"; do
        local url="${check%:*}"
        local service="${check#*:}"
        
        if curl -f -s "$url" > /dev/null 2>&1; then
            print_status "$service health check passed"
        else
            print_warning "$service health check failed"
        fi
    done
    
    # Check Docker container status
    print_info "Container status:"
    docker-compose ps
}

# Function to show environment status
show_environment_status() {
    print_header "Environment Status: $ENVIRONMENT"
    
    # Show environment configuration
    echo "Environment: $ENVIRONMENT"
    echo "Configuration file: .env.$ENVIRONMENT"
    
    # Show infrastructure status
    print_info "Infrastructure Status:"
    local terragrunt_env_dir="$PROJECT_ROOT/terragrunt/environments/$ENVIRONMENT"
    if [[ -d "$terragrunt_env_dir" ]]; then
        cd "$terragrunt_env_dir"
        terragrunt run-all show 2>/dev/null || echo "No infrastructure deployed"
        cd "$PROJECT_ROOT"
    fi
    
    # Show container status
    print_info "Container Status:"
    if docker-compose ps | grep -q "Up"; then
        docker-compose ps
    else
        echo "No containers running"
    fi
    
    # Show service health
    check_service_health
}

# Function to destroy environment
destroy_environment() {
    print_header "Destroying Environment: $ENVIRONMENT"
    
    print_warning "This will destroy all infrastructure and containers for $ENVIRONMENT"
    read -p "Type 'DESTROY $ENVIRONMENT' to continue: " -r
    if [[ ! $REPLY == "DESTROY $ENVIRONMENT" ]]; then
        echo "Destruction cancelled."
        exit 0
    fi
    
    # Stop and remove containers
    print_info "Stopping containers..."
    docker-compose down -v --remove-orphans || true
    
    # Destroy infrastructure
    print_info "Destroying infrastructure..."
    local terragrunt_env_dir="$PROJECT_ROOT/terragrunt/environments/$ENVIRONMENT"
    if [[ -d "$terragrunt_env_dir" ]]; then
        cd "$terragrunt_env_dir"
        terragrunt run-all destroy -auto-approve
        cd "$PROJECT_ROOT"
    fi
    
    print_status "Environment destroyed"
}

# Function to perform full deployment
full_deployment() {
    print_header "Full Deployment: $ENVIRONMENT"
    
    case "$COMPONENT" in
        "all")
            deploy_secrets
            deploy_infrastructure
            deploy_containers
            ;;
        "infrastructure")
            deploy_infrastructure
            ;;
        "secrets")
            deploy_secrets
            ;;
        "containers")
            deploy_containers
            ;;
        "monitoring")
            # Deploy only monitoring components
            docker-compose up -d prometheus grafana
            ;;
    esac
    
    if [[ "$ACTION" == "deploy" ]]; then
        show_environment_status
    fi
}

# Function to show deployment summary
show_deployment_summary() {
    print_header "Deployment Summary"
    
    echo "Environment: $ENVIRONMENT"
    echo "Action: $ACTION"
    echo "Component: $COMPONENT"
    echo ""
    
    if [[ "$ACTION" == "deploy" ]]; then
        echo "Next Steps:"
        echo "1. Check service health: curl http://localhost:8000/health"
        echo "2. Access Grafana: http://localhost:3000"
        echo "3. Access Prometheus: http://localhost:9090"
        echo "4. View logs: docker-compose logs -f"
        echo ""
        
        echo "Management Commands:"
        echo "• Check status: $0 $ENVIRONMENT status"
        echo "• Update secrets: $0 $ENVIRONMENT secrets"
        echo "• Redeploy containers: $0 $ENVIRONMENT containers"
        echo "• Destroy environment: $0 $ENVIRONMENT destroy"
    fi
}

# Main execution function
main() {
    print_header "HigherSelf Network Server - Docker-Terragrunt Deployment"
    echo "Environment: $ENVIRONMENT"
    echo "Action: $ACTION"
    echo "Component: $COMPONENT"
    echo ""
    
    validate_inputs
    check_prerequisites
    load_environment_config
    
    case "$ACTION" in
        "deploy")
            full_deployment
            ;;
        "destroy")
            destroy_environment
            ;;
        "plan")
            if [[ "$COMPONENT" == "infrastructure" || "$COMPONENT" == "all" ]]; then
                deploy_infrastructure
            fi
            if [[ "$COMPONENT" == "containers" || "$COMPONENT" == "all" ]]; then
                deploy_containers
            fi
            ;;
        "status")
            show_environment_status
            ;;
        "secrets")
            deploy_secrets
            ;;
        "infrastructure")
            deploy_infrastructure
            ;;
        "containers")
            deploy_containers
            ;;
    esac
    
    show_deployment_summary
}

# Production safety check
if [[ "$ENVIRONMENT" == "production" && "$ACTION" == "deploy" ]]; then
    print_warning "PRODUCTION DEPLOYMENT WARNING"
    echo "You are about to deploy to PRODUCTION environment."
    echo "This will affect live services and real users."
    echo ""
    read -p "Type 'DEPLOY TO PRODUCTION' to continue: " -r
    if [[ ! $REPLY == "DEPLOY TO PRODUCTION" ]]; then
        echo "Production deployment cancelled."
        exit 0
    fi
fi

# Execute main function
main "$@"
