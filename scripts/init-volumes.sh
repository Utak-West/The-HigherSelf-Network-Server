#!/bin/bash

# ======================================================
# HIGHERSELF NETWORK SERVER - VOLUME INITIALIZATION SCRIPT
# Initialize Docker volumes and directory structure for all environments
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

# Environment configuration
ENVIRONMENT="${1:-development}"
FORCE_RECREATE="${2:-false}"

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
    echo "Usage: $0 [ENVIRONMENT] [FORCE_RECREATE]"
    echo ""
    echo "Arguments:"
    echo "  ENVIRONMENT      Environment to initialize (development|staging|production)"
    echo "  FORCE_RECREATE   Force recreate existing volumes (true|false)"
    echo ""
    echo "Examples:"
    echo "  $0 development"
    echo "  $0 production false"
    echo "  $0 staging true"
}

# Function to validate environment
validate_environment() {
    local valid_envs=("development" "staging" "production")
    
    if [[ ! " ${valid_envs[@]} " =~ " ${ENVIRONMENT} " ]]; then
        print_error "Invalid environment: $ENVIRONMENT"
        print_info "Valid environments: ${valid_envs[*]}"
        exit 1
    fi
    
    print_info "Initializing volumes for environment: $ENVIRONMENT"
}

# Function to create directory structure
create_directory_structure() {
    print_header "Creating Directory Structure"
    
    local base_dirs=(
        "data/$ENVIRONMENT"
        "logs/$ENVIRONMENT"
        "backups/$ENVIRONMENT"
        "config/$ENVIRONMENT"
    )
    
    # Service-specific data directories
    local service_dirs=(
        "data/$ENVIRONMENT/mongodb"
        "data/$ENVIRONMENT/redis"
        "data/$ENVIRONMENT/consul"
        "data/$ENVIRONMENT/prometheus"
        "data/$ENVIRONMENT/grafana"
        "data/$ENVIRONMENT/vault"
    )
    
    # Business entity data directories
    local entity_dirs=(
        "data/$ENVIRONMENT/the_7_space"
        "data/$ENVIRONMENT/am_consulting"
        "data/$ENVIRONMENT/higherself_core"
    )
    
    # Log directories
    local log_dirs=(
        "logs/$ENVIRONMENT/application"
        "logs/$ENVIRONMENT/mongodb"
        "logs/$ENVIRONMENT/redis"
        "logs/$ENVIRONMENT/consul"
        "logs/$ENVIRONMENT/prometheus"
        "logs/$ENVIRONMENT/grafana"
        "logs/$ENVIRONMENT/nginx"
        "logs/$ENVIRONMENT/celery"
    )
    
    # Create all directories
    local all_dirs=("${base_dirs[@]}" "${service_dirs[@]}" "${entity_dirs[@]}" "${log_dirs[@]}")
    
    for dir in "${all_dirs[@]}"; do
        local full_path="$PROJECT_ROOT/$dir"
        if [[ ! -d "$full_path" ]]; then
            mkdir -p "$full_path"
            print_status "Created directory: $dir"
        else
            print_info "Directory already exists: $dir"
        fi
        
        # Set appropriate permissions
        chmod 755 "$full_path"
        
        # Create .gitkeep file to ensure directory is tracked
        touch "$full_path/.gitkeep"
    done
}

# Function to create Docker volumes
create_docker_volumes() {
    print_header "Creating Docker Volumes"
    
    local volume_prefix="higherself-network-server"
    local volumes=(
        "mongodb_data_$ENVIRONMENT"
        "redis_data_$ENVIRONMENT"
        "consul_data_$ENVIRONMENT"
        "prometheus_data_$ENVIRONMENT"
        "grafana_data_$ENVIRONMENT"
        "vault_data_$ENVIRONMENT"
    )
    
    for volume in "${volumes[@]}"; do
        local full_volume_name="${volume_prefix}_${volume}"
        
        # Check if volume exists
        if docker volume inspect "$full_volume_name" > /dev/null 2>&1; then
            if [[ "$FORCE_RECREATE" == "true" ]]; then
                print_warning "Removing existing volume: $full_volume_name"
                docker volume rm "$full_volume_name"
                create_volume "$full_volume_name" "$volume"
            else
                print_info "Volume already exists: $full_volume_name"
            fi
        else
            create_volume "$full_volume_name" "$volume"
        fi
    done
}

# Function to create a single Docker volume
create_volume() {
    local volume_name="$1"
    local volume_type="$2"
    
    # Extract service name from volume type
    local service=$(echo "$volume_type" | cut -d'_' -f1)
    
    # Create volume with appropriate labels
    docker volume create \
        --label "com.higherself.service=$service" \
        --label "com.higherself.environment=$ENVIRONMENT" \
        --label "com.higherself.project=higherself-network-server" \
        --label "com.higherself.backup=enabled" \
        --label "com.higherself.created=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        "$volume_name"
    
    print_status "Created volume: $volume_name"
}

