#!/usr/bin/env python3
"""
HigherSelf Network Server - Simple Secrets Upload Script

A standalone script to upload secrets without complex dependencies.
This script helps you securely upload your API keys and credentials.
"""

import getpass
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import hvac
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False
    print("⚠️  hvac not installed. Vault functionality will be limited.")

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  cryptography not installed. Key generation will be limited.")


class SimpleSecretsUploader:
    """Simple secrets uploader without complex dependencies."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.vault_client: Optional[hvac.Client] = None
        self.project_root = Path(__file__).parent.parent
        
        # Define secrets we need
        self.secrets_config = self._get_secrets_config()
    
    def _get_secrets_config(self) -> List[Tuple[str, str, str, bool]]:
        """Get secrets configuration as (name, env_var, description, required)."""
        return [
            # Core API Keys (Required)
            ("notion_api_token", "NOTION_API_TOKEN", "Notion API Integration Token (starts with 'secret_')", True),
            ("openai_api_key", "OPENAI_API_KEY", "OpenAI API Key (starts with 'sk-')", True),
            ("supabase_api_key", "SUPABASE_API_KEY", "Supabase API Key", True),
            
            # Optional API Keys
            ("anthropic_api_key", "ANTHROPIC_API_KEY", "Anthropic Claude API Key (starts with 'sk-ant-')", False),
            ("huggingface_api_key", "HUGGINGFACE_API_KEY", "Hugging Face API Token (starts with 'hf_')", False),
            ("typeform_api_key", "TYPEFORM_API_KEY", "TypeForm API Key", False),
            ("airtable_api_key", "AIRTABLE_API_KEY", "Airtable API Key", False),
            ("gohighlevel_client_secret", "GOHIGHLEVEL_CLIENT_SECRET", "GoHighLevel OAuth Client Secret", False),
            
            # Database Credentials
            ("mongodb_password", "MONGODB_PASSWORD", "MongoDB Database Password", True),
            ("redis_password", "REDIS_PASSWORD", "Redis Authentication Password (optional)", False),
            
            # Security Keys (will be auto-generated if not provided)
            ("jwt_secret_key", "JWT_SECRET_KEY", "JWT Signing Secret Key (min 32 characters)", True),
            ("webhook_secret", "WEBHOOK_SECRET", "Webhook Validation Secret (min 16 characters)", True),
            ("encryption_key", "ENCRYPTION_KEY", "Application Encryption Key (min 32 characters)", True),
        ]
    
    def validate_secret_format(self, secret_name: str, secret_value: str) -> bool:
        """Validate secret format based on known patterns."""
        if not secret_value or secret_value.startswith("your_"):
            return False
            
        validations = {
            "notion_api_token": lambda v: v.startswith("secret_") and len(v) > 50,
            "openai_api_key": lambda v: v.startswith("sk-") and len(v) > 40,
            "anthropic_api_key": lambda v: v.startswith("sk-ant-") and len(v) > 40,
            "huggingface_api_key": lambda v: v.startswith("hf_") and len(v) > 30,
            "supabase_api_key": lambda v: len(v) > 30,
            "jwt_secret_key": lambda v: len(v) >= 32,
            "webhook_secret": lambda v: len(v) >= 16,
            "encryption_key": lambda v: len(v) >= 32,
        }
        
        validator = validations.get(secret_name)
        if validator:
            return validator(secret_value)
        
        # Generic validation - not empty and not placeholder
        return len(secret_value) > 0
    
    def generate_secure_key(self, length: int = 32) -> str:
        """Generate a secure random key."""
        if CRYPTO_AVAILABLE:
            return Fernet.generate_key().decode()
        else:
            # Fallback to os.urandom
            import base64
            return base64.urlsafe_b64encode(os.urandom(length)).decode()[:length]
    
    def setup_vault_client(self, vault_addr: str = "http://localhost:8200") -> bool:
        """Setup Vault client connection."""
        if not VAULT_AVAILABLE:
            print("❌ Vault not available (hvac not installed)")
            return False
            
        try:
            self.vault_client = hvac.Client(url=vault_addr)
            
            # Try to get token from environment or use default
            vault_token = os.getenv("VAULT_TOKEN", "dev-root-token")
            self.vault_client.token = vault_token
            
            if not self.vault_client.is_authenticated():
                print("❌ Vault authentication failed")
                return False
            
            print(f"✅ Connected to Vault at {vault_addr}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Vault: {e}")
            return False
    
    def prompt_for_secret(self, name: str, env_var: str, description: str, required: bool) -> Optional[str]:
        """Prompt user for a secret value."""
        required_text = " (REQUIRED)" if required else " (Optional)"
        print(f"\n📝 {description}{required_text}")
        
        if not required:
            skip = input("   Skip this secret? (y/N): ").lower().strip()
            if skip in ['y', 'yes']:
                return None
        
        while True:
            # Use getpass for sensitive values
            if any(word in name.lower() for word in ['password', 'secret', 'key']):
                secret_value = getpass.getpass("   Enter value (hidden): ").strip()
            else:
                secret_value = input("   Enter value: ").strip()
            
            if not secret_value:
                if required:
                    print("   ❌ This secret is required. Please enter a value.")
                    continue
                else:
                    return None
            
            # Validate format
            if self.validate_secret_format(name, secret_value):
                print("   ✅ Secret format looks good!")
                return secret_value
            else:
                print("   ⚠️  Secret format may be incorrect. Continue anyway? (y/N): ", end="")
                if input().lower().strip() in ['y', 'yes']:
                    return secret_value
                print("   Please try again...")
    
    def upload_to_vault(self, name: str, secret_value: str) -> bool:
        """Upload secret to Vault."""
        if not self.vault_client:
            return False
            
        try:
            # Determine category based on secret name
            if "api" in name or name in ["notion_api_token", "openai_api_key", "anthropic_api_key", "huggingface_api_key"]:
                category = "api_keys"
            elif "password" in name or name in ["mongodb_password", "redis_password"]:
                category = "database"
            elif name in ["jwt_secret_key"]:
                category = "jwt"
            elif name in ["webhook_secret"]:
                category = "webhooks"
            elif name in ["encryption_key"]:
                category = "encryption"
            else:
                category = "api_keys"  # default
            
            secret_path = f"{category}/{name}"
            
            self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret={"value": secret_value}
            )
            
            print(f"   ✅ Uploaded to Vault: {secret_path}")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to upload to Vault: {e}")
            return False
    
    def upload_to_env_file(self, env_var: str, secret_value: str) -> bool:
        """Upload secret to .env file."""
        try:
            env_file = self.project_root / ".env"
            
            # Read current .env file
            if env_file.exists():
                with open(env_file, 'r') as f:
                    lines = f.readlines()
            else:
                lines = []
            
            # Find and update the line
            updated = False
            for i, line in enumerate(lines):
                if line.startswith(f"{env_var}="):
                    lines[i] = f"{env_var}={secret_value}\n"
                    updated = True
                    break
            
            # Add new line if not found
            if not updated:
                lines.append(f"{env_var}={secret_value}\n")
            
            # Write back to file
            with open(env_file, 'w') as f:
                f.writelines(lines)
            
            # Set secure permissions
            os.chmod(env_file, 0o600)
            
            print(f"   ✅ Updated .env file: {env_var}")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to update .env file: {e}")
            return False
    
    def run_interactive_upload(self):
        """Run interactive secret upload process."""
        print("🔐 HigherSelf Network Server - Simple Secret Upload")
        print("=" * 60)
        print(f"Environment: {self.environment}")
        print()
        
        # Ask about backend preference
        use_vault = False
        if VAULT_AVAILABLE:
            vault_choice = input("Use HashiCorp Vault for secrets? (y/N): ").lower().strip()
            if vault_choice in ['y', 'yes']:
                vault_addr = input("Vault address (http://localhost:8200): ").strip() or "http://localhost:8200"
                use_vault = self.setup_vault_client(vault_addr)
                
                if not use_vault:
                    print("❌ Cannot connect to Vault. Falling back to .env file.")
        
        if not use_vault:
            print("📁 Using .env file for secrets storage")
        
        print("\n🚀 Starting secret collection...")
        
        uploaded_count = 0
        skipped_count = 0
        generated_count = 0
        
        # Collect secrets
        collected_secrets = {}
        
        for name, env_var, description, required in self.secrets_config:
            secret_value = self.prompt_for_secret(name, env_var, description, required)
            
            if secret_value is None:
                print(f"   ⏭️  Skipped {name}")
                skipped_count += 1
                continue
            
            collected_secrets[name] = (env_var, secret_value)
        
        # Generate missing security keys
        print(f"\n🔐 GENERATING MISSING SECURITY KEYS")
        print("-" * 40)
        
        security_keys = ["jwt_secret_key", "webhook_secret", "encryption_key"]
        for key_name in security_keys:
            if key_name not in collected_secrets:
                env_var = next((env for name, env, _, _ in self.secrets_config if name == key_name), key_name.upper())
                generated_key = self.generate_secure_key()
                collected_secrets[key_name] = (env_var, generated_key)
                print(f"🔑 Generated {key_name}")
                generated_count += 1
        
        # Upload all collected secrets
        print(f"\n📤 UPLOADING SECRETS")
        print("-" * 40)
        
        for name, (env_var, secret_value) in collected_secrets.items():
            success = False
            if use_vault:
                success = self.upload_to_vault(name, secret_value)
            else:
                success = self.upload_to_env_file(env_var, secret_value)
            
            if success:
                uploaded_count += 1
            else:
                skipped_count += 1
        
        # Summary
        print(f"\n✅ UPLOAD COMPLETE")
        print("=" * 60)
        print(f"Uploaded: {uploaded_count} secrets")
        print(f"Generated: {generated_count} security keys")
        print(f"Skipped: {skipped_count} secrets")
        print(f"Backend: {'HashiCorp Vault' if use_vault else '.env file'}")
        
        if not use_vault:
            print(f"\n📁 Secrets saved to: {self.project_root}/.env")
            print("🔒 File permissions set to 600 (owner read/write only)")
        
        print("\n🚀 Next steps:")
        print("1. Test your application with: python3 main.py")
        print("2. Verify all integrations are working")
        print("3. Consider setting up Vault for production")


def main():
    """Main function."""
    print("🔐 HigherSelf Network Server - Simple Secrets Upload")
    
    # Get environment
    environment = input("Environment (development/staging/production) [development]: ").strip() or "development"
    
    if environment not in ["development", "staging", "production"]:
        print("❌ Invalid environment. Using 'development'.")
        environment = "development"
    
    uploader = SimpleSecretsUploader(environment)
    
    try:
        uploader.run_interactive_upload()
    except KeyboardInterrupt:
        print("\n\n❌ Upload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Upload failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
