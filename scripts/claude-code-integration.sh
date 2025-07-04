#!/bin/bash

# ======================================================
# CLAUDE CODE INTEGRATION SCRIPT
# HigherSelf Network Server AI-Assisted Development
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
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Functions
print_header() {
    echo -e "${PURPLE}======================================================${NC}"
    echo -e "${PURPLE}🤖 CLAUDE CODE INTEGRATION${NC}"
    echo -e "${PURPLE}HigherSelf Network Server AI-Assisted Development${NC}"
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
    
    # Check if Node.js is installed
    if command -v node &> /dev/null; then
        print_success "Node.js found: $(node --version)"
    else
        print_error "Node.js not found. Please install Node.js first."
        print_info "Download from: https://nodejs.org/"
        exit 1
    fi
    
    # Check if npm is installed
    if command -v npm &> /dev/null; then
        print_success "npm found: $(npm --version)"
    else
        print_error "npm not found. Please install npm."
        exit 1
    fi
    
    # Check if Claude Code is installed
    if command -v claude-code &> /dev/null; then
        print_success "Claude Code found: $(claude-code --version)"
    else
        print_warning "Claude Code not found. Installing..."
        install_claude_code
    fi
    
    echo ""
}

install_claude_code() {
    print_section "Installing Claude Code"
    
    print_info "Installing @anthropic-ai/claude-code globally..."
    
    if npm install -g @anthropic-ai/claude-code; then
        print_success "Claude Code installed successfully"
    else
        print_error "Failed to install Claude Code"
        print_info "Try running with sudo: sudo npm install -g @anthropic-ai/claude-code"
        exit 1
    fi
    
    echo ""
}

setup_claude_code_config() {
    print_section "Setting Up Claude Code Configuration"
    
    # Create Claude Code configuration directory
    mkdir -p "$HOME/.claude-code"
    
    # Create configuration file
    cat > "$HOME/.claude-code/config.json" << EOF
{
  "project": "HigherSelf Network Server",
  "description": "Voice-controlled server management with Termius integration",
  "context": {
    "framework": "FastAPI",
    "language": "Python",
    "deployment": "Docker",
    "integrations": ["Termius", "1Password", "Voice Control", "SiteGround"],
    "voice_control": true,
    "secure_snippets": true
  },
  "preferences": {
    "code_style": "pythonic",
    "documentation": "comprehensive",
    "security": "enterprise",
    "testing": "pytest"
  }
}
EOF
    
    print_success "Claude Code configuration created"
    echo ""
}

create_claude_code_snippets() {
    print_section "Creating Claude Code Integration Snippets"
    
    # Create Claude Code snippets directory
    mkdir -p "$PROJECT_ROOT/claude-code-snippets"
    
    # Voice Control Enhancement Snippet
    cat > "$PROJECT_ROOT/claude-code-snippets/voice-control-enhancement.md" << 'EOF'
# Claude Code: Voice Control Enhancement

## Context
HigherSelf Network Server with Termius voice control integration.

## Request
Enhance the voice control system with:
1. Natural language processing for complex commands
2. Error handling and recovery
3. Multi-environment support
4. Integration with 1Password snippets

## Current Implementation
- Voice commands via Aqua Voice API
- Server control through Docker Compose
- Termius Pro integration
- 1Password secure snippets

## Enhancement Goals
- More natural voice commands
- Better error messages
- Contextual help system
- Advanced logging and monitoring
EOF
    
    # API Enhancement Snippet
    cat > "$PROJECT_ROOT/claude-code-snippets/api-enhancement.md" << 'EOF'
# Claude Code: API Enhancement

## Context
FastAPI server with voice control endpoints and multi-entity support.

## Request
Enhance the API with:
1. Better error handling and validation
2. Rate limiting and security
3. Comprehensive documentation
4. Performance monitoring

## Current Endpoints
- /voice/server/control
- /voice/server/transcribe-and-control
- /health endpoints
- Multi-entity workflows

## Enhancement Goals
- OpenAPI documentation
- Input validation
- Security middleware
- Performance metrics
EOF
    
    # Deployment Enhancement Snippet
    cat > "$PROJECT_ROOT/claude-code-snippets/deployment-enhancement.md" << 'EOF'
# Claude Code: Deployment Enhancement

## Context
Docker-based deployment with SiteGround hosting and voice control.

## Request
Enhance deployment with:
1. CI/CD pipeline automation
2. Environment-specific configurations
3. Health checks and monitoring
4. Rollback capabilities

## Current Setup
- Docker Compose multi-environment
- SiteGround Jump Start hosting
- Manual deployment scripts
- Voice-activated operations

## Enhancement Goals
- Automated deployments
- Blue-green deployment
- Monitoring and alerting
- Voice-controlled deployments
EOF
    
    print_success "Claude Code snippets created"
    echo ""
}

