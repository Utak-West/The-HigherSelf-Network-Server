"""
Airtable integration service for The HigherSelf Network Server.
This service provides methods for interacting with Airtable.
"""

import os
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from pydantic import BaseModel


class AirtableConfig(BaseModel):
    """Configuration for Airtable API integration."""

    api_key: str
    base_id: str

    class Config:
        env_prefix = "AIRTABLE_"


class AirtableRecord(BaseModel):
    """Model representing an Airtable record."""

    id: Optional[str] = None
    fields: Dict[str, Any]


class AirtableService:
    """
    Service for interacting with the Airtable API.
    Serves as a secondary data destination while maintaining Notion as the primary data hub.
    """

    def __init__(self, api_key: str = None, base_id: str = None):
        """
        Initialize the Airtable service.

        Args:
            api_key: Airtable API key
            base_id: Airtable base ID
        """
        self.api_key = api_key or os.environ.get("AIRTABLE_API_KEY")
        self.base_id = base_id or os.environ.get("AIRTABLE_BASE_ID")

        if not self.api_key:
            logger.warning(
                "Airtable API key not set. Some functionality may be limited."
            )

        if not self.base_id:
            logger.warning(
                "Airtable base ID not set. Some functionality may be limited."
            )

        self.base_url = f"https://api.airtable.com/v0/{self.base_id}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_record(
        self, table_name: str, fields: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create a new record in an Airtable table.

        Args:
            table_name: Name of the table
            fields: Record fields to create

        Returns:
            Record ID if successful, None otherwise
        """
        if not self.api_key or not self.base_id:
            logger.error("Airtable credentials not configured")
            return None

        url = f"{self.base_url}/{table_name}"
        payload = {"fields": fields}

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            record_id = response.json().get("id")
            logger.info(f"Created Airtable record in {table_name}: {record_id}")
            return record_id
        except Exception as e:
            logger.error(f"Error creating Airtable record: {e}")
            return None

    async def get_record(
        self, table_name: str, record_id: str
    ) -> Optional[AirtableRecord]:
        """
        Retrieve a record from an Airtable table.

        Args:
            table_name: Name of the table
            record_id: ID of the record to retrieve

        Returns:
            Record data if found, None otherwise
        """
        if not self.api_key or not self.base_id:
            logger.error("Airtable credentials not configured")
            return None

        url = f"{self.base_url}/{table_name}/{record_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return AirtableRecord(id=data.get("id"), fields=data.get("fields", {}))
        except Exception as e:
            logger.error(f"Error getting Airtable record: {e}")
            return None

    async def update_record(
        self, table_name: str, record_id: str, fields: Dict[str, Any]
    ) -> bool:
        """
        Update an existing record in an Airtable table.

        Args:
            table_name: Name of the table
            record_id: ID of the record to update
            fields: Record fields to update

        Returns:
            True if successful, False otherwise
        """
        if not self.api_key or not self.base_id:
            logger.error("Airtable credentials not configured")
            return False

        url = f"{self.base_url}/{table_name}/{record_id}"
        payload = {"fields": fields}

        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Updated Airtable record in {table_name}: {record_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating Airtable record: {e}")
            return False

    async def delete_record(self, table_name: str, record_id: str) -> bool:
        """
        Delete a record from an Airtable table.

        Args:
            table_name: Name of the table
            record_id: ID of the record to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.api_key or not self.base_id:
            logger.error("Airtable credentials not configured")
            return False

        url = f"{self.base_url}/{table_name}/{record_id}"

        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            logger.info(f"Deleted Airtable record in {table_name}: {record_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting Airtable record: {e}")
            return False

    async def list_records(
        self,
        table_name: str,
        max_records: int = 100,
        filter_by_formula: Optional[str] = None,
    ) -> List[AirtableRecord]:
        """
        List records from an Airtable table.

        Args:
            table_name: Name of the table
            max_records: Maximum number of records to retrieve
            filter_by_formula: Formula to filter records

        Returns:
            List of records
        """
        if not self.api_key or not self.base_id:
            logger.error("Airtable credentials not configured")
            return []

        url = f"{self.base_url}/{table_name}"
        params = {"maxRecords": max_records}

        if filter_by_formula:
            params["filterByFormula"] = filter_by_formula

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            records = response.json().get("records", [])
            return [
                AirtableRecord(id=r.get("id"), fields=r.get("fields", {}))
                for r in records
            ]
        except Exception as e:
            logger.error(f"Error listing Airtable records: {e}")
            return []
