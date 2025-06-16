#!/usr/bin/env python3
"""
HigherSelf Network Server - Interactive Secrets Upload Script

This script helps you securely upload your API keys and credentials to the
secrets management system with guided prompts and validation.
"""

import asyncio
import getpass
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import click
import hvac
from cryptography.fernet import Fernet

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.secrets_config import get_secrets_config, SecretDefinition
from services.secrets_manager import SecretCategory


class SecretUploader:
    """Interactive secret uploader with validation and security."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.vault_client: Optional[hvac.Client] = None
        self.config = get_secrets_config(environment)
        
    def setup_vault_client(self, vault_addr: str = "http://localhost:8200", vault_token: str = None):
        """Setup Vault client connection."""
        try:
            self.vault_client = hvac.Client(url=vault_addr)
            
            if vault_token:
                self.vault_client.token = vault_token
            else:
                # Try to get token from environment
                vault_token = os.getenv("VAULT_TOKEN", "dev-root-token")
                self.vault_client.token = vault_token
            
            if not self.vault_client.is_authenticated():
                raise Exception("Vault authentication failed")
            
            print(f"✅ Connected to Vault at {vault_addr}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Vault: {e}")
            return False
    
    def validate_secret_format(self, secret_name: str, secret_value: str) -> bool:
        """Validate secret format based on known patterns."""
        validations = {
            "notion_api_token": lambda v: v.startswith("secret_") and len(v) > 50,
            "openai_api_key": lambda v: v.startswith("sk-") and len(v) > 40,
            "anthropic_api_key": lambda v: v.startswith("sk-ant-") and len(v) > 40,
            "huggingface_api_key": lambda v: v.startswith("hf_") and len(v) > 30,
            "supabase_api_key": lambda v: len(v) > 30 and not v.startswith("your_"),
            "jwt_secret_key": lambda v: len(v) >= 32,
            "webhook_secret": lambda v: len(v) >= 16,
            "encryption_key": lambda v: len(v) >= 32,
        }
        
        validator = validations.get(secret_name)
        if validator:
            return validator(secret_value)
        
        # Generic validation - not empty and not placeholder
        return len(secret_value) > 0 and not secret_value.startswith("your_")
    
    def get_secret_description(self, secret_def: SecretDefinition) -> str:
        """Get user-friendly description for a secret."""
        descriptions = {
            "notion_api_token": "Notion API Integration Token (starts with 'secret_')",
            "openai_api_key": "OpenAI API Key (starts with 'sk-')",
            "anthropic_api_key": "Anthropic Claude API Key (starts with 'sk-ant-')",
            "huggingface_api_key": "Hugging Face API Token (starts with 'hf_')",
            "supabase_api_key": "Supabase API Key",
            "typeform_api_key": "TypeForm API Key",
            "airtable_api_key": "Airtable API Key",
            "gohighlevel_client_secret": "GoHighLevel OAuth Client Secret",
            "mongodb_password": "MongoDB Database Password",
            "redis_password": "Redis Authentication Password",
            "jwt_secret_key": "JWT Signing Secret Key (min 32 characters)",
            "webhook_secret": "Webhook Validation Secret (min 16 characters)",
            "encryption_key": "Application Encryption Key (min 32 characters)",
        }
        
        return descriptions.get(secret_def.name, secret_def.description or f"{secret_def.name} secret")
    
    def prompt_for_secret(self, secret_def: SecretDefinition) -> Optional[str]:
        """Prompt user for a secret value with validation."""
        description = self.get_secret_description(secret_def)
        required_text = " (REQUIRED)" if secret_def.required else " (Optional)"
        
        print(f"\n📝 {description}{required_text}")
        
        if not secret_def.required:
            skip = input("   Skip this secret? (y/N): ").lower().strip()
            if skip in ['y', 'yes']:
                return None
        
        while True:
            # Use getpass for sensitive values
            if "password" in secret_def.name.lower() or "secret" in secret_def.name.lower():
                secret_value = getpass.getpass("   Enter value (hidden): ").strip()
            else:
                secret_value = input("   Enter value: ").strip()
            
            if not secret_value:
                if secret_def.required:
                    print("   ❌ This secret is required. Please enter a value.")
                    continue
                else:
                    return None
            
            # Validate format
            if self.validate_secret_format(secret_def.name, secret_value):
                print("   ✅ Secret format looks good!")
                return secret_value
            else:
                print("   ⚠️  Secret format may be incorrect. Continue anyway? (y/N): ", end="")
                if input().lower().strip() in ['y', 'yes']:
                    return secret_value
                print("   Please try again...")
    
    def upload_to_vault(self, secret_def: SecretDefinition, secret_value: str) -> bool:
        """Upload secret to Vault."""
        try:
            secret_path = f"{secret_def.category.value}/{secret_def.name}"
            
            self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret={"value": secret_value}
            )
            
            print(f"   ✅ Uploaded to Vault: {secret_path}")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to upload to Vault: {e}")
            return False
    
    def upload_to_env_file(self, secret_def: SecretDefinition, secret_value: str) -> bool:
        """Upload secret to .env file."""
        try:
            env_file = project_root / ".env"
            
            # Read current .env file
            if env_file.exists():
                with open(env_file, 'r') as f:
                    lines = f.readlines()
            else:
                lines = []
            
            # Find and update the line
            env_var_name = secret_def.env_var_name or secret_def.name.upper()
            updated = False
            
            for i, line in enumerate(lines):
                if line.startswith(f"{env_var_name}="):
                    lines[i] = f"{env_var_name}={secret_value}\n"
                    updated = True
                    break
            
            # Add new line if not found
            if not updated:
                lines.append(f"{env_var_name}={secret_value}\n")
            
            # Write back to file
            with open(env_file, 'w') as f:
                f.writelines(lines)
            
            # Set secure permissions
            os.chmod(env_file, 0o600)
            
            print(f"   ✅ Updated .env file: {env_var_name}")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to update .env file: {e}")
            return False
    
    def generate_missing_secrets(self) -> Dict[str, str]:
        """Generate secure values for missing security secrets."""
        generated = {}
        
        security_secrets = [
            ("jwt_secret_key", lambda: Fernet.generate_key().decode()),
            ("webhook_secret", lambda: Fernet.generate_key().decode()[:32]),
            ("encryption_key", lambda: Fernet.generate_key().decode()),
        ]
        
        for secret_name, generator in security_secrets:
            secret_def = next((s for s in self.config.secrets if s.name == secret_name), None)
            if secret_def:
                generated[secret_name] = generator()
                print(f"🔐 Generated secure {secret_name}")
        
        return generated
    
    async def interactive_upload(self, use_vault: bool = True):
        """Run interactive secret upload process."""
        print("🔐 HigherSelf Network Server - Secret Upload Wizard")
        print("=" * 60)
        print(f"Environment: {self.environment}")
        print(f"Backend: {'HashiCorp Vault' if use_vault else 'Environment File'}")
        print()
        
        # Setup backend
        if use_vault:
            vault_addr = input(f"Vault address (http://localhost:8200): ").strip() or "http://localhost:8200"
            if not self.setup_vault_client(vault_addr):
                print("❌ Cannot connect to Vault. Falling back to .env file.")
                use_vault = False
        
        # Categorize secrets
        categories = {}
        for secret_def in self.config.secrets:
            if secret_def.category not in categories:
                categories[secret_def.category] = []
            categories[secret_def.category].append(secret_def)
        
        uploaded_count = 0
        skipped_count = 0
        
        # Process each category
        for category, secrets in categories.items():
            print(f"\n📂 {category.value.upper()} SECRETS")
            print("-" * 40)
            
            for secret_def in secrets:
                secret_value = self.prompt_for_secret(secret_def)
                
                if secret_value is None:
                    print(f"   ⏭️  Skipped {secret_def.name}")
                    skipped_count += 1
                    continue
                
                # Upload to backend
                success = False
                if use_vault:
                    success = self.upload_to_vault(secret_def, secret_value)
                else:
                    success = self.upload_to_env_file(secret_def, secret_value)
                
                if success:
                    uploaded_count += 1
                else:
                    skipped_count += 1
        
        # Generate missing security secrets
        print(f"\n🔐 GENERATING SECURITY SECRETS")
        print("-" * 40)
        
        generated_secrets = self.generate_missing_secrets()
        for secret_name, secret_value in generated_secrets.items():
            secret_def = next((s for s in self.config.secrets if s.name == secret_name), None)
            if secret_def:
                if use_vault:
                    success = self.upload_to_vault(secret_def, secret_value)
                else:
                    success = self.upload_to_env_file(secret_def, secret_value)
                
                if success:
                    uploaded_count += 1
        
        # Summary
        print(f"\n✅ UPLOAD COMPLETE")
        print("=" * 60)
        print(f"Uploaded: {uploaded_count} secrets")
        print(f"Skipped: {skipped_count} secrets")
        print(f"Backend: {'HashiCorp Vault' if use_vault else '.env file'}")
        
        if not use_vault:
            print(f"\n📁 Secrets saved to: {project_root}/.env")
            print("🔒 File permissions set to 600 (owner read/write only)")
        
        print("\n🚀 Next steps:")
        print("1. Test your application with the new secrets")
        print("2. Verify all integrations are working")
        print("3. Consider setting up automatic rotation for production")


@click.command()
@click.option('--environment', '-e', default='development',
              type=click.Choice(['development', 'staging', 'production']),
              help='Environment to upload secrets for')
@click.option('--use-vault/--use-env', default=True,
              help='Use Vault or .env file for storage')
@click.option('--vault-addr', default='http://localhost:8200',
              help='Vault server address')
def main(environment: str, use_vault: bool, vault_addr: str):
    """Interactive secret upload wizard for HigherSelf Network Server."""
    
    uploader = SecretUploader(environment)
    
    try:
        asyncio.run(uploader.interactive_upload(use_vault))
    except KeyboardInterrupt:
        print("\n\n❌ Upload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Upload failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
