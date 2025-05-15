"""
Configuration for Hugging Face Pro integration with The HigherSelf Network.
Uses Pydantic for data validation and settings management.
"""
from pydantic import BaseModel, Field, HttpUrl, SecretStr
from typing import List, Optional, Dict, Any
from datetime import datetime


class HuggingFaceIntegrationConfig(BaseModel):
    """Configuration for Hugging Face Pro integration."""
    api_key: SecretStr
    organization: Optional[str] = None
    default_model_id: Optional[str] = None
    inference_endpoints: Dict[str, str] = Field(default_factory=dict)
    spaces_domain: str = "huggingface.co"
    default_space: Optional[str] = None
    
    class Config:
        """Pydantic configuration"""
        env_prefix = "HF_"


class NotionHuggingFaceConfig(BaseModel):
    """Configuration for Notion integration with Hugging Face."""
    notion_database_id: str
    huggingface_config: HuggingFaceIntegrationConfig
    history_log_enabled: bool = True
    sync_interval_minutes: int = 60
    last_sync_timestamp: Optional[datetime] = None
