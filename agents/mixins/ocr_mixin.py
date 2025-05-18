"""
OCR Mixin for The HigherSelf Network Server agents.

This mixin provides OCR capabilities to agents using multiple providers:
- Tesseract: Open-source OCR engine (default)
- Google Cloud Vision: Google's OCR service with high accuracy
- ABBYY: Commercial OCR service with high accuracy for structured documents
"""

import os
import base64
from typing import Dict, List, Optional, Union, Any
from loguru import logger

from services.ocr import (
    OCRServiceFactory,
    tesseract_service,
    google_vision_service,
    abbyy_service
)
from models.tesseract_models import (
    OCRRequest,
    OCRResponse,
    OCRLanguage,
    OCROutputFormat,
    OCRImageSource,
    OCRProvider,
    OCRDocumentType
)


class OCRMixin:
    """
    Mixin for adding OCR capabilities to agents.
    
    This mixin provides methods for extracting text from images using
    multiple OCR providers, with automatic selection based on document
    importance and type.
    """
    
    def __init__(self):
        """Initialize the OCR mixin."""
        # Default to Tesseract service
        self.default_ocr_service = tesseract_service
        logger.info(f"OCRMixin initialized for {getattr(self, 'agent_id', 'unknown agent')}")
    
    async def extract_text_from_image(
        self,
        image_path: str,
        languages: List[str] = ["eng"],
        preprocessing: bool = True,
        is_important: bool = False,
        document_type: str = "general",
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file
            languages: List of language codes
            preprocessing: Whether to apply preprocessing
            is_important: Whether this is an important document requiring high accuracy
            document_type: Type of document being processed
            provider: Specific OCR provider to use (overrides automatic selection)
        
        Returns:
            Dictionary containing:
                - success: Whether the operation was successful
                - text: Extracted text
                - confidence: Average confidence score
                - processing_time: Time taken to process the image
                - provider: OCR provider used
        """
        # Convert language strings to OCRLanguage enum values
        try:
            lang_enums = [OCRLanguage(lang) for lang in languages]
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid language code: {str(e)}"
            }
        
        # Convert document type string to enum
        try:
            doc_type = OCRDocumentType(document_type)
        except ValueError:
            doc_type = OCRDocumentType.GENERAL
        
        # Convert provider string to enum if specified
        provider_enum = None
        if provider:
            try:
                provider_enum = OCRProvider(provider)
            except ValueError:
                logger.warning(f"Invalid provider: {provider}, using automatic selection")
        
        # Create OCR request
        request = OCRRequest(
            image_source=OCRImageSource.FILE,
            image_data=image_path,
            languages=lang_enums,
            output_format=OCROutputFormat.TEXT,
            preprocessing=preprocessing,
            is_important=is_important,
            document_type=doc_type,
            provider=provider_enum or OCRProvider.TESSERACT
        )
        
        # Get the appropriate service based on the request
        if provider_enum:
            # Use the specified provider
            try:
                service = OCRServiceFactory.get_service(provider_enum)
            except ValueError:
                logger.warning(f"Provider {provider_enum} not available, using default")
                service = self.default_ocr_service
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
            "provider": response.provider.value
        }
    
    async def extract_text_from_url(
        self,
        image_url: str,
        languages: List[str] = ["eng"],
        preprocessing: bool = True,
        is_important: bool = False,
        document_type: str = "general",
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract text from an image URL.
        
        Args:
            image_url: URL of the image
            languages: List of language codes
            preprocessing: Whether to apply preprocessing
            is_important: Whether this is an important document requiring high accuracy
            document_type: Type of document being processed
            provider: Specific OCR provider to use (overrides automatic selection)
        
        Returns:
            Dictionary containing:
                - success: Whether the operation was successful
                - text: Extracted text
                - confidence: Average confidence score
                - processing_time: Time taken to process the image
                - provider: OCR provider used
        """
        # Convert language strings to OCRLanguage enum values
        try:
            lang_enums = [OCRLanguage(lang) for lang in languages]
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid language code: {str(e)}"
            }
        
        # Convert document type string to enum
        try:
            doc_type = OCRDocumentType(document_type)
        except ValueError:
            doc_type = OCRDocumentType.GENERAL
        
        # Convert provider string to enum if specified
        provider_enum = None
        if provider:
            try:
                provider_enum = OCRProvider(provider)
            except ValueError:
                logger.warning(f"Invalid provider: {provider}, using automatic selection")
        
        # Create OCR request
        request = OCRRequest(
            image_source=OCRImageSource.URL,
            image_data=image_url,
            languages=lang_enums,
            output_format=OCROutputFormat.TEXT,
            preprocessing=preprocessing,
            is_important=is_important,
            document_type=doc_type,
            provider=provider_enum or OCRProvider.TESSERACT
        )
        
        # Get the appropriate service based on the request
        if provider_enum:
            # Use the specified provider
            try:
                service = OCRServiceFactory.get_service(provider_enum)
            except ValueError:
                logger.warning(f"Provider {provider_enum} not available, using default")
                service = self.default_ocr_service
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
            "provider": response.provider.value
        }
    
    async def extract_text_from_base64(
        self,
        base64_image: str,
        languages: List[str] = ["eng"],
        preprocessing: bool = True,
        is_important: bool = False,
        document_type: str = "general",
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract text from a base64-encoded image.
        
        Args:
            base64_image: Base64-encoded image data
            languages: List of language codes
            preprocessing: Whether to apply preprocessing
            is_important: Whether this is an important document requiring high accuracy
            document_type: Type of document being processed
            provider: Specific OCR provider to use (overrides automatic selection)
        
        Returns:
            Dictionary containing:
                - success: Whether the operation was successful
                - text: Extracted text
                - confidence: Average confidence score
                - processing_time: Time taken to process the image
                - provider: OCR provider used
        """
        # Convert language strings to OCRLanguage enum values
        try:
            lang_enums = [OCRLanguage(lang) for lang in languages]
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid language code: {str(e)}"
            }
        
        # Convert document type string to enum
        try:
            doc_type = OCRDocumentType(document_type)
        except ValueError:
            doc_type = OCRDocumentType.GENERAL
        
        # Convert provider string to enum if specified
        provider_enum = None
        if provider:
            try:
                provider_enum = OCRProvider(provider)
            except ValueError:
                logger.warning(f"Invalid provider: {provider}, using automatic selection")
        
        # Create OCR request
        request = OCRRequest(
            image_source=OCRImageSource.BASE64,
            image_data=base64_image,
            languages=lang_enums,
            output_format=OCROutputFormat.TEXT,
            preprocessing=preprocessing,
            is_important=is_important,
            document_type=doc_type,
            provider=provider_enum or OCRProvider.TESSERACT
        )
        
        # Get the appropriate service based on the request
        if provider_enum:
            # Use the specified provider
            try:
                service = OCRServiceFactory.get_service(provider_enum)
            except ValueError:
                logger.warning(f"Provider {provider_enum} not available, using default")
                service = self.default_ocr_service
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
            "provider": response.provider.value
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
    
    def get_supported_providers(self) -> List[Dict[str, str]]:
        """
        Get a list of supported OCR providers.
        
        Returns:
            List of dictionaries containing:
                - code: Provider code
                - name: Provider name
                - available: Whether the provider is available
        """
        providers = []
        
        # Tesseract is always available
        providers.append({
            "code": OCRProvider.TESSERACT.value,
            "name": "Tesseract OCR",
            "available": True
        })
        
        # Google Cloud Vision
        providers.append({
            "code": OCRProvider.GOOGLE_VISION.value,
            "name": "Google Cloud Vision",
            "available": google_vision_service is not None
        })
        
        # ABBYY
        providers.append({
            "code": OCRProvider.ABBYY.value,
            "name": "ABBYY Cloud OCR",
            "available": abbyy_service is not None
        })
        
        return providers
    
    def get_supported_document_types(self) -> List[Dict[str, str]]:
        """
        Get a list of supported document types.
        
        Returns:
            List of dictionaries containing:
                - code: Document type code
                - name: Document type name
        """
        doc_types = []
        
        for doc_type in OCRDocumentType:
            doc_types.append({
                "code": doc_type.value,
                "name": doc_type.name.replace("_", " ").title()
            })
        
        return doc_types
