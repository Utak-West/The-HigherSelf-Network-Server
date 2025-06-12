"""
Plaud integration service for The HigherSelf Network Server.
This service provides methods for handling audio transcription via Plaud.
"""

import os
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from pydantic import BaseModel


class PlaudConfig(BaseModel):
    """Configuration for Plaud API integration."""

    api_key: str

    class Config:
        env_prefix = "PLAUD_"


class TranscriptionRequest(BaseModel):
    """Model for a transcription request."""

    audio_url: str
    callback_url: Optional[str] = None
    language: Optional[str] = "en"
    speaker_detection: bool = True
    sensitivity: str = "medium"  # low, medium, high


class TranscriptionResult(BaseModel):
    """Model for a transcription result."""

    id: str
    text: str
    status: str
    segments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class PlaudService:
    """
    Service for interacting with the Plaud API for audio transcription.
    Transcription results are processed and stored in Notion as the central hub.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the Plaud service.

        Args:
            api_key: Plaud API key
        """
        self.api_key = api_key or os.environ.get("PLAUD_API_KEY")
        self.base_url = "https://api.plaud.io/v1"

        if not self.api_key:
            logger.warning(
                "Plaud API key not configured. Transcription functionality will be limited."
            )

    async def submit_transcription(
        self, request: TranscriptionRequest
    ) -> Optional[str]:
        """
        Submit an audio file for transcription.

        Args:
            request: TranscriptionRequest model with audio URL and options

        Returns:
            Transcription ID if successful, None otherwise
        """
        if not self.api_key:
            logger.error("Plaud API key not configured")
            return None

        url = f"{self.base_url}/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "audio_url": request.audio_url,
            "language": request.language,
            "speaker_detection": request.speaker_detection,
            "sensitivity": request.sensitivity,
        }

        if request.callback_url:
            payload["callback_url"] = request.callback_url

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            transcription_id = data.get("id")
            logger.info(f"Submitted transcription request: {transcription_id}")
            return transcription_id
        except Exception as e:
            logger.error(f"Error submitting transcription: {e}")
            return None

    async def get_transcription(
        self, transcription_id: str
    ) -> Optional[TranscriptionResult]:
        """
        Get the status and results of a transcription.

        Args:
            transcription_id: ID of the transcription

        Returns:
            TranscriptionResult if found, None otherwise
        """
        if not self.api_key:
            logger.error("Plaud API key not configured")
            return None

        url = f"{self.base_url}/transcriptions/{transcription_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Create a TranscriptionResult model from the response
            result = TranscriptionResult(
                id=data.get("id"),
                text=data.get("text", ""),
                status=data.get("status", "unknown"),
                segments=data.get("segments"),
                metadata=data.get("metadata"),
            )

            logger.info(
                f"Retrieved transcription {transcription_id}: status={result.status}"
            )
            return result
        except Exception as e:
            logger.error(f"Error getting transcription: {e}")
            return None

    async def cancel_transcription(self, transcription_id: str) -> bool:
        """
        Cancel a transcription in progress.

        Args:
            transcription_id: ID of the transcription to cancel

        Returns:
            True if successful, False otherwise
        """
        if not self.api_key:
            logger.error("Plaud API key not configured")
            return False

        url = f"{self.base_url}/transcriptions/{transcription_id}/cancel"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            logger.info(f"Cancelled transcription {transcription_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling transcription: {e}")
            return False

    async def process_transcription_webhook(
        self, payload: Dict[str, Any]
    ) -> Optional[TranscriptionResult]:
        """
        Process a webhook notification from Plaud.

        Args:
            payload: Webhook payload

        Returns:
            TranscriptionResult if valid, None otherwise
        """
        try:
            # Extract relevant information from the webhook payload
            transcription_id = payload.get("id")
            if not transcription_id:
                logger.error("Invalid webhook payload: missing transcription ID")
                return None

            # Create a TranscriptionResult from the webhook data
            result = TranscriptionResult(
                id=transcription_id,
                text=payload.get("text", ""),
                status=payload.get("status", "unknown"),
                segments=payload.get("segments"),
                metadata=payload.get("metadata"),
            )

            logger.info(f"Processed transcription webhook for {transcription_id}")
            return result
        except Exception as e:
            logger.error(f"Error processing transcription webhook: {e}")
            return None
