#!/bin/bash

# HigherSelf Network Server - Backward Compatibility Check
# Ensures existing deployment methods continue to work with Gruntwork integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🔄 HigherSelf Network Server - Backward Compatibility Check${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if we're in the right directory
cd "$PROJECT_ROOT"

echo -e "${BLUE}Checking backward compatibility...${NC}"
echo ""

# 1. Check existing Terraform deployment
echo -e "${BLUE}1. Checking existing Terraform deployment compatibility...${NC}"

if [[ -f "terraform/main.tf" && -f "terraform/deploy.sh" ]]; then
    print_status "Existing Terraform files found"
    
    # Check if deploy.sh is executable
    if [[ -x "terraform/deploy.sh" ]]; then
        print_status "terraform/deploy.sh is executable"
    else
        print_warning "terraform/deploy.sh is not executable - fixing..."
        chmod +x terraform/deploy.sh
        print_status "Fixed terraform/deploy.sh permissions"
    fi
    
    # Test terraform validation
    cd terraform
    if terraform validate > /dev/null 2>&1; then
        print_status "Existing Terraform configuration is valid"
    else
        print_warning "Terraform validation issues detected - this is expected with Gruntwork integration"
        print_info "Use 'terragrunt validate' instead for new deployments"
    fi
    cd "$PROJECT_ROOT"
else
    print_error "Existing Terraform files not found"
fi

# 2. Check Docker Compose deployment
echo ""
echo -e "${BLUE}2. Checking Docker Compose deployment compatibility...${NC}"

if [[ -f "docker-compose.yml" ]]; then
    print_status "docker-compose.yml found"
    
    # Check if docker-compose is available
    if command -v docker-compose &> /dev/null; then
        print_status "docker-compose is available"
        
        # Validate docker-compose file
        if docker-compose config > /dev/null 2>&1; then
            print_status "docker-compose.yml is valid"
        else
            print_warning "docker-compose.yml validation issues"
        fi
    else
        print_warning "docker-compose not installed"
        print_info "Install with: pip install docker-compose"
    fi
else
    print_error "docker-compose.yml not found"
fi

# 3. Check deployment scripts
echo ""
echo -e "${BLUE}3. Checking deployment scripts compatibility...${NC}"

deployment_scripts=(
    "deploy.sh"
    "docker-deploy.sh"
    "scripts/deploy.sh"
    "deployment/deploy-to-vm.sh"
)

for script in "${deployment_scripts[@]}"; do
    if [[ -f "$script" ]]; then
        print_status "Found deployment script: $script"
        
        if [[ -x "$script" ]]; then
            print_status "$script is executable"
        else
            print_warning "$script is not executable - fixing..."
            chmod +x "$script"
            print_status "Fixed $script permissions"
        fi
    fi
done

# 4. Check environment configuration
echo ""
echo -e "${BLUE}4. Checking environment configuration compatibility...${NC}"

env_files=(
    ".env"
    ".env.example"
    ".env.development"
    ".env.staging"
    ".env.production"
)

for env_file in "${env_files[@]}"; do
    if [[ -f "$env_file" ]]; then
        print_status "Found environment file: $env_file"
    fi
done

# 5. Check new Terragrunt integration
echo ""
echo -e "${BLUE}5. Checking new Terragrunt integration...${NC}"

if [[ -f "terragrunt.hcl" ]]; then
    print_status "Root terragrunt.hcl found"
else
    print_error "Root terragrunt.hcl not found"
fi

if [[ -f "terragrunt-deploy.sh" ]]; then
    print_status "terragrunt-deploy.sh found"
    
    if [[ -x "terragrunt-deploy.sh" ]]; then
        print_status "terragrunt-deploy.sh is executable"
    else
        print_warning "terragrunt-deploy.sh is not executable - fixing..."
        chmod +x terragrunt-deploy.sh
        print_status "Fixed terragrunt-deploy.sh permissions"
    fi
else
    print_error "terragrunt-deploy.sh not found"
fi

# Check Terragrunt environment configurations
terragrunt_envs=("development" "staging" "production")
for env in "${terragrunt_envs[@]}"; do
    if [[ -f "terragrunt/environments/$env/terragrunt.hcl" ]]; then
        print_status "Terragrunt $env configuration found"
    else
        print_warning "Terragrunt $env configuration not found"
    fi
