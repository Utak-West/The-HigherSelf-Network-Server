"""
Utilities for Hugging Face Pro integration with The HigherSelf Network.
"""
from typing import Optional, Dict, Any, Union
import os
from pydantic import SecretStr
from loguru import logger

from notion_client import Client

from .config import HuggingFaceIntegrationConfig, NotionHuggingFaceConfig
from .service import HuggingFaceService
from .notion_sync import NotionHuggingFaceSync

def load_huggingface_config_from_env() -> HuggingFaceIntegrationConfig:
    """
    Load Hugging Face configuration from environment variables.
    
    Environment variables:
    - HF_API_KEY: Hugging Face API key
    - HF_ORGANIZATION: (Optional) Hugging Face organization
    - HF_DEFAULT_MODEL_ID: (Optional) Default model ID to use
    
    Returns:
        HuggingFaceIntegrationConfig object
    """
    api_key = os.environ.get("HF_API_KEY")
    if not api_key:
        raise ValueError("HF_API_KEY environment variable is required for Hugging Face integration")
    
    organization = os.environ.get("HF_ORGANIZATION")
    default_model_id = os.environ.get("HF_DEFAULT_MODEL_ID")
    
    # Get inference endpoints from environment
    inference_endpoints = {}
    for key, value in os.environ.items():
        if key.startswith("HF_ENDPOINT_"):
            endpoint_name = key[12:].lower()  # Remove HF_ENDPOINT_ prefix
            inference_endpoints[endpoint_name] = value
    
    return HuggingFaceIntegrationConfig(
        api_key=SecretStr(api_key),
        organization=organization,
        default_model_id=default_model_id,
        inference_endpoints=inference_endpoints
    )

def load_notion_huggingface_config_from_env() -> NotionHuggingFaceConfig:
    """
    Load Notion-Hugging Face integration configuration from environment variables.
    
    Environment variables:
    - NOTION_HF_DATABASE_ID: Notion database ID for Hugging Face resources
    - HF_* variables for Hugging Face configuration
    - NOTION_HF_SYNC_INTERVAL: (Optional) Sync interval in minutes
    - NOTION_HF_HISTORY_LOG: (Optional) Enable/disable history logging
    
    Returns:
        NotionHuggingFaceConfig object
    """
    database_id = os.environ.get("NOTION_HF_DATABASE_ID")
    if not database_id:
        raise ValueError("NOTION_HF_DATABASE_ID environment variable is required for Hugging Face-Notion integration")
    
    hf_config = load_huggingface_config_from_env()
    
    # Optional configuration
    sync_interval = os.environ.get("NOTION_HF_SYNC_INTERVAL")
    history_log = os.environ.get("NOTION_HF_HISTORY_LOG", "true").lower() in ("true", "1", "yes")
    
    return NotionHuggingFaceConfig(
        notion_database_id=database_id,
        huggingface_config=hf_config,
        sync_interval_minutes=int(sync_interval) if sync_interval else 60,
        history_log_enabled=history_log
    )

def create_huggingface_service() -> HuggingFaceService:
    """
    Create and initialize a Hugging Face service instance.
    
    Returns:
        Initialized HuggingFaceService
    """
    config = load_huggingface_config_from_env()
    return HuggingFaceService(config)

def create_notion_sync(notion_client: Client) -> NotionHuggingFaceSync:
    """
    Create and initialize a Notion synchronization service.
    
    Args:
        notion_client: Authenticated Notion client
        
    Returns:
        Initialized NotionHuggingFaceSync
    """
    config = load_notion_huggingface_config_from_env()
    hf_service = HuggingFaceService(config.huggingface_config)
    
    return NotionHuggingFaceSync(notion_client, hf_service, config)
