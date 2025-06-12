"""
Configuration settings for The HigherSelf Network Server.

This module provides a centralized configuration system using Pydantic Settings,
with support for environment variables, .env files, and validation.
"""

import os
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv  # Added

# Load .env file at the very beginning when this module is imported
load_dotenv()  # Added

# Since we're now using Pydantic v1 as specified in requirements.txt
from pydantic import AnyHttpUrl, BaseSettings, Field, field_validator

# Explicitly set to False since we're using Pydantic v1
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

    @property
    def is_token_valid(self) -> bool:
        """Check if the API token appears to be properly formatted."""
        return (
            self.api_token and len(self.api_token) >= 50
        )  # Notion tokens are typically very long

    parent_page_id: Optional[str] = Field(None, env="NOTION_PARENT_PAGE_ID")

    # Database IDs
    business_entities_db: Optional[str] = Field(None, env="NOTION_BUSINESS_ENTITIES_DB")
    contacts_profiles_db: Optional[str] = Field(None, env="NOTION_CONTACTS_PROFILES_DB")
    community_hub_db: Optional[str] = Field(None, env="NOTION_COMMUNITY_HUB_DB")
    products_services_db: Optional[str] = Field(None, env="NOTION_PRODUCTS_SERVICES_DB")
    active_workflow_instances_db: Optional[str] = Field(
        None, env="NOTION_ACTIVE_WORKFLOW_INSTANCES_DB"
    )
    marketing_campaigns_db: Optional[str] = Field(
        None, env="NOTION_MARKETING_CAMPAIGNS_DB"
    )
    feedback_surveys_db: Optional[str] = Field(None, env="NOTION_FEEDBACK_SURVEYS_DB")
    rewards_bounties_db: Optional[str] = Field(None, env="NOTION_REWARDS_BOUNTIES_DB")
    tasks_db: Optional[str] = Field(None, env="NOTION_TASKS_DB")
    agent_communication_db: Optional[str] = Field(
        None, env="NOTION_AGENT_COMMUNICATION_DB"
    )
    agent_registry_db: Optional[str] = Field(None, env="NOTION_AGENT_REGISTRY_DB")
    api_integrations_db: Optional[str] = Field(None, env="NOTION_API_INTEGRATIONS_DB")
    data_transformations_db: Optional[str] = Field(
        None, env="NOTION_DATA_TRANSFORMATIONS_DB"
    )
    notifications_templates_db: Optional[str] = Field(
        None, env="NOTION_NOTIFICATIONS_TEMPLATES_DB"
    )
    use_cases_db: Optional[str] = Field(None, env="NOTION_USE_CASES_DB")
    workflows_library_db: Optional[str] = Field(None, env="NOTION_WORKFLOWS_LIBRARY_DB")

    if PYDANTIC_V2:
        # This code will not be used since PYDANTIC_V2 is False
        @field_validator("api_token")
        def validate_api_token(cls, v):
            """Validate Notion API token."""
            if not v or len(v) < 50:
                raise ValueError(
                    "Invalid Notion API token - must be at least 50 characters"
                )
            return v

    else:

        @field_validator("api_token")
        def validate_api_token(cls, v):
            """Validate Notion API token."""
            if not v or len(v) < 50:
                raise ValueError(
                    "Invalid Notion API token - must be at least 50 characters"
                )
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
    workers: int = Field(
        2, env="SERVER_WORKERS"
    )  # Optimized for 4-core SiteGround plan
    log_level: LogLevel = Field(LogLevel.INFO, env="LOG_LEVEL")
    json_logs: bool = Field(False, env="JSON_LOGS")
    log_file: Optional[str] = Field("logs/app.log", env="LOG_FILE")
    webhook_secret: str = Field(..., env="WEBHOOK_SECRET")

    if PYDANTIC_V2:

        @field_validator("port")
        def validate_port(cls, v):
            """Validate port number."""
            if not 1024 <= v <= 65535:
                raise ValueError("Port must be between 1024 and 65535")
            return v

    else:

        @field_validator("port")
        def validate_port(cls, v):
            """Validate port number."""
            if not 1024 <= v <= 65535:
                raise ValueError("Port must be between 1024 and 65535")
            return v


