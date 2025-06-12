#!/bin/bash
# Resource Monitoring Script for SiteGround HigherSelf Network Server
# Monitors CPU, Memory, Disk, and Network usage with SiteGround-specific thresholds

set -euo pipefail

# Configuration
LOG_FILE="/var/log/higherself/resource_monitor.log"
ALERT_LOG="/var/log/higherself/alerts.log"
METRICS_FILE="/var/log/higherself/metrics.json"

# SiteGround Plan Limits
CPU_CORES=4
TOTAL_RAM_GB=8
TOTAL_DISK_GB=40
BANDWIDTH_TB=5

# Thresholds
CPU_WARNING=70
CPU_CRITICAL=85
MEMORY_WARNING=80
MEMORY_CRITICAL=90
DISK_WARNING=80
DISK_CRITICAL=90
RESPONSE_TIME_WARNING=1000  # milliseconds
ERROR_RATE_WARNING=5        # percentage

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Alert function
alert() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - [$level] $message" | tee -a "$ALERT_LOG"

    # Send to monitoring system if available
    if command -v curl >/dev/null 2>&1; then
        curl -X POST "http://localhost:9090/api/v1/alerts" \
             -H "Content-Type: application/json" \
             -d "{\"level\":\"$level\",\"message\":\"$message\",\"timestamp\":\"$(date -Iseconds)\"}" \
             >/dev/null 2>&1 || true
    fi
}

# Get CPU usage
get_cpu_usage() {
    local cpu_usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    echo "${cpu_usage:-0}"
}

# Get memory usage
get_memory_usage() {
    local memory_info
    memory_info=$(free -m | grep '^Mem:')
    local total used
    total=$(echo "$memory_info" | awk '{print $2}')
    used=$(echo "$memory_info" | awk '{print $3}')
    local percentage
    percentage=$(awk "BEGIN {printf \"%.1f\", ($used/$total)*100}")
    echo "$percentage"
}

# Get disk usage
get_disk_usage() {
    local disk_usage
    disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    echo "${disk_usage:-0}"
}

# Get network usage
get_network_usage() {
    local interface
    interface=$(ip route | grep default | awk '{print $5}' | head -1)

    if [ -n "$interface" ]; then
        local rx_bytes tx_bytes
        rx_bytes=$(cat "/sys/class/net/$interface/statistics/rx_bytes")
        tx_bytes=$(cat "/sys/class/net/$interface/statistics/tx_bytes")
        echo "$rx_bytes $tx_bytes"
    else
        echo "0 0"
    fi
}

# Check application health
check_application_health() {
    local response_time error_rate

    # Check response time
    if command -v curl >/dev/null 2>&1; then
        response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/health || echo "0")
        response_time_ms=$(awk "BEGIN {printf \"%.0f\", $response_time*1000}")
    else
        response_time_ms=0
    fi

    # Check error rate (simplified - would need proper log analysis)
    error_rate=0

    echo "$response_time_ms $error_rate"
}

