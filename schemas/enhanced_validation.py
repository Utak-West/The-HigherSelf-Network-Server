"""
Enhanced Input Validation for The HigherSelf Network Server.

This module provides comprehensive input validation using Pydantic models featuring:
1. Detailed validation rules for common data types
2. Custom validators for complex business rules
3. Consistent validation pattern for all inputs
4. Domain-specific validation models

Usage:
    # Define your data model with validation
    from schemas.enhanced_validation import (
        BaseSchema, EmailStr, PhoneNumber, validate_entity_id,
        regex_patterns, validators
    )

    class CustomerInfo(BaseSchema):
        name: str = Field(..., min_length=2, max_length=100)
        email: EmailStr
        phone: PhoneNumber
        customer_id: str

        _validate_customer_id = validators.field_validator('customer_id')(validate_entity_id)
"""

import json
import re
from datetime import date, datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Pattern,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from utils.error_handling import ValidationException

# Type variable for generic validation
T = TypeVar("T", bound=BaseModel)


# Regular expression patterns for common validations
class RegexPatterns:
    """Common regex patterns for validation."""

    # Entity identifiers
    ENTITY_ID = (
        r"^[a-zA-Z0-9_-]{4,36}$"  # Alphanumeric with underscore and dash, 4-36 chars
    )
    UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

    # Contact information
    PHONE_US = r"^\+?1?\s*\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$"  # US phone format
    PHONE_INTL = r"^\+(?:[0-9] ?){6,14}[0-9]$"  # International phone format

    # Business identifiers
    URL = (
        r"^(https?:\/\/)?(www\.)?([a-zA-Z0-9]+(-[a-zA-Z0-9]+)*\.)+[a-zA-Z]{2,}(\/\S*)?$"
    )
    USERNAME = (
        r"^[a-zA-Z0-9_-]{3,32}$"  # Alphanumeric with underscore and dash, 3-32 chars
    )

    # Financial data
    CREDIT_CARD = r"^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})$"

    # Date and time formats
    ISO_DATE = r"^\d{4}-\d{2}-\d{2}$"
    ISO_DATETIME = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"

    # Semantic versioning
    SEMVER = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"

    # File paths and names
    FILENAME = r"^[a-zA-Z0-9_-][\w\s.-]*$"
    FILE_PATH = r"^(?:[a-zA-Z]:|[\\/])[\\/](?:[\w\s.-]+[\\/])*[\w\s.-]+$"

    # Domain-specific patterns
    EVENT_TYPE = r"^[a-z_]+\.[a-z_]+$"  # namespace.event format
    TAG = r"^[a-z0-9_-]{1,30}$"  # Lowercase alphanumeric with underscore and dash, 1-30 chars


# Create an instance for ease of use
regex_patterns = RegexPatterns()


# Common field types with validation
class PhoneNumber(str):
    """Custom string type for phone numbers with validation."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        """Validate and normalize phone numbers."""
        if not v:
            return None

        # Convert to string if needed
        if not isinstance(v, str):
            v = str(v)

        # Strip whitespace and special characters for comparison
        cleaned = re.sub(r"[\s()\-.]", "", v)

        # Check US format
        if re.match(regex_patterns.PHONE_US, v):
            # Normalize to E.164 format for US numbers
            if cleaned.startswith("+1"):
                return cleaned
            elif cleaned.startswith("1"):
                return "+" + cleaned
            else:
                return "+1" + cleaned

        # Check international format
        elif re.match(regex_patterns.PHONE_INTL, v):
            # Ensure it starts with +
            if not cleaned.startswith("+"):
                return "+" + cleaned
            return cleaned

        raise ValueError("Invalid phone number format")


class EntityType(str, Enum):
    """Types of business entities in the system."""

    CUSTOMER = "customer"
    CONTACT = "contact"
    GALLERY = "gallery"
    ARTIST = "artist"
    ARTWORK = "artwork"
    EVENT = "event"
    AGENT = "agent"
    WORKFLOW = "workflow"
    CAMPAIGN = "campaign"
    SERVICE = "service"
    PRODUCT = "product"


class BaseSchema(BaseModel):
    """Base model for all schemas with enhanced validation."""

    model_config = ConfigDict(
        validate_assignment=True,
        strict=True,
        extra="forbid",
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    @model_validator(mode="before")
    @classmethod
    def check_empty_strings(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert empty strings to None for all string fields."""
        if not isinstance(data, dict):
            return data

        for field_name, value in data.items():
            if isinstance(value, str) and value.strip() == "":
                data[field_name] = None
        return data

    def model_dump_sanitized(self, exclude_none: bool = True) -> Dict[str, Any]:
        """
        Return the model as a dictionary, with sensitive fields redacted.

        This is useful for logging and debugging.
        """
        data = self.model_dump(exclude_none=exclude_none)

        # Redact sensitive fields
        sensitive_fields = [
            "password",
            "api_key",
            "secret",
            "token",
            "credit_card",
            "ssn",
            "social_security",
            "auth",
        ]

        for field in sensitive_fields:
            if field in data:
                data[field] = "***REDACTED***"

        return data

    def validate_business_rules(self) -> None:
        """
        Perform additional business rule validations that go beyond
        simple field-level validations.

        Subclasses should override this method to add domain-specific
        validation rules.

        Raises:
            ValidationException: If business rules are not satisfied
        """
        pass


