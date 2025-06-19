# The 7 Space Production Environment Terragrunt Configuration
# Enterprise-grade Infrastructure as Code for The 7 Space Art Gallery & Wellness Center

# Include the root terragrunt.hcl configuration
include "root" {
  path = find_in_parent_folders()
}

# Configure Terragrunt to use the terraform modules
terraform {
  source = "../../modules//the7space-infrastructure"
}

# Environment-specific inputs for The 7 Space production
inputs = {
  # Environment identification
  environment = "the7space-production"
  business_entity = "the_7_space"
  
  # The 7 Space specific configuration
  entity_name = "The 7 Space Art Gallery & Wellness Center"
  entity_domain = "the7space.com"
  api_domain = "api.the7space.com"
  contact_count = 191
  
  # Production scaling configuration
  enable_monitoring = true
  enable_autoscaling = true
  enable_high_availability = true
  
  # Application scaling
  min_replicas = 2
  max_replicas = 6
  cpu_threshold = 70
  memory_threshold = 80
  
  # Database configuration
  mongodb_replica_count = 3
  mongodb_storage = "100Gi"
  mongodb_backup_enabled = true
  mongodb_backup_retention_days = 30
  
  # Redis configuration
  redis_replica_count = 2
  redis_storage = "20Gi"
  redis_persistence_enabled = true
  redis_backup_enabled = true
  
  # Monitoring and observability
  prometheus_storage = "50Gi"
  prometheus_retention_days = 30
  grafana_persistence_enabled = true
  
  # Networking configuration
  enable_ssl = true
  enable_cdn = true
  enable_waf = true
  enable_ddos_protection = true
  
  # Security configuration (highly restrictive for production)
  allowed_cidr_blocks = [
    # Add specific IP ranges for production access
    # These should be set via environment variables or secrets
    # Example: "203.0.113.0/24"  # Office network
    # Example: "198.51.100.0/24" # VPN network
  ]
  
  # SSL/TLS configuration
  ssl_certificate_arn = get_env("THE_7_SPACE_SSL_CERT_ARN", "")
  ssl_policy = "ELBSecurityPolicy-TLS-1-2-2017-01"
  
  # Backup and disaster recovery
  backup_enabled = true
  backup_schedule = "cron(0 2 * * ? *)"  # Daily at 2 AM UTC
  backup_retention_days = 30
  point_in_time_recovery_enabled = true
  
  # Secrets management
  secrets_backend = "aws_secrets_manager"
  secrets_kms_key_id = get_env("THE_7_SPACE_KMS_KEY_ID", "")
  enable_secrets_rotation = true
  secrets_rotation_schedule = "rate(7 days)"
  
  # The 7 Space specific database IDs (from Notion)
  notion_databases = {
    contacts = get_env("THE_7_SPACE_CONTACTS_DB", "")
    artworks = get_env("THE_7_SPACE_ARTWORKS_DB", "")
    artists = get_env("THE_7_SPACE_ARTISTS_DB", "")
    events = get_env("THE_7_SPACE_EVENTS_DB", "")
    services = get_env("THE_7_SPACE_SERVICES_DB", "")
    appointments = get_env("THE_7_SPACE_APPOINTMENTS_DB", "")
    classes = get_env("THE_7_SPACE_CLASSES_DB", "")
    sales = get_env("THE_7_SPACE_SALES_DB", "")
    marketing = get_env("THE_7_SPACE_MARKETING_DB", "")
    analytics = get_env("THE_7_SPACE_ANALYTICS_DB", "")
  }
  
  # WordPress SiteGround integration
  wordpress_integration = {
    enabled = true
    url = "https://the7space.com"
    api_endpoint = "/wp-json/wp/v2/"
    webhook_endpoint = "/wp-json/the7space/v1/webhook"
  }
  
  # Gallery-specific configuration
  gallery_config = {
    enabled = true
    artwork_processing = true
    artist_onboarding = true
    exhibition_scheduling = true
    sales_tracking = true
    inventory_management = true
  }
  
  # Wellness center configuration
  wellness_config = {
    enabled = true
    appointment_scheduling = true
    class_management = true
    client_intake = true
    practitioner_management = true
    resource_booking = true
  }
  
  # Marketing automation configuration
  marketing_config = {
    enabled = true
    lead_scoring = true
    email_campaigns = true
    visitor_tracking = true
    conversion_optimization = true
    analytics_tracking = true
  }
  
  # Workflow automation configuration
  workflow_config = {
    contact_workflows = true
    gallery_workflows = true
    wellness_workflows = true
    marketing_workflows = true
    batch_processing_size = 10
    retry_attempts = 3
    retry_delay_seconds = 300
  }
  
  # Performance and resource limits
  resource_limits = {
    app_cpu_limit = "2000m"
    app_memory_limit = "4Gi"
    app_cpu_request = "1000m"
    app_memory_request = "2Gi"
    
    mongodb_cpu_limit = "1500m"
    mongodb_memory_limit = "3Gi"
    mongodb_cpu_request = "500m"
    mongodb_memory_request = "1Gi"
    
    redis_cpu_limit = "500m"
    redis_memory_limit = "1Gi"
    redis_cpu_request = "100m"
    redis_memory_request = "256Mi"
  }
  
  # Health check configuration
  health_checks = {
    app_health_check_path = "/health"
    app_health_check_interval = 30
    app_health_check_timeout = 30
    app_health_check_retries = 5
    app_health_check_start_period = 120
    
    db_health_check_interval = 30
    db_health_check_timeout = 10
    db_health_check_retries = 5
    
    external_service_health_check_interval = 60
    external_service_health_check_timeout = 15
    external_service_health_check_retries = 3
  }
  
  # Logging and monitoring configuration
  logging_config = {
    log_level = "INFO"
    json_logs = true
    log_retention_days = 30
    log_rotation_size = "100MB"
    centralized_logging = true
    log_aggregation_enabled = true
  }
  
  # Alerting configuration
  alerting_config = {
    cpu_alert_threshold = 80
    memory_alert_threshold = 85
    disk_alert_threshold = 90
    response_time_alert_threshold = 1000
    error_rate_alert_threshold = 5
    
    notification_channels = {
      email_enabled = true
      email_recipients = ["admin@the7space.com", "tech@the7space.com"]
      slack_enabled = false
      webhook_enabled = false
    }
  }
  
  # Maintenance configuration
  maintenance_config = {
    maintenance_window_start = "02:00"
    maintenance_window_end = "04:00"
    maintenance_timezone = "UTC"
    auto_patching_enabled = true
    auto_backup_before_maintenance = true
  }
  
  # Compliance and security
  compliance_config = {
    encryption_at_rest = true
    encryption_in_transit = true
    audit_logging = true
    access_logging = true
    security_scanning = true
    vulnerability_assessment = true
  }
  
  # Cost optimization
  cost_optimization = {
    enable_spot_instances = false  # Disabled for production stability
    enable_reserved_instances = true
    enable_auto_shutdown = false  # Production should run 24/7
    cost_monitoring = true
    budget_alerts = true
  }
  
  # Tags for resource management
  additional_tags = {
    BusinessEntity = "The7Space"
    ContactCount = "191"
    WorkloadType = "ArtGalleryWellnessCenter"
    CriticalityLevel = "High"
    BackupRequired = "Yes"
    MonitoringLevel = "Enhanced"
    ComplianceRequired = "Yes"
    CostCenter = "The7Space-Operations"
    DataClassification = "Confidential"
    DisasterRecoveryTier = "Tier1"
  }
}

