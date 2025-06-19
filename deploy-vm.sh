#!/bin/bash

# ======================================================
# THE HIGHERSELF NETWORK SERVER - VM PRODUCTION DEPLOYMENT
# MULTI-BUSINESS ENTITY DEPLOYMENT SCRIPT
# ======================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
VM_ENV_FILE=".env.vm.production"
VM_COMPOSE_FILE="docker-compose.vm.yml"
VM_DATA_DIR="/opt/higherself"
VM_LOGS_DIR="./logs/vm"
VM_CONFIG_DIR="./config/vm"
VM_BACKUP_DIR="./backups"
VM_SSL_DIR="./ssl"

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}======================================================${NC}"
    echo -e "${BLUE}  THE HIGHERSELF NETWORK SERVER - VM DEPLOYMENT${NC}"
    echo -e "${BLUE}  Multi-Business Entity Production Environment${NC}"
    echo -e "${BLUE}======================================================${NC}"
    echo ""
}

print_status() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_section() {
    echo -e "${PURPLE}▶ $1${NC}"
}

check_prerequisites() {
    print_section "Checking VM prerequisites..."
    
    # Check if running as root or with sudo
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root or with sudo for VM deployment"
        exit 1
    fi
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Installing Docker..."
        install_docker
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Starting Docker..."
        systemctl start docker
        systemctl enable docker
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Installing Docker Compose..."
        install_docker_compose
    fi
    
    # Check available disk space (minimum 20GB)
    available_space=$(df / | awk 'NR==2 {print $4}')
    required_space=20971520  # 20GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        print_error "Insufficient disk space. Required: 20GB, Available: $(($available_space/1024/1024))GB"
        exit 1
    fi
    
    # Check available memory (minimum 8GB)
    available_memory=$(free -m | awk 'NR==2{print $2}')
    required_memory=8192  # 8GB in MB
    
    if [ "$available_memory" -lt "$required_memory" ]; then
        print_warning "Low memory detected. Recommended: 8GB, Available: ${available_memory}MB"
    fi
    
    print_status "Prerequisites check passed"
}

install_docker() {
    print_info "Installing Docker..."
    
    # Update package index
    apt-get update
    
    # Install required packages
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up the stable repository
    echo \
        "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    print_status "Docker installed successfully"
}

install_docker_compose() {
    print_info "Installing Docker Compose..."
    
    # Download Docker Compose
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # Make it executable
    chmod +x /usr/local/bin/docker-compose
    
    # Create symlink
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    print_status "Docker Compose installed successfully"
}

setup_vm_environment() {
    print_section "Setting up VM environment..."
    
    # Create VM data directories with proper permissions
    mkdir -p "$VM_DATA_DIR"/{data/{mongodb,redis,consul,prometheus,grafana},logs,config,backups}
    mkdir -p "$VM_LOGS_DIR"
    mkdir -p "$VM_CONFIG_DIR"
    mkdir -p "$VM_BACKUP_DIR"
    mkdir -p "$VM_SSL_DIR"
    
    # Set proper ownership and permissions
    chown -R 1000:1000 "$VM_DATA_DIR"
    chmod -R 755 "$VM_DATA_DIR"
    
    # Create local directories
    mkdir -p "$VM_LOGS_DIR"/{mongodb,redis,consul,prometheus,grafana,nginx}
    mkdir -p "$VM_CONFIG_DIR"/{redis,nginx,prometheus,grafana}
    
    print_status "VM directories created"
    
    # Check if VM environment file exists
    if [ ! -f "$VM_ENV_FILE" ]; then
        if [ -f ".env.vm.production.template" ]; then
            print_info "Creating VM environment file from template..."
            cp .env.vm.production.template "$VM_ENV_FILE"
            print_warning "Please edit $VM_ENV_FILE with your actual credentials and VM IP"
            print_warning "Required: Notion API tokens, database passwords, and VM configuration"
        else
            print_error "VM environment template not found. Please create $VM_ENV_FILE"
            exit 1
        fi
    fi
    
    print_status "VM environment setup complete"
}

