#!/bin/bash
# Devin Environment Setup Script
# Source this file to automatically configure the development environment
# Usage: source devin_env_setup.sh

echo "Configuring Devin AI environment for The HigherSelf Network Server..."

# Navigate to project root
if [ ! -f "main.py" ]; then
    echo "Navigating to project directory..."
    cd ~/repos/The-HigherSelf-Network-Server 2>/dev/null || {
        echo "ERROR: Project directory not found. Please ensure you're in the correct location."
        return 1
    }
fi

# Set environment variables
echo "Setting environment variables..."
export TEST_MODE=True
export DISABLE_WEBHOOKS=True
export PYTHONPATH=$PWD
export NOTION_API_TOKEN=test_token
export REDIS_URI=redis://localhost:6379/0
export MONGODB_URI=mongodb://localhost:27017/test_db
export OPENAI_API_KEY=test_openai_key

# Verify Python setup
echo "Checking Python setup..."
if command -v python3 &> /dev/null; then
    echo "PASS: Python3 available: $(python3 --version)"
else
    echo "ERROR: Python3 not found. Please install Python 3.8+"
    return 1
fi

# Check project structure
echo "Verifying project structure..."
required_files=("main.py" "requirements.txt" "pyproject.toml" "devin_quick_validation.py" "devin_test_server.py")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo "PASS: All required files present"
else
    echo "WARN: Missing files: ${missing_files[*]}"
fi

# Define helpful aliases
echo "Setting up helpful aliases..."
alias devin-validate='python3 devin_quick_validation.py'
alias devin-test='python3 run_tests.py'
alias devin-server='python3 devin_test_server.py'
alias devin-health='curl -s http://localhost:8000/health'
alias devin-status='curl -s http://localhost:8000/api/status'
alias devin-fix='python3 fix_syntax_errors.py'

# Define helpful functions
devin-setup() {
    echo "Running complete Devin setup..."
    python3 devin_quick_validation.py
}

devin-commit-check() {
    echo "Running pre-commit checks..."
    python3 devin_quick_validation.py && \
    python3 -m pytest tests/test_basic_functionality.py -v --no-cov && \
    echo "Ready to commit!"
}

devin-start() {
    echo "Starting development server..."
    python3 devin_test_server.py
}

devin-test-endpoints() {
    echo "Testing all endpoints..."
    echo "Health: $(curl -s http://localhost:8000/health)"
    echo "Root: $(curl -s http://localhost:8000/)"
    echo "Status: $(curl -s http://localhost:8000/api/status)"
}

devin-reset() {
    echo "Resetting environment..."
    cd ~/repos/The-HigherSelf-Network-Server
    export TEST_MODE=True
    export DISABLE_WEBHOOKS=True
    export PYTHONPATH=$PWD
    echo "Environment reset complete"
}

# Display available commands
echo ""
echo "Available Devin commands:"
echo "  devin-validate     - Quick environment validation"
echo "  devin-test         - Run test suite"
echo "  devin-server       - Start test server"
echo "  devin-health       - Check server health"
echo "  devin-status       - Check API status"
echo "  devin-fix          - Fix syntax errors"
echo "  devin-setup        - Complete setup validation"
echo "  devin-commit-check - Pre-commit validation"
echo "  devin-start        - Start development server"
echo "  devin-test-endpoints - Test all endpoints"
echo "  devin-reset        - Reset environment"
echo ""
echo "Devin environment configured successfully!"
echo "Current directory: $(pwd)"
echo "Environment variables set for test mode"
echo ""
echo "Quick start:"
echo "  1. Run: devin-validate"
echo "  2. Run: devin-server"
echo "  3. Test: devin-health"
echo ""
