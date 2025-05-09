"""
Base service class for all service integrations in The HigherSelf Network Server.
Provides common functionality for authentication, error handling, and API communication.
"""

import os
import json
import hmac
import hashlib
import asyncio
import aiohttp
from typing import Dict, Any, Optional, Callable, TypeVar, Union, List, Type
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')


class ServiceCredentials(BaseModel):
    """Base model for service credentials."""
    service_name: str
    last_updated: datetime = datetime.now()
    last_verified: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class BaseService:
    """
    Base class for all service integrations.
    Provides common functionality for API communication, authentication, and error handling.
    """
    
    def __init__(self, service_name: str, credentials: Optional[ServiceCredentials] = None):
        """
        Initialize the base service.
        
        Args:
            service_name: Name of the service
            credentials: Optional credentials object
        """
        self.service_name = service_name
        self.credentials = credentials
        self.aiohttp_session: Optional[aiohttp.ClientSession] = None
        
        # Optional initialization timestamps for monitoring
        self.initialized_at: Optional[datetime] = None
        self.last_api_call: Optional[datetime] = None
        self.api_call_count: int = 0
        self.error_count: int = 0
        
        # Configurable retry settings
        self.max_retries = int(os.environ.get(f"{service_name.upper()}_MAX_RETRIES", "3"))
        self.base_retry_delay = float(os.environ.get(f"{service_name.upper()}_RETRY_DELAY", "1.0"))
        self.max_retry_delay = float(os.environ.get(f"{service_name.upper()}_MAX_RETRY_DELAY", "60.0"))
    
    async def initialize(self) -> bool:
        """
        Initialize the service and its dependencies.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Create aiohttp session for async HTTP requests
            self.aiohttp_session = aiohttp.ClientSession()
            
            # Record initialization time
            self.initialized_at = datetime.now()
            
            # Verify credentials if available
            if self.credentials:
                self.credentials.last_verified = datetime.now()
            
            logger.info(f"{self.service_name} service initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error initializing {self.service_name} service: {e}")
            return False
    
    async def close(self) -> None:
        """Close any resources held by the service."""
        if self.aiohttp_session:
            await self.aiohttp_session.close()
            self.aiohttp_session = None
            logger.info(f"Closed aiohttp session for {self.service_name} service")
    
    async def ensure_session(self) -> aiohttp.ClientSession:
        """
        Ensure an aiohttp session exists, creating one if needed.
        
        Returns:
            An active aiohttp ClientSession
        """
        if not self.aiohttp_session or self.aiohttp_session.closed:
            self.aiohttp_session = aiohttp.ClientSession()
            logger.debug(f"Created new aiohttp session for {self.service_name} service")
        
        return self.aiohttp_session
    
    async def execute_with_retry(self, coro, max_retries: Optional[int] = None, 
                               base_delay: Optional[float] = None) -> Any:
        """
        Execute a coroutine with exponential backoff retry logic.
        
        Args:
            coro: Coroutine to execute
            max_retries: Maximum number of retries (defaults to self.max_retries)
            base_delay: Base delay for exponential backoff (defaults to self.base_retry_delay)
            
        Returns:
            Result of the coroutine execution
            
        Raises:
            Exception: If all retries fail
        """
        # Set default values from instance if not provided
        if max_retries is None:
            max_retries = self.max_retries
        
        if base_delay is None:
            base_delay = self.base_retry_delay
        
        retries = 0
        last_exception = None
        
        while True:
            try:
                self.last_api_call = datetime.now()
                self.api_call_count += 1
                result = await coro
                return result
            
            except Exception as e:
                retries += 1
                self.error_count += 1
                last_exception = e
                
                if retries > max_retries:
                    logger.error(f"{self.service_name} API call failed after {max_retries} retries: {e}")
                    raise
                
                # Calculate delay with exponential backoff and jitter
                delay = min(
                    self.max_retry_delay,
                    base_delay * (2 ** (retries - 1)) * (0.9 + 0.2 * asyncio.get_event_loop().time() % 1)
                )
                
                logger.warning(f"{self.service_name} API call failed: {e}. Retry {retries}/{max_retries} after {delay:.2f}s")
                await asyncio.sleep(delay)
    
    async def async_get(self, url: str, headers: Optional[Dict[str, str]] = None, 
                       params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Make an async GET request with retry logic.
        
        Args:
            url: URL to request
            headers: Optional headers
            params: Optional query parameters
            **kwargs: Additional arguments to pass to aiohttp
            
        Returns:
            JSON response data as dictionary
            
        Raises:
            aiohttp.ClientError: If the request fails after all retries
        """
        session = await self.ensure_session()
        
        async def _make_request():
            async with session.get(url, headers=headers, params=params, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        
        return await self.execute_with_retry(_make_request)
    
    async def async_post(self, url: str, data: Optional[Dict[str, Any]] = None, 
                        json_data: Optional[Dict[str, Any]] = None, 
                        headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """
        Make an async POST request with retry logic.
        
        Args:
            url: URL to request
            data: Optional form data
            json_data: Optional JSON data
            headers: Optional headers
            **kwargs: Additional arguments to pass to aiohttp
            
        Returns:
            JSON response data as dictionary
            
        Raises:
            aiohttp.ClientError: If the request fails after all retries
        """
        session = await self.ensure_session()
        
        async def _make_request():
            async with session.post(url, data=data, json=json_data, headers=headers, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        
        return await self.execute_with_retry(_make_request)
    
    async def async_put(self, url: str, data: Optional[Dict[str, Any]] = None, 
                       json_data: Optional[Dict[str, Any]] = None, 
                       headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """
        Make an async PUT request with retry logic.
        
        Args:
            url: URL to request
            data: Optional form data
            json_data: Optional JSON data
            headers: Optional headers
            **kwargs: Additional arguments to pass to aiohttp
            
        Returns:
            JSON response data as dictionary
            
        Raises:
            aiohttp.ClientError: If the request fails after all retries
        """
        session = await self.ensure_session()
        
        async def _make_request():
            async with session.put(url, data=data, json=json_data, headers=headers, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        
        return await self.execute_with_retry(_make_request)
    
    async def async_patch(self, url: str, data: Optional[Dict[str, Any]] = None, 
                         json_data: Optional[Dict[str, Any]] = None, 
                         headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """
        Make an async PATCH request with retry logic.
        
        Args:
            url: URL to request
            data: Optional form data
            json_data: Optional JSON data
            headers: Optional headers
            **kwargs: Additional arguments to pass to aiohttp
            
        Returns:
            JSON response data as dictionary
            
        Raises:
            aiohttp.ClientError: If the request fails after all retries
        """
        session = await self.ensure_session()
        
        async def _make_request():
            async with session.patch(url, data=data, json=json_data, headers=headers, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        
        return await self.execute_with_retry(_make_request)
    
    async def async_delete(self, url: str, headers: Optional[Dict[str, str]] = None, 
                          params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Make an async DELETE request with retry logic.
        
        Args:
            url: URL to request
            headers: Optional headers
            params: Optional query parameters
            **kwargs: Additional arguments to pass to aiohttp
            
        Returns:
            JSON response data as dictionary
            
        Raises:
            aiohttp.ClientError: If the request fails after all retries
        """
        session = await self.ensure_session()
        
        async def _make_request():
            async with session.delete(url, headers=headers, params=params, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        
        return await self.execute_with_retry(_make_request)
    
    async def rotate_credentials(self) -> bool:
        """
        Rotate service credentials periodically for enhanced security.
        This is a placeholder method to be implemented by specific services.
        
        Returns:
            True if rotation successful, False otherwise
        """
        logger.warning(f"Credential rotation not implemented for {self.service_name} service")
        return False
    
    def verify_webhook_signature(self, payload: bytes, signature: str, 
                              secret: str, timestamp: Optional[str] = None) -> bool:
        """
        Verify a webhook signature with optional timestamp validation.
        
        Args:
            payload: Raw request payload bytes
            signature: Signature from webhook request
            secret: Secret key for signature verification
            timestamp: Optional timestamp for freshness validation
            
        Returns:
            True if signature is valid (and timestamp if provided), False otherwise
        """
        # Check timestamp freshness if provided
        if timestamp:
            try:
                # Try parsing as ISO format first
                try:
                    webhook_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    # Then try as unix timestamp
                    webhook_time = datetime.fromtimestamp(float(timestamp))
                
                # Check if timestamp is not too old (within last 5 minutes)
                if datetime.now() - webhook_time > timedelta(minutes=5):
                    logger.warning(f"{self.service_name} webhook timestamp too old: {timestamp}")
                    return False
            
            except Exception as e:
                logger.warning(f"Invalid {self.service_name} webhook timestamp: {e}")
                return False
        
        # Compute HMAC signature
        try:
            computed_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures using constant-time comparison
            return hmac.compare_digest(computed_signature, signature)
        
        except Exception as e:
            logger.error(f"Error verifying {self.service_name} webhook signature: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the health status of the service.
        
        Returns:
            Dictionary with health status information
        """
        now = datetime.now()
        
        return {
            "service_name": self.service_name,
            "status": "healthy" if self.initialized_at else "not_initialized",
            "initialized_at": self.initialized_at.isoformat() if self.initialized_at else None,
            "credentials_verified": self.credentials.last_verified.isoformat() if self.credentials and self.credentials.last_verified else None,
            "last_api_call": self.last_api_call.isoformat() if self.last_api_call else None,
            "uptime_seconds": (now - self.initialized_at).total_seconds() if self.initialized_at else None,
            "api_call_count": self.api_call_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.api_call_count if self.api_call_count > 0 else 0
        }
    
    @staticmethod
    def validate_model(model: BaseModel) -> None:
        """
        Validate a Pydantic model and raise appropriate exceptions for invalid data.
        
        Args:
            model: Pydantic model to validate
            
        Raises:
            ValueError: If validation fails
        """
        # Pydantic models already validate on creation, but this method allows for
        # custom validation logic beyond what Pydantic provides.
        # Subclasses can override for custom validation
        try:
            model_dict = model.dict()
            for field_name, field_value in model_dict.items():
                if field_value is None and field_name in model.__required_fields__:
                    raise ValueError(f"Required field '{field_name}' is missing or None")
        except Exception as e:
            raise ValueError(f"Model validation failed: {e}")
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid, False otherwise
        """
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Validate phone number format.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if phone is valid, False otherwise
        """
        import re
        # Allow for various formats with optional country code
        phone_regex = r'^\+?[0-9]{1,4}?[-.\s]?(\([0-9]{1,3}\)|[0-9]{1,3})[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}$'
        return bool(re.match(phone_regex, phone))
