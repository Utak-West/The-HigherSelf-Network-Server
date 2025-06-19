#!/bin/bash

# ======================================================
# HIGHERSELF NETWORK SERVER - VM DEPLOYMENT MONITOR
# Real-time monitoring script for deployment progress
# ======================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
VM_COMPOSE_FILE="docker-compose.vm.yml"
MONITOR_INTERVAL=5
MAX_WAIT_TIME=1800  # 30 minutes

print_header() {
    echo ""
    echo -e "${BLUE}======================================================${NC}"
    echo -e "${BLUE}  HIGHERSELF NETWORK SERVER - DEPLOYMENT MONITOR${NC}"
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

check_docker_status() {
    print_info "Checking Docker status..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running"
        return 1
    fi
    
    print_status "Docker is running"
    return 0
}

check_compose_file() {
    print_info "Checking Docker Compose configuration..."
    
    if [ ! -f "$VM_COMPOSE_FILE" ]; then
        print_error "Docker Compose file not found: $VM_COMPOSE_FILE"
        return 1
    fi
    
    if ! docker-compose -f "$VM_COMPOSE_FILE" config &> /dev/null; then
        print_error "Docker Compose configuration is invalid"
        return 1
    fi
    
    print_status "Docker Compose configuration is valid"
    return 0
}

monitor_service_health() {
    local service_name=$1
    local max_attempts=60
    local attempt=0
    
    print_info "Monitoring $service_name health..."
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f "$VM_COMPOSE_FILE" ps "$service_name" | grep -q "Up (healthy)"; then
            print_status "$service_name is healthy"
            return 0
        elif docker-compose -f "$VM_COMPOSE_FILE" ps "$service_name" | grep -q "Up"; then
            print_info "$service_name is starting... (attempt $((attempt + 1))/$max_attempts)"
        else
            print_warning "$service_name is not running"
        fi
        
        sleep $MONITOR_INTERVAL
        ((attempt++))
    done
    
    print_error "$service_name failed to become healthy within timeout"
    return 1
}

monitor_all_services() {
    print_info "Monitoring all VM services..."
    
    local services=(
        "mongodb-vm"
        "redis-vm"
        "consul-vm"
        "higherself-server"
        "prometheus-vm"
        "grafana-vm"
        "nginx-vm"
    )
    
    for service in "${services[@]}"; do
        monitor_service_health "$service"
    done
}

check_service_endpoints() {
    print_info "Checking service endpoints..."
    
    # Check main application
    if curl -f http://localhost/health &> /dev/null; then
        print_status "Main application is responding"
    else
        print_warning "Main application is not responding"
    fi
    
    # Check Grafana
    if curl -f http://localhost:3000/api/health &> /dev/null; then
        print_status "Grafana is responding"
    else
        print_warning "Grafana is not responding"
    fi
    
    # Check Prometheus
    if curl -f http://localhost:9090/-/ready &> /dev/null; then
        print_status "Prometheus is responding"
    else
        print_warning "Prometheus is not responding"
    fi
    
    # Check Consul
    if curl -f http://localhost:8500/v1/status/leader &> /dev/null; then
        print_status "Consul is responding"
    else
        print_warning "Consul is not responding"
    fi
}

show_deployment_status() {
    print_header
    print_info "Current deployment status:"
    echo ""
    
    # Show container status
    docker-compose -f "$VM_COMPOSE_FILE" ps
    echo ""
    
    # Show resource usage
    print_info "Resource usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
    echo ""
    
    # Show logs summary
    print_info "Recent logs (last 10 lines per service):"
    docker-compose -f "$VM_COMPOSE_FILE" logs --tail=10
}

show_access_info() {
    print_info "Service access information:"
    echo "  🌐 Main Application:         http://192.168.1.100"
    echo "  📊 Grafana Dashboard:        http://192.168.1.100:3000"
    echo "  📈 Prometheus Metrics:       http://192.168.1.100:9090"
    echo "  🔍 Consul Service Discovery: http://192.168.1.100:8500"
    echo ""
    print_info "Default credentials:"
    echo "  Grafana: admin / HigherSelf2024Grafana!"
}

# Main execution
case "${1:-status}" in
    "monitor")
        print_header
        check_docker_status
        check_compose_file
        monitor_all_services
        check_service_endpoints
        show_access_info
        ;;
    "status")
        show_deployment_status
        ;;
    "health")
        check_service_endpoints
        ;;
    "logs")
        docker-compose -f "$VM_COMPOSE_FILE" logs -f
        ;;
    *)
        echo "Usage: $0 {monitor|status|health|logs}"
        echo ""
        echo "Commands:"
        echo "  monitor  - Monitor deployment progress"
        echo "  status   - Show current status"
        echo "  health   - Check service health"
        echo "  logs     - Show service logs"
        exit 1
        ;;
esac
