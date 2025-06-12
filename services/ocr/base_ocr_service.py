"""
Base OCR Service for The HigherSelf Network Server.

This module defines the abstract base class for OCR services.
All OCR provider implementations must extend this class.
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from models.tesseract_models import (OCRImageSource, OCRLanguage,
                                     OCROutputFormat, OCRProvider, OCRRequest,
                                     OCRResponse)
from services.cache_service import CacheType, multi_level_cache


class BaseOCRService(ABC):
    """
    Abstract base class for OCR services.

    All OCR provider implementations must extend this class to ensure
    consistent behavior and interface across different providers.
    """

    def __init__(self, cache_results: bool = True):
        """
        Initialize the base OCR service.

        Args:
            cache_results: Whether to cache OCR results
        """
        self.cache_results = cache_results
        logger.info(f"Initialized {self.__class__.__name__}")

    @property
    @abstractmethod
    def provider(self) -> OCRProvider:
        """Get the OCR provider type."""
        pass

    @abstractmethod
    async def process_image(self, request: OCRRequest) -> OCRResponse:
        """
        Process an image using OCR.

        Args:
            request: OCR request

        Returns:
            OCR response
        """
        pass

    @abstractmethod
    async def _load_image(
        self, source_type: OCRImageSource, image_data: Union[str, bytes]
    ) -> Any:
        """
        Load an image from various sources.

        Args:
            source_type: Type of image source
            image_data: Image data or reference

        Returns:
            Loaded image in the format required by the provider
        """
        pass

    @abstractmethod
    def _generate_cache_key(self, request: OCRRequest) -> str:
        """
        Generate a cache key for an OCR request.

        Args:
            request: OCR request

        Returns:
            Cache key
        """
        pass

    async def get_cached_result(self, request: OCRRequest) -> Optional[OCRResponse]:
        """
        Get a cached OCR result if available.

        Args:
            request: OCR request

        Returns:
            Cached OCR response or None if not found
        """
        if not self.cache_results:
            return None

        cache_key = self._generate_cache_key(request)
        cached_result = await multi_level_cache.get(cache_key, CacheType.FUNCTION)

        if cached_result:
            logger.info(f"Using cached OCR result for {cache_key}")
            cached_result["from_cache"] = True
            return OCRResponse(**cached_result)

        return None

    async def cache_result(self, request: OCRRequest, result: OCRResponse) -> None:
        """
        Cache an OCR result.

        Args:
            request: OCR request
            result: OCR response
        """
        if not self.cache_results:
            return

        cache_key = self._generate_cache_key(request)
        await multi_level_cache.set(
            cache_key, result.dict(exclude={"from_cache"}), CacheType.FUNCTION
        )

        logger.info(f"Cached OCR result for {cache_key}")

    @classmethod
    def from_env(cls) -> "BaseOCRService":
        """
        Create a service instance from environment variables.

        Returns:
            Service instance
        """
        cache_results = os.getenv("OCR_CACHE_RESULTS", "True").lower() == "true"
        return cls(cache_results=cache_results)
