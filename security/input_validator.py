"""
Input validation and sanitization for LangChain operations.
"""

import json
import re
from typing import Any, Dict, List

from pydantic import BaseModel, validator


class SecureInput(BaseModel):
    """Validates and sanitizes inputs before LLM processing."""

    user_input: str
    agent_name: str
    task_type: str

    @validator("user_input")
    def sanitize_input(cls, v):
        """Remove potentially harmful content."""
        if not v:
            return v

        # Remove potential injection attempts
        v = re.sub(r"<script.*?</script>", "", v, flags=re.DOTALL | re.IGNORECASE)
        v = re.sub(r"<iframe.*?</iframe>", "", v, flags=re.DOTALL | re.IGNORECASE)
        v = re.sub(r"javascript:", "", v, flags=re.IGNORECASE)

        # Remove potential prompt injection patterns
        injection_patterns = [
            r"ignore previous instructions",
            r"forget everything",
            r"new instructions:",
            r"system override",
            r"admin mode",
            r"developer mode",
            r"jailbreak",
            r"system:",
            r"assistant:",
            r"human:",
            r"user:",
            r"ai:",
            r"chatbot:",
        ]

        for pattern in injection_patterns:
            v = re.sub(pattern, "", v, flags=re.IGNORECASE)

        # Remove excessive whitespace
        v = re.sub(r"\s+", " ", v)

        # Limit length
        if len(v) > 10000:
            v = v[:10000]

        return v.strip()

    @validator("agent_name")
    def validate_agent(cls, v):
        """Ensure agent name is valid."""
        valid_agents = [
            "Nyra",
            "Solari",
            "Ruvo",
            "Liora",
            "Sage",
            "Elan",
            "Zevi",
            "Grace",
            "Atlas",
        ]
        if v not in valid_agents:
            raise ValueError(f"Invalid agent name: {v}")
        return v

    @validator("task_type")
    def validate_task_type(cls, v):
        """Ensure task type is valid."""
        valid_types = [
            "lead_processing",
            "booking_management",
            "content_generation",
            "task_orchestration",
            "community_engagement",
            "audience_analysis",
            "knowledge_retrieval",
            "workflow_management",
            "general",
        ]
        if v not in valid_types:
            v = "general"  # Default to general if invalid
        return v


class OutputFilter:
    """Filters LLM outputs for security and compliance."""

    @staticmethod
    def filter_sensitive_data(output: str) -> str:
        """Remove or mask sensitive information."""
        if not output:
            return output

        # Mask email addresses
        output = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL]", output)

        # Mask phone numbers (various formats)
        output = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]", output)
        output = re.sub(r"\(\d{3}\)\s*\d{3}[-.]?\d{4}", "[PHONE]", output)

        # Mask credit card numbers
        output = re.sub(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "[CARD]", output)

        # Mask SSN
        output = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]", output)

        # Mask potential API keys (long alphanumeric strings)
        output = re.sub(r"\b[A-Za-z0-9]{32,}\b", "[API_KEY]", output)

        return output

    @staticmethod
    def validate_json_output(output: str) -> Dict[str, Any]:
        """Validate and sanitize JSON outputs."""
        try:
            data = json.loads(output)
            return OutputFilter._sanitize_dict(data)
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON output",
                "raw_output": output[:500] + "..." if len(output) > 500 else output,
            }

    @staticmethod
    def _sanitize_dict(data: Any) -> Any:
        """Recursively sanitize dictionary data."""
        if isinstance(data, dict):
            return {k: OutputFilter._sanitize_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [OutputFilter._sanitize_dict(item) for item in data]
        elif isinstance(data, str):
            return OutputFilter.filter_sensitive_data(data)
        else:
            return data

    @staticmethod
    def check_output_safety(output: str) -> bool:
        """Check if output contains potentially harmful content."""
        if not output:
            return True

        # Check for potential harmful patterns
        harmful_patterns = [
            r"<script",
            r"javascript:",
            r"eval\(",
            r"exec\(",
            r"system\(",
            r"import os",
            r"__import__",
        ]

        for pattern in harmful_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return False

        return True


class InputLengthValidator:
    """Validates input length for different contexts."""

    MAX_LENGTHS = {
        "lead_processing": 5000,
        "booking_management": 3000,
        "content_generation": 8000,
        "task_orchestration": 2000,
        "community_engagement": 4000,
        "audience_analysis": 6000,
        "knowledge_retrieval": 1000,
        "workflow_management": 3000,
        "general": 5000,
    }

    @classmethod
    def validate_length(cls, text: str, task_type: str) -> bool:
        """Validate if text length is appropriate for task type."""
        max_length = cls.MAX_LENGTHS.get(task_type, cls.MAX_LENGTHS["general"])
        return len(text) <= max_length

    @classmethod
    def truncate_if_needed(cls, text: str, task_type: str) -> str:
        """Truncate text if it exceeds maximum length."""
        max_length = cls.MAX_LENGTHS.get(task_type, cls.MAX_LENGTHS["general"])
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
