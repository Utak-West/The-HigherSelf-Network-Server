"""
Voice Router for The HigherSelf Network Server.

This module provides API endpoints for voice processing and command handling.
"""

import base64
import io
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from loguru import logger
from pydantic import BaseModel, Field

from services.ai_router import AIRouter
from services.aqua_voice_service import (
    AquaVoiceService,
    get_aqua_voice_service,
    VoiceCommandRequest,
    VoiceTranscriptionRequest,
)
from services.voice_server_control import get_voice_server_control_service, VoiceServerControlService


# Models
class TranscriptionRequest(BaseModel):
    """Request for voice transcription."""

    audio_data: str = Field(..., description="Base64 encoded audio data")
    content_type: str = Field("audio/wav", description="MIME type of audio")
    context: Optional[str] = Field(
        None, description="Optional context for better transcription"
    )
    format_type: Optional[str] = Field(
        None, description="Optional formatting type (email, code, etc.)"
    )


class TranscriptionResponse(BaseModel):
    """Response for transcription requests."""

    success: bool = Field(..., description="Whether the transcription was successful")
    text: str = Field(..., description="Transcribed text")
    confidence: Optional[float] = Field(None, description="Confidence score")
    processing_time: Optional[float] = Field(
        None, description="Processing time in seconds"
    )
    error: Optional[str] = Field(
        None, description="Error message if transcription failed"
    )


class CommandRequest(BaseModel):
    """Request for voice command processing."""

    text: str = Field(..., description="Transcribed text")
    context: Optional[str] = Field(
        None, description="Optional context for command processing"
    )


class CommandResponse(BaseModel):
    """Response for command requests."""

    success: bool = Field(
        ..., description="Whether the command processing was successful"
    )
    is_command: bool = Field(
        ..., description="Whether the text was identified as a command"
    )
    text: str = Field(..., description="Original text")
    response: Optional[str] = Field(None, description="Response to the command")
    action: Optional[Dict[str, Any]] = Field(
        None, description="Structured action details"
    )
    error: Optional[str] = Field(
        None, description="Error message if command processing failed"
    )


# Router
router = APIRouter(
    prefix="/voice",
    tags=["voice"],
    responses={404: {"description": "Not found"}},
)


# Dependencies
async def get_voice_service(ai_router: AIRouter = Depends()) -> AquaVoiceService:
    """Get the Aqua Voice service."""
    return await get_aqua_voice_service(ai_router)


# Endpoints
@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    request: TranscriptionRequest,
    voice_service: AquaVoiceService = Depends(get_voice_service),
) -> TranscriptionResponse:
    """
    Transcribe audio to text.

    Args:
        request: Transcription request
        voice_service: Aqua Voice service

    Returns:
        Transcription response
    """
    try:
        # Create transcription request
        voice_request = VoiceTranscriptionRequest(
            audio_data=request.audio_data,
            content_type=request.content_type,
            context=request.context,
            format_type=request.format_type,
        )

        # Transcribe audio
        result = await voice_service.transcribe(voice_request)

        # Convert to response model
        return TranscriptionResponse(**result)

    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return TranscriptionResponse(success=False, text="", error=str(e))


@router.post("/transcribe/file", response_model=TranscriptionResponse)
async def transcribe_audio_file(
    file: UploadFile = File(...),
    context: Optional[str] = Form(None),
    format_type: Optional[str] = Form(None),
    voice_service: AquaVoiceService = Depends(get_voice_service),
) -> TranscriptionResponse:
    """
    Transcribe an uploaded audio file to text.

    Args:
        file: Uploaded audio file
        context: Optional context for better transcription
        format_type: Optional formatting type (email, code, etc.)
        voice_service: Aqua Voice service

    Returns:
        Transcription response
    """
    try:
        # Read file content
        content = await file.read()

        # Encode as base64
        audio_data = base64.b64encode(content).decode("utf-8")

        # Create transcription request
        voice_request = VoiceTranscriptionRequest(
            audio_data=audio_data,
            content_type=file.content_type or "audio/wav",
            context=context,
            format_type=format_type,
        )

        # Transcribe audio
        result = await voice_service.transcribe(voice_request)

        # Convert to response model
        return TranscriptionResponse(**result)

    except Exception as e:
        logger.error(f"Error transcribing audio file: {e}")
        return TranscriptionResponse(success=False, text="", error=str(e))


@router.post("/command", response_model=CommandResponse)
async def process_command(
    request: CommandRequest,
    voice_service: AquaVoiceService = Depends(get_voice_service),
) -> CommandResponse:
    """
    Process a voice command.

    Args:
        request: Command request
        voice_service: Aqua Voice service

    Returns:
        Command response
    """
    try:
        # Create command request
        voice_request = VoiceCommandRequest(text=request.text, context=request.context)

        # Process command
        result = await voice_service.process_command(voice_request)

        # Convert to response model
        return CommandResponse(**result)

    except Exception as e:
        logger.error(f"Error processing command: {e}")
        return CommandResponse(
            success=False, is_command=False, text=request.text, error=str(e)
        )


