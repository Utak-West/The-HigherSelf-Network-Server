"""
Database Synchronization Service for The HigherSelf Network Server.

This service handles the synchronization between Notion databases and Supabase tables,
ensuring that data is consistent across both systems.
"""

import os
import logging
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
        self.notion_service = notion_service
        self.supabase_service = supabase_service
        self.logger = logging.getLogger(__name__)
        self.logger.info("Database Sync Service initialized")
        
        # Last sync timestamps for each model
        self.last_sync_timestamps: Dict[str, datetime] = {}
        
        # Check if we're in testing mode
        if is_api_disabled("notion") or is_api_disabled("supabase"):
            self.logger.warning("TESTING MODE ACTIVE: Some sync operations will be simulated")
    
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
        table_name = MODEL_TO_TABLE_MAPPING.get(model_name)
        
        if not table_name:
            return SyncResult(
                success=False,
                model_name=model_name,
                notion_page_id=notion_page_id,
                error_message=f"No table mapping found for model: {model_name}"
            )
        
        try:
            # Get the record from Notion
            notion_record = await self.notion_service.get_page(notion_page_id, model_class)
            
            if not notion_record:
                return SyncResult(
                    success=False,
                    model_name=model_name,
                    notion_page_id=notion_page_id,
                    error_message=f"Record not found in Notion: {notion_page_id}"
                )
            
            # Check if the record already exists in Supabase by notion_page_id
            existing_records = await self.supabase_service.query_records(
                table_name=table_name,
                model_class=model_class,
                filters={"notion_page_id": f"eq.{notion_page_id}"}
            )
            
            if existing_records:
                # Update the existing record
                supabase_id = existing_records[0].id
                success = await self.supabase_service.update_record(
                    table_name=table_name,
                    record_id=supabase_id,
                    model=notion_record
                )
                
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
                supabase_id = await self.supabase_service.create_record(
                    table_name=table_name,
                    model=notion_record
                )
                
                return SyncResult(
                    success=bool(supabase_id),
                    model_name=model_name,
                    record_id=getattr(notion_record, "id", None),
                    notion_page_id=notion_page_id,
                    supabase_id=supabase_id,
                    error_message=None if supabase_id else "Failed to create record in Supabase"
                )
        except Exception as e:
            self.logger.error(f"Error syncing from Notion to Supabase: {e}")
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
        table_name = MODEL_TO_TABLE_MAPPING.get(model_name)
        
        if not table_name:
            return SyncResult(
                success=False,
                model_name=model_name,
                supabase_id=supabase_id,
                error_message=f"No table mapping found for model: {model_name}"
            )
        
        try:
            # Get the record from Supabase
            supabase_record = await self.supabase_service.get_record(
                table_name=table_name,
                record_id=supabase_id,
                model_class=model_class
            )
            
            if not supabase_record:
                return SyncResult(
                    success=False,
                    model_name=model_name,
                    supabase_id=supabase_id,
                    error_message=f"Record not found in Supabase: {supabase_id}"
                )
            
            # Check if the record already exists in Notion
            notion_page_id = getattr(supabase_record, "notion_page_id", None)
            
            if notion_page_id:
                # Update the existing page
                success = await self.notion_service.update_page(supabase_record)
                
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
                notion_page_id = await self.notion_service.create_page(supabase_record)
                
                if notion_page_id:
                    # Update the Supabase record with the Notion page ID
                    setattr(supabase_record, "notion_page_id", notion_page_id)
                    await self.supabase_service.update_record(
                        table_name=table_name,
                        record_id=supabase_id,
                        model=supabase_record
                    )
                
                return SyncResult(
                    success=bool(notion_page_id),
                    model_name=model_name,
                    record_id=getattr(supabase_record, "id", None),
                    notion_page_id=notion_page_id,
                    supabase_id=supabase_id,
                    error_message=None if notion_page_id else "Failed to create page in Notion"
                )
        except Exception as e:
            self.logger.error(f"Error syncing from Supabase to Notion: {e}")
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
            since: Only sync records updated since this timestamp
            
        Returns:
            List of SyncResult instances
        """
        model_name = model_class.__name__
        table_name = MODEL_TO_TABLE_MAPPING.get(model_name)
        results = []
        
        if not table_name:
            results.append(SyncResult(
                success=False,
                model_name=model_name,
                error_message=f"No table mapping found for model: {model_name}"
            ))
            return results
        
        try:
            # Set default sync timestamp if not provided
            if not since:
                since = self.last_sync_timestamps.get(model_name, datetime.now() - timedelta(days=30))
            
            # Sync from Notion to Supabase
            if direction in ["notion_to_supabase", "both"]:
                # Get all records from Notion
                notion_records = await self.notion_service.query_database(
                    model_class=model_class,
                    filter_conditions=None,  # TODO: Add filter for updated_at > since
                    limit=1000
                )
                
                for record in notion_records:
                    notion_page_id = getattr(record, "page_id", None)
                    if notion_page_id:
                        result = await self.sync_notion_to_supabase(model_class, notion_page_id)
                        results.append(result)
            
            # Sync from Supabase to Notion
            if direction in ["supabase_to_notion", "both"]:
                # Get all records from Supabase
                supabase_records = await self.supabase_service.query_records(
                    table_name=table_name,
                    model_class=model_class,
                    filters=None,  # TODO: Add filter for updated_at > since
                    limit=1000
                )
                
                for record in supabase_records:
                    supabase_id = getattr(record, "id", None)
                    notion_page_id = getattr(record, "notion_page_id", None)
                    
                    # Only sync to Notion if no notion_page_id exists
                    if supabase_id and not notion_page_id:
                        result = await self.sync_supabase_to_notion(model_class, supabase_id)
                        results.append(result)
            
            # Update last sync timestamp
            self.last_sync_timestamps[model_name] = datetime.now()
            
            return results
        except Exception as e:
            self.logger.error(f"Error syncing all records: {e}")
            results.append(SyncResult(
                success=False,
                model_name=model_name,
                error_message=str(e)
            ))
            return results
    
    async def sync_all_databases(self, direction: str = "both") -> Dict[str, List[SyncResult]]:
        """
        Synchronize all databases.
        
        Args:
            direction: Sync direction ("notion_to_supabase", "supabase_to_notion", or "both")
            
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
            self.logger.info(f"Syncing {model_name}...")
            model_results = await self.sync_all_records(model_class, direction)
            results[model_name] = model_results
            
            # Log results
            success_count = sum(1 for r in model_results if r.success)
            total_count = len(model_results)
            self.logger.info(f"Synced {model_name}: {success_count}/{total_count} successful")
        
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
