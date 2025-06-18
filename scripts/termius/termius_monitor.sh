#!/bin/bash

# Termius Monitor Script for HigherSelf Network Server
# This script provides real-time monitoring and notifications in Termius terminals

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_FILE="$HOME/.termius_higherself_config"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_API_BASE_URL="http://localhost:8000"
DEFAULT_ENVIRONMENT="development"
DEFAULT_POLL_INTERVAL=30

# Load configuration
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        source "$CONFIG_FILE"
    fi
    
    # Set defaults if not configured
    API_BASE_URL="${API_BASE_URL:-$DEFAULT_API_BASE_URL}"
    ENVIRONMENT="${ENVIRONMENT:-$DEFAULT_ENVIRONMENT}"
    POLL_INTERVAL="${POLL_INTERVAL:-$DEFAULT_POLL_INTERVAL}"
    SESSION_ID="${SESSION_ID:-$(uuidgen)}"
    USER_ID="${USER_ID:-$(whoami)}"
    HOST_NAME="${HOST_NAME:-$(hostname)}"
}

# Save configuration
save_config() {
    cat > "$CONFIG_FILE" << EOF
# Termius HigherSelf Network Server Configuration
API_BASE_URL="$API_BASE_URL"
ENVIRONMENT="$ENVIRONMENT"
POLL_INTERVAL="$POLL_INTERVAL"
SESSION_ID="$SESSION_ID"
USER_ID="$USER_ID"
HOST_NAME="$HOST_NAME"
EOF
    echo -e "${GREEN}Configuration saved to $CONFIG_FILE${NC}"
}

# Print banner
print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                 HigherSelf Network Server                    ║"
    echo "║                    Termius Monitor                          ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Print status
print_status() {
    local status="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$status" in
        "success"|"healthy")
            echo -e "${GREEN}[${timestamp}] ✅ ${message}${NC}"
            ;;
        "failure"|"error"|"unhealthy")
            echo -e "${RED}[${timestamp}] ❌ ${message}${NC}"
            ;;
        "warning"|"degraded")
            echo -e "${YELLOW}[${timestamp}] ⚠️  ${message}${NC}"
            ;;
        "info")
            echo -e "${BLUE}[${timestamp}] ℹ️  ${message}${NC}"
            ;;
        *)
            echo -e "${WHITE}[${timestamp}] ${message}${NC}"
            ;;
    esac
}

# Register terminal session
register_session() {
    print_status "info" "Registering terminal session..."
    
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{
            \"session_id\": \"$SESSION_ID\",
            \"user_id\": \"$USER_ID\",
            \"host\": \"$HOST_NAME\",
            \"environment\": \"$ENVIRONMENT\"
        }" \
        "$API_BASE_URL/api/termius/sessions/register" 2>/dev/null || echo '{"success": false}')
    
    if echo "$response" | grep -q '"success": true'; then
        print_status "success" "Terminal session registered successfully"
        return 0
    else
        print_status "error" "Failed to register terminal session"
        return 1
    fi
}

# Unregister terminal session
unregister_session() {
    print_status "info" "Unregistering terminal session..."
    
    curl -s -X DELETE "$API_BASE_URL/api/termius/sessions/$SESSION_ID" >/dev/null 2>&1
    print_status "info" "Terminal session unregistered"
}

# Get service status
get_service_status() {
    local response=$(curl -s "$API_BASE_URL/api/termius/status" 2>/dev/null || echo '{"success": false}')
    
    if echo "$response" | grep -q '"success": true'; then
        local active_sessions=$(echo "$response" | grep -o '"active_sessions": [0-9]*' | cut -d':' -f2 | tr -d ' ')
        local recent_notifications=$(echo "$response" | grep -o '"recent_notifications": [0-9]*' | cut -d':' -f2 | tr -d ' ')
        
        print_status "success" "Service Status: Healthy"
        print_status "info" "Active Sessions: $active_sessions"
        print_status "info" "Recent Notifications: $recent_notifications"
        return 0
    else
        print_status "error" "Service Status: Unavailable"
        return 1
    fi
}