configure_firewall() {
    print_section "Configuring VM firewall..."
    
    # Install ufw if not present
    if ! command -v ufw &> /dev/null; then
        apt-get update
        apt-get install -y ufw
    fi
    
    # Reset firewall rules
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH (be careful not to lock yourself out)
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8080/tcp
    ufw allow 8443/tcp
    
    # Allow application ports
    ufw allow 3000/tcp  # Grafana
    ufw allow 9090/tcp  # Prometheus
    ufw allow 8500/tcp  # Consul
    
    # Allow database ports (restrict to local network if needed)
    ufw allow 27017/tcp  # MongoDB
    ufw allow 6379/tcp   # Redis
    
    # Enable firewall
    ufw --force enable
    
    print_status "Firewall configured"
}

setup_ssl_certificates() {
    print_section "Setting up SSL certificates..."
    
    if [ ! -f "$VM_SSL_DIR/cert.pem" ]; then
        print_info "Generating self-signed SSL certificate for development..."
        
        # Generate private key
        openssl genrsa -out "$VM_SSL_DIR/key.pem" 2048
        
        # Generate certificate
        openssl req -new -x509 -key "$VM_SSL_DIR/key.pem" -out "$VM_SSL_DIR/cert.pem" -days 365 -subj "/C=US/ST=State/L=City/O=Organization/CN=higherself.local"
        
        # Set proper permissions
        chmod 600 "$VM_SSL_DIR/key.pem"
        chmod 644 "$VM_SSL_DIR/cert.pem"
        
        print_warning "Self-signed certificate generated. Replace with proper SSL certificate for production."
    else
        print_status "SSL certificates found"
    fi
}

validate_configuration() {
    print_section "Validating VM configuration..."
    
    # Check if required environment variables are set
    if [ -f "$VM_ENV_FILE" ]; then
        source "$VM_ENV_FILE"
        
        # Check critical variables
        if [ "$NOTION_API_TOKEN" = "secret_your_production_notion_token_here" ]; then
            print_error "Please set your actual Notion API token in $VM_ENV_FILE"
            exit 1
        fi
        
        if [ "$VM_IP" = "YOUR_VM_IP_ADDRESS" ]; then
            print_error "Please set your actual VM IP address in $VM_ENV_FILE"
            exit 1
        fi
        
        if [ "$MONGODB_PASSWORD" = "MONGODB_PASSWORD_HERE" ]; then
            print_error "Please set secure database passwords in $VM_ENV_FILE"
            exit 1
        fi
        
        print_status "Configuration validation passed"
    else
        print_error "VM environment file $VM_ENV_FILE not found"
        exit 1
    fi
}

build_vm_images() {
    print_section "Building VM Docker images..."
    
    # Build the main application image with production tag
    docker-compose -f "$VM_COMPOSE_FILE" build --no-cache
    
    if [ $? -eq 0 ]; then
        print_status "VM images built successfully"
    else
        print_error "Failed to build VM images"
        exit 1
    fi
}

start_vm_services() {
    print_section "Starting VM services..."
    
    # Start all VM services
    docker-compose -f "$VM_COMPOSE_FILE" up -d
    
    if [ $? -eq 0 ]; then
        print_status "VM services started successfully"
    else
        print_error "Failed to start VM services"
        exit 1
    fi
}

wait_for_vm_services() {
    print_section "Waiting for VM services to be ready..."
    
    # Wait for MongoDB
    print_info "Waiting for MongoDB..."
    timeout 120 bash -c 'until docker-compose -f docker-compose.vm.yml exec -T mongodb-vm mongosh --eval "db.runCommand(\"ping\")" > /dev/null 2>&1; do sleep 3; done'
    
    # Wait for Redis
    print_info "Waiting for Redis..."
    timeout 60 bash -c 'until docker-compose -f docker-compose.vm.yml exec -T redis-vm redis-cli ping > /dev/null 2>&1; do sleep 2; done'
    
    # Wait for main application
    print_info "Waiting for HigherSelf Network Server..."
    timeout 180 bash -c 'until curl -f http://localhost/health > /dev/null 2>&1; do sleep 5; done'
    
    # Wait for monitoring services
    print_info "Waiting for monitoring services..."
    timeout 90 bash -c 'until curl -f http://localhost:9090/-/ready > /dev/null 2>&1; do sleep 3; done'
    timeout 90 bash -c 'until curl -f http://localhost:3000/api/health > /dev/null 2>&1; do sleep 3; done'
    
    print_status "All VM services are ready"
}

