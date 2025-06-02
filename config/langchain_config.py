"""
LangChain configuration for The HigherSelf Network Server.
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field

class LangChainConfig(BaseSettings):
    """Configuration for LangChain integration."""
    
    # Model configurations
    default_model: str = Field(default="gpt-3.5-turbo", env="LANGCHAIN_DEFAULT_MODEL")
    fallback_model: str = Field(default="gpt-3.5-turbo", env="LANGCHAIN_FALLBACK_MODEL")
    
    # API keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Performance settings
    max_retries: int = Field(default=3, env="LANGCHAIN_MAX_RETRIES")
    timeout: int = Field(default=30, env="LANGCHAIN_TIMEOUT")
    max_concurrent_requests: int = Field(default=10, env="LANGCHAIN_MAX_CONCURRENT")
    
    # Caching
    enable_caching: bool = Field(default=True, env="LANGCHAIN_ENABLE_CACHING")
    cache_ttl: int = Field(default=3600, env="LANGCHAIN_CACHE_TTL")
    
    # Vector store
    vector_store_path: str = Field(default="./vector_store", env="LANGCHAIN_VECTOR_STORE_PATH")
    embedding_model: str = Field(default="text-embedding-ada-002", env="LANGCHAIN_EMBEDDING_MODEL")
    
    # Memory settings
    memory_max_tokens: int = Field(default=2000, env="LANGCHAIN_MEMORY_MAX_TOKENS")
    conversation_ttl: int = Field(default=86400, env="LANGCHAIN_CONVERSATION_TTL")  # 24 hours
    
    # Security settings
    max_input_length: int = Field(default=10000, env="LANGCHAIN_MAX_INPUT_LENGTH")
    enable_input_validation: bool = Field(default=True, env="LANGCHAIN_ENABLE_INPUT_VALIDATION")
    enable_output_filtering: bool = Field(default=True, env="LANGCHAIN_ENABLE_OUTPUT_FILTERING")
    
    # Agent settings
    max_iterations: int = Field(default=5, env="LANGCHAIN_MAX_ITERATIONS")
    max_execution_time: int = Field(default=60, env="LANGCHAIN_MAX_EXECUTION_TIME")
    
    # Database IDs (should be moved to environment variables)
    contacts_database_id: str = Field(default="", env="NOTION_CONTACTS_DB_ID")
    workflows_database_id: str = Field(default="", env="NOTION_WORKFLOWS_DB_ID")
    tasks_database_id: str = Field(default="", env="NOTION_TASKS_DB_ID")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def validate_config(self) -> bool:
        """Validate configuration settings."""
        if not self.openai_api_key and not self.anthropic_api_key:
            raise ValueError("At least one LLM API key must be provided")
        
        if self.max_iterations <= 0:
            raise ValueError("max_iterations must be positive")
        
        if self.max_execution_time <= 0:
            raise ValueError("max_execution_time must be positive")
        
        return True

# Global configuration instance
langchain_config = LangChainConfig()

# Validate on import
try:
    langchain_config.validate_config()
except ValueError as e:
    print(f"Warning: LangChain configuration validation failed: {e}")
