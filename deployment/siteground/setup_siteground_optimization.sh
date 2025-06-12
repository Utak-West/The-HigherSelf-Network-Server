#!/bin/bash
# SiteGround Optimization Setup Script for HigherSelf Network
# This script configures all optimizations for the Jump Start plan

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="/var/log/higherself/setup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root"
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."

    mkdir -p /var/log/higherself
    mkdir -p /home/backup/logs
    mkdir -p /etc/prometheus
    mkdir -p /etc/grafana/provisioning/dashboards

    # Set proper permissions
    chown -R higherself:higherself /var/log/higherself 2>/dev/null || true
    chown -R higherself:higherself /home/backup 2>/dev/null || true

    log "Directories created successfully"
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."

    # Update package list
    apt update

    # Install required packages
    apt install -y \
        redis-server \
        mongodb \
        nginx \
        prometheus \
        grafana \
        logrotate \
        curl \
        jq \
        bc \
        apache2-utils

    log "Dependencies installed successfully"
}

# Configure Redis for SiteGround
configure_redis() {
    log "Configuring Redis for SiteGround optimization..."

    # Backup original config
    cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

    # Copy optimized Redis config
    cp "$SCRIPT_DIR/../redis/redis.conf" /etc/redis/redis.conf

    # Restart and enable Redis
    systemctl restart redis-server
    systemctl enable redis-server

    # Verify Redis is working
    if redis-cli ping | grep -q "PONG"; then
        log "Redis configured and running successfully"
    else
        error "Redis configuration failed"
        exit 1
    fi
}

# Configure MongoDB for SiteGround
configure_mongodb() {
    log "Configuring MongoDB for SiteGround optimization..."

    # Backup original config
    cp /etc/mongod.conf /etc/mongod.conf.backup

    # Create optimized MongoDB config
    cat > /etc/mongod.conf << EOF
# MongoDB configuration for SiteGround 8GB RAM
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1.5
    collectionConfig:
      blockCompressor: snappy
    indexConfig:
      prefixCompression: true

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

net:
  port: 27017
  bindIp: 127.0.0.1
  maxIncomingConnections: 20

processManagement:
  fork: true
  pidFilePath: /var/run/mongodb/mongod.pid

operationProfiling:
  slowOpThresholdMs: 100
  mode: slowOp
EOF

    # Restart and enable MongoDB
    systemctl restart mongod
    systemctl enable mongod

    log "MongoDB configured successfully"
}

# Set up monitoring
setup_monitoring() {
    log "Setting up monitoring for SiteGround..."

    # Copy Prometheus alerts
    cp "$SCRIPT_DIR/prometheus-alerts.yml" /etc/prometheus/

    # Update Prometheus config to include alerts
    if ! grep -q "prometheus-alerts.yml" /etc/prometheus/prometheus.yml; then
        cat >> /etc/prometheus/prometheus.yml << EOF

rule_files:
  - "prometheus-alerts.yml"
EOF
    fi

    # Copy Grafana dashboard
    cp "$SCRIPT_DIR/grafana-dashboard.json" /etc/grafana/provisioning/dashboards/

    # Restart monitoring services
    systemctl restart prometheus
    systemctl restart grafana-server
    systemctl enable prometheus
    systemctl enable grafana-server

    log "Monitoring configured successfully"
}

# Make scripts executable
setup_scripts() {
    log "Setting up optimization scripts..."

    # Make all scripts executable
    chmod +x "$SCRIPT_DIR/scripts/"*.sh

    # Create symlinks in /usr/local/bin for easy access
    ln -sf "$SCRIPT_DIR/scripts/memory_cleanup.sh" /usr/local/bin/higherself-memory-cleanup
    ln -sf "$SCRIPT_DIR/scripts/resource_monitor.sh" /usr/local/bin/higherself-monitor
    ln -sf "$SCRIPT_DIR/scripts/log_rotation.sh" /usr/local/bin/higherself-log-rotate

    log "Scripts configured successfully"
}

# Set up cron jobs
setup_cron_jobs() {
    log "Setting up automated maintenance cron jobs..."

    # Create cron file for HigherSelf maintenance
    cat > /etc/cron.d/higherself-maintenance << EOF
# HigherSelf Network Maintenance Jobs for SiteGround
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# Memory cleanup every 30 minutes
*/30 * * * * root $SCRIPT_DIR/scripts/memory_cleanup.sh >> /var/log/higherself/memory_cleanup.log 2>&1

# Resource monitoring every 5 minutes
*/5 * * * * root $SCRIPT_DIR/scripts/resource_monitor.sh >> /var/log/higherself/resource_monitor.log 2>&1

# Log rotation daily at 2 AM
0 2 * * * root $SCRIPT_DIR/scripts/log_rotation.sh >> /var/log/higherself/log_rotation.log 2>&1

# Weekly system cleanup on Sundays at 3 AM
0 3 * * 0 root apt autoremove -y && apt autoclean >> /var/log/higherself/system_cleanup.log 2>&1
EOF

    # Set proper permissions
    chmod 644 /etc/cron.d/higherself-maintenance

    # Restart cron service
    systemctl restart cron

    log "Cron jobs configured successfully"
}

