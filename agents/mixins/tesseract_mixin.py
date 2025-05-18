"""
Tesseract OCR Mixin for The HigherSelf Network Server agents.

This mixin provides OCR capabilities to agents using Tesseract.
"""

import os
import base64
from typing import Dict, List, Optional, Union, Any
from loguru import logger

from services.tesseract_service import tesseract_service
from models.tesseract_models import (
    OCRRequest,
    OCRResponse,
    OCRLanguage,
    OCROutputFormat,
    OCRImageSource
)


class TesseractMixin:
    """
    Mixin for adding Tesseract OCR capabilities to agents.
    
    This mixin provides methods for extracting text from images using Tesseract OCR.
    """
    
    def __init__(self):
        """Initialize the Tesseract mixin."""
        self.tesseract_service = tesseract_service
        logger.info(f"TesseractMixin initialized for {getattr(self, 'agent_id', 'unknown agent')}")
    
    async def setup_tesseract(self, tesseract_service=None):
        """
        Set up the Tesseract service for this agent.
        
        Args:
            tesseract_service: Optional TesseractService instance
        """
        if tesseract_service:
            self.tesseract_service = tesseract_service
        else:
            self.tesseract_service = tesseract_service
        
        logger.info(f"Tesseract service set up for {getattr(self, 'agent_id', 'unknown agent')}")
    
    async def extract_text_from_image(
        self,
        image_path: str,
        languages: List[str] = ["eng"],
        preprocessing: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file
            languages: List of language codes
            preprocessing: Whether to apply preprocessing
        
        Returns:
            Dictionary containing:
                - success: Whether the operation was successful
                - text: Extracted text
                - confidence: Average confidence score
                - processing_time: Time taken to process the image
        """
        # Convert language strings to OCRLanguage enum values
        try:
            lang_enums = [OCRLanguage(lang) for lang in languages]
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid language code: {str(e)}"
            }
        
        # Create OCR request
        request = OCRRequest(
            image_source=OCRImageSource.FILE,
            image_data=image_path,
            languages=lang_enums,
            output_format=OCROutputFormat.TEXT,
            preprocessing=preprocessing
        )
        
        # Process the image
        response = await self.tesseract_service.process_image(request)
        
        # Calculate average confidence if elements are available
        avg_confidence = None
        if response.elements and len(response.elements) > 0:
            confidences = [elem.confidence for elem in response.elements]
            avg_confidence = sum(confidences) / len(confidences)
        
        # Return the result
        return {
            "success": response.success,
            "text": response.text,
            "confidence": avg_confidence,
            "processing_time": response.processing_time,
            "error": response.error
        }
    
    async def extract_text_from_url(
        self,
        image_url: str,
        languages: List[str] = ["eng"],
        preprocessing: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text from an image URL.
        
        Args:
            image_url: URL of the image
            languages: List of language codes
            preprocessing: Whether to apply preprocessing
        
        Returns:
            Dictionary containing:
                - success: Whether the operation was successful
                - text: Extracted text
                - confidence: Average confidence score
                - processing_time: Time taken to process the image
        """
        # Convert language strings to OCRLanguage enum values
        try:
            lang_enums = [OCRLanguage(lang) for lang in languages]
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid language code: {str(e)}"
            }
        
        # Create OCR request
        request = OCRRequest(
            image_source=OCRImageSource.URL,
            image_data=image_url,
            languages=lang_enums,
            output_format=OCROutputFormat.TEXT,
            preprocessing=preprocessing
        )
        
        # Process the image
        response = await self.tesseract_service.process_image(request)
        
        # Calculate average confidence if elements are available
        avg_confidence = None
        if response.elements and len(response.elements) > 0:
            confidences = [elem.confidence for elem in response.elements]
            avg_confidence = sum(confidences) / len(confidences)
        
        # Return the result
        return {
            "success": response.success,
            "text": response.text,
            "confidence": avg_confidence,
            "processing_time": response.processing_time,
            "error": response.error
        }
    
    async def extract_text_from_base64(
        self,
        base64_image: str,
        languages: List[str] = ["eng"],
        preprocessing: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text from a base64-encoded image.
        
        Args:
            base64_image: Base64-encoded image data
            languages: List of language codes
            preprocessing: Whether to apply preprocessing
        
        Returns:
            Dictionary containing:
                - success: Whether the operation was successful
                - text: Extracted text
                - confidence: Average confidence score
                - processing_time: Time taken to process the image
        """
        # Convert language strings to OCRLanguage enum values
        try:
            lang_enums = [OCRLanguage(lang) for lang in languages]
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid language code: {str(e)}"
            }
        
        # Create OCR request
        request = OCRRequest(
            image_source=OCRImageSource.BASE64,
            image_data=base64_image,
            languages=lang_enums,
            output_format=OCROutputFormat.TEXT,
            preprocessing=preprocessing
        )
        
        # Process the image
        response = await self.tesseract_service.process_image(request)
        
        # Calculate average confidence if elements are available
        avg_confidence = None
        if response.elements and len(response.elements) > 0:
            confidences = [elem.confidence for elem in response.elements]
            avg_confidence = sum(confidences) / len(confidences)
        
        # Return the result
        return {
            "success": response.success,
            "text": response.text,
            "confidence": avg_confidence,
            "processing_time": response.processing_time,
            "error": response.error
        }
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get a list of supported OCR languages.
        
        Returns:
            List of dictionaries containing:
                - code: Language code
                - name: Language name
        """
        languages = []
        
        for lang in OCRLanguage:
            languages.append({
                "code": lang.value,
                "name": lang.name.replace("_", " ").title()
            })
        
        return languages
