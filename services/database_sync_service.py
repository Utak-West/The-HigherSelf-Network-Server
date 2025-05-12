"""
Database Synchronization Service for The HigherSelf Network Server.

This service handles the synchronization between Notion databases and Supabase tables,
ensuring that data is consistent across both systems.
"""

import os
# import logging # Replaced by loguru
from loguru import logger # Added for direct loguru usage
import asyncio
from typing import Dict, Any, List, Optional, Type, Union, Tuple
from datetime import datetime, timedelta

from pydantic import BaseModel, ValidationError

from services.notion_service import NotionService
from services.supabase_service import SupabaseService
from models.base import NotionIntegrationConfig
from config.testing_mode import is_api_disabled, TestingMode


# Mapping between model names and Supabase table names
MODEL_TO_TABLE_MAPPING = {
    "BusinessEntity": "business_entities",
    "ContactProfile": "contacts_profiles",
    "CommunityMember": "community_members",
    "ProductService": "products_services",
    "WorkflowInstance": "workflow_instances",
    "MarketingCampaign": "marketing_campaigns",
    "FeedbackSurvey": "feedback_surveys",
    "RewardBounty": "rewards_bounties",
    "Task": "tasks",
    "AgentCommunication": "agent_communication_patterns",
    "Agent": "agents",
    "ApiIntegration": "api_integrations",
    "DataTransformation": "data_transformations",
    "NotificationTemplate": "notification_templates",
    "UseCase": "use_cases",
    "Workflow": "workflows"
}


class SyncResult(BaseModel):
    """Result of a synchronization operation."""
    success: bool
    model_name: str
    record_id: Optional[str] = None
    notion_page_id: Optional[str] = None
    supabase_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = datetime.now()


