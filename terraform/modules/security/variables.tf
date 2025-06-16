# HigherSelf Network Server - Security Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "higherself-network-server"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "vault_address" {
  description = "HashiCorp Vault server address"
  type        = string
  default     = "http://localhost:8200"
}

variable "vault_token" {
  description = "HashiCorp Vault authentication token"
  type        = string
  sensitive   = true
}

variable "enable_aws_secrets" {
  description = "Enable AWS Secrets Manager integration"
  type        = bool
  default     = false
}

variable "enable_docker_secrets" {
  description = "Enable Docker secrets for containerized deployments"
  type        = bool
  default     = true
}

variable "aws_region" {
  description = "AWS region for secrets manager"
  type        = string
  default     = "us-east-1"
}

variable "secret_rotation_enabled" {
  description = "Enable automatic secret rotation"
  type        = bool
  default     = true
}

variable "notification_email" {
  description = "Email address for secret rotation notifications"
  type        = string
  default     = ""
}

variable "backup_retention_days" {
  description = "Number of days to retain secret backups"
  type        = number
  default     = 90
}

# Secret configuration variables
variable "secrets_config" {
  description = "Configuration for different types of secrets"
  type = map(object({
    rotation_period     = string
    notification_period = string
    auto_rotate        = bool
    backup_enabled     = bool
  }))
  default = {
    api_keys = {
      rotation_period     = "30d"
      notification_period = "7d"
      auto_rotate        = true
      backup_enabled     = true
    }
    database = {
      rotation_period     = "90d"
      notification_period = "14d"
      auto_rotate        = false
      backup_enabled     = true
    }
    encryption = {
      rotation_period     = "365d"
      notification_period = "30d"
      auto_rotate        = false
      backup_enabled     = true
    }
    webhooks = {
      rotation_period     = "60d"
      notification_period = "10d"
      auto_rotate        = true
      backup_enabled     = true
    }
    jwt = {
      rotation_period     = "30d"
      notification_period = "7d"
      auto_rotate        = true
      backup_enabled     = false
    }
  }
}

# Access control variables
variable "admin_users" {
  description = "List of admin users with full access to secrets"
  type        = list(string)
  default     = []
}

variable "service_accounts" {
  description = "Service accounts and their permissions"
  type = map(object({
    policies = list(string)
    ttl      = string
  }))
  default = {
    "higherself-app" = {
      policies = ["higherself-app"]
      ttl      = "24h"
    }
    "higherself-notion" = {
      policies = ["higherself-notion"]
      ttl      = "12h"
    }
    "higherself-database" = {
      policies = ["higherself-database"]
      ttl      = "24h"
    }
  }
}

# Monitoring and alerting variables
variable "enable_audit_logging" {
  description = "Enable audit logging for secret access"
  type        = bool
  default     = true
}

variable "enable_metrics" {
  description = "Enable metrics collection for secrets management"
  type        = bool
  default     = true
}

variable "alert_thresholds" {
  description = "Alert thresholds for secrets management monitoring"
  type = object({
    failed_auth_attempts = number
    secret_access_rate   = number
    rotation_failures    = number
  })
  default = {
    failed_auth_attempts = 5
    secret_access_rate   = 100
    rotation_failures    = 1
  }
}

# Encryption variables
variable "encryption_key_algorithm" {
  description = "Algorithm for encryption keys"
  type        = string
  default     = "aes256-gcm96"
}

variable "enable_transit_encryption" {
  description = "Enable Vault transit encryption engine"
  type        = bool
  default     = true
}

# Backup and recovery variables
variable "backup_storage_type" {
  description = "Type of storage for secret backups (s3, gcs, azure)"
  type        = string
  default     = "s3"
}

variable "backup_bucket_name" {
  description = "Name of the backup storage bucket"
  type        = string
  default     = ""
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup for disaster recovery"
  type        = bool
  default     = false
}
