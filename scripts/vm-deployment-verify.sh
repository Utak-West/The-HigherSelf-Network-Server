#!/bin/bash

# ======================================================
# HIGHERSELF NETWORK SERVER - VM DEPLOYMENT VERIFICATION
# Comprehensive verification script for VM deployment
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
VM_IP="192.168.1.100"
VERIFICATION_TIMEOUT=30

print_header() {
    echo ""
    echo -e "${BLUE}======================================================${NC}"
    echo -e "${BLUE}  HIGHERSELF NETWORK SERVER - DEPLOYMENT VERIFICATION${NC}"
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

print_section() {
    echo -e "${PURPLE}▶ $1${NC}"
}

verify_container_status() {
    print_section "Verifying container status..."
    
    local containers=(
        "higherself-server-vm"
        "higherself-mongodb-vm"
        "higherself-redis-vm"
        "higherself-consul-vm"
        "higherself-prometheus-vm"
        "higherself-grafana-vm"
        "higherself-nginx-vm"
    )
    
    local all_healthy=true
    
    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
            if docker inspect "$container" --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy\|starting"; then
                print_status "$container is running and healthy"
            else
                print_warning "$container is running but health status unknown"
            fi
        else
            print_error "$container is not running"
            all_healthy=false
        fi
    done
    
    return $all_healthy
}

verify_network_connectivity() {
    print_section "Verifying network connectivity..."
    
    # Test main application
    if curl -f -s --max-time $VERIFICATION_TIMEOUT "http://localhost/health" > /dev/null; then
        print_status "Main application health endpoint accessible"
    else
        print_error "Main application health endpoint not accessible"
        return 1
    fi
    
    # Test Grafana
    if curl -f -s --max-time $VERIFICATION_TIMEOUT "http://localhost:3000/api/health" > /dev/null; then
        print_status "Grafana API accessible"
    else
        print_error "Grafana API not accessible"
    fi
    
    # Test Prometheus
    if curl -f -s --max-time $VERIFICATION_TIMEOUT "http://localhost:9090/-/ready" > /dev/null; then
        print_status "Prometheus ready endpoint accessible"
    else
        print_error "Prometheus ready endpoint not accessible"
    fi
    
    # Test Consul
    if curl -f -s --max-time $VERIFICATION_TIMEOUT "http://localhost:8500/v1/status/leader" > /dev/null; then
        print_status "Consul leader endpoint accessible"
    else
        print_error "Consul leader endpoint not accessible"
    fi
}

verify_database_connectivity() {
    print_section "Verifying database connectivity..."
    
    # Test MongoDB
    if docker-compose -f "$VM_COMPOSE_FILE" exec -T mongodb-vm mongosh --eval "db.runCommand('ping')" > /dev/null 2>&1; then
        print_status "MongoDB is accessible and responding"
    else
        print_error "MongoDB is not accessible"
    fi
    
    # Test Redis
    if docker-compose -f "$VM_COMPOSE_FILE" exec -T redis-vm redis-cli ping > /dev/null 2>&1; then
        print_status "Redis is accessible and responding"
    else
        print_error "Redis is not accessible"
    fi
}

verify_business_entity_configuration() {
    print_section "Verifying business entity configuration..."
    
    # Check if environment variables are properly set
    if docker-compose -f "$VM_COMPOSE_FILE" exec -T higherself-server printenv | grep -q "MULTI_ENTITY_MODE=true"; then
        print_status "Multi-entity mode is enabled"
    else
        print_warning "Multi-entity mode configuration not verified"
    fi
    
    # Check business entity flags
    local entities=("THE_7_SPACE_ENABLED" "AM_CONSULTING_ENABLED" "HIGHERSELF_CORE_ENABLED")
    for entity in "${entities[@]}"; do
        if docker-compose -f "$VM_COMPOSE_FILE" exec -T higherself-server printenv | grep -q "$entity=true"; then
            print_status "$entity is enabled"
        else
            print_warning "$entity configuration not verified"
        fi
    done
}

verify_monitoring_stack() {
    print_section "Verifying monitoring stack..."
    
    # Check Prometheus targets
    local prometheus_targets=$(curl -s "http://localhost:9090/api/v1/targets" | grep -o '"health":"up"' | wc -l)
    if [ "$prometheus_targets" -gt 0 ]; then
        print_status "Prometheus has $prometheus_targets healthy targets"
    else
        print_warning "Prometheus targets not verified"
    fi
    
    # Check Grafana datasources
    if curl -s -u "admin:HigherSelf2024Grafana!" "http://localhost:3000/api/datasources" | grep -q "prometheus"; then
        print_status "Grafana Prometheus datasource configured"
    else
        print_warning "Grafana datasource configuration not verified"
    fi
}

verify_security_configuration() {
    print_section "Verifying security configuration..."
    
    # Check firewall status
    if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
        print_status "UFW firewall is active"
    else
        print_warning "UFW firewall status not verified"
    fi
    
    # Check SSL certificates
    if [ -f "./ssl/cert.pem" ] && [ -f "./ssl/key.pem" ]; then
        print_status "SSL certificates are present"
    else
        print_warning "SSL certificates not found"
    fi
}

verify_backup_configuration() {
    print_section "Verifying backup configuration..."
    
    # Check backup directories
    if [ -d "./backups" ]; then
        print_status "Backup directory exists"
    else
        print_warning "Backup directory not found"
    fi
    
    # Check backup service
    if docker ps --filter "name=higherself-backup-vm" --filter "status=running" | grep -q "higherself-backup-vm"; then
        print_status "Backup service is running"
    else
        print_warning "Backup service not running"
    fi
}

show_deployment_summary() {
    print_section "Deployment Summary"
    echo ""
    print_info "Service URLs:"
    echo "  🌐 Main Application:         http://$VM_IP"
    echo "  📊 Grafana Dashboard:        http://$VM_IP:3000"
    echo "  📈 Prometheus Metrics:       http://$VM_IP:9090"
    echo "  🔍 Consul Service Discovery: http://$VM_IP:8500"
    echo ""
    print_info "Business Entities Configured:"
    echo "  🎨 The 7 Space (Gallery/Wellness)"
    echo "  💼 AM Consulting (Business Services)"
    echo "  🌟 HigherSelf Core (Community Platform)"
    echo ""
    print_info "Default Credentials:"
    echo "  Grafana: admin / HigherSelf2024Grafana!"
    echo ""
    print_info "Next Steps:"
    echo "  1. Configure actual Notion API tokens"
    echo "  2. Import business entity contacts"
    echo "  3. Set up automation workflows"
    echo "  4. Configure monitoring alerts"
}

run_comprehensive_verification() {
    print_header
    
    local verification_passed=true
    
    verify_container_status || verification_passed=false
    verify_network_connectivity || verification_passed=false
    verify_database_connectivity || verification_passed=false
    verify_business_entity_configuration || verification_passed=false
    verify_monitoring_stack || verification_passed=false
    verify_security_configuration || verification_passed=false
    verify_backup_configuration || verification_passed=false
    
    echo ""
    if [ "$verification_passed" = true ]; then
        print_status "All verification checks passed!"
    else
        print_warning "Some verification checks failed. Review the output above."
    fi
    
    show_deployment_summary
}

# Main execution
case "${1:-verify}" in
    "verify")
        run_comprehensive_verification
        ;;
    "containers")
        verify_container_status
        ;;
    "network")
        verify_network_connectivity
        ;;
    "databases")
        verify_database_connectivity
        ;;
    "monitoring")
        verify_monitoring_stack
        ;;
    "security")
        verify_security_configuration
        ;;
    *)
        echo "Usage: $0 {verify|containers|network|databases|monitoring|security}"
        echo ""
        echo "Commands:"
        echo "  verify      - Run comprehensive verification"
        echo "  containers  - Check container status"
        echo "  network     - Test network connectivity"
        echo "  databases   - Test database connectivity"
        echo "  monitoring  - Check monitoring stack"
        echo "  security    - Verify security configuration"
        exit 1
        ;;
esac
