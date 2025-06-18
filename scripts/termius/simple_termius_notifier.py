#!/usr/bin/env python3
"""
Simple Termius Notifier - File-based notifications for Termius
Creates notification files that can be monitored by Termius terminals
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
import argparse
from rich.console import Console
from rich.panel import Panel

console = Console()

class SimpleTermiusNotifier:
    """Simple file-based notification system for Termius."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".termius_higherself"
        self.notifications_dir = self.config_dir / "notifications"
        self.notifications_dir.mkdir(parents=True, exist_ok=True)
        
        # Create notification files
        self.notification_file = self.notifications_dir / "latest.json"
        self.history_file = self.notifications_dir / "history.json"
        self.display_file = self.notifications_dir / "display.txt"
    
    def send_notification(self, message: str, notification_type: str = "info", title: str = "HigherSelf Network Server"):
        """Send a notification by writing to files."""
        timestamp = datetime.now()
        
        notification = {
            "id": int(timestamp.timestamp() * 1000),
            "title": title,
            "message": message,
            "type": notification_type,
            "timestamp": timestamp.isoformat(),
            "formatted_time": timestamp.strftime("%H:%M:%S")
        }
        
        # Write latest notification
        with open(self.notification_file, 'w') as f:
            json.dump(notification, f, indent=2)
        
        # Append to history
        history = self.load_history()
        history.append(notification)
        # Keep only last 50 notifications
        history = history[-50:]
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        # Create formatted display
        formatted = self.format_notification(notification)
        with open(self.display_file, 'w') as f:
            f.write(formatted)
        
        console.print(f"[green]✅ Notification sent: {title}[/green]")
        console.print(Panel(message, title=f"[{notification_type.upper()}] {title}"))
        
        return notification
    
    def format_notification(self, notification: dict) -> str:
        """Format notification for terminal display."""
        type_emoji = {
            "success": "✅",
            "failure": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "deployment": "🚀",
            "security": "🔒"
        }
        
        emoji = type_emoji.get(notification["type"], "📢")
        
        formatted = f"""
╔══════════════════════════════════════════════════════════════╗
║  {emoji} {notification['title']:<54} ║
╚══════════════════════════════════════════════════════════════╝

{notification['message']}

Time: {notification['formatted_time']}
Type: {notification['type'].upper()}
ID: {notification['id']}

╚══════════════════════════════════════════════════════════════╝
"""
        return formatted
    
    def load_history(self) -> list:
        """Load notification history."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load history: {e}[/yellow]")
        return []
    
    def get_latest_notification(self) -> dict:
        """Get the latest notification."""
        try:
            if self.notification_file.exists():
                with open(self.notification_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load latest notification: {e}[/yellow]")
        return {}
    
    def show_history(self, limit: int = 10):
        """Show notification history."""
        history = self.load_history()
        
        if not history:
            console.print("[yellow]No notifications in history[/yellow]")
            return
        
        console.print(f"[cyan]Last {min(limit, len(history))} notifications:[/cyan]")
        
        for notification in history[-limit:]:
            type_emoji = {
                "success": "✅",
                "failure": "❌", 
                "warning": "⚠️",
                "info": "ℹ️"
            }
            emoji = type_emoji.get(notification["type"], "📢")
            
            console.print(f"{emoji} [{notification['formatted_time']}] {notification['title']}")
            console.print(f"   {notification['message'][:80]}...")
            console.print()
    
    def send_github_actions_notification(self, workflow_data: dict):
        """Send GitHub Actions specific notification."""
        status = workflow_data.get("status", "unknown")
        workflow = workflow_data.get("workflow", "Unknown Workflow")
        branch = workflow_data.get("branch", "unknown")
        commit = workflow_data.get("commit_sha", "unknown")[:8]
        actor = workflow_data.get("actor", "unknown")
        
        # Determine notification type and emoji
        if status == "success":
            notification_type = "success"
            status_text = "✅ SUCCESS"
        elif status == "failure":
            notification_type = "failure"
            status_text = "❌ FAILED"
        elif status == "cancelled":
            notification_type = "warning"
            status_text = "⚠️ CANCELLED"
        else:
            notification_type = "info"
            status_text = "🔄 IN PROGRESS"
        
        message = f"""GitHub Actions Workflow: {workflow}