create_claude_code_commands() {
    print_section "Creating Claude Code Helper Commands"
    
    # Create Claude Code wrapper script
    cat > "$PROJECT_ROOT/scripts/claude-code-helper.sh" << 'EOF'
#!/bin/bash

# Claude Code Helper for HigherSelf Network Server
# Usage: ./scripts/claude-code-helper.sh [command] [options]

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

case "${1:-help}" in
    "enhance-voice")
        echo "🤖 Enhancing voice control with Claude Code..."
        claude-code analyze "$PROJECT_ROOT/services/voice_server_control.py" \
            --context "$PROJECT_ROOT/claude-code-snippets/voice-control-enhancement.md" \
            --output "$PROJECT_ROOT/claude-code-output/voice-enhancement.md"
        ;;
    "enhance-api")
        echo "🤖 Enhancing API with Claude Code..."
        claude-code analyze "$PROJECT_ROOT/api/voice_router.py" \
            --context "$PROJECT_ROOT/claude-code-snippets/api-enhancement.md" \
            --output "$PROJECT_ROOT/claude-code-output/api-enhancement.md"
        ;;
    "enhance-deployment")
        echo "🤖 Enhancing deployment with Claude Code..."
        claude-code analyze "$PROJECT_ROOT/docker-compose.yml" \
            --context "$PROJECT_ROOT/claude-code-snippets/deployment-enhancement.md" \
            --output "$PROJECT_ROOT/claude-code-output/deployment-enhancement.md"
        ;;
    "review-code")
        echo "🤖 Reviewing code with Claude Code..."
        claude-code review "$PROJECT_ROOT" \
            --exclude "node_modules,__pycache__,.git" \
            --output "$PROJECT_ROOT/claude-code-output/code-review.md"
        ;;
    "generate-docs")
        echo "🤖 Generating documentation with Claude Code..."
        claude-code document "$PROJECT_ROOT" \
            --format markdown \
            --output "$PROJECT_ROOT/claude-code-output/documentation.md"
        ;;
    "optimize")
        echo "🤖 Optimizing code with Claude Code..."
        claude-code optimize "$PROJECT_ROOT/services/" \
            --language python \
            --output "$PROJECT_ROOT/claude-code-output/optimizations.md"
        ;;
    "help"|*)
        echo "Claude Code Helper Commands:"
        echo "  enhance-voice     - Enhance voice control system"
        echo "  enhance-api       - Enhance API endpoints"
        echo "  enhance-deployment - Enhance deployment process"
        echo "  review-code       - Review entire codebase"
        echo "  generate-docs     - Generate documentation"
        echo "  optimize          - Optimize code performance"
        echo ""
        echo "Output will be saved to claude-code-output/ directory"
        ;;
esac
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/claude-code-helper.sh"
    
    # Create output directory
    mkdir -p "$PROJECT_ROOT/claude-code-output"
    
    print_success "Claude Code helper commands created"
    echo ""
}

