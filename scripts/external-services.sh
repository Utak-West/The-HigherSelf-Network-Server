#!/bin/bash

# ======================================================
# HIGHERSELF NETWORK SERVER - EXTERNAL SERVICES MANAGEMENT
# Comprehensive external API integration testing and monitoring
# ======================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INTEGRATION_CONFIG="$PROJECT_ROOT/deployment/external-services/integration-config.yml"

# Environment configuration
ENVIRONMENT="${ENVIRONMENT:-development}"
ACTION="${1:-status}"
SERVICE="${2:-all}"

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
    echo "Usage: $0 [ACTION] [SERVICE]"
    echo ""
    echo "Actions:"
    echo "  status           Show service status (default)"
    echo "  test             Test service connectivity"
    echo "  configure        Configure service connections"
    echo "  monitor          Monitor service performance"
    echo "  validate         Validate API credentials"
    echo "  benchmark        Benchmark service performance"
    echo "  troubleshoot     Troubleshoot connection issues"
    echo ""
    echo "Services:"
    echo "  all              All external services (default)"
    echo "  notion           Notion API"
    echo "  openai           OpenAI API"
    echo "  huggingface      HuggingFace API"
    echo "  smtp             SMTP email service"
    echo "  storage          Cloud storage services"
    echo "  webhooks         Webhook endpoints"
    echo ""
    echo "Environment Variables:"
    echo "  ENVIRONMENT      Environment (development|staging|production)"
    echo "  NOTION_API_TOKEN Notion API token"
    echo "  OPENAI_API_KEY   OpenAI API key"
    echo ""
    echo "Examples:"
    echo "  $0 status all"
    echo "  $0 test notion"
    echo "  $0 validate openai"
    echo "  ENVIRONMENT=production $0 monitor all"
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

# Function to test Notion API
test_notion_api() {
    print_info "Testing Notion API connectivity..."
    
    if [[ -z "${NOTION_API_TOKEN:-}" ]]; then
        print_error "NOTION_API_TOKEN not configured"
        return 1
    fi
    
    # Test API connectivity
    local response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $NOTION_API_TOKEN" \
        -H "Notion-Version: 2022-06-28" \
        -H "Content-Type: application/json" \
        "https://api.notion.com/v1/users/me" \
        -o /tmp/notion_test.json)
    
    if [[ "$response" == "200" ]]; then
        local user_name=$(jq -r '.name // "Unknown"' /tmp/notion_test.json 2>/dev/null || echo "Unknown")
        print_status "Notion API: Connected (User: $user_name)"
        
        # Test database access
        if [[ -n "${NOTION_BUSINESS_ENTITIES_DB:-}" ]]; then
            local db_response=$(curl -s -w "%{http_code}" \
                -H "Authorization: Bearer $NOTION_API_TOKEN" \
                -H "Notion-Version: 2022-06-28" \
                "https://api.notion.com/v1/databases/${NOTION_BUSINESS_ENTITIES_DB}" \
                -o /tmp/notion_db_test.json)
            
            if [[ "$db_response" == "200" ]]; then
                print_status "Notion Database: Accessible"
            else
                print_warning "Notion Database: Access issues (HTTP $db_response)"
            fi
        fi
        
        rm -f /tmp/notion_test.json /tmp/notion_db_test.json
        return 0
    else
        print_error "Notion API: Connection failed (HTTP $response)"
        return 1
    fi
}

# Function to test OpenAI API
test_openai_api() {
    print_info "Testing OpenAI API connectivity..."
    
    if [[ -z "${OPENAI_API_KEY:-}" ]]; then
        print_error "OPENAI_API_KEY not configured"
        return 1
    fi
    
    # Test API connectivity
    local response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -H "Content-Type: application/json" \
        "https://api.openai.com/v1/models" \
        -o /tmp/openai_test.json)
    
    if [[ "$response" == "200" ]]; then
        local model_count=$(jq '.data | length' /tmp/openai_test.json 2>/dev/null || echo "0")
        print_status "OpenAI API: Connected ($model_count models available)"
        
        # Test a simple completion
        local completion_response=$(curl -s -w "%{http_code}" \
            -H "Authorization: Bearer $OPENAI_API_KEY" \
            -H "Content-Type: application/json" \
            -d '{
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }' \
            "https://api.openai.com/v1/chat/completions" \
            -o /tmp/openai_completion_test.json)
        
        if [[ "$completion_response" == "200" ]]; then
            print_status "OpenAI Chat Completions: Working"
        else
            print_warning "OpenAI Chat Completions: Issues (HTTP $completion_response)"
        fi
        
        rm -f /tmp/openai_test.json /tmp/openai_completion_test.json
        return 0
    else
        print_error "OpenAI API: Connection failed (HTTP $response)"
        return 1
    fi
}

