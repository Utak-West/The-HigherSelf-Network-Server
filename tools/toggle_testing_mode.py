#!/usr/bin/env python3
"""
Utility to toggle testing mode for The HigherSelf Network Server.

This script provides a simple CLI interface to enable/disable testing mode
during development, which prevents real API calls to external services.
"""

import argparse
import os
import sys

from colorama import Fore, Style, init

# Add parent directory to path to allow importing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.testing_mode import (
    disable_testing_mode,
    enable_testing_mode,
    is_testing_mode,
)

# Initialize colorama for colored terminal output
init()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Toggle testing mode for The HigherSelf Network Server"
    )

    # Define mutually exclusive group for enable/disable
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--enable", action="store_true", help="Enable testing mode (block API calls)"
    )
    group.add_argument(
        "--disable", action="store_true", help="Disable testing mode (allow API calls)"
    )
    group.add_argument(
        "--status", action="store_true", help="Check current testing mode status"
    )

    # Optional APIs to disable
    parser.add_argument(
        "--apis",
        nargs="+",
        help="Specific APIs to disable (used with --enable), e.g. 'notion hubspot'",
    )

    # Parse arguments
    args = parser.parse_args()

    # Check testing mode status
    if args.status:
        if is_testing_mode():
            print(
                f"{Fore.YELLOW}Testing mode is currently {Fore.GREEN}ENABLED{Fore.YELLOW}.{Style.RESET_ALL}"
            )
            print("External API calls are being blocked.")
        else:
            print(
                f"{Fore.YELLOW}Testing mode is currently {Fore.RED}DISABLED{Fore.YELLOW}.{Style.RESET_ALL}"
            )
            print("External API calls are being made normally.")
        return

    # Enable or disable testing mode
    if args.enable:
        api_list = args.apis if args.apis else None
        enable_testing_mode(api_list)

        # Create marker file to persist across runs
        with open(".testing_mode", "w") as f:
            if api_list:
                f.write(",".join(api_list))
            else:
                f.write("all")

        print(
            f"{Fore.GREEN}Testing mode enabled. API calls will be blocked.{Style.RESET_ALL}"
        )
        if api_list:
            print(f"Disabled APIs: {', '.join(api_list)}")
        else:
            print("All APIs are disabled.")

    elif args.disable:
        disable_testing_mode()

        # Remove marker file
        if os.path.exists(".testing_mode"):
            os.remove(".testing_mode")

        print(
            f"{Fore.GREEN}Testing mode disabled. API calls will be made normally.{Style.RESET_ALL}"
        )


if __name__ == "__main__":
    main()
