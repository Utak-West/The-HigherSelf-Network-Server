"""
Configuration for MoneyPrinterTurbo integration.
"""

import os
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class MoneyPrinterConfig(BaseModel):
    """Configuration for MoneyPrinterTurbo integration."""
    
    # API connection
    api_url: str = Field(
        default="http://localhost:8080/api/v1",
        description="URL of the MoneyPrinterTurbo API"
    )
    
    # Default video settings
    default_language: str = Field(
        default="en",
        description="Default language for video generation (en or zh)"
    )
    default_voice: Optional[str] = Field(
        default="en-US-JennyNeural",
        description="Default voice for narration"
    )
    default_resolution: str = Field(
        default="1080x1920",
        description="Default video resolution (1080x1920 for portrait, 1920x1080 for landscape)"
    )
    default_clip_duration: int = Field(
        default=5,
        description="Default duration of each video clip in seconds"
    )
    
    # Subtitle settings
    default_subtitle_font: Optional[str] = Field(
        default=None,
        description="Default font for subtitles"
    )
    default_subtitle_position: str = Field(
        default="bottom",
        description="Default position of subtitles (top, middle, bottom)"
    )
    default_subtitle_color: str = Field(
        default="#FFFFFF",
        description="Default color of subtitles in hex format"
    )
    default_subtitle_size: int = Field(
        default=40,
        description="Default size of subtitle text"
    )
    default_subtitle_stroke_width: float = Field(
        default=1.5,
        description="Default width of subtitle text stroke/outline"
    )
    
    # Audio settings
    default_background_music_volume: float = Field(
        default=0.1,
        description="Default volume of background music (0.0-1.0)"
    )
    
    # API keys
    pexels_api_key: Optional[str] = Field(
        default=None,
        description="API key for Pexels (video source)"
    )
    pixabay_api_key: Optional[str] = Field(
        default=None,
        description="API key for Pixabay (video source)"
    )
    
    # LLM settings
    llm_provider: str = Field(
        default="openai",
        description="LLM provider for script generation"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="API key for OpenAI"
    )
    
    class Config:
        """Pydantic configuration."""
        env_prefix = "MONEYPRINTER_"


def get_config() -> MoneyPrinterConfig:
    """
    Get the MoneyPrinterTurbo configuration.
    
    Returns:
        MoneyPrinterConfig instance with values from environment variables
    """
    return MoneyPrinterConfig(
        api_url=os.environ.get("MONEYPRINTER_API_URL", "http://localhost:8080/api/v1"),
        default_language=os.environ.get("MONEYPRINTER_DEFAULT_LANGUAGE", "en"),
        default_voice=os.environ.get("MONEYPRINTER_DEFAULT_VOICE", "en-US-JennyNeural"),
        default_resolution=os.environ.get("MONEYPRINTER_DEFAULT_RESOLUTION", "1080x1920"),
        default_clip_duration=int(os.environ.get("MONEYPRINTER_DEFAULT_CLIP_DURATION", "5")),
        default_subtitle_font=os.environ.get("MONEYPRINTER_DEFAULT_SUBTITLE_FONT"),
        default_subtitle_position=os.environ.get("MONEYPRINTER_DEFAULT_SUBTITLE_POSITION", "bottom"),
        default_subtitle_color=os.environ.get("MONEYPRINTER_DEFAULT_SUBTITLE_COLOR", "#FFFFFF"),
        default_subtitle_size=int(os.environ.get("MONEYPRINTER_DEFAULT_SUBTITLE_SIZE", "40")),
        default_subtitle_stroke_width=float(os.environ.get("MONEYPRINTER_DEFAULT_SUBTITLE_STROKE_WIDTH", "1.5")),
        default_background_music_volume=float(os.environ.get("MONEYPRINTER_DEFAULT_BACKGROUND_MUSIC_VOLUME", "0.1")),
        pexels_api_key=os.environ.get("PEXELS_API_KEY"),
        pixabay_api_key=os.environ.get("PIXABAY_API_KEY"),
        llm_provider=os.environ.get("MONEYPRINTER_LLM_PROVIDER", "openai"),
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