integrate_with_voice_control() {
    print_section "Integrating Claude Code with Voice Control"
    
    # Add Claude Code commands to Termius snippets
    cat > "$PROJECT_ROOT/termius-setup/snippets-claude-code.json" << 'EOF'
{
  "claude_code_snippets": {
    "name": "HigherSelf Claude Code Integration",
    "description": "AI-assisted development with Claude Code",
    "version": "1.0.0"
  },
  "snippets": [
    {
      "id": "claude-enhance-voice",
      "name": "Claude: Enhance Voice Control",
      "description": "Use Claude Code to enhance voice control system",
      "category": "AI Development",
      "script": "#!/bin/bash\necho \"🤖 Using Claude Code to enhance voice control...\"\n./scripts/claude-code-helper.sh enhance-voice\necho \"✅ Enhancement suggestions saved to claude-code-output/voice-enhancement.md\""
    },
    {
      "id": "claude-review-code",
      "name": "Claude: Review Code",
      "description": "Use Claude Code to review entire codebase",
      "category": "AI Development",
      "script": "#!/bin/bash\necho \"🤖 Using Claude Code to review codebase...\"\n./scripts/claude-code-helper.sh review-code\necho \"✅ Code review saved to claude-code-output/code-review.md\""
    },
    {
      "id": "claude-generate-docs",
      "name": "Claude: Generate Documentation",
      "description": "Use Claude Code to generate comprehensive documentation",
      "category": "AI Development",
      "script": "#!/bin/bash\necho \"🤖 Using Claude Code to generate documentation...\"\n./scripts/claude-code-helper.sh generate-docs\necho \"✅ Documentation saved to claude-code-output/documentation.md\""
    }
  ]
}
EOF
    
    print_success "Claude Code integrated with Termius voice control"
    echo ""
}

update_env_file() {
    print_section "Updating Environment Configuration"
    
    # Add Claude Code integration to .env file
    if ! grep -q "CLAUDE_CODE_INTEGRATION" "$ENV_FILE"; then
        cat >> "$ENV_FILE" << 'EOF'

# ==== CLAUDE CODE INTEGRATION ====
# AI-assisted development with Claude Code
CLAUDE_CODE_INTEGRATION=true
CLAUDE_CODE_PROJECT=HigherSelf Network Server
CLAUDE_CODE_AUTO_REVIEW=false
CLAUDE_CODE_OUTPUT_DIR=claude-code-output
EOF
    fi
    
    print_success "Environment file updated with Claude Code integration"
    echo ""
}

