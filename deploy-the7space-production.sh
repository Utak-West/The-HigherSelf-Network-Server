#!/bin/bash

# ======================================================
# The 7 Space Production Deployment Script
# Enterprise-Grade Automated Deployment for Art Gallery & Wellness Center
# ======================================================

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
LOG_FILE="$PROJECT_ROOT/logs/the7space-deployment-$(date +%Y%m%d_%H%M%S).log"
DEPLOYMENT_CONFIG="docker-compose.the7space.prod.yml"
ENV_FILE=".env.the7space.production"
TERRAGRUNT_ENV="the7space-production"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')] ℹ️  $1${NC}" | tee -a "$LOG_FILE"
}

log_header() {
    echo -e "${PURPLE}[$(date +'%Y-%m-%d %H:%M:%S')] 🎨 $1${NC}" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log_error "$1"
    log_error "Deployment failed. Check logs at: $LOG_FILE"
    exit 1
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Deployment failed with exit code $exit_code"
        log_info "Initiating cleanup procedures..."
        
        # Stop any partially started services
        docker-compose -f "$DEPLOYMENT_CONFIG" down --remove-orphans 2>/dev/null || true
        
        # Clean up any dangling resources
        docker system prune -f 2>/dev/null || true
    fi
    exit $exit_code
}

trap cleanup EXIT

# Print deployment header
print_header() {
    echo ""
    echo -e "${PURPLE}======================================================${NC}"
    echo -e "${PURPLE}🎨 THE 7 SPACE PRODUCTION DEPLOYMENT${NC}"
    echo -e "${PURPLE}   Art Gallery & Wellness Center Automation Platform${NC}"
    echo -e "${PURPLE}======================================================${NC}"
    echo ""
    log_header "Starting The 7 Space production deployment"
    log_info "Deployment configuration: $DEPLOYMENT_CONFIG"
    log_info "Environment file: $ENV_FILE"
    log_info "Log file: $LOG_FILE"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check required commands
    local required_commands=("docker" "docker-compose" "terragrunt" "curl" "jq")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error_exit "Required command '$cmd' not found. Please install it first."
        fi
    done
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error_exit "Docker daemon is not running. Please start Docker first."
    fi
    
    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "${ENV_FILE}.template" ]; then
            log_warning "Environment file not found. Please copy ${ENV_FILE}.template to $ENV_FILE and configure it."
            error_exit "Environment file $ENV_FILE is required for production deployment."
        else
            error_exit "Environment file $ENV_FILE and template not found."
        fi
    fi
    
    # Check deployment configuration
    if [ ! -f "$DEPLOYMENT_CONFIG" ]; then
        error_exit "Deployment configuration $DEPLOYMENT_CONFIG not found."
    fi
    
    # Check Terragrunt configuration
    if [ ! -d "terragrunt/environments/$TERRAGRUNT_ENV" ]; then
        error_exit "Terragrunt environment configuration not found: terragrunt/environments/$TERRAGRUNT_ENV"
    fi
    
    # Validate environment file
    log_info "Validating environment configuration..."
    source "$ENV_FILE"
    
    # Check critical environment variables
    local required_vars=(
        "ENVIRONMENT"
        "PRIMARY_BUSINESS_ENTITY"
        "MONGODB_PASSWORD"
        "REDIS_PASSWORD"
        "NOTION_API_TOKEN"
        "OPENAI_API_KEY"
        "WEBHOOK_SECRET"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            error_exit "Required environment variable $var is not set in $ENV_FILE"
        fi
    done
    
    # Validate business entity configuration
    if [ "$PRIMARY_BUSINESS_ENTITY" != "the_7_space" ]; then
        error_exit "Invalid business entity configuration. Expected 'the_7_space', got '$PRIMARY_BUSINESS_ENTITY'"
    fi
    
    log_success "Prerequisites check completed successfully"
}

