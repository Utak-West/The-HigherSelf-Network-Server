#!/usr/bin/env python3
"""
Voice Processing Demo for The HigherSelf Network Server.

This example demonstrates how to use the Aqua Voice service to transcribe
audio and process voice commands.
"""

import os
import sys
import asyncio
import json
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path to allow importing from the server codebase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loguru import logger
from services.aqua_voice_service import get_aqua_voice_service, VoiceTranscriptionRequest, VoiceCommandRequest
from services.ai_router import AIRouter


async def transcribe_audio_file(file_path: str):
    """Transcribe an audio file using Aqua Voice."""
    logger.info("Initializing Aqua Voice service...")
    ai_router = AIRouter()
    voice_service = await get_aqua_voice_service(ai_router)
    
    # Read audio file
    with open(file_path, "rb") as f:
        audio_data = f.read()
    
    # Encode as base64
    audio_base64 = base64.b64encode(audio_data).decode("utf-8")
    
    # Create transcription request
    request = VoiceTranscriptionRequest(
        audio_data=audio_base64,
        content_type="audio/wav",  # Adjust based on your file type
        format_type="default"
    )
    
    # Transcribe audio
    logger.info(f"Transcribing audio file: {file_path}")
    result = await voice_service.transcribe(request)
    
    if result["success"]:
        logger.info("Successfully transcribed audio")
        logger.info(f"Confidence: {result.get('confidence', 'N/A')}")
        logger.info(f"Processing time: {result.get('processing_time', 'N/A')} seconds")
        
        # Print the transcription
        print("\n" + "="*50)
        print("Transcription:")
        print("="*50)
        print(result["text"])
        print("="*50 + "\n")
    else:
        logger.error(f"Failed to transcribe audio: {result.get('error')}")
    
    return result


async def process_voice_command(text: str):
    """Process a voice command using Aqua Voice."""
    logger.info("Initializing Aqua Voice service...")
    ai_router = AIRouter()
    voice_service = await get_aqua_voice_service(ai_router)
    
    # Create command request
    request = VoiceCommandRequest(
        text=text
    )
    
    # Process command
    logger.info(f"Processing voice command: {text}")
    result = await voice_service.process_command(request)
    
    if result["success"]:
        logger.info("Successfully processed command")
        logger.info(f"Is command: {result['is_command']}")
        
        if result["is_command"]:
            # Print the command response
            print("\n" + "="*50)
            print(f"Command: {text}")
            print("="*50)
            print(f"Response: {result.get('response', 'No response')}")
            print(f"Action: {json.dumps(result.get('action', {}), indent=2)}")
            print("="*50 + "\n")
        else:
            print("\n" + "="*50)
            print(f"Not a command: {text}")
            print("="*50 + "\n")
    else:
        logger.error(f"Failed to process command: {result.get('error')}")
    
    return result


async def main():
    """Run the voice processing demo."""
    # Set up logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Check if audio file path is provided
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        if os.path.exists(audio_file):
            # Transcribe audio file
            await transcribe_audio_file(audio_file)
        else:
            logger.error(f"Audio file not found: {audio_file}")
    
    # Process voice commands
    commands = [
        "Search for information about Crawl4AI and its features",
        "Create a new task to implement RAG in our application",
        "What is the weather like today?",
        "This is just a regular sentence, not a command"
    ]
    
    for command in commands:
        await process_voice_command(command)


if __name__ == "__main__":
    asyncio.run(main())
