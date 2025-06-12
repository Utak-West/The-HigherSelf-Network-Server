"""
AI Provider integrations for The HigherSelf Network Server.
"""

from .anthropic_provider import AnthropicConfig, AnthropicProvider
from .base_provider import (
    AICompletionRequest,
    AICompletionResponse,
    AIProvider,
    AIProviderConfig,
)
from .huggingface_provider import HuggingFaceConfig, HuggingFaceProvider
from .openai_provider import OpenAIConfig, OpenAIProvider

# Import mock provider if available
try:
    from .mock_provider import MockAIProvider

    _has_mock_provider = True
except ImportError:
    _has_mock_provider = False

__all__ = [
    "AIProvider",
    "AIProviderConfig",
    "AICompletionRequest",
    "AICompletionResponse",
    "OpenAIProvider",
    "OpenAIConfig",
    "AnthropicProvider",
    "AnthropicConfig",
    "HuggingFaceProvider",
    "HuggingFaceConfig",
]

# Add mock provider to __all__ if available
if _has_mock_provider:
    __all__.append("MockAIProvider")
