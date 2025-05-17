"""
AI Provider service for The HigherSelf Network Server.
This service manages routing to different AI providers while maintaining Notion as the central hub.
"""

import os
import json
from typing import Dict, List, Any, Optional, Union, Literal
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field, field_validator
# Import base service
from services.base_service import BaseService, ServiceCredentials


class AIProviderCredentials(ServiceCredentials):
    """Credentials for AI Provider services."""
    provider_type: str  # "openai", "anthropic", etc.
    api_key: str
    organization_id: Optional[str] = None
    
    class Config:
        env_prefix = "AI_PROVIDER_"
    
@field_validator('provider_type', mode='before')    def validate_provider_type(cls, v):
        valid_providers = ["openai", "anthropic", "custom"]
        if v not in valid_providers:
            raise ValueError(f"Provider type must be one of: {', '.join(valid_providers)}")
        return v
    
@field_validator('api_key', mode='before')    def validate_api_key(cls, v):
        if not v:
            raise ValueError("API key is required")
        return v


class AIMessage(BaseModel):
    """Model representing a message in an AI conversation."""
    role: str  # "system", "user", "assistant"
    content: str
    
@field_validator('role', mode='before')    def validate_role(cls, v):
        valid_roles = ["system", "user", "assistant", "function"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v
    
@field_validator('content', mode='before')    def validate_content(cls, v):
        if not v:
            raise ValueError("Content is required")
        return v


class AIRequest(BaseModel):
    """Model representing a request to an AI provider."""
    messages: List[AIMessage]
    model: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    provider: Optional[str] = None  # If not specified, use default provider
    stream: bool = False
    function_call: Optional[Dict[str, Any]] = None
    functions: Optional[List[Dict[str, Any]]] = None
    notion_page_id: Optional[str] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)
    
@field_validator('messages', mode='before')    def validate_messages(cls, v):
        if not v:
            raise ValueError("At least one message is required")
        return v
    
@field_validator('model', mode='before')    def validate_model(cls, v):
        if not v:
            raise ValueError("Model is required")
        return v
    
@field_validator('temperature', mode='before')    def validate_temperature(cls, v):
        if v is not None and (v < 0 or v > 2):
            raise ValueError("Temperature must be between 0 and 2")
        return v
    
