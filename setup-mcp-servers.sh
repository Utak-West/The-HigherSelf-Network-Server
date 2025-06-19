#!/bin/bash

# HigherSelf Network MCP Servers Setup Script
# This script helps install and configure MCP servers for Augment Code

set -e

echo "🚀 HigherSelf Network MCP Servers Setup"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Node.js is installed
check_nodejs() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_status "Node.js is installed: $NODE_VERSION"
    else
        print_error "Node.js is not installed. Please install Node.js first."
        exit 1
    fi
}

# Check if npm is installed
check_npm() {
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        print_status "npm is installed: $NPM_VERSION"
    else
        print_error "npm is not installed. Please install npm first."
        exit 1
    fi
}

# Install MCP servers
install_mcp_servers() {
    print_info "Installing MCP servers globally..."
    
    # Core business integration servers
    print_info "Installing Notion MCP server..."
    npm install -g @makenotion/notion-mcp-server || print_warning "Notion MCP server installation failed"
    
    print_info "Installing GitHub MCP server..."
    npm install -g @modelcontextprotocol/server-github || print_warning "GitHub MCP server installation failed"
    
    print_info "Installing PostgreSQL MCP server..."
    npm install -g @modelcontextprotocol/server-postgres || print_warning "PostgreSQL MCP server installation failed"
    
    print_info "Installing Brave Search MCP server..."
    npm install -g @modelcontextprotocol/server-brave-search || print_warning "Brave Search MCP server installation failed"
    
    print_info "Installing File System MCP server..."
    npm install -g @modelcontextprotocol/server-filesystem || print_warning "File System MCP server installation failed"
    
    print_info "Installing Google Drive MCP server..."
    npm install -g @google/mcp-server-gdrive || print_warning "Google Drive MCP server installation failed"
    
    print_info "Installing Slack MCP server..."
    npm install -g slack-mcp-server@latest || print_warning "Slack MCP server installation failed"
    
    print_status "MCP servers installation completed!"
}

# Create environment file
create_env_file() {
    if [ ! -f ".env.mcp" ]; then
        print_info "Creating .env.mcp file from template..."
        cp mcp-environment-template.env .env.mcp
        print_status "Created .env.mcp file. Please edit it with your actual credentials."
    else
        print_warning ".env.mcp file already exists. Skipping creation."
    fi
}

# Display next steps
show_next_steps() {
    echo ""
    echo "🎯 Next Steps:"
    echo "=============="
    echo ""
    echo "1. 📝 Edit the .env.mcp file with your actual API credentials:"
    echo "   - Notion integration token"
    echo "   - GitHub personal access token"
    echo "   - Database connection strings"
    echo "   - Google service account credentials"
    echo "   - Slack tokens"
    echo ""
    echo "2. 🔧 Configure Augment Code:"
    echo "   - Open Augment Code settings (Cmd/Ctrl + Shift + P)"
    echo "   - Search for 'Preferences: Open Settings (JSON)'"
    echo "   - Add the contents of mcp-servers-config.json to your settings"
    echo ""
    echo "3. 🔄 Restart Augment Code completely"
    echo ""
    echo "4. ✅ Test the MCP servers by asking questions like:"
    echo "   - 'Show me my Notion databases'"
    echo "   - 'List my GitHub repositories'"
    echo "   - 'Search for art gallery trends'"
    echo ""
    echo "5. 🚀 Once MCP servers are working, we'll implement the three projects:"
    echo "   - Project 1: Real-Time AI Agent Contact Processing"
    echo "   - Project 2: Multi-Entity Workflow Expansion"
    echo "   - Project 3: Bidirectional Notion Intelligence Hub"
    echo ""
}

# Main execution
main() {
    echo "Starting HigherSelf Network MCP setup..."
    echo ""
    
    check_nodejs
    check_npm
    echo ""
    
    install_mcp_servers
    echo ""
    
    create_env_file
    echo ""
    
    show_next_steps
    
    print_status "MCP servers setup completed! 🎉"
}

# Run main function
main
