#!/usr/bin/env python3
"""
Build Status Monitor for HigherSelf Network Server
Real-time GitHub Actions workflow monitoring in Termius terminals
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import argparse

import aiohttp
import requests
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class GitHubActionsMonitor:
    """Monitor GitHub Actions workflows and display status in terminal."""
    
    def __init__(self, github_token: str, repo_owner: str, repo_name: str):
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
    async def get_workflow_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflow runs from GitHub API."""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs"
        params = {"per_page": limit, "page": 1}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("workflow_runs", [])
                    else:
                        console.print(f"[red]Error fetching workflow runs: {response.status}[/red]")
                        return []
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return []
    
    async def get_workflow_jobs(self, run_id: int) -> List[Dict[str, Any]]:
        """Get jobs for a specific workflow run."""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}/jobs"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("jobs", [])
                    else:
                        return []
        except Exception as e:
            console.print(f"[red]Error fetching jobs: {e}[/red]")
            return []
    
    def format_duration(self, start_time: str, end_time: Optional[str] = None) -> str:
        """Format duration between start and end time."""
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if end_time:
                end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            else:
                end = datetime.now(start.tzinfo)
            
            duration = end - start
            total_seconds = int(duration.total_seconds())
            
            if total_seconds < 60:
                return f"{total_seconds}s"
            elif total_seconds < 3600:
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                return f"{minutes}m {seconds}s"
            else:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                return f"{hours}h {minutes}m"
        except Exception:
            return "Unknown"
    
    def get_status_emoji(self, status: str, conclusion: Optional[str] = None) -> str:
        """Get emoji for workflow status."""
        if status == "in_progress":
            return "🔄"
        elif status == "queued":
            return "⏳"
        elif status == "completed":
            if conclusion == "success":
                return "✅"
            elif conclusion == "failure":
                return "❌"
            elif conclusion == "cancelled":
                return "⚠️"
            elif conclusion == "skipped":
                return "⏭️"
            else:
                return "❓"
        else:
            return "❓"
    
    def get_status_color(self, status: str, conclusion: Optional[str] = None) -> str:
        """Get color for workflow status."""
        if status == "in_progress":
            return "blue"
        elif status == "queued":
            return "yellow"
        elif status == "completed":
            if conclusion == "success":
                return "green"
            elif conclusion == "failure":
                return "red"
            elif conclusion == "cancelled":
                return "yellow"
            elif conclusion == "skipped":
                return "dim"
            else:
                return "white"
        else:
            return "white"
    
    def create_workflow_table(self, runs: List[Dict[str, Any]]) -> Table:
        """Create a table showing workflow runs."""
        table = Table(title="GitHub Actions - Workflow Runs", show_header=True, header_style="bold magenta")
        
        table.add_column("Status", style="white", width=8)
        table.add_column("Workflow", style="cyan", width=25)
        table.add_column("Branch", style="green", width=15)
        table.add_column("Commit", style="yellow", width=10)
        table.add_column("Actor", style="blue", width=12)
        table.add_column("Duration", style="white", width=10)
        table.add_column("Started", style="dim", width=12)
        
        for run in runs[:10]:  # Show only top 10
            status_emoji = self.get_status_emoji(run["status"], run.get("conclusion"))
            status_color = self.get_status_color(run["status"], run.get("conclusion"))
            
            workflow_name = run["name"][:23] + "..." if len(run["name"]) > 25 else run["name"]
            branch = run["head_branch"][:13] + "..." if len(run["head_branch"]) > 15 else run["head_branch"]
            commit = run["head_sha"][:8]
            actor = run["actor"]["login"][:10] + "..." if len(run["actor"]["login"]) > 12 else run["actor"]["login"]
            
            duration = self.format_duration(run["created_at"], run.get("updated_at"))
            started = datetime.fromisoformat(run["created_at"].replace('Z', '+00:00')).strftime("%H:%M:%S")
            
            table.add_row(
                f"[{status_color}]{status_emoji}[/{status_color}]",
                workflow_name,
                branch,
                commit,
                actor,
                duration,
                started
            )
        
        return table
    
    async def create_jobs_table(self, run_id: int, workflow_name: str) -> Table:
        """Create a table showing jobs for a specific workflow run."""
        jobs = await self.get_workflow_jobs(run_id)
        
        table = Table(title=f"Jobs - {workflow_name}", show_header=True, header_style="bold cyan")
        
        table.add_column("Status", style="white", width=8)
        table.add_column("Job Name", style="cyan", width=30)
        table.add_column("Duration", style="white", width=10)
        table.add_column("Started", style="dim", width=12)
        
        for job in jobs:
            status_emoji = self.get_status_emoji(job["status"], job.get("conclusion"))
            status_color = self.get_status_color(job["status"], job.get("conclusion"))
            
            job_name = job["name"][:28] + "..." if len(job["name"]) > 30 else job["name"]
            duration = self.format_duration(job["started_at"], job.get("completed_at"))
            started = datetime.fromisoformat(job["started_at"].replace('Z', '+00:00')).strftime("%H:%M:%S")
            
            table.add_row(
                f"[{status_color}]{status_emoji}[/{status_color}]",
                job_name,
                duration,
                started
            )
        
        return table
    
    async def monitor_workflows(self, refresh_interval: int = 30):
        """Monitor workflows with live updates."""
        console.print("[bold green]Starting GitHub Actions Monitor for HigherSelf Network Server[/bold green]")
        console.print(f"Repository: {self.repo_owner}/{self.repo_name}")
        console.print(f"Refresh interval: {refresh_interval} seconds")
        console.print("Press Ctrl+C to stop monitoring\n")
        
        try:
            while True:
                # Clear screen and show header
                console.clear()
                console.print(Panel.fit(
                    f"[bold cyan]HigherSelf Network Server - GitHub Actions Monitor[/bold cyan]\n"
                    f"Repository: {self.repo_owner}/{self.repo_name}\n"
                    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    border_style="blue"
                ))
                
                # Get and display workflow runs
                runs = await self.get_workflow_runs()
                if runs:
                    table = self.create_workflow_table(runs)
                    console.print(table)
                    
                    # Show detailed view of the most recent run if it's in progress
                    latest_run = runs[0]
                    if latest_run["status"] == "in_progress":
                        console.print("\n")
                        jobs_table = await self.create_jobs_table(latest_run["id"], latest_run["name"])
                        console.print(jobs_table)
                else:
                    console.print("[yellow]No workflow runs found[/yellow]")
                
                # Wait for next refresh
                await asyncio.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped by user[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error during monitoring: {e}[/red]")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="GitHub Actions Build Status Monitor")
    parser.add_argument("--token", help="GitHub personal access token", 
                       default=os.getenv("GITHUB_TOKEN"))
    parser.add_argument("--owner", help="Repository owner", 
                       default=os.getenv("GITHUB_REPO_OWNER", "Utak-West"))
    parser.add_argument("--repo", help="Repository name", 
                       default=os.getenv("GITHUB_REPO_NAME", "The-HigherSelf-Network-Server"))
    parser.add_argument("--interval", type=int, help="Refresh interval in seconds", 
                       default=30)
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    if not args.token:
        console.print("[red]Error: GitHub token is required. Set GITHUB_TOKEN environment variable or use --token[/red]")
        sys.exit(1)
    
    monitor = GitHubActionsMonitor(args.token, args.owner, args.repo)
    
    if args.once:
        # Run once and exit
        async def run_once():
            runs = await monitor.get_workflow_runs()
            if runs:
                table = monitor.create_workflow_table(runs)
                console.print(table)
            else:
                console.print("[yellow]No workflow runs found[/yellow]")
        
        asyncio.run(run_once())
    else:
        # Continuous monitoring
        asyncio.run(monitor.monitor_workflows(args.interval))


if __name__ == "__main__":
    main()
