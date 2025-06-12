"""
Pydantic models for Notion integration.
Following The HigherSelf Network standardized data structure guidelines.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Enum, Field, enum, field_validator


class NotionPropertyType(str, Enum):
    """Enum for Notion property types"""

    TITLE = "title"
    RICH_TEXT = "rich_text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    PEOPLE = "people"
    FILES = "files"
    CHECKBOX = "checkbox"
    URL = "url"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    FORMULA = "formula"
    RELATION = "relation"
    ROLLUP = "rollup"
    CREATED_TIME = "created_time"
    CREATED_BY = "created_by"
    LAST_EDITED_TIME = "last_edited_time"
    LAST_EDITED_BY = "last_edited_by"
    STATUS = "status"


class NotionTextContent(BaseModel):
    """Model for Notion text content"""

    content: str
    link: Optional[Dict[str, str]] = None


class NotionText(BaseModel):
    """Model for Notion text"""

    type: str = "text"
    text: NotionTextContent
    annotations: Optional[Dict[str, Any]] = None
    plain_text: Optional[str] = None
    href: Optional[str] = None


class NotionRichText(BaseModel):
    """Model for Notion rich text property"""

    rich_text: List[NotionText]


class NotionTitle(BaseModel):
    """Model for Notion title property"""

    title: List[NotionText]


class NotionSelect(BaseModel):
    """Model for Notion select property"""

    select: Dict[str, str]


class NotionMultiSelect(BaseModel):
    """Model for Notion multi-select property"""

    multi_select: List[Dict[str, str]]


class NotionDate(BaseModel):
    """Model for Notion date property"""

    date: Dict[str, Any]


class NotionNumber(BaseModel):
    """Model for Notion number property"""

    number: float


class NotionCheckbox(BaseModel):
    """Model for Notion checkbox property"""

    checkbox: bool


class NotionStatus(BaseModel):
    """Model for Notion status property"""

    status: Dict[str, str]


class NotionRelation(BaseModel):
    """Model for Notion relation property"""

    relation: List[Dict[str, str]]


class NotionPropertyValue(BaseModel):
    """Model for Notion property value"""

    id: str
    type: NotionPropertyType
    value: Union[
        NotionTitle,
        NotionRichText,
        NotionSelect,
        NotionMultiSelect,
        NotionDate,
        NotionNumber,
        NotionCheckbox,
        NotionStatus,
        NotionRelation,
        Dict[str, Any],
    ]


class NotionPageProperties(BaseModel):
    """Model for Notion page properties"""

    properties: Dict[str, NotionPropertyValue]


class NotionPage(BaseModel):
    """Model for Notion page"""

    id: str
    created_time: datetime
    last_edited_time: datetime
    url: str
    properties: Dict[str, Any]

    @field_validator("properties", mode="before")
    @classmethod
    def validate_properties(cls, v):
        """Validate properties structure"""
        # Additional validation logic could be implemented here
        return v


class NotionIntegrationConfig(BaseModel):
    """Configuration for Notion integration"""

    notion_api_key: str = Field(..., description="Notion API token")
    database_ids: Dict[str, str] = Field(
        ..., description="Mapping of database names to their IDs"
    )

    class Config:
        env_file = ".env"
        env_prefix = "NOTION_"
