"""
Google Cloud Vision OCR Service for The HigherSelf Network Server.

This service provides OCR capabilities using Google Cloud Vision API,
allowing agents to extract text from images with high accuracy.
"""

import base64
import hashlib
import os
import time
from io import BytesIO
from typing import Any, Dict, List, Optional, Union

import httpx
from loguru import logger

try:
    from google.cloud import vision
    from google.cloud.vision_v1 import types
    from google.oauth2 import service_account

    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    logger.warning(
        "google-cloud-vision not installed. Google Vision OCR functionality will be limited."
    )
    GOOGLE_VISION_AVAILABLE = False

from models.tesseract_models import (
    GoogleVisionOCRConfig,
    OCRBoundingBox,
    OCRImageSource,
    OCRLanguage,
    OCROutputFormat,
    OCRProvider,
    OCRRequest,
    OCRResponse,
    OCRTextElement,
)
from services.ocr.base_ocr_service import BaseOCRService


class GoogleVisionOCRService(BaseOCRService):
    """
    Service for performing OCR operations using Google Cloud Vision.

    This service provides methods for extracting text from images using
    Google Cloud Vision API, which offers high accuracy OCR.
    """

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[str] = None,
        cache_results: bool = True,
    ):
        """
        Initialize the Google Vision OCR service.

        Args:
            credentials_path: Path to the Google Cloud credentials JSON file
            credentials_json: Google Cloud credentials JSON string
            cache_results: Whether to cache OCR results
        """
        super().__init__(cache_results=cache_results)

        self.credentials_path = credentials_path
        self.credentials_json = credentials_json
        self.client = None

        if not GOOGLE_VISION_AVAILABLE:
            logger.warning(
                "GoogleVisionOCRService initialized but google-cloud-vision is not installed."
            )
            return

        try:
            # Initialize the client
            if credentials_path:
                self.credentials = (
                    service_account.Credentials.from_service_account_file(
                        credentials_path
                    )
                )
                self.client = vision.ImageAnnotatorClient(credentials=self.credentials)
            elif credentials_json:
                self.credentials = (
                    service_account.Credentials.from_service_account_info(
                        credentials_json
                    )
                )
                self.client = vision.ImageAnnotatorClient(credentials=self.credentials)
            else:
                # Use default credentials
                self.client = vision.ImageAnnotatorClient()

            logger.info("Google Cloud Vision client initialized")
        except Exception as e:
            logger.error(f"Error initializing Google Cloud Vision client: {e}")
            raise RuntimeError(f"Google Cloud Vision not available: {e}")

    @property
    def provider(self) -> OCRProvider:
        """Get the OCR provider type."""
        return OCRProvider.GOOGLE_VISION

    @classmethod
    def from_env(cls) -> "GoogleVisionOCRService":
        """
        Create a GoogleVisionOCRService instance from environment variables.

        Environment variables:
            GOOGLE_APPLICATION_CREDENTIALS: Path to the Google Cloud credentials JSON file
            GOOGLE_CREDENTIALS_JSON: Google Cloud credentials JSON string
            OCR_CACHE_RESULTS: Whether to cache OCR results (default: True)

        Returns:
            GoogleVisionOCRService instance
        """
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        cache_results = os.getenv("OCR_CACHE_RESULTS", "True").lower() == "true"

        return cls(
            credentials_path=credentials_path,
            credentials_json=credentials_json,
            cache_results=cache_results,
        )

    async def process_image(self, request: OCRRequest) -> OCRResponse:
        """
        Process an image using Google Cloud Vision OCR.

        Args:
            request: OCR request

        Returns:
            OCR response
        """
        if not GOOGLE_VISION_AVAILABLE or not self.client:
            return OCRResponse(
                success=False,
                provider=self.provider,
                output_format=request.output_format,
                processing_time=0.0,
                error="Google Cloud Vision not available",
            )

        start_time = time.time()

        try:
            # Check cache first if enabled
            cached_result = await self.get_cached_result(request)
            if cached_result:
                return cached_result

            # Load the image
            image = await self._load_image(request.image_source, request.image_data)

            # Get Google Vision config
            vision_config = GoogleVisionOCRConfig(**(request.config or {}))

            # Prepare feature request
            features = [vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION)]

            # Add language hints if provided
            image_context = None
            if request.languages:
                language_hints = [lang.value for lang in request.languages]
                image_context = vision.ImageContext(language_hints=language_hints)

            # Perform OCR
            response = self.client.annotate_image(
                {"image": image, "features": features, "image_context": image_context}
            )

            # Process the response
            if response.error.message:
                return OCRResponse(
                    success=False,
                    provider=self.provider,
                    output_format=request.output_format,
                    processing_time=time.time() - start_time,
                    error=response.error.message,
                )

            # Extract text
            text = (
                response.full_text_annotation.text
                if response.full_text_annotation
                else ""
            )

            # Extract text elements
            elements = []
            if response.text_annotations:
                # Skip the first annotation, which is the entire image
                for annotation in response.text_annotations[1:]:
                    vertices = annotation.bounding_poly.vertices
                    if len(vertices) >= 4:
                        x = vertices[0].x
                        y = vertices[0].y
                        width = vertices[2].x - x
                        height = vertices[2].y - y

                        element = OCRTextElement(
                            text=annotation.description,
                            confidence=1.0,  # Google Vision doesn't provide confidence scores
                            bounding_box=OCRBoundingBox(
                                x=x, y=y, width=width, height=height
                            ),
                        )
                        elements.append(element)

            # Create response
            result = OCRResponse(
                success=True,
                provider=self.provider,
                text=text,
                elements=elements,
                output_format=request.output_format,
                processing_time=time.time() - start_time,
                metadata={
                    "locale": (
                        response.full_text_annotation.pages[0]
                        .property.detected_languages[0]
                        .language_code
                        if response.full_text_annotation
                        and response.full_text_annotation.pages
                        else None
                    )
                },
            )

            # Cache the result if enabled
            await self.cache_result(request, result)

            return result

        except Exception as e:
            logger.error(f"Error processing image with Google Cloud Vision: {e}")
            return OCRResponse(
                success=False,
                provider=self.provider,
                output_format=request.output_format,
                processing_time=time.time() - start_time,
                error=str(e),
            )

    async def _load_image(
        self, source_type: OCRImageSource, image_data: Union[str, bytes]
    ) -> vision.Image:
        """
        Load an image from various sources.

        Args:
            source_type: Type of image source
            image_data: Image data or reference

        Returns:
            Google Cloud Vision Image
        """
        if source_type == OCRImageSource.FILE:
            # Load from file
            with open(image_data, "rb") as image_file:
                content = image_file.read()
            return vision.Image(content=content)

        elif source_type == OCRImageSource.URL:
            # Load from URL
            async with httpx.AsyncClient() as client:
                response = await client.get(image_data)
                response.raise_for_status()
                return vision.Image(content=response.content)

        elif source_type == OCRImageSource.BASE64:
            # Load from base64
            content = base64.b64decode(image_data)
            return vision.Image(content=content)

        elif source_type == OCRImageSource.BYTES:
            # Load from bytes
            return vision.Image(content=image_data)

        else:
            raise ValueError(f"Unsupported image source: {source_type}")

    def _generate_cache_key(self, request: OCRRequest) -> str:
        """
        Generate a cache key for an OCR request.

        Args:
            request: OCR request

        Returns:
            Cache key
        """
        # For file and URL sources, use the source as part of the key
        if request.image_source in [OCRImageSource.FILE, OCRImageSource.URL]:
            source_key = request.image_data
        else:
            # For base64 and bytes, use a hash of the data
            if isinstance(request.image_data, str):
                source_key = hashlib.md5(request.image_data.encode()).hexdigest()
            else:
                source_key = hashlib.md5(request.image_data).hexdigest()

        # Combine with other request parameters
        languages = "+".join([lang.value for lang in request.languages])

        return f"ocr:google_vision:{source_key}:{languages}:{request.output_format}"