# Configure environment
setup_environment() {
    log "Setting up SiteGround-optimized environment..."

    # Copy environment file
    if [ -f "$PROJECT_ROOT/.env" ]; then
        cp "$PROJECT_ROOT/.env" "$PROJECT_ROOT/.env.backup"
    fi

    cp "$SCRIPT_DIR/.env.siteground" "$PROJECT_ROOT/.env"

    # Set proper permissions
    chmod 600 "$PROJECT_ROOT/.env"
    chown higherself:higherself "$PROJECT_ROOT/.env" 2>/dev/null || true

    log "Environment configured successfully"
}

# Configure system limits
configure_system_limits() {
    log "Configuring system limits for SiteGround..."

    # Configure limits.conf
    cat >> /etc/security/limits.conf << EOF

# HigherSelf Network optimizations for SiteGround
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
higherself soft nofile 65536
higherself hard nofile 65536
EOF

    # Configure sysctl for network optimization
    cat >> /etc/sysctl.conf << EOF

# HigherSelf Network optimizations for SiteGround
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_congestion_control = bbr
EOF

    # Apply sysctl changes
    sysctl -p

    log "System limits configured successfully"
}

# Verify installation
verify_installation() {
    log "Verifying SiteGround optimization installation..."

    local errors=0

    # Check services
    for service in redis-server mongod prometheus grafana-server; do
        if systemctl is-active --quiet "$service"; then
            info "✓ $service is running"
        else
            error "✗ $service is not running"
            ((errors++))
        fi
    done

    # Check scripts
    for script in memory_cleanup.sh resource_monitor.sh log_rotation.sh; do
        if [ -x "$SCRIPT_DIR/scripts/$script" ]; then
            info "✓ $script is executable"
        else
            error "✗ $script is not executable"
            ((errors++))
        fi
    done

    # Check cron jobs
    if [ -f /etc/cron.d/higherself-maintenance ]; then
        info "✓ Cron jobs configured"
    else
        error "✗ Cron jobs not configured"
        ((errors++))
    fi

    # Check environment file
    if [ -f "$PROJECT_ROOT/.env" ]; then
        info "✓ Environment file configured"
    else
        error "✗ Environment file not found"
        ((errors++))
    fi

    if [ $errors -eq 0 ]; then
        log "✓ All verifications passed successfully!"
        return 0
    else
        error "✗ $errors verification(s) failed"
        return 1
    fi
}

# Display summary
display_summary() {
    log "SiteGround Optimization Setup Complete!"
    echo
    echo -e "${GREEN}=== HigherSelf Network - SiteGround Optimization Summary ===${NC}"
    echo
    echo -e "${BLUE}Optimizations Applied:${NC}"
    echo "  ✓ Redis configured for 1GB memory limit"
    echo "  ✓ MongoDB configured for 1.5GB cache"
    echo "  ✓ Server workers set to 2 (optimized for 4 CPU cores)"
    echo "  ✓ Automated memory cleanup every 30 minutes"
    echo "  ✓ Resource monitoring every 5 minutes"
    echo "  ✓ Log rotation configured for 40GB SSD"
    echo "  ✓ Prometheus alerts for SiteGround limits"
    echo "  ✓ Grafana dashboard for monitoring"
    echo
    echo -e "${BLUE}Available Commands:${NC}"
    echo "  higherself-memory-cleanup  - Manual memory cleanup"
    echo "  higherself-monitor         - Check current resource usage"
    echo "  higherself-log-rotate      - Manual log rotation"
    echo
    echo -e "${BLUE}Monitoring URLs:${NC}"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana:    http://localhost:3000 (admin/admin)"
    echo
    echo -e "${BLUE}Log Files:${NC}"
    echo "  Setup:      /var/log/higherself/setup.log"
    echo "  Monitoring: /var/log/higherself/resource_monitor.log"
    echo "  Cleanup:    /var/log/higherself/memory_cleanup.log"
    echo "  Rotation:   /var/log/higherself/log_rotation.log"
    echo
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Review the launch readiness checklist:"
    echo "     $SCRIPT_DIR/LAUNCH_READINESS_CHECKLIST.md"
    echo "  2. Deploy your application with the optimized settings"
    echo "  3. Monitor resource usage in Grafana dashboard"
    echo "  4. Set up SSL certificates and domain configuration"
    echo
}

# Main execution
main() {
    log "Starting SiteGround optimization setup for HigherSelf Network..."

    # Create log directory first
    mkdir -p "$(dirname "$LOG_FILE")"

    check_root
    create_directories
    install_dependencies
    configure_redis
    configure_mongodb
    setup_monitoring
    setup_scripts
    setup_cron_jobs
    setup_environment
    configure_system_limits

    if verify_installation; then
        display_summary
        log "SiteGround optimization setup completed successfully!"
        exit 0
    else
        error "Setup completed with errors. Please check the logs."
        exit 1
    fi
}

# Run main function
main "$@"
