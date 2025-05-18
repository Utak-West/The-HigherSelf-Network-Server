"""
OCR models for The HigherSelf Network Server.

These models define the data structures for OCR operations using various providers
including Tesseract, Google Cloud Vision, and ABBYY.
"""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class OCRLanguage(str, Enum):
    """Supported OCR languages."""

    ENGLISH = "eng"
    FRENCH = "fra"
    GERMAN = "deu"
    SPANISH = "spa"
    ITALIAN = "ita"
    PORTUGUESE = "por"
    DUTCH = "nld"
    CHINESE_SIMPLIFIED = "chi_sim"
    CHINESE_TRADITIONAL = "chi_tra"
    JAPANESE = "jpn"
    KOREAN = "kor"
    ARABIC = "ara"
    HINDI = "hin"
    RUSSIAN = "rus"


class OCROutputFormat(str, Enum):
    """Output formats for OCR results."""

    TEXT = "text"
    HOCR = "hocr"
    TSV = "tsv"
    PDF = "pdf"
    BOX = "box"


class OCRImageSource(str, Enum):
    """Source types for images to be processed."""

    FILE = "file"
    URL = "url"
    BASE64 = "base64"
    BYTES = "bytes"


class OCRProvider(str, Enum):
    """OCR service providers."""

    TESSERACT = "tesseract"
    GOOGLE_VISION = "google_vision"
    ABBYY = "abbyy"


class OCRDocumentType(str, Enum):
    """Types of documents for OCR processing."""

    GENERAL = "general"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    ID_CARD = "id_card"
    PASSPORT = "passport"
    BUSINESS_CARD = "business_card"
    FORM = "form"
    CONTRACT = "contract"
    LEGAL = "legal"


class OCRRequest(BaseModel):
    """
    Request model for OCR operations.

    Attributes:
        image_source: Type of image source (file, URL, base64, bytes)
        image_data: Image data or reference (path, URL, base64 string, or bytes)
        provider: OCR provider to use (default: "tesseract")
        document_type: Type of document being processed (default: "general")
        is_important: Whether this is an important document requiring high accuracy
        languages: List of languages to use for OCR (default: ["eng"])
        output_format: Format of the OCR output (default: "text")
        config: Additional provider-specific configuration options
        preprocessing: Whether to apply preprocessing to the image (default: True)
        page_segmentation_mode: Tesseract-specific page segmentation mode (default: 3)
        ocr_engine_mode: Tesseract-specific OCR engine mode (default: 3)
    """

    image_source: OCRImageSource = Field(..., description="Type of image source")
    image_data: Union[str, bytes] = Field(..., description="Image data or reference")
    provider: OCRProvider = Field(
        default=OCRProvider.TESSERACT, description="OCR provider to use"
    )
    document_type: OCRDocumentType = Field(
        default=OCRDocumentType.GENERAL, description="Type of document being processed"
    )
    is_important: bool = Field(
        default=False,
        description="Whether this is an important document requiring high accuracy",
    )
    languages: List[OCRLanguage] = Field(
        default_factory=lambda: [OCRLanguage.ENGLISH],
        description="Languages to use for OCR",
    )
    output_format: OCROutputFormat = Field(
        default=OCROutputFormat.TEXT, description="Format of the OCR output"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional provider-specific configuration options"
    )
    preprocessing: bool = Field(
        default=True, description="Whether to apply preprocessing to the image"
    )
    page_segmentation_mode: int = Field(
        default=3, description="Tesseract-specific page segmentation mode"
    )
    ocr_engine_mode: int = Field(
        default=3, description="Tesseract-specific OCR engine mode"
    )


class OCRBoundingBox(BaseModel):
    """
    Bounding box for a text element in an OCR result.

    Attributes:
        x: X-coordinate of the top-left corner
        y: Y-coordinate of the top-left corner
        width: Width of the bounding box
        height: Height of the bounding box
    """

    x: int = Field(..., description="X-coordinate of the top-left corner")
    y: int = Field(..., description="Y-coordinate of the top-left corner")
    width: int = Field(..., description="Width of the bounding box")
    height: int = Field(..., description="Height of the bounding box")


class OCRTextElement(BaseModel):
    """
    Text element in an OCR result.

    Attributes:
        text: Extracted text
        confidence: Confidence score (0-100)
        bounding_box: Bounding box of the text element
    """

    text: str = Field(..., description="Extracted text")
    confidence: float = Field(..., description="Confidence score (0-100)")
    bounding_box: Optional[OCRBoundingBox] = Field(
        None, description="Bounding box of the text element"
    )


class OCRResponse(BaseModel):
    """
    Response model for OCR operations.

    Attributes:
        success: Whether the OCR operation was successful
        provider: OCR provider that processed the request
        text: Extracted text (if output_format is "text")
        elements: List of text elements with position and confidence
        raw_output: Raw output from the OCR provider
        output_format: Format of the OCR output
        processing_time: Time taken to process the image (in seconds)
        error: Error message (if success is False)
        metadata: Additional provider-specific metadata
    """

    success: bool = Field(..., description="Whether the OCR operation was successful")
    provider: OCRProvider = Field(
        ..., description="OCR provider that processed the request"
    )
    text: Optional[str] = Field(None, description="Extracted text")
    elements: Optional[List[OCRTextElement]] = Field(
        None, description="List of text elements with position and confidence"
    )
    raw_output: Optional[str] = Field(
        None, description="Raw output from the OCR provider"
    )
    output_format: OCROutputFormat = Field(..., description="Format of the OCR output")
    processing_time: float = Field(
        ..., description="Time taken to process the image (in seconds)"
    )
    error: Optional[str] = Field(None, description="Error message")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional provider-specific metadata"
    )


# Provider-specific models


class GoogleVisionOCRConfig(BaseModel):
    """
    Configuration for Google Cloud Vision OCR.

    Attributes:
        feature_type: Type of feature to detect (default: "TEXT_DETECTION")
        max_results: Maximum number of results to return
        model: Model to use for detection (default: "builtin/stable")
        language_hints: List of language hints
    """

    feature_type: str = Field(
        default="TEXT_DETECTION", description="Type of feature to detect"
    )
    max_results: Optional[int] = Field(
        default=None, description="Maximum number of results to return"
    )
    model: str = Field(
        default="builtin/stable", description="Model to use for detection"
    )
    language_hints: Optional[List[str]] = Field(
        default=None, description="List of language hints"
    )


class ABBYYOCRConfig(BaseModel):
    """
    Configuration for ABBYY OCR.

    Attributes:
        profile: Processing profile to use (default: "documentConversion")
        export_format: Format to export results in (default: "txt")
        description: Description of the processing task
        document_processing_params: Additional document processing parameters
    """

    profile: str = Field(
        default="documentConversion", description="Processing profile to use"
    )
    export_format: str = Field(default="txt", description="Format to export results in")
    description: Optional[str] = Field(
        default=None, description="Description of the processing task"
    )
    document_processing_params: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional document processing parameters"
    )
