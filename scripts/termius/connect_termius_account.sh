#!/bin/bash

# Connect Termius Account to HigherSelf Network Server
# This script sets up automatic notifications to your Termius terminals

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
CONFIG_DIR="$HOME/.termius_higherself"
NOTIFICATION_SCRIPT="$SCRIPT_DIR/termius_ssh_notifier.py"

print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              Connect Termius Account                         ║"
    echo "║           HigherSelf Network Server                          ║"
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

# Check if SSH notifier dependencies are installed
check_dependencies() {
    print_step "Checking dependencies..."
    
    if ! python3 -c "import paramiko" 2>/dev/null; then
        print_warning "paramiko not installed. Installing..."
        pip3 install paramiko
    fi
    
    if ! python3 -c "import rich" 2>/dev/null; then
        print_warning "rich not installed. Installing..."
        pip3 install rich
    fi
    
    print_success "Dependencies checked"
}

# Setup SSH key for notifications
setup_ssh_key() {
    print_step "Setting up SSH key for notifications..."
    
    SSH_KEY_PATH="$HOME/.ssh/termius_higherself_notifications"
    
    if [ ! -f "$SSH_KEY_PATH" ]; then
        print_info "Generating SSH key for Termius notifications..."
        ssh-keygen -t ed25519 -f "$SSH_KEY_PATH" -N "" -C "termius-higherself-notifications"
        print_success "SSH key generated: $SSH_KEY_PATH"
    else
        print_info "SSH key already exists: $SSH_KEY_PATH"
    fi
    
    # Add to authorized_keys for localhost connections
    if [ -f "$SSH_KEY_PATH.pub" ]; then
        mkdir -p "$HOME/.ssh"
        touch "$HOME/.ssh/authorized_keys"
        
        # Check if key is already in authorized_keys
        if ! grep -q "$(cat "$SSH_KEY_PATH.pub")" "$HOME/.ssh/authorized_keys" 2>/dev/null; then
            cat "$SSH_KEY_PATH.pub" >> "$HOME/.ssh/authorized_keys"
            chmod 600 "$HOME/.ssh/authorized_keys"
            print_success "SSH key added to authorized_keys"
        else
            print_info "SSH key already in authorized_keys"
        fi
    fi
    
    echo "$SSH_KEY_PATH"
}

# Register current terminal session
register_current_session() {
    local ssh_key_path="$1"
    
    print_step "Registering current terminal session..."
    
    # Get current user and hostname
    CURRENT_USER=$(whoami)
    CURRENT_HOST="localhost"
    
    # Register the session
    python3 "$NOTIFICATION_SCRIPT" register \
        --host "$CURRENT_HOST" \
        --username "$CURRENT_USER" \
        --key-file "$ssh_key_path"
    
    print_success "Current session registered for notifications"
}

# Test the notification system
test_notifications() {
    print_step "Testing notification system..."
    
    python3 "$NOTIFICATION_SCRIPT" test
    
    print_success "Test notification sent!"
    print_info "Check your terminal for the test notification"
}

# Create Termius startup script
create_termius_startup_script() {
    print_step "Creating Termius startup script..."
    
    STARTUP_SCRIPT="$CONFIG_DIR/scripts/termius_startup.sh"
    mkdir -p "$(dirname "$STARTUP_SCRIPT")"
    
    cat > "$STARTUP_SCRIPT" << 'EOF'
#!/bin/bash
# Termius Startup Script for HigherSelf Network Server
# This script runs when you connect to a terminal via Termius

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              HigherSelf Network Server                       ║"
echo "║                 Termius Connected                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}✅ Connected to HigherSelf Network Server${NC}"
echo -e "${BLUE}📡 Real-time GitHub Actions notifications enabled${NC}"
echo -e "${BLUE}🔔 You will receive build and deployment alerts here${NC}"
echo ""

# Register this session for notifications
SCRIPT_DIR="$HOME/.termius_higherself/scripts"
if [ -f "$SCRIPT_DIR/termius_ssh_notifier.py" ]; then
    python3 "$SCRIPT_DIR/termius_ssh_notifier.py" register \
        --host "localhost" \
        --username "$(whoami)" \
        --key-file "$HOME/.ssh/termius_higherself_notifications" 2>/dev/null || true
fi

# Show recent notifications if available
if [ -f "$HOME/.termius_higherself/scripts/termius_monitor.sh" ]; then
    echo -e "${BLUE}Recent Activity:${NC}"
    "$HOME/.termius_higherself/scripts/termius_monitor.sh" history 2>/dev/null || echo "No recent activity"
fi

echo ""
echo -e "${GREEN}Ready for development! 🚀${NC}"
EOF
    
    chmod +x "$STARTUP_SCRIPT"
    print_success "Startup script created: $STARTUP_SCRIPT"
}

