#!/bin/bash

# ====================================================================
# Redis Deployment Script for HigherSelf Network Server
# ====================================================================
# This script automates Redis deployment and configuration for
# development, staging, and production environments.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REDIS_VERSION="7.2"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"
ENVIRONMENT="${ENVIRONMENT:-development}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking system requirements..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    log_success "System requirements check passed"
}

create_redis_config() {
    log_info "Creating Redis configuration..."

    local config_dir="$PROJECT_ROOT/config/redis"
    mkdir -p "$config_dir"

    # Create Redis configuration file
    cat > "$config_dir/redis.conf" << EOF
# Redis Configuration for HigherSelf Network Server
# Environment: $ENVIRONMENT

# Network
bind 0.0.0.0
port $REDIS_PORT
timeout 300
tcp-keepalive 60

# General
daemonize no
supervised no
pidfile /var/run/redis_6379.pid
loglevel notice
logfile ""
databases 16

# Snapshotting
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data

# Replication
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync no
repl-diskless-sync-delay 5
repl-ping-replica-period 10
repl-timeout 60
repl-disable-tcp-nodelay no
repl-backlog-size 1mb
repl-backlog-ttl 3600

# Security
EOF

    # Add password if provided
    if [ -n "$REDIS_PASSWORD" ]; then
        echo "requirepass $REDIS_PASSWORD" >> "$config_dir/redis.conf"
        echo "# masterauth $REDIS_PASSWORD" >> "$config_dir/redis.conf"
    fi

    # Environment-specific configurations
    case $ENVIRONMENT in
        "production")
            cat >> "$config_dir/redis.conf" << EOF

# Production Settings
maxmemory 512mb
maxmemory-policy allkeys-lru
maxclients 1000

# Persistence
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Security
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG "CONFIG_9a8b7c6d"
EOF
            ;;
        "staging")
            cat >> "$config_dir/redis.conf" << EOF

# Staging Settings
maxmemory 256mb
maxmemory-policy allkeys-lru
maxclients 500

# Persistence
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 64
EOF
            ;;
        "development")
            cat >> "$config_dir/redis.conf" << EOF

# Development Settings
maxmemory 128mb
maxmemory-policy allkeys-lru
maxclients 100

# Persistence (lighter for development)
appendonly no

# Slow log
slowlog-log-slower-than 1000
slowlog-max-len 32
EOF
            ;;
    esac

    log_success "Redis configuration created at $config_dir/redis.conf"
}

create_docker_compose() {
    log_info "Creating Docker Compose configuration..."

    cat > "$PROJECT_ROOT/docker-compose.redis.yml" << EOF
version: '3.8'

services:
  redis:
    image: redis:${REDIS_VERSION}-alpine
    container_name: higherself-redis-${ENVIRONMENT}
    restart: unless-stopped
    ports:
      - "${REDIS_PORT}:6379"
    volumes:
      - ./config/redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
      - redis_data:/data
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - higherself-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    environment:
      - REDIS_REPLICATION_MODE=master
    labels:
      - "com.higherself.service=redis"
      - "com.higherself.environment=${ENVIRONMENT}"

volumes:
  redis_data:
    driver: local
    labels:
      - "com.higherself.service=redis"
      - "com.higherself.environment=${ENVIRONMENT}"

networks:
  higherself-network:
    driver: bridge
    labels:
      - "com.higherself.network=main"
      - "com.higherself.environment=${ENVIRONMENT}"
EOF

    log_success "Docker Compose configuration created"
}

deploy_redis() {
    log_info "Deploying Redis for $ENVIRONMENT environment..."

    cd "$PROJECT_ROOT"

    # Stop existing Redis container if running
    if docker-compose -f docker-compose.redis.yml ps | grep -q "higherself-redis-$ENVIRONMENT"; then
        log_info "Stopping existing Redis container..."
        docker-compose -f docker-compose.redis.yml down
    fi

    # Start Redis
    log_info "Starting Redis container..."
    docker-compose -f docker-compose.redis.yml up -d

    # Wait for Redis to be ready
    log_info "Waiting for Redis to be ready..."
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker exec "higherself-redis-$ENVIRONMENT" redis-cli ping > /dev/null 2>&1; then
            log_success "Redis is ready!"
            break
        fi

        if [ $attempt -eq $max_attempts ]; then
            log_error "Redis failed to start after $max_attempts attempts"
            exit 1
        fi

        log_info "Attempt $attempt/$max_attempts - waiting for Redis..."
        sleep 2
        ((attempt++))
    done
}

