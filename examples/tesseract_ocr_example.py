#!/usr/bin/env python3
"""
Tesseract OCR Example for The HigherSelf Network Server.

This example demonstrates how to use Tesseract OCR capabilities in agents.
It shows how to:
1. Create an agent with Tesseract OCR capabilities
2. Extract text from images using different methods
3. Process the extracted text

Usage:
    python examples/tesseract_ocr_example.py

Requirements:
    - pytesseract
    - Pillow
    - Tesseract OCR installed on the system
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

from loguru import logger

# Add parent directory to path to allow importing from the project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.base_agent import BaseAgent
from agents.mixins.tesseract_mixin import TesseractMixin
from models.base import AgentCapability, ApiPlatform
from models.tesseract_models import OCRLanguage
from services.tesseract_service import tesseract_service


class OCRAgent(BaseAgent, TesseractMixin):
    """
    Example agent with Tesseract OCR capabilities.

    This agent demonstrates how to use Tesseract OCR to extract text from images.
    """

    def __init__(
        self,
        agent_id: str = "ocr_agent",
        name: str = "OCR Agent",
        description: str = "Extracts text from images using Tesseract OCR",
    ):
        """Initialize the OCR agent."""
        # Initialize base agent
        BaseAgent.__init__(
            self,
            agent_id=agent_id,
            name=name,
            description=description,
            capabilities=[
                AgentCapability.CONTENT_CREATION,
                AgentCapability.AI_INTEGRATION,
            ],
            apis_utilized=[ApiPlatform.NOTION],
        )

        # Initialize Tesseract mixin
        TesseractMixin.__init__(self)

        logger.info(f"OCR Agent initialized: {agent_id}")

    async def process_image_from_file(self, image_path: str) -> None:
        """
        Process an image file using Tesseract OCR.

        Args:
            image_path: Path to the image file
        """
        logger.info(f"Processing image from file: {image_path}")

        # Extract text from the image
        result = await self.extract_text_from_image(
            image_path=image_path, languages=["eng"], preprocessing=True
        )

        if result["success"]:
            logger.info(f"Extracted text: {result['text']}")
            logger.info(f"Confidence: {result['confidence']}")
            logger.info(f"Processing time: {result['processing_time']} seconds")
        else:
            logger.error(f"Error extracting text: {result['error']}")

    async def process_image_from_url(self, image_url: str) -> None:
        """
        Process an image from a URL using Tesseract OCR.

        Args:
            image_url: URL of the image
        """
        logger.info(f"Processing image from URL: {image_url}")

        # Extract text from the image
        result = await self.extract_text_from_url(
            image_url=image_url, languages=["eng"], preprocessing=True
        )

        if result["success"]:
            logger.info(f"Extracted text: {result['text']}")
            logger.info(f"Confidence: {result['confidence']}")
            logger.info(f"Processing time: {result['processing_time']} seconds")
        else:
            logger.error(f"Error extracting text: {result['error']}")

    async def process_image_from_base64(self, base64_image: str) -> None:
        """
        Process a base64-encoded image using Tesseract OCR.

        Args:
            base64_image: Base64-encoded image data
        """
        logger.info("Processing image from base64 data")

        # Extract text from the image
        result = await self.extract_text_from_base64(
            base64_image=base64_image, languages=["eng"], preprocessing=True
        )

        if result["success"]:
            logger.info(f"Extracted text: {result['text']}")
            logger.info(f"Confidence: {result['confidence']}")
            logger.info(f"Processing time: {result['processing_time']} seconds")
        else:
            logger.error(f"Error extracting text: {result['error']}")

    async def get_supported_languages(self) -> None:
        """Get a list of supported OCR languages."""
        languages = super().get_supported_languages()

        logger.info("Supported OCR languages:")
        for lang in languages:
            logger.info(f"  {lang['name']} ({lang['code']})")


async def main():
    """Run the example."""
    # Create an OCR agent
    agent = OCRAgent()

    # Get supported languages
    await agent.get_supported_languages()

    # Example 1: Process an image file
    # Replace with an actual image file path
    image_path = "examples/data/sample_text.png"

    # Create the examples/data directory if it doesn't exist
    os.makedirs(os.path.dirname(image_path), exist_ok=True)

    # Check if the image file exists
    if not os.path.exists(image_path):
        logger.warning(f"Image file not found: {image_path}")
        logger.info("Please create an image file with text for testing")
    else:
        await agent.process_image_from_file(image_path)

    # Example 2: Process an image from a URL
    # Replace with an actual image URL
    image_url = "https://raw.githubusercontent.com/tesseract-ocr/tessdata/main/eng.training_text.png"
    await agent.process_image_from_url(image_url)

    # Example 3: Process a base64-encoded image
    # This is just a placeholder - you would need to provide actual base64 data
    # For demonstration purposes, we'll skip this if no image file is available
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            image_data = f.read()
            base64_image = base64.b64encode(image_data).decode("utf-8")
            await agent.process_image_from_base64(base64_image)


if __name__ == "__main__":
    asyncio.run(main())
