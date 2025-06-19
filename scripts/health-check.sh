#!/bin/bash

# ======================================================
# HIGHERSELF NETWORK SERVER - COMPREHENSIVE HEALTH CHECK SYSTEM
# Enterprise-grade health monitoring for all services
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
HEALTH_CONFIG="$PROJECT_ROOT/deployment/health-checks/health-check-config.yml"

# Environment configuration
ENVIRONMENT="${ENVIRONMENT:-development}"
CHECK_TYPE="${1:-all}"
OUTPUT_FORMAT="${2:-console}"
VERBOSE="${VERBOSE:-false}"

# Health check results
declare -A HEALTH_RESULTS
declare -A SERVICE_STATUS
declare -A CHECK_DETAILS

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
    echo "Usage: $0 [CHECK_TYPE] [OUTPUT_FORMAT]"
    echo ""
    echo "Check Types:"
    echo "  all              Check all services (default)"
    echo "  core             Check core services only (app, db, cache)"
    echo "  monitoring       Check monitoring services only"
    echo "  individual       Check individual service"
    echo "  quick            Quick health check"
    echo "  detailed         Detailed health check with metrics"
    echo ""
    echo "Output Formats:"
    echo "  console          Console output (default)"
    echo "  json             JSON format"
    echo "  prometheus       Prometheus metrics format"
    echo "  html             HTML report"
    echo ""
    echo "Environment Variables:"
    echo "  ENVIRONMENT      Environment to check (development|staging|production)"
    echo "  VERBOSE          Enable verbose output (true|false)"
    echo ""
    echo "Examples:"
    echo "  $0 all console"
    echo "  $0 core json"
    echo "  VERBOSE=true $0 detailed html"
}

# Function to load environment configuration
load_environment() {
    local env_file="$PROJECT_ROOT/.env.$ENVIRONMENT"
    if [[ -f "$env_file" ]]; then
        set -a
        source "$env_file"
        set +a
        print_info "Loaded environment configuration: $ENVIRONMENT"
    else
        print_warning "Environment file not found: $env_file"
    fi
}

# Function to check if Docker container is running
check_container_running() {
    local container_name="$1"
    if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        return 0
    else
        return 1
    fi
}

# Function to perform HTTP health check
http_health_check() {
    local service="$1"
    local endpoint="$2"
    local port="$3"
    local expected_status="${4:-200}"
    local timeout="${5:-10}"
    
    local url="http://localhost:${port}${endpoint}"
    local start_time=$(date +%s.%N)
    
    if curl -f -s -m "$timeout" -w "%{http_code}" "$url" > /dev/null 2>&1; then
        local end_time=$(date +%s.%N)
        local response_time=$(echo "$end_time - $start_time" | bc)
        HEALTH_RESULTS["${service}_http"]="PASS"
        CHECK_DETAILS["${service}_http_response_time"]="$response_time"
        return 0
    else
        HEALTH_RESULTS["${service}_http"]="FAIL"
        CHECK_DETAILS["${service}_http_error"]="HTTP check failed for $url"
        return 1
    fi
}

# Function to perform command health check
command_health_check() {
    local service="$1"
    local command="$2"
    local expected_output="${3:-}"
    local timeout="${4:-10}"
    
    local start_time=$(date +%s.%N)
    
    if timeout "$timeout" bash -c "$command" > /dev/null 2>&1; then
        local end_time=$(date +%s.%N)
        local response_time=$(echo "$end_time - $start_time" | bc)
        HEALTH_RESULTS["${service}_command"]="PASS"
        CHECK_DETAILS["${service}_command_response_time"]="$response_time"
        return 0
    else
        HEALTH_RESULTS["${service}_command"]="FAIL"
        CHECK_DETAILS["${service}_command_error"]="Command check failed: $command"
        return 1
    fi
}

# Function to check main application health
check_application_health() {
    print_info "Checking HigherSelf Server health..."
    
    local container_name="higherself-server-${ENVIRONMENT}"
    
    if ! check_container_running "$container_name"; then
        SERVICE_STATUS["higherself-server"]="DOWN"
        print_error "HigherSelf Server container is not running"
        return 1
    fi
    
    # Primary health check
    if http_health_check "higherself-server" "/health" "8000" "200" "30"; then
        print_status "Application health check passed"
    else
        SERVICE_STATUS["higherself-server"]="UNHEALTHY"
        print_error "Application health check failed"
        return 1
    fi
    
    # Secondary health checks
    if [[ "$CHECK_TYPE" == "detailed" ]]; then
        print_info "Performing detailed application checks..."
        
        # API readiness check
        if http_health_check "higherself-server" "/health/ready" "8000" "200" "10"; then
            print_status "API readiness check passed"
        else
            print_warning "API readiness check failed"
        fi
        
        # Database connectivity check
        if http_health_check "higherself-server" "/health/database" "8000" "200" "15"; then
            print_status "Database connectivity check passed"
        else
            print_warning "Database connectivity check failed"
        fi
        
        # External services check
        if http_health_check "higherself-server" "/health/external" "8000" "200" "20"; then
            print_status "External services check passed"
        else
            print_warning "External services check failed"
        fi
    fi
    
    SERVICE_STATUS["higherself-server"]="HEALTHY"
    return 0
}