setup_monitoring() {
    print_section "Setting up monitoring and alerting..."
    
    # Configure log rotation
    cat > /etc/logrotate.d/higherself << EOF
$VM_LOGS_DIR/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF
    
    # Setup monitoring cron jobs
    (crontab -l 2>/dev/null; echo "0 */6 * * * /usr/bin/docker system prune -f") | crontab -
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/higherself/scripts/backup.sh") | crontab -
    
    print_status "Monitoring and alerting configured"
}

show_vm_info() {
    print_header
    print_status "THE HIGHERSELF NETWORK SERVER VM DEPLOYMENT COMPLETE!"
    echo ""
    print_info "VM Services Access:"
    echo "  🌐 Main Application:         http://$VM_IP (HTTP) / https://$VM_IP (HTTPS)"
    echo "  📊 Grafana Dashboard:        http://$VM_IP:3000"
    echo "  📈 Prometheus Metrics:       http://$VM_IP:9090"
    echo "  🔍 Consul Service Discovery: http://$VM_IP:8500"
    echo "  🗄️  MongoDB:                 $VM_IP:27017"
    echo "  🔄 Redis:                    $VM_IP:6379"
    echo ""
    print_info "Business Entities Enabled:"
    echo "  🎨 The 7 Space (191 contacts)"
    echo "  💼 AM Consulting (1,300 contacts)"
    echo "  🌟 HigherSelf Core (1,300 contacts)"
    echo ""
    print_info "Integration Endpoints:"
    echo "  📡 Zapier Webhooks:          http://$VM_IP/api/webhooks/zapier"
    echo "  🔗 N8N Webhooks:             http://$VM_IP/api/webhooks/n8n"
    echo "  🔧 Make.com Webhooks:        http://$VM_IP/api/webhooks/make"
    echo ""
    print_info "Next Steps:"
    echo "  1. Configure your automation platform integrations"
    echo "  2. Import contacts for all three business entities"
    echo "  3. Set up monitoring alerts in Grafana"
    echo "  4. Configure backup and disaster recovery"
    echo ""
    print_warning "Remember to:"
    echo "  - Replace self-signed SSL certificates with proper ones"
    echo "  - Configure proper DNS records for your domain"
    echo "  - Set up regular backups and monitoring"
    echo "  - Review and update firewall rules as needed"
}

# Main execution
case "${1:-deploy}" in
    "deploy")
        print_header
        check_prerequisites
        setup_vm_environment
        configure_firewall
        setup_ssl_certificates
        validate_configuration
        build_vm_images
        start_vm_services
        wait_for_vm_services
        setup_monitoring
        show_vm_info
        ;;
    "start")
        print_info "Starting VM services..."
        docker-compose -f "$VM_COMPOSE_FILE" start
        wait_for_vm_services
        show_vm_info
        ;;
    "stop")
        print_info "Stopping VM services..."
        docker-compose -f "$VM_COMPOSE_FILE" stop
        print_status "VM services stopped"
        ;;
    "restart")
        print_info "Restarting VM services..."
        docker-compose -f "$VM_COMPOSE_FILE" restart
        wait_for_vm_services
        show_vm_info
        ;;
    "logs")
        print_info "Showing VM service logs..."
        docker-compose -f "$VM_COMPOSE_FILE" logs -f
        ;;
    "status")
        print_info "VM service status:"
        docker-compose -f "$VM_COMPOSE_FILE" ps
        echo ""
        print_info "System resources:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
        ;;
    "backup")
        print_info "Creating system backup..."
        ./scripts/backup-vm.sh
        ;;
    "update")
        print_info "Updating VM deployment..."
        docker-compose -f "$VM_COMPOSE_FILE" pull
        docker-compose -f "$VM_COMPOSE_FILE" up -d
        print_status "VM deployment updated"
        ;;
    *)
        echo "Usage: $0 {deploy|start|stop|restart|logs|status|backup|update}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full VM deployment (default)"
        echo "  start    - Start VM services"
        echo "  stop     - Stop VM services"
        echo "  restart  - Restart VM services"
        echo "  logs     - Show service logs"
        echo "  status   - Show service status"
        echo "  backup   - Create system backup"
        echo "  update   - Update deployment"
        exit 1
        ;;
esac
