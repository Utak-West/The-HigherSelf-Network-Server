#!/bin/bash
# Log Rotation Script for SiteGround HigherSelf Network Server
# Optimized for 40GB SSD storage with aggressive log management

set -euo pipefail

# Configuration
LOG_DIR="/app/logs"
SYSTEM_LOG_DIR="/var/log/higherself"
BACKUP_DIR="/home/backup/logs"
ROTATION_LOG="/var/log/higherself/log_rotation.log"

# Retention settings (optimized for limited storage)
APP_LOG_RETENTION_DAYS=7
SYSTEM_LOG_RETENTION_DAYS=14
BACKUP_RETENTION_DAYS=30
MAX_LOG_SIZE_MB=100
COMPRESS_AFTER_DAYS=1

# Disk space thresholds
DISK_WARNING_THRESHOLD=80
DISK_CRITICAL_THRESHOLD=90

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$ROTATION_LOG"
}

# Check disk usage
check_disk_usage() {
    local disk_usage
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    echo "$disk_usage"
}

# Get directory size in MB
get_dir_size() {
    local dir="$1"
    if [ -d "$dir" ]; then
        du -sm "$dir" | awk '{print $1}'
    else
        echo "0"
    fi
}

# Rotate application logs
rotate_app_logs() {
    log "Rotating application logs in $LOG_DIR"
    
    if [ ! -d "$LOG_DIR" ]; then
        log "Application log directory $LOG_DIR does not exist"
        return
    fi
    
    # Find and rotate large log files
    find "$LOG_DIR" -name "*.log" -size +${MAX_LOG_SIZE_MB}M -exec bash -c '
        for file; do
            echo "$(date) - Rotating large log file: $file"
            mv "$file" "${file}.$(date +%Y%m%d_%H%M%S)"
            touch "$file"
            chmod 644 "$file"
        done
    ' _ {} +
    
    # Compress logs older than 1 day
    find "$LOG_DIR" -name "*.log.*" -mtime +$COMPRESS_AFTER_DAYS ! -name "*.gz" -exec gzip {} \;
    
    # Remove old application logs
    find "$LOG_DIR" -name "*.log.*.gz" -mtime +$APP_LOG_RETENTION_DAYS -delete
    find "$LOG_DIR" -name "*.log.*" ! -name "*.gz" -mtime +$APP_LOG_RETENTION_DAYS -delete
    
    log "Application log rotation completed"
}

# Rotate system logs
rotate_system_logs() {
    log "Rotating system logs in $SYSTEM_LOG_DIR"
    
    if [ ! -d "$SYSTEM_LOG_DIR" ]; then
        mkdir -p "$SYSTEM_LOG_DIR"
        log "Created system log directory $SYSTEM_LOG_DIR"
        return
    fi
    
    # Rotate large system logs
    find "$SYSTEM_LOG_DIR" -name "*.log" -size +${MAX_LOG_SIZE_MB}M -exec bash -c '
        for file; do
            echo "$(date) - Rotating large system log: $file"
            mv "$file" "${file}.$(date +%Y%m%d_%H%M%S)"
            touch "$file"
            chmod 644 "$file"
        done
    ' _ {} +
    
    # Compress old system logs
    find "$SYSTEM_LOG_DIR" -name "*.log.*" -mtime +$COMPRESS_AFTER_DAYS ! -name "*.gz" -exec gzip {} \;
    
    # Remove old system logs
    find "$SYSTEM_LOG_DIR" -name "*.log.*.gz" -mtime +$SYSTEM_LOG_RETENTION_DAYS -delete
    find "$SYSTEM_LOG_DIR" -name "*.log.*" ! -name "*.gz" -mtime +$SYSTEM_LOG_RETENTION_DAYS -delete
    
    log "System log rotation completed"
}

