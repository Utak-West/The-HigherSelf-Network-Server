# HigherSelf Network Server - Secrets Manager Outputs
# Output values for the secrets manager module

output "secrets_arns" {
  description = "ARNs of all created secrets"
  value = {
    for k, v in aws_secretsmanager_secret.secrets : k => v.arn
  }
}

output "secrets_names" {
  description = "Names of all created secrets"
  value = {
    for k, v in aws_secretsmanager_secret.secrets : k => v.name
  }
}

output "kms_key_id" {
  description = "ID of the KMS key used for secrets encryption"
  value       = aws_kms_key.secrets_key.key_id
}

output "kms_key_arn" {
  description = "ARN of the KMS key used for secrets encryption"
  value       = aws_kms_key.secrets_key.arn
}

output "kms_key_alias" {
  description = "Alias of the KMS key used for secrets encryption"
  value       = aws_kms_alias.secrets_key_alias.name
}

output "secrets_access_policy_arn" {
  description = "ARN of the IAM policy for accessing secrets"
  value       = aws_iam_policy.secrets_access.arn
}

output "secrets_access_role_arn" {
  description = "ARN of the IAM role for accessing secrets"
  value       = aws_iam_role.secrets_access_role.arn
}

output "secrets_access_role_name" {
  description = "Name of the IAM role for accessing secrets"
  value       = aws_iam_role.secrets_access_role.name
}

output "instance_profile_name" {
  description = "Name of the instance profile for EC2 access to secrets"
  value       = aws_iam_instance_profile.secrets_access_profile.name
}

output "instance_profile_arn" {
  description = "ARN of the instance profile for EC2 access to secrets"
  value       = aws_iam_instance_profile.secrets_access_profile.arn
}

# Output for application configuration
output "secret_retrieval_commands" {
  description = "AWS CLI commands to retrieve secrets (for documentation)"
  value = {
    for k, v in aws_secretsmanager_secret.secrets : k => "aws secretsmanager get-secret-value --secret-id ${v.name} --query SecretString --output text"
  }
}

# Environment variables mapping for applications
output "environment_variable_mapping" {
  description = "Mapping of secret names to environment variable names"
  value = {
    notion_api_token      = "NOTION_API_TOKEN"
    notion_parent_page_id = "NOTION_PARENT_PAGE_ID"
    mongodb_credentials   = "MONGODB_CREDENTIALS"
    redis_credentials     = "REDIS_CREDENTIALS"
    openai_api_key       = "OPENAI_API_KEY"
    huggingface_token    = "HUGGINGFACE_TOKEN"
    webhook_secret       = "WEBHOOK_SECRET"
    grafana_admin_password = "GRAFANA_ADMIN_PASSWORD"
    jwt_secret           = "JWT_SECRET"
    session_secret       = "SESSION_SECRET"
  }
}
