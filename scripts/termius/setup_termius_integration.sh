#!/bin/bash

# Setup Termius Integration for HigherSelf Network Server
# This script configures Termius for GitHub Actions integration and monitoring

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TERMIUS_CONFIG_DIR="$HOME/.termius_higherself"
GITHUB_REPO="Utak-West/The-HigherSelf-Network-Server"

# Print functions
print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              HigherSelf Network Server                       ║"
    echo "║             Termius Integration Setup                        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${CYAN}[STEP] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

print_info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check if running on macOS (Termius is primarily used on macOS/iOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_success "Running on macOS - Termius compatible"
    else
        print_warning "Not running on macOS - ensure Termius is available on your platform"
    fi
    
    # Check for required tools
    local missing_tools=()
    
    if ! command -v curl &> /dev/null; then
        missing_tools+=("curl")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing_tools+=("jq")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    fi
    
    if ! command -v pip3 &> /dev/null; then
        missing_tools+=("pip3")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_info "Please install the missing tools and run this script again"
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Create configuration directory
create_config_directory() {
    print_step "Creating configuration directory..."
    
    mkdir -p "$TERMIUS_CONFIG_DIR"
    mkdir -p "$TERMIUS_CONFIG_DIR/scripts"
    mkdir -p "$TERMIUS_CONFIG_DIR/logs"
    
    print_success "Configuration directory created at $TERMIUS_CONFIG_DIR"
}

# Install Python dependencies
install_python_dependencies() {
    print_step "Installing Python dependencies..."
    
    # Create requirements file for Termius integration
    cat > "$TERMIUS_CONFIG_DIR/requirements.txt" << EOF
aiohttp>=3.8.0
requests>=2.28.0
rich>=12.0.0
pydantic>=1.10.0
fastapi>=0.95.0
uvicorn>=0.20.0
python-dotenv>=1.0.0
websockets>=11.0.0
EOF
    
    # Install dependencies
    pip3 install -r "$TERMIUS_CONFIG_DIR/requirements.txt"
    
    print_success "Python dependencies installed"
}

# Setup GitHub integration
setup_github_integration() {
    print_step "Setting up GitHub integration..."
    
    # Check if GitHub CLI is available
    if command -v gh &> /dev/null; then
        print_info "GitHub CLI detected - checking authentication..."
        if gh auth status &> /dev/null; then
            print_success "GitHub CLI authenticated"
            
            # Get GitHub token
            GITHUB_TOKEN=$(gh auth token 2>/dev/null || echo "")
            if [ -n "$GITHUB_TOKEN" ]; then
                print_success "GitHub token obtained from CLI"
            else
                print_warning "Could not obtain GitHub token from CLI"
            fi
        else
            print_warning "GitHub CLI not authenticated"
        fi
    else
        print_info "GitHub CLI not found - manual token setup required"
    fi
    
    # Create GitHub configuration
    cat > "$TERMIUS_CONFIG_DIR/github_config.sh" << EOF
#!/bin/bash
# GitHub Configuration for Termius Integration

# Repository information
export GITHUB_REPO_OWNER="Utak-West"
export GITHUB_REPO_NAME="The-HigherSelf-Network-Server"
export GITHUB_REPO_FULL="$GITHUB_REPO"

# GitHub token (set this manually if not using GitHub CLI)
export GITHUB_TOKEN="${GITHUB_TOKEN:-your_github_token_here}"

# API endpoints
export GITHUB_API_BASE="https://api.github.com"
export GITHUB_ACTIONS_API="\$GITHUB_API_BASE/repos/\$GITHUB_REPO_FULL/actions"
EOF
    
    chmod +x "$TERMIUS_CONFIG_DIR/github_config.sh"
    print_success "GitHub configuration created"
}

# Setup Termius scripts
setup_termius_scripts() {
    print_step "Setting up Termius scripts..."
    
    # Copy monitoring scripts
    cp "$SCRIPT_DIR/termius_monitor.sh" "$TERMIUS_CONFIG_DIR/scripts/"
    cp "$SCRIPT_DIR/build_status_monitor.py" "$TERMIUS_CONFIG_DIR/scripts/"
    
    # Make scripts executable
    chmod +x "$TERMIUS_CONFIG_DIR/scripts/"*.sh
    chmod +x "$TERMIUS_CONFIG_DIR/scripts/"*.py
    
    # Create wrapper scripts
    cat > "$TERMIUS_CONFIG_DIR/scripts/start_monitor.sh" << 'EOF'
#!/bin/bash
# Start Termius Monitor for HigherSelf Network Server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(dirname "$SCRIPT_DIR")"

# Load GitHub configuration
source "$CONFIG_DIR/github_config.sh"

# Start the monitor
"$SCRIPT_DIR/termius_monitor.sh" monitor
EOF
    
    cat > "$TERMIUS_CONFIG_DIR/scripts/start_build_monitor.sh" << 'EOF'
#!/bin/bash
# Start Build Status Monitor for HigherSelf Network Server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(dirname "$SCRIPT_DIR")"

# Load GitHub configuration
source "$CONFIG_DIR/github_config.sh"

# Start the build monitor
python3 "$SCRIPT_DIR/build_status_monitor.py" \
    --token "$GITHUB_TOKEN" \
    --owner "$GITHUB_REPO_OWNER" \
    --repo "$GITHUB_REPO_NAME" \
    --interval 30
EOF
    
    chmod +x "$TERMIUS_CONFIG_DIR/scripts/start_monitor.sh"
    chmod +x "$TERMIUS_CONFIG_DIR/scripts/start_build_monitor.sh"
    
    print_success "Termius scripts configured"
}

# Create Termius connection profiles
create_termius_profiles() {
    print_step "Creating Termius connection profiles..."
    
    # Create connection profile templates
    cat > "$TERMIUS_CONFIG_DIR/termius_profiles.json" << EOF
{
  "profiles": [
    {
      "name": "HigherSelf-Local-Dev",
      "description": "Local development environment",
      "host": "localhost",
      "port": 22,
      "username": "$(whoami)",
      "environment": "development",
      "tags": ["higherself", "development", "local"],
      "startup_commands": [
        "cd $PROJECT_ROOT",
        "source venv/bin/activate",
        "$TERMIUS_CONFIG_DIR/scripts/start_monitor.sh"
      ]
    },
    {
      "name": "HigherSelf-Monitor",
      "description": "Dedicated monitoring terminal",
      "host": "localhost",
      "port": 22,
      "username": "$(whoami)",
      "environment": "monitoring",
      "tags": ["higherself", "monitoring"],
      "startup_commands": [
        "$TERMIUS_CONFIG_DIR/scripts/start_build_monitor.sh"
      ]
    }
  ]
}
EOF
    
    print_success "Termius connection profiles created"
}

# Setup webhook endpoint
setup_webhook_endpoint() {
    print_step "Setting up webhook endpoint configuration..."
    
    # Create webhook configuration
    cat > "$TERMIUS_CONFIG_DIR/webhook_config.sh" << EOF
#!/bin/bash
# Webhook Configuration for Termius Integration

# Local webhook endpoint (when running HigherSelf Network Server locally)
export TERMIUS_WEBHOOK_URL="http://localhost:8000/api/termius/webhooks/github-actions"

# Production webhook endpoint (update with your production URL)
export TERMIUS_WEBHOOK_URL_PROD="https://your-production-domain.com/api/termius/webhooks/github-actions"

# Webhook secret (generate a secure secret)
export TERMIUS_WEBHOOK_SECRET="$(openssl rand -hex 32)"

echo "Webhook configuration:"
echo "Local URL: \$TERMIUS_WEBHOOK_URL"
echo "Production URL: \$TERMIUS_WEBHOOK_URL_PROD"
echo "Secret: \$TERMIUS_WEBHOOK_SECRET"
EOF
    
    chmod +x "$TERMIUS_CONFIG_DIR/webhook_config.sh"
    print_success "Webhook endpoint configuration created"
}

# Create documentation
create_documentation() {
    print_step "Creating documentation..."
    
    cat > "$TERMIUS_CONFIG_DIR/README.md" << EOF
# HigherSelf Network Server - Termius Integration

This directory contains the Termius integration setup for the HigherSelf Network Server project.

## Files and Directories

- \`scripts/\` - Monitoring and integration scripts
- \`logs/\` - Log files from monitoring scripts
- \`github_config.sh\` - GitHub API configuration
- \`webhook_config.sh\` - Webhook endpoint configuration
- \`termius_profiles.json\` - Termius connection profile templates
- \`requirements.txt\` - Python dependencies

## Quick Start

1. **Configure GitHub Token**:
   \`\`\`bash
   # Edit github_config.sh and set your GitHub token
   nano github_config.sh
   \`\`\`

2. **Start Monitoring**:
   \`\`\`bash
   # Start the general monitor
   ./scripts/start_monitor.sh
   
   # Or start the build status monitor
   ./scripts/start_build_monitor.sh
   \`\`\`

3. **Test Integration**:
   \`\`\`bash
   # Test the monitoring setup
   ./scripts/termius_monitor.sh test
   \`\`\`

## Termius Setup

1. **Import Connection Profiles**:
   - Use the templates in \`termius_profiles.json\`
   - Create connections for different environments
   - Set up SSH keys and authentication

2. **Configure Startup Commands**:
   - Set startup commands to automatically start monitoring
   - Configure environment-specific settings

3. **Team Collaboration**:
   - Share connection profiles with team members
   - Set up role-based access control
   - Configure team notifications

## GitHub Actions Integration

The integration automatically receives notifications from GitHub Actions workflows and displays them in your Termius terminals.

### Webhook Setup

1. Add the webhook URL to your GitHub repository settings
2. Configure the webhook secret for security
3. Test the webhook with a sample workflow run

### Supported Events

- Workflow started/completed
- Build success/failure
- Deployment notifications
- Security scan results

## Troubleshooting

- Check logs in the \`logs/\` directory
- Verify GitHub token permissions
- Test webhook connectivity
- Ensure Python dependencies are installed

For more information, see the main project documentation.
EOF
    
    print_success "Documentation created"
}

# Main setup function
main() {
    print_header
    
    print_info "Setting up Termius integration for HigherSelf Network Server..."
    print_info "This will configure monitoring, GitHub Actions integration, and terminal automation."
    echo ""
    
    # Run setup steps
    check_prerequisites
    create_config_directory
    install_python_dependencies
    setup_github_integration
    setup_termius_scripts
    create_termius_profiles
    setup_webhook_endpoint
    create_documentation
    
    echo ""
    print_success "Termius integration setup completed!"
    echo ""
    print_info "Next steps:"
    echo "1. Edit $TERMIUS_CONFIG_DIR/github_config.sh to set your GitHub token"
    echo "2. Configure Termius connection profiles using the templates"
    echo "3. Set up GitHub webhook in repository settings"
    echo "4. Test the integration with: $TERMIUS_CONFIG_DIR/scripts/termius_monitor.sh test"
    echo ""
    print_info "Configuration directory: $TERMIUS_CONFIG_DIR"
    print_info "Documentation: $TERMIUS_CONFIG_DIR/README.md"

    # Make setup script executable
    chmod +x "$0"
}

# Run main function
main "$@"
