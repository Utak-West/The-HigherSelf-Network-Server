"""
Notion integration for Hugging Face Pro services.
Synchronizes data between Hugging Face and Notion databases.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from loguru import logger
# Import Notion client
from notion_client import Client
from pydantic import ValidationError

# Local imports
from .config import NotionHuggingFaceConfig
from .models import (HuggingFaceAgent, HuggingFaceDataset,
                     HuggingFaceModelReference, HuggingFaceSpace,
                     NotionHuggingFaceModel)
from .service import HuggingFaceService


class NotionHuggingFaceSync:
    """
    Synchronizes data between Hugging Face and Notion.
    Ensures Notion remains the central data hub while leveraging Hugging Face Pro features.
    """

    def __init__(
        self,
        notion_client: Client,
        hf_service: HuggingFaceService,
        config: NotionHuggingFaceConfig,
    ):
        """
        Initialize the synchronization service.

        Args:
            notion_client: Authenticated Notion client
            hf_service: Initialized Hugging Face service
            config: Integration configuration
        """
        self.notion = notion_client
        self.hf = hf_service
        self.config = config

    def _update_sync_timestamp(self):
        """Update the last synchronization timestamp."""
        self.config.last_sync_timestamp = datetime.now()

    def _add_to_history_log(
        self, notion_page_id: str, action: str, details: Dict[str, Any]
    ):
        """
        Add an entry to the history log in Notion.

        Args:
            notion_page_id: ID of the Notion page
            action: Action being performed
            details: Details about the action
        """
        if not self.config.history_log_enabled:
            return

        try:
            # Get current history log
            page = self.notion.pages.retrieve(notion_page_id)
            current_log = (
                page.get("properties", {}).get("History Log", {}).get("rich_text", [])
            )

            # Format new log entry
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] {action}: {json.dumps(details)}\n"

            # Update the page with the new log entry
            self.notion.pages.update(
                page_id=notion_page_id,
                properties={
                    "History Log": {
                        "rich_text": [
                            {"type": "text", "text": {"content": log_entry}},
                            *current_log,  # Append existing log entries
                        ]
                    },
                    "Last Transition Date": {"date": {"start": timestamp}},
                },
            )
            logger.debug(f"Updated history log for page {notion_page_id}")
        except Exception as e:
            logger.error(
                f"Failed to update history log for page {notion_page_id}: {str(e)}"
            )

    def sync_model_to_notion(self, model: HuggingFaceModelReference) -> str:
        """
        Sync a Hugging Face model reference to Notion.

        Args:
            model: HuggingFaceModelReference object

        Returns:
            Notion page ID
        """
        # Prepare properties for Notion
        properties = {
            "Name": {"title": [{"text": {"content": model.name}}]},
            "Model ID": {"rich_text": [{"text": {"content": model.model_id}}]},
            "Type": {"select": {"name": model.model_type.value}},
            "Description": {
                "rich_text": [{"text": {"content": model.description or ""}}]
            },
            "Status": {"select": {"name": model.status}},
            "URL": {"url": str(model.hub_url)},
            "Tags": {
                "multi_select": [{"name": tag} for tag in model.tags[:10]]
            },  # Notion has a limit
            "Last Updated": {"date": {"start": model.updated_at.isoformat()}},
        }

        # Check if the page already exists
        if model.notion_id:
            # Update existing page
            self.notion.pages.update(page_id=model.notion_id, properties=properties)
            logger.info(f"Updated Notion page for model {model.model_id}")

            # Add to history log
            self._add_to_history_log(
                model.notion_id, "Updated Model Reference", {"model_id": model.model_id}
            )
            return model.notion_id
        else:
            # Create new page
            response = self.notion.pages.create(
                parent={"database_id": self.config.notion_database_id},
                properties=properties,
            )

            notion_id = response["id"]
            logger.info(
                f"Created new Notion page for model {model.model_id} with ID {notion_id}"
            )

            # Add to history log
            self._add_to_history_log(
                notion_id, "Created Model Reference", {"model_id": model.model_id}
            )
            return notion_id

    def sync_space_to_notion(self, space: HuggingFaceSpace) -> str:
        """
        Sync a Hugging Face space reference to Notion.

        Args:
            space: HuggingFaceSpace object

        Returns:
            Notion page ID
        """
        # Prepare properties for Notion
        properties = {
            "Name": {"title": [{"text": {"content": space.name}}]},
            "Space ID": {"rich_text": [{"text": {"content": space.space_id}}]},
            "Framework": {"select": {"name": space.framework.value}},
            "Description": {
                "rich_text": [{"text": {"content": space.description or ""}}]
            },
            "Status": {"select": {"name": space.status}},
            "URL": {"url": str(space.space_url)},
            "Hardware": {"select": {"name": space.hardware}},
            "Tags": {
                "multi_select": [{"name": tag} for tag in space.tags[:10]]
            },  # Notion has a limit
            "Last Updated": {"date": {"start": space.updated_at.isoformat()}},
            "Persistent": {"checkbox": space.persistent},
        }

        # Check if the page already exists
        if space.notion_id:
            # Update existing page
            self.notion.pages.update(page_id=space.notion_id, properties=properties)
            logger.info(f"Updated Notion page for space {space.space_id}")

            # Add to history log
            self._add_to_history_log(
                space.notion_id, "Updated Space Reference", {"space_id": space.space_id}
            )
            return space.notion_id
        else:
            # Create new page
            response = self.notion.pages.create(
                parent={"database_id": self.config.notion_database_id},
                properties=properties,
            )

            notion_id = response["id"]
            logger.info(
                f"Created new Notion page for space {space.space_id} with ID {notion_id}"
            )

            # Add to history log
            self._add_to_history_log(
                notion_id, "Created Space Reference", {"space_id": space.space_id}
            )
            return notion_id

    def sync_agent_to_notion(self, agent: HuggingFaceAgent) -> str:
        """
        Sync a Hugging Face agent configuration to Notion.

        Args:
            agent: HuggingFaceAgent object

        Returns:
            Notion page ID
        """
        # Prepare properties for Notion
        properties = {
            "Name": {"title": [{"text": {"content": agent.name}}]},
            "Base Model": {"rich_text": [{"text": {"content": agent.base_model_id}}]},
            "Description": {
                "rich_text": [{"text": {"content": agent.description or ""}}]
            },
            "Status": {"select": {"name": agent.status}},
            "Tools": {
                "multi_select": [
                    {"name": tool.tool_name[:100]} for tool in agent.tools[:10]
                ]
            },  # Notion has limits
            "Memory Enabled": {"checkbox": agent.memory_enabled},
            "Max Iterations": {"number": agent.max_iterations},
            "Last Updated": {"date": {"start": agent.updated_at.isoformat()}},
        }

        # Add system prompt as a separate content block if it exists
        content = []
        if agent.system_prompt:
            content = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "System Prompt"}}
                        ]
                    },
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": agent.system_prompt}}
                        ]
                    },
                },
            ]

        # Check if the page already exists
        if agent.notion_id:
            # Update existing page
            self.notion.pages.update(page_id=agent.notion_id, properties=properties)

            # Update page content if there's a system prompt
            if content:
                self.notion.blocks.children.append(agent.notion_id, children=content)

            logger.info(f"Updated Notion page for agent {agent.name}")

            # Add to history log
            self._add_to_history_log(
                agent.notion_id,
                "Updated Agent Configuration",
                {"name": agent.name, "tools_count": len(agent.tools)},
            )
            return agent.notion_id
        else:
            # Create new page
            response = self.notion.pages.create(
                parent={"database_id": self.config.notion_database_id},
                properties=properties,
                children=content if content else [],
            )

            notion_id = response["id"]
            logger.info(
                f"Created new Notion page for agent {agent.name} with ID {notion_id}"
            )

            # Add to history log
            self._add_to_history_log(
                notion_id,
                "Created Agent Configuration",
                {"name": agent.name, "tools_count": len(agent.tools)},
            )
            return notion_id

    def get_models_from_notion(self) -> List[HuggingFaceModelReference]:
        """
        Retrieve Hugging Face model references from Notion database.

        Returns:
            List of HuggingFaceModelReference objects
        """
        # Query the database for model entries
        query_filter = {"property": "Type", "select": {"is_not_empty": True}}

        response = self.notion.databases.query(
            database_id=self.config.notion_database_id, filter=query_filter
        )

        models = []
        for page in response.get("results", []):
            try:
                properties = page.get("properties", {})

                # Extract model information from Notion properties
                notion_id = page["id"]
                name = "".join(
                    [
                        text.get("text", {}).get("content", "")
                        for text in properties.get("Name", {}).get("title", [])
                    ]
                )

                model_id = "".join(
                    [
                        text.get("text", {}).get("content", "")
                        for text in properties.get("Model ID", {}).get("rich_text", [])
                    ]
                )

                description = "".join(
                    [
                        text.get("text", {}).get("content", "")
                        for text in properties.get("Description", {}).get(
                            "rich_text", []
                        )
                    ]
                )

                model_type_name = (
                    properties.get("Type", {})
                    .get("select", {})
                    .get("name", "text-generation")
                )
                status = (
                    properties.get("Status", {}).get("select", {}).get("name", "active")
                )

                hub_url = properties.get("URL", {}).get(
                    "url", f"https://huggingface.co/{model_id}"
                )

                tags = [
                    tag.get("name", "")
                    for tag in properties.get("Tags", {}).get("multi_select", [])
                ]

                # Create model reference object
                model = HuggingFaceModelReference(
                    notion_id=notion_id,
                    name=name,
                    description=description,
                    model_id=model_id,
                    model_type=model_type_name,  # This may need validation/conversion
                    hub_url=hub_url,
                    tags=tags,
                    status=status,
                )
                models.append(model)

            except Exception as e:
                logger.error(
                    f"Error parsing model from Notion page {page.get('id')}: {str(e)}"
                )
                continue

        logger.info(f"Retrieved {len(models)} model references from Notion")
        return models

    def get_spaces_from_notion(self) -> List[HuggingFaceSpace]:
        """
        Retrieve Hugging Face space references from Notion database.

        Returns:
            List of HuggingFaceSpace objects
        """
        # Query the database for space entries
        query_filter = {"property": "Framework", "select": {"is_not_empty": True}}

        response = self.notion.databases.query(
            database_id=self.config.notion_database_id, filter=query_filter
        )

        spaces = []
        for page in response.get("results", []):
            try:
                properties = page.get("properties", {})

                # Extract space information from Notion properties
                notion_id = page["id"]
                name = "".join(
                    [
                        text.get("text", {}).get("content", "")
                        for text in properties.get("Name", {}).get("title", [])
                    ]
                )

                space_id = "".join(
                    [
                        text.get("text", {}).get("content", "")
                        for text in properties.get("Space ID", {}).get("rich_text", [])
                    ]
                )

                description = "".join(
                    [
                        text.get("text", {}).get("content", "")
                        for text in properties.get("Description", {}).get(
                            "rich_text", []
                        )
                    ]
                )

                framework_name = (
                    properties.get("Framework", {})
                    .get("select", {})
                    .get("name", "gradio")
                )
                status = (
                    properties.get("Status", {}).get("select", {}).get("name", "active")
                )
                hardware = (
                    properties.get("Hardware", {})
                    .get("select", {})
                    .get("name", "cpu-basic")
                )

                space_url = properties.get("URL", {}).get(
                    "url", f"https://huggingface.co/spaces/{space_id}"
                )

                tags = [
                    tag.get("name", "")
                    for tag in properties.get("Tags", {}).get("multi_select", [])
                ]

                persistent = properties.get("Persistent", {}).get("checkbox", True)

                # Create space reference object
                space = HuggingFaceSpace(
                    notion_id=notion_id,
                    name=name,
                    description=description,
                    space_id=space_id,
                    space_url=space_url,
                    framework=framework_name,  # This may need validation/conversion
                    hardware=hardware,
                    tags=tags,
                    status=status,
                    persistent=persistent,
                )
                spaces.append(space)

            except Exception as e:
                logger.error(
                    f"Error parsing space from Notion page {page.get('id')}: {str(e)}"
                )
                continue

        logger.info(f"Retrieved {len(spaces)} space references from Notion")
        return spaces

    def get_agents_from_notion(self) -> List[HuggingFaceAgent]:
        """
        Retrieve Hugging Face agent configurations from Notion database.

        Returns:
            List of HuggingFaceAgent objects
        """
        # Query the database for agent entries
        query_filter = {"property": "Base Model", "rich_text": {"is_not_empty": True}}

        response = self.notion.databases.query(
            database_id=self.config.notion_database_id, filter=query_filter
        )

        agents = []
        for page in response.get("results", []):
            try:
                properties = page.get("properties", {})

                # Extract agent information from Notion properties
                notion_id = page["id"]
                name = "".join(
                    [
                        text.get("text", {}).get("content", "")
                        for text in properties.get("Name", {}).get("title", [])
                    ]
                )

                base_model_id = "".join(
                    [
                        text.get("text", {}).get("content", "")
                        for text in properties.get("Base Model", {}).get(
                            "rich_text", []
                        )
                    ]
                )

                description = "".join(
                    [
                        text.get("text", {}).get("content", "")
                        for text in properties.get("Description", {}).get(
                            "rich_text", []
                        )
                    ]
                )

                status = (
                    properties.get("Status", {}).get("select", {}).get("name", "active")
                )

                memory_enabled = properties.get("Memory Enabled", {}).get(
                    "checkbox", True
                )
                max_iterations = properties.get("Max Iterations", {}).get("number", 10)

                tool_names = [
                    tag.get("name", "")
                    for tag in properties.get("Tools", {}).get("multi_select", [])
                ]

                # Get system prompt from content blocks if available
                system_prompt = None
                try:
                    blocks = self.notion.blocks.children.list(notion_id).get(
                        "results", []
                    )
                    for block in blocks:
                        if block.get("type") == "paragraph" and block.get(
                            "paragraph", {}
                        ).get("rich_text", []):
                            text_content = "".join(
                                [
                                    text.get("text", {}).get("content", "")
                                    for text in block["paragraph"]["rich_text"]
                                ]
                            )
                            if system_prompt is None:
                                system_prompt = text_content
                            else:
                                system_prompt += "\n" + text_content
                except Exception as e:
                    logger.warning(
                        f"Error retrieving system prompt for agent {name}: {str(e)}"
                    )

                # Create agent tools from tool names
                tools = [
                    AgentToolConfig(
                        tool_name=tool_name, description=f"Tool: {tool_name}"
                    )
                    for tool_name in tool_names
                ]

                # Create agent configuration object
                agent = HuggingFaceAgent(
                    notion_id=notion_id,
                    name=name,
                    description=description,
                    base_model_id=base_model_id,
                    tools=tools,
                    memory_enabled=memory_enabled,
                    system_prompt=system_prompt,
                    max_iterations=max_iterations,
                    status=status,
                )
                agents.append(agent)

            except Exception as e:
                logger.error(
                    f"Error parsing agent from Notion page {page.get('id')}: {str(e)}"
                )
                continue

        logger.info(f"Retrieved {len(agents)} agent configurations from Notion")
        return agents

    def full_sync(self):
        """
        Perform a full synchronization between Notion and Hugging Face.

        This includes:
        1. Retrieving models, spaces, and agents from Notion
        2. Updating Hugging Face resources as needed
        3. Keeping history logs updated
        """
        logger.info("Starting full synchronization between Notion and Hugging Face")

        try:
            # Retrieve resources from Notion
            notion_models = self.get_models_from_notion()
            notion_spaces = self.get_spaces_from_notion()
            notion_agents = self.get_agents_from_notion()

            # Validate all model IDs in Notion
            for model in notion_models:
                try:
                    model_info = self.hf.get_model_info(model.model_id)
                    # Update Notion with latest model info as needed
                    if model.name != model_info.get(
                        "modelId"
                    ) or model.description != model_info.get("description"):
                        self.sync_model_to_notion(model)
                except Exception as e:
                    logger.error(f"Error validating model {model.model_id}: {str(e)}")
                    self._add_to_history_log(
                        model.notion_id, "Validation Error", {"error": str(e)}
                    )

            # Validate all space IDs in Notion
            for space in notion_spaces:
                try:
                    # Check if space exists
                    space_info = self.hf.api.space_info(space.space_id)
                    # Update Notion with latest space info as needed
                    if space.name != space_info.get(
                        "id"
                    ) or space.description != space_info.get("description"):
                        self.sync_space_to_notion(space)
                except Exception as e:
                    logger.error(f"Error validating space {space.space_id}: {str(e)}")
                    self._add_to_history_log(
                        space.notion_id, "Validation Error", {"error": str(e)}
                    )

            # Check agent configurations
            for agent in notion_agents:
                try:
                    # Verify the base model exists
                    self.hf.get_model_info(agent.base_model_id)
                except Exception as e:
                    logger.error(
                        f"Error validating agent base model {agent.base_model_id}: {str(e)}"
                    )
                    self._add_to_history_log(
                        agent.notion_id,
                        "Validation Error",
                        {"error": str(e), "model_id": agent.base_model_id},
                    )

            self._update_sync_timestamp()
            logger.info("Full synchronization completed successfully")

        except Exception as e:
            logger.error(f"Error during full synchronization: {str(e)}")
            raise
