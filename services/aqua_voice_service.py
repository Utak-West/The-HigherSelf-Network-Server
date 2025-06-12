"""
Aqua Voice Service for The HigherSelf Network Server.

This service provides voice-to-text capabilities using Aqua's advanced
transcription technology, with natural language command processing.
"""

import asyncio
import base64
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from knowledge.semantic_search import get_semantic_search
# Local imports
from services.ai_router import AIRouter


class VoiceTranscriptionRequest(BaseModel):
    """Request for voice transcription."""

    audio_data: str  # Base64 encoded audio data
    content_type: str = "audio/wav"  # MIME type of audio
    context: Optional[str] = None  # Optional context for better transcription
    format_type: Optional[str] = None  # Optional formatting type (email, code, etc.)


class VoiceCommandRequest(BaseModel):
    """Request for voice command processing."""

    text: str  # Transcribed text
    context: Optional[str] = None  # Optional context for command processing


class AquaVoiceService:
    """Service for voice-to-text and command processing using Aqua."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Aqua Voice service.

        Args:
            api_key: Optional API key for Aqua Voice service
        """
        self.api_key = api_key or os.getenv("AQUA_API_KEY")
        self.api_base_url = os.getenv("AQUA_API_URL", "https://api.withaqua.com/v1")
        self.semantic_search = None
        self.ai_router = None
        self._initialized = False
        self._http_client = None

    async def initialize(self, ai_router: Optional[AIRouter] = None):
        """
        Initialize the service and its dependencies.

        Args:
            ai_router: Optional AIRouter instance for command processing
        """
        if self._initialized:
            return

        try:
            # Initialize semantic search
            self.semantic_search = await get_semantic_search()

            # Set AI router
            self.ai_router = ai_router

            # Initialize HTTP client
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

            self._initialized = True
            logger.info("Aqua Voice service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Aqua Voice service: {e}")
            raise

    async def close(self):
        """Close the service and release resources."""
        if self._http_client:
            await self._http_client.aclose()
        self._initialized = False
        logger.info("Aqua Voice service closed")

    async def transcribe(self, request: VoiceTranscriptionRequest) -> Dict[str, Any]:
        """
        Transcribe audio to text using Aqua Voice.

        Args:
            request: Voice transcription request

        Returns:
            Dictionary with transcription results
        """
        if not self._initialized:
            raise RuntimeError("Aqua Voice service not initialized")

        if not self.api_key:
            # Fallback to local transcription if no API key
            return await self._local_transcribe(request)

        try:
            # Prepare request payload
            payload = {
                "audio_data": request.audio_data,
                "content_type": request.content_type,
            }

            if request.context:
                payload["context"] = request.context

            if request.format_type:
                payload["format_type"] = request.format_type

            # Make API request
            response = await self._http_client.post(
                f"{self.api_base_url}/transcribe", json=payload
            )

            if response.status_code != 200:
                logger.error(
                    f"Aqua Voice API error: {response.status_code} - {response.text}"
                )
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "text": "",
                }

            result = response.json()

            return {
                "success": True,
                "text": result.get("text", ""),
                "confidence": result.get("confidence", 0.0),
                "processing_time": result.get("processing_time", 0.0),
            }

        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return {"success": False, "error": str(e), "text": ""}

    async def _local_transcribe(
        self, request: VoiceTranscriptionRequest
    ) -> Dict[str, Any]:
        """
        Fallback to local transcription when Aqua API is not available.
        Uses Whisper or other local models if available.

        Args:
            request: Voice transcription request

        Returns:
            Dictionary with transcription results
        """
        try:
            # Decode base64 audio data
            audio_data = base64.b64decode(request.audio_data)

            # TODO: Implement local transcription using Whisper or other models
            # For now, return an error
            logger.warning("Local transcription not implemented, Aqua API key required")

            return {
                "success": False,
                "error": "Local transcription not implemented, Aqua API key required",
                "text": "",
            }

        except Exception as e:
            logger.error(f"Error during local transcription: {e}")
            return {"success": False, "error": str(e), "text": ""}

    async def process_command(self, request: VoiceCommandRequest) -> Dict[str, Any]:
        """
        Process a voice command using AI.

        Args:
            request: Voice command request

        Returns:
            Dictionary with command processing results
        """
        if not self._initialized:
            raise RuntimeError("Aqua Voice service not initialized")

        if not self.ai_router:
            logger.error("AI router not available for command processing")
            return {
                "success": False,
                "error": "AI router not available",
                "response": "",
            }

        try:
            # Detect if this is a command
            is_command = self._is_command(request.text)

            if not is_command:
                return {"success": True, "is_command": False, "text": request.text}

            # Process command with AI
            command_context = (
                f"The user has given the following voice command: {request.text}"
            )
            if request.context:
                command_context += f"\nAdditional context: {request.context}"

            completion_request = {
                "prompt": command_context,
                "max_tokens": 500,
                "temperature": 0.7,
                "system_message": "You are an AI assistant that processes voice commands. Interpret the command and provide a clear response about what action should be taken.",
            }

            completion_response = await self.ai_router.get_completion(
                completion_request
            )

            if not completion_response.get("success", False):
                logger.error(
                    f"AI completion error: {completion_response.get('error', 'Unknown error')}"
                )
                return {
                    "success": False,
                    "error": completion_response.get("error", "AI processing failed"),
                    "is_command": True,
                    "text": request.text,
                }

            return {
                "success": True,
                "is_command": True,
                "text": request.text,
                "response": completion_response.get("text", ""),
                "action": self._extract_action(completion_response.get("text", "")),
            }

        except Exception as e:
            logger.error(f"Error during command processing: {e}")
            return {
                "success": False,
                "error": str(e),
                "is_command": False,
                "text": request.text,
            }

    def _is_command(self, text: str) -> bool:
        """
        Determine if text is a command.

        Args:
            text: Transcribed text

        Returns:
            True if text appears to be a command, False otherwise
        """
        # Simple heuristic for command detection
        command_indicators = [
            "search for",
            "find",
            "look up",
            "tell me about",
            "create",
            "make",
            "add",
            "schedule",
            "set up",
            "delete",
            "remove",
            "cancel",
            "update",
            "change",
            "send",
            "email",
            "message",
            "call",
            "contact",
            "start",
            "stop",
            "pause",
            "resume",
            "play",
            "what is",
            "who is",
            "when is",
            "where is",
            "how to",
        ]

        text_lower = text.lower()
        return any(indicator in text_lower for indicator in command_indicators)

    def _extract_action(self, response: str) -> Dict[str, Any]:
        """
        Extract structured action from AI response.

        Args:
            response: AI response text

        Returns:
            Dictionary with action details
        """
        # Simple action extraction
        # In a real implementation, this would be more sophisticated
        action = {"type": "unknown", "parameters": {}}

        if "search" in response.lower():
            action["type"] = "search"
            # Extract search query
            if "for" in response.lower():
                query_part = response.lower().split("for", 1)[1].strip()
                action["parameters"]["query"] = query_part
        elif "create" in response.lower() or "add" in response.lower():
            action["type"] = "create"
        elif "update" in response.lower() or "change" in response.lower():
            action["type"] = "update"
        elif "delete" in response.lower() or "remove" in response.lower():
            action["type"] = "delete"

        return action


# Singleton instance
_aqua_voice_service = None


async def get_aqua_voice_service(
    ai_router: Optional[AIRouter] = None,
) -> AquaVoiceService:
    """Get or create the Aqua Voice service singleton."""
    global _aqua_voice_service
    if _aqua_voice_service is None:
        _aqua_voice_service = AquaVoiceService()
        await _aqua_voice_service.initialize(ai_router)
    return _aqua_voice_service
