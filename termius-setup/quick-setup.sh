#!/bin/bash

# HigherSelf Network Server - Termius Quick Setup Script
# This script automates the initial setup of Termius configuration

set -e

echo "🚀 HigherSelf Network Server - Termius Quick Setup"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HIGHERSELF_DIR="${HIGHERSELF_DIR:-$(pwd)}"
SSH_DIR="$HOME/.ssh"
TERMIUS_IMPORT_DIR="$HOME/termius-import"

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Termius is installed
    if ! command -v termius &> /dev/null; then
        log_warning "Termius CLI not found. Please install Termius Pro first."
        echo "Download from: https://termius.com/"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker ps &> /dev/null; then
        log_warning "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_warning "AWS CLI not found. Installing..."
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip awscliv2.zip
        sudo ./aws/install
        rm -rf aws awscliv2.zip
    fi
    
    log_success "Prerequisites check complete"
}

setup_directories() {
    log_info "Setting up directories..."
    
    mkdir -p "$SSH_DIR"
    mkdir -p "$TERMIUS_IMPORT_DIR"
    mkdir -p "$HIGHERSELF_DIR/backups/ssh-keys"
    
    log_success "Directories created"
}

generate_ssh_keys() {
    log_info "Generating SSH keys..."
    
    # Development key
    if [ ! -f "$SSH_DIR/higherself_dev_ed25519" ]; then
        log_info "Generating development SSH key..."
        ssh-keygen -t ed25519 -f "$SSH_DIR/higherself_dev_ed25519" -C "higherself-development" -N ""
        ssh-add "$SSH_DIR/higherself_dev_ed25519"
        log_success "Development SSH key generated"
    else
        log_warning "Development SSH key already exists"
    fi
    
    # Staging key
    if [ ! -f "$SSH_DIR/higherself_staging_ed25519" ]; then
        log_info "Generating staging SSH key..."
        read -s -p "Enter passphrase for staging key: " staging_passphrase
        echo ""
        ssh-keygen -t ed25519 -f "$SSH_DIR/higherself_staging_ed25519" -C "higherself-staging" -N "$staging_passphrase"
        log_success "Staging SSH key generated"
    else
        log_warning "Staging SSH key already exists"
    fi
    
    # Production key
    if [ ! -f "$SSH_DIR/higherself_prod_ed25519" ]; then
        log_info "Generating production SSH key..."
        read -s -p "Enter strong passphrase for production key: " prod_passphrase
        echo ""
        ssh-keygen -t ed25519 -f "$SSH_DIR/higherself_prod_ed25519" -C "higherself-production" -N "$prod_passphrase"
        log_success "Production SSH key generated"
    else
        log_warning "Production SSH key already exists"
    fi
    
    # Backup keys
    log_info "Creating backup of SSH keys..."
    cp "$SSH_DIR"/higherself_*_ed25519* "$HIGHERSELF_DIR/backups/ssh-keys/"
    log_success "SSH keys backed up"
}

setup_aws_integration() {
    log_info "Setting up AWS integration..."
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_warning "AWS credentials not configured. Please run 'aws configure' first."
        return 1
    fi
    
    # Create secrets for staging (if they don't exist)
    if ! aws secretsmanager describe-secret --secret-id higherself/staging/ssh-keys/main-key &> /dev/null; then
        log_info "Creating staging SSH key secret..."
        aws secretsmanager create-secret \
            --name higherself/staging/ssh-keys/main-key \
            --description "HigherSelf staging SSH key" \
            --secret-string file://"$SSH_DIR/higherself_staging_ed25519"
        log_success "Staging SSH key stored in AWS Secrets Manager"
    else
        log_warning "Staging SSH key secret already exists"
    fi
    
    # Create secrets for production (if they don't exist)
    if ! aws secretsmanager describe-secret --secret-id higherself/production/ssh-keys/main-key &> /dev/null; then
        log_info "Creating production SSH key secret..."
        aws secretsmanager create-secret \
            --name higherself/production/ssh-keys/main-key \
            --description "HigherSelf production SSH key - CRITICAL" \
            --secret-string file://"$SSH_DIR/higherself_prod_ed25519"
        log_success "Production SSH key stored in AWS Secrets Manager"
    else
        log_warning "Production SSH key secret already exists"
    fi
}

