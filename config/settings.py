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

# Using Pydantic v2 with pydantic-settings
from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Set to True since we're using Pydantic v2
PYDANTIC_V2 = True


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

    api_token: str = Field(..., description="Notion API token")

    @property
    def is_token_valid(self) -> bool:
        """Check if the API token appears to be properly formatted."""
        return (
            self.api_token and len(self.api_token) >= 50
        )  # Notion tokens are typically very long

    parent_page_id: Optional[str] = Field(None, description="Parent page ID for database creation")

    # Database IDs
    business_entities_db: Optional[str] = Field(None, description="Business entities database ID")
    contacts_profiles_db: Optional[str] = Field(None, description="Contacts profiles database ID")
    community_hub_db: Optional[str] = Field(None, description="Community hub database ID")
    products_services_db: Optional[str] = Field(None, description="Products services database ID")
    active_workflow_instances_db: Optional[str] = Field(
        None, description="Active workflow instances database ID"
    )
    marketing_campaigns_db: Optional[str] = Field(
        None, description="Marketing campaigns database ID"
    )
    feedback_surveys_db: Optional[str] = Field(None, description="Feedback surveys database ID")
    rewards_bounties_db: Optional[str] = Field(None, description="Rewards bounties database ID")
    tasks_db: Optional[str] = Field(None, description="Tasks database ID")
    agent_communication_db: Optional[str] = Field(
        None, description="Agent communication database ID"
    )
    agent_registry_db: Optional[str] = Field(None, description="Agent registry database ID")
    api_integrations_db: Optional[str] = Field(None, description="API integrations database ID")
    data_transformations_db: Optional[str] = Field(
        None, description="Data transformations database ID"
    )
    notifications_templates_db: Optional[str] = Field(
        None, description="Notifications templates database ID"
    )
    use_cases_db: Optional[str] = Field(None, description="Use cases database ID")
    workflows_library_db: Optional[str] = Field(None, description="Workflows library database ID")

    model_config = SettingsConfigDict(
        env_prefix="NOTION_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    @field_validator("api_token")
    @classmethod
    def validate_api_token(cls, v):
        """Validate Notion API token."""
        if not v:
            import os
            if os.environ.get("TEST_MODE", "").lower() == "true" or os.environ.get("TESTING_MODE", "").lower() == "true":
                return "test_token_12345678901234567890123456789012345678901234567890"
            raise ValueError("Notion API token is required")
        if len(v) < 50:
            raise ValueError("Invalid Notion API token - must be at least 50 characters")
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

    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    reload: bool = Field(False, description="Server reload")
    workers: int = Field(2, description="Server workers")  # Optimized for 4-core SiteGround plan
    log_level: LogLevel = Field(LogLevel.INFO, description="Log level")
    json_logs: bool = Field(False, description="JSON logs")
    log_file: Optional[str] = Field("logs/app.log", description="Log file")
    webhook_secret: str = Field(..., description="Webhook secret")

    model_config = SettingsConfigDict(
        env_prefix="SERVER_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    @field_validator("port")
    @classmethod
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
    uri: str = Field(default="redis://localhost:6379/0", description="Redis URI")
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    database: int = Field(default=0, description="Redis database")
    password: Optional[str] = Field(default="", description="Redis password")
    username: Optional[str] = Field(default="default", description="Redis username")

    # Connection pool settings - Optimized for SiteGround
    max_connections: int = Field(default=8, description="Redis max connections")
    timeout: int = Field(default=5, description="Redis timeout")
    socket_connect_timeout: int = Field(default=5, description="Redis socket connect timeout")
    socket_timeout: int = Field(default=5, description="Redis socket timeout")
    health_check_interval: int = Field(default=30, description="Redis health check interval")

    # Security settings
    ssl_enabled: bool = Field(default=False, description="Redis SSL enabled")
    ssl_cert_reqs: str = Field(default="required", description="Redis SSL cert reqs")
    ssl_ca_certs: Optional[str] = Field(default=None, description="Redis SSL CA certs")
    ssl_certfile: Optional[str] = Field(default=None, description="Redis SSL cert file")
    ssl_keyfile: Optional[str] = Field(default=None, description="Redis SSL key file")

    # Feature flags
    cache_enabled: bool = Field(default=True, description="Redis cache enabled")
    pubsub_enabled: bool = Field(default=True, description="Redis pubsub enabled")
    session_store_enabled: bool = Field(default=True, description="Redis session store enabled")
    rate_limiting_enabled: bool = Field(default=True, description="Redis rate limiting enabled")

    # Performance settings
    retry_on_timeout: bool = Field(default=True, description="Redis retry on timeout")
    retry_on_error: bool = Field(default=True, description="Redis retry on error")
    max_retries: int = Field(default=3, description="Redis max retries")
    retry_delay: float = Field(default=0.5, description="Redis retry delay")

    # Monitoring settings
    metrics_enabled: bool = Field(default=True, description="Redis metrics enabled")
    slow_query_threshold: float = Field(default=1.0, description="Redis slow query threshold")

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    @field_validator("timeout", "socket_connect_timeout", "socket_timeout")
    @classmethod
    def validate_timeout_values(cls, v):
        """Validate timeout values."""
        if v < 1:
            raise ValueError("Timeout must be at least 1 second")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        """Validate port number."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("max_connections")
    @classmethod
    def validate_max_connections(cls, v):
        """Validate max connections."""
        if v < 1:
            raise ValueError("Max connections must be at least 1")
        return v

    @field_validator("max_retries")
    @classmethod
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


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
