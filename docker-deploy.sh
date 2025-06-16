#!/bin/bash

# HigherSelf Network Server - Docker Deployment Script
# Quick deployment script for Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ACTION="${1:-up}"
ENVIRONMENT="${2:-development}"

echo -e "${BLUE}🐳 HigherSelf Network Server - Docker Deployment${NC}"
echo -e "${BLUE}Action: ${YELLOW}$ACTION${NC}"
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

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo -n "Waiting for $service_name to be ready... "
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo ""
            print_status "$service_name is ready"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo ""
    print_warning "$service_name may not be ready yet (timeout after ${max_attempts} attempts)"
    return 1
}

# Validate action
case $ACTION in
    "up"|"start"|"deploy")
        ACTION="up"
        ;;
    "down"|"stop"|"destroy")
        ACTION="down"
        ;;
    "restart"|"reload")
        ACTION="restart"
        ;;
    "logs"|"log")
        ACTION="logs"
        ;;
    "status"|"ps")
        ACTION="ps"
        ;;
    "build")
        ACTION="build"
        ;;
    *)
        print_error "Invalid action: $ACTION"
        echo "Usage: $0 [up|down|restart|logs|status|build] [environment]"
        echo ""
        echo "Actions:"
        echo "  up/start/deploy  - Start all services"
        echo "  down/stop        - Stop all services"
        echo "  restart          - Restart all services"
        echo "  logs             - Show service logs"
        echo "  status/ps        - Show service status"
        echo "  build            - Build Docker images"
        exit 1
        ;;
esac

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi
print_status "Docker is running"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    echo "Please install Docker Compose"
    exit 1
fi
print_status "Docker Compose is available"

# Check .env file
if [[ ! -f ".env" ]]; then
    print_warning ".env file not found"
    
    if [[ -f ".env.docker.example" ]]; then
        print_info "Creating .env from template..."
        cp .env.docker.example .env
        print_status ".env file created"
        print_warning "Please edit .env with your actual values"
    else
        print_error "No .env template found"
        exit 1
    fi
else
    print_status ".env file found"
fi

# Execute action
echo ""
echo -e "${BLUE}Executing Docker action: $ACTION${NC}"

case $ACTION in
    "up")
        # Build images first
        echo "Building Docker images..."
        if docker-compose build; then
            print_status "Images built successfully"
        else
            print_error "Failed to build images"
            exit 1
        fi
        
        # Start services
        echo "Starting services..."
        if docker-compose up -d; then
            print_status "Services started successfully"
        else
            print_error "Failed to start services"
            exit 1
        fi
        
        # Wait for services to be ready
        echo ""
        echo -e "${BLUE}Waiting for services to be ready...${NC}"
        sleep 5
        
        # Health checks
        wait_for_service "HigherSelf Network Server" "http://localhost:8000/health"
        wait_for_service "MongoDB" "http://localhost:27017" || true
        wait_for_service "Redis" "http://localhost:6379" || true
        wait_for_service "Prometheus" "http://localhost:9090/-/ready" || true
        wait_for_service "Grafana" "http://localhost:3000/api/health" || true
        wait_for_service "Consul" "http://localhost:8500/v1/status/leader" || true
        
        # Show service status
        echo ""
        echo -e "${BLUE}Service Status:${NC}"
        docker-compose ps
        
        # Show service endpoints
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
        echo -e "${BLUE}Useful Commands:${NC}"
        echo "• View logs: docker-compose logs -f windsurf-agent"
        echo "• Check status: docker-compose ps"
        echo "• Stop services: ./docker-deploy.sh down"
        echo "• Restart services: ./docker-deploy.sh restart"
        ;;
    "down")
        echo "Stopping services..."
        if docker-compose down; then
            print_status "Services stopped successfully"
        else
            print_error "Failed to stop services"
            exit 1
        fi
        ;;
    "restart")
        echo "Restarting services..."
        if docker-compose restart; then
            print_status "Services restarted successfully"
        else
            print_error "Failed to restart services"
            exit 1
        fi
        ;;
    "logs")
        echo "Showing service logs..."
        docker-compose logs -f
        ;;
    "ps")
        echo "Service status:"
        docker-compose ps
        echo ""
        echo "Resource usage:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | head -10
        ;;
    "build")
        echo "Building Docker images..."
        if docker-compose build --no-cache; then
            print_status "Images built successfully"
        else
            print_error "Failed to build images"
            exit 1
        fi
        ;;
esac

echo ""
echo -e "${GREEN}Docker deployment script completed!${NC}"
