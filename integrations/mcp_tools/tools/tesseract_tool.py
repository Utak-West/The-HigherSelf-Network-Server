"""
Tesseract OCR MCP Tool for Higher Self Network Server.
Provides a tool for agents to extract text from images using Tesseract OCR.
"""

import os
import json
import base64
import asyncio
from typing import Dict, List, Any, Optional
import httpx
from pydantic import BaseModel, Field
from loguru import logger

from integrations.mcp_tools.mcp_tools_registry import (
    mcp_tools_registry,
    MCPTool,
    ToolMetadata,
    ToolCapability
)
from services.cache_service import multi_level_cache, CacheType, CacheLevel
from services.tesseract_service import tesseract_service
from models.tesseract_models import (
    OCRRequest,
    OCRResponse,
    OCRLanguage,
    OCROutputFormat,
    OCRImageSource
)


class TesseractTool(MCPTool):
    """
    MCP Tool for performing OCR operations using Tesseract.
    
    This tool allows agents to extract text from images using Tesseract OCR.
    It supports various image sources, languages, and output formats.
    """
    
    def __init__(self):
        """Initialize the Tesseract tool."""
        super().__init__(
            tool_name="tesseract",
            metadata=ToolMetadata(
                name="Tesseract OCR",
                description="Extract text from images using Tesseract OCR",
                version="1.0.0",
                capabilities=[
                    ToolCapability.IMAGE_PROCESSING,
                    ToolCapability.TEXT_EXTRACTION,
                    ToolCapability.DOCUMENT_PROCESSING
                ]
            )
        )
        
        # Register methods
        self.register_method(
            "extract_text",
            self._extract_text,
            "Extract text from an image using Tesseract OCR"
        )
        
        self.register_method(
            "extract_text_from_url",
            self._extract_text_from_url,
            "Extract text from an image URL using Tesseract OCR"
        )
        
        self.register_method(
            "extract_text_from_base64",
            self._extract_text_from_base64,
            "Extract text from a base64-encoded image using Tesseract OCR"
        )
        
        self.register_method(
            "get_supported_languages",
            self._get_supported_languages,
            "Get a list of supported OCR languages"
        )
    
    async def _extract_text(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """
        Extract text from an image file.
        
        Args:
            params: Dictionary containing:
                - file_path: Path to the image file
                - languages: List of language codes (default: ["eng"])
                - preprocessing: Whether to apply preprocessing (default: True)
            agent_id: ID of the agent making the request
        
        Returns:
            Dictionary containing:
                - success: Whether the operation was successful
                - text: Extracted text
                - confidence: Average confidence score
                - processing_time: Time taken to process the image
        """
        file_path = params.get("file_path")
        if not file_path:
            return {"success": False, "message": "file_path is required"}
        
        languages = params.get("languages", ["eng"])
        preprocessing = params.get("preprocessing", True)
        
        # Convert language strings to OCRLanguage enum values
        try:
            lang_enums = [OCRLanguage(lang) for lang in languages]
        except ValueError as e:
            return {"success": False, "message": f"Invalid language code: {str(e)}"}
        
        # Create OCR request
        request = OCRRequest(
            image_source=OCRImageSource.FILE,
            image_data=file_path,
            languages=lang_enums,
            output_format=OCROutputFormat.TEXT,
            preprocessing=preprocessing
        )
        
        # Process the image
        response = await tesseract_service.process_image(request)
        
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
    
    async def _extract_text_from_url(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """
        Extract text from an image URL.
        
        Args:
            params: Dictionary containing:
                - url: URL of the image
                - languages: List of language codes (default: ["eng"])
                - preprocessing: Whether to apply preprocessing (default: True)
            agent_id: ID of the agent making the request
        
        Returns:
            Dictionary containing:
                - success: Whether the operation was successful
                - text: Extracted text
                - confidence: Average confidence score
                - processing_time: Time taken to process the image
        """
        url = params.get("url")
        if not url:
            return {"success": False, "message": "url is required"}
        
        languages = params.get("languages", ["eng"])
        preprocessing = params.get("preprocessing", True)
        
        # Convert language strings to OCRLanguage enum values
        try:
            lang_enums = [OCRLanguage(lang) for lang in languages]
        except ValueError as e:
            return {"success": False, "message": f"Invalid language code: {str(e)}"}
        
        # Create OCR request
        request = OCRRequest(
            image_source=OCRImageSource.URL,
            image_data=url,
            languages=lang_enums,
            output_format=OCROutputFormat.TEXT,
            preprocessing=preprocessing
        )
        
        # Process the image
        response = await tesseract_service.process_image(request)
        
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
    
    async def _extract_text_from_base64(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """
        Extract text from a base64-encoded image.
        
        Args:
            params: Dictionary containing:
                - base64_image: Base64-encoded image data
                - languages: List of language codes (default: ["eng"])
                - preprocessing: Whether to apply preprocessing (default: True)
            agent_id: ID of the agent making the request
        
        Returns:
            Dictionary containing:
                - success: Whether the operation was successful
                - text: Extracted text
                - confidence: Average confidence score
                - processing_time: Time taken to process the image
        """
        base64_image = params.get("base64_image")
        if not base64_image:
            return {"success": False, "message": "base64_image is required"}
        
        languages = params.get("languages", ["eng"])
        preprocessing = params.get("preprocessing", True)
        
        # Convert language strings to OCRLanguage enum values
        try:
            lang_enums = [OCRLanguage(lang) for lang in languages]
        except ValueError as e:
            return {"success": False, "message": f"Invalid language code: {str(e)}"}
        
        # Create OCR request
        request = OCRRequest(
            image_source=OCRImageSource.BASE64,
            image_data=base64_image,
            languages=lang_enums,
            output_format=OCROutputFormat.TEXT,
            preprocessing=preprocessing
        )
        
        # Process the image
        response = await tesseract_service.process_image(request)
        
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
    
    async def _get_supported_languages(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """
        Get a list of supported OCR languages.
        
        Args:
            params: Empty dictionary
            agent_id: ID of the agent making the request
        
        Returns:
            Dictionary containing:
                - languages: List of supported language codes and names
        """
        languages = []
        
        for lang in OCRLanguage:
            languages.append({
                "code": lang.value,
                "name": lang.name.replace("_", " ").title()
            })
        
        return {
            "success": True,
            "languages": languages
        }


# Create a singleton instance
tesseract_tool = TesseractTool()
