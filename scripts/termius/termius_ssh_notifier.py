#!/usr/bin/env python3
"""
Termius SSH Notifier - Direct terminal notifications via SSH
Sends notifications directly to active SSH sessions in Termius
"""

import asyncio
import json
import os
import subprocess
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import argparse

import paramiko
from rich.console import Console
from rich.panel import Panel

console = Console()

class TermiusSSHNotifier:
    """Send notifications to Termius via SSH connections."""
    
    def __init__(self):
        self.active_sessions = []
        self.notification_file = os.path.expanduser("~/.termius_higherself/active_sessions.json")
        self.load_active_sessions()
    
    def load_active_sessions(self):
        """Load active SSH sessions from file."""
        try:
            if os.path.exists(self.notification_file):
                with open(self.notification_file, 'r') as f:
                    self.active_sessions = json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load active sessions: {e}[/yellow]")
            self.active_sessions = []
    
    def save_active_sessions(self):
        """Save active SSH sessions to file."""
        try:
            os.makedirs(os.path.dirname(self.notification_file), exist_ok=True)
            with open(self.notification_file, 'w') as f:
                json.dump(self.active_sessions, f, indent=2)
        except Exception as e:
            console.print(f"[red]Error saving active sessions: {e}[/red]")
    
    def register_session(self, host: str, username: str, port: int = 22, key_file: Optional[str] = None):
        """Register a new SSH session for notifications."""
        session = {
            "host": host,
            "username": username,
            "port": port,
            "key_file": key_file,
            "registered_at": datetime.now().isoformat(),
            "active": True
        }
        
        # Remove existing session for same host/user
        self.active_sessions = [s for s in self.active_sessions 
                              if not (s["host"] == host and s["username"] == username)]
        
        self.active_sessions.append(session)
        self.save_active_sessions()
        console.print(f"[green]✅ Registered SSH session: {username}@{host}:{port}[/green]")
    
    def send_notification_to_session(self, session: Dict[str, Any], message: str) -> bool:
        """Send notification to a specific SSH session."""
        try:
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect using key or password
            if session.get("key_file"):
                ssh.connect(
                    hostname=session["host"],
                    port=session["port"],
                    username=session["username"],
                    key_filename=session["key_file"],
                    timeout=10
                )
            else:
                # For localhost connections, try without password first
                ssh.connect(
                    hostname=session["host"],
                    port=session["port"],
                    username=session["username"],
                    timeout=10
                )
            
            # Send notification via echo to all terminals
            notification_cmd = f'''
            # Send notification to all terminals for this user
            for tty in $(who | grep {session["username"]} | awk '{{print $2}}'); do
                if [[ "$tty" =~ ^pts/ ]] || [[ "$tty" =~ ^tty ]]; then
                    echo -e "\\n{message}\\n" > /dev/$tty 2>/dev/null || true
                fi
            done
            
            # Also try to send to tmux sessions if available
            if command -v tmux >/dev/null 2>&1; then
                tmux list-sessions 2>/dev/null | while read session_line; do
                    session_name=$(echo "$session_line" | cut -d: -f1)
                    tmux send-keys -t "$session_name" C-m
                    tmux send-keys -t "$session_name" "echo '{message}'" C-m
                done 2>/dev/null || true
            fi
            '''
            
            stdin, stdout, stderr = ssh.exec_command(notification_cmd)
            stdout.read()  # Wait for command to complete
            
            ssh.close()
            return True
            
        except Exception as e:
            console.print(f"[red]Failed to send notification to {session['host']}: {e}[/red]")
            return False
    
    def broadcast_notification(self, message: str, notification_type: str = "info"):
        """Broadcast notification to all active sessions."""
        if not self.active_sessions:
            console.print("[yellow]No active SSH sessions registered[/yellow]")
            return
        
        # Format message with colors and borders
        formatted_message = self.format_notification(message, notification_type)
        
        success_count = 0
        for session in self.active_sessions:
            if session.get("active", True):
                if self.send_notification_to_session(session, formatted_message):
                    success_count += 1
        
        console.print(f"[green]Sent notification to {success_count}/{len(self.active_sessions)} sessions[/green]")
    
    def format_notification(self, message: str, notification_type: str) -> str:
        """Format notification with colors and styling."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color codes for terminal
        colors = {
            "success": "\\033[32m",  # Green
            "failure": "\\033[31m",  # Red
            "warning": "\\033[33m",  # Yellow
            "info": "\\033[34m",     # Blue
            "reset": "\\033[0m"      # Reset
        }
        
        color = colors.get(notification_type, colors["info"])
        reset = colors["reset"]
        
        # Create bordered notification
        border = "=" * 60
        formatted = f"""
{color}{border}{reset}
{color}🔔 HigherSelf Network Server Notification{reset}
{color}{border}{reset}
{message}
{color}Time: {timestamp}{reset}
{color}{border}{reset}
"""
        return formatted
    
    def test_notification(self):
        """Send a test notification to verify the system works."""
        test_message = """
✅ Test notification from HigherSelf Network Server
🔧 Termius SSH integration is working correctly
📡 You will receive real-time GitHub Actions notifications here
"""
        self.broadcast_notification(test_message, "success")
    
    def send_github_actions_notification(self, workflow_data: Dict[str, Any]):
        """Send GitHub Actions workflow notification."""
        status = workflow_data.get("status", "unknown")
        workflow = workflow_data.get("workflow", "Unknown Workflow")
        branch = workflow_data.get("branch", "unknown")
        commit = workflow_data.get("commit_sha", "unknown")[:8]
        actor = workflow_data.get("actor", "unknown")
        
        # Status emoji
        status_emoji = {
            "success": "✅",
            "failure": "❌", 
            "cancelled": "⚠️",
            "in_progress": "🔄"
        }.get(status, "ℹ️")
        
        message = f"""
{status_emoji} GitHub Actions: {workflow}
📊 Status: {status.upper()}
🌿 Branch: {branch}
📝 Commit: {commit}
👤 Actor: {actor}
"""
        
        if workflow_data.get("run_url"):
            message += f"🔗 Details: {workflow_data['run_url']}"
        
        notification_type = "success" if status == "success" else "failure" if status == "failure" else "info"
        self.broadcast_notification(message, notification_type)


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Termius SSH Notifier")
    parser.add_argument("command", choices=["register", "test", "send", "list"], 
                       help="Command to execute")
    parser.add_argument("--host", help="SSH host")
    parser.add_argument("--username", help="SSH username")
    parser.add_argument("--port", type=int, default=22, help="SSH port")
    parser.add_argument("--key-file", help="SSH private key file")
    parser.add_argument("--message", help="Message to send")
    parser.add_argument("--type", default="info", help="Notification type")
    
    args = parser.parse_args()
    
    notifier = TermiusSSHNotifier()
    
    if args.command == "register":
        if not args.host or not args.username:
            console.print("[red]Error: --host and --username required for register[/red]")
            return
        notifier.register_session(args.host, args.username, args.port, args.key_file)
    
    elif args.command == "test":
        notifier.test_notification()
    
    elif args.command == "send":
        if not args.message:
            console.print("[red]Error: --message required for send[/red]")
            return
        notifier.broadcast_notification(args.message, args.type)
    
    elif args.command == "list":
        console.print("[cyan]Active SSH Sessions:[/cyan]")
        for i, session in enumerate(notifier.active_sessions, 1):
            status = "🟢 Active" if session.get("active", True) else "🔴 Inactive"
            console.print(f"{i}. {session['username']}@{session['host']}:{session['port']} - {status}")


if __name__ == "__main__":
    main()