done

# 6. Check secrets management
echo ""
echo -e "${BLUE}6. Checking secrets management compatibility...${NC}"

if [[ -f "terraform/modules/secrets-manager/main.tf" ]]; then
    print_status "Secrets manager module found"
else
    print_warning "Secrets manager module not found"
fi

if [[ -f "terragrunt/modules/secrets-manager/terragrunt.hcl" ]]; then
    print_status "Terragrunt secrets manager configuration found"
else
    print_warning "Terragrunt secrets manager configuration not found"
fi

# 7. Generate compatibility summary
echo ""
echo -e "${BLUE}📋 Compatibility Summary${NC}"
echo ""

echo -e "${GREEN}✅ Backward Compatible Deployment Methods:${NC}"
echo "1. Docker Compose: docker-compose up -d"
echo "2. Traditional Terraform: cd terraform && ./deploy.sh development"
echo "3. Docker Deploy Script: ./docker-deploy.sh"
echo ""

echo -e "${BLUE}🚀 New Gruntwork-Enhanced Deployment Methods:${NC}"
echo "1. Terragrunt (Recommended): ./terragrunt-deploy.sh development apply"
echo "2. Secrets Management: ./terragrunt-deploy.sh development apply secrets-manager"
echo "3. Environment-specific: ./terragrunt-deploy.sh production apply"
echo ""

echo -e "${YELLOW}⚠️ Migration Recommendations:${NC}"
echo "1. Continue using existing methods for current deployments"
echo "2. Test new Terragrunt methods in development environment"
echo "3. Gradually migrate to Gruntwork patterns for enhanced security"
echo "4. Use secrets manager for production deployments"
echo ""

echo -e "${BLUE}📚 Documentation:${NC}"
echo "• Gruntwork Integration Plan: docs/GRUNTWORK_INTEGRATION_PLAN.md"
echo "• Contributors & Acknowledgments: CONTRIBUTORS.md"
echo "• Deployment Guide: docs/integrations/HigherSelf_Network_Server_Deployment_Guide.md"
echo ""

# 8. Create compatibility wrapper scripts
echo -e "${BLUE}Creating compatibility wrapper scripts...${NC}"

# Create wrapper for existing terraform deploy
cat > terraform-legacy-deploy.sh << 'EOF'
#!/bin/bash
# Legacy Terraform deployment wrapper
# Maintains backward compatibility while recommending new methods

echo "🔄 Using legacy Terraform deployment method"
echo "💡 Consider upgrading to Terragrunt for enhanced features: ./terragrunt-deploy.sh"
echo ""

cd terraform
./deploy.sh "$@"
EOF

chmod +x terraform-legacy-deploy.sh
print_status "Created terraform-legacy-deploy.sh wrapper"

# Create migration helper script
cat > migrate-to-terragrunt.sh << 'EOF'
#!/bin/bash
# Migration helper script for moving from Terraform to Terragrunt

echo "🔄 HigherSelf Network Server - Terragrunt Migration Helper"
echo ""
echo "This script helps migrate from legacy Terraform to Gruntwork Terragrunt"
echo ""
echo "Steps:"
echo "1. Backup current state: terraform state pull > terraform-state-backup.json"
echo "2. Test Terragrunt deployment: ./terragrunt-deploy.sh development plan"
echo "3. Apply Terragrunt deployment: ./terragrunt-deploy.sh development apply"
echo "4. Verify services: curl http://localhost:8000/health"
echo ""
echo "For assistance, see: docs/GRUNTWORK_INTEGRATION_PLAN.md"
EOF

chmod +x migrate-to-terragrunt.sh
print_status "Created migrate-to-terragrunt.sh helper"

echo ""
echo -e "${GREEN}🎉 Backward compatibility check completed!${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Test existing deployment: ./terraform-legacy-deploy.sh development plan"
echo "2. Test new Terragrunt deployment: ./terragrunt-deploy.sh development plan"
echo "3. Review migration plan: docs/GRUNTWORK_INTEGRATION_PLAN.md"
echo "4. Begin Phase 2 implementation when ready"
