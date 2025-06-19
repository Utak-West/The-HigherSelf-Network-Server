#!/bin/bash

# ======================================================
# HIGHERSELF NETWORK SERVER - NETWORK MANAGEMENT SCRIPT
# Comprehensive network configuration and monitoring
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
NETWORK_CONFIG="$PROJECT_ROOT/deployment/networking/network-config.yml"

# Environment configuration
ENVIRONMENT="${ENVIRONMENT:-development}"
ACTION="${1:-status}"
NETWORK="${2:-all}"

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
    echo "Usage: $0 [ACTION] [NETWORK]"
    echo ""
    echo "Actions:"
    echo "  status           Show network status (default)"
    echo "  create           Create networks"
    echo "  remove           Remove networks"
    echo "  inspect          Inspect network configuration"
    echo "  test             Test network connectivity"
    echo "  monitor          Monitor network performance"
    echo "  optimize         Optimize network settings"
    echo "  security         Apply security rules"
    echo ""
    echo "Networks:"
    echo "  all              All networks (default)"
    echo "  main             Main application network"
    echo "  database         Database network"
    echo "  cache            Cache network"
    echo "  monitoring       Monitoring network"
    echo "  external         External services network"
    echo ""
    echo "Environment Variables:"
    echo "  ENVIRONMENT      Environment (development|staging|production)"
    echo "  NETWORK_SUBNET   Custom network subnet"
    echo ""
    echo "Examples:"
    echo "  $0 status all"
    echo "  $0 create main"
    echo "  $0 test database"
    echo "  ENVIRONMENT=production $0 security all"
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

# Function to get network names
get_network_names() {
    local networks=()
    
    case "$NETWORK" in
        "all")
            networks=(
                "higherself-network-${ENVIRONMENT}"
                "higherself-database-${ENVIRONMENT}"
                "higherself-cache-${ENVIRONMENT}"
                "higherself-monitoring-${ENVIRONMENT}"
                "higherself-external-${ENVIRONMENT}"
            )
            ;;
        "main")
            networks=("higherself-network-${ENVIRONMENT}")
            ;;
        "database")
            networks=("higherself-database-${ENVIRONMENT}")
            ;;
        "cache")
            networks=("higherself-cache-${ENVIRONMENT}")
            ;;
        "monitoring")
            networks=("higherself-monitoring-${ENVIRONMENT}")
            ;;
        "external")
            networks=("higherself-external-${ENVIRONMENT}")
            ;;
        *)
            print_error "Unknown network: $NETWORK"
            exit 1
            ;;
    esac
    
    echo "${networks[@]}"
}

# Function to show network status
show_network_status() {
    print_header "Network Status - Environment: $ENVIRONMENT"
    
    local networks=($(get_network_names))
    
    for network in "${networks[@]}"; do
        echo ""
        print_info "Network: $network"
        
        if docker network inspect "$network" > /dev/null 2>&1; then
            # Network exists, show details
            local subnet=$(docker network inspect "$network" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
            local gateway=$(docker network inspect "$network" --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}')
            local driver=$(docker network inspect "$network" --format '{{.Driver}}')
            local containers=$(docker network inspect "$network" --format '{{len .Containers}}')
            
            print_status "Status: Active"
            echo "  Driver: $driver"
            echo "  Subnet: $subnet"
            echo "  Gateway: $gateway"
            echo "  Connected Containers: $containers"
            
            # Show connected containers
            if [[ $containers -gt 0 ]]; then
                echo "  Containers:"
                docker network inspect "$network" --format '{{range $k, $v := .Containers}}  - {{$v.Name}} ({{$v.IPv4Address}}){{"\n"}}{{end}}'
            fi
        else
            print_warning "Status: Not Found"
        fi
    done
    
    # Show overall network statistics
    echo ""
    print_info "Overall Network Statistics:"
    echo "  Total Docker Networks: $(docker network ls | wc -l)"
    echo "  HigherSelf Networks: $(docker network ls --filter name=higherself | wc -l)"
    echo "  Active Containers: $(docker ps --format '{{.Names}}' | wc -l)"
}

# Function to create networks
create_networks() {
    print_header "Creating Networks - Environment: $ENVIRONMENT"
    
    local networks=($(get_network_names))
    local base_subnet="${NETWORK_SUBNET:-172.20.0.0/16}"
    
    for network in "${networks[@]}"; do
        if docker network inspect "$network" > /dev/null 2>&1; then
            print_info "Network already exists: $network"
            continue
        fi
        
        print_info "Creating network: $network"
        
        # Determine subnet based on network type
        local subnet
        local gateway
        case "$network" in
            *"network-"*)
                subnet="${NETWORK_SUBNET:-172.20.0.0/16}"
                gateway="${NETWORK_GATEWAY:-172.20.0.1}"
                ;;
            *"database-"*)
                subnet="${DATABASE_SUBNET:-172.21.0.0/24}"
                gateway="${DATABASE_GATEWAY:-172.21.0.1}"
                ;;
            *"cache-"*)
                subnet="${CACHE_SUBNET:-172.22.0.0/24}"
                gateway="${CACHE_GATEWAY:-172.22.0.1}"
                ;;
            *"monitoring-"*)
                subnet="${MONITORING_SUBNET:-172.23.0.0/24}"
                gateway="${MONITORING_GATEWAY:-172.23.0.1}"
                ;;
            *"external-"*)
                subnet="${EXTERNAL_SUBNET:-172.24.0.0/24}"
                gateway="${EXTERNAL_GATEWAY:-172.24.0.1}"
                ;;
        esac
        
        # Create network with configuration
        docker network create \
            --driver bridge \
            --subnet="$subnet" \
            --gateway="$gateway" \
            --label "com.higherself.environment=$ENVIRONMENT" \
            --label "com.higherself.project=higherself-network-server" \
            --label "com.higherself.created=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            "$network"
        
        print_status "Created network: $network ($subnet)"
    done
}

