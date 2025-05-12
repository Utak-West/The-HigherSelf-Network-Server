#!/usr/bin/env python3
"""
Notion data models for The HigherSelf Network Server.
These models represent Notion pages, databases, and integration configurations.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class NotionPage(BaseModel):
    """
    Represents a Notion page with its properties.
    """
    id: str
    title: str
    url: Optional[str] = None
    parent_id: Optional[str] = None
    parent_type: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    content: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the page to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "parent_id": self.parent_id,
            "parent_type": self.parent_type,
            "properties": self.properties,
            "content": self.content
        }


class NotionIntegrationConfig(BaseModel):
    """
    Configuration for Notion integration.
    """
    token: str
    database_mappings: Dict[str, str] = Field(default_factory=dict)
    last_sync: Optional[datetime] = None
    
    # Legacy fields for backward compatibility
    api_token: Optional[str] = None
    databases: Dict[str, str] = Field(default_factory=dict)
    
    # Database IDs for different types of data
    clients_database_id: Optional[str] = None
    products_database_id: Optional[str] = None
    orders_database_id: Optional[str] = None
    appointments_database_id: Optional[str] = None
    bookings_database_id: Optional[str] = None
    feedback_database_id: Optional[str] = None
    active_workflow_database_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {
            "token": self.token,
            "database_mappings": self.database_mappings,
            "last_sync": self.last_sync,
            "api_token": self.api_token or self.token,
            "databases": self.databases,
            "clients_database_id": self.clients_database_id,
            "products_database_id": self.products_database_id,
            "orders_database_id": self.orders_database_id,
            "appointments_database_id": self.appointments_database_id,
            "bookings_database_id": self.bookings_database_id,
            "feedback_database_id": self.feedback_database_id,
            "active_workflow_database_id": self.active_workflow_database_id
        }
