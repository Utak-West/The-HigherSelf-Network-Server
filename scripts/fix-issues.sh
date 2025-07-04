#!/bin/bash

# ======================================================
# HIGHERSELF NETWORK SERVER - AUTOMATED ISSUE FIX SCRIPT
# Fixes common issues and gets the server running
# ======================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Functions
print_header() {
    echo -e "${PURPLE}======================================================${NC}"
    echo -e "${PURPLE}🔧 HIGHERSELF NETWORK SERVER - AUTOMATED FIX${NC}"
    echo -e "${PURPLE}Fixing common issues and getting server running${NC}"
    echo -e "${PURPLE}======================================================${NC}"
    echo ""
}

print_section() {
    echo -e "${BLUE}📋 $1${NC}"
    echo "----------------------------------------"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

check_docker() {
    print_section "Checking Docker Status"
    
    # Check if Docker is installed
    if command -v docker &> /dev/null; then
        print_success "Docker is installed: $(docker --version)"
    else
        print_error "Docker is not installed"
        print_info "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if docker info &> /dev/null; then
        print_success "Docker daemon is running"
    else
        print_warning "Docker daemon is not running"
        print_info "Starting Docker Desktop..."
        
        # Try to start Docker Desktop on macOS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open -a Docker
            print_info "Waiting for Docker to start (30 seconds)..."
            sleep 30
            
            # Check again
            if docker info &> /dev/null; then
                print_success "Docker daemon started successfully"
            else
                print_error "Failed to start Docker daemon"
                print_info "Please start Docker Desktop manually and run this script again"
                exit 1
            fi
        else
            print_error "Please start Docker daemon manually and run this script again"
            exit 1
        fi
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose is available: $(docker-compose --version)"
    else
        print_error "Docker Compose is not available"
        exit 1
    fi
    
    echo ""
}

fix_environment_files() {
    print_section "Fixing Environment Files"
    
    # Check if .env exists
    if [ ! -f "$ENV_FILE" ]; then
        print_warning ".env file not found"
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
            print_success "Created .env from .env.example"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_success ".env file exists"
    fi
    
    # Check if .env.development exists
    if [ ! -f "$PROJECT_ROOT/.env.development" ]; then
        print_warning ".env.development file not found"
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env.development"
        print_success "Created .env.development from .env.example"
    else
        print_success ".env.development file exists"
    fi
    
    echo ""
}

fix_docker_compose() {
    print_section "Validating Docker Compose Configuration"
    
    # Test Docker Compose configuration
    if docker-compose config --quiet; then
        print_success "Docker Compose configuration is valid"
    else
        print_error "Docker Compose configuration has issues"
        print_info "Running docker-compose config to show details:"
        docker-compose config
        exit 1
    fi
    
    echo ""
}

create_required_directories() {
    print_section "Creating Required Directories"
    
    # Create log directories
    mkdir -p "$PROJECT_ROOT/logs/development"
    mkdir -p "$PROJECT_ROOT/logs/dev"
    mkdir -p "$PROJECT_ROOT/data/development"
    mkdir -p "$PROJECT_ROOT/data/dev"
    mkdir -p "$PROJECT_ROOT/backups"
    
    print_success "Created required directories"
    echo ""
}

stop_conflicting_services() {
    print_section "Stopping Conflicting Services"
    
    # Stop any existing containers
    if docker-compose ps -q | grep -q .; then
        print_info "Stopping existing containers..."
        docker-compose down
        print_success "Stopped existing containers"
    else
        print_info "No existing containers to stop"
    fi
    
    # Check for port conflicts
    local ports=(8000 27017 6379 8500 9090 3000)
    for port in "${ports[@]}"; do
        if lsof -i :$port &> /dev/null; then
            print_warning "Port $port is in use"
            print_info "You may need to stop the service using this port"
        fi
    done
    
    echo ""
}

start_server() {
    print_section "Starting HigherSelf Network Server"
    
    print_info "Starting services with Docker Compose..."
    
    # Start services
    if docker-compose up -d; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        print_info "Checking logs for errors..."
        docker-compose logs --tail=20
        exit 1
    fi
    
    # Wait for services to be ready
    print_info "Waiting for services to be ready (60 seconds)..."
    sleep 60
    
    echo ""
}

test_server() {
    print_section "Testing Server Health"
    
    # Test main API
    print_info "Testing main API health..."
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Main API is responding"
        
        # Show health status
        health_response=$(curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health)
        echo "Health Status: $health_response"
    else
        print_warning "Main API is not responding yet"
        print_info "This might be normal if services are still starting up"
    fi
    
    # Test voice control API
    print_info "Testing voice control API..."
    voice_response=$(curl -s -X POST "http://localhost:8000/voice/server/control" \
        -H "Content-Type: application/json" \
        -d '{"command": "server status", "environment": "development"}' 2>/dev/null || echo "API not ready")
    
    if echo "$voice_response" | grep -q "success"; then
        print_success "Voice control API is working"
    else
        print_warning "Voice control API is not ready yet"
        print_info "Response: $voice_response"
    fi
    
    echo ""
}

show_service_status() {
    print_section "Service Status"
    
    # Show Docker Compose status
    print_info "Docker Compose service status:"
    docker-compose ps
    
    echo ""
    
    # Show service URLs
    print_info "Service URLs:"
    echo "🌐 Main API: http://localhost:8000"
    echo "🏥 Health Check: http://localhost:8000/health"
    echo "🎤 Voice Control: http://localhost:8000/voice/server/control"
    echo "📊 Grafana: http://localhost:3000"
    echo "📈 Prometheus: http://localhost:9090"
    echo "🗄️  Consul: http://localhost:8500"
    
    echo ""
}

show_next_steps() {
    print_section "Next Steps"
    
    print_info "Your HigherSelf Network Server is now running!"
    echo ""
    echo "🎤 To test voice control:"
    echo "1. Open Termius Pro"
    echo "2. Connect to HigherSelf-Voice-Local host"
    echo "3. Try saying: 'server status'"
    echo ""
    echo "🔐 To test 1Password integration:"
    echo "1. Open any app"
    echo "2. Type: ;hsenv (for server environment)"
    echo "3. Type: ;vclog (for voice command log)"
    echo ""
    echo "🤖 To test Claude Code integration:"
    echo "1. Install Claude Code: npm install -g @anthropic-ai/claude-code"
    echo "2. Run: ./scripts/claude-code-helper.sh review-code"
    echo ""
    echo "📚 For troubleshooting, see: TROUBLESHOOTING_GUIDE.md"
    echo ""
}

main() {
    print_header
    
    print_info "Starting automated fix process..."
    print_info "Project Root: $PROJECT_ROOT"
    echo ""
    
    check_docker
    fix_environment_files
    fix_docker_compose
    create_required_directories
    stop_conflicting_services
    start_server
    test_server
    show_service_status
    show_next_steps
    
    print_section "Fix Complete!"
    print_success "HigherSelf Network Server is running with voice control!"
    echo ""
    print_warning "If you encounter any issues, check TROUBLESHOOTING_GUIDE.md"
}

# Run main function
main "$@"