# Check Redis health
check_redis_health() {
    if command -v redis-cli >/dev/null 2>&1; then
        local redis_memory redis_connections
        redis_memory=$(redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r' | sed 's/M//')
        redis_connections=$(redis-cli info clients | grep connected_clients | cut -d: -f2 | tr -d '\r')
        echo "${redis_memory:-0} ${redis_connections:-0}"
    else
        echo "0 0"
    fi
}

# Check MongoDB health
check_mongodb_health() {
    if command -v mongo >/dev/null 2>&1; then
        local mongo_connections
        mongo_connections=$(mongo --quiet --eval "db.serverStatus().connections.current" 2>/dev/null || echo "0")
        echo "${mongo_connections:-0}"
    else
        echo "0"
    fi
}

# Generate metrics JSON
generate_metrics() {
    local cpu_usage memory_usage disk_usage
    local network_stats app_health redis_health mongo_health

    cpu_usage=$(get_cpu_usage)
    memory_usage=$(get_memory_usage)
    disk_usage=$(get_disk_usage)
    network_stats=$(get_network_usage)
    app_health=$(check_application_health)
    redis_health=$(check_redis_health)
    mongo_health=$(check_mongodb_health)

    # Parse network stats
    local rx_bytes tx_bytes
    read -r rx_bytes tx_bytes <<< "$network_stats"

    # Parse app health
    local response_time error_rate
    read -r response_time error_rate <<< "$app_health"

    # Parse Redis health
    local redis_memory redis_connections
    read -r redis_memory redis_connections <<< "$redis_health"

    # Generate JSON
    cat > "$METRICS_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "siteground": {
    "plan": "jump_start",
    "limits": {
      "cpu_cores": $CPU_CORES,
      "ram_gb": $TOTAL_RAM_GB,
      "disk_gb": $TOTAL_DISK_GB,
      "bandwidth_tb": $BANDWIDTH_TB
    }
  },
  "resources": {
    "cpu": {
      "usage_percent": $cpu_usage,
      "cores_available": $CPU_CORES
    },
    "memory": {
      "usage_percent": $memory_usage,
      "total_gb": $TOTAL_RAM_GB
    },
    "disk": {
      "usage_percent": $disk_usage,
      "total_gb": $TOTAL_DISK_GB
    },
    "network": {
      "rx_bytes": $rx_bytes,
      "tx_bytes": $tx_bytes
    }
  },
  "application": {
    "response_time_ms": $response_time,
    "error_rate_percent": $error_rate
  },
  "services": {
    "redis": {
      "memory_mb": $redis_memory,
      "connections": $redis_connections
    },
    "mongodb": {
      "connections": $mongo_health
    }
  }
}
EOF
}

# Check thresholds and generate alerts
check_thresholds() {
    local cpu_usage memory_usage disk_usage
    local app_health

    cpu_usage=$(get_cpu_usage)
    memory_usage=$(get_memory_usage)
    disk_usage=$(get_disk_usage)
    app_health=$(check_application_health)

    # Parse app health
    local response_time error_rate
    read -r response_time error_rate <<< "$app_health"

    # CPU alerts
    if (( $(echo "$cpu_usage >= $CPU_CRITICAL" | bc -l) )); then
        alert "CRITICAL" "CPU usage is ${cpu_usage}% (threshold: ${CPU_CRITICAL}%)"
    elif (( $(echo "$cpu_usage >= $CPU_WARNING" | bc -l) )); then
        alert "WARNING" "CPU usage is ${cpu_usage}% (threshold: ${CPU_WARNING}%)"
    fi

    # Memory alerts
    if (( $(echo "$memory_usage >= $MEMORY_CRITICAL" | bc -l) )); then
        alert "CRITICAL" "Memory usage is ${memory_usage}% (threshold: ${MEMORY_CRITICAL}%)"
    elif (( $(echo "$memory_usage >= $MEMORY_WARNING" | bc -l) )); then
        alert "WARNING" "Memory usage is ${memory_usage}% (threshold: ${MEMORY_WARNING}%)"
    fi

    # Disk alerts
    if [ "$disk_usage" -ge "$DISK_CRITICAL" ]; then
        alert "CRITICAL" "Disk usage is ${disk_usage}% (threshold: ${DISK_CRITICAL}%)"
    elif [ "$disk_usage" -ge "$DISK_WARNING" ]; then
        alert "WARNING" "Disk usage is ${disk_usage}% (threshold: ${DISK_WARNING}%)"
    fi

    # Response time alerts
    if [ "$response_time" -gt "$RESPONSE_TIME_WARNING" ]; then
        alert "WARNING" "Response time is ${response_time}ms (threshold: ${RESPONSE_TIME_WARNING}ms)"
    fi
}

# Main monitoring function
main() {
    log "Resource monitoring started"

    # Create log directories
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$(dirname "$ALERT_LOG")"
    mkdir -p "$(dirname "$METRICS_FILE")"

    # Generate metrics
    generate_metrics

    # Check thresholds
    check_thresholds

    # Log current status
    local cpu_usage memory_usage disk_usage
    cpu_usage=$(get_cpu_usage)
    memory_usage=$(get_memory_usage)
    disk_usage=$(get_disk_usage)

    log "Current usage - CPU: ${cpu_usage}%, Memory: ${memory_usage}%, Disk: ${disk_usage}%"
}

# Run main function
main "$@"
