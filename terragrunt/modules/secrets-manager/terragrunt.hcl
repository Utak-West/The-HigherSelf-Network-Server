# HigherSelf Network Server - Secrets Manager Module
# Terragrunt configuration for AWS Secrets Manager integration

# Include the root terragrunt.hcl configuration
include "root" {
  path = find_in_parent_folders()
}

# Configure the terraform source for secrets management
terraform {
  source = "${get_parent_terragrunt_dir()}/terraform//modules/secrets-manager"
}

# Secrets manager specific inputs
inputs = {
  # Secrets configuration
  secrets = {
    # Notion Integration Secrets
    notion_api_token = {
      description = "Notion API token for HigherSelf Network Server integration"
      secret_string = get_env("NOTION_API_TOKEN", "")
      recovery_window_in_days = 7
    }
    
    notion_parent_page_id = {
      description = "Notion parent page ID for database creation"
      secret_string = get_env("NOTION_PARENT_PAGE_ID", "")
      recovery_window_in_days = 7
    }
    
    # Database Credentials
    mongodb_credentials = {
      description = "MongoDB database credentials"
      generate_secret_string = {
        secret_string_template = jsonencode({
          username = "higherself_admin"
          database = "higherselfnetwork"
        })
        generate_string_key = "password"
        password_length = 32
        exclude_characters = "\"@/\\"
      }
      recovery_window_in_days = 30
    }
    
    redis_credentials = {
      description = "Redis cache credentials"
      generate_secret_string = {
        secret_string_template = jsonencode({
          username = "default"
        })
        generate_string_key = "password"
        password_length = 32
        exclude_characters = "\"@/\\"
      }
      recovery_window_in_days = 30
    }
    
    # API Keys and Tokens
    openai_api_key = {
      description = "OpenAI API key for AI services"
      secret_string = get_env("OPENAI_API_KEY", "")
      recovery_window_in_days = 7
    }
    
    huggingface_token = {
      description = "HuggingFace API token for model access"
      secret_string = get_env("HUGGINGFACE_TOKEN", "")
      recovery_window_in_days = 7
    }
    
    # Webhook and Integration Secrets
    webhook_secret = {
      description = "Webhook secret for secure API communications"
      generate_secret_string = {
        password_length = 64
        exclude_characters = "\"@/\\"
      }
      recovery_window_in_days = 7
    }
    
    # Monitoring and Admin Credentials
    grafana_admin_password = {
      description = "Grafana admin password for monitoring dashboard"
      secret_string = get_env("GRAFANA_ADMIN_PASSWORD", "")
      recovery_window_in_days = 30
    }
    
    # JWT and Session Secrets
    jwt_secret = {
      description = "JWT secret for authentication tokens"
      generate_secret_string = {
        password_length = 64
        exclude_characters = "\"@/\\"
      }
      recovery_window_in_days = 30
    }
    
    session_secret = {
      description = "Session secret for secure session management"
      generate_secret_string = {
        password_length = 64
        exclude_characters = "\"@/\\"
      }
      recovery_window_in_days = 30
    }
  }
  
  # KMS key configuration for encryption
  kms_key_description = "HigherSelf Network Server secrets encryption key"
  kms_key_usage = "ENCRYPT_DECRYPT"
  kms_key_spec = "SYMMETRIC_DEFAULT"
  
  # Automatic rotation configuration
  enable_rotation = {
    mongodb_credentials = {
      automatically_after_days = 90
    }
    redis_credentials = {
      automatically_after_days = 90
    }
    jwt_secret = {
      automatically_after_days = 180
    }
    session_secret = {
      automatically_after_days = 180
    }
  }
  
  # Access policies
  secret_access_principals = [
    # ECS task role (when we migrate to ECS)
    # EC2 instance role (for current Docker deployment)
    # Add specific IAM roles that need access to secrets
  ]
  
  # Tagging
  secret_tags = {
    Component = "secrets-management"
    Security = "high"
    Compliance = "required"
  }
}

# Dependencies - secrets should be created before other services
dependencies {
  paths = []
}

# Hooks for secrets management
terraform {
  before_hook "secrets_validation" {
    commands = ["plan", "apply"]
    execute = ["bash", "-c", <<-EOF
      echo "🔐 Validating secrets configuration..."
      
      # Check for required environment variables
      required_vars=("NOTION_API_TOKEN" "OPENAI_API_KEY")
      missing_vars=()
      
      for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
          missing_vars+=("$var")
        fi
      done
      
      if [ ${#missing_vars[@]} -gt 0 ]; then
        echo "❌ Missing required environment variables:"
        printf '%s\n' "${missing_vars[@]}"
        echo "Please set these variables before deploying secrets"
        exit 1
      fi
      
      echo "✅ Secrets validation passed"
    EOF
    ]
  }
  
  after_hook "secrets_info" {
    commands     = ["apply"]
    execute      = ["echo", "🔐 Secrets management deployed. Use AWS CLI or console to manage secrets."]
    run_on_error = false
  }
}
