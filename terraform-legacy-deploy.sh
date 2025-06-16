#!/bin/bash
# Legacy Terraform deployment wrapper
# Maintains backward compatibility while recommending new methods

echo "🔄 Using legacy Terraform deployment method"
echo "💡 Consider upgrading to Terragrunt for enhanced features: ./terragrunt-deploy.sh"
echo ""

cd terraform
./deploy.sh "$@"
