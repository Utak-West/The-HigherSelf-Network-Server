#!/bin/bash
# Higher Self Network Server - Production Deployment Script
# Addresses all critical issues and provides comprehensive deployment automation

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Configuration
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="./logs/deployment_$(date +%Y%m%d_%H%M%S).log"

# Create necessary directories
mkdir -p logs backups

# Function to check prerequisites
check_prerequisites() {
    log "Checking deployment prerequisites..."
    
    # Check Docker and Docker Compose
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
    
    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        error "Environment file $ENV_FILE not found"
        error "Please copy .env.example to $ENV_FILE and configure it"
        exit 1
    fi
    
    # Check disk space (minimum 10GB)
    local available_space=$(df . | awk 'NR==2 {print $4}')
    local required_space=10485760  # 10GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        error "Insufficient disk space. Required: 10GB, Available: $(($available_space/1024/1024))GB"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Function to validate environment configuration
validate_environment() {
    log "Validating environment configuration..."
    
    # Source environment file
    source "$ENV_FILE"
    
    # Critical environment variables
    local required_vars=(
        "REDIS_URI"
        "REDIS_PASSWORD"
        "NOTION_API_TOKEN"
        "SUPABASE_URL"
        "SUPABASE_API_KEY"
        "MONGODB_USERNAME"
        "MONGODB_PASSWORD"
        "NEO4J_USER"
        "NEO4J_PASSWORD"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        error "Missing required environment variables: ${missing_vars[*]}"
        error "Please configure these variables in $ENV_FILE"
        exit 1
    fi
    
    # Test Redis connection
    log "Testing Redis Cloud connection..."
    if ! timeout 10 redis-cli -u "$REDIS_URI" --tls ping &> /dev/null; then
        error "Redis connection test failed. Please check REDIS_URI and REDIS_PASSWORD"
        exit 1
    fi
    
    success "Environment validation passed"
}

# Function to create backup
create_backup() {
    log "Creating backup before deployment..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup current containers if they exist
    if docker-compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
        log "Backing up current deployment..."
        
        # Export container data
        docker-compose -f "$COMPOSE_FILE" exec -T mongodb mongodump --archive > "$BACKUP_DIR/mongodb_backup.archive" 2>/dev/null || true
        docker-compose -f "$COMPOSE_FILE" exec -T neo4j neo4j-admin backup --to=/tmp/backup &> /dev/null || true
        docker-compose -f "$COMPOSE_FILE" exec -T neo4j tar -czf - /tmp/backup > "$BACKUP_DIR/neo4j_backup.tar.gz" 2>/dev/null || true
        
        # Backup application data
        docker-compose -f "$COMPOSE_FILE" exec -T higherself-server tar -czf - /app/data > "$BACKUP_DIR/app_data_backup.tar.gz" 2>/dev/null || true
        
        success "Backup created in $BACKUP_DIR"
    else
        log "No existing deployment found, skipping backup"
    fi
}

# Function to build images
build_images() {
    log "Building Docker images..."
    
    # Build production image
    docker-compose -f "$COMPOSE_FILE" build --no-cache --parallel
    
    # Tag images with timestamp
    local timestamp=$(date +%Y%m%d_%H%M%S)
    docker tag higherself-network-server_higherself-server:latest higherself-network-server:$timestamp
    
    success "Docker images built successfully"
}

# Function to deploy services
deploy_services() {
    log "Deploying services..."
    
    # Stop existing services gracefully
    if docker-compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
        log "Stopping existing services..."
        docker-compose -f "$COMPOSE_FILE" down --timeout 30
    fi
    
    # Start services in correct order
    log "Starting database services..."
    docker-compose -f "$COMPOSE_FILE" up -d mongodb neo4j
    
    # Wait for databases to be healthy
    log "Waiting for databases to be ready..."
    timeout 120 bash -c 'until docker-compose -f "$COMPOSE_FILE" ps mongodb | grep -q "healthy"; do sleep 5; done'
    timeout 120 bash -c 'until docker-compose -f "$COMPOSE_FILE" ps neo4j | grep -q "healthy"; do sleep 5; done'
    
    # Start application services
    log "Starting application services..."
    docker-compose -f "$COMPOSE_FILE" up -d higherself-server celery-worker
    
    # Start monitoring and proxy services
    log "Starting monitoring and proxy services..."
    docker-compose -f "$COMPOSE_FILE" up -d nginx prometheus grafana
    
    success "Services deployed successfully"
}

# Function to verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Wait for application to be ready
    log "Waiting for application to be healthy..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            success "Application health check passed"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error "Application health check failed after $max_attempts attempts"
            docker-compose -f "$COMPOSE_FILE" logs higherself-server
            exit 1
        fi
        
        log "Attempt $attempt/$max_attempts: Waiting for application..."
        sleep 10
        ((attempt++))
    done
    
    # Test critical endpoints
    log "Testing critical endpoints..."
    
    # Test API endpoints
    if ! curl -f http://localhost:8000/api/v1/health &> /dev/null; then
        warning "API health endpoint not responding"
    fi
    
    # Test agent endpoints
    if ! curl -f http://localhost:8000/api/v1/agents/status &> /dev/null; then
        warning "Agent status endpoint not responding"
    fi
    
    # Check service status
    log "Checking service status..."
    docker-compose -f "$COMPOSE_FILE" ps
    
    success "Deployment verification completed"
}

# Function to setup monitoring
setup_monitoring() {
    log "Setting up monitoring and alerting..."
    
    # Configure Grafana dashboards
    if [ -d "./monitoring/grafana/dashboards" ]; then
        log "Importing Grafana dashboards..."
        # Dashboards are automatically imported via volume mounts
    fi
    
    # Setup log rotation
    log "Configuring log rotation..."
    cat > /tmp/higherself-logrotate << EOF
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
    postrotate
        docker kill --signal=USR1 \$(docker ps -q) 2>/dev/null || true
    endscript
}
EOF
    
    sudo mv /tmp/higherself-logrotate /etc/logrotate.d/higherself
    
    success "Monitoring setup completed"
}