# Create Termius connection profiles
create_termius_connection_guide() {
    print_step "Creating Termius connection guide..."
    
    GUIDE_FILE="$CONFIG_DIR/TERMIUS_CONNECTION_GUIDE.md"
    
    cat > "$GUIDE_FILE" << EOF
# Termius Connection Guide - HigherSelf Network Server

## Quick Setup in Termius

### 1. Create New Host Connection

1. Open Termius app
2. Click "+" to add new host
3. Configure as follows:

\`\`\`
Name: HigherSelf-Notifications
Address: localhost (or your server IP)
Port: 22
Username: $(whoami)
\`\`\`

### 2. SSH Key Setup

1. In Termius, go to Keychain
2. Add new key: "HigherSelf-Notifications"
3. Import private key from: \`$HOME/.ssh/termius_higherself_notifications\`

### 3. Configure Startup Command

In the host settings, set startup command:
\`\`\`
$CONFIG_DIR/scripts/termius_startup.sh
\`\`\`

### 4. Test Connection

1. Connect to the host in Termius
2. You should see the HigherSelf welcome message
3. Test notifications with: \`python3 $NOTIFICATION_SCRIPT test\`

## Automatic Notifications

Once connected, you'll automatically receive:
- ✅ Build success/failure notifications
- 🚀 Deployment status updates
- 🔒 Security scan results
- ⚠️ Error alerts

## Manual Commands

\`\`\`bash
# Send test notification
python3 $NOTIFICATION_SCRIPT test

# Send custom notification
python3 $NOTIFICATION_SCRIPT send --message "Custom message" --type success

# List active sessions
python3 $NOTIFICATION_SCRIPT list

# Register new session
python3 $NOTIFICATION_SCRIPT register --host localhost --username $(whoami)
\`\`\`

## Troubleshooting

1. **No notifications received**:
   - Check SSH connection: \`ssh localhost\`
   - Verify key permissions: \`chmod 600 ~/.ssh/termius_higherself_notifications\`
   - Test manually: \`python3 $NOTIFICATION_SCRIPT test\`

2. **Permission denied**:
   - Check authorized_keys: \`cat ~/.ssh/authorized_keys\`
   - Verify SSH service is running: \`sudo systemctl status ssh\`

3. **Script not found**:
   - Run setup again: \`$SCRIPT_DIR/connect_termius_account.sh\`
   - Check file permissions: \`ls -la $CONFIG_DIR/scripts/\`

For more help, see the main documentation: \`docs/TERMIUS_INTEGRATION_GUIDE.md\`
EOF
    
    print_success "Connection guide created: $GUIDE_FILE"
}

# Update the notification service to use SSH
update_notification_service() {
    print_step "Updating notification service..."
    
    # Copy the SSH notifier to the config directory
    cp "$NOTIFICATION_SCRIPT" "$CONFIG_DIR/scripts/"
    chmod +x "$CONFIG_DIR/scripts/termius_ssh_notifier.py"
    
    # Create a webhook handler that uses SSH notifications
    WEBHOOK_HANDLER="$CONFIG_DIR/scripts/webhook_to_ssh.py"
    
    cat > "$WEBHOOK_HANDLER" << 'EOF'
#!/usr/bin/env python3
"""
Webhook to SSH Notification Bridge
Receives GitHub Actions webhooks and sends them via SSH to Termius
"""

import json
import sys
import os
from pathlib import Path

# Add the script directory to Python path
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

from termius_ssh_notifier import TermiusSSHNotifier

def handle_github_webhook(webhook_data):
    """Handle GitHub Actions webhook and send SSH notification."""
    notifier = TermiusSSHNotifier()
    
    # Extract relevant data
    workflow_data = {
        "status": webhook_data.get("data", {}).get("status", "unknown"),
        "workflow": webhook_data.get("data", {}).get("workflow", "Unknown"),
        "branch": webhook_data.get("data", {}).get("branch", "unknown"),
        "commit_sha": webhook_data.get("data", {}).get("commit_sha", "unknown"),
        "actor": webhook_data.get("data", {}).get("actor", "unknown"),
        "run_url": webhook_data.get("data", {}).get("run_url")
    }
    
    notifier.send_github_actions_notification(workflow_data)

if __name__ == "__main__":
    # Read webhook data from stdin or command line
    if len(sys.argv) > 1:
        webhook_data = json.loads(sys.argv[1])
    else:
        webhook_data = json.load(sys.stdin)
    
    handle_github_webhook(webhook_data)
EOF
    
    chmod +x "$WEBHOOK_HANDLER"
    print_success "Notification service updated"
}

# Main setup function
main() {
    print_header
    
    print_info "This script will connect your Termius account to receive real-time notifications"
    print_info "from the HigherSelf Network Server GitHub Actions workflows."
    echo ""
    
    # Check if config directory exists
    if [ ! -d "$CONFIG_DIR" ]; then
        print_error "Configuration directory not found: $CONFIG_DIR"
        print_info "Please run the setup script first: ./scripts/termius/setup_termius_integration.sh"
        exit 1
    fi
    
    # Run setup steps
    check_dependencies
    ssh_key_path=$(setup_ssh_key)
    register_current_session "$ssh_key_path"
    create_termius_startup_script
    create_termius_connection_guide
    update_notification_service
    
    echo ""
    print_success "Termius account connection setup completed!"
    echo ""
    print_info "Next steps:"
    echo "1. Open Termius app on your device"
    echo "2. Follow the guide: $CONFIG_DIR/TERMIUS_CONNECTION_GUIDE.md"
    echo "3. Create a new host connection to localhost"
    echo "4. Import the SSH key: $ssh_key_path"
    echo "5. Set startup command: $CONFIG_DIR/scripts/termius_startup.sh"
    echo ""
    print_info "Test the connection:"
    echo "python3 $NOTIFICATION_SCRIPT test"
    echo ""
    
    # Send test notification
    print_step "Sending test notification..."
    test_notifications
}

# Run main function
main "$@"
