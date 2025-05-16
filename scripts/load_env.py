#!/usr/bin/env python3
"""
Environment Variables Loader for Higher Self Network Server

This script loads environment variables from the appropriate .env file
based on the current environment (development, testing, production).
It ensures proper environment isolation per server rules.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

def load_environment(environment=None):
    """
    Load the appropriate environment variables file based on the specified environment
    
    Args:
        environment: The environment to load (development, testing, production)
                     If None, tries to determine from ENV or defaults to development
    """
    # Determine environment
    if not environment:
        environment = os.environ.get("ENVIRONMENT", "development")
    
    # Map of environment file paths
    env_files = {
        "development": ".env.development",
        "testing": ".env.testing",
        "production": ".env.production",
        "default": ".env"
    }
    
    # Try environment-specific file first, then fallback to .env
    env_file = env_files.get(environment.lower(), env_files["default"])
    fallback = env_files["default"]
    
    # Check if the environment-specific file exists
    if os.path.exists(env_file):
        print(f"🔄 Loading environment from {env_file}")
        load_dotenv(env_file, override=True)
    elif os.path.exists(fallback):
        print(f"⚠️ {env_file} not found, falling back to {fallback}")
        load_dotenv(fallback, override=True)
    else:
        print(f"❌ No environment file found ({env_file} or {fallback})")
        sys.exit(1)
    
    # Set the ENVIRONMENT variable if not already set
    if not os.environ.get("ENVIRONMENT"):
        os.environ["ENVIRONMENT"] = environment
        print(f"📌 Setting ENVIRONMENT={environment}")
    
    print(f"✅ Environment loaded: {os.environ.get('ENVIRONMENT', 'unknown')}")
    
    # Verify API Keys match the environment for security (prevents using prod keys in dev)
    if environment != "production" and any([
        os.environ.get("STRIPE_API_KEY", "").startswith("sk_live_"),
        "prod" in os.environ.get("MONGODB_CONNECTION_STRING", ""),
        "prod" in os.environ.get("POSTGRES_CONNECTION_STRING", "")
    ]):
        print("⚠️ WARNING: Production API keys detected in non-production environment!")

def main():
    parser = argparse.ArgumentParser(description="Load environment variables for the Higher Self Network Server")
    parser.add_argument("--env", "-e", choices=["development", "testing", "production"],
                        help="Environment to load (development, testing, production)")
    args = parser.parse_args()
    
    load_environment(args.env)

if __name__ == "__main__":
    main()