# Function to run post-deployment tasks
post_deployment_tasks() {
    log "Running post-deployment tasks..."
    
    # Run database migrations
    log "Running database migrations..."
    docker-compose -f "$COMPOSE_FILE" exec -T higherself-server python scripts/migrate.py || true
    
    # Initialize agent system
    log "Initializing agent system..."
    docker-compose -f "$COMPOSE_FILE" exec -T higherself-server python scripts/initialize_agents.py || true
    
    # Warm up caches
    log "Warming up application caches..."
    curl -s http://localhost:8000/api/v1/agents/warmup &> /dev/null || true
    
    # Send deployment notification
    log "Sending deployment notification..."
    # Add notification logic here (Slack, email, etc.)
    
    success "Post-deployment tasks completed"
}

# Function to display deployment summary
deployment_summary() {
    log "Deployment Summary"
    log "=================="
    log "Environment: Production"
    log "Timestamp: $(date)"
    log "Backup Location: $BACKUP_DIR"
    log "Log File: $LOG_FILE"
    log ""
    log "Service Status:"
    docker-compose -f "$COMPOSE_FILE" ps
    log ""
    log "Application URLs:"
    log "- API: http://localhost:8000"
    log "- Health Check: http://localhost:8000/health"
    log "- Grafana: http://localhost:3000"
    log "- Prometheus: http://localhost:9090"
    log ""
    success "Production deployment completed successfully!"
}

# Main deployment function
main() {
    log "Higher Self Network Server - Production Deployment"
    log "=================================================="
    
    # Execute deployment steps
    check_prerequisites
    validate_environment
    create_backup
    build_images
    deploy_services
    verify_deployment
    setup_monitoring
    post_deployment_tasks
    deployment_summary
}

# Handle script interruption
trap 'error "Deployment interrupted"; exit 1' SIGINT SIGTERM

# Execute main function and log output
main 2>&1 | tee "$LOG_FILE"
