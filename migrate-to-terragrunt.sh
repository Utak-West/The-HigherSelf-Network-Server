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