class RedisSettings(BaseSettings):
    """Redis configuration for HigherSelf Network Server.

    Supports both local Redis instances and Redis Cloud deployments
    with comprehensive connection management and security features.
    """

    # Connection settings
    uri: str = Field(default="redis://localhost:6379/0", env="REDIS_URI")
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    database: int = Field(default=0, env="REDIS_DATABASE")
    password: Optional[str] = Field(default="", env="REDIS_PASSWORD")
    username: Optional[str] = Field(default="default", env="REDIS_USERNAME")

    # Connection pool settings - Optimized for SiteGround
    max_connections: int = Field(default=8, env="REDIS_MAX_CONNECTIONS")
    timeout: int = Field(default=5, env="REDIS_TIMEOUT")
    socket_connect_timeout: int = Field(default=5, env="REDIS_SOCKET_CONNECT_TIMEOUT")
    socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")
    health_check_interval: int = Field(default=30, env="REDIS_HEALTH_CHECK_INTERVAL")

    # Security settings
    ssl_enabled: bool = Field(default=False, env="REDIS_SSL")
    ssl_cert_reqs: str = Field(default="required", env="REDIS_SSL_CERT_REQS")
    ssl_ca_certs: Optional[str] = Field(default=None, env="REDIS_SSL_CA_CERTS")
    ssl_certfile: Optional[str] = Field(default=None, env="REDIS_SSL_CERTFILE")
    ssl_keyfile: Optional[str] = Field(default=None, env="REDIS_SSL_KEYFILE")

    # Feature flags
    cache_enabled: bool = Field(default=True, env="REDIS_CACHE_ENABLED")
    pubsub_enabled: bool = Field(default=True, env="REDIS_PUBSUB_ENABLED")
    session_store_enabled: bool = Field(default=True, env="REDIS_SESSION_STORE_ENABLED")
    rate_limiting_enabled: bool = Field(default=True, env="REDIS_RATE_LIMITING_ENABLED")

    # Performance settings
    retry_on_timeout: bool = Field(default=True, env="REDIS_RETRY_ON_TIMEOUT")
    retry_on_error: bool = Field(default=True, env="REDIS_RETRY_ON_ERROR")
    max_retries: int = Field(default=3, env="REDIS_MAX_RETRIES")
    retry_delay: float = Field(default=0.5, env="REDIS_RETRY_DELAY")

    # Monitoring settings
    metrics_enabled: bool = Field(default=True, env="REDIS_METRICS_ENABLED")
    slow_query_threshold: float = Field(default=1.0, env="REDIS_SLOW_QUERY_THRESHOLD")

    if PYDANTIC_V2:

        @field_validator("timeout", "socket_connect_timeout", "socket_timeout")
        def validate_timeout_values(cls, v):
            """Validate timeout values."""
            if v < 1:
                raise ValueError("Timeout must be at least 1 second")
            return v

        @field_validator("port")
        def validate_port(cls, v):
            """Validate port number."""
            if not 1 <= v <= 65535:
                raise ValueError("Port must be between 1 and 65535")
            return v

        @field_validator("max_connections")
        def validate_max_connections(cls, v):
            """Validate max connections."""
            if v < 1:
                raise ValueError("Max connections must be at least 1")
            return v

        @field_validator("max_retries")
        def validate_max_retries(cls, v):
            """Validate max retries."""
            if v < 0:
                raise ValueError("Max retries cannot be negative")
            return v

    else:

        @field_validator("timeout", "socket_connect_timeout", "socket_timeout")
        def validate_timeout_values(cls, v):
            """Validate timeout values."""
            if v < 1:
                raise ValueError("Timeout must be at least 1 second")
            return v

        @field_validator("port")
        def validate_port(cls, v):
            """Validate port number."""
            if not 1 <= v <= 65535:
                raise ValueError("Port must be between 1 and 65535")
            return v

        @field_validator("max_connections")
        def validate_max_connections(cls, v):
            """Validate max connections."""
            if v < 1:
                raise ValueError("Max connections must be at least 1")
            return v

        @field_validator("max_retries")
        def validate_max_retries(cls, v):
            """Validate max retries."""
            if v < 0:
                raise ValueError("Max retries cannot be negative")
            return v

    def get_connection_url(self) -> str:
        """Generate Redis connection URL from individual components."""
        if self.uri and self.uri != "redis://localhost:6379/0":
            return self.uri

        # Build URL from components
        scheme = "rediss" if self.ssl_enabled else "redis"
        auth = ""
        if self.password:
            if self.username and self.username != "default":
                auth = f"{self.username}:{self.password}@"
            else:
                auth = f":{self.password}@"

        return f"{scheme}://{auth}{self.host}:{self.port}/{self.database}"

    def get_connection_kwargs(self) -> Dict[str, Any]:
        """Get connection kwargs for Redis client."""
        kwargs = {
            "decode_responses": True,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "max_connections": self.max_connections,
            "health_check_interval": self.health_check_interval,
            "retry_on_timeout": self.retry_on_timeout,
            "retry_on_error": self.retry_on_error,
        }

        if self.password:
            kwargs["password"] = self.password

        if self.username and self.username != "default":
            kwargs["username"] = self.username

        if self.ssl_enabled:
            kwargs["ssl"] = True
            kwargs["ssl_cert_reqs"] = self.ssl_cert_reqs
            if self.ssl_ca_certs:
                kwargs["ssl_ca_certs"] = self.ssl_ca_certs
            if self.ssl_certfile:
                kwargs["ssl_certfile"] = self.ssl_certfile
            if self.ssl_keyfile:
                kwargs["ssl_keyfile"] = self.ssl_keyfile

        return kwargs


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
    enable_redis: bool = Field(True, env="ENABLE_REDIS")
    enable_gohighlevel: bool = Field(True, env="ENABLE_GOHIGHLEVEL")

    # API credentials
    typeform_api_key: Optional[str] = Field(None, env="TYPEFORM_API_KEY")
    woocommerce_consumer_key: Optional[str] = Field(
        None, env="WOOCOMMERCE_CONSUMER_KEY"
    )
    woocommerce_consumer_secret: Optional[str] = Field(
        None, env="WOOCOMMERCE_CONSUMER_SECRET"
    )
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

    # GoHighLevel CRM credentials
    gohighlevel_client_id: Optional[str] = Field(None, env="GOHIGHLEVEL_CLIENT_ID")
    gohighlevel_client_secret: Optional[str] = Field(
        None, env="GOHIGHLEVEL_CLIENT_SECRET"
    )
    gohighlevel_redirect_uri: Optional[str] = Field(
        None, env="GOHIGHLEVEL_REDIRECT_URI"
    )
    gohighlevel_webhook_secret: Optional[str] = Field(
        None, env="GOHIGHLEVEL_WEBHOOK_SECRET"
    )
    gohighlevel_scope: str = Field(
        "contacts.read contacts.write opportunities.read opportunities.write campaigns.read campaigns.write calendars.read calendars.write",
        env="GOHIGHLEVEL_SCOPE",
    )

    # GoHighLevel Sub-Account Tokens
    gohighlevel_core_business_token: Optional[str] = Field(
        None, env="GOHIGHLEVEL_CORE_BUSINESS_TOKEN"
    )
    gohighlevel_home_services_token: Optional[str] = Field(
        None, env="GOHIGHLEVEL_HOME_SERVICES_TOKEN"
    )
    gohighlevel_extended_wellness_token: Optional[str] = Field(
        None, env="GOHIGHLEVEL_EXTENDED_WELLNESS_TOKEN"
    )
    gohighlevel_development_token: Optional[str] = Field(
        None, env="GOHIGHLEVEL_DEVELOPMENT_TOKEN"
    )
    gohighlevel_analytics_token: Optional[str] = Field(
        None, env="GOHIGHLEVEL_ANALYTICS_TOKEN"
    )

    # GoHighLevel Sub-Account Location IDs
    gohighlevel_core_business_location: Optional[str] = Field(
        None, env="GOHIGHLEVEL_CORE_BUSINESS_LOCATION"
    )
    gohighlevel_home_services_location: Optional[str] = Field(
        None, env="GOHIGHLEVEL_HOME_SERVICES_LOCATION"
    )
    gohighlevel_extended_wellness_location: Optional[str] = Field(
        None, env="GOHIGHLEVEL_EXTENDED_WELLNESS_LOCATION"
    )
    gohighlevel_development_location: Optional[str] = Field(
        None, env="GOHIGHLEVEL_DEVELOPMENT_LOCATION"
    )
    gohighlevel_analytics_location: Optional[str] = Field(
        None, env="GOHIGHLEVEL_ANALYTICS_LOCATION"
    )

    # GoHighLevel CRM credentials
    gohighlevel_client_id: Optional[str] = Field(None, env="GOHIGHLEVEL_CLIENT_ID")
    gohighlevel_client_secret: Optional[str] = Field(
        None, env="GOHIGHLEVEL_CLIENT_SECRET"
    )
    gohighlevel_redirect_uri: Optional[str] = Field(
        None, env="GOHIGHLEVEL_REDIRECT_URI"
    )
    gohighlevel_webhook_secret: Optional[str] = Field(
        None, env="GOHIGHLEVEL_WEBHOOK_SECRET"
    )
    gohighlevel_access_token: Optional[str] = Field(
        None, env="GOHIGHLEVEL_ACCESS_TOKEN"
    )
    gohighlevel_refresh_token: Optional[str] = Field(
        None, env="GOHIGHLEVEL_REFRESH_TOKEN"
    )
    gohighlevel_location_id: Optional[str] = Field(None, env="GOHIGHLEVEL_LOCATION_ID")
    gohighlevel_scope: str = Field(
        "contacts.read contacts.write opportunities.read opportunities.write campaigns.read campaigns.write",
        env="GOHIGHLEVEL_SCOPE",
    )


