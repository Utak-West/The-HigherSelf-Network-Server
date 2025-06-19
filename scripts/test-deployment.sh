#!/bin/bash

# ======================================================
# HIGHERSELF NETWORK SERVER - COMPREHENSIVE DEPLOYMENT TESTING
# End-to-end testing framework for all deployment scenarios
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

# Test configuration
ENVIRONMENT="${1:-development}"
TEST_SUITE="${2:-all}"
OUTPUT_FORMAT="${3:-console}"
VERBOSE="${VERBOSE:-false}"

# Test results tracking
declare -A TEST_RESULTS
declare -A TEST_DETAILS
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

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

print_test_result() {
    local test_name="$1"
    local result="$2"
    local details="${3:-}"
    
    case "$result" in
        "PASS")
            print_status "PASS: $test_name"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            ;;
        "FAIL")
            print_error "FAIL: $test_name"
            if [[ -n "$details" ]]; then
                echo "      Details: $details"
            fi
            FAILED_TESTS=$((FAILED_TESTS + 1))
            ;;
        "SKIP")
            print_warning "SKIP: $test_name"
            if [[ -n "$details" ]]; then
                echo "      Reason: $details"
            fi
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
            ;;
    esac
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    TEST_RESULTS["$test_name"]="$result"
    TEST_DETAILS["$test_name"]="$details"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [ENVIRONMENT] [TEST_SUITE] [OUTPUT_FORMAT]"
    echo ""
    echo "Environments:"
    echo "  development      Test development environment (default)"
    echo "  staging          Test staging environment"
    echo "  production       Test production environment"
    echo ""
    echo "Test Suites:"
    echo "  all              Run all tests (default)"
    echo "  infrastructure   Test infrastructure components"
    echo "  application      Test application functionality"
    echo "  integration      Test external service integrations"
    echo "  performance      Test performance and load"
    echo "  security         Test security configurations"
    echo "  business         Test business entity isolation"
    echo ""
    echo "Output Formats:"
    echo "  console          Console output (default)"
    echo "  json             JSON format"
    echo "  junit            JUnit XML format"
    echo "  html             HTML report"
    echo ""
    echo "Environment Variables:"
    echo "  VERBOSE          Enable verbose output (true|false)"
    echo "  TEST_TIMEOUT     Test timeout in seconds (default: 300)"
    echo ""
    echo "Examples:"
    echo "  $0 development all console"
    echo "  $0 staging integration json"
    echo "  VERBOSE=true $0 production security html"
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

# Function to test infrastructure components
test_infrastructure() {
    print_header "Testing Infrastructure Components"
    
    # Test Docker daemon
    if docker info > /dev/null 2>&1; then
        print_test_result "Docker Daemon" "PASS"
    else
        print_test_result "Docker Daemon" "FAIL" "Docker daemon not running"
    fi
    
    # Test Docker Compose
    if docker-compose version > /dev/null 2>&1; then
        print_test_result "Docker Compose" "PASS"
    else
        print_test_result "Docker Compose" "FAIL" "Docker Compose not available"
    fi
    
    # Test network creation
    local test_network="test-network-$$"
    if docker network create "$test_network" > /dev/null 2>&1; then
        docker network rm "$test_network" > /dev/null 2>&1
        print_test_result "Network Creation" "PASS"
    else
        print_test_result "Network Creation" "FAIL" "Cannot create Docker networks"
    fi
    
    # Test volume creation
    local test_volume="test-volume-$$"
    if docker volume create "$test_volume" > /dev/null 2>&1; then
        docker volume rm "$test_volume" > /dev/null 2>&1
        print_test_result "Volume Creation" "PASS"
    else
        print_test_result "Volume Creation" "FAIL" "Cannot create Docker volumes"
    fi
    
    # Test environment-specific networks
    local networks=(
        "higherself-network-${ENVIRONMENT}"
        "higherself-database-${ENVIRONMENT}"
        "higherself-cache-${ENVIRONMENT}"
    )
    
    for network in "${networks[@]}"; do
        if docker network inspect "$network" > /dev/null 2>&1; then
            print_test_result "Network: $network" "PASS"
        else
            print_test_result "Network: $network" "FAIL" "Network not found"
        fi
    done
    
    # Test environment-specific volumes
    local volumes=(
        "higherself-network-server_mongodb_data_${ENVIRONMENT}"
        "higherself-network-server_redis_data_${ENVIRONMENT}"
    )
    
    for volume in "${volumes[@]}"; do
        if docker volume inspect "$volume" > /dev/null 2>&1; then
            print_test_result "Volume: $volume" "PASS"
        else
            print_test_result "Volume: $volume" "FAIL" "Volume not found"
        fi
    done
}

