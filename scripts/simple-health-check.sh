#!/bin/bash

# Simple Health Check Script for HigherSelf Network Server
# Compatible with all bash versions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}=== HigherSelf Network Server Health Check ===${NC}"
echo "Timestamp: $(date)"
echo ""

# Function to check if a service is running
check_service() {
    local service_name=$1
    local display_name=$2
    
    if docker-compose ps "$service_name" 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}✓${NC} $display_name is running"
        return 0
    else
        echo -e "${RED}✗${NC} $display_name is not running"
        return 1
    fi
}

# Function to check HTTP endpoint
check_http() {
    local name=$1
    local url=$2
    
    if curl -s -f "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is responding ($url)"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not responding ($url)"
        return 1
    fi
}

# Function to check TCP port
check_port() {
    local name=$1
    local host=$2
    local port=$3
    
    if nc -z "$host" "$port" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $name is accepting connections ($host:$port)"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not accepting connections ($host:$port)"
        return 1
    fi
}

# Change to project directory
cd "$PROJECT_ROOT"

# Check Docker Compose services
echo -e "${BLUE}--- Docker Services Status ---${NC}"
check_service "higherself-server" "HigherSelf Server"
HIGHERSELF_STATUS=$?

check_service "redis" "Redis"
REDIS_STATUS=$?

check_service "mongodb" "MongoDB"
MONGODB_STATUS=$?

check_service "consul" "Consul"
CONSUL_STATUS=$?

echo ""

# Check service connectivity
echo -e "${BLUE}--- Service Connectivity ---${NC}"

# Check HigherSelf Server API
if [ $HIGHERSELF_STATUS -eq 0 ]; then
    check_http "HigherSelf Server Health" "http://localhost:8000/health"
    check_http "HigherSelf Server Docs" "http://localhost:8000/docs"
fi

# Check Redis
if [ $REDIS_STATUS -eq 0 ]; then
    check_port "Redis" "localhost" "6379"
fi

# Check MongoDB
if [ $MONGODB_STATUS -eq 0 ]; then
    check_port "MongoDB" "localhost" "27017"
fi

# Check Consul
if [ $CONSUL_STATUS -eq 0 ]; then
    check_port "Consul" "localhost" "8500"
    check_http "Consul UI" "http://localhost:8500/ui/"
fi

echo ""

# Show recent logs
echo -e "${BLUE}--- Recent Service Logs ---${NC}"
echo "HigherSelf Server (last 5 lines):"
docker-compose logs --tail=5 higherself-server 2>/dev/null | sed 's/^/  /' || echo "  No logs available"
echo ""

# Show container status
echo -e "${BLUE}--- Container Status ---${NC}"
docker-compose ps

echo ""

# Summary
echo -e "${BLUE}--- Summary ---${NC}"
TOTAL=4
RUNNING=0

[ $HIGHERSELF_STATUS -eq 0 ] && RUNNING=$((RUNNING + 1))
[ $REDIS_STATUS -eq 0 ] && RUNNING=$((RUNNING + 1))
[ $MONGODB_STATUS -eq 0 ] && RUNNING=$((RUNNING + 1))
[ $CONSUL_STATUS -eq 0 ] && RUNNING=$((RUNNING + 1))

if [ $RUNNING -eq $TOTAL ]; then
    echo -e "${GREEN}✓ All services are healthy ($RUNNING/$TOTAL)${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Some services need attention ($RUNNING/$TOTAL healthy)${NC}"
    exit 1
fi