class Settings(BaseSettings):
    """Main application settings."""

    environment: Environment = Field(Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    testing: bool = Field(False, env="TESTING")
    disable_webhooks: bool = Field(False, env="DISABLE_WEBHOOKS")

    def log_configuration_status(self):
        """Log configuration status for debugging purposes."""
        from loguru import logger

        logger.info(f"Environment: {self.environment.value}")
        logger.info(f"Debug mode: {self.debug}")
        logger.info(f"Testing mode: {self.testing}")

        # Check Notion configuration
        logger.info(f"Notion API token present: {bool(self.notion.api_token)}")
        if self.notion.api_token:
            # Only log a truncated version for security
            masked_token = (
                self.notion.api_token[:4] + "..." + self.notion.api_token[-4:]
                if len(self.notion.api_token) > 8
                else "***"
            )
            logger.info(f"Notion API token (masked): {masked_token}")
            logger.info(
                f"Notion API token appears valid by length: {self.notion.is_token_valid}"
            )

        # Log database mappings availability
        db_mappings = self.notion.get_database_mappings()
        for model_name, db_id in db_mappings.items():
            if not db_id:
                logger.warning(f"Missing database ID for {model_name}")

    # Component settings - don't initialize here for Pydantic v2
    notion: NotionSettings = Field(default_factory=NotionSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    integrations: IntegrationSettings = Field(default_factory=IntegrationSettings)

    if PYDANTIC_V2:
        model_config = {
            "env_file": ".env",
            "env_file_encoding": "utf-8",
            "case_sensitive": True,
            "extra": "ignore",
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

# Log settings on module import for debugging
from loguru import logger

logger.info("Configuration settings loaded")
try:
    settings.log_configuration_status()
except Exception as e:
    logger.error(f"Error logging configuration status: {e}")


# Function to reload settings (useful after environment changes)
def reload_settings():
    """Reload settings from environment variables and .env file."""
    global settings
    settings = Settings()
    return settings