# Validation utilities
class ValidationUtilities:
    """Collection of reusable validation functions."""

    @staticmethod
    def validate_date_range(
        start_date: Union[date, datetime],
        end_date: Union[date, datetime],
        allow_same_day: bool = True,
    ) -> bool:
        """
        Validate that a start date is before an end date.

        Args:
            start_date: The start date
            end_date: The end date
            allow_same_day: Whether the start and end can be the same day

        Returns:
            bool: True if valid, False otherwise
        """
        if not start_date or not end_date:
            return False

        if allow_same_day:
            return start_date <= end_date
        return start_date < end_date

    @staticmethod
    def validate_entity_id(
        entity_id: str, entity_type: Optional[EntityType] = None
    ) -> str:
        """
        Validate an entity ID format.

        Args:
            entity_id: The entity ID to validate
            entity_type: Optional entity type for specific validation

        Returns:
            str: The validated entity ID

        Raises:
            ValueError: If the entity ID is invalid
        """
        if not entity_id:
            raise ValueError("Entity ID cannot be empty")

        # Basic format validation
        if not re.match(regex_patterns.ENTITY_ID, entity_id):
            raise ValueError(
                f"Invalid entity ID format: {entity_id}. "
                "Use alphanumeric characters, underscores, and dashes (4-36 chars)."
            )

        # Type-specific validation
        if entity_type:
            prefix = entity_type.value[:3].lower()
            if not entity_id.startswith(f"{prefix}_"):
                raise ValueError(
                    f"Entity ID for {entity_type.value} must start with '{prefix}_'"
                )

        return entity_id

    @staticmethod
    def validate_json_size(json_data: Any, max_size_kb: int = 100) -> Any:
        """
        Validate that JSON data doesn't exceed a maximum size.

        Args:
            json_data: The JSON data to validate (dict, list, or JSON string)
            max_size_kb: Maximum size in kilobytes

        Returns:
            Any: The validated JSON data

        Raises:
            ValueError: If the JSON data exceeds the maximum size
        """
        if isinstance(json_data, str):
            # If it's a string, estimate its size
            data_size = len(json_data.encode("utf-8")) / 1024
        else:
            # If it's a Python object, convert to JSON string to get accurate size
            data_size = len(json.dumps(json_data).encode("utf-8")) / 1024

        if data_size > max_size_kb:
            raise ValueError(
                f"JSON data size ({data_size:.2f}KB) exceeds maximum allowed "
                f"size of {max_size_kb}KB"
            )

        return json_data

    @staticmethod
    def validate_list_length(
        items: List[Any], min_length: int = 0, max_length: int = 100
    ) -> List[Any]:
        """
        Validate that a list has an acceptable length.

        Args:
            items: The list to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length

        Returns:
            List[Any]: The validated list

        Raises:
            ValueError: If the list length is outside the allowed range
        """
        if not isinstance(items, list):
            raise ValueError(f"Expected a list, got {type(items).__name__}")

        if len(items) < min_length:
            raise ValueError(
                f"List must contain at least {min_length} items, got {len(items)}"
            )

        if len(items) > max_length:
            raise ValueError(
                f"List cannot contain more than {max_length} items, got {len(items)}"
            )

        return items

    @staticmethod
    def validate_unique_values(items: List[Any]) -> List[Any]:
        """
        Validate that a list contains only unique values.

        Args:
            items: The list to validate

        Returns:
            List[Any]: The validated list

        Raises:
            ValueError: If the list contains duplicate values
        """
        if not items:
            return items

        unique_items = set()
        duplicates = []

        for item in items:
            if item in unique_items:
                duplicates.append(item)
            unique_items.add(item)

        if duplicates:
            raise ValueError(
                f"List contains duplicate values: {', '.join(str(d) for d in duplicates)}"
            )

        return items


# Create an instance for ease of use
validators = ValidationUtilities()


# Validation functions for field-level validation
def validate_entity_id(value: str, entity_type: Optional[EntityType] = None) -> str:
    """
    Validate an entity ID format.

    This function is designed to be used with Pydantic's field_validator.

    Args:
        value: The entity ID to validate
        entity_type: Optional entity type for specific validation

    Returns:
        str: The validated entity ID

    Raises:
        ValueError: If the entity ID is invalid
    """
    return validators.validate_entity_id(value, entity_type)


