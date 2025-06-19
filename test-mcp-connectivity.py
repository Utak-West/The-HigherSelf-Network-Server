#!/usr/bin/env python3
"""
HigherSelf Network MCP Server Connectivity Test

This script tests the connectivity and functionality of MCP servers
configured for the HigherSelf Network ecosystem.
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
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
    WHITE = '\033[97m'
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

def test_package_availability(package_name: str) -> bool:
    """Test if an npm package is available."""
    try:
        result = subprocess.run(
            ["npx", "-y", package_name, "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return False

def test_environment_variables() -> Dict[str, bool]:
    """Test if required environment variables are set."""
    print_header("Testing Environment Variables")
    
    required_vars = {
        "NOTION_TOKEN": "Notion integration token",
        "GITHUB_PERSONAL_ACCESS_TOKEN": "GitHub personal access token",
        "BRAVE_API_KEY": "Brave Search API key (optional)"
    }
    
    results = {}
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value and value != f"your_{var_name.lower()}_here":
            print_success(f"{description}: Set")
            results[var_name] = True
        else:
            if var_name == "BRAVE_API_KEY":
                print_warning(f"{description}: Not set (optional)")
                results[var_name] = False
            else:
                print_error(f"{description}: Not set or using placeholder")
                results[var_name] = False
    
    return results

def test_mcp_packages() -> Dict[str, bool]:
    """Test MCP package availability."""
    print_header("Testing MCP Package Availability")
    
    packages = {
        "@modelcontextprotocol/server-notion": "Notion MCP Server",
        "@modelcontextprotocol/server-github": "GitHub MCP Server",
        "@modelcontextprotocol/server-brave-search": "Brave Search MCP Server",
        "@modelcontextprotocol/server-filesystem": "File System MCP Server",
        "@modelcontextprotocol/server-postgres": "PostgreSQL MCP Server"
    }
    
    results = {}
    
    for package, description in packages.items():
        print_info(f"Testing {description}...")
        if test_package_availability(package):
            print_success(f"{description}: Available")
            results[package] = True
        else:
            print_error(f"{description}: Not available or failed to load")
            results[package] = False
    
    return results

def test_file_system_access() -> bool:
    """Test file system access for the HigherSelf Network Server directory."""
    print_header("Testing File System Access")
    
    server_path = Path("/Users/utakwest/Documents/HigherSelf/The HigherSelf Network /The HigherSelf Network Server")
    
    if server_path.exists():
        print_success(f"HigherSelf Network Server directory exists: {server_path}")
        
        # Test read access
        try:
            files = list(server_path.iterdir())
            print_success(f"Directory is readable ({len(files)} items found)")
            
            # Show some key files/directories
            key_items = ["agents", "api", "config", "main.py", "requirements.txt"]
            found_items = []
            
            for item in key_items:
                if (server_path / item).exists():
                    found_items.append(item)
            
            if found_items:
                print_success(f"Key items found: {', '.join(found_items)}")
            
            return True
            
        except PermissionError:
            print_error("Directory exists but is not readable")
            return False
    else:
        print_error(f"HigherSelf Network Server directory not found: {server_path}")
        return False

def test_nodejs_environment() -> bool:
    """Test Node.js and npm environment."""
    print_header("Testing Node.js Environment")
    
    try:
        # Test Node.js
        node_result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if node_result.returncode == 0:
            print_success(f"Node.js: {node_result.stdout.strip()}")
        else:
            print_error("Node.js not found")
            return False
        
        # Test npm
        npm_result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if npm_result.returncode == 0:
            print_success(f"npm: {npm_result.stdout.strip()}")
        else:
            print_error("npm not found")
            return False
        
        # Test npx
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

def generate_test_report(results: Dict[str, Dict[str, bool]]) -> None:
    """Generate a comprehensive test report."""
    print_header("MCP Server Connectivity Test Report")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print_info(f"Test completed at: {timestamp}")
    
    total_tests = 0
    passed_tests = 0
    
    for category, tests in results.items():
        print(f"\n{Colors.BOLD}{Colors.PURPLE}{category}:{Colors.END}")
        for test_name, passed in tests.items():
            total_tests += 1
            if passed:
                passed_tests += 1
                print_success(f"  {test_name}")
            else:
                print_error(f"  {test_name}")
    
    print(f"\n{Colors.BOLD}Summary:{Colors.END}")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {Colors.GREEN}{passed_tests}{Colors.END}")
    print(f"  Failed: {Colors.RED}{total_tests - passed_tests}{Colors.END}")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    if success_rate >= 80:
        print_success(f"Overall success rate: {success_rate:.1f}% - Ready for AI agent enhancement!")
    elif success_rate >= 60:
        print_warning(f"Overall success rate: {success_rate:.1f}% - Some issues need attention")
    else:
        print_error(f"Overall success rate: {success_rate:.1f}% - Significant issues need resolution")

def main():
    """Main test function."""
    print_header("HigherSelf Network MCP Server Connectivity Test")
    print_info("Testing MCP server setup for AI agent enhancement...")
    
    results = {}
    
    # Test Node.js environment
    nodejs_ok = test_nodejs_environment()
    results["Node.js Environment"] = {"Node.js/npm/npx": nodejs_ok}
    
    if not nodejs_ok:
        print_error("Node.js environment issues detected. Please install Node.js first.")
        return
    
    # Test environment variables
    env_results = test_environment_variables()
    results["Environment Variables"] = env_results
    
    # Test MCP packages
    package_results = test_mcp_packages()
    results["MCP Packages"] = package_results
    
    # Test file system access
    fs_ok = test_file_system_access()
    results["File System"] = {"HigherSelf Server Directory": fs_ok}
    
    # Generate report
    generate_test_report(results)
    
    # Next steps
    print_header("Next Steps")
    
    critical_failures = []
    if not env_results.get("NOTION_TOKEN", False):
        critical_failures.append("Set up Notion integration token")
    if not env_results.get("GITHUB_PERSONAL_ACCESS_TOKEN", False):
        critical_failures.append("Set up GitHub personal access token")
    if not fs_ok:
        critical_failures.append("Fix file system access issues")
    
    if critical_failures:
        print_error("Critical issues that need resolution:")
        for issue in critical_failures:
            print(f"  • {issue}")
        print_info("Please resolve these issues before proceeding with AI agent enhancement.")
    else:
        print_success("Core MCP servers are ready!")
        print_info("You can now proceed with implementing the three high-impact projects:")
        print("  1. Real-Time AI Agent Contact Processing Pipeline")
        print("  2. Multi-Entity Intelligent Workflow Expansion")
        print("  3. Bidirectional Notion Intelligence Hub")

if __name__ == "__main__":
    main()
