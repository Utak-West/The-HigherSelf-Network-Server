#!/usr/bin/env python3
"""
HigherSelf Network MCP Setup Verification Script

This script helps verify that MCP servers are properly configured
and ready for AI agent enhancement.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str):
    """Print info message."""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

def check_mcp_config_file() -> bool:
    """Check if MCP configuration file exists and is valid."""
    print_header("Checking MCP Configuration Files")
    
    config_file = Path("mcp-servers-config.json")
    if not config_file.exists():
        print_error("mcp-servers-config.json not found")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        if "augment.advanced" in config and "mcpServers" in config["augment.advanced"]:
            servers = config["augment.advanced"]["mcpServers"]
            print_success(f"Configuration file found with {len(servers)} MCP servers")
            
            for server in servers:
                name = server.get("name", "Unknown")
                command = server.get("command", "Unknown")
                print_info(f"  • {name}: {command}")
            
            return True
        else:
            print_error("Invalid configuration structure")
            return False
            
    except json.JSONDecodeError:
        print_error("Invalid JSON in configuration file")
        return False
    except Exception as e:
        print_error(f"Error reading configuration: {e}")
        return False

def check_environment_setup() -> Dict[str, bool]:
    """Check environment variables and credentials."""
    print_header("Checking Environment Setup")
    
    results = {}
    
    # Check for environment template
    env_template = Path("mcp-environment-template.env")
    if env_template.exists():
        print_success("Environment template file found")
        results["env_template"] = True
    else:
        print_warning("Environment template file not found")
        results["env_template"] = False
    
    # Check for actual environment file
    env_file = Path(".env.mcp")
    if env_file.exists():
        print_success("Environment file (.env.mcp) found")
        results["env_file"] = True
    else:
        print_warning("Environment file (.env.mcp) not found - you'll need to create this")
        results["env_file"] = False
    
    return results

def check_project_structure() -> bool:
    """Check if the HigherSelf Network Server project structure is intact."""
    print_header("Checking Project Structure")
    
    required_items = [
        "agents",
        "api", 
        "config",
        "main.py",
        "requirements.txt",
        "services",
        "models"
    ]
    
    missing_items = []
    found_items = []
    
    for item in required_items:
        if Path(item).exists():
            found_items.append(item)
        else:
            missing_items.append(item)
    
    if found_items:
        print_success(f"Found key project items: {', '.join(found_items)}")
    
    if missing_items:
        print_warning(f"Missing items: {', '.join(missing_items)}")
        return False
    
    print_success("Project structure looks good")
    return True

def check_node_environment() -> bool:
    """Check Node.js environment for MCP servers."""
    print_header("Checking Node.js Environment")
    
    try:
        # Check Node.js
        node_result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if node_result.returncode == 0:
            print_success(f"Node.js: {node_result.stdout.strip()}")
        else:
            print_error("Node.js not found")
            return False
        
        # Check npm
        npm_result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if npm_result.returncode == 0:
            print_success(f"npm: {npm_result.stdout.strip()}")
        else:
            print_error("npm not found")
            return False
        
        # Check npx
        npx_result = subprocess.run(["npx", "--version"], capture_output=True, text=True)
        if npx_result.returncode == 0:
            print_success(f"npx: {npx_result.stdout.strip()}")
            return True
        else:
            print_error("npx not found")
            return False
            
    except FileNotFoundError:
        print_error("Node.js environment not found")
        return False

def show_next_steps(results: Dict[str, bool]):
    """Show next steps based on verification results."""
    print_header("Next Steps")
    
    if all(results.values()):
        print_success("All checks passed! You're ready to configure Augment Code.")
        print_info("Follow these steps:")
        print("  1. Open Augment Code")
        print("  2. Press Cmd/Ctrl + Shift + P")
        print("  3. Type 'Preferences: Open Settings (JSON)'")
        print("  4. Add the MCP server configuration from mcp-servers-config.json")
        print("  5. Set up your Notion integration token")
        print("  6. Restart Augment Code")
        print("  7. Test with queries like 'Show me my Notion databases'")
    else:
        print_warning("Some issues need to be resolved:")
        
        if not results.get("node_env", True):
            print("  • Install Node.js and npm")
        
        if not results.get("config_file", True):
            print("  • Check mcp-servers-config.json file")
        
        if not results.get("env_template", True):
            print("  • Create environment template file")
        
        if not results.get("project_structure", True):
            print("  • Verify project structure")
        
        print_info("Resolve these issues and run the verification again.")

def main():
    """Main verification function."""
    print_header("HigherSelf Network MCP Setup Verification")
    print_info("Verifying MCP server configuration for AI agent enhancement...")
    
    results = {}
    
    # Check Node.js environment
    results["node_env"] = check_node_environment()
    
    # Check MCP configuration
    results["config_file"] = check_mcp_config_file()
    
    # Check environment setup
    env_results = check_environment_setup()
    results.update(env_results)
    
    # Check project structure
    results["project_structure"] = check_project_structure()
    
    # Show summary
    print_header("Verification Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"Checks passed: {Colors.GREEN}{passed}{Colors.END}/{total}")
    
    if passed == total:
        print_success("All verification checks passed! 🎉")
    elif passed >= total * 0.8:
        print_warning("Most checks passed - minor issues to resolve")
    else:
        print_error("Several issues need attention")
    
    # Show next steps
    show_next_steps(results)

if __name__ == "__main__":
    main()
