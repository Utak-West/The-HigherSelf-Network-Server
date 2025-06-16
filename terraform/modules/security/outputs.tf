# HigherSelf Network Server - Security Module Outputs

output "vault_mount_paths" {
  description = "Vault mount paths for different environments"
  value = {
    for env, path in local.secret_paths : env => vault_mount.env_secrets[env].path
  }
}

output "vault_policies" {
  description = "Created Vault policies"
  value = {
    admin    = vault_policy.higherself_admin.name
    app      = vault_policy.higherself_app.name
    notion   = vault_policy.higherself_notion.name
    database = vault_policy.higherself_database.name
  }
}

output "aws_secrets_manager_arn" {
  description = "AWS Secrets Manager secret ARN"
  value       = var.enable_aws_secrets ? aws_secretsmanager_secret.higherself_master[0].arn : null
}

output "docker_secret_names" {
  description = "Docker secret names"
  value = var.enable_docker_secrets ? {
    vault_token = docker_secret.vault_token[0].name
  } : {}
}

output "secret_paths" {
  description = "Secret paths for different categories"
  value = {
    for category, config in local.secret_categories : category => {
      path        = "higherself-${var.environment}/data/${category}"
      description = config.description
      ttl         = config.ttl
    }
  }
}

output "rotation_config_path" {
  description = "Path to secret rotation configuration"
  value       = vault_generic_secret.rotation_config.path
}

output "security_endpoints" {
  description = "Security service endpoints"
  value = {
    vault_address = var.vault_address
    vault_ui      = "${var.vault_address}/ui"
  }
}

output "access_policies" {
  description = "Access policies for different service accounts"
  value = {
    for account, config in var.service_accounts : account => {
      policies = config.policies
      ttl      = config.ttl
    }
  }
}

output "monitoring_config" {
  description = "Monitoring and alerting configuration"
  value = {
    audit_logging_enabled = var.enable_audit_logging
    metrics_enabled      = var.enable_metrics
    alert_thresholds     = var.alert_thresholds
  }
}

output "backup_config" {
  description = "Backup and recovery configuration"
  value = {
    retention_days        = var.backup_retention_days
    storage_type         = var.backup_storage_type
    bucket_name          = var.backup_bucket_name
    cross_region_enabled = var.enable_cross_region_backup
  }
}

output "encryption_config" {
  description = "Encryption configuration"
  value = {
    key_algorithm        = var.encryption_key_algorithm
    transit_enabled      = var.enable_transit_encryption
  }
}
