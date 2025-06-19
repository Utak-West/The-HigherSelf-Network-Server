# ======================================================
# HIGHERSELF NETWORK SERVER - DOCKER DEPLOYMENT MODULE
# Terragrunt configuration for Docker container orchestration
# ======================================================

# Include the root terragrunt configuration
include "root" {
  path = find_in_parent_folders()
}

# Include environment-specific configuration
include "env" {
  path = find_in_parent_folders("env.hcl")
}

# Terraform source configuration
terraform {
  source = "${get_parent_terragrunt_dir()}/terraform//modules/docker-deployment"
}

# Dependencies - ensure secrets and infrastructure are deployed first
dependencies {
  paths = [
    "../secrets-manager",
    "../networking",
    "../monitoring"
  ]
}

# Module inputs
inputs = {
  # Environment configuration
  environment = get_env("ENVIRONMENT", "development")
  project_name = "higherself-network-server"
  
  # Docker configuration
  docker_image_name = "thehigherselfnetworkserver"
  docker_image_tag = get_env("IMAGE_TAG", "latest")
  docker_registry = get_env("DOCKER_REGISTRY", "ghcr.io/utak-west")
  
  # Container configuration
  container_port = 8000
  container_replicas = get_env("CONTAINER_REPLICAS", "2")
  container_memory_limit = get_env("CONTAINER_MEMORY_LIMIT", "2Gi")
  container_cpu_limit = get_env("CONTAINER_CPU_LIMIT", "1000m")
  
  # Multi-entity configuration
  multi_entity_mode = true
  primary_business_entity = get_env("PRIMARY_BUSINESS_ENTITY", "the_7_space")
  business_entities = [
    "the_7_space",
    "am_consulting", 
    "higherself_core"
  ]
  
  # Database configuration
  mongodb_enabled = true
  mongodb_replica_count = get_env("MONGODB_REPLICA_COUNT", "1")
  mongodb_storage_size = get_env("MONGODB_STORAGE_SIZE", "10Gi")
  
  redis_enabled = true
  redis_replica_count = get_env("REDIS_REPLICA_COUNT", "1")
  redis_storage_size = get_env("REDIS_STORAGE_SIZE", "5Gi")
  
  # Service mesh configuration
  consul_enabled = true
  consul_replica_count = get_env("CONSUL_REPLICA_COUNT", "1")
  
  # Monitoring configuration
  prometheus_enabled = get_env("ENABLE_MONITORING", "true")
  grafana_enabled = get_env("ENABLE_MONITORING", "true")
  prometheus_storage_size = get_env("PROMETHEUS_STORAGE_SIZE", "20Gi")
  grafana_storage_size = get_env("GRAFANA_STORAGE_SIZE", "5Gi")
  
  # Networking configuration
  enable_ingress = get_env("ENABLE_INGRESS", "true")
  domain_name = get_env("API_DOMAIN", "localhost")
  enable_ssl = get_env("ENABLE_SSL", "false")
  
  # Security configuration
  enable_network_policies = get_env("ENABLE_NETWORK_POLICIES", "false")
  enable_pod_security_policies = get_env("ENABLE_POD_SECURITY_POLICIES", "false")
  
  # Secrets configuration
  secrets_backend = get_env("SECRETS_BACKEND", "env_file")
  vault_enabled = get_env("VAULT_ENABLED", "false")
  aws_secrets_manager_enabled = get_env("ENABLE_AWS_SECRETS_MANAGER", "false")
  
  # Environment-specific secrets
  notion_api_token_secret = "higherself-notion-api-token-${get_env("ENVIRONMENT", "development")}"
  openai_api_key_secret = "higherself-openai-api-key-${get_env("ENVIRONMENT", "development")}"
  mongodb_password_secret = "higherself-mongodb-password-${get_env("ENVIRONMENT", "development")}"
  redis_password_secret = "higherself-redis-password-${get_env("ENVIRONMENT", "development")}"
  
  # Backup configuration
  enable_backups = get_env("ENABLE_AUTOMATED_BACKUPS", "false")
  backup_schedule = get_env("BACKUP_SCHEDULE", "0 1 * * *")
  backup_retention_days = get_env("BACKUP_RETENTION_DAYS", "7")
  
  # Auto-scaling configuration
  enable_autoscaling = get_env("ENABLE_AUTO_SCALING", "false")
  min_replicas = get_env("MIN_REPLICAS", "1")
  max_replicas = get_env("MAX_REPLICAS", "5")
  cpu_threshold = get_env("CPU_THRESHOLD", "70")
  memory_threshold = get_env("MEMORY_THRESHOLD", "80")
  
  # Health check configuration
  health_check_path = "/health"
  health_check_interval = "30s"
  health_check_timeout = "10s"
  health_check_retries = 3
  
  # Logging configuration
  enable_json_logs = get_env("JSON_LOGS", "false")
  log_level = get_env("LOG_LEVEL", "INFO")
  log_retention_days = get_env("LOG_RETENTION_DAYS", "30")
  
  # Resource limits per environment
  resource_limits = {
    development = {
      cpu_request = "100m"
      cpu_limit = "500m"
      memory_request = "256Mi"
      memory_limit = "1Gi"
    }
    staging = {
      cpu_request = "250m"
      cpu_limit = "1000m"
      memory_request = "512Mi"
      memory_limit = "2Gi"
    }
    production = {
      cpu_request = "500m"
      cpu_limit = "2000m"
      memory_request = "1Gi"
      memory_limit = "4Gi"
    }
  }
  
  # Volume configuration
  persistent_volumes = {
    mongodb_data = {
      size = get_env("MONGODB_STORAGE_SIZE", "10Gi")
      storage_class = get_env("STORAGE_CLASS", "standard")
      access_mode = "ReadWriteOnce"
    }
    redis_data = {
      size = get_env("REDIS_STORAGE_SIZE", "5Gi")
      storage_class = get_env("STORAGE_CLASS", "standard")
      access_mode = "ReadWriteOnce"
    }
    prometheus_data = {
      size = get_env("PROMETHEUS_STORAGE_SIZE", "20Gi")
      storage_class = get_env("STORAGE_CLASS", "standard")
      access_mode = "ReadWriteOnce"
    }
    grafana_data = {
      size = get_env("GRAFANA_STORAGE_SIZE", "5Gi")
      storage_class = get_env("STORAGE_CLASS", "standard")
      access_mode = "ReadWriteOnce"
    }
    application_logs = {
      size = get_env("LOG_STORAGE_SIZE", "10Gi")
      storage_class = get_env("STORAGE_CLASS", "standard")
      access_mode = "ReadWriteMany"
    }
  }
  
  # Service configuration
  services = {
    higherself_server = {
      port = 8000
      target_port = 8000
      protocol = "TCP"
      type = "ClusterIP"
    }
    mongodb = {
      port = 27017
      target_port = 27017
      protocol = "TCP"
      type = "ClusterIP"
    }
    redis = {
      port = 6379
      target_port = 6379
      protocol = "TCP"
      type = "ClusterIP"
    }
    consul = {
      port = 8500
      target_port = 8500
      protocol = "TCP"
      type = "ClusterIP"
    }
    prometheus = {
      port = 9090
      target_port = 9090
      protocol = "TCP"
      type = "ClusterIP"
    }
    grafana = {
      port = 3000
      target_port = 3000
      protocol = "TCP"
      type = "ClusterIP"
    }
  }
  
  # Environment-specific configuration overrides
  environment_config = {
    development = {
      debug_enabled = true
      hot_reload = true
      expose_debug_ports = true
      resource_requests_enabled = false
    }
    staging = {
      debug_enabled = false
      hot_reload = false
      expose_debug_ports = false
      resource_requests_enabled = true
      performance_testing = true
    }
    production = {
      debug_enabled = false
      hot_reload = false
      expose_debug_ports = false
      resource_requests_enabled = true
      high_availability = true
      security_hardening = true
    }
  }
  
  # Business entity specific configuration
  business_entity_config = {
    the_7_space = {
      contact_count = 191
      primary_workflows = ["gallery_management", "artist_engagement", "event_coordination"]
      notion_workspace_id = get_env("THE_7_SPACE_NOTION_WORKSPACE", "")
    }
    am_consulting = {
      contact_count = 1300
      primary_workflows = ["client_management", "project_tracking", "business_automation"]
      notion_workspace_id = get_env("AM_CONSULTING_NOTION_WORKSPACE", "")
    }
    higherself_core = {
      contact_count = 1300
      primary_workflows = ["community_management", "content_curation", "member_engagement"]
      notion_workspace_id = get_env("HIGHERSELF_CORE_NOTION_WORKSPACE", "")
    }
  }
  
  # Integration configuration
  integrations = {
    notion = {
      enabled = true
      api_token_secret = "higherself-notion-api-token-${get_env("ENVIRONMENT", "development")}"
    }
    openai = {
      enabled = true
      api_key_secret = "higherself-openai-api-key-${get_env("ENVIRONMENT", "development")}"
    }
    huggingface = {
      enabled = get_env("HUGGINGFACE_ENABLED", "true")
      api_key_secret = "higherself-huggingface-api-key-${get_env("ENVIRONMENT", "development")}"
    }
    smtp = {
      enabled = get_env("ENABLE_EMAIL_INTEGRATION", "true")
      host = get_env("SMTP_HOST", "smtp.gmail.com")
      port = get_env("SMTP_PORT", "587")
      use_tls = get_env("SMTP_USE_TLS", "true")
    }
    aws_s3 = {
      enabled = get_env("AWS_S3_ENABLED", "false")
      bucket = get_env("AWS_S3_BUCKET", "")
      region = get_env("AWS_REGION", "us-east-1")
    }
  }
  
  # Common tags for all resources
  common_tags = {
    Project = "HigherSelf-Network-Server"
    Environment = get_env("ENVIRONMENT", "development")
    ManagedBy = "terragrunt"
    Component = "docker-deployment"
    BusinessEntities = "the_7_space,am_consulting,higherself_core"
    Purpose = "enterprise-automation-platform"
  }
}