# Function to test HuggingFace API
test_huggingface_api() {
    print_info "Testing HuggingFace API connectivity..."
    
    if [[ -z "${HUGGINGFACE_API_KEY:-}" ]]; then
        print_warning "HUGGINGFACE_API_KEY not configured (optional)"
        return 0
    fi
    
    # Test API connectivity with a simple model
    local response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $HUGGINGFACE_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"inputs": "Hello world"}' \
        "https://api-inference.huggingface.co/models/gpt2" \
        -o /tmp/huggingface_test.json)
    
    if [[ "$response" == "200" ]]; then
        print_status "HuggingFace API: Connected"
        rm -f /tmp/huggingface_test.json
        return 0
    elif [[ "$response" == "503" ]]; then
        print_warning "HuggingFace API: Model loading (HTTP $response)"
        return 0
    else
        print_error "HuggingFace API: Connection failed (HTTP $response)"
        return 1
    fi
}

# Function to test SMTP service
test_smtp_service() {
    print_info "Testing SMTP service connectivity..."
    
    local smtp_host="${SMTP_HOST:-smtp.gmail.com}"
    local smtp_port="${SMTP_PORT:-587}"
    
    # Test SMTP connectivity
    if command -v nc >/dev/null 2>&1; then
        if nc -z "$smtp_host" "$smtp_port" 2>/dev/null; then
            print_status "SMTP: Port $smtp_port accessible on $smtp_host"
        else
            print_error "SMTP: Cannot connect to $smtp_host:$smtp_port"
            return 1
        fi
    else
        print_warning "SMTP: Cannot test connectivity (nc not available)"
    fi
    
    # Test SMTP authentication (if credentials provided)
    if [[ -n "${SMTP_USERNAME:-}" && -n "${SMTP_PASSWORD:-}" ]]; then
        print_info "SMTP credentials configured"
        # Note: Actual authentication test would require more complex SMTP interaction
    else
        print_warning "SMTP credentials not configured"
    fi
    
    return 0
}

# Function to test cloud storage
test_cloud_storage() {
    print_info "Testing cloud storage connectivity..."
    
    # Test AWS S3
    if [[ "${AWS_S3_ENABLED:-false}" == "true" ]]; then
        if command -v aws >/dev/null 2>&1; then
            if aws sts get-caller-identity >/dev/null 2>&1; then
                print_status "AWS S3: Credentials valid"
                
                # Test bucket access
                if [[ -n "${AWS_S3_BUCKET:-}" ]]; then
                    if aws s3 ls "s3://${AWS_S3_BUCKET}" >/dev/null 2>&1; then
                        print_status "AWS S3: Bucket accessible"
                    else
                        print_warning "AWS S3: Bucket access issues"
                    fi
                fi
            else
                print_error "AWS S3: Invalid credentials"
                return 1
            fi
        else
            print_warning "AWS S3: AWS CLI not available"
        fi
    else
        print_info "AWS S3: Disabled"
    fi
    
    return 0
}

# Function to show service status
show_service_status() {
    print_header "External Services Status - Environment: $ENVIRONMENT"
    
    local services=()
    case "$SERVICE" in
        "all")
            services=("notion" "openai" "huggingface" "smtp" "storage")
            ;;
        *)
            services=("$SERVICE")
            ;;
    esac
    
    local total_services=${#services[@]}
    local healthy_services=0
    local failed_services=0
    
    for service in "${services[@]}"; do
        echo ""
        case "$service" in
            "notion")
                if test_notion_api; then
                    healthy_services=$((healthy_services + 1))
                else
                    failed_services=$((failed_services + 1))
                fi
                ;;
            "openai")
                if test_openai_api; then
                    healthy_services=$((healthy_services + 1))
                else
                    failed_services=$((failed_services + 1))
                fi
                ;;
            "huggingface")
                if test_huggingface_api; then
                    healthy_services=$((healthy_services + 1))
                else
                    failed_services=$((failed_services + 1))
                fi
                ;;
            "smtp")
                if test_smtp_service; then
                    healthy_services=$((healthy_services + 1))
                else
                    failed_services=$((failed_services + 1))
                fi
                ;;
            "storage")
                if test_cloud_storage; then
                    healthy_services=$((healthy_services + 1))
                else
                    failed_services=$((failed_services + 1))
                fi
                ;;
            *)
                print_error "Unknown service: $service"
                ;;
        esac
    done
    
    # Summary
    echo ""
    print_header "Service Status Summary"
    echo "Total Services: $total_services"
    echo "Healthy Services: $healthy_services"
    echo "Failed Services: $failed_services"
    
    if [[ $failed_services -eq 0 ]]; then
        print_status "All external services are healthy"
        return 0
    else
        print_warning "$failed_services service(s) have issues"
        return 1
    fi
}

