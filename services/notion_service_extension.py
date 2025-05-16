"""
Extension methods for NotionService to handle video transactions.
These methods will be added to the NotionService class.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from loguru import logger

from models.video_transaction_models import VideoTransaction, VideoTransactionStatus
from models.video_models import VideoContent
from config.testing_mode import is_api_disabled, TestingMode


async def create_video_transaction(self, transaction: VideoTransaction) -> str:
    """
    Create a video transaction record in Notion.
    
    Args:
        transaction: VideoTransaction model
        
    Returns:
        ID of the created page
    """
    try:
        # Ensure we have a database mapping for VideoTransaction
        if "VideoTransaction" not in self.db_mappings:
            # If not in mappings, try to get from environment
            import os
            self.db_mappings["VideoTransaction"] = os.environ.get("NOTION_VIDEO_TRANSACTIONS_DB", "")
            
            if not self.db_mappings["VideoTransaction"]:
                raise ValueError("No database mapping found for VideoTransaction")
        
        db_id = self.db_mappings["VideoTransaction"]
        properties = self._model_to_notion_properties(transaction)
        
        # Check if Notion API is disabled in testing mode
        if is_api_disabled("notion"):
            TestingMode.log_attempted_api_call(
                api_name="notion",
                endpoint="pages.create",
                method="POST",
                params={"parent": {"database_id": db_id}, "properties": properties}
            )
            logger.info(f"[TESTING MODE] Simulated creating video transaction in Notion")
            return f"test_page_id_VideoTransaction_{transaction.transaction_id}"
        
        response = self.client.pages.create(
            parent={"database_id": db_id},
            properties=properties
        )
        
        transaction_id = response["id"]
        logger.info(f"Created video transaction in Notion with ID: {transaction_id}")
        return transaction_id
    
    except Exception as e:
        logger.error(f"Error creating video transaction in Notion: {e}")
        raise


async def update_video_transaction(self, page_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update a video transaction in Notion.
    
    Args:
        page_id: Notion page ID
        updates: Dictionary of fields to update
        
    Returns:
        True if update was successful
    """
    try:
        # Convert updates to Notion properties format
        properties = {}
        
        for key, value in updates.items():
            if key == "transaction_status":
                properties["transaction_status"] = {
                    "select": {"name": value}
                }
            elif key == "payment_status":
                properties["payment_status"] = {
                    "select": {"name": value}
                }
            elif key == "updated_at":
                properties["updated_at"] = {
                    "date": {"start": value.isoformat()}
                }
            elif key == "expires_at" and value:
                properties["expires_at"] = {
                    "date": {"start": value.isoformat()}
                }
            # Add other fields as needed
        
        # Check if Notion API is disabled in testing mode
        if is_api_disabled("notion"):
            TestingMode.log_attempted_api_call(
                api_name="notion",
                endpoint="pages.update",
                method="PATCH",
                params={"page_id": page_id, "properties": properties}
            )
            logger.info(f"[TESTING MODE] Simulated updating video transaction {page_id}")
            return True
        
        self.client.pages.update(
            page_id=page_id,
            properties=properties
        )
        
        logger.info(f"Updated video transaction in Notion with ID: {page_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error updating video transaction in Notion: {e}")
        return False


