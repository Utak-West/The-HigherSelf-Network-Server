#!/usr/bin/env python3
"""
HigherSelf Network Server - Secrets Management Setup Script

This script sets up the complete secrets management infrastructure including:
- HashiCorp Vault initialization
- Docker secrets creation
- AWS Secrets Manager setup (optional)
- Secret rotation configuration
- Audit logging setup
"""

import asyncio
import json
import logging
import os
import secrets
import string
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click
import hvac
import boto3
from cryptography.fernet import Fernet

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SecretsSetupManager:
    """Manager for setting up secrets management infrastructure."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.vault_client: Optional[hvac.Client] = None
        self.aws_client: Optional[boto3.client] = None
        self.project_root = Path(__file__).parent.parent
        
    def generate_secure_password(self, length: int = 32) -> str:
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_api_key(self, length: int = 64) -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(length)
    
    async def setup_vault(self, vault_addr: str = "http://localhost:8200") -> Dict[str, str]:
        """Setup HashiCorp Vault with initial configuration."""
        logger.info("Setting up HashiCorp Vault...")
        
        try:
            # Initialize Vault client
            self.vault_client = hvac.Client(url=vault_addr)
            
            # Check if Vault is already initialized
            if not self.vault_client.sys.is_initialized():
                logger.info("Initializing Vault...")
                
                # Initialize Vault with 5 key shares and threshold of 3
                init_response = self.vault_client.sys.initialize(
                    secret_shares=5,
                    secret_threshold=3
                )
                
                unseal_keys = init_response['keys']
                root_token = init_response['root_token']
                
                # Unseal Vault
                for key in unseal_keys[:3]:  # Use first 3 keys to unseal
                    self.vault_client.sys.submit_unseal_key(key)
                
                # Set root token
                self.vault_client.token = root_token
                
                logger.info("Vault initialized successfully")
                
                # Save keys securely (in production, distribute these securely)
                vault_keys = {
                    'unseal_keys': unseal_keys,
                    'root_token': root_token
                }
                
                # Write to secure file (development only)
                if self.environment == "development":
                    keys_file = self.project_root / f"vault_keys_{self.environment}.json"
                    with open(keys_file, 'w') as f:
                        json.dump(vault_keys, f, indent=2)
                    os.chmod(keys_file, 0o600)
                    logger.info(f"Vault keys saved to {keys_file}")
                
                return vault_keys
            else:
                logger.info("Vault is already initialized")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to setup Vault: {e}")
            raise
    
    async def configure_vault_policies(self):
        """Configure Vault policies for different access levels."""
        logger.info("Configuring Vault policies...")
        
        if not self.vault_client:
            raise Exception("Vault client not initialized")
        
        # Application policy
        app_policy = f"""
        path "higherself-{self.environment}/data/*" {{
            capabilities = ["read"]
        }}
        
        path "auth/token/renew-self" {{
            capabilities = ["update"]
        }}
        """
        
        self.vault_client.sys.create_or_update_policy(
            name=f"higherself-app-{self.environment}",
            policy=app_policy
        )
        
        # Service-specific policies
        services = ["notion", "database", "api-keys", "webhooks"]
        for service in services:
            service_policy = f"""
            path "higherself-{self.environment}/data/{service}/*" {{
                capabilities = ["read"]
            }}
            """
            
            self.vault_client.sys.create_or_update_policy(
                name=f"higherself-{service}-{self.environment}",
                policy=service_policy
            )
        
        logger.info("Vault policies configured successfully")
    
    async def setup_vault_secrets(self) -> Dict[str, str]:
        """Setup initial secrets in Vault."""
        logger.info("Setting up initial secrets in Vault...")
        
        if not self.vault_client:
            raise Exception("Vault client not initialized")
        
        # Enable KV v2 secrets engine
        try:
            self.vault_client.sys.enable_secrets_engine(
                backend_type='kv',
                path=f'higherself-{self.environment}',
                options={'version': '2'}
            )
        except Exception as e:
            if "path is already in use" not in str(e):
                raise
        
        # Generate and store secrets
        secrets_data = {
            # API Keys
            'api_keys/notion_api_token': {'value': 'REPLACE_WITH_ACTUAL_NOTION_TOKEN'},
            'api_keys/openai_api_key': {'value': 'REPLACE_WITH_ACTUAL_OPENAI_KEY'},
            'api_keys/anthropic_api_key': {'value': 'REPLACE_WITH_ACTUAL_ANTHROPIC_KEY'},
            'api_keys/huggingface_api_key': {'value': 'REPLACE_WITH_ACTUAL_HUGGINGFACE_KEY'},
            
            # Database credentials
            'database/mongodb_password': {'value': self.generate_secure_password()},
            'database/redis_password': {'value': self.generate_secure_password()},
            'database/supabase_api_key': {'value': 'REPLACE_WITH_ACTUAL_SUPABASE_KEY'},
            
            # Security keys
            'jwt/secret_key': {'value': self.generate_api_key()},
            'webhooks/secret': {'value': self.generate_api_key(32)},
            'encryption/key': {'value': Fernet.generate_key().decode()},
            
            # Third-party integrations
            'api_keys/typeform_api_key': {'value': 'REPLACE_WITH_ACTUAL_TYPEFORM_KEY'},
            'api_keys/airtable_api_key': {'value': 'REPLACE_WITH_ACTUAL_AIRTABLE_KEY'},
            'api_keys/gohighlevel_client_secret': {'value': 'REPLACE_WITH_ACTUAL_GHL_SECRET'},
        }
        
        generated_secrets = {}
        
        for secret_path, secret_data in secrets_data.items():
            try:
                self.vault_client.secrets.kv.v2.create_or_update_secret(
                    path=secret_path,
                    secret=secret_data
                )
                
                # Store generated secrets for return
                if not secret_data['value'].startswith('REPLACE_WITH_ACTUAL'):
                    generated_secrets[secret_path] = secret_data['value']
                
                logger.info(f"Created secret: {secret_path}")
                
            except Exception as e:
                logger.error(f"Failed to create secret {secret_path}: {e}")
        
        logger.info("Initial secrets setup completed")
        return generated_secrets
    
    async def setup_docker_secrets(self, secrets_data: Dict[str, str]):
        """Setup Docker secrets for containerized deployment."""
        logger.info("Setting up Docker secrets...")
        
        try:
            for secret_name, secret_value in secrets_data.items():
                # Convert path to Docker secret name
                docker_secret_name = f"higherself-{secret_name.replace('/', '-')}-{self.environment}"
                
                # Create Docker secret
                cmd = [
                    "docker", "secret", "create",
                    docker_secret_name,
                    "-"
                ]
                
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate(input=secret_value)
                
                if process.returncode == 0:
                    logger.info(f"Created Docker secret: {docker_secret_name}")
                else:
                    if "already exists" in stderr:
                        logger.info(f"Docker secret already exists: {docker_secret_name}")
                    else:
                        logger.error(f"Failed to create Docker secret {docker_secret_name}: {stderr}")
        
        except Exception as e:
            logger.error(f"Failed to setup Docker secrets: {e}")
    
    async def setup_aws_secrets_manager(self, secrets_data: Dict[str, str]):
        """Setup AWS Secrets Manager (optional)."""
        if not os.getenv("AWS_ACCESS_KEY_ID"):
            logger.info("AWS credentials not found, skipping AWS Secrets Manager setup")
            return
        
        logger.info("Setting up AWS Secrets Manager...")
        
        try:
            self.aws_client = boto3.client('secretsmanager', region_name='us-east-1')
            
            for secret_path, secret_value in secrets_data.items():
                secret_name = f"higherself-network-server-{self.environment}-{secret_path.replace('/', '-')}"
                
                try:
                    self.aws_client.create_secret(
                        Name=secret_name,
                        SecretString=json.dumps({'value': secret_value}),
                        Description=f"HigherSelf Network Server {self.environment} - {secret_path}"
                    )
                    logger.info(f"Created AWS secret: {secret_name}")
                    
                except self.aws_client.exceptions.ResourceExistsException:
                    logger.info(f"AWS secret already exists: {secret_name}")
                    
        except Exception as e:
            logger.error(f"Failed to setup AWS Secrets Manager: {e}")
    
    async def create_environment_file(self, vault_keys: Dict[str, str]):
        """Create environment-specific .env file with Vault configuration."""
        logger.info(f"Creating .env.{self.environment} file...")
        
        env_file = self.project_root / f".env.{self.environment}"
        template_file = self.project_root / f".env.{self.environment}.template"
        
        if template_file.exists():
            # Copy template and update with Vault configuration
            with open(template_file, 'r') as f:
                content = f.read()
            
            # Update Vault token if available
            if 'root_token' in vault_keys:
                content = content.replace('VAULT_TOKEN_FROM_SECURE_STORAGE', vault_keys['root_token'])
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            os.chmod(env_file, 0o600)
            logger.info(f"Created {env_file}")
        else:
            logger.warning(f"Template file {template_file} not found")
    
    async def setup_complete_infrastructure(self, vault_addr: str = "http://localhost:8200"):
        """Setup complete secrets management infrastructure."""
        logger.info(f"Setting up complete secrets management infrastructure for {self.environment}")
        
        try:
            # 1. Setup Vault
            vault_keys = await self.setup_vault(vault_addr)
            
            # 2. Configure Vault policies
            await self.configure_vault_policies()
            
            # 3. Setup initial secrets
            generated_secrets = await self.setup_vault_secrets()
            
            # 4. Setup Docker secrets
            await self.setup_docker_secrets(generated_secrets)
            
            # 5. Setup AWS Secrets Manager (optional)
            await self.setup_aws_secrets_manager(generated_secrets)
            
            # 6. Create environment file
            await self.create_environment_file(vault_keys)
            
            logger.info("Secrets management infrastructure setup completed successfully!")
            
            # Print summary
            print("\n" + "="*60)
            print("SECRETS MANAGEMENT SETUP SUMMARY")
            print("="*60)
            print(f"Environment: {self.environment}")
            print(f"Vault Address: {vault_addr}")
            print(f"Generated Secrets: {len(generated_secrets)}")
            
            if vault_keys and self.environment == "development":
                print(f"\nVault Keys saved to: vault_keys_{self.environment}.json")
                print("⚠️  IMPORTANT: Store these keys securely!")
            
            print("\nNext Steps:")
            print("1. Update placeholder secrets with actual API keys")
            print("2. Test secret retrieval with the application")
            print("3. Configure secret rotation schedules")
            print("4. Set up monitoring and alerting")
            print("="*60)
            
        except Exception as e:
            logger.error(f"Failed to setup secrets management infrastructure: {e}")
            raise


@click.command()
@click.option('--environment', '-e', default='development', 
              type=click.Choice(['development', 'staging', 'production']),
              help='Environment to setup')
@click.option('--vault-addr', default='http://localhost:8200',
              help='Vault server address')
@click.option('--skip-docker', is_flag=True, help='Skip Docker secrets setup')
@click.option('--skip-aws', is_flag=True, help='Skip AWS Secrets Manager setup')
def main(environment: str, vault_addr: str, skip_docker: bool, skip_aws: bool):
    """Setup secrets management infrastructure for HigherSelf Network Server."""
    
    print(f"Setting up secrets management for {environment} environment...")
    
    manager = SecretsSetupManager(environment)
    
    try:
        asyncio.run(manager.setup_complete_infrastructure(vault_addr))
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nSetup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