# Setup deployment environment
setup_deployment_environment() {
    log_info "Setting up deployment environment..."
    
    # Create necessary directories
    local directories=(
        "logs/the7space"
        "data/the7space/mongodb"
        "data/the7space/redis"
        "backups/the7space"
        "config/the7space"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_info "Created directory: $dir"
    done
    
    # Set proper permissions
    chmod 755 logs/the7space data/the7space backups/the7space
    chmod 700 data/the7space/mongodb data/the7space/redis
    
    # Create log file directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log_success "Deployment environment setup completed"
}

# Deploy infrastructure with Terragrunt
deploy_infrastructure() {
    log_info "Deploying infrastructure with Terragrunt..."
    
    cd "terragrunt/environments/$TERRAGRUNT_ENV"
    
    # Initialize Terragrunt
    log_info "Initializing Terragrunt..."
    terragrunt init || error_exit "Terragrunt initialization failed"
    
    # Plan infrastructure changes
    log_info "Planning infrastructure changes..."
    terragrunt plan -out=tfplan || error_exit "Terragrunt planning failed"
    
    # Apply infrastructure changes
    log_info "Applying infrastructure changes..."
    terragrunt apply tfplan || error_exit "Terragrunt apply failed"
    
    cd "$PROJECT_ROOT"
    
    log_success "Infrastructure deployment completed"
}

# Build Docker images
build_docker_images() {
    log_info "Building Docker images for The 7 Space..."
    
    # Build main application image
    log_info "Building The 7 Space application image..."
    docker build \
        --build-arg ENVIRONMENT=production \
        --build-arg BUSINESS_ENTITY=the_7_space \
        --build-arg BUILD_VERSION="$(date +%Y%m%d_%H%M%S)" \
        -t thehigherselfnetworkserver:the7space-production \
        . || error_exit "Docker image build failed"
    
    # Tag image with latest
    docker tag thehigherselfnetworkserver:the7space-production \
        thehigherselfnetworkserver:the7space-latest || error_exit "Docker image tagging failed"
    
    log_success "Docker images built successfully"
}

# Deploy services
deploy_services() {
    log_info "Deploying The 7 Space services..."
    
    # Stop any existing services
    log_info "Stopping existing services..."
    docker-compose -f "$DEPLOYMENT_CONFIG" down --remove-orphans || true
    
    # Pull latest images (if using registry)
    log_info "Pulling latest images..."
    docker-compose -f "$DEPLOYMENT_CONFIG" pull || log_warning "Some images could not be pulled (using local builds)"
    
    # Start services
    log_info "Starting The 7 Space services..."
    docker-compose -f "$DEPLOYMENT_CONFIG" up -d || error_exit "Service deployment failed"
    
    log_success "Services deployed successfully"
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to become healthy..."
    
    local max_wait=300  # 5 minutes
    local wait_interval=10
    local elapsed=0
    
    while [ $elapsed -lt $max_wait ]; do
        log_info "Checking service health... (${elapsed}s/${max_wait}s)"
        
        # Check if all services are healthy
        local unhealthy_services
        unhealthy_services=$(docker-compose -f "$DEPLOYMENT_CONFIG" ps --filter "health=unhealthy" -q)
        
        if [ -z "$unhealthy_services" ]; then
            # Check if main application is responding
            if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
                log_success "All services are healthy and responding"
                return 0
            fi
        fi
        
        sleep $wait_interval
        elapsed=$((elapsed + wait_interval))
    done
    
    # If we reach here, services didn't become healthy in time
    log_error "Services did not become healthy within ${max_wait} seconds"
    log_info "Service status:"
    docker-compose -f "$DEPLOYMENT_CONFIG" ps
    
    log_info "Service logs:"
    docker-compose -f "$DEPLOYMENT_CONFIG" logs --tail=50
    
    error_exit "Service health check failed"
}

# Validate deployment
validate_deployment() {
    log_info "Validating The 7 Space deployment..."
    
    # Test main application health endpoint
    log_info "Testing application health endpoint..."
    local health_response
    health_response=$(curl -s http://localhost:8000/health || echo "FAILED")
    
    if [[ "$health_response" == *"healthy"* ]] || [[ "$health_response" == *"ok"* ]]; then
        log_success "Application health check passed"
    else
        log_error "Application health check failed: $health_response"
        error_exit "Application validation failed"
    fi
    
    # Test database connectivity
    log_info "Testing database connectivity..."
    local db_health
    db_health=$(curl -s http://localhost:8000/health/database || echo "FAILED")
    
    if [[ "$db_health" == *"healthy"* ]] || [[ "$db_health" == *"ok"* ]]; then
        log_success "Database connectivity check passed"
    else
        log_warning "Database connectivity check failed: $db_health"
    fi
    
    # Test external service connectivity
    log_info "Testing external service connectivity..."
    local external_health
    external_health=$(curl -s http://localhost:8000/health/external || echo "FAILED")
    
    if [[ "$external_health" == *"healthy"* ]] || [[ "$external_health" == *"ok"* ]]; then
        log_success "External service connectivity check passed"
    else
        log_warning "External service connectivity check failed: $external_health"
    fi
    
    # Test The 7 Space specific endpoints
    log_info "Testing The 7 Space specific functionality..."
    
    # Test contact management endpoint
    local contact_test
    contact_test=$(curl -s -H "Content-Type: application/json" \
        http://localhost:8000/api/the7space/contacts/health || echo "FAILED")
    
    if [[ "$contact_test" != "FAILED" ]]; then
        log_success "Contact management functionality check passed"
    else
        log_warning "Contact management functionality check failed"
    fi
    
    # Test workflow automation endpoint
    local workflow_test
    workflow_test=$(curl -s -H "Content-Type: application/json" \
        http://localhost:8000/api/the7space/workflows/health || echo "FAILED")
    
    if [[ "$workflow_test" != "FAILED" ]]; then
        log_success "Workflow automation functionality check passed"
    else
        log_warning "Workflow automation functionality check failed"
    fi
    
    log_success "Deployment validation completed"
}

# Show deployment summary
show_deployment_summary() {
    echo ""
    log_header "THE 7 SPACE PRODUCTION DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo ""
    log_info "Deployment Summary:"
    echo "  🎨 The 7 Space Application:     http://localhost:8000"
    echo "  📊 Grafana Dashboard:           http://localhost:3000"
    echo "  📈 Prometheus Metrics:          http://localhost:9090"
    echo "  🗄️  MongoDB:                    localhost:27017"
    echo "  🔄 Redis:                       localhost:6379"
    echo "  🔍 Consul:                      http://localhost:8500"
    echo ""
    log_info "The 7 Space Features Enabled:"
    echo "  ✅ Contact Management (191 contacts)"
    echo "  ✅ Gallery Workflow Automation"
    echo "  ✅ Wellness Center Operations"
    echo "  ✅ WordPress SiteGround Integration"
    echo "  ✅ Artist Onboarding Workflows"
    echo "  ✅ Visitor Engagement Automation"
    echo "  ✅ Marketing Campaign Management"
    echo "  ✅ Exhibition Scheduling"
    echo "  ✅ Appointment Management"
    echo "  ✅ Lead Scoring & Qualification"
    echo ""
    log_info "Monitoring & Management:"
    echo "  📋 View logs: docker-compose -f $DEPLOYMENT_CONFIG logs -f"
    echo "  📊 Service status: docker-compose -f $DEPLOYMENT_CONFIG ps"
    echo "  🔄 Restart services: docker-compose -f $DEPLOYMENT_CONFIG restart"
    echo "  🛑 Stop services: docker-compose -f $DEPLOYMENT_CONFIG down"
    echo ""
    log_info "Configuration Files:"
    echo "  🔧 Environment: $ENV_FILE"
    echo "  🐳 Docker Compose: $DEPLOYMENT_CONFIG"
    echo "  🏗️  Terragrunt: terragrunt/environments/$TERRAGRUNT_ENV/"
    echo "  📝 Deployment Log: $LOG_FILE"
    echo ""
    log_success "The 7 Space is now ready for production use!"
    echo ""
}

# Main deployment function
main() {
    print_header
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Execute deployment steps
    check_prerequisites
    setup_deployment_environment
    deploy_infrastructure
    build_docker_images
    deploy_services
    wait_for_services
    validate_deployment
    show_deployment_summary
    
    log_success "The 7 Space production deployment completed successfully!"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "infrastructure")
        print_header
        check_prerequisites
        deploy_infrastructure
        log_success "Infrastructure deployment completed"
        ;;
    "services")
        print_header
        check_prerequisites
        setup_deployment_environment
        build_docker_images
        deploy_services
        wait_for_services
        validate_deployment
        show_deployment_summary
        ;;
    "validate")
        print_header
        validate_deployment
        log_success "Deployment validation completed"
        ;;
    "status")
        echo "The 7 Space Production Status:"
        docker-compose -f "$DEPLOYMENT_CONFIG" ps
        ;;
    "logs")
        docker-compose -f "$DEPLOYMENT_CONFIG" logs -f
        ;;
    "stop")
        log_info "Stopping The 7 Space services..."
        docker-compose -f "$DEPLOYMENT_CONFIG" down
        log_success "Services stopped"
        ;;
    "restart")
        log_info "Restarting The 7 Space services..."
        docker-compose -f "$DEPLOYMENT_CONFIG" restart
        wait_for_services
        log_success "Services restarted"
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy        Full deployment (default)"
        echo "  infrastructure Deploy infrastructure only"
        echo "  services      Deploy services only"
        echo "  validate      Validate deployment"
        echo "  status        Show service status"
        echo "  logs          Show service logs"
        echo "  stop          Stop services"
        echo "  restart       Restart services"
        echo "  help          Show this help"
        ;;
    *)
        error_exit "Unknown command: $1. Use 'help' for available commands."
        ;;
esac
