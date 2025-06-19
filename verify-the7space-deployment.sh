#!/bin/bash

# ======================================================
# The 7 Space Deployment Verification Script
# Comprehensive verification for The 7 Space production deployment
# ======================================================

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
LOG_FILE="$PROJECT_ROOT/logs/the7space-verification-$(date +%Y%m%d_%H%M%S).log"
DEPLOYMENT_CONFIG="docker-compose.the7space.prod.yml"
ENV_FILE=".env.the7space.production"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Verification results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
    ((PASSED_CHECKS++))
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
    ((WARNING_CHECKS++))
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
    ((FAILED_CHECKS++))
}

log_info() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')] ℹ️  $1${NC}" | tee -a "$LOG_FILE"
}

log_header() {
    echo -e "${PURPLE}[$(date +'%Y-%m-%d %H:%M:%S')] 🎨 $1${NC}" | tee -a "$LOG_FILE"
}

# Increment total checks counter
check_start() {
    ((TOTAL_CHECKS++))
}

# Print verification header
print_header() {
    echo ""
    echo -e "${PURPLE}======================================================${NC}"
    echo -e "${PURPLE}🎨 THE 7 SPACE DEPLOYMENT VERIFICATION${NC}"
    echo -e "${PURPLE}   Art Gallery & Wellness Center Production Verification${NC}"
    echo -e "${PURPLE}======================================================${NC}"
    echo ""
    log_header "Starting The 7 Space deployment verification"
    log_info "Verification log: $LOG_FILE"
    echo ""
}

# Verify prerequisites
verify_prerequisites() {
    log_info "Verifying prerequisites..."
    
    # Check required commands
    local required_commands=("docker" "docker-compose" "curl" "jq" "python3")
    for cmd in "${required_commands[@]}"; do
        check_start
        if command -v "$cmd" &> /dev/null; then
            log_success "Command available: $cmd"
        else
            log_error "Required command not found: $cmd"
        fi
    done
    
    # Check deployment files
    local required_files=("$DEPLOYMENT_CONFIG" "$ENV_FILE")
    for file in "${required_files[@]}"; do
        check_start
        if [ -f "$file" ]; then
            log_success "File exists: $file"
        else
            log_error "Required file not found: $file"
        fi
    done
}

# Verify Docker services
verify_docker_services() {
    log_info "Verifying Docker services..."
    
    # Check if Docker is running
    check_start
    if docker info &> /dev/null; then
        log_success "Docker daemon is running"
    else
        log_error "Docker daemon is not running"
        return 1
    fi
    
    # Check Docker Compose services
    check_start
    if [ -f "$DEPLOYMENT_CONFIG" ]; then
        local service_status
        service_status=$(docker-compose -f "$DEPLOYMENT_CONFIG" ps --format "table {{.Name}}\t{{.State}}\t{{.Status}}" 2>/dev/null || echo "FAILED")
        
        if [ "$service_status" != "FAILED" ]; then
            log_success "Docker Compose services accessible"
            log_info "Service Status:"
            echo "$service_status" | tee -a "$LOG_FILE"
            
            # Count running services
            local running_count
            running_count=$(docker-compose -f "$DEPLOYMENT_CONFIG" ps -q --filter "status=running" | wc -l)
            local total_count
            total_count=$(docker-compose -f "$DEPLOYMENT_CONFIG" ps -q | wc -l)
            
            check_start
            if [ "$running_count" -eq "$total_count" ] && [ "$total_count" -gt 0 ]; then
                log_success "All services are running ($running_count/$total_count)"
            else
                log_warning "Some services may not be running ($running_count/$total_count)"
            fi
        else
            log_error "Failed to get Docker Compose service status"
        fi
    else
        log_error "Docker Compose file not found: $DEPLOYMENT_CONFIG"
    fi
}

