#!/bin/bash
# Memory Cleanup Script for SiteGround HigherSelf Network Server
# Optimized for 8GB RAM environment

set -euo pipefail

# Configuration
LOG_FILE="/var/log/higherself/memory_cleanup.log"
MEMORY_THRESHOLD=85  # Percentage
REDIS_MEMORY_THRESHOLD=90  # Percentage
PYTHON_PID_FILE="/var/run/higherself/app.pid"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Check memory usage
check_memory_usage() {
    local memory_usage
    memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    echo "$memory_usage"
}

# Check Redis memory usage
check_redis_memory() {
    local redis_memory_usage
    redis_memory_usage=$(redis-cli info memory | grep used_memory_rss_human | cut -d: -f2 | tr -d '\r')
    echo "$redis_memory_usage"
}

# Clean system caches
clean_system_caches() {
    log "Cleaning system caches..."

    # Clear page cache, dentries and inodes
    sync
    echo 3 > /proc/sys/vm/drop_caches

    log "System caches cleared"
}

# Clean Python garbage collection
clean_python_gc() {
    log "Triggering Python garbage collection..."

    if [ -f "$PYTHON_PID_FILE" ]; then
        local pid
        pid=$(cat "$PYTHON_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            # Send SIGUSR1 to trigger garbage collection
            kill -USR1 "$pid"
            log "Python GC triggered for PID $pid"
        else
            log "Python process not running (PID $pid not found)"
        fi
    else
        log "Python PID file not found"
    fi
}

# Clean Redis memory
clean_redis_memory() {
    log "Cleaning Redis memory..."

    # Trigger Redis memory cleanup
    redis-cli MEMORY PURGE
    redis-cli BGREWRITEAOF

    log "Redis memory cleanup completed"
}

# Clean application logs
clean_application_logs() {
    log "Cleaning old application logs..."

    # Remove logs older than 7 days
    find /app/logs -name "*.log" -mtime +7 -delete
    find /app/logs -name "*.log.*" -mtime +7 -delete

    # Compress logs older than 1 day
    find /app/logs -name "*.log" -mtime +1 -exec gzip {} \;

    log "Application logs cleaned"
}

# Clean temporary files
clean_temp_files() {
    log "Cleaning temporary files..."

    # Clean /tmp files older than 3 days
    find /tmp -type f -mtime +3 -delete 2>/dev/null || true

    # Clean application temp files
    find /app/temp -type f -mtime +1 -delete 2>/dev/null || true

    log "Temporary files cleaned"
}

# Main cleanup function
perform_cleanup() {
    local current_memory
    current_memory=$(check_memory_usage)

    log "Starting memory cleanup - Current usage: ${current_memory}%"

    if [ "$current_memory" -gt "$MEMORY_THRESHOLD" ]; then
        log "Memory usage (${current_memory}%) exceeds threshold (${MEMORY_THRESHOLD}%)"

        # Perform cleanup steps
        clean_temp_files
        clean_application_logs
        clean_redis_memory
        clean_python_gc
        clean_system_caches

        # Wait a moment and check again
        sleep 5
        local new_memory
        new_memory=$(check_memory_usage)
        log "Cleanup completed - New usage: ${new_memory}%"

        # Calculate memory freed
        local freed_memory
        freed_memory=$((current_memory - new_memory))
        log "Memory freed: ${freed_memory}%"

    else
        log "Memory usage (${current_memory}%) is within acceptable limits"
    fi
}

# Emergency cleanup for critical memory situations
emergency_cleanup() {
    log "EMERGENCY: Performing aggressive memory cleanup"

    # Stop non-essential services temporarily
    systemctl stop grafana-server || true
    systemctl stop prometheus || true

    # Perform all cleanup steps
    clean_temp_files
    clean_application_logs
    clean_redis_memory
    clean_python_gc
    clean_system_caches

    # Restart services
    sleep 10
    systemctl start prometheus || true
    systemctl start grafana-server || true

    log "Emergency cleanup completed"
}

# Check if this is an emergency situation
check_emergency() {
    local current_memory
    current_memory=$(check_memory_usage)

    if [ "$current_memory" -gt 95 ]; then
        emergency_cleanup
    else
        perform_cleanup
    fi
}

# Main execution
main() {
    log "Memory cleanup script started"

    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"

    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        log "ERROR: This script must be run as root"
        exit 1
    fi

    # Perform cleanup
    check_emergency

    log "Memory cleanup script completed"
}

# Run main function
main "$@"
