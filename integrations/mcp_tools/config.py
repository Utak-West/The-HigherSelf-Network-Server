"""
Configuration settings for MCP Tools integration.
"""

import os
from typing import Dict, List, Optional, Set

from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class MCPToolConfig(BaseModel):
    """Configuration model for an individual MCP tool."""

    enabled: bool = True
    server_url: str
    api_key: Optional[str] = None
    auth_type: str = "none"  # none, api_key, oauth
    timeout: int = 30  # seconds
    max_retries: int = 3
    requires_permission: bool = (
        False  # Whether agent needs explicit permission to use this tool
    )
    allowed_agents: Set[str] = Field(
        default_factory=lambda: {"*"}
    )  # * means all agents
    rate_limit_per_min: Optional[int] = None

    class Config:
        extra = "allow"


class MCPConfig:
    """Configuration manager for MCP Tools."""

    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(MCPConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize MCP tool configurations."""
        # Default configurations for supported MCP tools
        self.configs = {
            # Context 7 RAG tool
            "context7": MCPToolConfig(
                server_url=os.environ.get(
                    "MCP_CONTEXT7_URL", "https://api.context7.com/v1"
                ),
                api_key=os.environ.get("MCP_CONTEXT7_API_KEY"),
                auth_type="api_key",
                timeout=45,  # Longer timeout for RAG operations
                requires_permission=False,
                allowed_agents=set(
                    os.environ.get("MCP_CONTEXT7_ALLOWED_AGENTS", "*").split(",")
                ),
            ),
            # Memory tool for knowledge persistence
            "memory": MCPToolConfig(
                server_url=os.environ.get(
                    "MCP_MEMORY_URL", "https://api.memory.dev/v1"
                ),
                api_key=os.environ.get("MCP_MEMORY_API_KEY"),
                auth_type="api_key",
                requires_permission=False,
                allowed_agents=set(
                    os.environ.get("MCP_MEMORY_ALLOWED_AGENTS", "*").split(",")
                ),
            ),
            # Perplexity for advanced search capabilities
            "perplexity": MCPToolConfig(
                server_url=os.environ.get(
                    "MCP_PERPLEXITY_URL", "https://api.perplexity.ai"
                ),
                api_key=os.environ.get("MCP_PERPLEXITY_API_KEY"),
                auth_type="api_key",
                requires_permission=True,  # Requires explicit permission due to potential costs
                allowed_agents=set(
                    os.environ.get(
                        "MCP_PERPLEXITY_ALLOWED_AGENTS", "research,knowledge"
                    ).split(",")
                ),
                rate_limit_per_min=10,
            ),
            # Brave search for web search capabilities
            "brave_search": MCPToolConfig(
                server_url=os.environ.get(
                    "MCP_BRAVE_SEARCH_URL", "https://api.search.brave.com"
                ),
                api_key=os.environ.get("MCP_BRAVE_SEARCH_API_KEY"),
                auth_type="api_key",
                requires_permission=True,
                allowed_agents=set(
                    os.environ.get("MCP_BRAVE_SEARCH_ALLOWED_AGENTS", "research").split(
                        ","
                    )
                ),
                rate_limit_per_min=30,
            ),
            # Sequential thinking for complex reasoning tasks
            "sequential_thinking": MCPToolConfig(
                server_url=os.environ.get(
                    "MCP_SEQ_THINKING_URL", "https://api.sequential-thinking.com"
                ),
                api_key=os.environ.get("MCP_SEQ_THINKING_API_KEY"),
                auth_type="api_key",
                requires_permission=False,
                allowed_agents=set(
                    os.environ.get("MCP_SEQ_THINKING_ALLOWED_AGENTS", "*").split(",")
                ),
            ),
            "devon_ai": MCPToolConfig(
                server_url=os.environ.get(
                    "MCP_DEVON_AI_URL", "https://api.devon.ai/v1"
                ),
                api_key=os.environ.get("DEVON_AI_API_KEY"),
                auth_type="api_key",
                requires_permission=True,
                allowed_agents=set(
                    os.environ.get("MCP_DEVON_AI_ALLOWED_AGENTS", "grace_fields,technical").split(",")
                ),
                rate_limit_per_min=10,
            ),
            "manus_ai": MCPToolConfig(
                server_url=os.environ.get(
                    "MCP_MANUS_AI_URL", "https://api.manus.ai/v1"
                ),
                api_key=os.environ.get("MANUS_AI_API_KEY"),
                auth_type="api_key",
                requires_permission=True,
                allowed_agents=set(
                    os.environ.get("MCP_MANUS_AI_ALLOWED_AGENTS", "grace_fields,strategic").split(",")
                ),
                rate_limit_per_min=15,
            ),
            "genspark": MCPToolConfig(
                server_url=os.environ.get(
                    "MCP_GENSPARK_URL", "https://api.genspark.ai/v1"
                ),
                api_key=os.environ.get("GENSPARK_API_KEY"),
                auth_type="api_key",
                requires_permission=False,
                allowed_agents=set(
                    os.environ.get("MCP_GENSPARK_ALLOWED_AGENTS", "*").split(",")
                ),
                rate_limit_per_min=20,
            ),
        }

        # Load custom tool configurations from environment variables
        self._load_custom_tools()

        # Validate configurations
        self._validate_configs()

    def _load_custom_tools(self):
        """Load custom MCP tool configurations from environment variables."""
        # Format: MCP_TOOL_{NAME}_ENABLED, MCP_TOOL_{NAME}_URL, etc.
        # Example: MCP_TOOL_CUSTOM_RAG_ENABLED=true, MCP_TOOL_CUSTOM_RAG_URL=https://example.com

        custom_tools = {}
        for env_name, env_value in os.environ.items():
            if env_name.startswith("MCP_TOOL_") and "_URL" in env_name:
                tool_name = (
                    env_name.replace("MCP_TOOL_", "").replace("_URL", "").lower()
                )

                # Skip if already defined in default configs
                if tool_name in self.configs:
                    continue

                # Create config for new tool
                enabled_env = f"MCP_TOOL_{tool_name.upper()}_ENABLED"
                api_key_env = f"MCP_TOOL_{tool_name.upper()}_API_KEY"
                auth_type_env = f"MCP_TOOL_{tool_name.upper()}_AUTH_TYPE"
                requires_perm_env = f"MCP_TOOL_{tool_name.upper()}_REQUIRES_PERMISSION"
                allowed_agents_env = f"MCP_TOOL_{tool_name.upper()}_ALLOWED_AGENTS"
                rate_limit_env = f"MCP_TOOL_{tool_name.upper()}_RATE_LIMIT"

                custom_tools[tool_name] = MCPToolConfig(
                    enabled=os.environ.get(enabled_env, "true").lower() == "true",
                    server_url=env_value,
                    api_key=os.environ.get(api_key_env),
                    auth_type=os.environ.get(auth_type_env, "none"),
                    requires_permission=os.environ.get(
                        requires_perm_env, "false"
                    ).lower()
                    == "true",
                    allowed_agents=set(
                        os.environ.get(allowed_agents_env, "*").split(",")
                    ),
                    rate_limit_per_min=(
                        int(rate_limit_value)
                        if (rate_limit_value := os.environ.get(rate_limit_env)) and rate_limit_value.isdigit()
                        else None
                    ),
                )

        # Add custom tools to configs
        self.configs.update(custom_tools)

    def _validate_configs(self):
        """Validate MCP tool configurations."""
        for name, config in self.configs.items():
            if config.enabled:
                # Check required fields based on auth type
                if config.auth_type == "api_key" and not config.api_key:
                    logger.warning(
                        f"MCP tool '{name}' is configured with auth_type='api_key' but no API key is provided. Tool will be disabled."
                    )
                    config.enabled = False

                # Log validation status
                if config.enabled:
                    logger.info(
                        f"MCP tool '{name}' configuration validated and enabled."
                    )
                    if config.requires_permission:
                        logger.info(
                            f"MCP tool '{name}' requires explicit permission for use."
                        )
                else:
                    logger.warning(
                        f"MCP tool '{name}' is disabled due to invalid configuration."
                    )

    def get_config(self, tool_name: str) -> Optional[MCPToolConfig]:
        """Get configuration for a specific MCP tool."""
        return self.configs.get(tool_name.lower())

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a specific MCP tool is enabled."""
        config = self.get_config(tool_name)
        return config is not None and config.enabled

    def is_agent_allowed(self, tool_name: str, agent_id: str) -> bool:
        """Check if an agent is allowed to use a specific MCP tool."""
        config = self.get_config(tool_name)
        if not config or not config.enabled:
            return False

        return "*" in config.allowed_agents or agent_id in config.allowed_agents

    def get_enabled_tools(self) -> Dict[str, MCPToolConfig]:
        """Get all enabled MCP tools."""
        return {name: config for name, config in self.configs.items() if config.enabled}

    def get_tools_for_agent(self, agent_id: str) -> Dict[str, MCPToolConfig]:
        """Get enabled MCP tools available to a specific agent."""
        return {
            name: config
            for name, config in self.configs.items()
            if config.enabled
            and ("*" in config.allowed_agents or agent_id in config.allowed_agents)
        }


# Create a singleton instance
mcp_config = MCPConfig()