# Function to test application functionality
test_application() {
    print_header "Testing Application Functionality"
    
    # Test container status
    local containers=(
        "higherself-server-${ENVIRONMENT}"
        "higherself-mongodb-${ENVIRONMENT}"
        "higherself-redis-${ENVIRONMENT}"
        "higherself-consul-${ENVIRONMENT}"
    )
    
    for container in "${containers[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
            print_test_result "Container: $container" "PASS"
        else
            print_test_result "Container: $container" "FAIL" "Container not running"
        fi
    done
    
    # Test application health endpoints
    local health_endpoints=(
        "http://localhost:8000/health"
        "http://localhost:8000/health/ready"
        "http://localhost:8000/health/database"
        "http://localhost:8000/health/external"
    )
    
    for endpoint in "${health_endpoints[@]}"; do
        local endpoint_name=$(basename "$endpoint")
        if curl -f -s "$endpoint" > /dev/null 2>&1; then
            print_test_result "Health Endpoint: $endpoint_name" "PASS"
        else
            print_test_result "Health Endpoint: $endpoint_name" "FAIL" "Endpoint not responding"
        fi
    done
    
    # Test API documentation
    if curl -f -s "http://localhost:8000/docs" > /dev/null 2>&1; then
        print_test_result "API Documentation" "PASS"
    else
        print_test_result "API Documentation" "FAIL" "Documentation not accessible"
    fi
    
    # Test database connectivity
    local db_container="higherself-mongodb-${ENVIRONMENT}"
    if docker ps --format "{{.Names}}" | grep -q "^${db_container}$"; then
        if docker exec "$db_container" mongosh --eval "db.runCommand('ping')" > /dev/null 2>&1; then
            print_test_result "Database Connectivity" "PASS"
        else
            print_test_result "Database Connectivity" "FAIL" "Cannot connect to MongoDB"
        fi
    else
        print_test_result "Database Connectivity" "SKIP" "MongoDB container not running"
    fi
    
    # Test cache connectivity
    local redis_container="higherself-redis-${ENVIRONMENT}"
    if docker ps --format "{{.Names}}" | grep -q "^${redis_container}$"; then
        if docker exec "$redis_container" redis-cli ping > /dev/null 2>&1; then
            print_test_result "Cache Connectivity" "PASS"
        else
            print_test_result "Cache Connectivity" "FAIL" "Cannot connect to Redis"
        fi
    else
        print_test_result "Cache Connectivity" "SKIP" "Redis container not running"
    fi
}

# Function to test external service integrations
test_integration() {
    print_header "Testing External Service Integrations"
    
    # Test Notion API
    if [[ -n "${NOTION_API_TOKEN:-}" ]]; then
        if curl -f -s -H "Authorization: Bearer $NOTION_API_TOKEN" \
           -H "Notion-Version: 2022-06-28" \
           "https://api.notion.com/v1/users/me" > /dev/null 2>&1; then
            print_test_result "Notion API" "PASS"
        else
            print_test_result "Notion API" "FAIL" "API request failed"
        fi
    else
        print_test_result "Notion API" "SKIP" "API token not configured"
    fi
    
    # Test OpenAI API
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then
        if curl -f -s -H "Authorization: Bearer $OPENAI_API_KEY" \
           "https://api.openai.com/v1/models" > /dev/null 2>&1; then
            print_test_result "OpenAI API" "PASS"
        else
            print_test_result "OpenAI API" "FAIL" "API request failed"
        fi
    else
        print_test_result "OpenAI API" "SKIP" "API key not configured"
    fi
    
    # Test HuggingFace API
    if [[ -n "${HUGGINGFACE_API_KEY:-}" ]]; then
        local response=$(curl -s -w "%{http_code}" \
            -H "Authorization: Bearer $HUGGINGFACE_API_KEY" \
            -d '{"inputs": "test"}' \
            "https://api-inference.huggingface.co/models/gpt2" \
            -o /dev/null)
        
        if [[ "$response" == "200" || "$response" == "503" ]]; then
            print_test_result "HuggingFace API" "PASS"
        else
            print_test_result "HuggingFace API" "FAIL" "API request failed (HTTP $response)"
        fi
    else
        print_test_result "HuggingFace API" "SKIP" "API key not configured"
    fi
    
    # Test SMTP connectivity
    local smtp_host="${SMTP_HOST:-smtp.gmail.com}"
    local smtp_port="${SMTP_PORT:-587}"
    
    if command -v nc >/dev/null 2>&1; then
        if nc -z "$smtp_host" "$smtp_port" 2>/dev/null; then
            print_test_result "SMTP Connectivity" "PASS"
        else
            print_test_result "SMTP Connectivity" "FAIL" "Cannot connect to SMTP server"
        fi
    else
        print_test_result "SMTP Connectivity" "SKIP" "netcat not available"
    fi
}