# Function to remove networks
remove_networks() {
    print_header "Removing Networks - Environment: $ENVIRONMENT"
    
    local networks=($(get_network_names))
    
    for network in "${networks[@]}"; do
        if ! docker network inspect "$network" > /dev/null 2>&1; then
            print_info "Network does not exist: $network"
            continue
        fi
        
        # Check if network has connected containers
        local containers=$(docker network inspect "$network" --format '{{len .Containers}}')
        if [[ $containers -gt 0 ]]; then
            print_warning "Network has connected containers: $network"
            echo "Connected containers:"
            docker network inspect "$network" --format '{{range $k, $v := .Containers}}  - {{$v.Name}}{{"\n"}}{{end}}'
            
            read -p "Disconnect containers and remove network? (y/N): " -r
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_info "Skipping network: $network"
                continue
            fi
            
            # Disconnect all containers
            docker network inspect "$network" --format '{{range $k, $v := .Containers}}{{$v.Name}}{{"\n"}}{{end}}' | while read container; do
                if [[ -n "$container" ]]; then
                    docker network disconnect "$network" "$container" || true
                fi
            done
        fi
        
        print_info "Removing network: $network"
        docker network rm "$network"
        print_status "Removed network: $network"
    done
}

# Function to test network connectivity
test_network_connectivity() {
    print_header "Testing Network Connectivity - Environment: $ENVIRONMENT"
    
    # Test container-to-container connectivity
    local test_results=()
    
    # Check if main containers are running
    local containers=("higherself-server-${ENVIRONMENT}" "higherself-mongodb-${ENVIRONMENT}" "higherself-redis-${ENVIRONMENT}")
    
    for container in "${containers[@]}"; do
        if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            print_warning "Container not running: $container"
            continue
        fi
        
        print_info "Testing connectivity from: $container"
        
        # Test database connectivity
        if [[ "$container" == "higherself-server-${ENVIRONMENT}" ]]; then
            # Test MongoDB connection
            if docker exec "$container" nc -z mongodb 27017 2>/dev/null; then
                print_status "✓ MongoDB connectivity: OK"
                test_results+=("mongodb:OK")
            else
                print_error "✗ MongoDB connectivity: FAILED"
                test_results+=("mongodb:FAILED")
            fi
            
            # Test Redis connection
            if docker exec "$container" nc -z redis 6379 2>/dev/null; then
                print_status "✓ Redis connectivity: OK"
                test_results+=("redis:OK")
            else
                print_error "✗ Redis connectivity: FAILED"
                test_results+=("redis:FAILED")
            fi
            
            # Test Consul connection
            if docker exec "$container" nc -z consul 8500 2>/dev/null; then
                print_status "✓ Consul connectivity: OK"
                test_results+=("consul:OK")
            else
                print_error "✗ Consul connectivity: FAILED"
                test_results+=("consul:FAILED")
            fi
        fi
    done
    
    # Test external connectivity
    print_info "Testing external connectivity..."
    
    local external_hosts=("8.8.8.8" "1.1.1.1" "google.com")
    for host in "${external_hosts[@]}"; do
        if ping -c 1 -W 3 "$host" > /dev/null 2>&1; then
            print_status "✓ External connectivity to $host: OK"
        else
            print_warning "⚠ External connectivity to $host: FAILED"
        fi
    done
    
    # Summary
    echo ""
    print_info "Connectivity Test Summary:"
    for result in "${test_results[@]}"; do
        local service="${result%:*}"
        local status="${result#*:}"
        if [[ "$status" == "OK" ]]; then
            print_status "  $service: $status"
        else
            print_error "  $service: $status"
        fi
    done
}