# Verify service health
verify_service_health() {
    log_info "Verifying service health..."
    
    local base_url="http://localhost:8000"
    local timeout=30
    
    # Main health check
    check_start
    local health_response
    health_response=$(curl -s -w "%{http_code}" -o /tmp/health_response.json --max-time $timeout "$base_url/health" 2>/dev/null || echo "000")
    
    if [ "$health_response" = "200" ]; then
        log_success "Main application health check passed"
        
        # Parse health response
        if [ -f "/tmp/health_response.json" ]; then
            local app_status
            app_status=$(jq -r '.status // "unknown"' /tmp/health_response.json 2>/dev/null || echo "unknown")
            log_info "Application status: $app_status"
        fi
    else
        log_error "Main application health check failed (HTTP: $health_response)"
    fi
    
    # Database health check
    check_start
    local db_health_response
    db_health_response=$(curl -s -w "%{http_code}" -o /tmp/db_health_response.json --max-time $timeout "$base_url/health/database" 2>/dev/null || echo "000")
    
    if [ "$db_health_response" = "200" ]; then
        log_success "Database health check passed"
    else
        log_warning "Database health check failed or not available (HTTP: $db_health_response)"
    fi
    
    # External services health check
    check_start
    local ext_health_response
    ext_health_response=$(curl -s -w "%{http_code}" -o /tmp/ext_health_response.json --max-time $timeout "$base_url/health/external" 2>/dev/null || echo "000")
    
    if [ "$ext_health_response" = "200" ]; then
        log_success "External services health check passed"
    else
        log_warning "External services health check failed or not available (HTTP: $ext_health_response)"
    fi
    
    # Clean up temporary files
    rm -f /tmp/health_response.json /tmp/db_health_response.json /tmp/ext_health_response.json
}

# Verify The 7 Space functionality
verify_the7space_functionality() {
    log_info "Verifying The 7 Space specific functionality..."
    
    local base_url="http://localhost:8000"
    local timeout=30
    
    # The 7 Space API endpoints
    local endpoints=(
        "/api/the7space/health:The 7 Space API Health"
        "/api/the7space/contacts/health:Contact Management"
        "/api/the7space/workflows/health:Workflow Automation"
        "/api/the7space/gallery/health:Gallery Management"
        "/api/the7space/wellness/health:Wellness Center"
    )
    
    for endpoint_info in "${endpoints[@]}"; do
        local endpoint="${endpoint_info%%:*}"
        local description="${endpoint_info##*:}"
        
        check_start
        local response_code
        response_code=$(curl -s -w "%{http_code}" -o /dev/null --max-time $timeout "$base_url$endpoint" 2>/dev/null || echo "000")
        
        if [ "$response_code" = "200" ]; then
            log_success "$description endpoint is accessible"
        elif [ "$response_code" = "404" ]; then
            log_warning "$description endpoint not found (may not be implemented yet)"
        else
            log_warning "$description endpoint returned HTTP $response_code"
        fi
    done
}

# Verify integrations
verify_integrations() {
    log_info "Verifying external integrations..."
    
    # Check environment variables for integration configuration
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
        
        # Notion integration
        check_start
        if [ -n "${NOTION_API_TOKEN:-}" ] && [ "$NOTION_API_TOKEN" != "CHANGE_IN_PRODUCTION_NOTION_TOKEN" ]; then
            log_success "Notion API token is configured"
        else
            log_warning "Notion API token not configured or using default value"
        fi
        
        # WordPress integration
        check_start
        if [ -n "${THE_7_SPACE_WORDPRESS_URL:-}" ] && [ "$THE_7_SPACE_WORDPRESS_URL" != "https://the7space.com" ]; then
            log_success "WordPress URL is configured"
        else
            log_warning "WordPress URL not configured or using default value"
        fi
        
        # OpenAI integration
        check_start
        if [ -n "${OPENAI_API_KEY:-}" ] && [ "$OPENAI_API_KEY" != "CHANGE_IN_PRODUCTION_OPENAI_KEY" ]; then
            log_success "OpenAI API key is configured"
        else
            log_warning "OpenAI API key not configured or using default value"
        fi
    else
        log_error "Environment file not found: $ENV_FILE"
    fi
}

