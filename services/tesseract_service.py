"""
Tesseract OCR Service for The HigherSelf Network Server.

This service provides OCR capabilities using Tesseract, allowing agents to extract
text from images. It supports various image sources, languages, and output formats.
"""

import base64
import os
import tempfile
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
from loguru import logger
from PIL import Image, ImageEnhance, ImageFilter

try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    logger.warning("pytesseract not installed. OCR functionality will be limited.")
    TESSERACT_AVAILABLE = False

from models.tesseract_models import (
    OCRBoundingBox,
    OCRImageSource,
    OCRLanguage,
    OCROutputFormat,
    OCRRequest,
    OCRResponse,
    OCRTextElement,
)
from services.cache_service import CacheType, multi_level_cache


class TesseractService:
    """
    Service for performing OCR operations using Tesseract.

    This service provides methods for extracting text from images using Tesseract OCR.
    It supports various image sources, languages, and output formats.
    """

    def __init__(
        self,
        tesseract_cmd: Optional[str] = None,
        tessdata_dir: Optional[str] = None,
        cache_results: bool = True,
    ):
        """
        Initialize the Tesseract service.

        Args:
            tesseract_cmd: Path to the Tesseract executable
            tessdata_dir: Path to the Tesseract data directory
            cache_results: Whether to cache OCR results
        """
        self.cache_results = cache_results

        if not TESSERACT_AVAILABLE:
            logger.warning(
                "TesseractService initialized but pytesseract is not installed."
            )
            return

        # Set Tesseract command path if provided
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        # Set Tesseract data directory if provided
        if tessdata_dir:
            os.environ["TESSDATA_PREFIX"] = tessdata_dir

        # Check if Tesseract is available
        try:
            pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {pytesseract.get_tesseract_version()}")
        except Exception as e:
            logger.error(f"Error initializing Tesseract: {e}")
            raise RuntimeError(f"Tesseract not available: {e}")

    @classmethod
    def from_env(cls) -> "TesseractService":
        """
        Create a TesseractService instance from environment variables.

        Environment variables:
            TESSERACT_CMD: Path to the Tesseract executable
            TESSDATA_DIR: Path to the Tesseract data directory
            TESSERACT_CACHE_RESULTS: Whether to cache OCR results (default: True)

        Returns:
            TesseractService instance
        """
        tesseract_cmd = os.getenv("TESSERACT_CMD")
        tessdata_dir = os.getenv("TESSDATA_DIR")
        cache_results = os.getenv("TESSERACT_CACHE_RESULTS", "True").lower() == "true"

        return cls(
            tesseract_cmd=tesseract_cmd,
            tessdata_dir=tessdata_dir,
            cache_results=cache_results,
        )

    async def process_image(self, request: OCRRequest) -> OCRResponse:
        """
        Process an image using Tesseract OCR.

        Args:
            request: OCR request

        Returns:
            OCR response
        """
        if not TESSERACT_AVAILABLE:
            return OCRResponse(
                success=False,
                output_format=request.output_format,
                processing_time=0.0,
                error="pytesseract not installed",
            )

        start_time = time.time()

        try:
            # Check cache first if enabled
            if self.cache_results:
                cache_key = self._generate_cache_key(request)
                cached_result = await multi_level_cache.get(
                    cache_key, CacheType.FUNCTION
                )
                if cached_result:
                    logger.info(f"Using cached OCR result for {cache_key}")
                    cached_result["from_cache"] = True
                    return OCRResponse(**cached_result)

            # Load the image
            image = await self._load_image(request.image_source, request.image_data)

            # Preprocess the image if requested
            if request.preprocessing:
                image = self._preprocess_image(image)

            # Prepare Tesseract configuration
            config = self._prepare_config(request)

            # Perform OCR
            languages = "+".join([lang.value for lang in request.languages])

            if request.output_format == OCROutputFormat.TEXT:
                # Extract text
                text = pytesseract.image_to_string(image, lang=languages, config=config)

                # Get text elements with confidence if available
                elements = None
                try:
                    data = pytesseract.image_to_data(
                        image,
                        lang=languages,
                        config=config,
                        output_type=pytesseract.Output.DICT,
                    )
                    elements = self._parse_text_elements(data)
                except Exception as e:
                    logger.warning(f"Error getting text elements: {e}")

                result = OCRResponse(
                    success=True,
                    text=text,
                    elements=elements,
                    output_format=request.output_format,
                    processing_time=time.time() - start_time,
                )

            elif request.output_format == OCROutputFormat.HOCR:
                # Extract HOCR
                hocr = pytesseract.image_to_pdf_or_hocr(
                    image, lang=languages, config=config, extension="hocr"
                )
                result = OCRResponse(
                    success=True,
                    raw_output=hocr.decode("utf-8"),
                    output_format=request.output_format,
                    processing_time=time.time() - start_time,
                )

            elif request.output_format == OCROutputFormat.TSV:
                # Extract TSV
                tsv = pytesseract.image_to_data(image, lang=languages, config=config)
                result = OCRResponse(
                    success=True,
                    raw_output=tsv,
                    output_format=request.output_format,
                    processing_time=time.time() - start_time,
                )

            elif request.output_format == OCROutputFormat.BOX:
                # Extract bounding boxes
                boxes = pytesseract.image_to_boxes(image, lang=languages, config=config)
                result = OCRResponse(
                    success=True,
                    raw_output=boxes,
                    output_format=request.output_format,
                    processing_time=time.time() - start_time,
                )

            else:
                # Unsupported output format
                result = OCRResponse(
                    success=False,
                    output_format=request.output_format,
                    processing_time=time.time() - start_time,
                    error=f"Unsupported output format: {request.output_format}",
                )

            # Cache the result if enabled
            if self.cache_results:
                cache_key = self._generate_cache_key(request)
                await multi_level_cache.set(
                    cache_key, result.dict(exclude={"from_cache"}), CacheType.FUNCTION
                )

            return result

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return OCRResponse(
                success=False,
                output_format=request.output_format,
                processing_time=time.time() - start_time,
                error=str(e),
            )

    async def _load_image(
        self, source_type: OCRImageSource, image_data: Union[str, bytes]
    ) -> Image.Image:
        """
        Load an image from various sources.

        Args:
            source_type: Type of image source
            image_data: Image data or reference

        Returns:
            PIL Image
        """
        if source_type == OCRImageSource.FILE:
            # Load from file
            return Image.open(image_data)

        elif source_type == OCRImageSource.URL:
            # Load from URL
            async with httpx.AsyncClient() as client:
                response = await client.get(image_data)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))

        elif source_type == OCRImageSource.BASE64:
            # Load from base64
            image_bytes = base64.b64decode(image_data)
            return Image.open(BytesIO(image_bytes))

        elif source_type == OCRImageSource.BYTES:
            # Load from bytes
            return Image.open(BytesIO(image_data))

        else:
            raise ValueError(f"Unsupported image source: {source_type}")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess an image to improve OCR results.

        Args:
            image: PIL Image

        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        image = image.convert("L")

        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Apply slight blur to reduce noise
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))

        # Apply threshold to make text more distinct
        threshold = 150
        image = image.point(lambda p: p > threshold and 255)

        return image

    def _prepare_config(self, request: OCRRequest) -> str:
        """
        Prepare Tesseract configuration string.

        Args:
            request: OCR request

        Returns:
            Tesseract configuration string
        """
        config_parts = [
            f"--psm {request.page_segmentation_mode}",
            f"--oem {request.ocr_engine_mode}",
        ]

        # Add custom configuration if provided
        if request.config:
            for key, value in request.config.items():
                config_parts.append(f"-c {key}={value}")

        return " ".join(config_parts)

    def _parse_text_elements(self, data: Dict[str, List]) -> List[OCRTextElement]:
        """
        Parse text elements from Tesseract data.

        Args:
            data: Tesseract data dictionary

        Returns:
            List of OCR text elements
        """
        elements = []

        n_boxes = len(data["text"])
        for i in range(n_boxes):
            # Skip empty text
            if not data["text"][i].strip():
                continue

            # Create text element
            element = OCRTextElement(
                text=data["text"][i],
                confidence=float(data["conf"][i]),
                bounding_box=OCRBoundingBox(
                    x=data["left"][i],
                    y=data["top"][i],
                    width=data["width"][i],
                    height=data["height"][i],
                ),
            )

            elements.append(element)

        return elements

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
            import hashlib

            if isinstance(request.image_data, str):
                source_key = hashlib.md5(request.image_data.encode()).hexdigest()
            else:
                source_key = hashlib.md5(request.image_data).hexdigest()

        # Combine with other request parameters
        languages = "+".join([lang.value for lang in request.languages])
        config_key = f"{request.page_segmentation_mode}_{request.ocr_engine_mode}"

        return f"ocr:{source_key}:{languages}:{request.output_format}:{config_key}:{request.preprocessing}"


# Create a singleton instance
tesseract_service = TesseractService.from_env()