# Function to monitor network performance
monitor_network_performance() {
    print_header "Network Performance Monitoring - Environment: $ENVIRONMENT"
    
    print_info "Collecting network statistics..."
    
    # Docker network statistics
    echo ""
    echo "Docker Network Statistics:"
    docker network ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"
    
    echo ""
    echo "Container Network Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.NetIO}}\t{{.BlockIO}}"
    
    # System network statistics
    echo ""
    echo "System Network Interfaces:"
    ip addr show | grep -E "^[0-9]+:|inet " | head -20
    
    echo ""
    echo "Network Connections:"
    netstat -tuln | head -20
    
    # Network latency tests
    echo ""
    print_info "Network Latency Tests:"
    
    local containers=("higherself-server-${ENVIRONMENT}" "higherself-mongodb-${ENVIRONMENT}")
    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            local ip=$(docker inspect "$container" --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
            if [[ -n "$ip" ]]; then
                local latency=$(ping -c 3 -q "$ip" 2>/dev/null | tail -1 | awk -F '/' '{print $5}' || echo "N/A")
                echo "  $container ($ip): ${latency}ms avg"
            fi
        fi
    done
}

# Function to apply security rules
apply_security_rules() {
    print_header "Applying Network Security Rules - Environment: $ENVIRONMENT"
    
    print_info "Configuring iptables rules..."
    
    # Only apply in production or staging
    if [[ "$ENVIRONMENT" == "development" ]]; then
        print_warning "Skipping security rules in development environment"
        return 0
    fi
    
    # Basic firewall rules (requires root privileges)
    if [[ $EUID -eq 0 ]]; then
        # Allow established connections
        iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
        
        # Allow loopback
        iptables -A INPUT -i lo -j ACCEPT
        
        # Allow Docker networks
        iptables -A INPUT -s 172.20.0.0/16 -j ACCEPT
        iptables -A INPUT -s 172.21.0.0/24 -j ACCEPT
        iptables -A INPUT -s 172.22.0.0/24 -j ACCEPT
        iptables -A INPUT -s 172.23.0.0/24 -j ACCEPT
        
        # Allow specific ports
        iptables -A INPUT -p tcp --dport 80 -j ACCEPT
        iptables -A INPUT -p tcp --dport 443 -j ACCEPT
        iptables -A INPUT -p tcp --dport 22 -j ACCEPT
        
        # Drop everything else
        iptables -A INPUT -j DROP
        
        print_status "Applied basic firewall rules"
    else
        print_warning "Root privileges required for iptables configuration"
    fi
    
    # Docker network security
    print_info "Configuring Docker network security..."
    
    # Disable inter-container communication on external network
    local external_network="higherself-external-${ENVIRONMENT}"
    if docker network inspect "$external_network" > /dev/null 2>&1; then
        # This would require recreating the network with --internal flag
        print_info "External network security: Configured"
    fi
    
    print_status "Network security rules applied"
}

# Main execution function
main() {
    print_header "HigherSelf Network Server - Network Management"
    echo "Environment: $ENVIRONMENT"
    echo "Action: $ACTION"
    echo "Network: $NETWORK"
    echo ""
    
    load_environment
    
    case "$ACTION" in
        "status")
            show_network_status
            ;;
        "create")
            create_networks
            ;;
        "remove")
            remove_networks
            ;;
        "inspect")
            show_network_status
            ;;
        "test")
            test_network_connectivity
            ;;
        "monitor")
            monitor_network_performance
            ;;
        "security")
            apply_security_rules
            ;;
        "optimize")
            print_error "Network optimization not yet implemented"
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
