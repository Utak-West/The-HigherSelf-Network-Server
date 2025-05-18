"""
Tesseract OCR models for The HigherSelf Network Server.

These models define the data structures for OCR operations using Tesseract.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, HttpUrl


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


class OCRRequest(BaseModel):
    """
    Request model for OCR operations.
    
    Attributes:
        image_source: Type of image source (file, URL, base64, bytes)
        image_data: Image data or reference (path, URL, base64 string, or bytes)
        languages: List of languages to use for OCR (default: ["eng"])
        output_format: Format of the OCR output (default: "text")
        config: Additional Tesseract configuration options
        preprocessing: Whether to apply preprocessing to the image (default: True)
        page_segmentation_mode: Tesseract page segmentation mode (default: 3)
        ocr_engine_mode: Tesseract OCR engine mode (default: 3)
    """
    
    image_source: OCRImageSource = Field(..., description="Type of image source")
    image_data: Union[str, bytes] = Field(..., description="Image data or reference")
    languages: List[OCRLanguage] = Field(
        default=["eng"], 
        description="Languages to use for OCR"
    )
    output_format: OCROutputFormat = Field(
        default=OCROutputFormat.TEXT, 
        description="Format of the OCR output"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional Tesseract configuration options"
    )
    preprocessing: bool = Field(
        default=True, 
        description="Whether to apply preprocessing to the image"
    )
    page_segmentation_mode: int = Field(
        default=3, 
        description="Tesseract page segmentation mode"
    )
    ocr_engine_mode: int = Field(
        default=3, 
        description="Tesseract OCR engine mode"
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
        None, 
        description="Bounding box of the text element"
    )


class OCRResponse(BaseModel):
    """
    Response model for OCR operations.
    
    Attributes:
        success: Whether the OCR operation was successful
        text: Extracted text (if output_format is "text")
        elements: List of text elements with position and confidence
        raw_output: Raw output from Tesseract
        output_format: Format of the OCR output
        processing_time: Time taken to process the image (in seconds)
        error: Error message (if success is False)
    """
    
    success: bool = Field(..., description="Whether the OCR operation was successful")
    text: Optional[str] = Field(None, description="Extracted text")
    elements: Optional[List[OCRTextElement]] = Field(
        None, 
        description="List of text elements with position and confidence"
    )
    raw_output: Optional[str] = Field(None, description="Raw output from Tesseract")
    output_format: OCROutputFormat = Field(..., description="Format of the OCR output")
    processing_time: float = Field(..., description="Time taken to process the image (in seconds)")
    error: Optional[str] = Field(None, description="Error message")