prepare_termius_configs() {
    log_info "Preparing Termius configuration files..."
    
    # Update paths in configuration files
    sed -i.bak "s|/path/to/higherself|$HIGHERSELF_DIR|g" termius-setup/*.json
    
    # Copy configurations to import directory
    cp termius-setup/*.json "$TERMIUS_IMPORT_DIR/"
    
    log_success "Configuration files prepared in $TERMIUS_IMPORT_DIR"
}

test_docker_setup() {
    log_info "Testing Docker setup..."
    
    cd "$HIGHERSELF_DIR"
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml not found in $HIGHERSELF_DIR"
        return 1
    fi
    
    # Start services
    log_info "Starting Docker services..."
    docker-compose up -d
    
    # Wait for services to start
    log_info "Waiting for services to start..."
    sleep 30
    
    # Test API health
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "HigherSelf API is responding"
    else
        log_warning "HigherSelf API not responding yet"
    fi
    
    # Test MongoDB
    if mongosh mongodb://localhost:27017 --eval "db.runCommand({ping: 1})" --quiet > /dev/null 2>&1; then
        log_success "MongoDB is responding"
    else
        log_warning "MongoDB not responding yet"
    fi
    
    # Test Redis
    if redis-cli ping > /dev/null 2>&1; then
        log_success "Redis is responding"
    else
        log_warning "Redis not responding yet"
    fi
}

create_quick_access_script() {
    log_info "Creating quick access script..."
    
    cat > "$HIGHERSELF_DIR/termius-quick-access.sh" << 'EOF'
#!/bin/bash

# HigherSelf Termius Quick Access Script

echo "🚀 HigherSelf Network Server - Quick Access"
echo "==========================================="
echo ""
echo "Available actions:"
echo "1. Start development stack"
echo "2. Stop development stack"
echo "3. Health check all services"
echo "4. View service logs"
echo "5. Open monitoring dashboards"
echo "6. Connect to staging"
echo "7. Emergency production access"
echo ""

read -p "Select action (1-7): " action

case $action in
    1)
        echo "🚀 Starting development stack..."
        docker-compose up -d
        sleep 15
        curl -s http://localhost:8000/health | jq '.'
        ;;
    2)
        echo "🛑 Stopping development stack..."
        docker-compose down
        ;;
    3)
        echo "🏥 Health check..."
        curl -s http://localhost:8000/health | jq '.'
        mongosh mongodb://localhost:27017 --eval "db.runCommand({ping: 1})" --quiet
        redis-cli ping
        ;;
    4)
        echo "📋 Service logs..."
        docker-compose logs --tail=20
        ;;
    5)
        echo "📊 Opening monitoring dashboards..."
        open http://localhost:3000  # Grafana
        open http://localhost:9090  # Prometheus
        open http://localhost:8500  # Consul
        ;;
    6)
        echo "🎯 Connecting to staging..."
        echo "Use Termius to connect to staging environment"
        ;;
    7)
        echo "🚨 Emergency production access..."
        echo "⚠️  This requires approval and MFA"
        echo "Use Termius production emergency access"
        ;;
    *)
        echo "❌ Invalid selection"
        ;;
esac
EOF

    chmod +x "$HIGHERSELF_DIR/termius-quick-access.sh"
    log_success "Quick access script created: $HIGHERSELF_DIR/termius-quick-access.sh"
}

print_next_steps() {
    echo ""
    echo "🎉 Setup Complete!"
    echo "=================="
    echo ""
    echo "Next steps:"
    echo "1. Open Termius Pro"
    echo "2. Import configurations from: $TERMIUS_IMPORT_DIR"
    echo "3. Test development environment connection"
    echo "4. Configure staging and production access"
    echo ""
    echo "Quick access commands:"
    echo "• Run health check: $HIGHERSELF_DIR/termius-quick-access.sh"
    echo "• View logs: docker-compose logs -f"
    echo "• Access API: http://localhost:8000/health"
    echo "• Access Grafana: http://localhost:3000"
    echo ""
    echo "SSH Keys generated:"
    echo "• Development: $SSH_DIR/higherself_dev_ed25519"
    echo "• Staging: $SSH_DIR/higherself_staging_ed25519"
    echo "• Production: $SSH_DIR/higherself_prod_ed25519"
    echo ""
    echo "Configuration files ready for import:"
    ls -la "$TERMIUS_IMPORT_DIR"
    echo ""
    echo "📖 For detailed setup instructions, see: termius-setup/IMPLEMENTATION_GUIDE.md"
}

# Main execution
main() {
    echo "Starting HigherSelf Termius setup..."
    echo ""
    
    check_prerequisites
    setup_directories
    generate_ssh_keys
    setup_aws_integration
    prepare_termius_configs
    test_docker_setup
    create_quick_access_script
    print_next_steps
    
    log_success "Setup completed successfully!"
}

# Run main function
main "$@"