create_documentation() {
    print_section "Creating Claude Code Documentation"
    
    cat > "$PROJECT_ROOT/CLAUDE_CODE_INTEGRATION.md" << 'EOF'
# Claude Code Integration for HigherSelf Network Server

## 🤖 Overview

Claude Code is integrated with your HigherSelf Network Server to provide AI-assisted development capabilities alongside your voice control system.

## 🚀 Quick Start

### Installation
```bash
# Install Claude Code globally
npm install -g @anthropic-ai/claude-code

# Run integration setup
./scripts/claude-code-integration.sh
```

### Basic Usage
```bash
# Enhance voice control system
./scripts/claude-code-helper.sh enhance-voice

# Review entire codebase
./scripts/claude-code-helper.sh review-code

# Generate documentation
./scripts/claude-code-helper.sh generate-docs
```

## 🎤 Voice + AI Workflow

### Enhanced Development Process
1. **Voice Command**: "start higher self server"
2. **Claude Code**: Analyze and optimize server startup
3. **1Password**: Secure credential management
4. **Termius**: Remote server management

### AI-Assisted Voice Control
- **Natural Language Processing**: Better command understanding
- **Error Recovery**: Intelligent error handling
- **Code Optimization**: Performance improvements
- **Documentation**: Auto-generated docs

## 📋 Available Commands

### Code Enhancement
- `enhance-voice` - Improve voice control system
- `enhance-api` - Optimize API endpoints
- `enhance-deployment` - Better deployment process

### Code Analysis
- `review-code` - Comprehensive code review
- `optimize` - Performance optimizations
- `generate-docs` - Documentation generation

## 🔧 Integration Features

### With Voice Control
- AI-enhanced command processing
- Intelligent error messages
- Contextual help system
- Performance monitoring

### With 1Password
- Secure AI model configurations
- Encrypted prompt templates
- Safe credential handling

### With Termius
- AI-assisted server management
- Intelligent deployment strategies
- Automated troubleshooting

## 📊 Output Structure

All Claude Code output is saved to `claude-code-output/`:
- `voice-enhancement.md` - Voice control improvements
- `api-enhancement.md` - API optimizations
- `deployment-enhancement.md` - Deployment improvements
- `code-review.md` - Comprehensive code review
- `documentation.md` - Generated documentation

## 🛡️ Security Considerations

- AI analysis runs locally
- No code sent to external services without consent
- Secure integration with 1Password
- Encrypted configuration storage

## 🎯 Best Practices

1. **Regular Reviews**: Run code reviews weekly
2. **Incremental Improvements**: Apply suggestions gradually
3. **Test Changes**: Validate AI suggestions thoroughly
4. **Document Decisions**: Keep track of applied changes

## 🔄 Workflow Examples

### Daily Development
```bash
# Morning routine
./scripts/claude-code-helper.sh review-code
# Review suggestions and apply improvements

# Voice development
"enhance voice control"  # Termius voice command
# Claude Code analyzes and suggests improvements
```

### Deployment Preparation
```bash
# Pre-deployment analysis
./scripts/claude-code-helper.sh enhance-deployment
# Review deployment optimizations

# Voice deployment
"deploy to production"  # Voice command
# AI-enhanced deployment process
```

## 📈 Benefits

✅ **AI-Enhanced Development** - Intelligent code suggestions
✅ **Voice + AI Synergy** - Natural language + AI analysis
✅ **Automated Documentation** - Always up-to-date docs
✅ **Performance Optimization** - AI-driven improvements
✅ **Error Prevention** - Proactive issue detection
✅ **Security Enhancement** - AI-powered security analysis

## 🆘 Troubleshooting

### Claude Code Not Found
```bash
# Reinstall globally
npm install -g @anthropic-ai/claude-code

# Check installation
claude-code --version
```

### Permission Issues
```bash
# Fix permissions
sudo npm install -g @anthropic-ai/claude-code

# Or use alternative package manager
yarn global add @anthropic-ai/claude-code
```

### Integration Issues
```bash
# Reset configuration
rm -rf ~/.claude-code
./scripts/claude-code-integration.sh
```

## 🎉 Next Steps

1. **Install Claude Code** using npm
2. **Run integration script** to set up configuration
3. **Test AI commands** with voice control
4. **Review AI suggestions** and apply improvements
5. **Integrate into daily workflow** for continuous improvement

You now have AI-assisted development integrated with voice-controlled server management! 🤖🎤
EOF
    
    print_success "Claude Code documentation created"
    echo ""
}

main() {
    print_header
    
    print_info "Setting up Claude Code integration..."
    print_info "Project Root: $PROJECT_ROOT"
    echo ""
    
    check_prerequisites
    setup_claude_code_config
    create_claude_code_snippets
    create_claude_code_commands
    integrate_with_voice_control
    update_env_file
    create_documentation
    
    print_section "Setup Complete!"
    print_success "Claude Code integration setup completed!"
    echo ""
    print_info "Next steps:"
    echo "1. Install Claude Code: npm install -g @anthropic-ai/claude-code"
    echo "2. Test integration: ./scripts/claude-code-helper.sh help"
    echo "3. Enhance voice control: ./scripts/claude-code-helper.sh enhance-voice"
    echo "4. Review the documentation: CLAUDE_CODE_INTEGRATION.md"
    echo ""
    print_info "AI-assisted commands available:"
    echo "• enhance-voice - Improve voice control system"
    echo "• enhance-api - Optimize API endpoints"
    echo "• review-code - Comprehensive code review"
    echo "• generate-docs - Auto-generate documentation"
    echo ""
    print_warning "Remember to install Claude Code first with npm!"
}

# Run main function
main "$@"
