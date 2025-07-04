"""
Voice-Activated Server Control Service for The HigherSelf Network Server.

This service provides voice command processing for server management operations
including start, stop, restart, status checks, and log viewing through Termius integration.
"""

import asyncio
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from pydantic import BaseModel, Field

from services.aqua_voice_service import AquaVoiceService, VoiceCommandRequest
from services.ai_router import AIRouter


class ServerControlCommand(BaseModel):
    """Server control command model."""
    
    command: str = Field(..., description="The server control command")
    action: str = Field(..., description="The action to perform (start, stop, restart, status, logs)")
    environment: str = Field(default="development", description="Target environment")
    confirmation_required: bool = Field(default=False, description="Whether confirmation is required")


class VoiceServerControlService:
    """Service for voice-activated server control operations."""

    def __init__(self, voice_service: AquaVoiceService):
        """
        Initialize the voice server control service.

        Args:
            voice_service: Aqua voice service instance
        """
        self.voice_service = voice_service
        self.project_root = os.getenv("PYTHONPATH", os.getcwd())
        self.docker_compose_file = os.getenv("DOCKER_COMPOSE_FILE", "docker-compose.yml")
        self.onepassword_enabled = os.getenv("ONEPASSWORD_INTEGRATION", "false").lower() == "true"
        
        # Voice command mappings
        self.command_mappings = {
            "start higher self server": "start",
            "start the server": "start",
            "start server": "start",
            "boot up server": "start",
            "launch server": "start",
            
            "stop higher self server": "stop",
            "stop the server": "stop",
            "stop server": "stop",
            "shutdown server": "stop",
            "halt server": "stop",
            
            "restart higher self server": "restart",
            "restart the server": "restart",
            "restart server": "restart",
            "reboot server": "restart",
            "reload server": "restart",
            
            "server status": "status",
            "check server status": "status",
            "server health": "status",
            "is server running": "status",
            "server info": "status",
            
            "show server logs": "logs",
            "server logs": "logs",
            "view logs": "logs",
            "check logs": "logs",
            "tail logs": "logs",
            
            "deploy server": "deploy",
            "deploy to production": "deploy",
            "start deployment": "deploy",
            
            "run tests": "test",
            "execute tests": "test",
            "test server": "test",
            
            "build server": "build",
            "build docker images": "build",
            "rebuild server": "build"
        }

    async def process_voice_command(self, voice_text: str) -> Dict[str, Any]:
        """
        Process a voice command for server control.

        Args:
            voice_text: Transcribed voice command text

        Returns:
            Dictionary with command processing results
        """
        try:
            # Normalize the voice text
            normalized_text = voice_text.lower().strip()
            
            # Find matching command
            action = self._find_matching_action(normalized_text)
            
            if not action:
                return {
                    "success": False,
                    "error": f"Unknown server command: {voice_text}",
                    "available_commands": list(self.command_mappings.keys())
                }

            # Create server control command
            command = ServerControlCommand(
                command=voice_text,
                action=action,
                environment=self._extract_environment(normalized_text),
                confirmation_required=action in ["stop", "restart", "deploy"]
            )

            # Execute the command
            result = await self._execute_server_command(command)
            
            return {
                "success": True,
                "action": action,
                "command": voice_text,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error processing voice command '{voice_text}': {e}")
            return {
                "success": False,
                "error": str(e),
                "command": voice_text
            }

    def _find_matching_action(self, normalized_text: str) -> Optional[str]:
        """
        Find the matching action for the normalized voice text.

        Args:
            normalized_text: Normalized voice command text

        Returns:
            Matching action or None if not found
        """
        # Direct mapping lookup
        if normalized_text in self.command_mappings:
            return self.command_mappings[normalized_text]
        
        # Partial matching for more flexible voice recognition
        for command_phrase, action in self.command_mappings.items():
            if command_phrase in normalized_text or normalized_text in command_phrase:
                return action
        
        # Keyword-based matching
        if any(word in normalized_text for word in ["start", "launch", "boot", "run"]):
            return "start"
        elif any(word in normalized_text for word in ["stop", "shutdown", "halt", "kill"]):
            return "stop"
        elif any(word in normalized_text for word in ["restart", "reboot", "reload"]):
            return "restart"
        elif any(word in normalized_text for word in ["status", "health", "check", "running"]):
            return "status"
        elif any(word in normalized_text for word in ["logs", "log", "tail", "view"]):
            return "logs"
        elif any(word in normalized_text for word in ["deploy", "deployment"]):
            return "deploy"
        elif any(word in normalized_text for word in ["test", "testing"]):
            return "test"
        elif any(word in normalized_text for word in ["build", "rebuild"]):
            return "build"
        
        return None

    def _extract_environment(self, normalized_text: str) -> str:
        """
        Extract the target environment from the voice command.

        Args:
            normalized_text: Normalized voice command text

        Returns:
            Target environment (development, staging, production)
        """
        if any(word in normalized_text for word in ["production", "prod", "live"]):
            return "production"
        elif any(word in normalized_text for word in ["staging", "stage", "test"]):
            return "staging"
        else:
            return "development"

    async def _execute_server_command(self, command: ServerControlCommand) -> Dict[str, Any]:
        """
        Execute the server control command.

        Args:
            command: Server control command to execute

        Returns:
            Command execution results
        """
        try:
            if command.action == "start":
                return await self._start_server(command.environment)
            elif command.action == "stop":
                return await self._stop_server(command.environment)
            elif command.action == "restart":
                return await self._restart_server(command.environment)
            elif command.action == "status":
                return await self._check_server_status(command.environment)
            elif command.action == "logs":
                return await self._get_server_logs(command.environment)
            elif command.action == "deploy":
                return await self._deploy_server(command.environment)
            elif command.action == "test":
                return await self._run_tests()
            elif command.action == "build":
                return await self._build_server(command.environment)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {command.action}"
                }

        except Exception as e:
            logger.error(f"Error executing server command {command.action}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _start_server(self, environment: str) -> Dict[str, Any]:
        """Start the server."""
        try:
            if environment == "development":
                # Start development server
                cmd = ["docker-compose", "up", "-d"]
            elif environment == "staging":
                cmd = ["docker-compose", "-f", "docker-compose.yml", "-f", "docker-compose.staging.yml", "up", "-d"]
            elif environment == "production":
                cmd = ["docker-compose", "-f", "docker-compose.yml", "-f", "docker-compose.prod.yml", "up", "-d"]
            else:
                cmd = ["docker-compose", "up", "-d"]

            result = await self._run_command(cmd)
            
            if result["success"]:
                # Wait a moment for services to start
                await asyncio.sleep(3)
                
                # Check if services are running
                status_result = await self._check_server_status(environment)
                
                return {
                    "success": True,
                    "message": f"Server started successfully in {environment} environment",
                    "output": result["output"],
                    "status": status_result
                }
            else:
                return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start server: {str(e)}"
            }

    async def _stop_server(self, environment: str) -> Dict[str, Any]:
        """Stop the server."""
        try:
            cmd = ["docker-compose", "down"]
            result = await self._run_command(cmd)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Server stopped successfully in {environment} environment",
                    "output": result["output"]
                }
            else:
                return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop server: {str(e)}"
            }

    async def _restart_server(self, environment: str) -> Dict[str, Any]:
        """Restart the server."""
        try:
            # Stop the server first
            stop_result = await self._stop_server(environment)
            if not stop_result["success"]:
                return stop_result
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Start the server
            start_result = await self._start_server(environment)
            
            return {
                "success": start_result["success"],
                "message": f"Server restarted successfully in {environment} environment",
                "stop_result": stop_result,
                "start_result": start_result
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to restart server: {str(e)}"
            }

    async def _check_server_status(self, environment: str) -> Dict[str, Any]:
        """Check server status."""
        try:
            cmd = ["docker-compose", "ps"]
            result = await self._run_command(cmd)
            
            if result["success"]:
                # Parse the output to get service status
                services = self._parse_docker_compose_ps(result["output"])
                
                return {
                    "success": True,
                    "message": f"Server status for {environment} environment",
                    "services": services,
                    "output": result["output"]
                }
            else:
                return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to check server status: {str(e)}"
            }

    async def _get_server_logs(self, environment: str, lines: int = 50) -> Dict[str, Any]:
        """Get server logs."""
        try:
            cmd = ["docker-compose", "logs", "--tail", str(lines), "-f"]
            result = await self._run_command(cmd, timeout=10)  # Limit log output time
            
            return {
                "success": True,
                "message": f"Server logs for {environment} environment (last {lines} lines)",
                "logs": result["output"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get server logs: {str(e)}"
            }

    async def _deploy_server(self, environment: str) -> Dict[str, Any]:
        """Deploy the server."""
        try:
            if environment == "production":
                cmd = ["./deploy-the7space-production.sh"]
            elif environment == "staging":
                cmd = ["./scripts/deploy.sh", "--env", "staging"]
            else:
                cmd = ["./scripts/deploy.sh", "--env", "dev"]

            result = await self._run_command(cmd, timeout=300)  # 5 minute timeout for deployment
            
            return {
                "success": result["success"],
                "message": f"Deployment {'completed' if result['success'] else 'failed'} for {environment} environment",
                "output": result["output"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to deploy server: {str(e)}"
            }

    async def _run_tests(self) -> Dict[str, Any]:
        """Run server tests."""
        try:
            cmd = ["python", "-m", "pytest", "tests/", "-v"]
            result = await self._run_command(cmd, timeout=120)  # 2 minute timeout for tests
            
            return {
                "success": result["success"],
                "message": f"Tests {'passed' if result['success'] else 'failed'}",
                "output": result["output"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to run tests: {str(e)}"
            }

    async def _build_server(self, environment: str) -> Dict[str, Any]:
        """Build server images."""
        try:
            cmd = ["docker-compose", "build"]
            result = await self._run_command(cmd, timeout=600)  # 10 minute timeout for build
            
            return {
                "success": result["success"],
                "message": f"Server build {'completed' if result['success'] else 'failed'} for {environment} environment",
                "output": result["output"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to build server: {str(e)}"
            }

    async def _run_command(self, cmd: List[str], timeout: int = 60) -> Dict[str, Any]:
        """
        Run a shell command asynchronously.

        Args:
            cmd: Command to run as list of strings
            timeout: Command timeout in seconds

        Returns:
            Command execution results
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.project_root
            )
            
            try:
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
                output = stdout.decode('utf-8') if stdout else ""
                
                return {
                    "success": process.returncode == 0,
                    "output": output,
                    "return_code": process.returncode,
                    "command": " ".join(cmd)
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "command": " ".join(cmd)
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": " ".join(cmd)
            }

    def _parse_docker_compose_ps(self, output: str) -> List[Dict[str, str]]:
        """
        Parse docker-compose ps output to extract service information.

        Args:
            output: Raw docker-compose ps output

        Returns:
            List of service information dictionaries
        """
        services = []
        lines = output.strip().split('\n')
        
        # Skip header lines
        for line in lines[2:]:  # Usually first 2 lines are headers
            if line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    services.append({
                        "name": parts[0],
                        "command": " ".join(parts[1:-3]) if len(parts) > 4 else parts[1],
                        "state": parts[-3],
                        "ports": parts[-1] if len(parts) > 4 else ""
                    })
        
        return services

    async def _log_to_onepassword(self, command: str, result: Dict[str, Any]) -> None:
        """
        Log command execution to 1Password clipboard for snippet use.

        Args:
            command: The executed command
            result: Command execution result
        """
        if not self.onepassword_enabled:
            return

        try:
            # Create log entry for 1Password clipboard
            log_entry = f"Voice Command: {command}\n"
            log_entry += f"Time: {datetime.now().isoformat()}\n"
            log_entry += f"Success: {result.get('success', False)}\n"
            log_entry += f"Action: {result.get('action', 'unknown')}\n"

            if result.get('message'):
                log_entry += f"Message: {result['message']}\n"

            # Copy to clipboard for 1Password snippet use
            process = await asyncio.create_subprocess_exec(
                'pbcopy',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            await process.communicate(input=log_entry.encode('utf-8'))
            logger.info("Command logged to clipboard for 1Password snippets")

        except Exception as e:
            logger.warning(f"Failed to log to 1Password clipboard: {e}")


# Service factory function
async def get_voice_server_control_service(voice_service: AquaVoiceService) -> VoiceServerControlService:
    """
    Get a voice server control service instance.

    Args:
        voice_service: Aqua voice service instance

    Returns:
        Voice server control service instance
    """
    return VoiceServerControlService(voice_service)