# Get notification history
get_notification_history() {
    local limit="${1:-10}"
    
    print_status "info" "Fetching recent notifications..."
    
    local response=$(curl -s "$API_BASE_URL/api/termius/notifications/history?limit=$limit" 2>/dev/null || echo '{"success": false}')
    
    if echo "$response" | grep -q '"success": true'; then
        echo -e "${CYAN}Recent Notifications:${NC}"
        echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    notifications = data.get('notifications', [])
    if not notifications:
        print('  No recent notifications')
    else:
        for notif in notifications[-5:]:  # Show last 5
            timestamp = notif.get('timestamp', 'Unknown')
            event_type = notif.get('event_type', 'Unknown')
            status = notif.get('data', {}).get('status', 'unknown')
            workflow = notif.get('data', {}).get('workflow', 'Unknown')
            print(f'  • {timestamp[:19]} - {workflow} ({event_type}) - {status}')
except:
    print('  Error parsing notifications')
"
    else
        print_status "error" "Failed to fetch notification history"
    fi
}

# Monitor mode - continuous monitoring
monitor_mode() {
    print_status "info" "Starting monitor mode (polling every ${POLL_INTERVAL}s)"
    print_status "info" "Press Ctrl+C to stop monitoring"
    
    # Register session
    register_session
    
    # Trap to unregister on exit
    trap 'unregister_session; exit 0' INT TERM
    
    while true; do
        clear
        print_banner
        echo -e "${WHITE}Environment: $ENVIRONMENT | Session: ${SESSION_ID:0:8}...${NC}"
        echo -e "${WHITE}$(date '+%Y-%m-%d %H:%M:%S UTC')${NC}"
        echo ""
        
        # Check service status
        get_service_status
        echo ""
        
        # Get recent notifications
        get_notification_history 5
        echo ""
        
        # Wait for next poll
        sleep "$POLL_INTERVAL"
    done
}

# Send test notification
send_test_notification() {
    print_status "info" "Sending test notification..."
    
    local response=$(curl -s -X POST "$API_BASE_URL/api/termius/test/notification" 2>/dev/null || echo '{"success": false}')
    
    if echo "$response" | grep -q '"success": true'; then
        print_status "success" "Test notification sent successfully"
    else
        print_status "error" "Failed to send test notification"
    fi
}

# Configuration setup
setup_config() {
    echo -e "${YELLOW}Setting up Termius Monitor Configuration${NC}"
    echo ""
    
    read -p "API Base URL [$API_BASE_URL]: " input_url
    API_BASE_URL="${input_url:-$API_BASE_URL}"
    
    read -p "Environment [$ENVIRONMENT]: " input_env
    ENVIRONMENT="${input_env:-$ENVIRONMENT}"
    
    read -p "Poll Interval (seconds) [$POLL_INTERVAL]: " input_interval
    POLL_INTERVAL="${input_interval:-$POLL_INTERVAL}"
    
    read -p "User ID [$USER_ID]: " input_user
    USER_ID="${input_user:-$USER_ID}"
    
    read -p "Host Name [$HOST_NAME]: " input_host
    HOST_NAME="${input_host:-$HOST_NAME}"
    
    # Generate new session ID
    SESSION_ID=$(uuidgen)
    
    save_config
}

# Show help
show_help() {
    echo -e "${WHITE}HigherSelf Network Server - Termius Monitor${NC}"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  monitor     Start continuous monitoring mode"
    echo "  status      Check service status"
    echo "  history     Show notification history"
    echo "  test        Send test notification"
    echo "  setup       Configure monitor settings"
    echo "  register    Register terminal session"
    echo "  unregister  Unregister terminal session"
    echo "  help        Show this help message"
    echo ""
    echo "Configuration file: $CONFIG_FILE"
}

# Main function
main() {
    load_config
    
    case "${1:-help}" in
        "monitor")
            monitor_mode
            ;;
        "status")
            print_banner
            get_service_status
            ;;
        "history")
            print_banner
            get_notification_history "${2:-10}"
            ;;
        "test")
            print_banner
            send_test_notification
            ;;
        "setup")
            setup_config
            ;;
        "register")
            print_banner
            register_session
            ;;
        "unregister")
            print_banner
            unregister_session
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function
main "$@"