# Function to check MongoDB health
check_mongodb_health() {
    print_info "Checking MongoDB health..."
    
    local container_name="higherself-mongodb-${ENVIRONMENT}"
    
    if ! check_container_running "$container_name"; then
        SERVICE_STATUS["mongodb"]="DOWN"
        print_error "MongoDB container is not running"
        return 1
    fi
    
    # Primary health check
    local mongo_check="echo 'db.runCommand(\"ping\").ok' | docker exec -i $container_name mongosh localhost:27017/${MONGODB_DB_NAME:-higherself_${ENVIRONMENT}} --quiet"
    
    if command_health_check "mongodb" "$mongo_check" "" "10"; then
        print_status "MongoDB health check passed"
    else
        SERVICE_STATUS["mongodb"]="UNHEALTHY"
        print_error "MongoDB health check failed"
        return 1
    fi
    
    # Detailed checks
    if [[ "$CHECK_TYPE" == "detailed" ]]; then
        print_info "Performing detailed MongoDB checks..."
        
        # Check disk space
        local disk_check="docker exec $container_name df -h /data/db | awk 'NR==2 {print \$5}' | sed 's/%//' | awk '{if(\$1 > 85) exit 1; else exit 0}'"
        if command_health_check "mongodb" "$disk_check" "" "5"; then
            print_status "MongoDB disk space check passed"
        else
            print_warning "MongoDB disk space check failed - high usage"
        fi
        
        # Check connection count
        local conn_check="echo 'db.serverStatus().connections.current' | docker exec -i $container_name mongosh localhost:27017/${MONGODB_DB_NAME:-higherself_${ENVIRONMENT}} --quiet"
        if command_health_check "mongodb" "$conn_check" "" "10"; then
            print_status "MongoDB connection check passed"
        else
            print_warning "MongoDB connection check failed"
        fi
    fi
    
    SERVICE_STATUS["mongodb"]="HEALTHY"
    return 0
}

# Function to check Redis health
check_redis_health() {
    print_info "Checking Redis health..."
    
    local container_name="higherself-redis-${ENVIRONMENT}"
    
    if ! check_container_running "$container_name"; then
        SERVICE_STATUS["redis"]="DOWN"
        print_error "Redis container is not running"
        return 1
    fi
    
    # Primary health check
    local redis_check="docker exec $container_name redis-cli ping"
    
    if command_health_check "redis" "$redis_check" "PONG" "5"; then
        print_status "Redis health check passed"
    else
        SERVICE_STATUS["redis"]="UNHEALTHY"
        print_error "Redis health check failed"
        return 1
    fi
    
    # Detailed checks
    if [[ "$CHECK_TYPE" == "detailed" ]]; then
        print_info "Performing detailed Redis checks..."
        
        # Check memory usage
        local memory_check="docker exec $container_name redis-cli info memory | grep used_memory_human"
        if command_health_check "redis" "$memory_check" "" "5"; then
            print_status "Redis memory check passed"
        else
            print_warning "Redis memory check failed"
        fi
        
        # Check connected clients
        local clients_check="docker exec $container_name redis-cli info clients | grep connected_clients"
        if command_health_check "redis" "$clients_check" "" "5"; then
            print_status "Redis clients check passed"
        else
            print_warning "Redis clients check failed"
        fi
    fi
    
    SERVICE_STATUS["redis"]="HEALTHY"
    return 0
}

# Function to check Consul health
check_consul_health() {
    print_info "Checking Consul health..."
    
    local container_name="higherself-consul-${ENVIRONMENT}"
    
    if ! check_container_running "$container_name"; then
        SERVICE_STATUS["consul"]="DOWN"
        print_error "Consul container is not running"
        return 1
    fi
    
    # Primary health check
    local consul_check="docker exec $container_name consul members"
    
    if command_health_check "consul" "$consul_check" "" "10"; then
        print_status "Consul health check passed"
    else
        SERVICE_STATUS["consul"]="UNHEALTHY"
        print_error "Consul health check failed"
        return 1
    fi
    
    # HTTP API check
    if http_health_check "consul" "/v1/status/leader" "8500" "200" "10"; then
        print_status "Consul API check passed"
    else
        print_warning "Consul API check failed"
    fi
    
    SERVICE_STATUS["consul"]="HEALTHY"
    return 0
}

