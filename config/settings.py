"""
Configuration settings for The HigherSelf Network Server.

This module provides a centralized configuration system using Pydantic Settings,
with support for environment variables, .env files, and validation.
"""

import os
from typing import Dict, List, Optional, Union, Any
from enum import Enum
from dotenv import load_dotenv # Added

# Load .env file at the very beginning when this module is imported
load_dotenv() # Added

try:
    # Try to import from pydantic-settings first (Pydantic v2)
    from pydantic_settings import BaseSettings
    from pydantic import Field, field_validator, AnyHttpUrl # For Pydantic v2, validator is field_validator
    PYDANTIC_V2 = True
except ImportError:
    # Fall back to Pydantic v1
    from pydantic import BaseSettings, Field, validator, AnyHttpUrl
    PYDANTIC_V2 = False


class LogLevel(str, Enum):
    """Valid log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Valid deployment environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class NotionSettings(BaseSettings):
    """Notion API configuration."""
    api_token: str = Field(..., env="NOTION_API_TOKEN")
    parent_page_id: Optional[str] = Field(None, env="NOTION_PARENT_PAGE_ID")

    # Database IDs
    business_entities_db: Optional[str] = Field(None, env="NOTION_BUSINESS_ENTITIES_DB")
    contacts_profiles_db: Optional[str] = Field(None, env="NOTION_CONTACTS_PROFILES_DB")
    community_hub_db: Optional[str] = Field(None, env="NOTION_COMMUNITY_HUB_DB")
    products_services_db: Optional[str] = Field(None, env="NOTION_PRODUCTS_SERVICES_DB")
    active_workflow_instances_db: Optional[str] = Field(None, env="NOTION_ACTIVE_WORKFLOW_INSTANCES_DB")
    marketing_campaigns_db: Optional[str] = Field(None, env="NOTION_MARKETING_CAMPAIGNS_DB")
    feedback_surveys_db: Optional[str] = Field(None, env="NOTION_FEEDBACK_SURVEYS_DB")
    rewards_bounties_db: Optional[str] = Field(None, env="NOTION_REWARDS_BOUNTIES_DB")
    tasks_db: Optional[str] = Field(None, env="NOTION_TASKS_DB")
    agent_communication_db: Optional[str] = Field(None, env="NOTION_AGENT_COMMUNICATION_DB")
    agent_registry_db: Optional[str] = Field(None, env="NOTION_AGENT_REGISTRY_DB")
    api_integrations_db: Optional[str] = Field(None, env="NOTION_API_INTEGRATIONS_DB")
    data_transformations_db: Optional[str] = Field(None, env="NOTION_DATA_TRANSFORMATIONS_DB")
    notifications_templates_db: Optional[str] = Field(None, env="NOTION_NOTIFICATIONS_TEMPLATES_DB")
    use_cases_db: Optional[str] = Field(None, env="NOTION_USE_CASES_DB")
    workflows_library_db: Optional[str] = Field(None, env="NOTION_WORKFLOWS_LIBRARY_DB")

    if PYDANTIC_V2:
        @field_validator('api_token')
        def validate_api_token(cls, v):
            """Validate Notion API token."""
            if not v or len(v) < 10:
                raise ValueError("Invalid Notion API token")
            return v
    else:
        @validator('api_token')
        def validate_api_token(cls, v):
            """Validate Notion API token."""
            if not v or len(v) < 10:
                raise ValueError("Invalid Notion API token")
            return v

    def get_database_mappings(self) -> Dict[str, str]:
        """Get database mappings for Notion service."""
        return {
            "BusinessEntity": self.business_entities_db,
            "ContactProfile": self.contacts_profiles_db,
            "CommunityMember": self.community_hub_db,
            "ProductService": self.products_services_db,
            "WorkflowInstance": self.active_workflow_instances_db,
            "MarketingCampaign": self.marketing_campaigns_db,
            "FeedbackSurvey": self.feedback_surveys_db,
            "RewardBounty": self.rewards_bounties_db,
            "Task": self.tasks_db,
            "AgentCommunication": self.agent_communication_db,
            "Agent": self.agent_registry_db,
            "ApiIntegration": self.api_integrations_db,
            "DataTransformation": self.data_transformations_db,
            "NotificationTemplate": self.notifications_templates_db,
            "UseCase": self.use_cases_db,
            "Workflow": self.workflows_library_db,
        }


class ServerSettings(BaseSettings):
    """Server configuration."""
    host: str = Field("0.0.0.0", env="SERVER_HOST")
    port: int = Field(8000, env="SERVER_PORT")
    reload: bool = Field(False, env="SERVER_RELOAD")
    workers: int = Field(1, env="SERVER_WORKERS")
    log_level: LogLevel = Field(LogLevel.INFO, env="LOG_LEVEL")
    json_logs: bool = Field(False, env="JSON_LOGS")
    log_file: Optional[str] = Field("logs/app.log", env="LOG_FILE")
    webhook_secret: str = Field(..., env="WEBHOOK_SECRET")

    if PYDANTIC_V2:
        @field_validator('port')
        def validate_port(cls, v):
            """Validate port number."""
            if not 1024 <= v <= 65535:
                raise ValueError("Port must be between 1024 and 65535")
            return v
    else:
        @validator('port')
        def validate_port(cls, v):
            """Validate port number."""
            if not 1024 <= v <= 65535:
                raise ValueError("Port must be between 1024 and 65535")
            return v


class IntegrationSettings(BaseSettings):
    """Third-party integration configuration."""
    # Integration toggles
    enable_typeform: bool = Field(True, env="ENABLE_TYPEFORM")
    enable_woocommerce: bool = Field(True, env="ENABLE_WOOCOMMERCE")
    enable_acuity: bool = Field(True, env="ENABLE_ACUITY")
    enable_amelia: bool = Field(True, env="ENABLE_AMELIA")
    enable_user_feedback: bool = Field(True, env="ENABLE_USER_FEEDBACK")
    enable_tutor_lm: bool = Field(True, env="ENABLE_TUTOR_LM")
    enable_ai_providers: bool = Field(True, env="ENABLE_AI_PROVIDERS")
    enable_airtable: bool = Field(True, env="ENABLE_AIRTABLE")
    enable_snovio: bool = Field(True, env="ENABLE_SNOVIO")
    enable_plaud: bool = Field(True, env="ENABLE_PLAUD")
    enable_beehiiv: bool = Field(True, env="ENABLE_BEEHIIV")
    enable_circle: bool = Field(True, env="ENABLE_CIRCLE")

    # API credentials
    typeform_api_key: Optional[str] = Field(None, env="TYPEFORM_API_KEY")
    woocommerce_consumer_key: Optional[str] = Field(None, env="WOOCOMMERCE_CONSUMER_KEY")
    woocommerce_consumer_secret: Optional[str] = Field(None, env="WOOCOMMERCE_CONSUMER_SECRET")
    woocommerce_url: Optional[AnyHttpUrl] = Field(None, env="WOOCOMMERCE_URL")
    acuity_user_id: Optional[str] = Field(None, env="ACUITY_USER_ID")
    acuity_api_key: Optional[str] = Field(None, env="ACUITY_API_KEY")
    amelia_api_key: Optional[str] = Field(None, env="AMELIA_API_KEY")
    amelia_endpoint: Optional[AnyHttpUrl] = Field(None, env="AMELIA_ENDPOINT")
    airtable_api_key: Optional[str] = Field(None, env="AIRTABLE_API_KEY")
    airtable_base_id: Optional[str] = Field(None, env="AIRTABLE_BASE_ID")
    snovio_api_key: Optional[str] = Field(None, env="SNOVIO_API_KEY")
    plaud_api_key: Optional[str] = Field(None, env="PLAUD_API_KEY")
    beehiiv_api_key: Optional[str] = Field(None, env="BEEHIIV_API_KEY")
    beehiiv_publication_id: Optional[str] = Field(None, env="BEEHIIV_PUBLICATION_ID")
    circle_api_token: Optional[str] = Field(None, env="CIRCLE_API_TOKEN")
    circle_community_id: Optional[str] = Field(None, env="CIRCLE_COMMUNITY_ID")

    # AI provider credentials
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_organization_id: Optional[str] = Field(None, env="OPENAI_ORGANIZATION_ID")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    tutorlm_api_key: Optional[str] = Field(None, env="TUTORLM_API_KEY")


class Settings(BaseSettings):
    """Main application settings."""
    environment: Environment = Field(Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    testing: bool = Field(False, env="TESTING")
    disable_webhooks: bool = Field(False, env="DISABLE_WEBHOOKS")

    # Component settings - don't initialize here for Pydantic v2
    notion: NotionSettings = Field(default_factory=NotionSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    integrations: IntegrationSettings = Field(default_factory=IntegrationSettings)

    if PYDANTIC_V2:
        model_config = {
            "env_file": ".env",
            "env_file_encoding": "utf-8",
            "case_sensitive": True,
            "extra": "ignore"
        }
    else:
        class Config:
            """Pydantic configuration."""
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = True
            extra = "ignore"


# Create global settings instance
settings = Settings()


# Function to reload settings (useful after environment changes)
def reload_settings():
    """Reload settings from environment variables and .env file."""
    global settings
    settings = Settings()
    return settings