# Function to initialize MongoDB data
initialize_mongodb() {
    print_header "Initializing MongoDB Configuration"
    
    local mongodb_config_dir="$PROJECT_ROOT/deployment/mongodb"
    mkdir -p "$mongodb_config_dir"
    
    # Create MongoDB initialization script
    cat > "$mongodb_config_dir/init-mongo.js" << 'EOF'
// MongoDB initialization script for HigherSelf Network Server

// Switch to admin database
db = db.getSiblingDB('admin');

// Create application user
db.createUser({
    user: process.env.MONGO_APP_USER || 'higherself_user',
    pwd: process.env.MONGO_APP_PASSWORD || 'secure_password',
    roles: [
        { role: 'readWrite', db: process.env.MONGO_INITDB_DATABASE || 'higherself_dev' },
        { role: 'dbAdmin', db: process.env.MONGO_INITDB_DATABASE || 'higherself_dev' }
    ]
});

// Switch to application database
db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE || 'higherself_dev');

// Create collections for business entities
db.createCollection('the_7_space_contacts');
db.createCollection('am_consulting_contacts');
db.createCollection('higherself_core_contacts');
db.createCollection('business_entities');
db.createCollection('workflows');
db.createCollection('tasks');
db.createCollection('notifications');

// Create indexes for performance
db.the_7_space_contacts.createIndex({ "email": 1 }, { unique: true });
db.am_consulting_contacts.createIndex({ "email": 1 }, { unique: true });
db.higherself_core_contacts.createIndex({ "email": 1 }, { unique: true });
db.business_entities.createIndex({ "name": 1 }, { unique: true });
db.workflows.createIndex({ "business_entity": 1, "status": 1 });
db.tasks.createIndex({ "business_entity": 1, "created_at": 1 });

print('MongoDB initialization completed for HigherSelf Network Server');
EOF
    
    print_status "Created MongoDB initialization script"
}

# Function to initialize Redis configuration
initialize_redis() {
    print_header "Initializing Redis Configuration"
    
    local redis_config_dir="$PROJECT_ROOT/deployment/redis"
    mkdir -p "$redis_config_dir"
    
    # Create Redis configuration file
    cat > "$redis_config_dir/redis.conf" << EOF
# Redis configuration for HigherSelf Network Server
# Environment: $ENVIRONMENT

# Network
bind 0.0.0.0
port 6379
protected-mode no

# General
daemonize no
supervised no
pidfile /var/run/redis_6379.pid

# Logging
loglevel notice
logfile ""

# Persistence
save 900 1
save 300 10
save 60 10000

stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir ./

# Replication
replica-serve-stale-data yes
replica-read-only yes

# Security
# requirepass (set via environment variable)

# Memory management
maxmemory-policy allkeys-lru

# Business entity namespaces
# the_7_space:*
# am_consulting:*
# higherself_core:*

# Append only file
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes
EOF
    
    print_status "Created Redis configuration file"
}

# Function to initialize Consul configuration
initialize_consul() {
    print_header "Initializing Consul Configuration"
    
    local consul_config_dir="$PROJECT_ROOT/deployment/consul"
    mkdir -p "$consul_config_dir"
    
    # Create Consul configuration file
    cat > "$consul_config_dir/consul.hcl" << EOF
# Consul configuration for HigherSelf Network Server
# Environment: $ENVIRONMENT

datacenter = "higherself-$ENVIRONMENT"
data_dir = "/consul/data"
log_level = "INFO"
node_name = "higherself-server-$ENVIRONMENT"
server = true

# UI
ui_config {
  enabled = true
}

# Client configuration
client_addr = "0.0.0.0"
bind_addr = "0.0.0.0"

# Bootstrap
bootstrap_expect = 1

# Connect
connect {
  enabled = true
}

# Service definitions
services {
  name = "higherself-server"
  port = 8000
  tags = ["api", "higherself", "$ENVIRONMENT"]
  
  check {
    http = "http://localhost:8000/health"
    interval = "30s"
    timeout = "10s"
  }
}

services {
  name = "mongodb"
  port = 27017
  tags = ["database", "mongodb", "$ENVIRONMENT"]
}

services {
  name = "redis"
  port = 6379
  tags = ["cache", "redis", "$ENVIRONMENT"]
}
EOF
    
    print_status "Created Consul configuration file"
}

# Function to set up business entity isolation
setup_business_entity_isolation() {
    print_header "Setting Up Business Entity Data Isolation"
    
    # Create entity-specific configuration files
    local entities=("the_7_space" "am_consulting" "higherself_core")
    
    for entity in "${entities[@]}"; do
        local entity_config_dir="$PROJECT_ROOT/config/$ENVIRONMENT/$entity"
        mkdir -p "$entity_config_dir"
        
        # Create entity-specific configuration
        cat > "$entity_config_dir/config.yml" << EOF
# Configuration for $entity business entity
# Environment: $ENVIRONMENT

entity:
  name: $entity
  environment: $ENVIRONMENT
  
database:
  mongodb:
    database: ${entity}_db
    collection_prefix: ${entity}_
  
  redis:
    namespace: "${entity}:"
    
storage:
  data_path: ./data/$ENVIRONMENT/$entity
  backup_path: ./backups/$ENVIRONMENT/$entity
  
workflows:
  enabled: true
  automation_level: high
  
notifications:
  enabled: true
  channels:
    - email
    - webhook
EOF
        
        print_status "Created configuration for entity: $entity"
    done
}

