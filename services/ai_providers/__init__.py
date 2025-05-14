"""
AI Provider integrations for The HigherSelf Network Server.
"""

from .base_provider import AIProvider, AIProviderConfig, AICompletionRequest, AICompletionResponse
from .openai_provider import OpenAIProvider, OpenAIConfig
from .anthropic_provider import AnthropicProvider, AnthropicConfig
from .huggingface_provider import HuggingFaceProvider, HuggingFaceConfig

# Import mock provider if available
try:
    from .mock_provider import MockAIProvider
    _has_mock_provider = True
except ImportError:
    _has_mock_provider = False

__all__ = [
    'AIProvider',
    'AIProviderConfig',
    'AICompletionRequest',
    'AICompletionResponse',
    'OpenAIProvider',
    'OpenAIConfig',
    'AnthropicProvider',
    'AnthropicConfig',
    'HuggingFaceProvider',
    'HuggingFaceConfig',
]

# Add mock provider to __all__ if available
if _has_mock_provider:
    __all__.append('MockAIProvider')
