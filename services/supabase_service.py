"""
Supabase integration service for The HigherSelf Network Server.
Handles all interactions with the Supabase database, following the standardized
data structures and patterns defined in the Pydantic models.
"""

import os
import json
# import logging # Replaced by loguru
from loguru import logger # Added for direct loguru usage
from typing import Dict, Any, List, Optional, Type, Union, TypeVar
from datetime import datetime

import httpx
from pydantic import BaseModel, ValidationError

from models.base import NotionIntegrationConfig
from config.testing_mode import is_api_disabled, TestingMode


T = TypeVar('T', bound=BaseModel)


class SupabaseConfig(BaseModel):
    """Configuration for Supabase integration."""
    url: str
    api_key: str
    project_id: str


class SupabaseService:
    """Service for interacting with Supabase databases."""

    def __init__(self, config: SupabaseConfig):
        """
        Initialize the Supabase service with the provided configuration.

        Args:
            config: SupabaseConfig containing URL and API key
        """
        self.config = config
        self.url = config.url
        self.api_key = config.api_key
        self.project_id = config.project_id
        # self.logger removed, use global loguru logger
        logger.info(f"Supabase service initialized with URL: {self.url} for {self.__class__.__name__}")

        # Check if we're in testing mode
        if is_api_disabled("supabase"):
            logger.warning(f"TESTING MODE ACTIVE for {self.__class__.__name__}: Supabase API calls will be simulated")

    async def _make_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the Supabase API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path
            data: Request data
            params: Query parameters

        Returns:
            Response data
        """
        headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        url = f"{self.url}{path}"

        # Check if Supabase API is disabled in testing mode
        if is_api_disabled("supabase"):
            # Force disable the API in testing mode
            from config.testing_mode import TestingMode
            TestingMode.add_disabled_api("supabase")

            TestingMode.log_attempted_api_call(
                api_name="supabase",
                endpoint=path,
                method=method,
                params={"data": data, "params": params}
            )
            logger.info(f"[TESTING MODE] Simulated {method} request to {path}")
            return {"data": [], "status": 200, "statusText": "OK"}

        try:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error making request to Supabase: {e}")
            raise

    async def create_record(self, table_name: str, model: BaseModel) -> Optional[str]:
        """
        Create a record in a Supabase table.

        Args:
            table_name: Name of the table
            model: Pydantic model instance

        Returns:
            ID of the created record
        """
        try:
            # Convert model to dict and remove None values
            data = {k: v for k, v in model.dict().items() if v is not None}

            # Make request to Supabase
            response = await self._make_request(
                method="POST",
                path=f"/rest/v1/{table_name}",
                data=data,
                params={"select": "id"}
            )

            # Extract ID from response
            if response and "data" in response and len(response["data"]) > 0:
                return response["data"][0]["id"]

            return None
        except Exception as e:
            logger.error(f"Error creating record in Supabase: {e}")
            return None

    async def update_record(self, table_name: str, record_id: str, model: BaseModel) -> bool:
        """
        Update a record in a Supabase table.

        Args:
            table_name: Name of the table
            record_id: ID of the record to update
            model: Pydantic model instance

        Returns:
            True if update was successful
        """
        try:
            # Convert model to dict and remove None values
            data = {k: v for k, v in model.dict().items() if v is not None}

            # Make request to Supabase
            await self._make_request(
                method="PUT",
                path=f"/rest/v1/{table_name}",
                data=data,
                params={"id": f"eq.{record_id}"}
            )

            return True
        except Exception as e:
            logger.error(f"Error updating record in Supabase: {e}")
            return False

    async def get_record(self, table_name: str, record_id: str, model_class: Type[T]) -> Optional[T]:
        """
        Get a record from a Supabase table.

        Args:
            table_name: Name of the table
            record_id: ID of the record to get
            model_class: Pydantic model class

        Returns:
            Model instance
        """
        try:
            # Make request to Supabase
            response = await self._make_request(
                method="GET",
                path=f"/rest/v1/{table_name}",
                params={"id": f"eq.{record_id}", "select": "*"}
            )

            # Extract data from response
            if response and "data" in response and len(response["data"]) > 0:
                return model_class(**response["data"][0])

            return None
        except Exception as e:
            logger.error(f"Error getting record from Supabase: {e}")
            return None

    async def query_records(
        self,
        table_name: str,
        model_class: Type[T],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[T]:
        """
        Query records from a Supabase table.

        Args:
            table_name: Name of the table
            model_class: Pydantic model class
            filters: Filter conditions
            limit: Maximum number of results

        Returns:
            List of model instances
        """
        try:
            # Prepare query parameters
            params = {"select": "*", "limit": limit}

            # Add filters if provided
            if filters:
                for key, value in filters.items():
                    params[key] = value

            # Make request to Supabase
            response = await self._make_request(
                method="GET",
                path=f"/rest/v1/{table_name}",
                params=params
            )

            # Extract data from response
            results = []
            if response and "data" in response:
                for item in response["data"]:
                    try:
                        model = model_class(**item)
                        results.append(model)
                    except ValidationError as e:
                        logger.warning(f"Error converting Supabase record to model: {e}")

            return results
        except Exception as e:
            logger.error(f"Error querying records from Supabase: {e}")
            return []

    async def delete_record(self, table_name: str, record_id: str) -> bool:
        """
        Delete a record from a Supabase table.

        Args:
            table_name: Name of the table
            record_id: ID of the record to delete

        Returns:
            True if deletion was successful
        """
        try:
            # Make request to Supabase
            await self._make_request(
                method="DELETE",
                path=f"/rest/v1/{table_name}",
                params={"id": f"eq.{record_id}"}
            )

            return True
        except Exception as e:
            logger.error(f"Error deleting record from Supabase: {e}")
            return False

    async def execute_sql(self, sql: str, params: List[Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query on Supabase.

        Args:
            sql: SQL query to execute
            params: Query parameters

        Returns:
            Query results
        """
        # Check if Supabase API is disabled in testing mode
        if is_api_disabled("supabase"):
            TestingMode.log_attempted_api_call(
                api_name="supabase",
                endpoint="/rest/v1/rpc/execute_sql",
                method="POST",
                params={"sql": sql, "params": params}
            )
            logger.info(f"[TESTING MODE] Simulated SQL query: {sql}")
            return []

        try:
            # For testing purposes, return empty results
            # In a real implementation, this would make a request to Supabase
            logger.warning("Mock SQL execution - returning empty results")
            return []
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            raise

    @classmethod
    async def create_from_env(cls) -> 'SupabaseService':
        """
        Create a SupabaseService instance from environment variables.

        Returns:
            SupabaseService instance
        """
        url = os.environ.get("SUPABASE_URL")
        api_key = os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_API_KEY"))
        project_id = os.environ.get("SUPABASE_PROJECT_ID", "default")

        if not url or not api_key:
            logger.warning("Missing Supabase configuration, using mock configuration for testing")
            url = "https://mock-supabase-url.com"
            api_key = "mock-api-key"
            project_id = "mock-project-id"

            # Force testing mode
            from config.testing_mode import TestingMode
            TestingMode.add_disabled_api("supabase")

        config = SupabaseConfig(url=url, api_key=api_key, project_id=project_id)
        return cls(config)


# Singleton instance
_supabase_service_instance = None

async def get_supabase_service() -> SupabaseService:
    """
    Get or create the Supabase service singleton.

    Returns:
        SupabaseService instance
    """
    global _supabase_service_instance
    if _supabase_service_instance is None:
        try:
            _supabase_service_instance = await SupabaseService.create_from_env()
        except Exception as e:
            logger.error(f"Error creating Supabase service: {e}")
            raise
    return _supabase_service_instance
