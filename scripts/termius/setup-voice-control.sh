#!/bin/bash

# ======================================================
# TERMIUS VOICE CONTROL SETUP SCRIPT
# HigherSelf Network Server Voice-Activated Management
# ======================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TERMIUS_CONFIG_DIR="$PROJECT_ROOT/termius-setup"
VOICE_CONTROL_CONFIG="$TERMIUS_CONFIG_DIR/snippets-voice-control.json"
ENV_FILE="$PROJECT_ROOT/.env"

# Functions
print_header() {
    echo -e "${PURPLE}======================================================${NC}"
    echo -e "${PURPLE}🎤 TERMIUS VOICE CONTROL SETUP${NC}"
    echo -e "${PURPLE}HigherSelf Network Server Voice-Activated Management${NC}"
    echo -e "${PURPLE}======================================================${NC}"
    echo ""
}

print_section() {
    echo -e "${BLUE}📋 $1${NC}"
    echo "----------------------------------------"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

check_prerequisites() {
    print_section "Checking Prerequisites"
    
    # Check if Termius is installed
    if command -v termius &> /dev/null; then
        print_success "Termius CLI found"
    else
        print_warning "Termius CLI not found. Please install Termius Pro"
        print_info "Download from: https://termius.com/"
    fi
    
    # Check if Docker is installed
    if command -v docker &> /dev/null; then
        print_success "Docker found"
    else
        print_error "Docker not found. Please install Docker"
        exit 1
    fi
    
    # Check if docker-compose is installed
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose found"
    else
        print_error "Docker Compose not found. Please install Docker Compose"
        exit 1
    fi
    
    # Check if jq is installed
    if command -v jq &> /dev/null; then
        print_success "jq found"
    else
        print_warning "jq not found. Installing jq for JSON processing..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install jq
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-get update && sudo apt-get install -y jq
        fi
    fi
    
    # Check if curl is installed
    if command -v curl &> /dev/null; then
        print_success "curl found"
    else
        print_error "curl not found. Please install curl"
        exit 1
    fi
    
    echo ""
}

setup_environment() {
    print_section "Setting Up Environment"
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
            print_success ".env file created"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_success ".env file found"
    fi
    
    # Enable voice control in environment
    if grep -q "VOICE_COMMAND_ENABLED" "$ENV_FILE"; then
        sed -i.bak 's/VOICE_COMMAND_ENABLED=.*/VOICE_COMMAND_ENABLED=true/' "$ENV_FILE"
    else
        echo "VOICE_COMMAND_ENABLED=true" >> "$ENV_FILE"
    fi
    
    if grep -q "TERMIUS_VOICE_CONTROL_ENABLED" "$ENV_FILE"; then
        sed -i.bak 's/TERMIUS_VOICE_CONTROL_ENABLED=.*/TERMIUS_VOICE_CONTROL_ENABLED=true/' "$ENV_FILE"
    else
        echo "TERMIUS_VOICE_CONTROL_ENABLED=true" >> "$ENV_FILE"
    fi
    
    print_success "Voice control enabled in environment"
    echo ""
}

create_voice_control_scripts() {
    print_section "Creating Voice Control Scripts"
    
    # Create scripts directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/scripts/voice"
    
    # Create voice server control wrapper script
    cat > "$PROJECT_ROOT/scripts/voice/voice-server-control.sh" << 'EOF'
#!/bin/bash

# Voice Server Control Wrapper Script
# This script provides a command-line interface for voice-activated server control

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
fi

# Function to call the voice API
call_voice_api() {
    local command="$1"
    local environment="${2:-development}"
    
    curl -s -X POST "http://localhost:8000/voice/server/control" \
        -H "Content-Type: application/json" \
        -d "{\"command\": \"$command\", \"environment\": \"$environment\"}" | jq .
}

# Main command processing
case "${1:-help}" in
    "start")
        echo "🎤 Voice Command: Starting server..."
        call_voice_api "start higher self server" "${2:-development}"
        ;;
    "stop")
        echo "🎤 Voice Command: Stopping server..."
        call_voice_api "stop higher self server" "${2:-development}"
        ;;
    "restart")
        echo "🎤 Voice Command: Restarting server..."
        call_voice_api "restart higher self server" "${2:-development}"
        ;;
    "status")
        echo "🎤 Voice Command: Checking server status..."
        call_voice_api "server status" "${2:-development}"
        ;;
    "logs")
        echo "🎤 Voice Command: Showing server logs..."
        call_voice_api "show server logs" "${2:-development}"
        ;;
    "deploy")
        echo "🎤 Voice Command: Deploying server..."
        call_voice_api "deploy server" "${2:-development}"
        ;;
    "test")
        echo "🎤 Voice Command: Running tests..."
        call_voice_api "run tests" "${2:-development}"
        ;;
    "build")
        echo "🎤 Voice Command: Building server..."
        call_voice_api "build server" "${2:-development}"
        ;;
    "help"|*)
        echo "Voice Server Control Commands:"
        echo "  start [env]    - Start the server"
        echo "  stop [env]     - Stop the server"
        echo "  restart [env]  - Restart the server"
        echo "  status [env]   - Check server status"
        echo "  logs [env]     - Show server logs"
        echo "  deploy [env]   - Deploy the server"
        echo "  test [env]     - Run tests"
        echo "  build [env]    - Build server images"
        echo ""
        echo "Environment options: development, staging, production"
        echo "Default environment: development"
        ;;
