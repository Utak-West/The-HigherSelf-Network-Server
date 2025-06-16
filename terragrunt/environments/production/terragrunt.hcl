# HigherSelf Network Server - Production Environment Configuration
# Terragrunt configuration for production environment

# Include the root terragrunt.hcl configuration
include "root" {
  path = find_in_parent_folders()
}

# Configure the terraform source
terraform {
  source = "${get_parent_terragrunt_dir()}/terraform//environments/production"
}

# Environment-specific inputs
inputs = {
  environment = "production"
  
  # Production scaling configuration
  enable_monitoring = true
  enable_autoscaling = true
  min_replicas = 3
  max_replicas = 10
  cpu_threshold = 70
  memory_threshold = 80
  
  # Production resource limits
  mongodb_storage = "100Gi"
  redis_storage = "20Gi"
  prometheus_storage = "50Gi"
  
  # Production networking
  enable_ssl = true
  domain_name = get_env("PRODUCTION_DOMAIN", "api.higherself.network")
  enable_cdn = true
  enable_waf = true
  
  # Production security (highly restrictive)
  allowed_cidr_blocks = [
    # Add specific IP ranges for production access
    # These should be set via environment variables
  ]
  
  # Production database settings
  mongodb_replica_count = 3
  redis_replica_count = 3
  enable_database_backup = true
  backup_retention_days = 30
  
  # Production monitoring and logging
  log_level = "INFO"
  enable_debug_endpoints = false
  enable_detailed_monitoring = true
  enable_alerting = true
  
  # Production secrets (must be set via environment variables)
  grafana_admin_password = get_env("GRAFANA_ADMIN_PASSWORD")
  
  # Production feature flags
  enable_experimental_features = false
  enable_performance_testing = false
  enable_load_testing = false
  
  # Production compliance
  enable_audit_logging = true
  enable_encryption_at_rest = true
  enable_encryption_in_transit = true
}

# Production-specific dependencies
dependencies {
  paths = []
}

# Production-specific hooks with safety checks
terraform {
  before_hook "production_safety_check" {
    commands = ["plan", "apply"]
    execute = ["bash", "-c", <<-EOF
      echo "🚨 PRODUCTION DEPLOYMENT SAFETY CHECK 🚨"
      echo "Environment: PRODUCTION"
      echo "Domain: ${get_env("PRODUCTION_DOMAIN", "DOMAIN_NOT_SET")}"
      echo ""
      echo "Required environment variables:"
      echo "- PRODUCTION_DOMAIN: ${get_env("PRODUCTION_DOMAIN", "❌ NOT SET")}"
      echo "- GRAFANA_ADMIN_PASSWORD: ${get_env("GRAFANA_ADMIN_PASSWORD", "❌ NOT SET") != "" ? "✅ SET" : "❌ NOT SET"}"
      echo "- SSL_CERT_PATH: ${get_env("SSL_CERT_PATH", "❌ NOT SET")}"
      echo ""
      if [ -z "${get_env("PRODUCTION_DOMAIN", "")}" ] || [ -z "${get_env("GRAFANA_ADMIN_PASSWORD", "")}" ]; then
        echo "❌ Missing required production environment variables"
        echo "Please set all required variables before deploying to production"
        exit 1
      fi
      echo "✅ Production safety checks passed"
    EOF
    ]
  }
  
  before_hook "production_confirmation" {
    commands = ["apply"]
    execute = ["bash", "-c", <<-EOF
      echo "⚠️  FINAL PRODUCTION DEPLOYMENT CONFIRMATION ⚠️"
      echo "You are about to deploy to PRODUCTION environment"
      echo "This will affect live services and real users"
      echo ""
      read -p "Type 'DEPLOY TO PRODUCTION' to continue: " confirmation
      if [ "$confirmation" != "DEPLOY TO PRODUCTION" ]; then
        echo "❌ Production deployment cancelled"
        exit 1
      fi
      echo "✅ Production deployment confirmed"
    EOF
    ]
  }
  
  after_hook "production_deployment_complete" {
    commands     = ["apply"]
    execute      = ["bash", "-c", "echo '🎉 Production deployment complete! Monitor at https://${get_env("PRODUCTION_DOMAIN")}'"]
    run_on_error = false
  }
  
  after_hook "production_monitoring_reminder" {
    commands     = ["apply"]
    execute      = ["bash", "-c", "echo '📊 Remember to check monitoring dashboards and set up alerts'"]
    run_on_error = false
  }
}

# Enable prevent_destroy for production critical resources
prevent_destroy = true
