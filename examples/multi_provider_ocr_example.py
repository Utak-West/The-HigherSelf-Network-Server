#!/usr/bin/env python3
"""
Multi-Provider OCR Example for The HigherSelf Network Server.

This example demonstrates how to use OCR capabilities with multiple providers:
- Tesseract: Open-source OCR engine (default)
- Google Cloud Vision: Google's OCR service with high accuracy
- ABBYY: Commercial OCR service with high accuracy for structured documents

It shows how to:
1. Create an agent with OCR capabilities
2. Extract text from images using different providers
3. Process the extracted text
4. Automatically select the appropriate provider based on document importance

Usage:
    python examples/multi_provider_ocr_example.py

Requirements:
    - pytesseract
    - Pillow
    - google-cloud-vision (optional)
    - ABBYY SDK (optional)
    - Tesseract OCR installed on the system
"""

import os
import sys
import asyncio
import base64
from pathlib import Path
from loguru import logger

# Add parent directory to path to allow importing from the project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.base_agent import BaseAgent
from agents.mixins.ocr_mixin import OCRMixin
from models.base import AgentCapability, ApiPlatform
from models.tesseract_models import OCRProvider, OCRDocumentType


class MultiProviderOCRAgent(BaseAgent, OCRMixin):
    """
    Example agent with multi-provider OCR capabilities.
    
    This agent demonstrates how to use different OCR providers to extract text from images.
    """
    
    def __init__(
        self,
        agent_id: str = "ocr_agent",
        name: str = "OCR Agent",
        description: str = "Extracts text from images using multiple OCR providers"
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
                AgentCapability.AI_INTEGRATION
            ],
            apis_utilized=[
                ApiPlatform.NOTION
            ]
        )
        
        # Initialize OCR mixin
        OCRMixin.__init__(self)
        
        logger.info(f"Multi-Provider OCR Agent initialized: {agent_id}")
    
    async def process_image_with_tesseract(self, image_path: str) -> None:
        """
        Process an image file using Tesseract OCR.
        
        Args:
            image_path: Path to the image file
        """
        logger.info(f"Processing image with Tesseract: {image_path}")
        
        # Extract text from the image
        result = await self.extract_text_from_image(
            image_path=image_path,
            languages=["eng"],
            preprocessing=True,
            provider=OCRProvider.TESSERACT.value
        )
        
        if result["success"]:
            logger.info(f"Extracted text: {result['text']}")
            logger.info(f"Confidence: {result['confidence']}")
            logger.info(f"Processing time: {result['processing_time']} seconds")
            logger.info(f"Provider: {result['provider']}")
        else:
            logger.error(f"Error extracting text: {result['error']}")
    
    async def process_image_with_google_vision(self, image_path: str) -> None:
        """
        Process an image file using Google Cloud Vision OCR.
        
        Args:
            image_path: Path to the image file
        """
        logger.info(f"Processing image with Google Cloud Vision: {image_path}")
        
        # Extract text from the image
        result = await self.extract_text_from_image(
            image_path=image_path,
            languages=["eng"],
            preprocessing=False,  # Google Vision doesn't need preprocessing
            provider=OCRProvider.GOOGLE_VISION.value
        )
        
        if result["success"]:
            logger.info(f"Extracted text: {result['text']}")
            logger.info(f"Confidence: {result['confidence']}")
            logger.info(f"Processing time: {result['processing_time']} seconds")
            logger.info(f"Provider: {result['provider']}")
        else:
            logger.error(f"Error extracting text: {result['error']}")
    
    async def process_image_with_abbyy(self, image_path: str) -> None:
        """
        Process an image file using ABBYY OCR.
        
        Args:
            image_path: Path to the image file
        """
        logger.info(f"Processing image with ABBYY: {image_path}")
        
        # Extract text from the image
        result = await self.extract_text_from_image(
            image_path=image_path,
            languages=["eng"],
            preprocessing=False,  # ABBYY doesn't need preprocessing
            provider=OCRProvider.ABBYY.value
        )
        
        if result["success"]:
            logger.info(f"Extracted text: {result['text']}")
            logger.info(f"Confidence: {result['confidence']}")
            logger.info(f"Processing time: {result['processing_time']} seconds")
            logger.info(f"Provider: {result['provider']}")
        else:
            logger.error(f"Error extracting text: {result['error']}")
    
    async def process_important_document(self, image_path: str, document_type: str) -> None:
        """
        Process an important document with automatic provider selection.
        
        Args:
            image_path: Path to the image file
            document_type: Type of document
        """
        logger.info(f"Processing important document of type {document_type}: {image_path}")
        
        # Extract text from the image
        result = await self.extract_text_from_image(
            image_path=image_path,
            languages=["eng"],
            preprocessing=True,
            is_important=True,
            document_type=document_type
        )
        
        if result["success"]:
            logger.info(f"Extracted text: {result['text']}")
            logger.info(f"Confidence: {result['confidence']}")
            logger.info(f"Processing time: {result['processing_time']} seconds")
            logger.info(f"Provider: {result['provider']}")
        else:
            logger.error(f"Error extracting text: {result['error']}")
    
    async def show_supported_features(self) -> None:
        """Show supported OCR features."""
        # Get supported languages
        languages = self.get_supported_languages()
        logger.info("Supported OCR languages:")
        for lang in languages:
            logger.info(f"  {lang['name']} ({lang['code']})")
        
        # Get supported providers
        providers = self.get_supported_providers()
        logger.info("Supported OCR providers:")
        for provider in providers:
            status = "Available" if provider["available"] else "Not available"
            logger.info(f"  {provider['name']} ({provider['code']}): {status}")
        
        # Get supported document types
        doc_types = self.get_supported_document_types()
        logger.info("Supported document types:")
        for doc_type in doc_types:
            logger.info(f"  {doc_type['name']} ({doc_type['code']})")


async def main():
    """Run the example."""
    # Create an OCR agent
    agent = MultiProviderOCRAgent()
    
    # Show supported features
    await agent.show_supported_features()
    
    # Example 1: Process an image file with Tesseract
    # Replace with an actual image file path
    image_path = "examples/data/sample_text.png"
    
    # Create the examples/data directory if it doesn't exist
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    
    # Check if the image file exists
    if not os.path.exists(image_path):
        logger.warning(f"Image file not found: {image_path}")
        logger.info("Please create an image file with text for testing")
    else:
        # Process with different providers
        await agent.process_image_with_tesseract(image_path)
        
        # Try Google Cloud Vision if available
        try:
            await agent.process_image_with_google_vision(image_path)
        except Exception as e:
            logger.warning(f"Google Cloud Vision not available: {e}")
        
        # Try ABBYY if available
        try:
            await agent.process_image_with_abbyy(image_path)
        except Exception as e:
            logger.warning(f"ABBYY not available: {e}")
        
        # Process important documents with automatic provider selection
        await agent.process_important_document(image_path, OCRDocumentType.INVOICE.value)
        await agent.process_important_document(image_path, OCRDocumentType.PASSPORT.value)


if __name__ == "__main__":
    asyncio.run(main())
