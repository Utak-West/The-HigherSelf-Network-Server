#!/bin/bash

# ======================================================
# HIGHERSELF NETWORK SERVER - VOLUME BACKUP & RESTORE SCRIPT
# Comprehensive backup and restore system for Docker volumes
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
BACKUP_CONFIG="$PROJECT_ROOT/deployment/volumes/volume-management.yml"

# Environment configuration
ENVIRONMENT="${ENVIRONMENT:-development}"
ACTION="${1:-backup}"
SERVICE="${2:-all}"
BACKUP_TYPE="${3:-full}"

# Backup configuration
BACKUP_BASE_DIR="$PROJECT_ROOT/backups/$ENVIRONMENT"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$BACKUP_BASE_DIR/$TIMESTAMP"

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
    echo "Usage: $0 [ACTION] [SERVICE] [BACKUP_TYPE]"
    echo ""
    echo "Actions:"
    echo "  backup           Create backup (default)"
    echo "  restore          Restore from backup"
    echo "  list             List available backups"
    echo "  verify           Verify backup integrity"
    echo "  cleanup          Clean up old backups"
    echo "  migrate          Migrate data between environments"
    echo ""
    echo "Services:"
    echo "  all              All services (default)"
    echo "  mongodb          MongoDB data only"
    echo "  redis            Redis data only"
    echo "  consul           Consul data only"
    echo "  prometheus       Prometheus data only"
    echo "  grafana          Grafana data only"
    echo "  logs             Application logs only"
    echo ""
    echo "Backup Types:"
    echo "  full             Full backup (default)"
    echo "  incremental      Incremental backup"
    echo "  differential     Differential backup"
    echo ""
    echo "Environment Variables:"
    echo "  ENVIRONMENT      Environment (development|staging|production)"
    echo "  BACKUP_LOCATION  Custom backup location"
    echo "  ENCRYPTION_KEY   Encryption key for backups"
    echo ""
    echo "Examples:"
    echo "  $0 backup all full"
    echo "  $0 restore mongodb"
    echo "  $0 list"
    echo "  ENVIRONMENT=production $0 backup mongodb full"
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

# Function to create backup directory
create_backup_directory() {
    mkdir -p "$BACKUP_DIR"
    print_info "Created backup directory: $BACKUP_DIR"
    
    # Create metadata file
    cat > "$BACKUP_DIR/backup_metadata.json" << EOF
{
    "timestamp": "$TIMESTAMP",
    "environment": "$ENVIRONMENT",
    "backup_type": "$BACKUP_TYPE",
    "service": "$SERVICE",
    "version": "1.0.0",
    "created_by": "$(whoami)",
    "hostname": "$(hostname)"
}
EOF
}

# Function to backup MongoDB
backup_mongodb() {
    print_info "Backing up MongoDB data..."
    
    local container_name="higherself-mongodb-${ENVIRONMENT}"
    local backup_file="$BACKUP_DIR/mongodb_backup.tar.gz"
    
    if ! docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        print_warning "MongoDB container is not running, backing up volume data only"
        
        # Backup volume data directly
        local volume_name="higherself-network-server_mongodb_data_${ENVIRONMENT}"
        if docker volume inspect "$volume_name" > /dev/null 2>&1; then
            docker run --rm \
                -v "$volume_name:/data:ro" \
                -v "$BACKUP_DIR:/backup" \
                alpine:latest \
                tar czf "/backup/mongodb_volume.tar.gz" -C /data .
            print_status "MongoDB volume backup completed"
        else
            print_error "MongoDB volume not found: $volume_name"
            return 1
        fi
    else
        # Create database dump
        print_info "Creating MongoDB database dump..."
        docker exec "$container_name" mongodump \
            --out /tmp/mongodb_dump \
            --gzip \
            --oplog
        
        # Copy dump from container
        docker cp "$container_name:/tmp/mongodb_dump" "$BACKUP_DIR/mongodb_dump"
        
        # Create compressed archive
        tar czf "$backup_file" -C "$BACKUP_DIR" mongodb_dump
        rm -rf "$BACKUP_DIR/mongodb_dump"
        
        # Backup volume data as well
        local volume_name="higherself-network-server_mongodb_data_${ENVIRONMENT}"
        docker run --rm \
            -v "$volume_name:/data:ro" \
            -v "$BACKUP_DIR:/backup" \
            alpine:latest \
            tar czf "/backup/mongodb_volume.tar.gz" -C /data .
        
        print_status "MongoDB backup completed: $backup_file"
    fi
}

