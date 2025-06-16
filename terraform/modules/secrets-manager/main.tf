# HigherSelf Network Server - Secrets Manager Module
# AWS Secrets Manager implementation following Gruntwork patterns

# KMS key for secrets encryption
resource "aws_kms_key" "secrets_key" {
  description             = var.kms_key_description
  key_usage              = var.kms_key_usage
  customer_master_key_spec = var.kms_key_spec
  deletion_window_in_days = 7
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-secrets-key-${var.environment}"
    Component = "secrets-management"
  })
}

# KMS key alias
resource "aws_kms_alias" "secrets_key_alias" {
  name          = "alias/${var.project_name}-secrets-${var.environment}"
  target_key_id = aws_kms_key.secrets_key.key_id
}

# Create secrets in AWS Secrets Manager
resource "aws_secretsmanager_secret" "secrets" {
  for_each = var.secrets
  
  name        = "${var.project_name}-${each.key}-${var.environment}"
  description = each.value.description
  kms_key_id  = aws_kms_key.secrets_key.arn
  
  recovery_window_in_days = lookup(each.value, "recovery_window_in_days", 30)
  
  tags = merge(var.common_tags, var.secret_tags, {
    Name = "${var.project_name}-${each.key}-${var.environment}"
    SecretType = each.key
  })
}

# Create secret versions with values
resource "aws_secretsmanager_secret_version" "secret_values" {
  for_each = {
    for k, v in var.secrets : k => v
    if lookup(v, "secret_string", "") != ""
  }
  
  secret_id     = aws_secretsmanager_secret.secrets[each.key].id
  secret_string = each.value.secret_string
}

# Generate random passwords for secrets that need them
resource "aws_secretsmanager_secret_version" "generated_secrets" {
  for_each = {
    for k, v in var.secrets : k => v
    if lookup(v, "generate_secret_string", null) != null
  }
  
  secret_id = aws_secretsmanager_secret.secrets[each.key].id
  secret_string = jsonencode(
    lookup(each.value.generate_secret_string, "secret_string_template", null) != null ?
    merge(
      jsondecode(each.value.generate_secret_string.secret_string_template),
      {
        (each.value.generate_secret_string.generate_string_key) = random_password.generated_passwords[each.key].result
      }
    ) :
    {
      password = random_password.generated_passwords[each.key].result
    }
  )
}

# Generate random passwords
resource "random_password" "generated_passwords" {
  for_each = {
    for k, v in var.secrets : k => v
    if lookup(v, "generate_secret_string", null) != null
  }
  
  length  = lookup(each.value.generate_secret_string, "password_length", 32)
  special = true
  
  override_special = lookup(each.value.generate_secret_string, "exclude_characters", null) != null ? 
    replace("!@#$%^&*()_+-=[]{}|;:,.<>?", each.value.generate_secret_string.exclude_characters, "") : 
    "!@#$%^&*()_+-=[]{}|;:,.<>?"
}

# IAM policy for secrets access
resource "aws_iam_policy" "secrets_access" {
  name        = "${var.project_name}-secrets-access-${var.environment}"
  description = "Policy for accessing HigherSelf Network Server secrets"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          for secret in aws_secretsmanager_secret.secrets : secret.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = [aws_kms_key.secrets_key.arn]
      }
    ]
  })
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-secrets-access-${var.environment}"
    Component = "secrets-management"
  })
}

# IAM role for applications to access secrets
resource "aws_iam_role" "secrets_access_role" {
  name = "${var.project_name}-secrets-access-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "ec2.amazonaws.com",
            "ecs-tasks.amazonaws.com"
          ]
        }
      }
    ]
  })
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-secrets-access-role-${var.environment}"
    Component = "secrets-management"
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "secrets_access_attachment" {
  role       = aws_iam_role.secrets_access_role.name
  policy_arn = aws_iam_policy.secrets_access.arn
}

# Instance profile for EC2 instances
resource "aws_iam_instance_profile" "secrets_access_profile" {
  name = "${var.project_name}-secrets-access-profile-${var.environment}"
  role = aws_iam_role.secrets_access_role.name
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-secrets-access-profile-${var.environment}"
    Component = "secrets-management"
  })
}
