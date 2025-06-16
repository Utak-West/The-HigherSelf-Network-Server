# HigherSelf Network Server - Development Environment Configuration
# Terragrunt configuration for development environment

# Include the root terragrunt.hcl configuration
include "root" {
  path = find_in_parent_folders()
}

# Configure the terraform source
terraform {
  source = "${get_parent_terragrunt_dir()}/terraform//environments/development"
}

# Environment-specific inputs
inputs = {
  environment = "development"
  
  # Development-specific scaling
  enable_monitoring = true
  enable_autoscaling = false
  min_replicas = 1
  max_replicas = 2
  
  # Development resource limits
  mongodb_storage = "10Gi"
  redis_storage = "5Gi"
  prometheus_storage = "10Gi"
  
  # Development networking
  enable_ssl = false
  domain_name = "localhost"
  
  # Development security (less restrictive for testing)
  allowed_cidr_blocks = ["0.0.0.0/0"]
  
  # Development database settings
  mongodb_replica_count = 1
  redis_replica_count = 1
  
  # Development monitoring
  log_level = "DEBUG"
  enable_debug_endpoints = true
  
  # Development secrets (will be overridden by environment variables)
  grafana_admin_password = "admin"
  
  # Development feature flags
  enable_experimental_features = true
  enable_performance_testing = true
}

# Development-specific dependencies
dependencies {
  paths = []
}

# Development-specific hooks
terraform {
  before_hook "validate_development" {
    commands = ["plan", "apply"]
    execute  = ["echo", "Deploying to DEVELOPMENT environment"]
  }
  
  after_hook "development_info" {
    commands     = ["apply"]
    execute      = ["echo", "Development deployment complete. Services available at http://localhost:8000"]
    run_on_error = false
  }
}