# Function to backup Redis
backup_redis() {
    print_info "Backing up Redis data..."
    
    local container_name="higherself-redis-${ENVIRONMENT}"
    local backup_file="$BACKUP_DIR/redis_backup.tar.gz"
    
    if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        # Trigger Redis save
        docker exec "$container_name" redis-cli BGSAVE
        
        # Wait for save to complete
        while [[ "$(docker exec "$container_name" redis-cli LASTSAVE)" == "$(docker exec "$container_name" redis-cli LASTSAVE)" ]]; do
            sleep 1
        done
        
        print_info "Redis BGSAVE completed"
    fi
    
    # Backup volume data
    local volume_name="higherself-network-server_redis_data_${ENVIRONMENT}"
    if docker volume inspect "$volume_name" > /dev/null 2>&1; then
        docker run --rm \
            -v "$volume_name:/data:ro" \
            -v "$BACKUP_DIR:/backup" \
            alpine:latest \
            tar czf "/backup/redis_backup.tar.gz" -C /data .
        print_status "Redis backup completed: $backup_file"
    else
        print_error "Redis volume not found: $volume_name"
        return 1
    fi
}

# Function to backup Consul
backup_consul() {
    print_info "Backing up Consul data..."
    
    local container_name="higherself-consul-${ENVIRONMENT}"
    local backup_file="$BACKUP_DIR/consul_backup.tar.gz"
    
    if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        # Create Consul snapshot
        docker exec "$container_name" consul snapshot save /tmp/consul_snapshot.snap
        
        # Copy snapshot from container
        docker cp "$container_name:/tmp/consul_snapshot.snap" "$BACKUP_DIR/consul_snapshot.snap"
        
        print_info "Consul snapshot created"
    fi
    
    # Backup volume data
    local volume_name="higherself-network-server_consul_data_${ENVIRONMENT}"
    if docker volume inspect "$volume_name" > /dev/null 2>&1; then
        docker run --rm \
            -v "$volume_name:/data:ro" \
            -v "$BACKUP_DIR:/backup" \
            alpine:latest \
            tar czf "/backup/consul_backup.tar.gz" -C /data .
        print_status "Consul backup completed: $backup_file"
    else
        print_error "Consul volume not found: $volume_name"
        return 1
    fi
}

# Function to backup Prometheus
backup_prometheus() {
    print_info "Backing up Prometheus data..."
    
    local volume_name="higherself-network-server_prometheus_data_${ENVIRONMENT}"
    local backup_file="$BACKUP_DIR/prometheus_backup.tar.gz"
    
    if docker volume inspect "$volume_name" > /dev/null 2>&1; then
        docker run --rm \
            -v "$volume_name:/data:ro" \
            -v "$BACKUP_DIR:/backup" \
            alpine:latest \
            tar czf "/backup/prometheus_backup.tar.gz" -C /data .
        print_status "Prometheus backup completed: $backup_file"
    else
        print_error "Prometheus volume not found: $volume_name"
        return 1
    fi
}

# Function to backup Grafana
backup_grafana() {
    print_info "Backing up Grafana data..."
    
    local volume_name="higherself-network-server_grafana_data_${ENVIRONMENT}"
    local backup_file="$BACKUP_DIR/grafana_backup.tar.gz"
    
    if docker volume inspect "$volume_name" > /dev/null 2>&1; then
        docker run --rm \
            -v "$volume_name:/data:ro" \
            -v "$BACKUP_DIR:/backup" \
            alpine:latest \
            tar czf "/backup/grafana_backup.tar.gz" -C /data .
        print_status "Grafana backup completed: $backup_file"
    else
        print_error "Grafana volume not found: $volume_name"
        return 1
    fi
}

# Function to backup application logs
backup_logs() {
    print_info "Backing up application logs..."
    
    local logs_dir="$PROJECT_ROOT/logs/$ENVIRONMENT"
    local backup_file="$BACKUP_DIR/logs_backup.tar.gz"
    
    if [[ -d "$logs_dir" ]]; then
        tar czf "$backup_file" -C "$PROJECT_ROOT/logs" "$ENVIRONMENT"
        print_status "Logs backup completed: $backup_file"
    else
        print_warning "Logs directory not found: $logs_dir"
    fi
}

