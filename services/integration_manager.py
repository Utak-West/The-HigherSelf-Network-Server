"""
Integration Manager for The HigherSelf Network Server.
This service coordinates all third-party integrations and ensures Notion remains the central hub.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

from loguru import logger
from pydantic import BaseModel

from config.settings import settings as global_settings  # Added
from models.notion import NotionIntegrationConfig  # Added
from services.acuity_service import AcuityService
from services.ai_provider_service import AIProviderService
from services.airtable_service import AirtableService
from services.amelia_service import AmeliaServiceClient as AmeliaService

# Import base service
from services.base_service import BaseService
from services.bettermode_service import BetterModeService
from services.capcut_service import CapCutService
from services.huggingface_service import HuggingFaceService

# Import service classes
from services.notion_service import NotionService
from services.pipit_service import PipitService
from services.plaud_service import PlaudService
from services.snovio_service import SnovIOService  # Corrected import
from services.softr_service import SoftrService
from services.tutor_lm_service import TutorLMService
from services.tutorlm_service import TutorLMService as LegacyTutorLMService
from services.typeform_service import TypeFormService
from services.user_feedback_service import UserFeedbackService
from services.userfeedback_service import (
    UserFeedbackService as LegacyUserFeedbackService,
)
from services.woocommerce_service import WooCommerceService

# Singleton instance of the IntegrationManager
_integration_manager = None


# Function to get or create the IntegrationManager instance
async def get_integration_manager() -> "IntegrationManager":
    """
    Get or create a singleton instance of the IntegrationManager.

    Returns:
        IntegrationManager: The singleton instance of the integration manager
    """
    global _integration_manager

    if _integration_manager is None:
        _integration_manager = IntegrationManager()
        await _integration_manager.initialize()

    return _integration_manager


class IntegrationManagerConfig(BaseModel):
    """Configuration for the Integration Manager."""

    notion_api_token: str
    enable_typeform: bool = True
    enable_woocommerce: bool = True
    enable_acuity: bool = True
    enable_amelia: bool = True
    enable_user_feedback: bool = True
    enable_userfeedback: bool = True  # Legacy name for backward compatibility
    enable_tutor_lm: bool = True
    enable_tutorlm: bool = True  # Legacy name for backward compatibility
    enable_ai_providers: bool = True
    enable_airtable: bool = True
    enable_snovio: bool = True
    enable_plaud: bool = True
    enable_beehiiv: bool = True
    enable_circle: bool = True
    enable_bettermode: bool = True  # Added for BetterMode integration
    enable_huggingface: bool = True
    enable_softr: bool = True
    enable_capcut: bool = True
    enable_pipit: bool = True

    class Config:
        env_prefix = "INTEGRATION_"

    def validate_notion_token(self, v):
        if not v:
            raise ValueError("Notion API token is required")
        return v


class IntegrationManager:
    """
    Manages all third-party integrations for The HigherSelf Network.
    Ensures all services work together with Notion as the central hub.
    """

    def __init__(self, config: IntegrationManagerConfig = None):
        """
        Initialize the Integration Manager.

        Args:
            config: Optional configuration object
        """
        # Load config from environment if not provided
        if not config:
            try:
                self.config = IntegrationManagerConfig(
                    notion_api_token=os.environ.get("NOTION_API_TOKEN", ""),
                    enable_typeform=os.environ.get("ENABLE_TYPEFORM", "true").lower()
                    == "true",
                    enable_woocommerce=os.environ.get(
                        "ENABLE_WOOCOMMERCE", "true"
                    ).lower()
                    == "true",
                    enable_acuity=os.environ.get("ENABLE_ACUITY", "true").lower()
                    == "true",
                    enable_amelia=os.environ.get("ENABLE_AMELIA", "true").lower()
                    == "true",
                    enable_user_feedback=os.environ.get(
                        "ENABLE_USER_FEEDBACK", "true"
                    ).lower()
                    == "true",
                    enable_tutor_lm=os.environ.get("ENABLE_TUTOR_LM", "true").lower()
                    == "true",
                    enable_ai_providers=os.environ.get(
                        "ENABLE_AI_PROVIDERS", "true"
                    ).lower()
                    == "true",
                )
            except ValueError as e:
                logger.error(f"Error initializing IntegrationManager config: {e}")
                raise
        else:
            self.config = config

        # Initialize core services
        # Create NotionIntegrationConfig from global settings
        notion_config_obj = NotionIntegrationConfig(
            token=global_settings.notion.api_token,
            database_mappings=global_settings.notion.get_database_mappings(),
            # last_sync can be omitted or set to now if needed for this context
        )
        self.notion_service = NotionService(config=notion_config_obj)

        # Initialize optional services based on configuration
        self.services = {}

        # Dictionary to track initialization status
        self.initialization_status = {}

    async def initialize(self) -> bool:
        """
        Initialize all enabled integrations.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize Notion service first (required)
            logger.info("Initializing Notion service...")

            # Log detailed Notion configuration information
            if hasattr(global_settings, "notion") and global_settings.notion:
                notion_config = global_settings.notion
                token_present = bool(notion_config.api_token)
                token_length = len(notion_config.api_token) if token_present else 0

                # Only log a masked version of the token
                masked_token = "None"
                if token_present and token_length > 8:
                    masked_token = (
                        notion_config.api_token[:4]
                        + "..."
                        + notion_config.api_token[-4:]
                    )
                elif token_present:
                    masked_token = "***"

                logger.info(f"Notion API token present: {token_present}")
                logger.info(f"Notion API token length: {token_length}")
                logger.info(f"Notion API token (masked): {masked_token}")

                # Log database mappings
                db_mappings = notion_config.get_database_mappings()
                missing_dbs = [name for name, db_id in db_mappings.items() if not db_id]
                if missing_dbs:
                    logger.warning(
                        f"Missing Notion database IDs for: {', '.join(missing_dbs)}"
                    )

            # Attempt to validate the token
            try:
                logger.info("Validating Notion API token...")
                notion_initialized = await self.notion_service.validate_token()
                self.initialization_status["notion"] = notion_initialized

                if notion_initialized:
                    logger.info("✅ Notion API token validated successfully")
                else:
                    logger.error("❌ Notion API token validation failed")
            except Exception as e:
                logger.error(f"❌ Exception during Notion API token validation: {e}")
                notion_initialized = False
                self.initialization_status["notion"] = False

            if not notion_initialized:
                logger.error("Failed to initialize Notion service. Cannot continue.")
                return False

            logger.info("Notion service initialized successfully")

            # Initialize optional services

            # TypeForm
            if self.config.enable_typeform:
                logger.info("Initializing TypeForm service...")
                try:
                    typeform_service = TypeFormService()
                    typeform_initialized = await typeform_service.validate_connection()
                    if typeform_initialized:
                        self.services["typeform"] = typeform_service
                        logger.info("TypeForm service initialized successfully")
                    else:
                        logger.warning("TypeForm service failed connection validation")
                except Exception as e:
                    logger.error(f"Failed to initialize TypeForm service: {e}")
                    typeform_initialized = False

                self.initialization_status["typeform"] = typeform_initialized

            # WooCommerce
            if self.config.enable_woocommerce:
                logger.info("Initializing WooCommerce service...")
                try:
                    woocommerce_service = WooCommerceService()
                    woocommerce_initialized = (
                        await woocommerce_service.validate_connection()
                    )
                    if woocommerce_initialized:
                        self.services["woocommerce"] = woocommerce_service
                        logger.info("WooCommerce service initialized successfully")
                    else:
                        logger.warning(
                            "WooCommerce service failed connection validation"
                        )
                except Exception as e:
                    logger.error(f"Failed to initialize WooCommerce service: {e}")
                    woocommerce_initialized = False

                self.initialization_status["woocommerce"] = woocommerce_initialized

            # Acuity
            if self.config.enable_acuity:
                logger.info("Initializing Acuity service...")
                try:
                    acuity_service = AcuityService()
                    acuity_initialized = await acuity_service.validate_connection()
                    if acuity_initialized:
                        self.services["acuity"] = acuity_service
                        logger.info("Acuity service initialized successfully")
                    else:
                        logger.warning("Acuity service failed connection validation")
                except Exception as e:
                    logger.error(f"Failed to initialize Acuity service: {e}")
                    acuity_initialized = False

                self.initialization_status["acuity"] = acuity_initialized

            # Amelia
            if self.config.enable_amelia:
                logger.info("Initializing Amelia service...")
                try:
                    amelia_service = AmeliaService()
                    amelia_initialized = await amelia_service.validate_connection()
                    if amelia_initialized:
                        self.services["amelia"] = amelia_service
                        logger.info("Amelia service initialized successfully")
                    else:
                        logger.warning("Amelia service failed connection validation")
                except Exception as e:
                    logger.error(f"Failed to initialize Amelia service: {e}")
                    amelia_initialized = False

                self.initialization_status["amelia"] = amelia_initialized

            # Airtable
            if self.config.enable_airtable:
                logger.info("Initializing Airtable service...")
                self.services["airtable"] = AirtableService()
                # Airtable doesn't have a validate method, so assume it's initialized
                self.initialization_status["airtable"] = True

            # SnovIO
            if self.config.enable_snovio:
                logger.info("Initializing SnovIO service...")
                self.services["snovio"] = SnovioService()
                snovio_initialized = await self.services[
                    "snovio"
                ].validate_credentials()
                self.initialization_status["snovio"] = snovio_initialized
                if not snovio_initialized:
                    logger.warning(
                        "SnovIO service failed to initialize. Some features may be unavailable."
                    )

            # UserFeedback
            if self.config.enable_user_feedback or self.config.enable_userfeedback:
                logger.info("Initializing UserFeedback service...")
                self.services["user_feedback"] = UserFeedbackService()
                # UserFeedback doesn't have a specific validation method
                self.initialization_status["user_feedback"] = True

            # TutorLM
            if self.config.enable_tutor_lm or self.config.enable_tutorlm:
                logger.info("Initializing TutorLM service...")
                self.services["tutor_lm"] = TutorLMService()
                # TutorLM doesn't have a specific validation method
                self.initialization_status["tutor_lm"] = True

            # Plaud
            if self.config.enable_plaud:
                logger.info("Initializing Plaud service...")
                self.services["plaud"] = PlaudService()
                # Plaud doesn't have a specific validation method
                self.initialization_status["plaud"] = True

            # Hugging Face
            if self.config.enable_huggingface:
                logger.info("Initializing Hugging Face service...")
                try:
                    huggingface_service = HuggingFaceService(
                        notion_service=self.notion_service
                    )
                    # Hugging Face doesn't have a specific validation method yet
                    self.services["huggingface"] = huggingface_service
                    self.initialization_status["huggingface"] = True
                    logger.info("Hugging Face service initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Hugging Face service: {e}")
                    self.initialization_status["huggingface"] = False

            # Softr
            if self.config.enable_softr:
                logger.info("Initializing Softr service...")
                try:
                    softr_service = SoftrService()
                    # Softr doesn't have a specific validation method yet
                    self.services["softr"] = softr_service
                    self.initialization_status["softr"] = True
                    logger.info("Softr service initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Softr service: {e}")
                    self.initialization_status["softr"] = False

            # BetterMode
            if self.config.enable_bettermode:
                logger.info("Initializing BetterMode service...")
                try:
                    bettermode_service = BetterModeService()
                    bettermode_initialized = (
                        await bettermode_service.validate_connection()
                    )
                    if bettermode_initialized:
                        self.services["bettermode"] = bettermode_service
                        logger.info("BetterMode service initialized successfully")
                    else:
                        logger.warning(
                            "BetterMode service failed connection validation"
                        )
                except Exception as e:
                    logger.error(f"Failed to initialize BetterMode service: {e}")
                    bettermode_initialized = False

                self.initialization_status["bettermode"] = bettermode_initialized

            # CapCut
            if self.config.enable_capcut:
                logger.info("Initializing CapCut service...")
                try:
                    capcut_service = CapCutService(notion_service=self.notion_service)
                    # CapCut doesn't have a specific validation method yet
                    self.services["capcut"] = capcut_service
                    self.initialization_status["capcut"] = True
                    logger.info("CapCut service initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize CapCut service: {e}")
                    self.initialization_status["capcut"] = False

            # Pipit
            if self.config.enable_pipit:
                logger.info("Initializing Pipit service...")
                try:
                    pipit_service = PipitService(notion_service=self.notion_service)
                    # Pipit doesn't have a specific validation method yet
                    self.services["pipit"] = pipit_service
                    self.initialization_status["pipit"] = True
                    logger.info("Pipit service initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Pipit service: {e}")
                    self.initialization_status["pipit"] = False

            # AI Providers
            if self.config.enable_ai_providers:
                logger.info("Initializing AI Provider service...")
                try:
                    ai_provider_service = AIProviderService()

                    # Try to validate both OpenAI and Anthropic providers
                    openai_initialized = await ai_provider_service.validate_connection(
                        "openai"
                    )
                    anthropic_initialized = (
                        await ai_provider_service.validate_connection("anthropic")
                    )

                    # Consider service initialized if at least one provider works
                    ai_initialized = openai_initialized or anthropic_initialized

                    if ai_initialized:
                        self.services["ai_provider"] = ai_provider_service
                        logger.info("AI Provider service initialized successfully")
                        if openai_initialized:
                            logger.info("OpenAI provider validated successfully")
                        if anthropic_initialized:
                            logger.info("Anthropic provider validated successfully")
                    else:
                        logger.warning(
                            "AI Provider service failed - no providers validated"
                        )
                except Exception as e:
                    logger.error(f"Failed to initialize AI Provider service: {e}")
                    ai_initialized = False

                self.initialization_status["ai_provider"] = ai_initialized

            # Log initialization summary
            successful = sum(
                1 for status in self.initialization_status.values() if status
            )
            total = len(self.initialization_status)
            logger.info(
                f"Integration Manager initialization complete. {successful}/{total} services initialized successfully."
            )

            return True
        except Exception as e:
            logger.error(f"Error initializing Integration Manager: {e}")
            return False

    def get_service(self, service_name: str) -> Any:
        """
        Get a specific service by name.

        Args:
            service_name: Name of the service to retrieve

        Returns:
            Service instance if available, None otherwise
        """
        if service_name == "notion":
            return self.notion_service

        return self.services.get(service_name)

    def get_initialization_status(self) -> Dict[str, bool]:
        """
        Get initialization status for all services.

        Returns:
            Dictionary mapping service names to initialization status
        """
        return self.initialization_status

    async def sync_to_notion(
        self, service_name: str, data: Dict[str, Any], model_type: Type[BaseModel]
    ) -> Optional[str]:
        """
        Synchronize data from an integration to Notion.

        Args:
            service_name: Name of the source service
            data: Data to synchronize
            model_type: Pydantic model type for the data

        Returns:
            Notion page ID if successful, None otherwise
        """
        try:
            # Verify Notion service is available
            if not self.notion_service or not self.initialization_status.get(
                "notion", False
            ):
                logger.error("Notion service not initialized - cannot sync")
                return None

            # Convert data to the specified model type
            model_instance = model_type(**data)

            # Add source metadata
            if hasattr(model_instance, "meta_data"):
                if model_instance.meta_data is None:
                    model_instance.meta_data = {}

                model_instance.meta_data["source_integration"] = service_name
                model_instance.meta_data["sync_timestamp"] = datetime.now().isoformat()
                model_instance.meta_data["notion_managed"] = True

            # Create or update in Notion
            page_id = await self.notion_service.create_page(model_instance)

            # Update the model with Notion page ID if it has that field
            if hasattr(model_instance, "notion_page_id") and page_id:
                model_instance.notion_page_id = page_id

                # Also update in the source service if it supports it
                service = self.get_service(service_name)
                if service and hasattr(service, "update_notion_reference"):
                    await service.update_notion_reference(model_instance)

            logger.info(f"Synchronized data from {service_name} to Notion: {page_id}")
            return page_id
        except Exception as e:
            logger.error(f"Error synchronizing data from {service_name} to Notion: {e}")
            return None

    async def sync_from_notion(
        self, service_name: str, notion_page_id: str, model_type: Type[BaseModel]
    ) -> bool:
        """
        Synchronize data from Notion to an integration.

        Args:
            service_name: Name of the target service
            notion_page_id: Notion page ID to sync from
            model_type: Pydantic model type for the data

        Returns:
            True if sync successful, False otherwise
        """
        try:
            # Verify Notion service is available
            if not self.notion_service or not self.initialization_status.get(
                "notion", False
            ):
                logger.error("Notion service not initialized - cannot sync")
                return False

            # Get service instance
            service = self.get_service(service_name)
            if not service:
                logger.error(f"Service {service_name} not available")
                return False

            # Check if service is initialized
            if not self.initialization_status.get(service_name, False):
                logger.error(f"Service {service_name} is not properly initialized")
                return False

            # Get page data from Notion
            page_data = await self.notion_service.get_page(notion_page_id)
            if not page_data:
                logger.error(f"Failed to get Notion page data for {notion_page_id}")
                return False

            # Ensure the page_data includes the Notion page ID
            page_data["notion_page_id"] = notion_page_id

            # Add sync metadata
            if "meta_data" not in page_data or page_data["meta_data"] is None:
                page_data["meta_data"] = {}

            page_data["meta_data"]["notion_sync_timestamp"] = datetime.now().isoformat()
            page_data["meta_data"]["notion_managed"] = True

            # Convert to model
            model_instance = model_type(**page_data)

            # Call appropriate sync method on the service
            # The implementation will depend on the specific service
            if hasattr(service, "sync_from_notion"):
                success = await service.sync_from_notion(model_instance)
                logger.info(
                    f"Synchronized data from Notion to {service_name}: {success}"
                )
                return success
            else:
                logger.warning(
                    f"Service {service_name} does not support sync_from_notion"
                )
                return False
        except Exception as e:
            logger.error(f"Error synchronizing data from Notion to {service_name}: {e}")
            return False

    async def validate_all_connections(self) -> Dict[str, bool]:
        """
        Validate connections for all initialized services.

        Returns:
            Dictionary mapping service names to validation results
        """
        validation_results = {}

        for service_name, service in self.services.items():
            try:
                if hasattr(service, "validate_connection"):
                    logger.info(f"Validating connection for {service_name}...")
                    result = await service.validate_connection()
                    validation_results[service_name] = result
                    if result:
                        logger.info(f"Connection validated for {service_name}")
                    else:
                        logger.warning(
                            f"Connection validation failed for {service_name}"
                        )
                else:
                    logger.warning(
                        f"Service {service_name} does not support connection validation"
                    )
                    validation_results[service_name] = False
            except Exception as e:
                logger.error(f"Error validating connection for {service_name}: {e}")
                validation_results[service_name] = False

        return validation_results
