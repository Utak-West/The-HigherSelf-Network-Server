#!/usr/bin/env python3
"""
Test script for Aqua Voice service.

This script tests the Aqua Voice service for voice transcription and command processing.
"""

import asyncio
import base64
import json
import os
import sys
from typing import Any, Dict, List, Optional

# Add parent directory to path to allow importing from the server codebase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

from services.ai_router import AIRouter

# Import required services
# Import required services
from services.aqua_voice_service import (
    VoiceCommandRequest,
    VoiceTranscriptionRequest,
    get_aqua_voice_service,
)


async def test_voice_transcription():
    """Test voice transcription functionality."""
    print("\n=== Testing Voice Transcription ===\n")

    # Check if Aqua API key is set
    api_key = os.getenv("AQUA_API_KEY")
    if not api_key:
        print(
            "❌ AQUA_API_KEY environment variable not set. Skipping transcription test."
        )
        return False

    # Initialize AI router
    ai_router = AIRouter()
    await ai_router.initialize()

    # Initialize Aqua Voice service
    voice_service = await get_aqua_voice_service(ai_router)

    # Load test audio file
    test_audio_path = os.path.join(os.path.dirname(__file__), "data", "test_audio.wav")

    if not os.path.exists(test_audio_path):
        print(f"❌ Test audio file not found: {test_audio_path}")
        print("Creating a directory for test data...")
        os.makedirs(os.path.dirname(test_audio_path), exist_ok=True)
        print(f"Please add a test audio file at: {test_audio_path}")
        return False

    # Read and encode audio file
    with open(test_audio_path, "rb") as f:
        audio_data = base64.b64encode(f.read()).decode("utf-8")

    print(f"Transcribing test audio file: {test_audio_path}")

    # Create transcription request
    request = VoiceTranscriptionRequest(audio_data=audio_data, content_type="audio/wav")

    # Transcribe audio
    result = await voice_service.transcribe(request)

    if result.get("success", False):
        print(f"✅ Successfully transcribed audio")
        print(f"  - Text: {result.get('text')}")
        print(f"  - Confidence: {result.get('confidence')}")
        return True
    else:
        print(f"❌ Failed to transcribe audio")
        print(f"  - Error: {result.get('error')}")
        return False


async def test_command_processing():
    """Test voice command processing functionality."""
    print("\n=== Testing Command Processing ===\n")

    # Initialize AI router
    ai_router = AIRouter()
    await ai_router.initialize()

    # Initialize Aqua Voice service
    voice_service = await get_aqua_voice_service(ai_router)

    # Test command
    test_command = "Search for information about retrieval augmented generation"

    print(f"Processing test command: '{test_command}'")

    # Create command request
    request = VoiceCommandRequest(text=test_command)

    # Process command
    result = await voice_service.process_command(request)

    if result.get("success", False):
        print(f"✅ Successfully processed command")
        print(f"  - Is command: {result.get('is_command')}")
        if result.get("is_command"):
            print(f"  - Response: {result.get('response')[:100]}...")
            print(f"  - Action type: {result.get('action', {}).get('type')}")
        return True
    else:
        print(f"❌ Failed to process command")
        print(f"  - Error: {result.get('error')}")
        return False


async def main():
    """Main function to run all tests."""
    print("\n=== Aqua Voice Service Test ===\n")

    # Run tests
    transcription_success = await test_voice_transcription()
    command_success = await test_command_processing()

    # Print summary
    print("\n=== Test Summary ===\n")
    print(f"Voice Transcription: {'✅ PASSED' if transcription_success else '❌ FAILED'}")
    print(f"Command Processing: {'✅ PASSED' if command_success else '❌ FAILED'}")

    overall_success = transcription_success and command_success
    print(f"\nOverall: {'✅ PASSED' if overall_success else '❌ FAILED'}")

    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