class DatabaseSyncService:
    """Service for synchronizing between Notion and Supabase."""

    def __init__(self, notion_service: NotionService, supabase_service: SupabaseService):
        """
        Initialize the Database Sync Service.

        Args:
            notion_service: NotionService instance
            supabase_service: SupabaseService instance
        """
        logger.info("--- DatabaseSyncService __init__ START ---") # ADDED FOR DEBUGGING
        self.notion_service = notion_service
        self.supabase_service = supabase_service
        # self.logger = logging.getLogger(__name__) # Replaced by global loguru logger
        logger.info(f"Database Sync Service initialized for {self.__class__.__name__}")

        # Last sync timestamps for each model
        self.last_sync_timestamps: Dict[str, datetime] = {}
        logger.info("--- DatabaseSyncService __init__ END ---") # ADDED FOR DEBUGGING

        # Check if we're in testing mode
        if is_api_disabled("notion") or is_api_disabled("supabase"):
            logger.warning(f"TESTING MODE ACTIVE for {self.__class__.__name__}: Some sync operations will be simulated")

    async def sync_notion_to_supabase(
        self,
        model_class: Type[BaseModel],
        notion_page_id: str
    ) -> SyncResult:
        """
        Synchronize a record from Notion to Supabase.

        Args:
            model_class: Pydantic model class
            notion_page_id: Notion page ID

        Returns:
            SyncResult instance
        """
        model_name = model_class.__name__
        logger.bind(model_name=model_name, notion_page_id=notion_page_id, operation="sync_notion_to_supabase").info("Attempting to sync record from Notion to Supabase.")
        table_name = MODEL_TO_TABLE_MAPPING.get(model_name)

        if not table_name:
            return SyncResult(
                success=False,
                model_name=model_name,
                notion_page_id=notion_page_id,
                error_message=f"No table mapping found for model: {model_name}"
            )

        # Check if we're in testing mode
        notion_api_disabled = is_api_disabled("notion")
        supabase_api_disabled = is_api_disabled("supabase")

        # Log testing mode status
        logger.bind(
            model_name=model_name,
            notion_page_id=notion_page_id,
            operation="sync_notion_to_supabase",
            notion_api_disabled=notion_api_disabled,
            supabase_api_disabled=supabase_api_disabled
        ).debug(f"Testing mode status: Notion API disabled: {notion_api_disabled}, Supabase API disabled: {supabase_api_disabled}")

        # If both APIs are disabled in testing mode, return a mock success result
        if notion_api_disabled and supabase_api_disabled:
            logger.bind(model_name=model_name, notion_page_id=notion_page_id, operation="sync_notion_to_supabase").info("Both Notion and Supabase APIs are disabled in testing mode. Returning mock success result.")
            return SyncResult(
                success=True,
                model_name=model_name,
                record_id="mock_record_id",
                notion_page_id=notion_page_id,
                supabase_id="mock_supabase_id",
                error_message=None
            )

        try:
            # Get the record from Notion
            notion_record = None
            if notion_api_disabled:
                logger.bind(model_name=model_name, notion_page_id=notion_page_id, operation="sync_notion_to_supabase").info("Notion API is disabled in testing mode. Using mock record.")
                # Create a mock record for testing
                notion_record = model_class.model_construct()  # Create an empty instance
                setattr(notion_record, "page_id", notion_page_id)
                setattr(notion_record, "id", "mock_id")
            else:
                notion_record = await self.notion_service.get_page(notion_page_id, model_class)

            if not notion_record:
                logger.bind(model_name=model_name, notion_page_id=notion_page_id, operation="sync_notion_to_supabase").warning("Record not found in Notion.")
                return SyncResult(
                    success=False,
                    model_name=model_name,
                    notion_page_id=notion_page_id,
                    error_message=f"Record not found in Notion: {notion_page_id}"
                )
            logger.bind(model_name=model_name, notion_page_id=notion_page_id, operation="sync_notion_to_supabase").debug(f"Successfully fetched record from Notion: {notion_record.model_dump_json(indent=2, exclude_none=True) if hasattr(notion_record, 'model_dump_json') else 'Mock record'}")

            # Check if the record already exists in Supabase by notion_page_id
            existing_records = []
            if supabase_api_disabled:
                logger.bind(model_name=model_name, notion_page_id=notion_page_id, operation="sync_notion_to_supabase").info("Supabase API is disabled in testing mode. Assuming record does not exist.")
            else:
                existing_records = await self.supabase_service.query_records(
                    table_name=table_name,
                    model_class=model_class,
                    filters={"notion_page_id": f"eq.{notion_page_id}"}
                )

            logger.bind(model_name=model_name, notion_page_id=notion_page_id, operation="sync_notion_to_supabase").debug(f"Found {len(existing_records)} existing records in Supabase for notion_page_id {notion_page_id}.")

            if existing_records:
                # Update the existing record
                supabase_id = existing_records[0].id
                logger.bind(model_name=model_name, notion_page_id=notion_page_id, supabase_id=supabase_id, operation="sync_notion_to_supabase").info("Record exists in Supabase. Attempting update.")

                success = True
                if not supabase_api_disabled:
                    success = await self.supabase_service.update_record(
                        table_name=table_name,
                        record_id=supabase_id,
                        model=notion_record
                    )
                else:
                    logger.bind(model_name=model_name, notion_page_id=notion_page_id, supabase_id=supabase_id, operation="sync_notion_to_supabase").info("Supabase API is disabled in testing mode. Simulating successful update.")

                logger.bind(model_name=model_name, notion_page_id=notion_page_id, supabase_id=supabase_id, operation="sync_notion_to_supabase").info(f"Supabase update {'succeeded' if success else 'failed'}.")

                return SyncResult(
                    success=success,
                    model_name=model_name,
                    record_id=getattr(notion_record, "id", None),
                    notion_page_id=notion_page_id,
                    supabase_id=supabase_id,
                    error_message=None if success else "Failed to update record in Supabase"
                )
            else:
                # Create a new record
                logger.bind(model_name=model_name, notion_page_id=notion_page_id, operation="sync_notion_to_supabase").info("Record does not exist in Supabase. Attempting create.")

                supabase_id = "mock_supabase_id"
                if not supabase_api_disabled:
                    supabase_id = await self.supabase_service.create_record(
                        table_name=table_name,
                        model=notion_record
                    )
                else:
                    logger.bind(model_name=model_name, notion_page_id=notion_page_id, operation="sync_notion_to_supabase").info("Supabase API is disabled in testing mode. Simulating successful create.")

                logger.bind(model_name=model_name, notion_page_id=notion_page_id, supabase_id=supabase_id, operation="sync_notion_to_supabase").info(f"Supabase create {'succeeded' if supabase_id else 'failed'}. New Supabase ID: {supabase_id}")

                return SyncResult(
                    success=bool(supabase_id),
                    model_name=model_name,
                    record_id=getattr(notion_record, "id", None),
                    notion_page_id=notion_page_id,
                    supabase_id=supabase_id,
                    error_message=None if supabase_id else "Failed to create record in Supabase"
                )
        except Exception as e:
            logger.bind(model_name=model_name, notion_page_id=notion_page_id, operation="sync_notion_to_supabase").error(f"Exception during sync from Notion to Supabase: {e}", exc_info=True)
            return SyncResult(
                success=False,
                model_name=model_name,
                notion_page_id=notion_page_id,
                error_message=str(e)
            )

    async def sync_supabase_to_notion(
        self,
        model_class: Type[BaseModel],
        supabase_id: str
    ) -> SyncResult:
        """
        Synchronize a record from Supabase to Notion.

        Args:
            model_class: Pydantic model class
            supabase_id: Supabase record ID

        Returns:
            SyncResult instance
        """
        model_name = model_class.__name__
        logger.bind(model_name=model_name, supabase_id=supabase_id, operation="sync_supabase_to_notion").info("Attempting to sync record from Supabase to Notion.")
        table_name = MODEL_TO_TABLE_MAPPING.get(model_name)

        if not table_name:
            logger.bind(model_name=model_name, supabase_id=supabase_id, operation="sync_supabase_to_notion").error(f"No table mapping found for model: {model_name}")
            return SyncResult(
                success=False,
                model_name=model_name,
                supabase_id=supabase_id,
                error_message=f"No table mapping found for model: {model_name}"
            )

        # Check if we're in testing mode
        notion_api_disabled = is_api_disabled("notion")
        supabase_api_disabled = is_api_disabled("supabase")

        # Log testing mode status
        logger.bind(
            model_name=model_name,
            supabase_id=supabase_id,
            operation="sync_supabase_to_notion",
            notion_api_disabled=notion_api_disabled,
            supabase_api_disabled=supabase_api_disabled
        ).debug(f"Testing mode status: Notion API disabled: {notion_api_disabled}, Supabase API disabled: {supabase_api_disabled}")

        # If both APIs are disabled in testing mode, return a mock success result
        if notion_api_disabled and supabase_api_disabled:
            logger.bind(model_name=model_name, supabase_id=supabase_id, operation="sync_supabase_to_notion").info("Both Notion and Supabase APIs are disabled in testing mode. Returning mock success result.")
            return SyncResult(
                success=True,
                model_name=model_name,
                record_id="mock_record_id",
                notion_page_id="mock_notion_page_id",
                supabase_id=supabase_id,
                error_message=None
            )

        try:
            # Get the record from Supabase
            supabase_record = None
            if supabase_api_disabled:
                logger.bind(model_name=model_name, supabase_id=supabase_id, operation="sync_supabase_to_notion").info("Supabase API is disabled in testing mode. Using mock record.")
                # Create a mock record for testing
                supabase_record = model_class.model_construct()  # Create an empty instance
                setattr(supabase_record, "id", supabase_id)
            else:
                supabase_record = await self.supabase_service.get_record(
                    table_name=table_name,
                    record_id=supabase_id,
                    model_class=model_class
                )

            if not supabase_record:
                logger.bind(model_name=model_name, supabase_id=supabase_id, operation="sync_supabase_to_notion").warning("Record not found in Supabase.")
                return SyncResult(
                    success=False,
                    model_name=model_name,
                    supabase_id=supabase_id,
                    error_message=f"Record not found in Supabase: {supabase_id}"
                )
            logger.bind(model_name=model_name, supabase_id=supabase_id, operation="sync_supabase_to_notion").debug(f"Successfully fetched record from Supabase: {supabase_record.model_dump_json(indent=2, exclude_none=True) if hasattr(supabase_record, 'model_dump_json') else 'Mock record'}")

            # Check if the record already exists in Notion
            notion_page_id = getattr(supabase_record, "notion_page_id", None)
            logger.bind(model_name=model_name, supabase_id=supabase_id, notion_page_id=notion_page_id, operation="sync_supabase_to_notion").debug(f"Supabase record has notion_page_id: {notion_page_id}")

            if notion_page_id:
                # Update the existing page
                logger.bind(model_name=model_name, supabase_id=supabase_id, notion_page_id=notion_page_id, operation="sync_supabase_to_notion").info("Record has Notion page ID. Attempting update in Notion.")

                success = True
                if not notion_api_disabled:
                    success = await self.notion_service.update_page(supabase_record)
                else:
                    logger.bind(model_name=model_name, supabase_id=supabase_id, notion_page_id=notion_page_id, operation="sync_supabase_to_notion").info("Notion API is disabled in testing mode. Simulating successful update.")

                logger.bind(model_name=model_name, supabase_id=supabase_id, notion_page_id=notion_page_id, operation="sync_supabase_to_notion").info(f"Notion page update {'succeeded' if success else 'failed'}.")

                return SyncResult(
                    success=success,
                    model_name=model_name,
                    record_id=getattr(supabase_record, "id", None),
                    notion_page_id=notion_page_id,
                    supabase_id=supabase_id,
                    error_message=None if success else "Failed to update page in Notion"
                )
            else:
                # Create a new page
                logger.bind(model_name=model_name, supabase_id=supabase_id, operation="sync_supabase_to_notion").info("Record does not have Notion page ID. Attempting create in Notion.")

                notion_page_id = "mock_notion_page_id"
                if not notion_api_disabled:
                    notion_page_id = await self.notion_service.create_page(supabase_record)
                else:
                    logger.bind(model_name=model_name, supabase_id=supabase_id, operation="sync_supabase_to_notion").info("Notion API is disabled in testing mode. Simulating successful page creation.")

                logger.bind(model_name=model_name, supabase_id=supabase_id, new_notion_page_id=notion_page_id, operation="sync_supabase_to_notion").info(f"Notion page create {'succeeded' if notion_page_id else 'failed'}. New Notion Page ID: {notion_page_id}")

                if notion_page_id:
                    # Update the Supabase record with the Notion page ID
                    logger.bind(model_name=model_name, supabase_id=supabase_id, new_notion_page_id=notion_page_id, operation="sync_supabase_to_notion").info("Updating Supabase record with new Notion page ID.")
                    setattr(supabase_record, "notion_page_id", notion_page_id)

                    update_success = True
                    if not supabase_api_disabled:
                        update_success = await self.supabase_service.update_record(
                            table_name=table_name,
                            record_id=supabase_id,
                            model=supabase_record
                        )
                    else:
                        logger.bind(model_name=model_name, supabase_id=supabase_id, new_notion_page_id=notion_page_id, operation="sync_supabase_to_notion").info("Supabase API is disabled in testing mode. Simulating successful record update.")

                    logger.bind(model_name=model_name, supabase_id=supabase_id, new_notion_page_id=notion_page_id, operation="sync_supabase_to_notion").info(f"Supabase record update with new Notion page ID {'succeeded' if update_success else 'failed'}.")

                return SyncResult(
                    success=bool(notion_page_id),
                    model_name=model_name,
                    record_id=getattr(supabase_record, "id", None),
                    notion_page_id=notion_page_id,
                    supabase_id=supabase_id,
                    error_message=None if notion_page_id else "Failed to create page in Notion"
                )
        except Exception as e:
            logger.bind(model_name=model_name, supabase_id=supabase_id, operation="sync_supabase_to_notion").error(f"Exception during sync from Supabase to Notion: {e}", exc_info=True)
            return SyncResult(
                success=False,
                model_name=model_name,
                supabase_id=supabase_id,
                error_message=str(e)
            )

    async def sync_all_records(
        self,
        model_class: Type[BaseModel],
        direction: str = "both",
        since: Optional[datetime] = None
    ) -> List[SyncResult]:
        """
        Synchronize all records of a specific model.

        Args:
            model_class: Pydantic model class
            direction: Sync direction ("notion_to_supabase", "supabase_to_notion", or "both")
            since: Only sync records updated since this timestamp. If not provided, defaults to
                  the last sync timestamp for this model or 30 days ago.

        Returns:
            List of SyncResult instances

        Notes:
            - For Notion, filtering uses the "last_edited_time" field
            - For Supabase, filtering uses the "updated_at" field
            - The sync timestamp for each model is updated after successful synchronization
        """
        model_name = model_class.__name__
        logger.info(f"--- DatabaseSyncService.sync_all_records START for {model_name} ---") # ADDED FOR DEBUGGING
        logger.bind(model_name=model_name, direction=direction, since=since.isoformat() if since else "None", operation="sync_all_records").info("Attempting to sync all records for model.")
        table_name = MODEL_TO_TABLE_MAPPING.get(model_name)
        results = []

        if not table_name:
            logger.bind(model_name=model_name, operation="sync_all_records").error(f"No table mapping found for model: {model_name}")
            results.append(SyncResult(
                success=False,
                model_name=model_name,
                error_message=f"No table mapping found for model: {model_name}"
            ))
            return results

        try:
            effective_since = since
            # Set default sync timestamp if not provided
            if not effective_since:
                effective_since = self.last_sync_timestamps.get(model_name, datetime.now() - timedelta(days=30))
                logger.bind(model_name=model_name, operation="sync_all_records").info(f"No 'since' timestamp provided, using effective_since: {effective_since.isoformat()}")
            else:
                logger.bind(model_name=model_name, operation="sync_all_records").info(f"Using provided 'since' timestamp: {effective_since.isoformat()}")

            # Check if we're in testing mode
            from config.testing_mode import is_api_disabled, is_testing_mode, TestingMode

            # If we're in test mode, make sure both APIs are disabled
            if is_testing_mode():
                TestingMode.add_disabled_api("notion")
                TestingMode.add_disabled_api("supabase")

            # Force disable APIs in testing mode if environment variables are set
            if os.environ.get("TEST_MODE", "").lower() == "true":
                if os.environ.get("DISABLE_APIS", "").lower().find("notion") != -1:
                    TestingMode.add_disabled_api("notion")

                if os.environ.get("DISABLE_APIS", "").lower().find("supabase") != -1:
                    TestingMode.add_disabled_api("supabase")

            notion_api_disabled = is_api_disabled("notion")
            supabase_api_disabled = is_api_disabled("supabase")

            # Log testing mode status
            logger.bind(
                model_name=model_name,
                operation="sync_all_records",
                notion_api_disabled=notion_api_disabled,
                supabase_api_disabled=supabase_api_disabled
            ).debug(f"Testing mode status: Notion API disabled: {notion_api_disabled}, Supabase API disabled: {supabase_api_disabled}")

            # Sync from Notion to Supabase
            if direction in ["notion_to_supabase", "both"]:
                logger.bind(model_name=model_name, operation="sync_all_records", sub_operation="notion_to_supabase").info("Starting sync from Notion to Supabase.")
                # Create filter for records updated since the specified timestamp
                filter_conditions = None
                if effective_since:
                    # Format the timestamp for Notion's filter API
                    # Notion uses "last_edited_time" as the field for when a page was last updated
                    filter_conditions = {
                        "timestamp": "last_edited_time",
                        "last_edited_time": {
                            "on_or_after": effective_since.isoformat()
                        }
                    }
                    logger.bind(model_name=model_name, operation="sync_all_records", sub_operation="notion_to_supabase").info(f"Filtering Notion records updated on_or_after: {effective_since.isoformat()}")

                # Get all records from Notion
                notion_records = []
                if notion_api_disabled:
                    # In testing mode, use mock data
                    logger.bind(model_name=model_name, operation="sync_all_records", sub_operation="notion_to_supabase").info("Notion API is disabled in testing mode. Using mock data.")
                    # No mock records for now, just an empty list
                else:
                    notion_records = await self.notion_service.query_database(
                        model_class=model_class,
                        filter_conditions=filter_conditions,
                        limit=1000 # Consider making limit configurable or handling pagination
                    )

                logger.bind(model_name=model_name, operation="sync_all_records", sub_operation="notion_to_supabase").info(f"Retrieved {len(notion_records)} records from Notion.")

                for i, record in enumerate(notion_records):
                    notion_page_id = getattr(record, "page_id", None)
                    logger.bind(model_name=model_name, notion_page_id=notion_page_id, item_index=i, total_items=len(notion_records), operation="sync_all_records", sub_operation="notion_to_supabase_item").debug("Processing Notion record.")
                    if notion_page_id:
                        result = await self.sync_notion_to_supabase(model_class, notion_page_id)
                        results.append(result)
                        logger.bind(model_name=model_name, notion_page_id=notion_page_id, item_index=i, total_items=len(notion_records), operation="sync_all_records", sub_operation="notion_to_supabase_item").debug(f"Sync result: {result.success}, Error: {result.error_message}")

            # Sync from Supabase to Notion
            if direction in ["supabase_to_notion", "both"]:
                logger.bind(model_name=model_name, operation="sync_all_records", sub_operation="supabase_to_notion").info("Starting sync from Supabase to Notion.")
                # Create filter for records updated since the specified timestamp
                filters = None
                if effective_since:
                    # Format the timestamp for Supabase's filter API
                    # Supabase uses "updated_at" as the standard field for when a record was last updated
                    filters = {
                        "updated_at": f"gte.{effective_since.isoformat()}"
                    }
                    logger.bind(model_name=model_name, operation="sync_all_records", sub_operation="supabase_to_notion").info(f"Filtering Supabase records updated gte: {effective_since.isoformat()}")

                # Get all records from Supabase
                supabase_records = []
                if supabase_api_disabled:
                    # In testing mode, use mock data
                    logger.bind(model_name=model_name, operation="sync_all_records", sub_operation="supabase_to_notion").info("Supabase API is disabled in testing mode. Using mock data.")
                    # No mock records for now, just an empty list
                else:
                    supabase_records = await self.supabase_service.query_records(
                        table_name=table_name,
                        model_class=model_class,
                        filters=filters,
                        limit=1000 # Consider making limit configurable or handling pagination
                    )

                logger.bind(model_name=model_name, operation="sync_all_records", sub_operation="supabase_to_notion").info(f"Retrieved {len(supabase_records)} records from Supabase.")

                for i, record in enumerate(supabase_records):
                    supabase_id = getattr(record, "id", None)
                    notion_page_id = getattr(record, "notion_page_id", None)
                    logger.bind(model_name=model_name, supabase_id=supabase_id, notion_page_id=notion_page_id, item_index=i, total_items=len(supabase_records), operation="sync_all_records", sub_operation="supabase_to_notion_item").debug("Processing Supabase record.")

                    # Only sync to Notion if no notion_page_id exists OR if Notion record is older (more complex, not implemented here for simplicity)
                    if supabase_id and not notion_page_id: # Simplified logic: only sync if Notion page ID is missing
                        logger.bind(model_name=model_name, supabase_id=supabase_id, item_index=i, total_items=len(supabase_records), operation="sync_all_records", sub_operation="supabase_to_notion_item").info("Supabase record missing notion_page_id, attempting sync to Notion.")
                        result = await self.sync_supabase_to_notion(model_class, supabase_id)
                        results.append(result)
                        logger.bind(model_name=model_name, supabase_id=supabase_id, item_index=i, total_items=len(supabase_records), operation="sync_all_records", sub_operation="supabase_to_notion_item").debug(f"Sync result: {result.success}, Error: {result.error_message}")
                    elif supabase_id and notion_page_id:
                         logger.bind(model_name=model_name, supabase_id=supabase_id, notion_page_id=notion_page_id, item_index=i, total_items=len(supabase_records), operation="sync_all_records", sub_operation="supabase_to_notion_item").debug("Supabase record already has notion_page_id, skipping sync to Notion to avoid potential loops without further logic.")


            # Update last sync timestamp
            new_sync_time = datetime.now()
            self.last_sync_timestamps[model_name] = new_sync_time
            logger.bind(model_name=model_name, new_sync_timestamp=new_sync_time.isoformat(), operation="sync_all_records").info("Updated last_sync_timestamp for model.")

            return results
        except Exception as e:
            logger.bind(model_name=model_name, operation="sync_all_records").error(f"Exception during sync_all_records for {model_name}: {e}", exc_info=True)
            results.append(SyncResult(
                success=False,
                model_name=model_name,
                error_message=str(e)
            ))
            return results

    async def sync_all_databases(
        self,
        direction: str = "both",
        since: Optional[datetime] = None
    ) -> Dict[str, List[SyncResult]]:
        """
        Synchronize all databases.

        Args:
            direction: Sync direction ("notion_to_supabase", "supabase_to_notion", or "both")
            since: Only sync records updated since this timestamp. If not provided, defaults to
                  the last sync timestamp for each model or 30 days ago.

        Returns:
            Dictionary mapping model names to lists of SyncResult instances
        """
        # Import here to avoid circular imports
        from models.notion_db_models import (
            BusinessEntity, Agent, Workflow, WorkflowInstance,
            ApiIntegration, DataTransformation, UseCase,
            NotificationTemplate, AgentCommunication, Task
        )
        from models.notion_db_models_extended import (
            ContactProfile, CommunityMember, ProductService,
            MarketingCampaign, FeedbackSurvey, RewardBounty
        )

        models = [
            BusinessEntity, ContactProfile, CommunityMember, ProductService,
            WorkflowInstance, MarketingCampaign, FeedbackSurvey, RewardBounty,
            Task, AgentCommunication, Agent, ApiIntegration,
            DataTransformation, NotificationTemplate, UseCase, Workflow
        ]

        results = {}

        for model_class in models:
            model_name = model_class.__name__
            logger.info(f"Syncing {model_name}...")
            model_results = await self.sync_all_records(model_class, direction, since)
            results[model_name] = model_results

            # Log results
            success_count = sum(1 for r in model_results if r.success)
            total_count = len(model_results)
            logger.info(f"Synced {model_name}: {success_count}/{total_count} successful")

        return results

    @classmethod
    async def create_from_services(
        cls,
        notion_service: NotionService,
        supabase_service: SupabaseService
    ) -> 'DatabaseSyncService':
        """
        Create a DatabaseSyncService instance from existing services.

        Args:
            notion_service: NotionService instance
            supabase_service: SupabaseService instance

        Returns:
            DatabaseSyncService instance
        """
        return cls(notion_service, supabase_service)
