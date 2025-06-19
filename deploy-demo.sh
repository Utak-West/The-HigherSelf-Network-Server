#!/bin/bash

# ======================================================
# THE HIGHERSELF NETWORK SERVER - DEMO DEPLOYMENT SCRIPT
# THE 7 SPACE FOCUSED DEPLOYMENT
# ======================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEMO_ENV_FILE=".env.demo"
DEMO_COMPOSE_FILE="docker-compose.demo.yml"
DEMO_DATA_DIR="./data/demo"
DEMO_LOGS_DIR="./logs/demo"
DEMO_CONFIG_DIR="./config/demo"

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}======================================================${NC}"
    echo -e "${BLUE}  THE 7 SPACE DEMO DEPLOYMENT${NC}"
    echo -e "${BLUE}  HigherSelf Network Server Demo Environment${NC}"
    echo -e "${BLUE}======================================================${NC}"
    echo ""
}

print_status() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

setup_demo_environment() {
    print_info "Setting up demo environment..."
    
    # Create demo directories
    mkdir -p "$DEMO_DATA_DIR"
    mkdir -p "$DEMO_LOGS_DIR"
    mkdir -p "$DEMO_CONFIG_DIR"
    mkdir -p "$DEMO_LOGS_DIR/mongodb"
    mkdir -p "$DEMO_LOGS_DIR/redis"
    mkdir -p "$DEMO_LOGS_DIR/consul"
    mkdir -p "$DEMO_LOGS_DIR/prometheus"
    mkdir -p "$DEMO_LOGS_DIR/grafana"
    
    # Set proper permissions
    chmod 755 "$DEMO_DATA_DIR"
    chmod 755 "$DEMO_LOGS_DIR"
    chmod 755 "$DEMO_CONFIG_DIR"
    
    print_status "Demo directories created"
    
    # Check if demo environment file exists
    if [ ! -f "$DEMO_ENV_FILE" ]; then
        if [ -f ".env.demo.template" ]; then
            print_info "Creating demo environment file from template..."
            cp .env.demo.template "$DEMO_ENV_FILE"
            print_warning "Please edit $DEMO_ENV_FILE with your actual Notion API credentials"
            print_warning "Required: NOTION_API_TOKEN and database IDs"
        else
            print_error "Demo environment template not found. Please create $DEMO_ENV_FILE"
            exit 1
        fi
    fi
    
    print_status "Demo environment setup complete"
}

validate_configuration() {
    print_info "Validating demo configuration..."
    
    # Check if required environment variables are set
    if [ -f "$DEMO_ENV_FILE" ]; then
        source "$DEMO_ENV_FILE"
        
        if [ "$NOTION_API_TOKEN" = "secret_your_notion_token_here" ]; then
            print_error "Please set your actual Notion API token in $DEMO_ENV_FILE"
            exit 1
        fi
        
        if [ "$NOTION_PARENT_PAGE_ID" = "your_parent_page_id_here" ]; then
            print_warning "Notion parent page ID not set. Database creation may fail."
        fi
        
        print_status "Configuration validation passed"
    else
        print_error "Demo environment file $DEMO_ENV_FILE not found"
        exit 1
    fi
}

build_demo_images() {
    print_info "Building demo Docker images..."
    
    # Build the main application image with demo tag
    docker-compose -f "$DEMO_COMPOSE_FILE" build --no-cache
    
    if [ $? -eq 0 ]; then
        print_status "Demo images built successfully"
    else
        print_error "Failed to build demo images"
        exit 1
    fi
}

start_demo_services() {
    print_info "Starting demo services..."
    
    # Start all demo services
    docker-compose -f "$DEMO_COMPOSE_FILE" up -d
    
    if [ $? -eq 0 ]; then
        print_status "Demo services started successfully"
    else
        print_error "Failed to start demo services"
        exit 1
    fi
}

