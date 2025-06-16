"""
HigherSelf Network Server - Secrets Configuration

Environment-specific secrets management configuration with support for
multiple backends and automatic failover.
"""

import os
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from services.secrets_manager import SecretBackend, SecretCategory


class Environment(str, Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SecretDefinition(BaseModel):
    """Definition of a secret with its properties."""
    name: str
    category: SecretCategory
    required: bool = True
    description: str = ""
    env_var_name: Optional[str] = None
    rotation_period_days: int = 30
    auto_rotate: bool = False
    backup_enabled: bool = True


class EnvironmentSecretsConfig(BaseModel):
    """Environment-specific secrets configuration."""
    environment: Environment
    primary_backend: SecretBackend
    fallback_backend: SecretBackend
    secrets: List[SecretDefinition]
    
    # Backend-specific configuration
    vault_config: Dict = Field(default_factory=dict)
    aws_config: Dict = Field(default_factory=dict)
    docker_config: Dict = Field(default_factory=dict)


# Development environment configuration
DEVELOPMENT_CONFIG = EnvironmentSecretsConfig(
    environment=Environment.DEVELOPMENT,
    primary_backend=SecretBackend.ENV_FILE,
    fallback_backend=SecretBackend.VAULT,
    secrets=[
        # Core API Keys
        SecretDefinition(
            name="notion_api_token",
            category=SecretCategory.API_KEYS,
            required=True,
            description="Notion API integration token",
            env_var_name="NOTION_API_TOKEN",
            rotation_period_days=90,
            auto_rotate=False
        ),
        SecretDefinition(
            name="openai_api_key",
            category=SecretCategory.API_KEYS,
            required=True,
            description="OpenAI API key for LLM operations",
            env_var_name="OPENAI_API_KEY",
            rotation_period_days=60,
            auto_rotate=False
        ),
        SecretDefinition(
            name="anthropic_api_key",
            category=SecretCategory.API_KEYS,
            required=False,
            description="Anthropic Claude API key",
            env_var_name="ANTHROPIC_API_KEY",
            rotation_period_days=60,
            auto_rotate=False
        ),
        SecretDefinition(
            name="huggingface_api_key",
            category=SecretCategory.API_KEYS,
            required=False,
            description="Hugging Face API key",
            env_var_name="HUGGINGFACE_API_KEY",
            rotation_period_days=60,
            auto_rotate=False
        ),
        
        # Database Credentials
        SecretDefinition(
            name="mongodb_password",
            category=SecretCategory.DATABASE,
            required=True,
            description="MongoDB application user password",
            env_var_name="MONGODB_PASSWORD",
            rotation_period_days=90,
            auto_rotate=False
        ),
        SecretDefinition(
            name="redis_password",
            category=SecretCategory.DATABASE,
            required=False,
            description="Redis authentication password",
            env_var_name="REDIS_PASSWORD",
            rotation_period_days=90,
            auto_rotate=False
        ),
        SecretDefinition(
            name="supabase_api_key",
            category=SecretCategory.DATABASE,
            required=True,
            description="Supabase API key",
            env_var_name="SUPABASE_API_KEY",
            rotation_period_days=60,
            auto_rotate=False
        ),
        
        # Security Keys
        SecretDefinition(
            name="jwt_secret_key",
            category=SecretCategory.JWT,
            required=True,
            description="JWT signing secret key",
            env_var_name="JWT_SECRET_KEY",
            rotation_period_days=30,
            auto_rotate=False
        ),
        SecretDefinition(
            name="webhook_secret",
            category=SecretCategory.WEBHOOKS,
            required=True,
            description="Webhook validation secret",
            env_var_name="WEBHOOK_SECRET",
            rotation_period_days=60,
            auto_rotate=False
        ),
        SecretDefinition(
            name="encryption_key",
            category=SecretCategory.ENCRYPTION,
            required=True,
            description="Application encryption key",
            env_var_name="ENCRYPTION_KEY",
            rotation_period_days=365,
            auto_rotate=False
        ),
        
        # Third-party Integrations
        SecretDefinition(
            name="typeform_api_key",
            category=SecretCategory.API_KEYS,
            required=False,
            description="TypeForm API key",
            env_var_name="TYPEFORM_API_KEY",
            rotation_period_days=90,
            auto_rotate=False
        ),
        SecretDefinition(
            name="airtable_api_key",
            category=SecretCategory.API_KEYS,
            required=False,
            description="Airtable API key",
            env_var_name="AIRTABLE_API_KEY",
            rotation_period_days=90,
            auto_rotate=False
        ),
        SecretDefinition(
            name="gohighlevel_client_secret",
            category=SecretCategory.API_KEYS,
            required=False,
            description="GoHighLevel OAuth client secret",
            env_var_name="GOHIGHLEVEL_CLIENT_SECRET",
            rotation_period_days=90,
            auto_rotate=False
        ),
    ],
    vault_config={
        "address": "http://localhost:8200",
        "mount_path": "higherself-development"
    }
)

# Staging environment configuration
STAGING_CONFIG = EnvironmentSecretsConfig(
    environment=Environment.STAGING,
    primary_backend=SecretBackend.VAULT,
    fallback_backend=SecretBackend.AWS_SECRETS_MANAGER,
    secrets=DEVELOPMENT_CONFIG.secrets.copy(),  # Same secrets as dev
    vault_config={
        "address": os.getenv("VAULT_ADDR", "https://vault.staging.higherself.network"),
        "mount_path": "higherself-staging"
    },
    aws_config={
        "region": "us-east-1",
        "secret_name_prefix": "higherself-network-server-staging"
    }
)

# Update staging secrets for more frequent rotation
for secret in STAGING_CONFIG.secrets:
    if secret.category == SecretCategory.API_KEYS:
        secret.rotation_period_days = 60
        secret.auto_rotate = True
    elif secret.category == SecretCategory.JWT:
        secret.rotation_period_days = 14
        secret.auto_rotate = True

# Production environment configuration
PRODUCTION_CONFIG = EnvironmentSecretsConfig(
    environment=Environment.PRODUCTION,
    primary_backend=SecretBackend.VAULT,
    fallback_backend=SecretBackend.AWS_SECRETS_MANAGER,
    secrets=DEVELOPMENT_CONFIG.secrets.copy(),  # Same secrets as dev
    vault_config={
        "address": os.getenv("VAULT_ADDR", "https://vault.higherself.network"),
        "mount_path": "higherself-production",
        "namespace": "higherself"
    },
    aws_config={
        "region": "us-east-1",
        "secret_name_prefix": "higherself-network-server-production",
        "kms_key_id": "alias/higherself-secrets"
    },
    docker_config={
        "secrets_path": "/run/secrets"
    }
)

# Update production secrets for enterprise-grade rotation
for secret in PRODUCTION_CONFIG.secrets:
    secret.backup_enabled = True
    if secret.category == SecretCategory.API_KEYS:
        secret.rotation_period_days = 30
        secret.auto_rotate = True
    elif secret.category == SecretCategory.JWT:
        secret.rotation_period_days = 7
        secret.auto_rotate = True
    elif secret.category == SecretCategory.WEBHOOKS:
        secret.rotation_period_days = 30
        secret.auto_rotate = True


# Environment configuration mapping
ENVIRONMENT_CONFIGS = {
    Environment.DEVELOPMENT: DEVELOPMENT_CONFIG,
    Environment.STAGING: STAGING_CONFIG,
    Environment.PRODUCTION: PRODUCTION_CONFIG,
}


def get_secrets_config(environment: str = None) -> EnvironmentSecretsConfig:
    """
    Get secrets configuration for the specified environment.
    
    Args:
        environment: Environment name (defaults to ENVIRONMENT env var)
        
    Returns:
        Environment-specific secrets configuration
    """
    if not environment:
        environment = os.getenv("ENVIRONMENT", "development")
    
    env_enum = Environment(environment.lower())
    return ENVIRONMENT_CONFIGS[env_enum]


def get_required_secrets(environment: str = None) -> List[SecretDefinition]:
    """
    Get list of required secrets for the specified environment.
    
    Args:
        environment: Environment name
        
    Returns:
        List of required secret definitions
    """
    config = get_secrets_config(environment)
    return [secret for secret in config.secrets if secret.required]


def get_secrets_by_category(
    category: SecretCategory, 
    environment: str = None
) -> List[SecretDefinition]:
    """
    Get secrets by category for the specified environment.
    
    Args:
        category: Secret category
        environment: Environment name
        
    Returns:
        List of secrets in the specified category
    """
    config = get_secrets_config(environment)
    return [secret for secret in config.secrets if secret.category == category]


def validate_environment_secrets(environment: str = None) -> Dict[str, bool]:
    """
    Validate that all required secrets are available in the environment.
    
    Args:
        environment: Environment name
        
    Returns:
        Dictionary mapping secret names to availability status
    """
    config = get_secrets_config(environment)
    results = {}
    
    for secret in config.secrets:
        if secret.required:
            # Check if secret is available via environment variable
            env_value = os.getenv(secret.env_var_name) if secret.env_var_name else None
            results[secret.name] = bool(env_value)
    
    return results