test_redis_connection() {
    log_info "Testing Redis connection..."

    # Test basic connectivity
    if docker exec "higherself-redis-$ENVIRONMENT" redis-cli ping > /dev/null 2>&1; then
        log_success "✅ Redis ping test passed"
    else
        log_error "❌ Redis ping test failed"
        return 1
    fi

    # Test set/get operations
    local test_key="higherself:test:$(date +%s)"
    local test_value="test_value_$(date +%s)"

    if [ -n "$REDIS_PASSWORD" ]; then
        docker exec "higherself-redis-$ENVIRONMENT" redis-cli -a "$REDIS_PASSWORD" set "$test_key" "$test_value" > /dev/null 2>&1
        local retrieved_value=$(docker exec "higherself-redis-$ENVIRONMENT" redis-cli -a "$REDIS_PASSWORD" get "$test_key" 2>/dev/null)
        docker exec "higherself-redis-$ENVIRONMENT" redis-cli -a "$REDIS_PASSWORD" del "$test_key" > /dev/null 2>&1
    else
        docker exec "higherself-redis-$ENVIRONMENT" redis-cli set "$test_key" "$test_value" > /dev/null 2>&1
        local retrieved_value=$(docker exec "higherself-redis-$ENVIRONMENT" redis-cli get "$test_key" 2>/dev/null)
        docker exec "higherself-redis-$ENVIRONMENT" redis-cli del "$test_key" > /dev/null 2>&1
    fi

    if [ "$retrieved_value" = "$test_value" ]; then
        log_success "✅ Redis set/get test passed"
    else
        log_error "❌ Redis set/get test failed"
        return 1
    fi

    # Test Redis info
    log_info "Redis server information:"
    if [ -n "$REDIS_PASSWORD" ]; then
        docker exec "higherself-redis-$ENVIRONMENT" redis-cli -a "$REDIS_PASSWORD" info server | grep -E "(redis_version|os|arch_bits|process_id|uptime_in_seconds)" 2>/dev/null || true
    else
        docker exec "higherself-redis-$ENVIRONMENT" redis-cli info server | grep -E "(redis_version|os|arch_bits|process_id|uptime_in_seconds)" 2>/dev/null || true
    fi

    log_success "Redis connection tests completed successfully"
}

show_connection_info() {
    log_info "Redis Connection Information:"
    echo "=================================="
    echo "Environment: $ENVIRONMENT"
    echo "Host: localhost"
    echo "Port: $REDIS_PORT"
    echo "Password: ${REDIS_PASSWORD:-"(not set)"}"
    echo "Container: higherself-redis-$ENVIRONMENT"
    echo ""
    echo "Connection URL:"
    if [ -n "$REDIS_PASSWORD" ]; then
        echo "redis://:$REDIS_PASSWORD@localhost:$REDIS_PORT/0"
    else
        echo "redis://localhost:$REDIS_PORT/0"
    fi
    echo ""
    echo "Environment Variables for .env:"
    echo "REDIS_HOST=localhost"
    echo "REDIS_PORT=$REDIS_PORT"
    echo "REDIS_DATABASE=0"
    if [ -n "$REDIS_PASSWORD" ]; then
        echo "REDIS_PASSWORD=$REDIS_PASSWORD"
    fi
    echo "REDIS_SSL=false"
    echo "ENABLE_REDIS=true"
    echo "=================================="
}

cleanup() {
    log_info "Cleaning up Redis deployment..."

    cd "$PROJECT_ROOT"

    # Stop and remove containers
    docker-compose -f docker-compose.redis.yml down -v

    # Remove configuration files
    rm -f docker-compose.redis.yml
    rm -rf config/redis

    log_success "Redis deployment cleaned up"
}

show_help() {
    echo "Redis Deployment Script for HigherSelf Network Server"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  deploy    Deploy Redis (default)"
    echo "  test      Test Redis connection"
    echo "  cleanup   Remove Redis deployment"
    echo "  help      Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  ENVIRONMENT    Deployment environment (development|staging|production)"
    echo "  REDIS_PORT     Redis port (default: 6379)"
    echo "  REDIS_PASSWORD Redis password (optional)"
    echo ""
    echo "Examples:"
    echo "  $0 deploy"
    echo "  ENVIRONMENT=production REDIS_PASSWORD=secret123 $0 deploy"
    echo "  $0 test"
    echo "  $0 cleanup"
}

# Main execution
main() {
    local command="${1:-deploy}"

    case $command in
        "deploy")
            log_info "Starting Redis deployment for HigherSelf Network Server"
            log_info "Environment: $ENVIRONMENT"
            check_requirements
            create_redis_config
            create_docker_compose
            deploy_redis
            test_redis_connection
            show_connection_info
            log_success "Redis deployment completed successfully!"
            ;;
        "test")
            test_redis_connection
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
