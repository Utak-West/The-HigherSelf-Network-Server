"""
Consul Service for Higher Self Network Server.
Provides service registration, discovery, and configuration management capabilities.
"""

import os
import socket
import json
import consul
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional, Set, Union
from loguru import logger
from pydantic import BaseModel, Field
from datetime import datetime

class ServiceDefinition(BaseModel):
    """Service definition for Consul registration."""
    name: str = Field(..., description="Service name")
    id: Optional[str] = Field(None, description="Unique service ID")
    tags: List[str] = Field(default_factory=list, description="Service tags")
    address: Optional[str] = Field(None, description="Service address")
    port: Optional[int] = Field(None, description="Service port")
    meta: Dict[str, str] = Field(default_factory=dict, description="Service metadata")
    check: Optional[Dict[str, Any]] = Field(None, description="Health check configuration")

class ConsulService:
    """Service for Consul integration, providing service discovery and registration."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(ConsulService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the Consul service if not already initialized."""
        if not self._initialized:
            self._initialized = True
            self._consul = None
            self._async_session = None
            self._consul_addr = os.environ.get("CONSUL_HTTP_ADDR", "localhost:8500")
            self._consul_token = os.environ.get("CONSUL_HTTP_TOKEN", "")
            self._dc = os.environ.get("CONSUL_DATACENTER", "dc1")
            self._registered_services = set()
            self._host_ip = None
            self._host_name = socket.gethostname()
            
            # Connect to Consul
            try:
                self._connect()
                logger.info(f"Connected to Consul at {self._consul_addr}")
            except Exception as e:
                logger.error(f"Failed to connect to Consul: {e}")
    
    def _connect(self):
        """Connect to Consul server."""
        if self._consul is None:
            host, port = self._parse_addr(self._consul_addr)
            self._consul = consul.Consul(
                host=host, 
                port=port,
                token=self._consul_token,
                scheme="http"  # Change to https for secure connections
            )
            
    def _parse_addr(self, addr: str) -> tuple:
        """Parse Consul address string into host and port."""
        if ":" in addr:
            host, port_str = addr.split(":")
            return host, int(port_str)
        return addr, 8500  # Default Consul port
    
    async def get_async_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session for async operations."""
        if self._async_session is None or self._async_session.closed:
            self._async_session = aiohttp.ClientSession()
        return self._async_session
    
    async def close_async_session(self):
        """Close the aiohttp session."""
        if self._async_session and not self._async_session.closed:
            await self._async_session.close()
            self._async_session = None
    
    def get_host_ip(self) -> str:
        """Get the host IP address."""
        if self._host_ip is None:
            try:
                # Try to get a non-localhost IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(0.1)
                # Doesn't actually connect but gives us the interface IP
                s.connect(("8.8.8.8", 80))
                self._host_ip = s.getsockname()[0]
                s.close()
            except:
                # Fall back to localhost
                self._host_ip = "127.0.0.1"
        return self._host_ip
    
    def register_service(self, service: ServiceDefinition) -> bool:
        """
        Register a service with Consul.
        
        Args:
            service: Service definition
            
        Returns:
            True if registration was successful, False otherwise
        """
        try:
            # Ensure connection
            self._connect()
            
            # Generate unique ID if not provided
            service_id = service.id
            if service_id is None:
                service_id = f"{service.name}-{self._host_name}-{service.port}"
            
            # Set address to host IP if not provided
            address = service.address
            if address is None:
                address = self.get_host_ip()
            
            # Prepare check if provided
            check = None
            if service.check:
                check = service.check
            
            # Register service
            result = self._consul.agent.service.register(
                name=service.name,
                service_id=service_id,
                address=address,
                port=service.port,
                tags=service.tags,
                check=check,
                meta=service.meta
            )
            
            if result:
                self._registered_services.add(service_id)
                logger.info(f"Registered service {service.name} (ID: {service_id}) with Consul")
            
            return result
        except Exception as e:
            logger.error(f"Failed to register service {service.name}: {e}")
            return False
    
    def deregister_service(self, service_id: str) -> bool:
        """
        Deregister a service from Consul.
        
        Args:
            service_id: Service ID to deregister
            
        Returns:
            True if deregistration was successful, False otherwise
        """
        try:
            # Ensure connection
            self._connect()
            
            # Deregister service
            result = self._consul.agent.service.deregister(service_id)
            
            if result and service_id in self._registered_services:
                self._registered_services.remove(service_id)
                logger.info(f"Deregistered service {service_id} from Consul")
            
            return result
        except Exception as e:
            logger.error(f"Failed to deregister service {service_id}: {e}")
            return False
    
    def get_service(self, service_name: str) -> List[Dict[str, Any]]:
        """
        Get service instances by name.
        
        Args:
            service_name: Service name to look up
            
        Returns:
            List of service instances
        """
        try:
            # Ensure connection
            self._connect()
            
            # Get service
            index, services = self._consul.catalog.service(service_name)
            return services
        except Exception as e:
            logger.error(f"Failed to get service {service_name}: {e}")
            return []
    
    def get_healthy_service(self, service_name: str) -> List[Dict[str, Any]]:
        """
        Get healthy service instances by name.
        
        Args:
            service_name: Service name to look up
            
        Returns:
            List of healthy service instances
        """
        try:
            # Ensure connection
            self._connect()
            
            # Get healthy service
            index, services = self._consul.health.service(service_name, passing=True)
            return services
        except Exception as e:
            logger.error(f"Failed to get healthy service {service_name}: {e}")
            return []
    
    async def async_get_service(self, service_name: str) -> List[Dict[str, Any]]:
        """
        Get service instances by name asynchronously.
        
        Args:
            service_name: Service name to look up
            
        Returns:
            List of service instances
        """
        try:
            # Get session
            session = await self.get_async_session()
            
            # Prepare request
            url = f"http://{self._consul_addr}/v1/catalog/service/{service_name}"
            headers = {}
            if self._consul_token:
                headers["X-Consul-Token"] = self._consul_token
            
            # Make request
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get service {service_name}: HTTP {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Failed to get service {service_name}: {e}")
            return []
    
    async def async_get_healthy_service(self, service_name: str) -> List[Dict[str, Any]]:
        """
        Get healthy service instances by name asynchronously.
        
        Args:
            service_name: Service name to look up
            
        Returns:
            List of healthy service instances
        """
        try:
            # Get session
            session = await self.get_async_session()
            
            # Prepare request
            url = f"http://{self._consul_addr}/v1/health/service/{service_name}?passing=true"
            headers = {}
            if self._consul_token:
                headers["X-Consul-Token"] = self._consul_token
            
            # Make request
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get healthy service {service_name}: HTTP {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Failed to get healthy service {service_name}: {e}")
            return []
    
    def put_key_value(self, key: str, value: Any) -> bool:
        """
        Store a key-value pair in Consul.
        
        Args:
            key: The key
            value: The value (will be JSON-encoded if not a string)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure connection
            self._connect()
            
            # Serialize value if not a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            # Store key-value pair
            result = self._consul.kv.put(key, value)
            
            if result:
                logger.debug(f"Stored key-value pair in Consul: {key}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to store key-value pair {key}: {e}")
            return False
    
    def get_key_value(self, key: str, as_json: bool = False) -> Optional[Any]:
        """
        Get a value from Consul by key.
        
        Args:
            key: The key
            as_json: Whether to parse the result as JSON
            
        Returns:
            The value or None if not found
        """
        try:
            # Ensure connection
            self._connect()
            
            # Get value
            index, data = self._consul.kv.get(key)
            
            if data is None:
                return None
            
            # Extract value
            value = data.get("Value", None)
            
            if value is not None:
                # Decode bytes
                value = value.decode("utf-8")
                
                # Parse as JSON if requested
                if as_json:
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse value for key {key} as JSON")
            
            return value
        except Exception as e:
            logger.error(f"Failed to get value for key {key}: {e}")
            return None
    
    def delete_key_value(self, key: str) -> bool:
        """
        Delete a key-value pair from Consul.
        
        Args:
            key: The key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure connection
            self._connect()
            
            # Delete key-value pair
            result = self._consul.kv.delete(key)
            
            if result:
                logger.debug(f"Deleted key-value pair from Consul: {key}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to delete key-value pair {key}: {e}")
            return False
    
    def register_agent_service(self, agent_id: str, api_port: int = 8000) -> bool:
        """
        Register an agent service with Consul.
        
        Args:
            agent_id: Agent ID
            api_port: API port
            
        Returns:
            True if registration was successful, False otherwise
        """
        service = ServiceDefinition(
            name="agent",
            id=f"agent-{agent_id}",
            tags=["agent", agent_id],
            port=api_port,
            meta={
                "agent_id": agent_id,
                "host": self._host_name,
                "registered_at": datetime.utcnow().isoformat()
            },
            check={
                "http": f"http://localhost:{api_port}/health",
                "interval": "30s",
                "timeout": "5s"
            }
        )
        
        return self.register_service(service)
    
    def register_workflow_service(self, workflow_id: str, api_port: int = 8000) -> bool:
        """
        Register a workflow service with Consul.
        
        Args:
            workflow_id: Workflow ID
            api_port: API port
            
        Returns:
            True if registration was successful, False otherwise
        """
        service = ServiceDefinition(
            name="workflow",
            id=f"workflow-{workflow_id}",
            tags=["workflow", workflow_id],
            port=api_port,
            meta={
                "workflow_id": workflow_id,
                "host": self._host_name,
                "registered_at": datetime.utcnow().isoformat()
            },
            check={
                "http": f"http://localhost:{api_port}/health",
                "interval": "30s",
                "timeout": "5s"
            }
        )
        
        return self.register_service(service)
    
    def register_mcp_tool_service(self, tool_name: str, api_port: int = 8000) -> bool:
        """
        Register an MCP tool service with Consul.
        
        Args:
            tool_name: Tool name
            api_port: API port
            
        Returns:
            True if registration was successful, False otherwise
        """
        service = ServiceDefinition(
            name="mcp-tool",
            id=f"mcp-tool-{tool_name}",
            tags=["mcp-tool", tool_name],
            port=api_port,
            meta={
                "tool_name": tool_name,
                "host": self._host_name,
                "registered_at": datetime.utcnow().isoformat()
            },
            check={
                "http": f"http://localhost:{api_port}/health",
                "interval": "30s",
                "timeout": "5s"
            }
        )
        
        return self.register_service(service)
    
    def cleanup(self):
        """Deregister all registered services."""
        for service_id in list(self._registered_services):
            self.deregister_service(service_id)

# Create a singleton instance
consul_service = ConsulService()
