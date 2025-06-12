"""
OCR Service Factory for The HigherSelf Network Server.

This module provides a factory for creating OCR service instances
based on provider type and document importance.
"""

import os
from typing import Dict, Optional, Type

from loguru import logger

from models.tesseract_models import OCRDocumentType, OCRProvider, OCRRequest
from services.ocr.base_ocr_service import BaseOCRService


class OCRServiceFactory:
    """
    Factory for creating OCR service instances.

    This factory selects the appropriate OCR service based on the provider
    specified in the request and the importance of the document.
    """

    _services: Dict[OCRProvider, BaseOCRService] = {}
    _service_classes: Dict[OCRProvider, Type[BaseOCRService]] = {}

    @classmethod
    def register_service_class(
        cls, provider: OCRProvider, service_class: Type[BaseOCRService]
    ) -> None:
        """
        Register a service class for a provider.

        Args:
            provider: OCR provider
            service_class: Service class for the provider
        """
        cls._service_classes[provider] = service_class
        logger.info(f"Registered {service_class.__name__} for provider {provider}")

    @classmethod
    def get_service(cls, provider: OCRProvider) -> BaseOCRService:
        """
        Get a service instance for a provider.

        Args:
            provider: OCR provider

        Returns:
            Service instance

        Raises:
            ValueError: If the provider is not supported
        """
        # Check if we already have an instance
        if provider in cls._services:
            return cls._services[provider]

        # Check if we have a class for this provider
        if provider not in cls._service_classes:
            raise ValueError(f"Unsupported OCR provider: {provider}")

        # Create a new instance
        service_class = cls._service_classes[provider]
        service = service_class.from_env()
        cls._services[provider] = service

        return service

    @classmethod
    def select_provider(cls, request: OCRRequest) -> OCRProvider:
        """
        Select the appropriate provider based on the request.

        This method implements the logic for selecting a provider based on
        document importance and type. If the document is marked as important,
        it will use a premium provider (ABBYY or Google Vision) based on the
        document type.

        Args:
            request: OCR request

        Returns:
            Selected OCR provider
        """
        # If a specific provider is requested and not overridden by importance, use it
        if not request.is_important:
            return request.provider

        # For important documents, select the best provider based on document type
        if request.document_type in [
            OCRDocumentType.INVOICE,
            OCRDocumentType.RECEIPT,
            OCRDocumentType.FORM,
            OCRDocumentType.CONTRACT,
            OCRDocumentType.LEGAL,
        ]:
            # ABBYY is better for structured documents
            return OCRProvider.ABBYY
        else:
            # Google Vision is better for general text and ID cards
            return OCRProvider.GOOGLE_VISION

    @classmethod
    async def process_request(cls, request: OCRRequest) -> BaseOCRService:
        """
        Process an OCR request by selecting the appropriate provider.

        Args:
            request: OCR request

        Returns:
            Selected OCR service
        """
        # Select the provider based on the request
        provider = cls.select_provider(request)

        # If the provider is different from the one in the request, log it
        if provider != request.provider:
            logger.info(
                f"Overriding requested provider {request.provider} with {provider} "
                f"due to document importance and type"
            )

        # Get the service for the selected provider
        return cls.get_service(provider)
