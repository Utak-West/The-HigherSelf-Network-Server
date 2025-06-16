# HigherSelf Network Server - Root Terragrunt Configuration
# Enterprise-grade Infrastructure as Code with Gruntwork integration

# Configure Terragrunt to automatically store tfstate files in an S3 bucket
remote_state {
  backend = "s3"
  config = {
    encrypt        = true
    bucket         = "higherself-terraform-state-${get_env("ENVIRONMENT", "development")}"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = get_env("AWS_REGION", "us-east-1")
    dynamodb_table = "higherself-terraform-locks-${get_env("ENVIRONMENT", "development")}"
    
    # Enable versioning and server-side encryption
    s3_bucket_tags = {
      Project     = "HigherSelf-Network-Server"
      Environment = get_env("ENVIRONMENT", "development")
      ManagedBy   = "terragrunt"
      Purpose     = "terraform-state-storage"
      Owner       = "HigherSelf-Network"
    }
    
    dynamodb_table_tags = {
      Project     = "HigherSelf-Network-Server"
      Environment = get_env("ENVIRONMENT", "development")
      ManagedBy   = "terragrunt"
      Purpose     = "terraform-state-locking"
      Owner       = "HigherSelf-Network"
    }
  }
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
}

# Generate an AWS provider block
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
# Auto-generated provider configuration by Terragrunt
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
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "HigherSelf-Network-Server"
      Environment = var.environment
      ManagedBy   = "terragrunt"
      Owner       = "HigherSelf-Network"
      Purpose     = "enterprise-automation-platform"
    }
  }
}

provider "docker" {
  host = var.docker_host
}
EOF
}

# Configure root level variables that will be inherited by all child terragrunt configs
inputs = {
  # Project configuration
  project_name = "higherself-network-server"
  environment  = get_env("ENVIRONMENT", "development")
  
  # AWS configuration
  aws_region = get_env("AWS_REGION", "us-east-1")
  
  # Docker configuration
  docker_host = get_env("DOCKER_HOST", "unix:///var/run/docker.sock")
  
  # Common tags applied to all resources
  common_tags = {
    Project     = "HigherSelf-Network-Server"
    Environment = get_env("ENVIRONMENT", "development")
    ManagedBy   = "terragrunt"
    Owner       = "HigherSelf-Network"
    Purpose     = "enterprise-automation-platform"
    Repository  = "https://github.com/Utak-West/The-HigherSelf-Network-Server"
  }
}

# Configure Terragrunt to use common terraform configurations
terraform {
  # Force Terragrunt to copy the terraform configurations from the specified source into a temporary folder and run
  # terraform in that temporary folder
  source = "${get_parent_terragrunt_dir()}/terraform//modules"
  
  # Configure terraform to automatically retry on known errors
  extra_arguments "retry_lock" {
    commands  = get_terraform_commands_that_need_locking()
    arguments = ["-lock-timeout=20m"]
  }
  
  # Automatically format terraform code
  extra_arguments "fmt" {
    commands = ["fmt"]
    arguments = ["-recursive"]
  }
  
  # Configure terraform to automatically validate configurations
  extra_arguments "validate" {
    commands = ["validate"]
  }
}

# Configure Terragrunt logging
terragrunt_version_constraints = ">= 0.45.0"

# Skip outputs if the module doesn't define any
skip = false

# Prevent destruction of critical resources in production
prevent_destroy = get_env("ENVIRONMENT", "development") == "production" ? true : false