# Verify monitoring and observability
verify_monitoring() {
    log_info "Verifying monitoring and observability..."
    
    # Prometheus
    check_start
    local prometheus_response
    prometheus_response=$(curl -s -w "%{http_code}" -o /dev/null --max-time 15 "http://localhost:9090/-/healthy" 2>/dev/null || echo "000")
    
    if [ "$prometheus_response" = "200" ]; then
        log_success "Prometheus is accessible and healthy"
    else
        log_warning "Prometheus not accessible (HTTP: $prometheus_response)"
    fi
    
    # Grafana
    check_start
    local grafana_response
    grafana_response=$(curl -s -w "%{http_code}" -o /dev/null --max-time 15 "http://localhost:3000/api/health" 2>/dev/null || echo "000")
    
    if [ "$grafana_response" = "200" ]; then
        log_success "Grafana is accessible and healthy"
    else
        log_warning "Grafana not accessible (HTTP: $grafana_response)"
    fi
    
    # Consul
    check_start
    local consul_response
    consul_response=$(curl -s -w "%{http_code}" -o /dev/null --max-time 15 "http://localhost:8500/v1/status/leader" 2>/dev/null || echo "000")
    
    if [ "$consul_response" = "200" ]; then
        log_success "Consul is accessible and healthy"
    else
        log_warning "Consul not accessible (HTTP: $consul_response)"
    fi
}

# Run integration tests
run_integration_tests() {
    log_info "Running integration tests..."
    
    check_start
    if [ -f "testing/the7space/test_deployment_integration.py" ]; then
        log_info "Running Python integration tests..."
        
        if python3 testing/the7space/test_deployment_integration.py > /tmp/integration_test_output.log 2>&1; then
            log_success "Integration tests passed"
            
            # Show test summary
            if grep -q "Test Summary:" /tmp/integration_test_output.log; then
                log_info "Integration test summary:"
                grep -A 10 "Test Summary:" /tmp/integration_test_output.log | tee -a "$LOG_FILE"
            fi
        else
            log_error "Integration tests failed"
            log_info "Integration test output:"
            tail -20 /tmp/integration_test_output.log | tee -a "$LOG_FILE"
        fi
        
        # Clean up
        rm -f /tmp/integration_test_output.log
    else
        log_warning "Integration test script not found"
    fi
}

# Verify performance
verify_performance() {
    log_info "Verifying performance metrics..."
    
    local base_url="http://localhost:8000"
    
    # Response time test
    check_start
    local start_time
    start_time=$(date +%s.%N)
    
    local response_code
    response_code=$(curl -s -w "%{http_code}" -o /dev/null --max-time 30 "$base_url/health" 2>/dev/null || echo "000")
    
    local end_time
    end_time=$(date +%s.%N)
    
    local response_time
    response_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
    
    if [ "$response_code" = "200" ]; then
        if (( $(echo "$response_time < 1.0" | bc -l 2>/dev/null || echo "0") )); then
            log_success "Response time is acceptable: ${response_time}s"
        else
            log_warning "Response time is slow: ${response_time}s (target: <1.0s)"
        fi
    else
        log_error "Performance test failed (HTTP: $response_code)"
    fi
}

