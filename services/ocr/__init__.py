"""
OCR Services for The HigherSelf Network Server.

This package provides OCR capabilities using various providers:
- Tesseract: Open-source OCR engine
- Google Cloud Vision: Google's OCR service with high accuracy
- ABBYY: Commercial OCR service with high accuracy for structured documents
"""

import asyncio

from loguru import logger

from models.tesseract_models import OCRProvider
from services.ocr.abbyy_ocr_service import ABBYY_AVAILABLE, ABBYYOCRService
from services.ocr.base_ocr_service import BaseOCRService
from services.ocr.google_vision_ocr_service import (GOOGLE_VISION_AVAILABLE,
                                                    GoogleVisionOCRService)
from services.ocr.ocr_service_factory import OCRServiceFactory
from services.ocr.tesseract_ocr_service import TesseractOCRService

# Register service classes with the factory
OCRServiceFactory.register_service_class(OCRProvider.TESSERACT, TesseractOCRService)

if GOOGLE_VISION_AVAILABLE:
    OCRServiceFactory.register_service_class(
        OCRProvider.GOOGLE_VISION, GoogleVisionOCRService
    )
else:
    logger.warning(
        "Google Cloud Vision OCR service not available. Install google-cloud-vision to enable it."
    )

if ABBYY_AVAILABLE:
    OCRServiceFactory.register_service_class(OCRProvider.ABBYY, ABBYYOCRService)
else:
    logger.warning("ABBYY OCR service not available. Install ABBYY SDK to enable it.")


# Create singleton instances
tesseract_service = TesseractOCRService.from_env()

# Initialize Google Vision service if available
google_vision_service = None
if GOOGLE_VISION_AVAILABLE:
    try:
        google_vision_service = GoogleVisionOCRService.from_env()
    except Exception as e:
        logger.error(f"Failed to initialize Google Vision OCR service: {e}")

# Initialize ABBYY service if available
abbyy_service = None
if ABBYY_AVAILABLE:
    try:
        abbyy_service = ABBYYOCRService.from_env()
    except Exception as e:
        logger.error(f"Failed to initialize ABBYY OCR service: {e}")


__all__ = [
    "BaseOCRService",
    "TesseractOCRService",
    "GoogleVisionOCRService",
    "ABBYYOCRService",
    "OCRServiceFactory",
    "tesseract_service",
    "google_vision_service",
    "abbyy_service",
]