async def get_video_transaction(self, transaction_id: str) -> Optional[VideoTransaction]:
    """
    Get a video transaction from Notion by ID.
    
    Args:
        transaction_id: Notion page ID
        
    Returns:
        VideoTransaction model or None if not found
    """
    try:
        # Check if Notion API is disabled in testing mode
        if is_api_disabled("notion"):
            TestingMode.log_attempted_api_call(
                api_name="notion",
                endpoint="pages.retrieve",
                method="GET",
                params={"page_id": transaction_id}
            )
            logger.info(f"[TESTING MODE] Simulated retrieving video transaction {transaction_id}")
            
            # Return a mock transaction in testing mode
            return VideoTransaction(
                id=transaction_id,
                transaction_id=f"vt-test-{transaction_id[-8:]}",
                video_id=f"vid-test-{transaction_id[-8:]}",
                customer_email="test@example.com",
                customer_name="Test User",
                transaction_type="premium_feature",
                transaction_status=VideoTransactionStatus.COMPLETED,
                payment_id=f"pay-test-{transaction_id[-8:]}",
                payment_status="completed",
                amount=29.99,
                currency="usd",
                features=[{
                    "feature_id": "feat-001",
                    "feature_type": "export_4k",
                    "name": "4K Export",
                    "description": "Export video in 4K resolution",
                    "price": 29.99
                }],
                business_entity_id="test_entity",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        # Retrieve the page from Notion
        page = self.client.pages.retrieve(page_id=transaction_id)
        
        # Convert to model
        transaction = self._notion_to_model(page, VideoTransaction)
        return transaction
    
    except Exception as e:
        logger.error(f"Error getting video transaction from Notion: {e}")
        return None


async def find_transaction_by_payment_id(self, payment_id: str) -> Optional[VideoTransaction]:
    """
    Find a video transaction by payment ID.
    
    Args:
        payment_id: Payment ID to search for
        
    Returns:
        VideoTransaction model or None if not found
    """
    try:
        # Ensure we have a database mapping for VideoTransaction
        if "VideoTransaction" not in self.db_mappings:
            # If not in mappings, try to get from environment
            import os
            self.db_mappings["VideoTransaction"] = os.environ.get("NOTION_VIDEO_TRANSACTIONS_DB", "")
            
            if not self.db_mappings["VideoTransaction"]:
                raise ValueError("No database mapping found for VideoTransaction")
        
        db_id = self.db_mappings["VideoTransaction"]
        
        # Prepare query
        query_params = {
            "database_id": db_id,
            "filter": {
                "property": "payment_id",
                "rich_text": {
                    "equals": payment_id
                }
            }
        }
        
        # Check if Notion API is disabled in testing mode
        if is_api_disabled("notion"):
            TestingMode.log_attempted_api_call(
                api_name="notion",
                endpoint="databases.query",
                method="POST",
                params=query_params
            )
            logger.info(f"[TESTING MODE] Simulated querying for transaction with payment ID {payment_id}")
            
            # Return a mock transaction in testing mode
            return VideoTransaction(
                id=f"test_page_id_VideoTransaction_{payment_id}",
                transaction_id=f"vt-{payment_id}",
                video_id=f"vid-test-{payment_id[-8:]}",
                customer_email="test@example.com",
                customer_name="Test User",
                transaction_type="premium_feature",
                transaction_status=VideoTransactionStatus.PENDING,
                payment_id=payment_id,
                payment_status="pending",
                amount=29.99,
                currency="usd",
                features=[{
                    "feature_id": "feat-001",
                    "feature_type": "export_4k",
                    "name": "4K Export",
                    "description": "Export video in 4K resolution",
                    "price": 29.99
                }],
                business_entity_id="test_entity",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        # Query Notion
        response = self.client.databases.query(**query_params)
        
        # Check if any results
        if not response["results"]:
            return None
        
        # Convert first result to model
        transaction = self._notion_to_model(response["results"][0], VideoTransaction)
        return transaction
    
    except Exception as e:
        logger.error(f"Error finding transaction by payment ID: {e}")
        return None


async def find_video_content_by_task_id(self, task_id: str) -> Optional[VideoContent]:
    """
    Find video content by task ID.
    
    Args:
        task_id: Task ID to search for
        
    Returns:
        VideoContent model or None if not found
    """
    try:
        # Ensure we have a database mapping for VideoContent
        if "VideoContent" not in self.db_mappings:
            # If not in mappings, try to get from environment
            import os
            self.db_mappings["VideoContent"] = os.environ.get("NOTION_VIDEO_CONTENT_DB", "")
            
            if not self.db_mappings["VideoContent"]:
                raise ValueError("No database mapping found for VideoContent")
        
        db_id = self.db_mappings["VideoContent"]
        
        # Prepare query
        query_params = {
            "database_id": db_id,
            "filter": {
                "property": "task_id",
                "rich_text": {
                    "equals": task_id
                }
            }
        }
        
        # Check if Notion API is disabled in testing mode
        if is_api_disabled("notion"):
            TestingMode.log_attempted_api_call(
                api_name="notion",
                endpoint="databases.query",
                method="POST",
                params=query_params
            )
            logger.info(f"[TESTING MODE] Simulated querying for video content with task ID {task_id}")
            
            # Return a mock video content in testing mode
            return VideoContent(
                id=f"test_page_id_VideoContent_{task_id}",
                title=f"Test Video - {task_id[-8:]}",
                description="Test video description",
                content_type="VIDEO",
                stage="IDEA",
                business_entity_id="test_entity",
                topic="Test Topic",
                resolution="1920x1080",
                video_status="pending",
                task_id=task_id,
                created_by="Test Agent",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        # Query Notion
        response = self.client.databases.query(**query_params)
        
        # Check if any results
        if not response["results"]:
            return None
        
        # Convert first result to model
        video_content = self._notion_to_model(response["results"][0], VideoContent)
        return video_content
    
    except Exception as e:
        logger.error(f"Error finding video content by task ID: {e}")
        return None