Status: {status_text}
Branch: {branch}
Commit: {commit}
Actor: {actor}"""
        
        if workflow_data.get("run_url"):
            message += f"\n\nView Details: {workflow_data['run_url']}"
        
        return self.send_notification(
            message=message,
            notification_type=notification_type,
            title="GitHub Actions Update"
        )
    
    def test_notification(self):
        """Send a test notification."""
        test_message = """🧪 Test notification from HigherSelf Network Server

✅ Termius integration is working correctly
📡 You will receive real-time GitHub Actions notifications
🔔 Build status, deployments, and security alerts
🚀 Ready for development workflow monitoring!"""
        
        return self.send_notification(
            message=test_message,
            notification_type="success",
            title="Termius Integration Test"
        )
    
    def create_monitor_script(self):
        """Create a script to monitor notifications in Termius."""
        monitor_script = self.config_dir / "scripts" / "monitor_notifications.sh"
        monitor_script.parent.mkdir(parents=True, exist_ok=True)
        
        script_content = f'''#!/bin/bash
# Termius Notification Monitor
# Run this script in Termius to see real-time notifications

NOTIFICATION_FILE="{self.display_file}"
LAST_MODIFIED=""

echo "🔔 HigherSelf Network Server - Notification Monitor"
echo "Watching for notifications... (Press Ctrl+C to stop)"
echo ""

while true; do
    if [ -f "$NOTIFICATION_FILE" ]; then
        CURRENT_MODIFIED=$(stat -f "%m" "$NOTIFICATION_FILE" 2>/dev/null || stat -c "%Y" "$NOTIFICATION_FILE" 2>/dev/null)
        
        if [ "$CURRENT_MODIFIED" != "$LAST_MODIFIED" ]; then
            clear
            echo "🔔 HigherSelf Network Server - Notification Monitor"
            echo "Last updated: $(date)"
            echo ""
            cat "$NOTIFICATION_FILE"
            LAST_MODIFIED="$CURRENT_MODIFIED"
        fi
    fi
    
    sleep 2
done
'''
        
        with open(monitor_script, 'w') as f:
            f.write(script_content)
        
        monitor_script.chmod(0o755)
        console.print(f"[green]✅ Monitor script created: {monitor_script}[/green]")
        return monitor_script


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Simple Termius Notifier")
    parser.add_argument("command", choices=["send", "test", "history", "monitor", "github"], 
                       help="Command to execute")
    parser.add_argument("--message", help="Message to send")
    parser.add_argument("--type", default="info", help="Notification type")
    parser.add_argument("--title", default="HigherSelf Network Server", help="Notification title")
    parser.add_argument("--limit", type=int, default=10, help="History limit")
    
    # GitHub Actions specific arguments
    parser.add_argument("--status", help="GitHub Actions status")
    parser.add_argument("--workflow", help="Workflow name")
    parser.add_argument("--branch", help="Branch name")
    parser.add_argument("--commit", help="Commit SHA")
    parser.add_argument("--actor", help="GitHub actor")
    parser.add_argument("--url", help="GitHub Actions run URL")
    
    args = parser.parse_args()
    
    notifier = SimpleTermiusNotifier()
    
    if args.command == "send":
        if not args.message:
            console.print("[red]Error: --message required for send[/red]")
            return
        notifier.send_notification(args.message, args.type, args.title)
    
    elif args.command == "test":
        notifier.test_notification()
    
    elif args.command == "history":
        notifier.show_history(args.limit)
    
    elif args.command == "monitor":
        monitor_script = notifier.create_monitor_script()
        console.print(f"[cyan]Run this in Termius to monitor notifications:[/cyan]")
        console.print(f"[white]{monitor_script}[/white]")
    
    elif args.command == "github":
        workflow_data = {
            "status": args.status or "success",
            "workflow": args.workflow or "Test Workflow",
            "branch": args.branch or "main",
            "commit_sha": args.commit or "abc12345",
            "actor": args.actor or "Developer",
            "run_url": args.url
        }
        notifier.send_github_actions_notification(workflow_data)


if __name__ == "__main__":
    main()
