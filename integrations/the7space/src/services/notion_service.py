"""
Notion integration service for The 7 Space.
Handles all interactions with Notion databases via the Notion API.
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from loguru import logger
from notion_client import Client
from pydantic import BaseModel

from ..models.notion_models import (
    NotionIntegrationConfig,
    NotionPage,
    NotionPropertyType,
)

T = TypeVar("T", bound=BaseModel)


class NotionService(Generic[T]):
    """
    Service for interacting with Notion databases.
    Handles CRUD operations and maintains synchronization between
    The 7 Space's data models and Notion databases.
    """

    def __init__(self, config: NotionIntegrationConfig, model_class: Type[T]):
        """
        Initialize the Notion service with API token and database mappings.

        Args:
            config: Configuration for Notion API
            model_class: The Pydantic model class for type checking
        """
        self.notion = Client(auth=config.notion_api_key)
        self.database_ids = config.database_ids
        self.model_class = model_class

        # Validate connection
        try:
            self.notion.users.me()
            logger.info(
                f"Successfully connected to Notion API with {model_class.__name__} model"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Notion API: {e}")
            raise ConnectionError(f"Failed to connect to Notion API: {e}")

    async def create_page(self, model_instance: T, database_name: str) -> str:
        """
        Create a new page in the specified Notion database from model instance.

        Args:
            model_instance: Pydantic model instance to create in Notion
            database_name: Name of the database in config.database_ids

        Returns:
            Notion page ID of the created page
        """
        database_id = self.database_ids.get(database_name)
        if not database_id:
            raise ValueError(f"Database '{database_name}' not found in configuration")

        # Convert model to Notion properties
        properties = self._model_to_notion_properties(model_instance)

        # Create page in Notion
        try:
            response = self.notion.pages.create(
                parent={"database_id": database_id}, properties=properties
            )
            page_id = response["id"]

            # Update model with Notion page ID if it has that field
            if hasattr(model_instance, "notion_page_id"):
                model_instance.notion_page_id = page_id

            logger.info(f"Created Notion page {page_id} in database {database_name}")
            return page_id
        except Exception as e:
            logger.error(f"Failed to create Notion page: {e}")
            raise

    async def update_page(self, page_id: str, model_instance: T) -> bool:
        """
        Update an existing Notion page with data from model instance.

        Args:
            page_id: Notion page ID to update
            model_instance: Pydantic model instance with updated data

        Returns:
            Success status
        """
        # Convert model to Notion properties
        properties = self._model_to_notion_properties(model_instance)

        # Update page in Notion
        try:
            self.notion.pages.update(page_id=page_id, properties=properties)
            logger.info(f"Updated Notion page {page_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update Notion page {page_id}: {e}")
            raise

    async def get_page(self, page_id: str) -> T:
        """
        Retrieve a page from Notion and convert to model instance.

        Args:
            page_id: Notion page ID to retrieve

        Returns:
            Model instance populated with page data
        """
        try:
            response = self.notion.pages.retrieve(page_id=page_id)
            model_data = self._notion_to_model_data(response)
            return self.model_class(**model_data)
        except Exception as e:
            logger.error(f"Failed to retrieve Notion page {page_id}: {e}")
            raise

    async def query_database(
        self,
        database_name: str,
        filter_conditions: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
    ) -> List[T]:
        """
        Query a Notion database with optional filters and sorting.

        Args:
            database_name: Name of database in config.database_ids
            filter_conditions: Notion API filter object
            sorts: Notion API sort objects

        Returns:
            List of model instances from query results
        """
        database_id = self.database_ids.get(database_name)
        if not database_id:
            raise ValueError(f"Database '{database_name}' not found in configuration")

        query_params = {}
        if filter_conditions:
            query_params["filter"] = filter_conditions
        if sorts:
            query_params["sorts"] = sorts

        try:
            response = self.notion.databases.query(
                database_id=database_id, **query_params
            )

            results = []
            for page in response.get("results", []):
                model_data = self._notion_to_model_data(page)
                model_instance = self.model_class(**model_data)
                results.append(model_instance)

            # Handle pagination if needed
            has_more = response.get("has_more", False)
            next_cursor = response.get("next_cursor")

            while has_more and next_cursor:
                query_params["start_cursor"] = next_cursor
                response = self.notion.databases.query(
                    database_id=database_id, **query_params
                )

                for page in response.get("results", []):
                    model_data = self._notion_to_model_data(page)
                    model_instance = self.model_class(**model_data)
                    results.append(model_instance)

                has_more = response.get("has_more", False)
                next_cursor = response.get("next_cursor")

            logger.info(f"Retrieved {len(results)} records from {database_name}")
            return results
        except Exception as e:
            logger.error(f"Failed to query Notion database {database_name}: {e}")
            raise

    async def delete_page(self, page_id: str) -> bool:
        """
        Archive a page in Notion (Notion API doesn't support true deletion).

        Args:
            page_id: Notion page ID to archive

        Returns:
            Success status
        """
        try:
            self.notion.pages.update(page_id=page_id, archived=True)
            logger.info(f"Archived Notion page {page_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to archive Notion page {page_id}: {e}")
            raise

    def _model_to_notion_properties(self, model_instance: T) -> Dict[str, Any]:
        """
        Convert a Pydantic model to Notion page properties format.

        Args:
            model_instance: Pydantic model instance to convert

        Returns:
            Notion properties dictionary
        """
        properties = {}
        model_dict = model_instance.model_dump()

        for field_name, field_value in model_dict.items():
            if field_name == "notion_page_id":
                continue  # Skip the Notion page ID field

            # Handle different field types based on value and model field type
            if field_value is None:
                continue

            if isinstance(field_value, str):
                properties[field_name] = {
                    "rich_text": [{"text": {"content": field_value}}]
                }

                # Title field should be handled differently
                if field_name == "name" or field_name == "title":
                    properties[field_name] = {
                        "title": [{"text": {"content": field_value}}]
                    }

            elif isinstance(field_value, (int, float)):
                properties[field_name] = {"number": field_value}

            elif isinstance(field_value, bool):
                properties[field_name] = {"checkbox": field_value}

            elif isinstance(field_value, datetime):
                properties[field_name] = {"date": {"start": field_value.isoformat()}}

            elif isinstance(field_value, list):
                if field_value and all(isinstance(item, str) for item in field_value):
                    # Assume it's a multi-select if all items are strings
                    properties[field_name] = {
                        "multi_select": [{"name": item} for item in field_value]
                    }
                # Handle other list types as needed

            elif isinstance(field_value, dict):
                # Handle rich text for dictionaries by converting to JSON
                json_value = json.dumps(field_value)
                properties[field_name] = {
                    "rich_text": [{"text": {"content": json_value}}]
                }

        return properties

    def _notion_to_model_data(self, notion_page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Notion page data to a dictionary for model instantiation.

        Args:
            notion_page: Notion page data

        Returns:
            Dictionary compatible with model_class
        """
        model_data = {}
        page_properties = notion_page.get("properties", {})

        # Add the Notion page ID if model supports it
        model_fields = self.model_class.model_fields
        if "notion_page_id" in model_fields:
            model_data["notion_page_id"] = notion_page.get("id")

        for prop_name, prop_data in page_properties.items():
            prop_type = prop_data.get("type")

            if prop_type == "title":
                title_items = prop_data.get("title", [])
                if title_items:
                    model_data[prop_name] = title_items[0].get("plain_text", "")

            elif prop_type == "rich_text":
                text_items = prop_data.get("rich_text", [])
                if text_items:
                    text_content = text_items[0].get("plain_text", "")

                    # Try to parse as JSON if it looks like it
                    if text_content.startswith("{") and text_content.endswith("}"):
                        try:
                            model_data[prop_name] = json.loads(text_content)
                        except json.JSONDecodeError:
                            model_data[prop_name] = text_content
                    else:
                        model_data[prop_name] = text_content

            elif prop_type == "number":
                model_data[prop_name] = prop_data.get("number")

            elif prop_type == "checkbox":
                model_data[prop_name] = prop_data.get("checkbox")

            elif prop_type == "date":
                date_obj = prop_data.get("date", {})
                if date_obj and date_obj.get("start"):
                    start_date = date_obj.get("start")
                    model_data[prop_name] = datetime.fromisoformat(start_date)

            elif prop_type == "multi_select":
                select_items = prop_data.get("multi_select", [])
                model_data[prop_name] = [item.get("name") for item in select_items]

            elif prop_type == "select":
                select_obj = prop_data.get("select", {})
                if select_obj:
                    model_data[prop_name] = select_obj.get("name")

            elif prop_type == "relation":
                relation_items = prop_data.get("relation", [])
                model_data[prop_name] = [item.get("id") for item in relation_items]

        return model_data


# Factory function to create type-specific Notion services
def create_notion_service(
    config: NotionIntegrationConfig, model_class: Type[T]
) -> NotionService[T]:
    """
    Create a NotionService instance for a specific model type.

    Args:
        config: Notion integration configuration
        model_class: Pydantic model class to use with the service

    Returns:
        Typed NotionService instance
    """
    return NotionService(config, model_class)