# Function to check monitoring services
check_monitoring_health() {
    print_info "Checking monitoring services health..."
    
    # Check Prometheus
    if check_container_running "higherself-prometheus-${ENVIRONMENT}"; then
        if http_health_check "prometheus" "/-/healthy" "9090" "200" "10"; then
            print_status "Prometheus health check passed"
            SERVICE_STATUS["prometheus"]="HEALTHY"
        else
            print_warning "Prometheus health check failed"
            SERVICE_STATUS["prometheus"]="UNHEALTHY"
        fi
    else
        print_warning "Prometheus container is not running"
        SERVICE_STATUS["prometheus"]="DOWN"
    fi
    
    # Check Grafana
    if check_container_running "higherself-grafana-${ENVIRONMENT}"; then
        if http_health_check "grafana" "/api/health" "3000" "200" "10"; then
            print_status "Grafana health check passed"
            SERVICE_STATUS["grafana"]="HEALTHY"
        else
            print_warning "Grafana health check failed"
            SERVICE_STATUS["grafana"]="UNHEALTHY"
        fi
    else
        print_warning "Grafana container is not running"
        SERVICE_STATUS["grafana"]="DOWN"
    fi
}

# Function to perform overall health assessment
perform_health_assessment() {
    local total_services=0
    local healthy_services=0
    local unhealthy_services=0
    local down_services=0
    
    for service in "${!SERVICE_STATUS[@]}"; do
        total_services=$((total_services + 1))
        case "${SERVICE_STATUS[$service]}" in
            "HEALTHY")
                healthy_services=$((healthy_services + 1))
                ;;
            "UNHEALTHY")
                unhealthy_services=$((unhealthy_services + 1))
                ;;
            "DOWN")
                down_services=$((down_services + 1))
                ;;
        esac
    done
    
    print_header "Health Assessment Summary"
    echo "Environment: $ENVIRONMENT"
    echo "Total Services: $total_services"
    echo "Healthy Services: $healthy_services"
    echo "Unhealthy Services: $unhealthy_services"
    echo "Down Services: $down_services"
    echo ""
    
    # Overall health status
    if [[ $down_services -gt 0 ]]; then
        print_error "CRITICAL: $down_services service(s) are down"
        return 2
    elif [[ $unhealthy_services -gt 0 ]]; then
        print_warning "WARNING: $unhealthy_services service(s) are unhealthy"
        return 1
    else
        print_status "ALL SYSTEMS HEALTHY"
        return 0
    fi
}

# Function to output results in different formats
output_results() {
    case "$OUTPUT_FORMAT" in
        "json")
            output_json_results
            ;;
        "prometheus")
            output_prometheus_metrics
            ;;
        "html")
            output_html_report
            ;;
        *)
            output_console_results
            ;;
    esac
}

# Function to output JSON results
output_json_results() {
    local json_output="{"
    json_output+='"timestamp":"'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",'
    json_output+='"environment":"'$ENVIRONMENT'",'
    json_output+='"services":{'
    
    local first=true
    for service in "${!SERVICE_STATUS[@]}"; do
        if [[ "$first" == "false" ]]; then
            json_output+=","
        fi
        json_output+='"'$service'":{"status":"'${SERVICE_STATUS[$service]}'"'
        
        # Add response times if available
        if [[ -n "${CHECK_DETAILS[${service}_http_response_time]:-}" ]]; then
            json_output+=',"response_time":'${CHECK_DETAILS[${service}_http_response_time]}
        fi
        
        json_output+='}'
        first=false
    done
    
    json_output+='}}'
    echo "$json_output" | jq '.'
}

# Function to output console results
output_console_results() {
    print_header "Service Health Status"
    
    for service in "${!SERVICE_STATUS[@]}"; do
        local status="${SERVICE_STATUS[$service]}"
        case "$status" in
            "HEALTHY")
                print_status "$service: $status"
                ;;
            "UNHEALTHY")
                print_warning "$service: $status"
                ;;
            "DOWN")
                print_error "$service: $status"
                ;;
        esac
        
        # Show response times if verbose
        if [[ "$VERBOSE" == "true" && -n "${CHECK_DETAILS[${service}_http_response_time]:-}" ]]; then
            echo "  Response time: ${CHECK_DETAILS[${service}_http_response_time]}s"
        fi
    done
}

# Main execution function
main() {
    print_header "HigherSelf Network Server - Health Check System"
    echo "Environment: $ENVIRONMENT"
    echo "Check Type: $CHECK_TYPE"
    echo "Output Format: $OUTPUT_FORMAT"
    echo ""
    
    load_environment
    
    # Perform health checks based on type
    case "$CHECK_TYPE" in
        "core")
            check_application_health
            check_mongodb_health
            check_redis_health
            ;;
        "monitoring")
            check_monitoring_health
            ;;
        "quick")
            check_application_health
            ;;
        "detailed"|"all")
            check_application_health
            check_mongodb_health
            check_redis_health
            check_consul_health
            check_monitoring_health
            ;;
        *)
            print_error "Unknown check type: $CHECK_TYPE"
            show_usage
            exit 1
            ;;
    esac
    
    # Output results
    output_results
    
    # Perform overall assessment
    perform_health_assessment
    exit $?
}

# Handle command line arguments
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_usage
    exit 0
fi

# Execute main function
main "$@"
