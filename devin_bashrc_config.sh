#!/bin/bash
# Devin AI Permanent Configuration for The HigherSelf Network Server
# Add this to your ~/.bashrc or ~/.zshrc for automatic setup

# =============================================================================
# DEVIN AI CONFIGURATION - The HigherSelf Network Server
# =============================================================================

# Project-specific environment variables
export DEVIN_PROJECT_ROOT="$HOME/repos/The-HigherSelf-Network-Server"

# Function to set up Devin environment for The HigherSelf Network Server
devin_higherself_setup() {
    if [ -d "$DEVIN_PROJECT_ROOT" ]; then
        cd "$DEVIN_PROJECT_ROOT"
        export TEST_MODE=True
        export DISABLE_WEBHOOKS=True
        export PYTHONPATH="$DEVIN_PROJECT_ROOT"
        export NOTION_API_TOKEN=test_token
        export REDIS_URI=redis://localhost:6379/0
        export MONGODB_URI=mongodb://localhost:27017/test_db
        export OPENAI_API_KEY=test_openai_key
        echo "✅ Devin environment configured for The HigherSelf Network Server"
        echo "📁 Current directory: $(pwd)"
    else
        echo "❌ Project directory not found: $DEVIN_PROJECT_ROOT"
        echo "Please ensure the repository is cloned to the correct location"
    fi
}

# Aliases for common Devin tasks
alias devin-cd='cd $DEVIN_PROJECT_ROOT && devin_higherself_setup'
alias devin-validate='cd $DEVIN_PROJECT_ROOT && python3 devin_quick_validation.py'
alias devin-test='cd $DEVIN_PROJECT_ROOT && python3 run_tests.py'
alias devin-server='cd $DEVIN_PROJECT_ROOT && python3 devin_test_server.py'
alias devin-health='curl -s http://localhost:8000/health | jq .'
alias devin-status='curl -s http://localhost:8000/api/status | jq .'
alias devin-fix='cd $DEVIN_PROJECT_ROOT && python3 fix_syntax_errors.py'
alias devin-docs='cd $DEVIN_PROJECT_ROOT && open DEVIN_REPOSITORY_NOTES.md'

# Advanced Devin functions
devin_full_setup() {
    echo "🤖 Running complete Devin setup for The HigherSelf Network Server..."
    devin_higherself_setup
    python3 devin_quick_validation.py
    if [ $? -eq 0 ]; then
        echo "✅ Setup completed successfully!"
        echo "🚀 Ready to start development"
    else
        echo "❌ Setup validation failed"
        echo "📚 Check DEVIN_REPOSITORY_NOTES.md for troubleshooting"
    fi
}

devin_commit_ready() {
    echo "🔍 Checking if code is ready to commit..."
    devin_higherself_setup
    
    # Run validation
    if ! python3 devin_quick_validation.py; then
        echo "❌ Validation failed - not ready to commit"
        return 1
    fi
    
    # Run core tests
    if ! python3 -m pytest tests/test_basic_functionality.py -v --no-cov; then
        echo "❌ Core tests failed - not ready to commit"
        return 1
    fi
    
    # Check syntax
    if ! python3 -c "import py_compile; py_compile.compile('main.py', doraise=True)"; then
        echo "❌ Syntax errors found - not ready to commit"
        return 1
    fi
    
    echo "✅ Code is ready to commit!"
    return 0
}

devin_start_dev() {
    echo "🚀 Starting Devin development session..."
    devin_higherself_setup
    
    # Start server in background
    python3 devin_test_server.py &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 5
    
    # Test health endpoint
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Development server started successfully"
        echo "🌐 Server running at: http://localhost:8000"
        echo "❤️  Health check: http://localhost:8000/health"
        echo "📚 API docs: http://localhost:8000/docs"
        echo ""
        echo "🛑 To stop server: kill $SERVER_PID"
    else
        echo "❌ Server failed to start properly"
        kill $SERVER_PID 2>/dev/null
    fi
}

devin_quick_test() {
    echo "⚡ Running quick Devin test suite..."
    devin_higherself_setup
    
    # Quick validation
    if python3 devin_quick_validation.py; then
        echo "✅ Quick validation passed"
    else
        echo "❌ Quick validation failed"
        return 1
    fi
    
    # Basic functionality test
    if python3 -m pytest tests/test_basic_functionality.py -v --no-cov; then
        echo "✅ Basic functionality tests passed"
    else
        echo "❌ Basic functionality tests failed"
        return 1
    fi
    
    echo "🎉 All quick tests passed!"
}

# Auto-completion for Devin commands
_devin_commands() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="validate test server health status fix docs setup commit-ready start-dev quick-test"
    
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}

# Register completion
complete -F _devin_commands devin-validate devin-test devin-server

# Display help when sourced
devin_help() {
    echo ""
    echo "🤖 Devin AI Commands for The HigherSelf Network Server"
    echo "======================================================"
    echo ""
    echo "Setup Commands:"
    echo "  devin-cd           - Navigate to project and setup environment"
    echo "  devin_full_setup   - Complete setup and validation"
    echo "  devin_higherself_setup - Setup environment variables only"
    echo ""
    echo "Development Commands:"
    echo "  devin-validate     - Quick environment validation"
    echo "  devin-test         - Run test suite"
    echo "  devin-server       - Start test server"
    echo "  devin_start_dev    - Start development session"
    echo ""
    echo "Testing Commands:"
    echo "  devin_quick_test   - Run quick test suite"
    echo "  devin_commit_ready - Check if ready to commit"
    echo "  devin-health       - Check server health"
    echo "  devin-status       - Check API status"
    echo ""
    echo "Utility Commands:"
    echo "  devin-fix          - Fix syntax errors"
    echo "  devin-docs         - Open documentation"
    echo "  devin_help         - Show this help"
    echo ""
    echo "🚀 Quick start: devin_full_setup"
    echo ""
}

# Show help message when this file is sourced
echo "✅ Devin AI configuration loaded for The HigherSelf Network Server"
echo "📝 Type 'devin_help' to see available commands"
echo "🚀 Type 'devin_full_setup' to get started"