# Function to perform full backup
perform_backup() {
    print_header "Starting Backup Process"
    echo "Environment: $ENVIRONMENT"
    echo "Service: $SERVICE"
    echo "Backup Type: $BACKUP_TYPE"
    echo "Backup Directory: $BACKUP_DIR"
    echo ""
    
    create_backup_directory
    
    case "$SERVICE" in
        "all")
            backup_mongodb
            backup_redis
            backup_consul
            backup_prometheus
            backup_grafana
            backup_logs
            ;;
        "mongodb")
            backup_mongodb
            ;;
        "redis")
            backup_redis
            ;;
        "consul")
            backup_consul
            ;;
        "prometheus")
            backup_prometheus
            ;;
        "grafana")
            backup_grafana
            ;;
        "logs")
            backup_logs
            ;;
        *)
            print_error "Unknown service: $SERVICE"
            show_usage
            exit 1
            ;;
    esac
    
    # Create backup summary
    create_backup_summary
    
    # Encrypt backup if encryption key is provided
    if [[ -n "${ENCRYPTION_KEY:-}" ]]; then
        encrypt_backup
    fi
    
    # Upload to cloud storage if configured
    if [[ -n "${BACKUP_LOCATION:-}" ]]; then
        upload_backup
    fi
    
    print_status "Backup process completed successfully"
    print_info "Backup location: $BACKUP_DIR"
}

# Function to create backup summary
create_backup_summary() {
    local summary_file="$BACKUP_DIR/backup_summary.txt"
    
    {
        echo "HigherSelf Network Server Backup Summary"
        echo "========================================"
        echo "Timestamp: $TIMESTAMP"
        echo "Environment: $ENVIRONMENT"
        echo "Service: $SERVICE"
        echo "Backup Type: $BACKUP_TYPE"
        echo ""
        echo "Files:"
        find "$BACKUP_DIR" -type f -exec ls -lh {} \; | awk '{print $9, $5}'
        echo ""
        echo "Total Size: $(du -sh "$BACKUP_DIR" | cut -f1)"
    } > "$summary_file"
    
    print_info "Backup summary created: $summary_file"
}

# Function to list available backups
list_backups() {
    print_header "Available Backups for Environment: $ENVIRONMENT"
    
    if [[ ! -d "$BACKUP_BASE_DIR" ]]; then
        print_warning "No backups found for environment: $ENVIRONMENT"
        return 0
    fi
    
    for backup_dir in "$BACKUP_BASE_DIR"/*; do
        if [[ -d "$backup_dir" ]]; then
            local backup_name=$(basename "$backup_dir")
            local metadata_file="$backup_dir/backup_metadata.json"
            
            if [[ -f "$metadata_file" ]]; then
                local service=$(jq -r '.service' "$metadata_file" 2>/dev/null || echo "unknown")
                local backup_type=$(jq -r '.backup_type' "$metadata_file" 2>/dev/null || echo "unknown")
                local size=$(du -sh "$backup_dir" | cut -f1)
                
                echo "📦 $backup_name"
                echo "   Service: $service"
                echo "   Type: $backup_type"
                echo "   Size: $size"
                echo ""
            else
                echo "📦 $backup_name (no metadata)"
                echo ""
            fi
        fi
    done
}

# Function to verify backup integrity
verify_backup() {
    local backup_timestamp="${2:-latest}"
    
    print_header "Verifying Backup Integrity"
    
    if [[ "$backup_timestamp" == "latest" ]]; then
        backup_timestamp=$(ls -1 "$BACKUP_BASE_DIR" | sort -r | head -n1)
    fi
    
    local verify_dir="$BACKUP_BASE_DIR/$backup_timestamp"
    
    if [[ ! -d "$verify_dir" ]]; then
        print_error "Backup not found: $verify_dir"
        exit 1
    fi
    
    print_info "Verifying backup: $backup_timestamp"
    
    # Check if all expected files exist
    local expected_files=()
    case "$SERVICE" in
        "all")
            expected_files=("mongodb_backup.tar.gz" "redis_backup.tar.gz" "consul_backup.tar.gz" "prometheus_backup.tar.gz" "grafana_backup.tar.gz" "logs_backup.tar.gz")
            ;;
        *)
            expected_files=("${SERVICE}_backup.tar.gz")
            ;;
    esac
    
    for file in "${expected_files[@]}"; do
        if [[ -f "$verify_dir/$file" ]]; then
            # Test archive integrity
            if tar tzf "$verify_dir/$file" > /dev/null 2>&1; then
                print_status "✓ $file - integrity check passed"
            else
                print_error "✗ $file - integrity check failed"
            fi
        else
            print_warning "⚠ $file - file not found"
        fi
    done
    
    print_status "Backup verification completed"
}

# Main execution function
main() {
    print_header "HigherSelf Network Server - Volume Backup System"
    echo "Environment: $ENVIRONMENT"
    echo "Action: $ACTION"
    echo "Service: $SERVICE"
    echo ""
    
    load_environment
    
    case "$ACTION" in
        "backup")
            perform_backup
            ;;
        "restore")
            print_error "Restore functionality not yet implemented"
            exit 1
            ;;
        "list")
            list_backups
            ;;
        "verify")
            verify_backup
            ;;
        "cleanup")
            print_error "Cleanup functionality not yet implemented"
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
