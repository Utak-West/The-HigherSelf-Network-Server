#!/usr/bin/env python3
"""
Utility script to enable testing mode for The HigherSelf Network Server.

This script allows for easy enabling/disabling of API calls during development
and testing to prevent unintended interactions with third-party services.
"""

import argparse
import os
import sys

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.testing_mode import enable_testing_mode, disable_testing_mode, TestingMode


def main():
    """Parse command line arguments and configure testing mode."""
    parser = argparse.ArgumentParser(
        description="Enable or disable testing mode for The HigherSelf Network Server"
    )
    
    parser.add_argument(
        "--enable", 
        action="store_true",
        help="Enable testing mode (disable all API calls)"
    )
    
    parser.add_argument(
        "--disable", 
        action="store_true",
        help="Disable testing mode (allow all API calls)"
    )
    
    parser.add_argument(
        "--apis", 
        nargs="*",
        help="Specific APIs to disable (default: all). Example: --apis notion openai"
    )
    
    parser.add_argument(
        "--env", 
        action="store_true",
        help="Create or update .env file with TESTING_MODE=1"
    )
    
    args = parser.parse_args()
    
    if args.enable and args.disable:
        print("❌ Error: Cannot both enable and disable testing mode at the same time.")
        sys.exit(1)
    
    if args.enable:
        enable_testing_mode(args.apis)
        print("✅ Testing mode enabled")
        
        if args.env:
            _update_env_file(enabled=True)
            
    elif args.disable:
        disable_testing_mode()
        print("✅ Testing mode disabled")
        
        if args.env:
            _update_env_file(enabled=False)
    else:
        # Just show current status if no flags provided
        status = "ENABLED" if TestingMode.is_testing_mode() else "DISABLED"
        print(f"ℹ️ Testing mode is currently: {status}")
        
        if TestingMode.is_testing_mode():
            print(f"ℹ️ Disabled APIs: {', '.join(sorted(TestingMode._disabled_apis))}")


def _update_env_file(enabled: bool):
    """Update the .env file with testing mode setting."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    if os.path.exists(env_path):
        # Read existing content
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Check if TESTING_MODE is already defined
        testing_mode_exists = False
        for i, line in enumerate(lines):
            if line.startswith('TESTING_MODE='):
                if enabled:
                    lines[i] = 'TESTING_MODE=1\n'
                else:
                    lines[i] = 'TESTING_MODE=0\n'
                testing_mode_exists = True
                break
        
        # Add TESTING_MODE if it doesn't exist
        if not testing_mode_exists and enabled:
            lines.append('TESTING_MODE=1\n')
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.writelines(lines)
    else:
        # Create new .env file
        with open(env_path, 'w') as f:
            if enabled:
                f.write('TESTING_MODE=1\n')
    
    print(f"✅ Updated .env file with TESTING_MODE={'1' if enabled else '0'}")


if __name__ == "__main__":
    main()
