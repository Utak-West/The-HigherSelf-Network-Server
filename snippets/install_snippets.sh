#!/bin/bash
# HigherSelf Network Server - Snippets Installation Script
# Installs enhanced business-specific productivity snippets for Raycast and Termius

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SNIPPETS_FILE="$SCRIPT_DIR/raycast/enhanced_business_technical_snippets.json"
README_FILE="$SCRIPT_DIR/raycast/ENHANCED_SNIPPETS_README.md"
RAYCAST_SNIPPETS_DIR="$HOME/Library/Application Support/com.raycast.macos/snippets"
TERMIUS_SNIPPETS_DIR="$HOME/.termius/snippets"

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Raycast is installed
check_raycast() {
    if ! command -v raycast &> /dev/null; then
        warning "Raycast is not installed or not in PATH"
        echo "Please install Raycast from: https://raycast.com/"
        return 1
    fi
    success "Raycast is installed"
    return 0
}

# Check if 1Password CLI is installed
check_1password_cli() {
    if ! command -v op &> /dev/null; then
        warning "1Password CLI is not installed"
        echo "Install with: brew install --cask 1password-cli"
        echo "Then authenticate with: op signin"
        return 1
    fi
    
    # Check if authenticated
    if ! op whoami &> /dev/null; then
        warning "1Password CLI is not authenticated"
        echo "Please authenticate with: op signin"
        return 1
    fi
    
    success "1Password CLI is installed and authenticated"
    return 0
}

# Check if Termius is installed
check_termius() {
    if [ ! -d "/Applications/Termius.app" ]; then
        warning "Termius is not installed"
        echo "Please install Termius from: https://termius.com/"
        return 1
    fi
    success "Termius is installed"
    return 0
}

# Install Raycast snippets
install_raycast_snippets() {
    log "Installing Raycast snippets..."
    
    # Create Raycast snippets directory if it doesn't exist
    mkdir -p "$RAYCAST_SNIPPETS_DIR"
    
    # Copy snippets file
    if [ -f "$SNIPPETS_FILE" ]; then
        cp "$SNIPPETS_FILE" "$RAYCAST_SNIPPETS_DIR/"
        success "Copied enhanced snippets to Raycast directory"
    else
        error "Snippets file not found: $SNIPPETS_FILE"
        return 1
    fi
    
    # Copy README
    if [ -f "$README_FILE" ]; then
        cp "$README_FILE" "$RAYCAST_SNIPPETS_DIR/"
        success "Copied README to Raycast directory"
    fi
    
    # Try to refresh Raycast snippets
    if command -v raycast &> /dev/null; then
        raycast refresh-snippets 2>/dev/null || true
        success "Refreshed Raycast snippets"
    fi
    
    return 0
}

# Install Termius snippets
install_termius_snippets() {
    log "Installing Termius snippets..."
    
    # Create Termius snippets directory if it doesn't exist
    mkdir -p "$TERMIUS_SNIPPETS_DIR"
    
    # Extract Termius-specific snippets (voice control snippets)
    if [ -f "$SNIPPETS_FILE" ]; then
        # Create a filtered version for Termius with voice control snippets
        jq '[.[] | select(.keyword | startswith("!termvoice") or startswith("!term"))]' "$SNIPPETS_FILE" > "$TERMIUS_SNIPPETS_DIR/higherself_voice_control.json"
        success "Created Termius voice control snippets"
    fi
    
    # Create Termius SSH profiles
    cat > "$TERMIUS_SNIPPETS_DIR/higherself_ssh_profiles.json" << 'EOF'
{
  "profiles": [
    {
      "name": "HigherSelf-Server-Dev",
      "host": "localhost",
      "port": 22,
      "username": "$(op read 'op://HigherSelf/Server-Access/username')",
      "key_path": "~/.ssh/higherself_server_key",
      "tags": ["higherself", "development", "server"],
      "startup_commands": [
        "cd ~/higherself-network-server",
        "source venv/bin/activate",
        "./scripts/server-status.sh"
      ]
    },
    {
      "name": "HigherSelf-Server-Prod",
      "host": "$(op read 'op://HigherSelf/Server-Access/hostname')",
      "port": 22,
      "username": "$(op read 'op://HigherSelf/Server-Access/username')",
      "key_path": "~/.ssh/higherself_server_key",
      "tags": ["higherself", "production", "server"],
      "startup_commands": [
        "cd ~/higherself-network-server",
        "source venv/bin/activate",
        "docker-compose ps"
      ]
    }
  ]
}
EOF
    success "Created Termius SSH profiles"
    
    return 0
}

