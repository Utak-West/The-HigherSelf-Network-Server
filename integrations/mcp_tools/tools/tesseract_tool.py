"""
OCR MCP Tool for Higher Self Network Server.
Provides a tool for agents to extract text from images using multiple OCR providers:
- Tesseract: Open-source OCR engine (default)
- Google Cloud Vision: Google's OCR service with high accuracy
- ABBYY: Commercial OCR service with high accuracy for structured documents
"""

import asyncio
import base64
import json
import os
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from integrations.mcp_tools.mcp_tools_registry import (
    MCPTool,
    ToolCapability,
    ToolMetadata,
    mcp_tools_registry,
)
from models.tesseract_models import (
    OCRDocumentType,
    OCRImageSource,
    OCRLanguage,
    OCROutputFormat,
    OCRProvider,
    OCRRequest,
    OCRResponse,
)
from services.cache_service import CacheLevel, CacheType, multi_level_cache
from services.ocr import (
    OCRServiceFactory,
    abbyy_service,
    google_vision_service,
    tesseract_service,
)


class TesseractTool(MCPTool):
    """
    MCP Tool for performing OCR operations using multiple providers.

    This tool allows agents to extract text from images using various OCR providers:
    - Tesseract: Open-source OCR engine (default)
    - Google Cloud Vision: Google's OCR service with high accuracy
    - ABBYY: Commercial OCR service with high accuracy for structured documents

    It supports various image sources, languages, and output formats, with
    automatic provider selection based on document importance.
    """

    def __init__(self):
        """Initialize the OCR tool."""
        super().__init__(
            tool_name="ocr",
            metadata=ToolMetadata(
                name="OCR Tool",
                description="Extract text from images using multiple OCR providers",
                version="2.0.0",
                capabilities=[
                    "IMAGE_PROCESSING",
                    "TEXT_EXTRACTION",
                    "DOCUMENT_PROCESSING",
                ],
            ),
        )

        # Register methods
        self.register_method(
            "extract_text",
            self._extract_text,
            "Extract text from an image using OCR",
        )

        self.register_method(
            "extract_text_from_url",
            self._extract_text_from_url,
            "Extract text from an image URL using OCR",
        )

        self.register_method(
            "extract_text_from_base64",
            self._extract_text_from_base64,
            "Extract text from a base64-encoded image using OCR",
        )

        self.register_method(
            "get_supported_languages",
            self._get_supported_languages,
            "Get a list of supported OCR languages",
        )

        self.register_method(
            "get_supported_providers",
            self._get_supported_providers,
            "Get a list of supported OCR providers",
        )

        self.register_method(
            "get_supported_document_types",
            self._get_supported_document_types,
            "Get a list of supported document types",
        )

    async def _extract_text(
        self, params: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """
        Extract text from an image file.

        Args:
            params: Dictionary containing:
                - file_path: Path to the image file
                - languages: List of language codes (default: ["eng"])
                - preprocessing: Whether to apply preprocessing (default: True)
                - is_important: Whether this is an important document (default: False)
                - document_type: Type of document (default: "general")
                - provider: Specific OCR provider to use (optional)
            agent_id: ID of the agent making the request

        Returns:
            Dictionary containing:
                - success: Whether the operation was successful
                - text: Extracted text
                - confidence: Average confidence score
                - processing_time: Time taken to process the image
                - provider: OCR provider used
        """
        file_path = params.get("file_path")
        if not file_path:
            return {"success": False, "message": "file_path is required"}

        languages = params.get("languages", ["eng"])
        preprocessing = params.get("preprocessing", True)
        is_important = params.get("is_important", False)
        document_type = params.get("document_type", "general")
        provider_str = params.get("provider")

        # Convert language strings to OCRLanguage enum values
        try:
            lang_enums = [OCRLanguage(lang) for lang in languages]
        except ValueError as e:
            return {"success": False, "message": f"Invalid language code: {str(e)}"}

        # Convert document type string to enum
        try:
            doc_type = OCRDocumentType(document_type)
        except ValueError:
            doc_type = OCRDocumentType.GENERAL

        # Convert provider string to enum if specified
        provider_enum = None
        if provider_str:
            try:
                provider_enum = OCRProvider(provider_str)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid provider: {provider_str}",
                }

        # Create OCR request
        request = OCRRequest(
            image_source=OCRImageSource.FILE,
            image_data=file_path,
            languages=lang_enums,
            output_format=OCROutputFormat.TEXT,
            preprocessing=preprocessing,
            is_important=is_important,
            document_type=doc_type,
            provider=provider_enum or OCRProvider.TESSERACT,
        )

        # Get the appropriate service based on the request
        if provider_enum:
            # Use the specified provider
            try:
                service = OCRServiceFactory.get_service(provider_enum)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Provider {provider_enum} not available",
                }
        else:
            # Let the factory select the appropriate provider
            provider_enum = OCRServiceFactory.select_provider(request)
            service = OCRServiceFactory.get_service(provider_enum)

        # Process the image
        response = await service.process_image(request)

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
            "error": response.error,
            "provider": response.provider.value,
        }

    async def _extract_text_from_url(
        self, params: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """
        Extract text from an image URL.

        Args:
            params: Dictionary containing:
                - url: URL of the image
                - languages: List of language codes (default: ["eng"])
                - preprocessing: Whether to apply preprocessing (default: True)
                - is_important: Whether this is an important document (default: False)
                - document_type: Type of document (default: "general")
                - provider: Specific OCR provider to use (optional)
            agent_id: ID of the agent making the request

        Returns:
            Dictionary containing:
                - success: Whether the operation was successful
                - text: Extracted text
                - confidence: Average confidence score
                - processing_time: Time taken to process the image
                - provider: OCR provider used
        """
        url = params.get("url")
        if not url:
            return {"success": False, "message": "url is required"}

        languages = params.get("languages", ["eng"])
        preprocessing = params.get("preprocessing", True)
        is_important = params.get("is_important", False)
        document_type = params.get("document_type", "general")
        provider_str = params.get("provider")

        # Convert language strings to OCRLanguage enum values
        try:
            lang_enums = [OCRLanguage(lang) for lang in languages]
        except ValueError as e:
            return {"success": False, "message": f"Invalid language code: {str(e)}"}

        # Convert document type string to enum
        try:
            doc_type = OCRDocumentType(document_type)
        except ValueError:
            doc_type = OCRDocumentType.GENERAL

        # Convert provider string to enum if specified
        provider_enum = None
        if provider_str:
            try:
                provider_enum = OCRProvider(provider_str)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid provider: {provider_str}",
                }

        # Create OCR request
        request = OCRRequest(
            image_source=OCRImageSource.URL,
            image_data=url,
            languages=lang_enums,
            output_format=OCROutputFormat.TEXT,
            preprocessing=preprocessing,
            is_important=is_important,
            document_type=doc_type,
            provider=provider_enum or OCRProvider.TESSERACT,
        )

        # Get the appropriate service based on the request
        if provider_enum:
            # Use the specified provider
            try:
                service = OCRServiceFactory.get_service(provider_enum)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Provider {provider_enum} not available",
                }
        else:
            # Let the factory select the appropriate provider
            provider_enum = OCRServiceFactory.select_provider(request)
            service = OCRServiceFactory.get_service(provider_enum)

        # Process the image
        response = await service.process_image(request)

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
            "error": response.error,
            "provider": response.provider.value,
        }

    async def _extract_text_from_base64(
        self, params: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """
        Extract text from a base64-encoded image.

        Args:
            params: Dictionary containing:
                - base64_image: Base64-encoded image data
                - languages: List of language codes (default: ["eng"])
                - preprocessing: Whether to apply preprocessing (default: True)
                - is_important: Whether this is an important document (default: False)
                - document_type: Type of document (default: "general")
                - provider: Specific OCR provider to use (optional)
            agent_id: ID of the agent making the request

        Returns:
            Dictionary containing:
                - success: Whether the operation was successful
                - text: Extracted text
                - confidence: Average confidence score
                - processing_time: Time taken to process the image
                - provider: OCR provider used
        """
        base64_image = params.get("base64_image")
        if not base64_image:
            return {"success": False, "message": "base64_image is required"}

        languages = params.get("languages", ["eng"])
        preprocessing = params.get("preprocessing", True)
        is_important = params.get("is_important", False)
        document_type = params.get("document_type", "general")
        provider_str = params.get("provider")

        # Convert language strings to OCRLanguage enum values
        try:
            lang_enums = [OCRLanguage(lang) for lang in languages]
        except ValueError as e:
            return {"success": False, "message": f"Invalid language code: {str(e)}"}

        # Convert document type string to enum
        try:
            doc_type = OCRDocumentType(document_type)
        except ValueError:
            doc_type = OCRDocumentType.GENERAL

        # Convert provider string to enum if specified
        provider_enum = None
        if provider_str:
            try:
                provider_enum = OCRProvider(provider_str)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid provider: {provider_str}",
                }

        # Create OCR request
        request = OCRRequest(
            image_source=OCRImageSource.BASE64,
            image_data=base64_image,
            languages=lang_enums,
            output_format=OCROutputFormat.TEXT,
            preprocessing=preprocessing,
            is_important=is_important,
            document_type=doc_type,
            provider=provider_enum or OCRProvider.TESSERACT,
        )

        # Get the appropriate service based on the request
        if provider_enum:
            # Use the specified provider
            try:
                service = OCRServiceFactory.get_service(provider_enum)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Provider {provider_enum} not available",
                }
        else:
            # Let the factory select the appropriate provider
            provider_enum = OCRServiceFactory.select_provider(request)
            service = OCRServiceFactory.get_service(provider_enum)

        # Process the image
        response = await service.process_image(request)

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
            "error": response.error,
            "provider": response.provider.value,
        }

    async def _get_supported_languages(
        self, params: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
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
            languages.append(
                {"code": lang.value, "name": lang.name.replace("_", " ").title()}
            )

        return {"success": True, "languages": languages}

    async def _get_supported_providers(
        self, params: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """
        Get a list of supported OCR providers.

        Args:
            params: Empty dictionary
            agent_id: ID of the agent making the request

        Returns:
            Dictionary containing:
                - providers: List of supported OCR providers
        """
        providers = []

        # Tesseract is always available
        providers.append(
            {
                "code": OCRProvider.TESSERACT.value,
                "name": "Tesseract OCR",
                "available": True,
                "description": "Open-source OCR engine (default)",
            }
        )

        # Google Cloud Vision
        providers.append(
            {
                "code": OCRProvider.GOOGLE_VISION.value,
                "name": "Google Cloud Vision",
                "available": google_vision_service is not None,
                "description": "Google's OCR service with high accuracy",
            }
        )

        # ABBYY
        providers.append(
            {
                "code": OCRProvider.ABBYY.value,
                "name": "ABBYY Cloud OCR",
                "available": abbyy_service is not None,
                "description": "Commercial OCR service with high accuracy for structured documents",
            }
        )

        return {"success": True, "providers": providers}

    async def _get_supported_document_types(
        self, params: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """
        Get a list of supported document types.

        Args:
            params: Empty dictionary
            agent_id: ID of the agent making the request

        Returns:
            Dictionary containing:
                - document_types: List of supported document types
        """
        document_types = []

        for doc_type in OCRDocumentType:
            document_types.append(
                {
                    "code": doc_type.value,
                    "name": doc_type.name.replace("_", " ").title(),
                }
            )

        return {"success": True, "document_types": document_types}


# Create a singleton instance
tesseract_tool = TesseractTool()
