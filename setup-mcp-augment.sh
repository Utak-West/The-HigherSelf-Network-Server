#!/bin/bash

# HigherSelf Network MCP Setup for Augment Code
# This script helps configure MCP servers in Augment Code

set -e

echo "🚀 HigherSelf Network MCP Setup for Augment Code"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js first."
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm first."
        exit 1
    fi
    
    print_status "Node.js and npm are installed"
}

# Test MCP server availability
test_mcp_servers() {
    print_info "Testing MCP server availability..."
    
    # Test Notion MCP server
    print_info "Testing Notion MCP server..."
    if timeout 10 npx -y @notionhq/notion-mcp-server --version &>/dev/null; then
        print_status "Notion MCP server is available"
    else
        print_warning "Notion MCP server test inconclusive (this is normal)"
    fi
    
    # Test File System MCP server
    print_info "Testing File System MCP server..."
    if timeout 10 npx -y @modelcontextprotocol/server-filesystem --version &>/dev/null; then
        print_status "File System MCP server is available"
    else
        print_warning "File System MCP server test inconclusive (this is normal)"
    fi
    
    # Test Slack MCP server
    print_info "Testing Slack MCP server..."
    if timeout 10 npx -y @modelcontextprotocol/server-slack --version &>/dev/null; then
        print_status "Slack MCP server is available"
    else
        print_warning "Slack MCP server test inconclusive (this is normal)"
    fi
}

# Display configuration instructions
show_configuration_steps() {
    echo ""
    print_info "📋 Configuration Steps for Augment Code:"
    echo ""
    echo "1. 🔧 Open Augment Code"
    echo "2. 🔧 Press Cmd/Ctrl + Shift + P"
    echo "3. 🔧 Type 'Preferences: Open Settings (JSON)'"
    echo "4. 🔧 Add this configuration to your settings:"
    echo ""
    echo "{"
    echo '  "augment.advanced": {'
    echo '    "mcpServers": ['
    echo '      {'
    echo '        "name": "notion-higherself",'
    echo '        "command": "npx",'
    echo '        "args": ["-y", "@notionhq/notion-mcp-server"],'
    echo '        "env": {'
    echo '          "NOTION_TOKEN": "secret_your_notion_integration_token_here"'
    echo '        }'
    echo '      },'
    echo '      {'
    echo '        "name": "filesystem-higherself",'
    echo '        "command": "npx",'
    echo '        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/utakwest/Documents/HigherSelf/The HigherSelf Network /The HigherSelf Network Server"],'
    echo '        "env": {}'
    echo '      },'
    echo '      {'
    echo '        "name": "slack-higherself",'
    echo '        "command": "npx",'
    echo '        "args": ["-y", "@modelcontextprotocol/server-slack"],'
    echo '        "env": {'
    echo '          "SLACK_BOT_TOKEN": "xoxb-your-bot-token-here",'
    echo '          "SLACK_TEAM_ID": "your-team-id-here"'
    echo '        }'
    echo '      }'
    echo '    ]'
    echo '  }'
    echo "}"
    echo ""
}

# Display credential setup instructions
show_credential_setup() {
    print_info "🔑 API Credential Setup:"
    echo ""
    echo "📝 Notion Integration Token (REQUIRED):"
    echo "   1. Go to https://www.notion.so/profile/integrations"
    echo "   2. Click 'Create new integration'"
    echo "   3. Name it 'HigherSelf Network MCP'"
    echo "   4. Copy the integration token (starts with 'secret_')"
    echo "   5. Share your databases with the integration"
    echo ""
    echo "📝 Slack Bot Token (OPTIONAL):"
    echo "   1. Go to https://api.slack.com/apps"
    echo "   2. Create a new app or use existing one"
    echo "   3. Get Bot User OAuth Token (starts with 'xoxb-')"
    echo "   4. Get your Team/Workspace ID"
    echo ""
}

# Display testing instructions
show_testing_steps() {
    print_info "🧪 Testing Your Setup:"
    echo ""
    echo "After configuring Augment Code, test with these queries:"
    echo "• 'Show me my Notion databases'"
    echo "• 'List files in my HigherSelf Network Server directory'"
    echo "• 'Help me search my Notion workspace'"
    echo "• 'Show me the structure of my project files'"
    echo ""
}

# Display next steps
show_next_steps() {
    print_info "🚀 Next Steps:"
    echo ""
    echo "1. ✅ Configure Augment Code with the MCP servers"
    echo "2. ✅ Set up your Notion integration token"
    echo "3. ✅ Test the MCP servers with sample queries"
    echo "4. 🎯 Begin implementing the three high-impact projects:"
    echo "   • Project 1: Real-Time AI Agent Contact Processing"
    echo "   • Project 2: Multi-Entity Workflow Expansion"
    echo "   • Project 3: Bidirectional Notion Intelligence Hub"
    echo ""
}

# Main execution
main() {
    check_prerequisites
    echo ""
    
    test_mcp_servers
    echo ""
    
    show_configuration_steps
    show_credential_setup
    show_testing_steps
    show_next_steps
    
    print_status "MCP setup guide completed! 🎉"
    print_info "Follow the steps above to configure Augment Code with MCP servers."
}

# Run main function
main
