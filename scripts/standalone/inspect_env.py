#!/usr/bin/env python
"""
Script to inspect environment variables and their sources.
"""
import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv


def inspect_env_vars():
    """Inspect environment variables related to Notion"""

    # First check what's in the actual environment before loading any files
    print("=== OS Environment Variables (before loading .env files) ===")
    notion_token_env = os.environ.get("NOTION_API_TOKEN")
    print(f"NOTION_API_TOKEN from os.environ: {notion_token_env}")

    # Check specific .env files individually
    env_files = [".env", ".env.mcp", ".env.local", ".env.development"]

    for env_file in env_files:
        if Path(env_file).exists():
            print(f"\n=== Contents of {env_file} ===")
            env_values = dotenv_values(env_file)

            # Print all variables
            for key, value in env_values.items():
                if "NOTION" in key:
                    print(f"{key}: {value}")

            # Specifically check for NOTION_API_TOKEN
            notion_token = env_values.get("NOTION_API_TOKEN")
            if notion_token:
                print(f"NOTION_API_TOKEN from {env_file}: {notion_token}")
                print(f"Length: {len(notion_token) if notion_token else 0}")
            else:
                print(f"NOTION_API_TOKEN not found in {env_file}")
        else:
            print(f"\n{env_file} does not exist")


if __name__ == "__main__":
    inspect_env_vars()
