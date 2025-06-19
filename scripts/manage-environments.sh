#!/bin/bash

# ======================================================
# THE HIGHERSELF NETWORK SERVER - ENVIRONMENT MANAGEMENT SCRIPT
# Enterprise automation platform environment configuration manager
# ======================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Available environments
ENVIRONMENTS=("development" "staging" "production")
CURRENT_ENV="${ENVIRONMENT:-development}"

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
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  switch <env>     Switch to environment (development|staging|production)"
    echo "  validate <env>   Validate environment configuration"
    echo "  setup <env>      Set up environment with Docker Compose"
    echo "  deploy <env>     Deploy to environment"
    echo "  status           Show current environment status"
    echo "  list             List all available environments"
    echo "  secrets <env>    Manage secrets for environment"
    echo "  backup <env>     Backup environment data"
    echo "  restore <env>    Restore environment data"
    echo "  logs <env>       View environment logs"
    echo "  health <env>     Check environment health"
    echo ""
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  -v, --verbose    Enable verbose output"
    echo ""
    echo "Examples:"
    echo "  $0 switch development"
    echo "  $0 validate staging"
    echo "  $0 deploy production"
    echo "  $0 status"
}

# Function to validate environment
validate_environment() {
    local env="$1"
    
    print_header "Validating $env Environment"
    
    # Check if environment file exists
    local env_file="$PROJECT_ROOT/.env.$env"
    if [[ ! -f "$env_file" ]]; then
        print_error "Environment file not found: $env_file"
        return 1
    fi
    
    print_status "Environment file found: $env_file"
    
    # Load environment variables
    set -a
    source "$env_file"
    set +a
    
    # Validate required variables
    local required_vars=(
        "ENVIRONMENT"
        "MONGODB_USERNAME"
        "MONGODB_PASSWORD"
        "REDIS_PASSWORD"
        "NOTION_API_TOKEN"
        "OPENAI_API_KEY"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]] || [[ "${!var}" == *"RETRIEVED_FROM"* ]] || [[ "${!var}" == *"your_"* ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_warning "Missing or placeholder values for:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        
        if [[ "$env" == "production" ]]; then
            print_info "Production environment uses AWS Secrets Manager - this is expected"
        else
            print_error "Please configure these variables in $env_file"
            return 1
        fi
    fi
    
    # Validate Docker Compose configuration
    print_info "Validating Docker Compose configuration..."
    
    local compose_files=("-f" "$PROJECT_ROOT/docker-compose.yml")
    
    if [[ "$env" == "development" ]]; then
        compose_files+=("-f" "$PROJECT_ROOT/docker-compose.override.yml")
    elif [[ "$env" == "production" ]]; then
        compose_files+=("-f" "$PROJECT_ROOT/docker-compose.prod.yml")
    fi
    
    if ! docker-compose "${compose_files[@]}" config > /dev/null 2>&1; then
        print_error "Docker Compose configuration is invalid"
        return 1
    fi
    
    print_status "Docker Compose configuration is valid"
    
    # Check Docker secrets for production
    if [[ "$env" == "production" ]]; then
        print_info "Checking Docker secrets..."
        local secrets=(
            "higherself-notion-api-token-production"
            "higherself-openai-api-key-production"
            "higherself-mongodb-password-production"
            "higherself-redis-password-production"
        )
        
        for secret in "${secrets[@]}"; do
            if ! docker secret inspect "$secret" > /dev/null 2>&1; then
                print_warning "Docker secret not found: $secret"
            else
                print_status "Docker secret found: $secret"
            fi
        done
    fi
    
    print_status "Environment validation completed for $env"
}

# Function to switch environment
switch_environment() {
    local env="$1"
    
    if [[ ! " ${ENVIRONMENTS[@]} " =~ " ${env} " ]]; then
        print_error "Invalid environment: $env"
        print_info "Available environments: ${ENVIRONMENTS[*]}"
        return 1
    fi
    
    print_header "Switching to $env Environment"
    
    # Validate environment first
    if ! validate_environment "$env"; then
        print_error "Environment validation failed"
        return 1
    fi
    
    # Export environment variable
    export ENVIRONMENT="$env"
    
    # Create symlink to current environment file
    local env_file="$PROJECT_ROOT/.env.$env"
    local current_env_file="$PROJECT_ROOT/.env"
    
    if [[ -L "$current_env_file" ]] || [[ -f "$current_env_file" ]]; then
        rm -f "$current_env_file"
    fi
    
    ln -s ".env.$env" "$current_env_file"
    
    print_status "Switched to $env environment"
    print_info "Environment file: $env_file"
    print_info "Current symlink: $current_env_file -> .env.$env"
    
    # Show environment status
    show_environment_status
}

# Function to show environment status
show_environment_status() {
    print_header "Environment Status"
    
    # Determine current environment
    local current_env="unknown"
    if [[ -L "$PROJECT_ROOT/.env" ]]; then
        local link_target=$(readlink "$PROJECT_ROOT/.env")
        if [[ "$link_target" =~ \.env\.(.+) ]]; then
            current_env="${BASH_REMATCH[1]}"
        fi
    elif [[ -f "$PROJECT_ROOT/.env" ]]; then
        # Try to determine from ENVIRONMENT variable in file
        if grep -q "^ENVIRONMENT=" "$PROJECT_ROOT/.env"; then
            current_env=$(grep "^ENVIRONMENT=" "$PROJECT_ROOT/.env" | cut -d'=' -f2)
        fi
    fi
    
    echo "Current Environment: $current_env"
    echo "Available Environments: ${ENVIRONMENTS[*]}"
    
    # Check Docker status
    if docker info > /dev/null 2>&1; then
        print_status "Docker is running"
        
        # Check if containers are running
        local running_containers=$(docker ps --filter "label=com.higherself.environment=$current_env" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "")
        if [[ -n "$running_containers" ]]; then
            echo ""
            echo "Running Containers:"
            echo "$running_containers"
        fi
    else
        print_warning "Docker is not running"
    fi
    
    # Check environment file
    local env_file="$PROJECT_ROOT/.env.$current_env"
    if [[ -f "$env_file" ]]; then
        print_status "Environment file exists: $env_file"
    else
        print_warning "Environment file not found: $env_file"
    fi
}

# Function to setup environment
setup_environment() {
    local env="$1"
    
    print_header "Setting up $env Environment"
    
    # Switch to environment first
    if ! switch_environment "$env"; then
        return 1
    fi
    
    # Build and start services
    local compose_files=("-f" "$PROJECT_ROOT/docker-compose.yml")
    
    if [[ "$env" == "development" ]]; then
        compose_files+=("-f" "$PROJECT_ROOT/docker-compose.override.yml")
    elif [[ "$env" == "production" ]]; then
        compose_files+=("-f" "$PROJECT_ROOT/docker-compose.prod.yml")
    fi
    
    print_info "Building Docker images..."
    docker-compose "${compose_files[@]}" build
    
    print_info "Starting services..."
    docker-compose "${compose_files[@]}" up -d
    
    print_info "Waiting for services to be healthy..."
    sleep 30
    
    # Check health
    check_environment_health "$env"
    
    print_status "Environment setup completed for $env"
}

# Function to check environment health
check_environment_health() {
    local env="$1"
    
    print_header "Checking $env Environment Health"
    
    # Check main application health
    local health_url="http://localhost:8000/health"
    if curl -f -s "$health_url" > /dev/null; then
        print_status "Application health check passed"
    else
        print_error "Application health check failed"
        return 1
    fi
    
    # Check individual services
    local services=("mongodb" "redis" "consul")
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            print_status "$service is running"
        else
            print_error "$service is not running"
        fi
    done
}

# Function to manage secrets
manage_secrets() {
    local env="$1"
    
    print_header "Managing Secrets for $env Environment"
    
    if [[ "$env" == "production" ]]; then
        print_info "Production secrets are managed via AWS Secrets Manager"
        print_info "Use the Terragrunt deployment to configure secrets"
    else
        print_info "Development/Staging secrets are managed via environment files"
        print_info "Edit .env.$env to configure secrets"
    fi
}

# Main script logic
main() {
    local command="${1:-status}"
    
    case "$command" in
        "switch")
            if [[ $# -lt 2 ]]; then
                print_error "Environment required for switch command"
                show_usage
                exit 1
            fi
            switch_environment "$2"
            ;;
        "validate")
            if [[ $# -lt 2 ]]; then
                print_error "Environment required for validate command"
                show_usage
                exit 1
            fi
            validate_environment "$2"
            ;;
        "setup")
            if [[ $# -lt 2 ]]; then
                print_error "Environment required for setup command"
                show_usage
                exit 1
            fi
            setup_environment "$2"
            ;;
        "status")
            show_environment_status
            ;;
        "list")
            echo "Available environments:"
            for env in "${ENVIRONMENTS[@]}"; do
                echo "  - $env"
            done
            ;;
        "secrets")
            if [[ $# -lt 2 ]]; then
                print_error "Environment required for secrets command"
                show_usage
                exit 1
            fi
            manage_secrets "$2"
            ;;
        "health")
            if [[ $# -lt 2 ]]; then
                print_error "Environment required for health command"
                show_usage
                exit 1
            fi
            check_environment_health "$2"
            ;;
        "-h"|"--help"|"help")
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
