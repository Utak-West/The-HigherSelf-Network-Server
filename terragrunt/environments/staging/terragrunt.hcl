# HigherSelf Network Server - Staging Environment Configuration
# Terragrunt configuration for staging environment

# Include the root terragrunt.hcl configuration
include "root" {
  path = find_in_parent_folders()
}

# Configure the terraform source
terraform {
  source = "${get_parent_terragrunt_dir()}/terraform//environments/staging"
}

# Environment-specific inputs
inputs = {
  environment = "staging"
  
  # Staging-specific scaling (production-like but smaller)
  enable_monitoring = true
  enable_autoscaling = true
  min_replicas = 2
  max_replicas = 4
  
  # Staging resource limits (production-like)
  mongodb_storage = "50Gi"
  redis_storage = "10Gi"
  prometheus_storage = "25Gi"
  
  # Staging networking
  enable_ssl = true
  domain_name = get_env("STAGING_DOMAIN", "staging.higherself.network")
  
  # Staging security (more restrictive than development)
  allowed_cidr_blocks = [
    "10.0.0.0/8",     # Internal networks
    "172.16.0.0/12",  # Private networks
    "192.168.0.0/16"  # Local networks
  ]
  
  # Staging database settings
  mongodb_replica_count = 2
  redis_replica_count = 2
  
  # Staging monitoring
  log_level = "INFO"
  enable_debug_endpoints = false
  
  # Staging secrets (will be overridden by environment variables)
  grafana_admin_password = get_env("GRAFANA_ADMIN_PASSWORD", "changeme")
  
  # Staging feature flags
  enable_experimental_features = true
  enable_performance_testing = true
  enable_load_testing = true
}

# Staging-specific dependencies
dependencies {
  paths = []
}

# Staging-specific hooks
terraform {
  before_hook "validate_staging" {
    commands = ["plan", "apply"]
    execute  = ["echo", "Deploying to STAGING environment - Production-like testing"]
  }
  
  before_hook "staging_safety_check" {
    commands = ["apply"]
    execute  = ["bash", "-c", "echo 'Staging deployment requires SSL certificates and proper domain configuration'"]
  }
  
  after_hook "staging_info" {
    commands     = ["apply"]
    execute      = ["echo", "Staging deployment complete. Verify at https://${get_env("STAGING_DOMAIN", "staging.higherself.network")}"]
    run_on_error = false
  }
}