# Function to test business entity isolation
test_business_entities() {
    print_header "Testing Business Entity Isolation"
    
    local entities=("the_7_space" "am_consulting" "higherself_core")
    
    for entity in "${entities[@]}"; do
        # Test entity-specific health endpoint
        if curl -f -s -H "X-Business-Entity: $entity" \
           "http://localhost:8000/health" > /dev/null 2>&1; then
            print_test_result "Entity Health: $entity" "PASS"
        else
            print_test_result "Entity Health: $entity" "FAIL" "Entity health check failed"
        fi
        
        # Test entity configuration
        local entity_enabled_var="${entity^^}_ENABLED"
        entity_enabled_var="${entity_enabled_var//7_SPACE/THE_7_SPACE}"
        
        if [[ "${!entity_enabled_var:-true}" == "true" ]]; then
            print_test_result "Entity Config: $entity" "PASS"
        else
            print_test_result "Entity Config: $entity" "SKIP" "Entity disabled"
        fi
    done
    
    # Test multi-entity mode
    if [[ "${MULTI_ENTITY_MODE:-true}" == "true" ]]; then
        print_test_result "Multi-Entity Mode" "PASS"
    else
        print_test_result "Multi-Entity Mode" "SKIP" "Multi-entity mode disabled"
    fi
}

# Function to test performance
test_performance() {
    print_header "Testing Performance"
    
    # Test application response time
    local start_time=$(date +%s.%N)
    if curl -f -s "http://localhost:8000/health" > /dev/null 2>&1; then
        local end_time=$(date +%s.%N)
        local response_time=$(echo "$end_time - $start_time" | bc)
        local response_time_ms=$(echo "$response_time * 1000" | bc)
        
        if (( $(echo "$response_time < 2.0" | bc -l) )); then
            print_test_result "Response Time" "PASS" "${response_time_ms}ms"
        else
            print_test_result "Response Time" "FAIL" "Slow response: ${response_time_ms}ms"
        fi
    else
        print_test_result "Response Time" "FAIL" "Health endpoint not responding"
    fi
    
    # Test concurrent requests
    local concurrent_requests=10
    local success_count=0
    
    for i in $(seq 1 $concurrent_requests); do
        if curl -f -s "http://localhost:8000/health" > /dev/null 2>&1 &; then
            success_count=$((success_count + 1))
        fi
    done
    
    wait  # Wait for all background jobs to complete
    
    if [[ $success_count -eq $concurrent_requests ]]; then
        print_test_result "Concurrent Requests" "PASS" "$success_count/$concurrent_requests successful"
    else
        print_test_result "Concurrent Requests" "FAIL" "Only $success_count/$concurrent_requests successful"
    fi
}

# Function to test security
test_security() {
    print_header "Testing Security Configuration"
    
    # Test that sensitive endpoints are not exposed
    local sensitive_endpoints=(
        "http://localhost:27017"  # MongoDB
        "http://localhost:6379"   # Redis
    )
    
    for endpoint in "${sensitive_endpoints[@]}"; do
        local service_name=$(echo "$endpoint" | sed 's/.*://')
        if curl -f -s --connect-timeout 5 "$endpoint" > /dev/null 2>&1; then
            print_test_result "Security: $service_name Exposure" "FAIL" "Service exposed externally"
        else
            print_test_result "Security: $service_name Exposure" "PASS"
        fi
    done
    
    # Test environment-specific security
    if [[ "$ENVIRONMENT" == "production" ]]; then
        # Test SSL/TLS configuration
        if [[ "${ENABLE_SSL:-false}" == "true" ]]; then
            print_test_result "SSL/TLS Configuration" "PASS"
        else
            print_test_result "SSL/TLS Configuration" "FAIL" "SSL not enabled in production"
        fi
        
        # Test secrets management
        if [[ "${SECRETS_BACKEND:-env_file}" != "env_file" ]]; then
            print_test_result "Secrets Management" "PASS"
        else
            print_test_result "Secrets Management" "FAIL" "Using env_file in production"
        fi
    else
        print_test_result "SSL/TLS Configuration" "SKIP" "Not required in $ENVIRONMENT"
        print_test_result "Secrets Management" "SKIP" "Not required in $ENVIRONMENT"
    fi
}