# Domain-specific validation models
class WebhookPayload(BaseSchema):
    """Base model for webhook payloads with enhanced validation."""

    source: str
    event_type: str
    timestamp: datetime
    payload: Dict[str, Any]

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v):
        """Ensure event_type follows the namespace.event format."""
        if not re.match(regex_patterns.EVENT_TYPE, v):
            raise ValueError(
                "event_type must be in format 'namespace.event' using only lowercase "
                "letters and underscores"
            )
        return v

    @field_validator("payload")
    @classmethod
    def validate_payload_size(cls, v):
        """Ensure payload is not too large."""
        return validators.validate_json_size(v, max_size_kb=1024)  # 1MB limit

    @model_validator(mode="after")
    def validate_source_matches_event(self):
        """Ensure source is consistent with event_type."""
        if (
            self.source
            and self.event_type
            and not self.event_type.startswith(f"{self.source}.")
        ):
            raise ValueError(f"event_type must start with '{self.source}.'")
        return self


class ContactInfo(BaseSchema):
    """Reusable contact information model with validation."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[PhoneNumber] = None
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v):
        """Convert email to lowercase."""
        return v.lower() if v else None


class TagList(BaseSchema):
    """Model for a list of tags with validation."""

    tags: List[str] = Field(default_factory=list)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Ensure tags are valid."""
        # Validate list length
        validators.validate_list_length(v, max_length=20)

        # Validate individual tags
        for tag in v:
            if not re.match(regex_patterns.TAG, tag):
                raise ValueError(
                    f"Invalid tag format: {tag}. Use only lowercase letters, numbers, "
                    "underscores, and hyphens (1-30 characters)."
                )

        # Validate uniqueness
        validators.validate_unique_values(v)

        return v


class DateRangeFilter(BaseSchema):
    """Date range filter for queries."""

    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_date_range(self):
        """Ensure start_date is before end_date."""
        if not validators.validate_date_range(self.start_date, self.end_date):
            raise ValueError("start_date must be on or before end_date")
        return self


class PaginationParams(BaseSchema):
    """Pagination parameters for list endpoints."""

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    def __init__(self, **data):
        if "page" not in data:
            data["page"] = 1
        if "page_size" not in data:
            data["page_size"] = 20
        super().__init__(**data)

    def get_offset(self) -> int:
        """Calculate the offset for database queries."""
        return (self.page - 1) * self.page_size


class SortingParams(BaseSchema):
    """Sorting parameters for list endpoints."""

    sort_by: str
    sort_order: str = Field("asc", pattern="^(asc|desc)$")

    def get_sort_direction(self) -> bool:
        """Get the sort direction as a boolean for database queries."""
        return self.sort_order.lower() == "asc"


# Composite models for common request patterns
class ListQueryParams(BaseSchema):
    """Common parameters for list endpoints."""

    pagination: PaginationParams = Field(
        default_factory=lambda: PaginationParams(page=1, page_size=20)
    )
    sorting: Optional[SortingParams] = None
    filters: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, v):
        """Validate filter parameters."""
        # Limit the size of filters to prevent abuse
        return validators.validate_json_size(v, max_size_kb=5)


# Factory functions for creating validation models
def create_id_validator(
    entity_type: EntityType, id_field_name: str = "id"
) -> Callable[[Type[T]], Type[T]]:
    """
    Create a validator for entity IDs.

    Args:
        entity_type: The type of entity
        id_field_name: The name of the ID field

    Returns:
        Callable: A decorator that adds ID validation to a Pydantic model
    """

    def validator(cls: Type[T]) -> Type[T]:
        # Create the validator function
        def validate_id(value: str) -> str:
            return validators.validate_entity_id(value, entity_type)

        # Add the validator to the class
        setattr(
            cls,
            f"_validate_{id_field_name}",
            field_validator(id_field_name)(validate_id),
        )

        return cls

    return validator


def validate_with_exception(data: Any, model_cls: Type[BaseSchema]) -> BaseSchema:
    """
    Validate data against a Pydantic model, raising a custom exception.

    This function wraps Pydantic validation with our application-specific
    ValidationException for consistent error handling.

    Args:
        data: The data to validate
        model_cls: The Pydantic model class to validate against

    Returns:
        BaseSchema: The validated model instance

    Raises:
        ValidationException: If validation fails
    """
    try:
        instance = model_cls.model_validate(data)
        # Apply additional business rule validations
        instance.validate_business_rules()
        return instance
    except ValueError as e:
        # Convert Pydantic validation errors to our application-specific exception
        raise ValidationException(message=str(e), details={"model": model_cls.__name__})


# Example domain-specific models
class CustomerData(BaseSchema):
    """Customer data with business validation rules."""

    customer_id: str
    contact_info: ContactInfo
    tags: Optional[List[str]] = Field(default_factory=list)
    tier: str = Field(..., pattern="^(free|basic|premium|enterprise)$")

    # Apply entity ID validation
    _validate_customer_id = field_validator("customer_id")(
        lambda v: validate_entity_id(v, EntityType.CUSTOMER)
    )

    # Apply tags validation
    _validate_tags = field_validator("tags")(
        lambda v: validators.validate_list_length(v, max_length=20)
    )

    def validate_business_rules(self) -> None:
        """Apply customer-specific business rules."""
        # Enterprise customers require a phone number
        if self.tier == "enterprise" and not self.contact_info.phone:
            raise ValidationException(
                message="Enterprise customers must provide a phone number",
                details={"customer_id": self.customer_id, "tier": self.tier},
            )