# Verify security configuration
verify_security() {
    log_info "Verifying security configuration..."
    
    # Check if sensitive files have proper permissions
    check_start
    if [ -f "$ENV_FILE" ]; then
        local file_perms
        file_perms=$(stat -c "%a" "$ENV_FILE" 2>/dev/null || stat -f "%A" "$ENV_FILE" 2>/dev/null || echo "unknown")
        
        if [ "$file_perms" = "600" ] || [ "$file_perms" = "0600" ]; then
            log_success "Environment file has secure permissions"
        else
            log_warning "Environment file permissions should be 600 (current: $file_perms)"
        fi
    fi
    
    # Check for default passwords in environment file
    check_start
    if [ -f "$ENV_FILE" ]; then
        local default_passwords=("CHANGE_IN_PRODUCTION" "password" "admin" "secret")
        local found_defaults=false
        
        for default_pass in "${default_passwords[@]}"; do
            if grep -q "$default_pass" "$ENV_FILE" 2>/dev/null; then
                found_defaults=true
                break
            fi
        done
        
        if [ "$found_defaults" = false ]; then
            log_success "No default passwords found in environment file"
        else
            log_error "Default passwords found in environment file - please change them"
        fi
    fi
}

# Generate verification report
generate_verification_report() {
    local total_time=$(($(date +%s) - START_TIME))
    
    echo ""
    log_header "THE 7 SPACE DEPLOYMENT VERIFICATION COMPLETED"
    echo ""
    log_info "Verification Summary:"
    echo "  📊 Total Checks: $TOTAL_CHECKS"
    echo "  ✅ Passed: $PASSED_CHECKS"
    echo "  ❌ Failed: $FAILED_CHECKS"
    echo "  ⚠️  Warnings: $WARNING_CHECKS"
    echo "  ⏱️  Duration: ${total_time}s"
    echo ""
    
    # Calculate success rate
    local success_rate=0
    if [ "$TOTAL_CHECKS" -gt 0 ]; then
        success_rate=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
    fi
    
    echo "  📈 Success Rate: ${success_rate}%"
    echo ""
    
    # Determine overall status
    if [ "$FAILED_CHECKS" -eq 0 ]; then
        if [ "$WARNING_CHECKS" -eq 0 ]; then
            log_success "ALL VERIFICATIONS PASSED! The 7 Space is ready for production."
        else
            log_warning "Verification completed with warnings. Review warnings before production use."
        fi
        echo ""
        log_info "Next Steps:"
        echo "  1. Review any warnings above"
        echo "  2. Configure any missing integrations"
        echo "  3. Set up monitoring alerts"
        echo "  4. Schedule regular health checks"
        echo "  5. Document deployment procedures"
    else
        log_error "VERIFICATION FAILED! Please address the failed checks before production use."
        echo ""
        log_info "Required Actions:"
        echo "  1. Fix all failed checks"
        echo "  2. Re-run verification"
        echo "  3. Address any warnings"
        echo "  4. Test all functionality manually"
    fi
    
    echo ""
    log_info "Verification log saved to: $LOG_FILE"
    echo ""
    
    # Return appropriate exit code
    if [ "$FAILED_CHECKS" -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Main verification function
main() {
    # Record start time
    START_TIME=$(date +%s)
    
    print_header
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Run verification steps
    verify_prerequisites
    verify_docker_services
    verify_service_health
    verify_the7space_functionality
    verify_integrations
    verify_monitoring
    run_integration_tests
    verify_performance
    verify_security
    
    # Generate report and exit
    if generate_verification_report; then
        exit 0
    else
        exit 1
    fi
}

# Handle command line arguments
case "${1:-verify}" in
    "verify")
        main
        ;;
    "health")
        print_header
        verify_service_health
        verify_the7space_functionality
        ;;
    "services")
        print_header
        verify_docker_services
        verify_monitoring
        ;;
    "integrations")
        print_header
        verify_integrations
        ;;
    "performance")
        print_header
        verify_performance
        ;;
    "security")
        print_header
        verify_security
        ;;
    "tests")
        print_header
        run_integration_tests
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  verify        Full verification (default)"
        echo "  health        Health checks only"
        echo "  services      Service status checks"
        echo "  integrations  Integration checks"
        echo "  performance   Performance checks"
        echo "  security      Security checks"
        echo "  tests         Run integration tests"
        echo "  help          Show this help"
        ;;
    *)
        echo "Unknown command: $1. Use 'help' for available commands."
        exit 1
        ;;
esac