# Backup important logs
backup_logs() {
    log "Backing up important logs to $BACKUP_DIR"
    
    mkdir -p "$BACKUP_DIR"
    
    # Create daily backup archive
    local backup_file="$BACKUP_DIR/logs_backup_$(date +%Y%m%d).tar.gz"
    
    if [ ! -f "$backup_file" ]; then
        # Backup application logs
        if [ -d "$LOG_DIR" ]; then
            tar -czf "$backup_file" -C "$(dirname "$LOG_DIR")" "$(basename "$LOG_DIR")" 2>/dev/null || true
        fi
        
        # Append system logs
        if [ -d "$SYSTEM_LOG_DIR" ]; then
            tar -rzf "$backup_file" -C "$(dirname "$SYSTEM_LOG_DIR")" "$(basename "$SYSTEM_LOG_DIR")" 2>/dev/null || true
        fi
        
        log "Created backup: $backup_file"
    else
        log "Backup already exists: $backup_file"
    fi
    
    # Remove old backups
    find "$BACKUP_DIR" -name "logs_backup_*.tar.gz" -mtime +$BACKUP_RETENTION_DAYS -delete
    
    log "Log backup completed"
}

# Clean Docker logs if using Docker
clean_docker_logs() {
    if command -v docker >/dev/null 2>&1; then
        log "Cleaning Docker container logs"
        
        # Get all container IDs
        local containers
        containers=$(docker ps -aq 2>/dev/null || true)
        
        if [ -n "$containers" ]; then
            for container in $containers; do
                local log_file="/var/lib/docker/containers/$container/$container-json.log"
                if [ -f "$log_file" ] && [ "$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null || echo 0)" -gt $((MAX_LOG_SIZE_MB * 1024 * 1024)) ]; then
                    echo "" > "$log_file"
                    log "Truncated Docker log for container $container"
                fi
            done
        fi
        
        log "Docker log cleanup completed"
    fi
}

# Emergency cleanup for critical disk space
emergency_cleanup() {
    log "EMERGENCY: Performing aggressive log cleanup due to critical disk space"
    
    # Remove all compressed logs older than 3 days
    find "$LOG_DIR" -name "*.gz" -mtime +3 -delete 2>/dev/null || true
    find "$SYSTEM_LOG_DIR" -name "*.gz" -mtime +3 -delete 2>/dev/null || true
    
    # Truncate large current log files
    find "$LOG_DIR" -name "*.log" -size +50M -exec truncate -s 10M {} \;
    find "$SYSTEM_LOG_DIR" -name "*.log" -size +50M -exec truncate -s 10M {} \;
    
    # Clean temporary files
    find /tmp -name "*.log" -mtime +1 -delete 2>/dev/null || true
    
    # Clean old backups more aggressively
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || true
    
    log "Emergency cleanup completed"
}

# Generate log rotation report
generate_report() {
    local app_log_size system_log_size backup_size total_size
    
    app_log_size=$(get_dir_size "$LOG_DIR")
    system_log_size=$(get_dir_size "$SYSTEM_LOG_DIR")
    backup_size=$(get_dir_size "$BACKUP_DIR")
    total_size=$((app_log_size + system_log_size + backup_size))
    
    log "Log Rotation Report:"
    log "  Application logs: ${app_log_size}MB"
    log "  System logs: ${system_log_size}MB"
    log "  Log backups: ${backup_size}MB"
    log "  Total log storage: ${total_size}MB"
    
    # Check if logs are taking too much space (more than 2GB)
    if [ "$total_size" -gt 2048 ]; then
        log "WARNING: Log storage (${total_size}MB) exceeds recommended limit (2GB)"
    fi
}

# Main rotation function
main() {
    log "Log rotation started"
    
    # Create necessary directories
    mkdir -p "$(dirname "$ROTATION_LOG")"
    mkdir -p "$BACKUP_DIR"
    
    # Check disk usage
    local disk_usage
    disk_usage=$(check_disk_usage)
    log "Current disk usage: ${disk_usage}%"
    
    # Perform emergency cleanup if critical
    if [ "$disk_usage" -gt "$DISK_CRITICAL_THRESHOLD" ]; then
        emergency_cleanup
    fi
    
    # Perform regular rotation
    rotate_app_logs
    rotate_system_logs
    clean_docker_logs
    
    # Backup logs if not in emergency mode
    if [ "$disk_usage" -lt "$DISK_CRITICAL_THRESHOLD" ]; then
        backup_logs
    fi
    
    # Generate report
    generate_report
    
    # Final disk usage check
    local final_disk_usage
    final_disk_usage=$(check_disk_usage)
    log "Final disk usage: ${final_disk_usage}%"
    
    local space_freed
    space_freed=$((disk_usage - final_disk_usage))
    if [ "$space_freed" -gt 0 ]; then
        log "Disk space freed: ${space_freed}%"
    fi
    
    log "Log rotation completed"
}

# Run main function
main "$@"
