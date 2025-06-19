# ======================================================
# HIGHERSELF NETWORK SERVER - DOCKER DEPLOYMENT VARIABLES
# Variable definitions for Docker container orchestration
# ======================================================

# Environment configuration
variable "environment" {
  description = "Deployment environment (development, staging, production)"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "higherself-network-server"
}

# Docker configuration
variable "docker_registry" {
  description = "Docker registry URL"
  type        = string
  default     = "ghcr.io/utak-west"
}

variable "docker_image_name" {
  description = "Docker image name"
  type        = string
  default     = "thehigherselfnetworkserver"
}

variable "docker_image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

# Container configuration
variable "container_port" {
  description = "Container port for the main application"
  type        = number
  default     = 8000
}

variable "container_replicas" {
  description = "Number of container replicas"
  type        = number
  default     = 1
}

variable "container_memory_limit" {
  description = "Memory limit for containers"
  type        = string
  default     = "2Gi"
}

variable "container_cpu_limit" {
  description = "CPU limit for containers"
  type        = string
  default     = "1000m"
}

# Multi-entity configuration
variable "multi_entity_mode" {
  description = "Enable multi-entity mode"
  type        = bool
  default     = true
}

variable "primary_business_entity" {
  description = "Primary business entity"
  type        = string
  default     = "the_7_space"
  validation {
    condition     = contains(["the_7_space", "am_consulting", "higherself_core"], var.primary_business_entity)
    error_message = "Primary business entity must be one of: the_7_space, am_consulting, higherself_core."
  }
}

variable "business_entities" {
  description = "List of enabled business entities"
  type        = list(string)
  default     = ["the_7_space", "am_consulting", "higherself_core"]
}

# Database configuration
variable "mongodb_enabled" {
  description = "Enable MongoDB deployment"
  type        = bool
  default     = true
}

variable "mongodb_username" {
  description = "MongoDB application username"
  type        = string
  default     = "higherself_user"
}

variable "mongodb_password" {
  description = "MongoDB application password"
  type        = string
  sensitive   = true
}

variable "mongodb_root_username" {
  description = "MongoDB root username"
  type        = string
  default     = "admin"
}

variable "mongodb_root_password" {
  description = "MongoDB root password"
  type        = string
  sensitive   = true
}

variable "mongodb_database" {
  description = "MongoDB database name"
  type        = string
}

variable "mongodb_cache_size" {
  description = "MongoDB WiredTiger cache size in GB"
  type        = string
  default     = "1"
}

variable "redis_enabled" {
  description = "Enable Redis deployment"
  type        = bool
  default     = true
}

variable "redis_password" {
  description = "Redis password"
  type        = string
  sensitive   = true
  default     = ""
}

# Service mesh configuration
variable "consul_enabled" {
  description = "Enable Consul deployment"
  type        = bool
  default     = true
}

# Monitoring configuration
variable "prometheus_enabled" {
  description = "Enable Prometheus deployment"
  type        = bool
  default     = true
}

variable "grafana_enabled" {
  description = "Enable Grafana deployment"
  type        = bool
  default     = true
}

# Networking configuration
variable "network_subnet" {
  description = "Docker network subnet"
  type        = string
  default     = "172.20.0.0/16"
}

variable "enable_ingress" {
  description = "Enable ingress configuration"
  type        = bool
  default     = true
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "localhost"
}

variable "enable_ssl" {
  description = "Enable SSL/TLS"
  type        = bool
  default     = false
}

# Security configuration
variable "enable_network_policies" {
  description = "Enable network policies"
  type        = bool
  default     = false
}

variable "enable_pod_security_policies" {
  description = "Enable pod security policies"
  type        = bool
  default     = false
}

# Secrets configuration
variable "secrets_backend" {
  description = "Secrets backend (env_file, vault, aws_secrets_manager)"
  type        = string
  default     = "env_file"
  validation {
    condition     = contains(["env_file", "vault", "aws_secrets_manager"], var.secrets_backend)
    error_message = "Secrets backend must be one of: env_file, vault, aws_secrets_manager."
  }
}

variable "vault_enabled" {
  description = "Enable Vault deployment"
  type        = bool
  default     = false
}

variable "aws_secrets_manager_enabled" {
  description = "Enable AWS Secrets Manager integration"
  type        = bool
  default     = false
}

# Logging configuration
variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR."
  }
}

variable "enable_json_logs" {
  description = "Enable JSON structured logging"
  type        = bool
  default     = false
}

# Resource limits per environment
variable "resource_limits" {
  description = "Resource limits per environment"
  type = map(object({
    cpu_request    = string
    cpu_limit      = string
    memory_request = string
    memory_limit   = string
  }))
  default = {
    development = {
      cpu_request    = "100m"
      cpu_limit      = "500m"
      memory_request = "256Mi"
      memory_limit   = "1Gi"
    }
    staging = {
      cpu_request    = "250m"
      cpu_limit      = "1000m"
      memory_request = "512Mi"
      memory_limit   = "2Gi"
    }
    production = {
      cpu_request    = "500m"
      cpu_limit      = "2000m"
      memory_request = "1Gi"
      memory_limit   = "4Gi"
    }
  }
}

# Environment-specific configuration
variable "environment_config" {
  description = "Environment-specific configuration"
  type = map(object({
    debug_enabled                = bool
    hot_reload                  = bool
    expose_debug_ports          = bool
    resource_requests_enabled   = bool
    performance_testing         = optional(bool, false)
    high_availability          = optional(bool, false)
    security_hardening         = optional(bool, false)
  }))
  default = {
    development = {
      debug_enabled              = true
      hot_reload                = true
      expose_debug_ports        = true
      resource_requests_enabled = false
    }
    staging = {
      debug_enabled              = false
      hot_reload                = false
      expose_debug_ports        = false
      resource_requests_enabled = true
      performance_testing       = true
    }
    production = {
      debug_enabled              = false
      hot_reload                = false
      expose_debug_ports        = false
      resource_requests_enabled = true
      high_availability         = true
      security_hardening        = true
    }
  }
}

# Additional environment variables
variable "additional_env_vars" {
  description = "Additional environment variables for the application container"
  type        = list(string)
  default     = []
}

# Common tags
variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "HigherSelf-Network-Server"
    ManagedBy   = "terraform"
    Purpose     = "enterprise-automation-platform"
  }
}