esac
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/voice/voice-server-control.sh"
    print_success "Voice control wrapper script created"
    
    # Create Termius integration script
    cat > "$PROJECT_ROOT/scripts/voice/termius-voice-integration.sh" << 'EOF'
#!/bin/bash

# Termius Voice Integration Script
# This script sets up voice command integration with Termius

echo "🎤 Setting up Termius Voice Integration..."

# Check if Termius CLI is available
if ! command -v termius &> /dev/null; then
    echo "❌ Termius CLI not found. Please install Termius Pro"
    exit 1
fi

# Import voice control snippets
echo "📋 Importing voice control snippets..."
termius snippets import termius-setup/snippets-voice-control.json

# Set up voice recognition (if supported)
echo "🎙️  Configuring voice recognition..."
termius config set voice.enabled true
termius config set voice.confidence_threshold 0.8
termius config set voice.timeout 30

echo "✅ Termius voice integration setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Open Termius Pro"
echo "2. Connect to your HigherSelf server"
echo "3. Use voice commands like 'start higher self server'"
echo "4. Monitor execution in session logs"
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/voice/termius-voice-integration.sh"
    print_success "Termius integration script created"
    
    echo ""
}

setup_termius_configuration() {
    print_section "Setting Up Termius Configuration"
    
    # Create enhanced host configuration for voice control
    cat > "$TERMIUS_CONFIG_DIR/hosts-voice-control.json" << EOF
{
  "voice_control_hosts": {
    "environment": "voice-enabled",
    "description": "Voice-controlled HigherSelf Network Server hosts",
    "voice_integration": true
  },
  "hosts": [
    {
      "id": "higherself-voice-local",
      "name": "HigherSelf-Voice-Local",
      "address": "localhost",
      "hostname": "localhost",
      "port": 22,
      "username": "$(whoami)",
      "group": "Voice Control",
      "tags": ["voice", "local", "development", "higherself"],
      "description": "Local HigherSelf server with voice control enabled",
      "connection_type": "ssh",
      "voice_enabled": true,
      "auto_connect": true,
      "startup_snippets": [
        "voice-server-status"
      ],
      "voice_commands": {
        "start_server": "voice-server-start",
        "stop_server": "voice-server-stop",
        "restart_server": "voice-server-restart",
        "check_status": "voice-server-status",
        "show_logs": "voice-server-logs",
        "deploy": "voice-server-deploy",
        "run_tests": "voice-server-test",
        "build": "voice-server-build"
      },
      "environment_variables": {
        "ENVIRONMENT": "development",
        "VOICE_CONTROL_ENABLED": "true",
        "PROJECT_ROOT": "$PROJECT_ROOT"
      }
    }
  ]
}
EOF
    
    print_success "Voice control host configuration created"
    echo ""
}

test_voice_integration() {
    print_section "Testing Voice Integration"
    
    # Start the server if not running
    print_info "Checking if HigherSelf server is running..."
    if ! curl -s http://localhost:8000/health > /dev/null; then
        print_warning "Server not running. Starting server for testing..."
        cd "$PROJECT_ROOT"
        docker-compose up -d
        sleep 10
    fi
    
    # Test voice API endpoints
    print_info "Testing voice control API..."
    
    # Test server status command
    echo "Testing 'server status' command..."
    response=$(curl -s -X POST "http://localhost:8000/voice/server/control" \
        -H "Content-Type: application/json" \
        -d '{"command": "server status", "environment": "development"}')
    
    if echo "$response" | jq -e '.success' > /dev/null; then
        print_success "Voice control API is working"
    else
        print_error "Voice control API test failed"
        echo "Response: $response"
    fi
    
    echo ""
}

