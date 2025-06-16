# HigherSelf Network Server - Secrets Manager Variables
# Variable definitions for AWS Secrets Manager module

variable "project_name" {
  description = "Name of the HigherSelf Network project"
  type        = string
  default     = "higherself-network-server"
}

variable "environment" {
  description = "Deployment environment (development, staging, production)"
  type        = string
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Map of secrets to create in AWS Secrets Manager"
  type = map(object({
    description             = string
    secret_string          = optional(string)
    recovery_window_in_days = optional(number, 30)
    generate_secret_string = optional(object({
      secret_string_template = optional(string)
      generate_string_key   = optional(string, "password")
      password_length       = optional(number, 32)
      exclude_characters    = optional(string)
    }))
  }))
  default = {}
}

variable "kms_key_description" {
  description = "Description for the KMS key used to encrypt secrets"
  type        = string
  default     = "HigherSelf Network Server secrets encryption key"
}

variable "kms_key_usage" {
  description = "Usage type for the KMS key"
  type        = string
  default     = "ENCRYPT_DECRYPT"
  
  validation {
    condition     = contains(["ENCRYPT_DECRYPT", "SIGN_VERIFY"], var.kms_key_usage)
    error_message = "KMS key usage must be either ENCRYPT_DECRYPT or SIGN_VERIFY."
  }
}

variable "kms_key_spec" {
  description = "Key spec for the KMS key"
  type        = string
  default     = "SYMMETRIC_DEFAULT"
}

variable "enable_rotation" {
  description = "Map of secrets that should have automatic rotation enabled"
  type = map(object({
    automatically_after_days = number
  }))
  default = {}
}

variable "secret_access_principals" {
  description = "List of IAM principals that should have access to secrets"
  type        = list(string)
  default     = []
}

variable "secret_tags" {
  description = "Additional tags to apply to secrets"
  type        = map(string)
  default = {
    Component = "secrets-management"
    Security  = "high"
  }
}

# AWS Region variable
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}