# Function to create backup configuration
create_backup_configuration() {
    print_header "Creating Backup Configuration"
    
    local backup_config_dir="$PROJECT_ROOT/config/$ENVIRONMENT/backup"
    mkdir -p "$backup_config_dir"
    
    # Create backup schedule configuration
    cat > "$backup_config_dir/schedule.yml" << EOF
# Backup schedule configuration for $ENVIRONMENT
# Environment: $ENVIRONMENT

schedules:
  mongodb:
    enabled: true
    schedule: "0 2 * * *"  # Daily at 2 AM
    retention_days: $([ "$ENVIRONMENT" = "production" ] && echo "90" || echo "7")
    compression: true
    encryption: $([ "$ENVIRONMENT" = "production" ] && echo "true" || echo "false")
  
  redis:
    enabled: true
    schedule: "0 3 * * *"  # Daily at 3 AM
    retention_days: $([ "$ENVIRONMENT" = "production" ] && echo "30" || echo "3")
    compression: true
    encryption: $([ "$ENVIRONMENT" = "production" ] && echo "true" || echo "false")
  
  consul:
    enabled: true
    schedule: "0 4 * * *"  # Daily at 4 AM
    retention_days: $([ "$ENVIRONMENT" = "production" ] && echo "30" || echo "7")
    compression: true
    encryption: $([ "$ENVIRONMENT" = "production" ] && echo "true" || echo "false")
  
  prometheus:
    enabled: true
    schedule: "0 5 * * *"  # Daily at 5 AM
    retention_days: $([ "$ENVIRONMENT" = "production" ] && echo "30" || echo "7")
    compression: true
    encryption: false
  
  logs:
    enabled: true
    schedule: "0 1 * * 0"  # Weekly on Sunday at 1 AM
    retention_days: $([ "$ENVIRONMENT" = "production" ] && echo "90" || echo "14")
    compression: true
    encryption: false

storage:
  local:
    enabled: true
    path: ./backups/$ENVIRONMENT
  
  cloud:
    enabled: $([ "$ENVIRONMENT" = "production" ] && echo "true" || echo "false")
    provider: aws_s3
    bucket: higherself-$ENVIRONMENT-backups
    region: us-east-1
EOF
    
    print_status "Created backup schedule configuration"
}

# Function to set permissions
set_permissions() {
    print_header "Setting Directory Permissions"
    
    # Set appropriate permissions for data directories
    find "$PROJECT_ROOT/data/$ENVIRONMENT" -type d -exec chmod 755 {} \; 2>/dev/null || true
    find "$PROJECT_ROOT/logs/$ENVIRONMENT" -type d -exec chmod 755 {} \; 2>/dev/null || true
    find "$PROJECT_ROOT/backups/$ENVIRONMENT" -type d -exec chmod 755 {} \; 2>/dev/null || true
    find "$PROJECT_ROOT/config/$ENVIRONMENT" -type d -exec chmod 755 {} \; 2>/dev/null || true
    
    # Set file permissions
    find "$PROJECT_ROOT/config/$ENVIRONMENT" -type f -exec chmod 644 {} \; 2>/dev/null || true
    
    print_status "Directory permissions set"
}

# Function to create summary
create_initialization_summary() {
    print_header "Initialization Summary"
    
    echo "Environment: $ENVIRONMENT"
    echo "Force Recreate: $FORCE_RECREATE"
    echo ""
    
    echo "Created Directories:"
    find "$PROJECT_ROOT" -path "*/data/$ENVIRONMENT*" -o -path "*/logs/$ENVIRONMENT*" -o -path "*/config/$ENVIRONMENT*" -o -path "*/backups/$ENVIRONMENT*" | head -20
    echo ""
    
    echo "Created Docker Volumes:"
    docker volume ls --filter "label=com.higherself.environment=$ENVIRONMENT" --format "table {{.Name}}\t{{.Driver}}\t{{.Labels}}"
    echo ""
    
    echo "Configuration Files:"
    find "$PROJECT_ROOT/deployment" -name "*.conf" -o -name "*.hcl" -o -name "*.js" | head -10
    echo ""
    
    print_status "Volume initialization completed successfully"
    print_info "Next steps:"
    echo "  1. Review configuration files in config/$ENVIRONMENT/"
    echo "  2. Update environment variables in .env.$ENVIRONMENT"
    echo "  3. Start services with: docker-compose up -d"
    echo "  4. Run health checks with: ./scripts/health-check.sh"
}

# Main execution function
main() {
    print_header "HigherSelf Network Server - Volume Initialization"
    echo "Environment: $ENVIRONMENT"
    echo "Force Recreate: $FORCE_RECREATE"
    echo ""
    
    validate_environment
    create_directory_structure
    create_docker_volumes
    initialize_mongodb
    initialize_redis
    initialize_consul
    setup_business_entity_isolation
    create_backup_configuration
    set_permissions
    create_initialization_summary
}

# Handle command line arguments
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_usage
    exit 0
fi

# Execute main function
main "$@"