create_documentation() {
    print_section "Creating Documentation"
    
    cat > "$PROJECT_ROOT/TERMIUS_VOICE_CONTROL_GUIDE.md" << 'EOF'
# Termius Voice Control Setup Guide

## Overview

This guide explains how to set up and use voice-activated server management for the HigherSelf Network Server through Termius Pro.

## Prerequisites

- Termius Pro (with voice recognition support)
- HigherSelf Network Server running
- Docker and Docker Compose installed
- Microphone access enabled

## Voice Commands

### Server Management
- **"start higher self server"** - Start the server
- **"stop higher self server"** - Stop the server  
- **"restart higher self server"** - Restart the server
- **"server status"** - Check server status
- **"show server logs"** - Display recent logs

### Development Operations
- **"deploy server"** - Deploy to specified environment
- **"run tests"** - Execute test suite
- **"build server"** - Build Docker images

## Setup Instructions

1. **Install Termius Pro**
   ```bash
   # Download from https://termius.com/
   ```

2. **Run Setup Script**
   ```bash
   ./scripts/termius/setup-voice-control.sh
   ```

3. **Import Configuration**
   - Open Termius Pro
   - Go to Settings > Import
   - Import `termius-setup/hosts-voice-control.json`
   - Import `termius-setup/snippets-voice-control.json`

4. **Configure Voice Recognition**
   - Enable microphone access in Termius
   - Set confidence threshold to 0.8
   - Configure trigger phrases

## Usage

1. **Connect to Server**
   ```bash
   # In Termius, connect to "HigherSelf-Voice-Local"
   ```

2. **Use Voice Commands**
   - Speak clearly into microphone
   - Use exact trigger phrases
   - Wait for command confirmation

3. **Monitor Execution**
   - Watch command output in terminal
   - Check session logs for details
   - Verify results with status commands

## Troubleshooting

### Voice Recognition Issues
- Check microphone permissions
- Verify trigger phrase accuracy
- Adjust confidence threshold
- Test with manual commands first

### Server Connection Issues
- Verify SSH key setup
- Check server accessibility
- Confirm Docker services running
- Review environment variables

### API Endpoint Issues
- Ensure server is running on port 8000
- Check voice router endpoints
- Verify environment configuration
- Review server logs for errors

## Security Considerations

- Voice commands are logged for audit
- Production deployments require confirmation
- SSH keys should be properly secured
- Session recording is enabled by default

## Advanced Configuration

### Custom Voice Commands
Edit `termius-setup/snippets-voice-control.json` to add custom commands.

### Environment-Specific Settings
Configure different voice commands for development, staging, and production.

### Integration with CI/CD
Voice commands can trigger automated deployment pipelines.

## Support

For issues or questions:
1. Check server logs: `docker-compose logs`
2. Review voice API responses
3. Verify Termius configuration
4. Test manual command execution
EOF
    
    print_success "Documentation created: TERMIUS_VOICE_CONTROL_GUIDE.md"
    echo ""
}

main() {
    print_header
    
    print_info "Starting Termius Voice Control Setup..."
    print_info "Project Root: $PROJECT_ROOT"
    echo ""
    
    check_prerequisites
    setup_environment
    create_voice_control_scripts
    setup_termius_configuration
    test_voice_integration
    create_documentation
    
    print_section "Setup Complete!"
    print_success "Termius voice control setup completed successfully!"
    echo ""
    print_info "Next steps:"
    echo "1. Open Termius Pro"
    echo "2. Import the configuration files from termius-setup/"
    echo "3. Connect to 'HigherSelf-Voice-Local' host"
    echo "4. Try voice commands like 'server status'"
    echo "5. Review the documentation in TERMIUS_VOICE_CONTROL_GUIDE.md"
    echo ""
    print_info "Voice commands available:"
    echo "• start higher self server"
    echo "• stop higher self server"
    echo "• restart higher self server"
    echo "• server status"
    echo "• show server logs"
    echo "• deploy server"
    echo "• run tests"
    echo "• build server"
    echo ""
    print_warning "Remember to enable microphone access in Termius Pro!"
}

# Run main function
main "$@"