# Generate provider configuration
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    consul = {
      source  = "hashicorp/consul"
      version = "~> 2.0"
    }
    vault = {
      source  = "hashicorp/vault"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = merge(var.common_tags, {
      Environment = "the7space-production"
      ManagedBy   = "terragrunt"
      Project     = "The7Space-AutomationPlatform"
    })
  }
}

provider "docker" {
  host = var.docker_host
}

provider "consul" {
  address    = var.consul_address
  datacenter = "the7space-production"
}

provider "vault" {
  address = var.vault_address
}
EOF
}

# Generate backend configuration
generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  backend "s3" {
    bucket         = "higherself-terraform-state-the7space-production"
    key            = "the7space/production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "higherself-terraform-locks-the7space-production"
    
    # Enable versioning and server-side encryption
    versioning = true
    server_side_encryption_configuration {
      rule {
        apply_server_side_encryption_by_default {
          sse_algorithm = "AES256"
        }
      }
    }
  }
}
EOF
}

# Generate variables file
generate "variables" {
  path      = "variables.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "the7space-production"
}

variable "business_entity" {
  description = "Business entity identifier"
  type        = string
  default     = "the_7_space"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "docker_host" {
  description = "Docker host"
  type        = string
  default     = "unix:///var/run/docker.sock"
}

variable "consul_address" {
  description = "Consul address"
  type        = string
  default     = "localhost:8500"
}

variable "vault_address" {
  description = "Vault address"
  type        = string
  default     = "http://localhost:8200"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
EOF
}
