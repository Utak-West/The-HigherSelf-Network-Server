"""
Base AI provider interface for The HigherSelf Network Server.
All AI providers must implement this interface to ensure consistent interaction.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class AIProviderConfig(BaseModel):
    """Base configuration for AI providers."""
    provider_name: str


class AICompletionRequest(BaseModel):
    """Base model for AI completion requests."""
    prompt: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    stop_sequences: Optional[List[str]] = None
    model: Optional[str] = None
    system_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AICompletionResponse(BaseModel):
    """Base model for AI completion responses."""
    text: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AIProvider(ABC):
    """
    Abstract base class for AI providers.
    All provider implementations must extend this class.
    """

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the AI provider with required credentials and configuration.

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_completion(self, request: AICompletionRequest) -> AICompletionResponse:
        """
        Get a completion from the AI provider.

        Args:
            request: AICompletionRequest with prompt and parameters

        Returns:
            AICompletionResponse with generated text and metadata
        """
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """
        Validate the provider credentials.

        Returns:
            True if credentials are valid, False otherwise
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the AI provider.

        Returns:
            Provider name string
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get a list of available models from this provider.

        Returns:
            List of model identifiers
        """
        pass