@field_validator('top_p', mode='before')    def validate_top_p(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError("Top_p must be between 0 and 1")
        return v


class AIResponse(BaseModel):
    """Model representing a response from an AI provider."""
    id: str
    model: str
    provider: str
    content: str
    usage: Dict[str, int] = Field(default_factory=dict)
    created_at: datetime
    finish_reason: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    notion_page_id: Optional[str] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class AIProviderService(BaseService):
    """
    Service for managing AI providers.
    Ensures all requests and responses are synchronized with Notion as the central hub.
    """
    
    def __init__(self, default_provider: str = "openai"):
        """
        Initialize the AI Provider service.
        
        Args:
            default_provider: Default AI provider to use
        """
        # Initialize base service
        super().__init__(service_name="ai_provider")
        
        # Specific properties
        self.default_provider = default_provider
        self.providers = {}
        
        # Initialize providers from environment variables
        self._init_providers()
    
    def _init_providers(self):
        """Initialize available AI providers from environment variables."""
        # OpenAI
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        openai_org_id = os.environ.get("OPENAI_ORGANIZATION_ID")
        
        if openai_api_key:
            try:
                self.providers["openai"] = AIProviderCredentials(
                    service_name="ai_provider",
                    provider_type="openai",
                    api_key=openai_api_key,
                    organization_id=openai_org_id
                )
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.error(f"Error initializing OpenAI provider: {e}")
        
        # Anthropic
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if anthropic_api_key:
            try:
                self.providers["anthropic"] = AIProviderCredentials(
                    service_name="ai_provider",
                    provider_type="anthropic",
                    api_key=anthropic_api_key
                )
                logger.info("Anthropic provider initialized")
            except Exception as e:
                logger.error(f"Error initializing Anthropic provider: {e}")
    
    async def validate_connection(self, provider: Optional[str] = None) -> bool:
        """
        Validate the connection to an AI provider.
        
        Args:
            provider: Provider to validate (if None, validate default provider)
            
        Returns:
            True if connection is valid, False otherwise
        """
        provider_name = provider or self.default_provider
        
        if provider_name not in self.providers:
            logger.error(f"{provider_name} provider not configured")
            return False
        
        provider_credentials = self.providers[provider_name]
        
        try:
            # Test connection with a simple API call
            if provider_name == "openai":
                await self._validate_openai_connection(provider_credentials)
            elif provider_name == "anthropic":
                await self._validate_anthropic_connection(provider_credentials)
            else:
                logger.error(f"Validation not implemented for provider {provider_name}")
                return False
            
            # Update credentials verification timestamp
            provider_credentials.last_verified = datetime.now()
            
            logger.info(f"{provider_name} connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"Error validating {provider_name} connection: {e}")
            return False
    
    async def _validate_openai_connection(self, credentials: AIProviderCredentials) -> bool:
        """
        Validate connection to OpenAI.
        
        Args:
            credentials: OpenAI credentials
            
        Returns:
            True if connection is valid, False otherwise
        """
        headers = {
            "Authorization": f"Bearer {credentials.api_key}",
            "Content-Type": "application/json"
        }
        
        if credentials.organization_id:
            headers["OpenAI-Organization"] = credentials.organization_id
        
        response = await self.async_get(
            "https://api.openai.com/v1/models",
            headers=headers
        )
        
        return "data" in response
    
    async def _validate_anthropic_connection(self, credentials: AIProviderCredentials) -> bool:
        """
        Validate connection to Anthropic.
        
        Args:
            credentials: Anthropic credentials
            
        Returns:
            True if connection is valid, False otherwise
        """
        headers = {
            "x-api-key": credentials.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # We can't just check models with Anthropic, so use a minimal message
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 10,
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }
        
        try:
            await self.async_post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=5  # Short timeout for validation
            )
            return True
        except Exception as e:
            if "401" in str(e):
                logger.error("Anthropic API key is invalid")
            elif "404" in str(e):
                logger.error("Anthropic API endpoint not found")
            else:
                logger.error(f"Anthropic validation error: {e}")
            return False
    
    async def process_request(self, request: AIRequest) -> Optional[AIResponse]:
        """
        Process an AI request and get a response.
        
        Args:
            request: AIRequest containing the request details
            
        Returns:
            AIResponse if successful, None otherwise
        """
        try:
            # Validate request data
            self.validate_model(request)
            
            # Determine provider
            provider_name = request.provider or self.default_provider
            
            if provider_name not in self.providers:
                logger.error(f"{provider_name} provider not configured")
                return None
            
            # Process request based on provider
            if provider_name == "openai":
                return await self._process_openai_request(request)
            elif provider_name == "anthropic":
                return await self._process_anthropic_request(request)
            else:
                logger.error(f"Processing not implemented for provider {provider_name}")
                return None
        except ValueError as e:
            # Handle validation errors
            logger.error(f"Validation error processing AI request: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing AI request: {e}")
            return None
    
    async def _process_openai_request(self, request: AIRequest) -> Optional[AIResponse]:
        """
        Process a request using OpenAI.
        
        Args:
            request: AIRequest for OpenAI
            
        Returns:
            AIResponse if successful, None otherwise
        """
        provider_credentials = self.providers["openai"]
        
        headers = {
            "Authorization": f"Bearer {provider_credentials.api_key}",
            "Content-Type": "application/json"
        }
        
        if provider_credentials.organization_id:
            headers["OpenAI-Organization"] = provider_credentials.organization_id
        
        # Build OpenAI API request
        api_request = {
            "model": request.model,
            "messages": [m.dict() for m in request.messages]
        }
        
        # Add optional parameters if present
        if request.max_tokens is not None:
            api_request["max_tokens"] = request.max_tokens
        
        if request.temperature is not None:
            api_request["temperature"] = request.temperature
        
        if request.top_p is not None:
            api_request["top_p"] = request.top_p
        
        if request.functions:
            api_request["functions"] = request.functions
        
        if request.function_call:
            api_request["function_call"] = request.function_call
        
        try:
            response = await self.async_post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=api_request
            )
            
            # Process OpenAI response
            if "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                
                # Check for function call
                function_call = None
                content = ""
                
                if "message" in choice:
                    message = choice["message"]
                    
                    if "function_call" in message:
                        function_call = message["function_call"]
                    
                    if "content" in message and message["content"]:
                        content = message["content"]
                
                # Build AI response
                ai_response = AIResponse(
                    id=response.get("id", ""),
                    model=response.get("model", request.model),
                    provider="openai",
                    content=content,
                    usage=response.get("usage", {}),
                    created_at=datetime.fromtimestamp(response.get("created", datetime.now().timestamp())),
                    finish_reason=choice.get("finish_reason"),
                    function_call=function_call,
                    notion_page_id=request.notion_page_id,
                    meta_data=request.meta_data.copy()
                )
                
                # If Notion integration is enabled
                if request.notion_page_id:
                    # Add metadata indicating this is managed by Notion
                    ai_response.meta_data["notion_managed"] = True
                    ai_response.meta_data["notion_sync_time"] = datetime.now().isoformat()
                
                return ai_response
            else:
                logger.error("Invalid response from OpenAI API")
                return None
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return None
    
    async def _process_anthropic_request(self, request: AIRequest) -> Optional[AIResponse]:
        """
        Process a request using Anthropic.
        
        Args:
            request: AIRequest for Anthropic
            
        Returns:
            AIResponse if successful, None otherwise
        """
        provider_credentials = self.providers["anthropic"]
        
        headers = {
            "x-api-key": provider_credentials.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Convert message format from OpenAI to Anthropic
        anthropic_messages = []
        
        # Extract system message if present
        system_content = None
        for msg in request.messages:
            if msg.role == "system":
                system_content = msg.content
                break
        
        # Add non-system messages
        for msg in request.messages:
            if msg.role != "system":
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Build Anthropic API request
        api_request = {
            "model": request.model,
            "messages": anthropic_messages,
            "max_tokens": request.max_tokens or 1024
        }
        
        # Add system content if present
        if system_content:
            api_request["system"] = system_content
        
        # Add optional parameters if present
        if request.temperature is not None:
            api_request["temperature"] = request.temperature
        
        if request.top_p is not None:
            api_request["top_p"] = request.top_p
        
        try:
            response = await self.async_post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=api_request
            )
            
            # Process Anthropic response
            if "content" in response and len(response["content"]) > 0:
                # Extract content
                content = response["content"][0]["text"]
                
                # Build AI response
                ai_response = AIResponse(
                    id=response.get("id", ""),
                    model=response.get("model", request.model),
                    provider="anthropic",
                    content=content,
                    usage={
                        "input_tokens": response.get("usage", {}).get("input_tokens", 0),
                        "output_tokens": response.get("usage", {}).get("output_tokens", 0),
                        "total_tokens": response.get("usage", {}).get("input_tokens", 0) + 
                                       response.get("usage", {}).get("output_tokens", 0)
                    },
                    created_at=datetime.now(),  # Anthropic doesn't return a creation timestamp
                    finish_reason=response.get("stop_reason"),
                    function_call=None,  # Anthropic doesn't support function calling in the same way
                    notion_page_id=request.notion_page_id,
                    meta_data=request.meta_data.copy()
                )
                
                # If Notion integration is enabled
                if request.notion_page_id:
                    # Add metadata indicating this is managed by Notion
                    ai_response.meta_data["notion_managed"] = True
                    ai_response.meta_data["notion_sync_time"] = datetime.now().isoformat()
                
                return ai_response
            else:
                logger.error("Invalid response from Anthropic API")
                return None
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            return None