@router.post("/transcribe-and-command", response_model=CommandResponse)
async def transcribe_and_process_command(
    request: TranscriptionRequest,
    voice_service: AquaVoiceService = Depends(get_voice_service),
) -> CommandResponse:
    """
    Transcribe audio and process as a command in one step.

    Args:
        request: Transcription request
        voice_service: Aqua Voice service

    Returns:
        Command response
    """
    try:
        # First transcribe the audio
        voice_transcription_request = VoiceTranscriptionRequest(
            audio_data=request.audio_data,
            content_type=request.content_type,
            context=request.context,
            format_type=request.format_type,
        )

        transcription_result = await voice_service.transcribe(
            voice_transcription_request
        )

        if not transcription_result.get("success", False):
            return CommandResponse(
                success=False,
                is_command=False,
                text="",
                error=transcription_result.get("error", "Transcription failed"),
            )

        # Then process the transcribed text as a command
        voice_command_request = VoiceCommandRequest(
            text=transcription_result.get("text", ""), context=request.context
        )

        command_result = await voice_service.process_command(voice_command_request)

        # Convert to response model
        return CommandResponse(**command_result)

    except Exception as e:
        logger.error(f"Error in transcribe and command: {e}")
        return CommandResponse(success=False, is_command=False, text="", error=str(e))


# Server Control Models
class ServerControlRequest(BaseModel):
    """Server control request model."""

    command: str = Field(..., description="Voice command for server control")
    environment: Optional[str] = Field(default="development", description="Target environment")


class ServerControlResponse(BaseModel):
    """Server control response model."""

    success: bool = Field(..., description="Whether the command was successful")
    action: Optional[str] = Field(None, description="The action that was performed")
    message: Optional[str] = Field(None, description="Response message")
    result: Optional[Dict[str, Any]] = Field(None, description="Command execution results")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: Optional[str] = Field(None, description="Command execution timestamp")


# Server Control Endpoints
@router.post("/server/control", response_model=ServerControlResponse)
async def voice_server_control(
    request: ServerControlRequest,
    voice_service: AquaVoiceService = Depends(get_voice_service),
) -> ServerControlResponse:
    """
    Process voice commands for server control operations.

    Args:
        request: Server control request
        voice_service: Aqua Voice service

    Returns:
        Server control response
    """
    try:
        # Get voice server control service
        server_control_service = await get_voice_server_control_service(voice_service)

        # Process the voice command
        result = await server_control_service.process_voice_command(request.command)

        # Convert to response model
        return ServerControlResponse(**result)

    except Exception as e:
        logger.error(f"Error processing server control command: {e}")
        return ServerControlResponse(
            success=False,
            error=str(e),
            message="Failed to process server control command"
        )


@router.post("/server/transcribe-and-control", response_model=ServerControlResponse)
async def transcribe_and_control_server(
    file: UploadFile = File(...),
    environment: str = Form(default="development"),
    voice_service: AquaVoiceService = Depends(get_voice_service),
) -> ServerControlResponse:
    """
    Transcribe audio and process as server control command.

    Args:
        file: Audio file to transcribe
        environment: Target environment
        voice_service: Aqua Voice service

    Returns:
        Server control response
    """
    try:
        # Read file content
        content = await file.read()

        # Encode as base64
        audio_data = base64.b64encode(content).decode("utf-8")

        # Create transcription request
        voice_request = VoiceTranscriptionRequest(
            audio_data=audio_data,
            content_type=file.content_type or "audio/wav",
        )

        # Transcribe audio
        transcription_result = await voice_service.transcribe(voice_request)

        if not transcription_result.get("success", False):
            return ServerControlResponse(
                success=False,
                error=transcription_result.get("error", "Transcription failed"),
                message="Failed to transcribe audio"
            )

        # Get transcribed text
        transcribed_text = transcription_result.get("text", "")

        if not transcribed_text:
            return ServerControlResponse(
                success=False,
                error="No text transcribed from audio",
                message="Audio transcription returned empty text"
            )

        # Get voice server control service
        server_control_service = await get_voice_server_control_service(voice_service)

        # Process the transcribed command
        result = await server_control_service.process_voice_command(transcribed_text)

        # Add transcription info to result
        result["transcribed_text"] = transcribed_text
        result["transcription_confidence"] = transcription_result.get("confidence", 0.0)

        # Convert to response model
        return ServerControlResponse(**result)

    except Exception as e:
        logger.error(f"Error transcribing and controlling server: {e}")
        return ServerControlResponse(
            success=False,
            error=str(e),
            message="Failed to transcribe and process server control command"
        )