wait_for_services() {
    print_info "Waiting for services to be ready..."
    
    # Wait for MongoDB
    print_info "Waiting for MongoDB..."
    timeout 60 bash -c 'until docker-compose -f docker-compose.demo.yml exec -T mongodb-demo mongosh --eval "db.runCommand(\"ping\")" > /dev/null 2>&1; do sleep 2; done'
    
    # Wait for Redis
    print_info "Waiting for Redis..."
    timeout 30 bash -c 'until docker-compose -f docker-compose.demo.yml exec -T redis-demo redis-cli ping > /dev/null 2>&1; do sleep 2; done'
    
    # Wait for main application
    print_info "Waiting for The 7 Space Demo App..."
    timeout 90 bash -c 'until curl -f http://localhost:8000/health > /dev/null 2>&1; do sleep 3; done'
    
    print_status "All services are ready"
}

show_demo_info() {
    print_header
    print_status "THE 7 SPACE DEMO ENVIRONMENT IS READY!"
    echo ""
    print_info "Demo Services:"
    echo "  🎨 The 7 Space Demo App:    http://localhost:8000"
    echo "  📊 Grafana Dashboard:       http://localhost:3001 (admin/demo_admin_2024)"
    echo "  📈 Prometheus Metrics:      http://localhost:9091"
    echo "  🗄️  MongoDB:                localhost:27018"
    echo "  🔄 Redis:                   localhost:6380"
    echo "  🔍 Consul:                  http://localhost:8501"
    echo ""
    print_info "Demo Features Enabled:"
    echo "  ✅ Contact Management (191 The 7 Space contacts)"
    echo "  ✅ Workflow Automation"
    echo "  ✅ Lead Scoring & Qualification"
    echo "  ✅ Task Management"
    echo "  ✅ Artist Onboarding"
    echo "  ✅ Gallery Visitor Follow-up"
    echo "  ✅ Event Management"
    echo "  ✅ Wellness Program Enrollment"
    echo ""
    print_info "Next Steps:"
    echo "  1. Configure your Notion API credentials in $DEMO_ENV_FILE"
    echo "  2. Run: docker-compose -f $DEMO_COMPOSE_FILE restart the7space-demo"
    echo "  3. Access the demo at http://localhost:8000"
    echo "  4. Monitor with Grafana at http://localhost:3001"
    echo ""
    print_warning "This is a demo environment. Do not use in production!"
}

show_logs() {
    print_info "Showing demo service logs..."
    docker-compose -f "$DEMO_COMPOSE_FILE" logs -f
}

stop_demo() {
    print_info "Stopping demo services..."
    docker-compose -f "$DEMO_COMPOSE_FILE" down
    print_status "Demo services stopped"
}

cleanup_demo() {
    print_info "Cleaning up demo environment..."
    docker-compose -f "$DEMO_COMPOSE_FILE" down -v --remove-orphans
    docker system prune -f
    print_status "Demo environment cleaned up"
}

# Main execution
case "${1:-deploy}" in
    "deploy")
        print_header
        check_prerequisites
        setup_demo_environment
        validate_configuration
        build_demo_images
        start_demo_services
        wait_for_services
        show_demo_info
        ;;
    "start")
        print_info "Starting existing demo services..."
        docker-compose -f "$DEMO_COMPOSE_FILE" start
        wait_for_services
        show_demo_info
        ;;
    "stop")
        stop_demo
        ;;
    "restart")
        stop_demo
        sleep 2
        start_demo_services
        wait_for_services
        show_demo_info
        ;;
    "logs")
        show_logs
        ;;
    "status")
        print_info "Demo service status:"
        docker-compose -f "$DEMO_COMPOSE_FILE" ps
        ;;
    "cleanup")
        cleanup_demo
        ;;
    "rebuild")
        stop_demo
        build_demo_images
        start_demo_services
        wait_for_services
        show_demo_info
        ;;
    *)
        echo "Usage: $0 {deploy|start|stop|restart|logs|status|cleanup|rebuild}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full demo deployment (default)"
        echo "  start    - Start existing demo services"
        echo "  stop     - Stop demo services"
        echo "  restart  - Restart demo services"
        echo "  logs     - Show service logs"
        echo "  status   - Show service status"
        echo "  cleanup  - Remove demo environment completely"
        echo "  rebuild  - Rebuild and restart demo"
        exit 1
        ;;
esac