# Create desktop shortcuts
create_desktop_shortcuts() {
    log "Creating desktop shortcuts..."
    
    # Copy files to desktop
    cp "$SNIPPETS_FILE" "$HOME/Desktop/" 2>/dev/null || true
    cp "$README_FILE" "$HOME/Desktop/" 2>/dev/null || true
    
    success "Copied snippets and documentation to Desktop"
    return 0
}

# Validate snippets file
validate_snippets() {
    log "Validating snippets file..."
    
    if [ ! -f "$SNIPPETS_FILE" ]; then
        error "Snippets file not found: $SNIPPETS_FILE"
        return 1
    fi
    
    # Check if it's valid JSON
    if ! jq empty "$SNIPPETS_FILE" 2>/dev/null; then
        error "Snippets file is not valid JSON"
        return 1
    fi
    
    # Count snippets
    SNIPPET_COUNT=$(jq length "$SNIPPETS_FILE")
    success "Validated $SNIPPET_COUNT snippets in file"
    
    # Check for required fields
    MISSING_FIELDS=$(jq -r '.[] | select(.name == null or .text == null or .keyword == null) | .keyword // "unknown"' "$SNIPPETS_FILE")
    if [ -n "$MISSING_FIELDS" ]; then
        error "Some snippets are missing required fields: $MISSING_FIELDS"
        return 1
    fi
    
    success "All snippets have required fields"
    return 0
}

# Display installation summary
show_summary() {
    echo ""
    echo -e "${BLUE}📋 Installation Summary${NC}"
    echo "=================================="
    
    if [ -f "$RAYCAST_SNIPPETS_DIR/enhanced_business_technical_snippets.json" ]; then
        SNIPPET_COUNT=$(jq length "$RAYCAST_SNIPPETS_DIR/enhanced_business_technical_snippets.json")
        success "Raycast: $SNIPPET_COUNT snippets installed"
    fi
    
    if [ -f "$TERMIUS_SNIPPETS_DIR/higherself_voice_control.json" ]; then
        TERMIUS_COUNT=$(jq length "$TERMIUS_SNIPPETS_DIR/higherself_voice_control.json")
        success "Termius: $TERMIUS_COUNT voice control snippets installed"
    fi
    
    if [ -f "$HOME/Desktop/enhanced_business_technical_snippets.json" ]; then
        success "Desktop: Files copied for easy access"
    fi
    
    echo ""
    echo -e "${BLUE}🚀 Next Steps${NC}"
    echo "=================================="
    echo "1. Open Raycast and refresh snippets (Cmd+Shift+P → 'Reload Snippets')"
    echo "2. Configure 1Password CLI if not already done: op signin"
    echo "3. Set up Termius SSH profiles using the generated configuration"
    echo "4. Test a snippet: Type '!hsnstatus' in any text field"
    echo "5. Review the README file on your Desktop for detailed usage instructions"
    echo ""
    echo -e "${GREEN}✨ Installation completed successfully!${NC}"
}

# Main installation function
main() {
    echo -e "${BLUE}🚀 HigherSelf Network Server - Snippets Installation${NC}"
    echo "======================================================"
    echo ""
    
    # Validate snippets file first
    if ! validate_snippets; then
        error "Snippets validation failed. Aborting installation."
        exit 1
    fi
    
    # Check prerequisites
    log "Checking prerequisites..."
    RAYCAST_OK=false
    ONEPASSWORD_OK=false
    TERMIUS_OK=false
    
    check_raycast && RAYCAST_OK=true
    check_1password_cli && ONEPASSWORD_OK=true
    check_termius && TERMIUS_OK=true
    
    echo ""
    
    # Install components based on what's available
    if [ "$RAYCAST_OK" = true ]; then
        install_raycast_snippets
    else
        warning "Skipping Raycast installation due to missing prerequisites"
    fi
    
    if [ "$TERMIUS_OK" = true ]; then
        install_termius_snippets
    else
        warning "Skipping Termius installation due to missing prerequisites"
    fi
    
    # Always create desktop shortcuts
    create_desktop_shortcuts
    
    # Show summary
    show_summary
}

# Run main function
main "$@"