# Function to generate test report
generate_test_report() {
    local report_file="test-report-${ENVIRONMENT}-$(date +%Y%m%d_%H%M%S)"
    
    case "$OUTPUT_FORMAT" in
        "json")
            generate_json_report "$report_file.json"
            ;;
        "junit")
            generate_junit_report "$report_file.xml"
            ;;
        "html")
            generate_html_report "$report_file.html"
            ;;
        *)
            generate_console_report
            ;;
    esac
}

# Function to generate console report
generate_console_report() {
    print_header "Test Results Summary"
    
    echo "Environment: $ENVIRONMENT"
    echo "Test Suite: $TEST_SUITE"
    echo "Timestamp: $(date)"
    echo ""
    echo "Results:"
    echo "  Total Tests: $TOTAL_TESTS"
    echo "  Passed: $PASSED_TESTS"
    echo "  Failed: $FAILED_TESTS"
    echo "  Skipped: $SKIPPED_TESTS"
    echo ""
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        print_status "All tests passed successfully!"
        return 0
    else
        print_error "$FAILED_TESTS test(s) failed"
        
        echo ""
        echo "Failed Tests:"
        for test_name in "${!TEST_RESULTS[@]}"; do
            if [[ "${TEST_RESULTS[$test_name]}" == "FAIL" ]]; then
                echo "  - $test_name: ${TEST_DETAILS[$test_name]}"
            fi
        done
        
        return 1
    fi
}

# Function to generate JSON report
generate_json_report() {
    local report_file="$1"
    
    cat > "$report_file" << EOF
{
    "environment": "$ENVIRONMENT",
    "test_suite": "$TEST_SUITE",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "summary": {
        "total": $TOTAL_TESTS,
        "passed": $PASSED_TESTS,
        "failed": $FAILED_TESTS,
        "skipped": $SKIPPED_TESTS
    },
    "tests": [
EOF
    
    local first=true
    for test_name in "${!TEST_RESULTS[@]}"; do
        if [[ "$first" == "false" ]]; then
            echo "," >> "$report_file"
        fi
        
        cat >> "$report_file" << EOF
        {
            "name": "$test_name",
            "result": "${TEST_RESULTS[$test_name]}",
            "details": "${TEST_DETAILS[$test_name]}"
        }EOF
        
        first=false
    done
    
    echo "" >> "$report_file"
    echo "    ]" >> "$report_file"
    echo "}" >> "$report_file"
    
    print_info "JSON report generated: $report_file"
}

# Main execution function
main() {
    print_header "HigherSelf Network Server - Deployment Testing"
    echo "Environment: $ENVIRONMENT"
    echo "Test Suite: $TEST_SUITE"
    echo "Output Format: $OUTPUT_FORMAT"
    echo ""
    
    load_environment
    
    # Run test suites based on selection
    case "$TEST_SUITE" in
        "all")
            test_infrastructure
            test_application
            test_integration
            test_business_entities
            test_performance
            test_security
            ;;
        "infrastructure")
            test_infrastructure
            ;;
        "application")
            test_application
            ;;
        "integration")
            test_integration
            ;;
        "business")
            test_business_entities
            ;;
        "performance")
            test_performance
            ;;
        "security")
            test_security
            ;;
        *)
            print_error "Unknown test suite: $TEST_SUITE"
            show_usage
            exit 1
            ;;
    esac
    
    # Generate test report
    generate_test_report
    
    # Return appropriate exit code
    if [[ $FAILED_TESTS -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

# Handle command line arguments
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_usage
    exit 0
fi

# Execute main function
main "$@"
