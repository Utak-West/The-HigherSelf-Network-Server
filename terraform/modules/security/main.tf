# HigherSelf Network Server - Security Module
# Enterprise-grade secrets management and security infrastructure

terraform {
  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "~> 3.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

# Local variables for security configuration
locals {
  project_name = var.project_name
  environment  = var.environment
  
  # Secret categories for organization
  secret_categories = {
    "api_keys" = {
      description = "Third-party API keys and tokens"
      ttl         = "30d"
    }
    "database" = {
      description = "Database credentials and connection strings"
      ttl         = "90d"
    }
    "encryption" = {
      description = "Encryption keys and certificates"
      ttl         = "365d"
    }
    "webhooks" = {
      description = "Webhook secrets and signing keys"
      ttl         = "60d"
    }
    "jwt" = {
      description = "JWT signing keys and tokens"
      ttl         = "30d"
    }
  }
  
  # Environment-specific secret paths
  secret_paths = {
    development = "secret/higherself/dev"
    staging     = "secret/higherself/staging"
    production  = "secret/higherself/prod"
  }
  
  common_tags = {
    Project     = local.project_name
    Environment = local.environment
    ManagedBy   = "terraform"
    Purpose     = "secrets-management"
  }
}

# HashiCorp Vault Configuration
resource "vault_mount" "higherself_secrets" {
  path        = "secret"
  type        = "kv-v2"
  description = "HigherSelf Network Server secrets store"
  
  options = {
    version = "2"
  }
}

# Create environment-specific secret engines
resource "vault_mount" "env_secrets" {
  for_each = local.secret_paths
  
  path        = "higherself-${each.key}"
  type        = "kv-v2"
  description = "HigherSelf ${each.key} environment secrets"
  
  options = {
    version = "2"
  }
}

# Vault policies for different access levels
resource "vault_policy" "higherself_admin" {
  name = "higherself-admin"
  
  policy = <<EOT
# Admin policy for HigherSelf Network Server
path "higherself-*/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "secret/data/higherself/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "secret/metadata/higherself/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Allow token creation for service accounts
path "auth/token/create" {
  capabilities = ["create", "update"]
}
EOT
}

resource "vault_policy" "higherself_app" {
  name = "higherself-app-${var.environment}"
  
  policy = <<EOT
# Application policy for HigherSelf Network Server
path "higherself-${var.environment}/data/*" {
  capabilities = ["read"]
}

path "secret/data/higherself/${var.environment}/*" {
  capabilities = ["read"]
}

# Allow token renewal
path "auth/token/renew-self" {
  capabilities = ["update"]
}
EOT
}

# Service-specific policies
resource "vault_policy" "higherself_notion" {
  name = "higherself-notion-${var.environment}"
  
  policy = <<EOT
# Notion service policy
path "higherself-${var.environment}/data/api_keys/notion" {
  capabilities = ["read"]
}

path "higherself-${var.environment}/data/webhooks/notion" {
  capabilities = ["read"]
}
EOT
}

resource "vault_policy" "higherself_database" {
  name = "higherself-database-${var.environment}"
  
  policy = <<EOT
# Database service policy
path "higherself-${var.environment}/data/database/*" {
  capabilities = ["read"]
}
EOT
}

# AWS Secrets Manager integration (for cloud deployments)
resource "aws_secretsmanager_secret" "higherself_master" {
  count = var.enable_aws_secrets ? 1 : 0
  
  name        = "higherself-network-server-${var.environment}"
  description = "Master secrets for HigherSelf Network Server ${var.environment}"
  
  tags = local.common_tags
}

# Docker secrets for containerized deployments
resource "docker_secret" "vault_token" {
  count = var.enable_docker_secrets ? 1 : 0
  
  name = "higherself-vault-token-${var.environment}"
  data = base64encode(var.vault_token)
  
  labels {
    label = "environment"
    value = var.environment
  }
  
  labels {
    label = "service"
    value = "vault"
  }
}

# Secret rotation configuration
resource "vault_generic_secret" "rotation_config" {
  path = "higherself-${var.environment}/config/rotation"
  
  data_json = jsonencode({
    api_keys = {
      rotation_period = "30d"
      notification_period = "7d"
      auto_rotate = var.environment == "production"
    }
    database = {
      rotation_period = "90d"
      notification_period = "14d"
      auto_rotate = false
    }
    jwt = {
      rotation_period = "30d"
      notification_period = "7d"
      auto_rotate = true
    }
    webhooks = {
      rotation_period = "60d"
      notification_period = "10d"
      auto_rotate = var.environment == "production"
    }
  })
}
