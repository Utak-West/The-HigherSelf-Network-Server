# HigherSelf Network Server - Terraform Variables
# Enterprise-grade configuration variables for infrastructure deployment

variable "environment" {
  description = "Deployment environment (development, staging, production)"
  type        = string
  default     = "development"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "project_name" {
  description = "Name of the HigherSelf Network project"
  type        = string
  default     = "higherself-network-server"
}

variable "docker_host" {
  description = "Docker daemon host"
  type        = string
  default     = "unix:///var/run/docker.sock"
}

variable "aws_region" {
  description = "AWS region for cloud resources"
  type        = string
  default     = "us-east-1"
}

# Database Configuration
variable "mongodb_root_user" {
  description = "MongoDB root username"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "mongodb_root_password" {
  description = "MongoDB root password"
  type        = string
  sensitive   = true
}

variable "mongodb_app_user" {
  description = "MongoDB application username"
  type        = string
  default     = "higherself_app"
  sensitive   = true
}

variable "mongodb_app_password" {
  description = "MongoDB application password"
  type        = string
  sensitive   = true
}

variable "mongodb_database" {
  description = "MongoDB database name"
  type        = string
  default     = "higherselfnetwork"
}

# Redis Configuration
variable "redis_password" {
  description = "Redis password"
  type        = string
  default     = ""
  sensitive   = true
}

# Grafana Configuration
variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  default     = "admin"
  sensitive   = true
}

# SSL Configuration
variable "ssl_cert_path" {
  description = "Path to SSL certificate"
  type        = string
  default     = "./deployment/ssl/cert.pem"
}

variable "ssl_key_path" {
  description = "Path to SSL private key"
  type        = string
  default     = "./deployment/ssl/key.pem"
}

# Resource Limits
variable "resource_limits" {
  description = "Resource limits for different environments"
  type = map(object({
    windsurf_agent = object({
      cpu_limit    = string
      memory_limit = string
      replicas     = number
    })
    mongodb = object({
      cpu_limit    = string
      memory_limit = string
      storage_size = string
    })
    redis = object({
      cpu_limit    = string
      memory_limit = string
      storage_size = string
    })
    nginx = object({
      cpu_limit    = string
      memory_limit = string
    })
  }))
  
  default = {
    development = {
      windsurf_agent = {
        cpu_limit    = "1.0"
        memory_limit = "1Gi"
        replicas     = 1
      }
      mongodb = {
        cpu_limit    = "1.0"
        memory_limit = "2Gi"
        storage_size = "10Gi"
      }
      redis = {
        cpu_limit    = "0.5"
        memory_limit = "512Mi"
        storage_size = "5Gi"
      }
      nginx = {
        cpu_limit    = "0.25"
        memory_limit = "128Mi"
      }
    }
    staging = {
      windsurf_agent = {
        cpu_limit    = "2.0"
        memory_limit = "2Gi"
        replicas     = 2
      }
      mongodb = {
        cpu_limit    = "2.0"
        memory_limit = "4Gi"
        storage_size = "50Gi"
      }
      redis = {
        cpu_limit    = "1.0"
        memory_limit = "1Gi"
        storage_size = "10Gi"
      }
      nginx = {
        cpu_limit    = "0.5"
        memory_limit = "256Mi"
      }
    }
    production = {
      windsurf_agent = {
        cpu_limit    = "4.0"
        memory_limit = "4Gi"
        replicas     = 3
      }
      mongodb = {
        cpu_limit    = "4.0"
        memory_limit = "8Gi"
        storage_size = "100Gi"
      }
      redis = {
        cpu_limit    = "2.0"
        memory_limit = "2Gi"
        storage_size = "20Gi"
      }
      nginx = {
        cpu_limit    = "1.0"
        memory_limit = "512Mi"
      }
    }
  }
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable Prometheus and Grafana monitoring"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable centralized logging"
  type        = bool
  default     = true
}

# Backup Configuration
variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

variable "backup_schedule" {
  description = "Cron schedule for automated backups"
  type        = string
  default     = "0 2 * * *"  # Daily at 2 AM
}

# Security Configuration
variable "allowed_ips" {
  description = "List of allowed IP addresses for admin access"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict in production
}

variable "enable_ssl" {
  description = "Enable SSL/TLS encryption"
  type        = bool
  default     = true
}

# Integration Configuration
variable "notion_token" {
  description = "Notion API token"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "huggingface_token" {
  description = "Hugging Face API token"
  type        = string
  sensitive   = true
}

# Cloud Provider Configuration
variable "enable_cloud_deployment" {
  description = "Enable cloud deployment (AWS, GCP, Azure)"
  type        = bool
  default     = false
}

variable "cloud_provider" {
  description = "Cloud provider for deployment"
  type        = string
  default     = "aws"
  
  validation {
    condition     = contains(["aws", "gcp", "azure"], var.cloud_provider)
    error_message = "Cloud provider must be one of: aws, gcp, azure."
  }
}

# Auto-scaling Configuration
variable "enable_autoscaling" {
  description = "Enable auto-scaling for production workloads"
  type        = bool
  default     = false
}

variable "min_replicas" {
  description = "Minimum number of replicas for auto-scaling"
  type        = number
  default     = 1
}

variable "max_replicas" {
  description = "Maximum number of replicas for auto-scaling"
  type        = number
  default     = 10
}

variable "cpu_threshold" {
  description = "CPU utilization threshold for auto-scaling"
  type        = number
  default     = 70
}
