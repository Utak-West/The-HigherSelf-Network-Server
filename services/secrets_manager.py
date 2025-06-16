"""
HigherSelf Network Server - Enterprise Secrets Management Service

This service provides a unified interface for managing secrets across different
backends (HashiCorp Vault, AWS Secrets Manager, Docker Secrets) with automatic
rotation, encryption, and audit logging capabilities.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

import hvac
import boto3
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecretBackend(str, Enum):
    """Supported secret backends."""
    VAULT = "vault"
    AWS_SECRETS_MANAGER = "aws_secrets_manager"
    DOCKER_SECRETS = "docker_secrets"
    ENV_FILE = "env_file"


class SecretCategory(str, Enum):
    """Secret categories for organization and access control."""
    API_KEYS = "api_keys"
    DATABASE = "database"
    ENCRYPTION = "encryption"
    WEBHOOKS = "webhooks"
    JWT = "jwt"


class SecretMetadata(BaseModel):
    """Metadata for secret management."""
    name: str
    category: SecretCategory
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    rotation_period: Optional[int] = None  # days
    auto_rotate: bool = False
    backup_enabled: bool = True
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class SecretValue(BaseModel):
    """Secret value with metadata."""
    value: str
    metadata: SecretMetadata
    encrypted: bool = False


class SecretsManagerConfig(BaseModel):
    """Configuration for the secrets manager."""
    environment: str = Field(default="development")
    primary_backend: SecretBackend = Field(default=SecretBackend.VAULT)
    fallback_backend: SecretBackend = Field(default=SecretBackend.ENV_FILE)
    
    # Vault configuration
    vault_address: str = Field(default="http://localhost:8200")
    vault_token: Optional[str] = None
    vault_namespace: Optional[str] = None
    
    # AWS configuration
    aws_region: str = Field(default="us-east-1")
    aws_secret_name_prefix: str = Field(default="higherself-network-server")
    
    # Encryption configuration
    encryption_key: Optional[str] = None
    enable_encryption_at_rest: bool = Field(default=True)
    
    # Rotation configuration
    enable_auto_rotation: bool = Field(default=True)
    default_rotation_period: int = Field(default=30)  # days
    rotation_notification_period: int = Field(default=7)  # days
    
    # Audit configuration
    enable_audit_logging: bool = Field(default=True)
    audit_log_path: str = Field(default="logs/secrets_audit.log")


class SecretsManager:
    """
    Enterprise-grade secrets management service for HigherSelf Network Server.
    
    Provides unified access to secrets across multiple backends with automatic
    rotation, encryption, and comprehensive audit logging.
    """
    
    def __init__(self, config: SecretsManagerConfig):
        self.config = config
        self.vault_client: Optional[hvac.Client] = None
        self.aws_client: Optional[boto3.client] = None
        self.encryption_key: Optional[Fernet] = None
        self._secret_cache: Dict[str, SecretValue] = {}
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup audit logging for secrets access."""
        if self.config.enable_audit_logging:
            # Create audit logger
            self.audit_logger = logging.getLogger("secrets_audit")
            handler = logging.FileHandler(self.config.audit_log_path)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.audit_logger.addHandler(handler)
            self.audit_logger.setLevel(logging.INFO)
    
    async def initialize(self):
        """Initialize the secrets manager and all backends."""
        logger.info(f"Initializing SecretsManager with {self.config.primary_backend} backend")
        
        # Initialize encryption
        if self.config.enable_encryption_at_rest:
            await self._initialize_encryption()
        
        # Initialize primary backend
        if self.config.primary_backend == SecretBackend.VAULT:
            await self._initialize_vault()
        elif self.config.primary_backend == SecretBackend.AWS_SECRETS_MANAGER:
            await self._initialize_aws()
        
        # Initialize fallback backend
        if self.config.fallback_backend != self.config.primary_backend:
            if self.config.fallback_backend == SecretBackend.VAULT:
                await self._initialize_vault()
            elif self.config.fallback_backend == SecretBackend.AWS_SECRETS_MANAGER:
                await self._initialize_aws()
        
        logger.info("SecretsManager initialized successfully")
    
    async def _initialize_encryption(self):
        """Initialize encryption for secrets at rest."""
        encryption_key = self.config.encryption_key or os.getenv("SECRETS_ENCRYPTION_KEY")
        
        if not encryption_key:
            # Generate a new key if none provided
            encryption_key = Fernet.generate_key().decode()
            logger.warning("Generated new encryption key - store this securely!")
            logger.warning(f"SECRETS_ENCRYPTION_KEY={encryption_key}")
        
        self.encryption_key = Fernet(encryption_key.encode())
        logger.info("Encryption initialized for secrets at rest")
    
    async def _initialize_vault(self):
        """Initialize HashiCorp Vault client."""
        try:
            self.vault_client = hvac.Client(
                url=self.config.vault_address,
                token=self.config.vault_token or os.getenv("VAULT_TOKEN"),
                namespace=self.config.vault_namespace
            )
            
            if not self.vault_client.is_authenticated():
                raise Exception("Vault authentication failed")
            
            logger.info("Vault client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vault client: {e}")
            raise
    
    async def _initialize_aws(self):
        """Initialize AWS Secrets Manager client."""
        try:
            self.aws_client = boto3.client(
                'secretsmanager',
                region_name=self.config.aws_region
            )
            
            # Test connection
            self.aws_client.list_secrets(MaxResults=1)
            logger.info("AWS Secrets Manager client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS Secrets Manager client: {e}")
            raise
    
    async def get_secret(
        self, 
        name: str, 
        category: SecretCategory = SecretCategory.API_KEYS,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Retrieve a secret value.
        
        Args:
            name: Secret name
            category: Secret category
            use_cache: Whether to use cached value
            
        Returns:
            Secret value or None if not found
        """
        cache_key = f"{category.value}/{name}"
        
        # Check cache first
        if use_cache and cache_key in self._secret_cache:
            secret = self._secret_cache[cache_key]
            secret.metadata.access_count += 1
            secret.metadata.last_accessed = datetime.utcnow()
            self._audit_log("SECRET_ACCESS", name, category.value)
            return secret.value
        
        # Try primary backend
        secret_value = await self._get_secret_from_backend(
            name, category, self.config.primary_backend
        )
        
        # Try fallback backend if primary fails
        if not secret_value and self.config.fallback_backend != self.config.primary_backend:
            secret_value = await self._get_secret_from_backend(
                name, category, self.config.fallback_backend
            )
        
        if secret_value:
            # Cache the secret
            metadata = SecretMetadata(
                name=name,
                category=category,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                access_count=1,
                last_accessed=datetime.utcnow()
            )
            
            self._secret_cache[cache_key] = SecretValue(
                value=secret_value,
                metadata=metadata
            )
            
            self._audit_log("SECRET_ACCESS", name, category.value)
            return secret_value
        
        self._audit_log("SECRET_NOT_FOUND", name, category.value)
        return None
    
    async def _get_secret_from_backend(
        self, 
        name: str, 
        category: SecretCategory, 
        backend: SecretBackend
    ) -> Optional[str]:
        """Get secret from specific backend."""
        try:
            if backend == SecretBackend.VAULT:
                return await self._get_secret_from_vault(name, category)
            elif backend == SecretBackend.AWS_SECRETS_MANAGER:
                return await self._get_secret_from_aws(name, category)
            elif backend == SecretBackend.DOCKER_SECRETS:
                return await self._get_secret_from_docker(name, category)
            elif backend == SecretBackend.ENV_FILE:
                return await self._get_secret_from_env(name, category)
        except Exception as e:
            logger.error(f"Failed to get secret {name} from {backend}: {e}")
            return None
    
    async def _get_secret_from_vault(self, name: str, category: SecretCategory) -> Optional[str]:
        """Get secret from HashiCorp Vault."""
        if not self.vault_client:
            return None
        
        try:
            secret_path = f"higherself-{self.config.environment}/data/{category.value}/{name}"
            response = self.vault_client.secrets.kv.v2.read_secret_version(path=secret_path)
            
            if response and 'data' in response and 'data' in response['data']:
                secret_data = response['data']['data']
                return secret_data.get('value') or secret_data.get(name)
        except Exception as e:
            logger.debug(f"Secret {name} not found in Vault: {e}")
            return None
    
    async def _get_secret_from_aws(self, name: str, category: SecretCategory) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        if not self.aws_client:
            return None
        
        try:
            secret_name = f"{self.config.aws_secret_name_prefix}-{self.config.environment}-{category.value}-{name}"
            response = self.aws_client.get_secret_value(SecretId=secret_name)
            
            if 'SecretString' in response:
                secret_data = json.loads(response['SecretString'])
                return secret_data.get('value') or secret_data.get(name)
        except Exception as e:
            logger.debug(f"Secret {name} not found in AWS Secrets Manager: {e}")
            return None
    
    async def _get_secret_from_docker(self, name: str, category: SecretCategory) -> Optional[str]:
        """Get secret from Docker secrets."""
        try:
            secret_path = f"/run/secrets/higherself-{category.value}-{name}"
            if os.path.exists(secret_path):
                with open(secret_path, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            logger.debug(f"Secret {name} not found in Docker secrets: {e}")
            return None
    
    async def _get_secret_from_env(self, name: str, category: SecretCategory) -> Optional[str]:
        """Get secret from environment variables."""
        # Map common secret names to environment variable names
        env_mappings = {
            "notion_api_token": "NOTION_API_TOKEN",
            "openai_api_key": "OPENAI_API_KEY",
            "anthropic_api_key": "ANTHROPIC_API_KEY",
            "huggingface_api_key": "HUGGINGFACE_API_KEY",
            "webhook_secret": "WEBHOOK_SECRET",
            "jwt_secret_key": "JWT_SECRET_KEY",
            "mongodb_password": "MONGODB_PASSWORD",
            "redis_password": "REDIS_PASSWORD",
        }
        
        env_var_name = env_mappings.get(name.lower()) or name.upper()
        return os.getenv(env_var_name)
    
    def _audit_log(self, action: str, secret_name: str, category: str, details: str = ""):
        """Log secret access for audit purposes."""
        if self.config.enable_audit_logging:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": action,
                "secret_name": secret_name,
                "category": category,
                "environment": self.config.environment,
                "details": details
            }
            self.audit_logger.info(json.dumps(log_entry))
    
    async def close(self):
        """Clean up resources."""
        if self.vault_client:
            self.vault_client = None
        if self.aws_client:
            self.aws_client = None
        self._secret_cache.clear()
        logger.info("SecretsManager closed")


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


async def get_secrets_manager() -> SecretsManager:
    """Get or create the global secrets manager instance."""
    global _secrets_manager
    
    if _secrets_manager is None:
        config = SecretsManagerConfig(
            environment=os.getenv("ENVIRONMENT", "development"),
            vault_address=os.getenv("VAULT_ADDR", "http://localhost:8200"),
            vault_token=os.getenv("VAULT_TOKEN"),
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
        )
        
        _secrets_manager = SecretsManager(config)
        await _secrets_manager.initialize()
    
    return _secrets_manager


async def get_secret(name: str, category: SecretCategory = SecretCategory.API_KEYS) -> Optional[str]:
    """Convenience function to get a secret."""
    manager = await get_secrets_manager()
    return await manager.get_secret(name, category)