# Function to validate API credentials
validate_credentials() {
    print_header "Validating API Credentials - Environment: $ENVIRONMENT"
    
    local credentials_valid=true
    
    # Check required environment variables
    local required_vars=()
    
    if [[ "$SERVICE" == "all" || "$SERVICE" == "notion" ]]; then
        required_vars+=("NOTION_API_TOKEN")
    fi
    
    if [[ "$SERVICE" == "all" || "$SERVICE" == "openai" ]]; then
        required_vars+=("OPENAI_API_KEY")
    fi
    
    if [[ "$SERVICE" == "all" || "$SERVICE" == "smtp" ]]; then
        required_vars+=("SMTP_USERNAME" "SMTP_PASSWORD")
    fi
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            print_error "Missing required variable: $var"
            credentials_valid=false
        else
            # Mask the value for security
            local masked_value="${!var:0:8}..."
            print_status "$var: $masked_value"
        fi
    done
    
    if [[ "$credentials_valid" == "true" ]]; then
        print_status "All required credentials are configured"
        return 0
    else
        print_error "Some credentials are missing"
        return 1
    fi
}

# Function to benchmark service performance
benchmark_services() {
    print_header "Benchmarking Service Performance - Environment: $ENVIRONMENT"
    
    # Notion API benchmark
    if [[ "$SERVICE" == "all" || "$SERVICE" == "notion" ]] && [[ -n "${NOTION_API_TOKEN:-}" ]]; then
        print_info "Benchmarking Notion API..."
        
        local start_time=$(date +%s.%N)
        test_notion_api >/dev/null 2>&1
        local end_time=$(date +%s.%N)
        local response_time=$(echo "$end_time - $start_time" | bc)
        
        echo "  Notion API Response Time: ${response_time}s"
    fi
    
    # OpenAI API benchmark
    if [[ "$SERVICE" == "all" || "$SERVICE" == "openai" ]] && [[ -n "${OPENAI_API_KEY:-}" ]]; then
        print_info "Benchmarking OpenAI API..."
        
        local start_time=$(date +%s.%N)
        test_openai_api >/dev/null 2>&1
        local end_time=$(date +%s.%N)
        local response_time=$(echo "$end_time - $start_time" | bc)
        
        echo "  OpenAI API Response Time: ${response_time}s"
    fi
    
    print_status "Performance benchmarking completed"
}

# Function to troubleshoot connection issues
troubleshoot_connections() {
    print_header "Troubleshooting Connection Issues - Environment: $ENVIRONMENT"
    
    # Check internet connectivity
    print_info "Checking internet connectivity..."
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        print_status "Internet connectivity: OK"
    else
        print_error "Internet connectivity: FAILED"
        return 1
    fi
    
    # Check DNS resolution
    print_info "Checking DNS resolution..."
    local test_domains=("api.notion.com" "api.openai.com" "api-inference.huggingface.co")
    
    for domain in "${test_domains[@]}"; do
        if nslookup "$domain" >/dev/null 2>&1; then
            print_status "DNS resolution for $domain: OK"
        else
            print_warning "DNS resolution for $domain: FAILED"
        fi
    done
    
    # Check SSL certificates
    print_info "Checking SSL certificates..."
    for domain in "${test_domains[@]}"; do
        if openssl s_client -connect "$domain:443" -servername "$domain" </dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
            print_status "SSL certificate for $domain: Valid"
        else
            print_warning "SSL certificate for $domain: Issues"
        fi
    done
    
    print_status "Troubleshooting completed"
}

# Main execution function
main() {
    print_header "HigherSelf Network Server - External Services Management"
    echo "Environment: $ENVIRONMENT"
    echo "Action: $ACTION"
    echo "Service: $SERVICE"
    echo ""
    
    load_environment
    
    case "$ACTION" in
        "status")
            show_service_status
            ;;
        "test")
            show_service_status
            ;;
        "validate")
            validate_credentials
            ;;
        "benchmark")
            benchmark_services
            ;;
        "troubleshoot")
            troubleshoot_connections
            ;;
        "configure")
            print_error "Service configuration not yet implemented"
            exit 1
            ;;
        "monitor")
            print_error "Service monitoring not yet implemented"
            exit 1
            ;;
        "-h"|"--help"|"help")
            show_usage
            ;;
        *)
            print_error "Unknown action: $ACTION"
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
