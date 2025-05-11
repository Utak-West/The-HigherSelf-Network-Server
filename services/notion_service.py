"""
Notion integration service for The HigherSelf Network Server.
Handles all interactions with the Notion API, following the standardized
data structures and patterns defined in the Pydantic models.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Type, Union, TypeVar
from datetime import datetime

from pydantic import ValidationError, BaseModel
from notion_client import Client

from models.notion import NotionPage, NotionIntegrationConfig
from config.testing_mode import is_api_disabled, TestingMode
from models.notion_db_models import (
    BusinessEntity, Agent, Workflow, WorkflowInstance,
    ApiIntegration, DataTransformation, UseCase,
    NotificationTemplate, AgentCommunication, Task,
    AIContentReview
)

# Add AgentBestPractices, WorkflowPatterns, and AgentTrainingResults to database mappings
# These will be used by the Grace Fields training system


T = TypeVar('T', bound=BaseModel)


class NotionService:
    """Service for interacting with Notion databases via the Notion API."""

    def __init__(self, config: NotionIntegrationConfig):
        """
        Initialize the Notion service with the provided configuration.

        Args:
            config: NotionIntegrationConfig containing API token and database mappings
        """
        self.config = config
        self.client = Client(auth=config.token)
        self.db_mappings = config.database_mappings
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Notion service initialized with {len(self.db_mappings)} database mappings")

        # Check if we're in testing mode
        if is_api_disabled("notion"):
            self.logger.warning("TESTING MODE ACTIVE: Notion API calls will be simulated")

    @classmethod
    def from_env(cls) -> 'NotionService':
        """Create a NotionService instance using environment variables."""
        token = os.environ.get('NOTION_API_TOKEN')
        if not token:
            raise ValueError("NOTION_API_TOKEN environment variable not set")

        # Create database mappings from environment variables
        db_mappings = {
            'BusinessEntity': os.environ.get('NOTION_BUSINESS_ENTITIES_DB', ''),
            'Agent': os.environ.get('NOTION_AGENT_REGISTRY_DB', ''),
            'Workflow': os.environ.get('NOTION_WORKFLOWS_LIBRARY_DB', ''),
            'WorkflowInstance': os.environ.get('NOTION_ACTIVE_WORKFLOW_INSTANCES_DB', ''),
            'ApiIntegration': os.environ.get('NOTION_API_INTEGRATIONS_DB', ''),
            'DataTransformation': os.environ.get('NOTION_DATA_TRANSFORMATIONS_DB', ''),
            'UseCase': os.environ.get('NOTION_USE_CASES_DB', ''),
            'NotificationTemplate': os.environ.get('NOTION_NOTIFICATIONS_TEMPLATES_DB', ''),
            'AgentCommunication': os.environ.get('NOTION_AGENT_COMMUNICATION_DB', ''),
            'Task': os.environ.get('NOTION_TASKS_DB', ''),
            # Add Grace Fields training databases
            'AgentBestPractices': os.environ.get('NOTION_BEST_PRACTICES_DB', ''),
            'WorkflowPatterns': os.environ.get('NOTION_WORKFLOW_PATTERNS_DB', ''),
            'AgentTrainingResults': os.environ.get('NOTION_TRAINING_RESULTS_DB', ''),
        }

        # Validate that all required database IDs are present
        for key, value in db_mappings.items():
            if not value:
                logger.warning(f"Database ID for {key} not set in environment variables")

        config = NotionIntegrationConfig(
            token=token,
            database_mappings=db_mappings,
            last_sync=datetime.now()
        )

        return cls(config)

    def _model_to_notion_properties(self, model: BaseModel) -> Dict[str, Any]:
        """
        Convert a Pydantic model to Notion properties format.

        Args:
            model: Pydantic model to convert

        Returns:
            Dictionary of Notion properties
        """
        properties = {}
        model_dict = model.dict(exclude={'page_id'})

        for field_name, field_value in model_dict.items():
            if field_value is None:
                continue

            # Handle different field types
            if isinstance(field_value, str):
                properties[field_name] = {"rich_text": [{"text": {"content": field_value}}]}

                # Title fields need special handling
                if field_name in ["name", "agent_id", "workflow_id", "instance_id",
                                 "platform", "transformation_name", "use_case_id",
                                 "template_id", "pattern_name", "task_id", "content_title"]:
                    properties[field_name] = {"title": [{"text": {"content": field_value}}]}

            elif isinstance(field_value, bool):
                properties[field_name] = {"checkbox": field_value}

            elif isinstance(field_value, (int, float)):
                properties[field_name] = {"number": field_value}

            elif isinstance(field_value, datetime):
                properties[field_name] = {"date": {"start": field_value.isoformat()}}

            elif isinstance(field_value, list):
                if field_value and isinstance(field_value[0], str):
                    # Handle multi-select and relation properties
                    # This is simplified and would need customization based on actual schema
                    properties[field_name] = {"multi_select": [{"name": item} for item in field_value]}

            elif isinstance(field_value, dict):
                # For complex objects, store as JSON in a text field
                json_str = json.dumps(field_value)
                properties[field_name] = {"rich_text": [{"text": {"content": json_str}}]}

        return properties

    def _notion_to_model(self, notion_page: Dict[str, Any], model_class: Type[T]) -> T:
        """
        Convert a Notion page to a Pydantic model.

        Args:
            notion_page: Notion page data
            model_class: Pydantic model class to convert to

        Returns:
            Instance of the specified Pydantic model
        """
        model_data = {"page_id": notion_page["id"]}
        properties = notion_page.get("properties", {})

        for prop_name, prop_value in properties.items():
            prop_type = next(iter(prop_value.keys())) if prop_value else None

            if not prop_type:
                continue

            # Extract value based on property type
            if prop_type == "title":
                content = prop_value["title"][0]["text"]["content"] if prop_value["title"] else ""
                model_data[prop_name] = content

            elif prop_type == "rich_text":
                if prop_value["rich_text"]:
                    content = prop_value["rich_text"][0]["text"]["content"]
                    # Try to parse JSON for complex objects
                    try:
                        if content.startswith("{") or content.startswith("["):
                            model_data[prop_name] = json.loads(content)
                        else:
                            model_data[prop_name] = content
                    except json.JSONDecodeError:
                        model_data[prop_name] = content

            elif prop_type == "number":
                model_data[prop_name] = prop_value["number"]

            elif prop_type == "checkbox":
                model_data[prop_name] = prop_value["checkbox"]

            elif prop_type == "date":
                if prop_value["date"]:
                    date_str = prop_value["date"]["start"]
                    model_data[prop_name] = datetime.fromisoformat(date_str)

            elif prop_type == "select":
                if prop_value["select"]:
                    model_data[prop_name] = prop_value["select"]["name"]

            elif prop_type == "multi_select":
                model_data[prop_name] = [item["name"] for item in prop_value["multi_select"]]

            elif prop_type == "relation":
                model_data[prop_name] = [item["id"] for item in prop_value["relation"]]

        return model_class(**model_data)

    async def create_page(self, model: BaseModel) -> str:
        """
        Create a new page in the appropriate Notion database.

        Args:
            model: Pydantic model to create a page from

        Returns:
            ID of the created page
        """
        try:
            # Determine the database type from the model class
            db_type = model.__class__.__name__

            if db_type not in self.db_mappings:
                raise ValueError(f"No database mapping found for model type: {db_type}")

            db_id = self.db_mappings[db_type]
            properties = self._model_to_notion_properties(model)

            # Check if Notion API is disabled in testing mode
            if is_api_disabled("notion"):
                TestingMode.log_attempted_api_call(
                    api_name="notion",
                    endpoint="pages.create",
                    method="POST",
                    params={"parent": {"database_id": db_id}, "properties": properties}
                )
                self.logger.info(f"[TESTING MODE] Simulated creating page in {db_type} database")
                return f"test_page_id_{db_type}_{model.id if hasattr(model, 'id') else id(model)}"

            response = self.client.pages.create(
                parent={"database_id": db_id},
                properties=properties
            )

            return response["id"]

        except Exception as e:
            self.logger.error(f"Error creating Notion page: {e}")
            raise

    async def update_page(self, model: BaseModel) -> bool:
        """
        Update an existing page in Notion.

        Args:
            model: Pydantic model with updated data

        Returns:
            True if update was successful
        """
        try:
            if not hasattr(model, "page_id") or not model.page_id:
                raise ValueError("Model must have a page_id attribute to update")

            properties = self._model_to_notion_properties(model)

            # Check if Notion API is disabled in testing mode
            if is_api_disabled("notion"):
                TestingMode.log_attempted_api_call(
                    api_name="notion",
                    endpoint="pages.update",
                    method="PATCH",
                    params={"page_id": model.page_id, "properties": properties}
                )
                self.logger.info(f"[TESTING MODE] Simulated updating page {model.page_id}")
                return True

            self.client.pages.update(
                page_id=model.page_id,
                properties=properties
            )

            return True

        except Exception as e:
            self.logger.error(f"Error updating Notion page: {e}")
            return False

    async def get_page(self, page_id: str, model_class: Type[T]) -> T:
        """
        Retrieve a specific page from Notion and convert to a Pydantic model.

        Args:
            page_id: Notion page ID
            model_class: Pydantic model class to convert to

        Returns:
            Instance of the specified Pydantic model
        """
        response = self.client.pages.retrieve(page_id=page_id)
        return self._notion_to_model(response, model_class)

    async def query_database(
        self,
        model_class: Type[T],
        filter_conditions: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        limit: int = 100
    ) -> List[T]:
        """
        Query a Notion database based on filter conditions.

        Args:
            model_class: Pydantic model class to convert results to
            filter_conditions: Optional Notion filter conditions
            sorts: Optional sort specifications
            limit: Maximum number of results to return

        Returns:
            List of model instances matching the query
        """
        try:
            db_type = model_class.__name__

            if db_type not in self.db_mappings:
                raise ValueError(f"No database mapping found for model type: {db_type}")

            db_id = self.db_mappings[db_type]

            query_params = {"database_id": db_id}

            if filter_conditions:
                query_params["filter"] = filter_conditions

            if sorts:
                query_params["sorts"] = sorts

            if limit:
                query_params["page_size"] = min(limit, 100)  # Notion API limits to 100

            # Check if Notion API is disabled in testing mode
            if is_api_disabled("notion"):
                TestingMode.log_attempted_api_call(
                    api_name="notion",
                    endpoint="databases.query",
                    method="POST",
                    params=query_params
                )
                self.logger.info(f"[TESTING MODE] Simulated querying {db_type} database")
                # Return empty list in testing mode
                return []

            response = self.client.databases.query(**query_params)

            results = []
            for page in response.get("results", []):
                try:
                    model = self._notion_to_model(page, model_class)
                    results.append(model)
                except ValidationError as e:
                    self.logger.warning(f"Error converting Notion page to model: {e}")

            return results

        except Exception as e:
            self.logger.error(f"Error querying Notion database: {e}")
            return []

    async def append_to_history_log(self, workflow_instance: WorkflowInstance, action: str, details: Dict[str, Any] = None) -> bool:
        """
        Append an entry to the history log of a workflow instance.

        Args:
            workflow_instance: WorkflowInstance model with page_id set
            action: Description of the action
            details: Optional details about the action

        Returns:
            True if update was successful
        """
        if not workflow_instance.page_id:
            raise ValueError("WorkflowInstance does not have a page_id set")

        # Get the current history log
        try:
            current_instance = await self.get_page(workflow_instance.page_id, WorkflowInstance)

            # Add the new entry to the history log
            workflow_instance.add_history_entry(action, details)

            # Convert the history log to a JSON string
            history_log_json = json.dumps(workflow_instance.history_log)

            # Update just the history_log property
            self.client.pages.update(
                page_id=workflow_instance.page_id,
                properties={
                    "history_log": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": history_log_json
                                }
                            }
                        ]
                    },
                    "last_transition_date": {
                        "date": {
                            "start": workflow_instance.last_transition_date.isoformat()
                        }
                    }
                }
            )

            logger.info(f"Updated history log for workflow instance {workflow_instance.instance_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating history log: {e}")
            return False

    async def update_workflow_instance_state(
        self,
        instance_id: str,
        new_state: str,
        action_description: str,
        details: Dict[str, Any] = None
    ) -> bool:
        """
        Update the state of a workflow instance and log the transition.

        Args:
            instance_id: ID of the workflow instance
            new_state: New state to transition to
            action_description: Description of the state transition
            details: Optional details about the state transition

        Returns:
            True if update was successful
        """
        # Query for the workflow instance
        filter_conditions = {
            "property": "instance_id",
            "rich_text": {
                "equals": instance_id
            }
        }

        instances = await self.query_database(WorkflowInstance, filter_conditions, limit=1)

        if not instances:
            logger.error(f"No workflow instance found with ID {instance_id}")
            return False

        instance = instances[0]

        # Update the state
        instance.current_state = new_state
        instance.add_history_entry(action_description, details)

        # Update the instance in Notion
        return await self.update_page(instance)

    async def create_task_from_workflow(
        self,
        workflow_instance: WorkflowInstance,
        task_name: str,
        description: str,
        assigned_to: Optional[str] = None,
        due_date: Optional[datetime] = None,
        priority: str = "Medium"
    ) -> Task:
        """
        Create a task in the Master Tasks Database linked to a workflow instance.

        Args:
            workflow_instance: The workflow instance the task is related to
            task_name: Name of the task
            description: Task description
            assigned_to: Optional user to assign the task to
            due_date: Optional due date
            priority: Task priority (default: Medium)

        Returns:
            Created Task model
        """
        task = Task(
            task_name=task_name,
            description=description,
            assigned_to=assigned_to,
            due_date=due_date,
            priority=priority,
            related_workflow_instance=workflow_instance.instance_id,
            related_business_entity=workflow_instance.business_entity,
            created_by=f"Agent-{workflow_instance.current_state}"
        )

        page_id = await self.create_page(task)
        task.page_id = page_id

        # Log the task creation in the workflow instance history
        await self.append_to_history_log(
            workflow_instance=workflow_instance,
            action=f"Created task: {task_name}",
            details={
                "task_id": task.task_id,
                "assigned_to": assigned_to,
                "due_date": due_date.isoformat() if due_date else None
            }
        )

        return task

    async def query_database(self, database_id: str, filter_conditions: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Query a Notion database with optional filter conditions.

        Args:
            database_id: ID or name of the database to query
            filter_conditions: Optional filter conditions

        Returns:
            List of database items matching the filter
        """
        # Resolve database ID if a name was provided
        if not database_id.startswith("db_") and not database_id.startswith("database_"):
            database_id = self.get_database_id(database_id)

        try:
            # Prepare query parameters
            params = {}
            if filter_conditions:
                params["filter"] = filter_conditions

            # Execute the query
            response = await self.notion.databases.query(database_id, **params)

            # Process the results
            results = []
            for page in response.get("results", []):
                # Extract properties
                properties = page.get("properties", {})
                item = {"id": page.get("id")}

                # Process each property
                for prop_name, prop_data in properties.items():
                    prop_type = prop_data.get("type")

                    if prop_type == "title":
                        title_array = prop_data.get("title", [])
                        item["name"] = "".join([text.get("plain_text", "") for text in title_array])
                    elif prop_type == "rich_text":
                        text_array = prop_data.get("rich_text", [])
                        item[prop_name.lower()] = "".join([text.get("plain_text", "") for text in text_array])
                    elif prop_type == "select":
                        select_data = prop_data.get("select")
                        if select_data:
                            item[prop_name.lower()] = select_data.get("name")
                    elif prop_type == "multi_select":
                        multi_select = prop_data.get("multi_select", [])
                        item[prop_name.lower()] = [option.get("name") for option in multi_select]
                    elif prop_type == "checkbox":
                        item[prop_name.lower()] = prop_data.get("checkbox", False)
                    elif prop_type == "date":
                        date_data = prop_data.get("date")
                        if date_data:
                            item[prop_name.lower()] = date_data.get("start")
                    elif prop_type == "number":
                        item[prop_name.lower()] = prop_data.get("number")

                results.append(item)

            return results
        except Exception as e:
            self.logger.error(f"Error querying Notion database {database_id}: {e}")
            return []

    async def create_page(self, database_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new page in a Notion database.

        Args:
            database_id: ID or name of the database
            properties: Properties for the new page

        Returns:
            Created page data
        """
        # Resolve database ID if a name was provided
        if not database_id.startswith("db_") and not database_id.startswith("database_"):
            database_id = self.get_database_id(database_id)

        try:
            # Convert properties to Notion format
            notion_properties = {}

            for key, value in properties.items():
                # Convert property name to title case for Notion
                prop_name = " ".join(word.capitalize() for word in key.split("_"))

                if key == "name" or key == "title":
                    # Title property
                    notion_properties["Name"] = {
                        "title": [{"text": {"content": str(value)}}]
                    }
                elif isinstance(value, bool):
                    # Checkbox property
                    notion_properties[prop_name] = {
                        "checkbox": value
                    }
                elif isinstance(value, (int, float)):
                    # Number property
                    notion_properties[prop_name] = {
                        "number": value
                    }
                elif isinstance(value, list):
                    # Multi-select property
                    notion_properties[prop_name] = {
                        "multi_select": [{"name": str(item)} for item in value]
                    }
                elif key.lower() in ["date", "timestamp", "due_date", "start_date", "end_date"]:
                    # Date property
                    notion_properties[prop_name] = {
                        "date": {"start": value}
                    }
                else:
                    # Default to rich text
                    notion_properties[prop_name] = {
                        "rich_text": [{"text": {"content": str(value)}}]
                    }

            # Create the page
            response = await self.notion.pages.create(
                parent={"database_id": database_id},
                properties=notion_properties
            )

            return {"id": response.get("id"), "status": "success"}
        except Exception as e:
            self.logger.error(f"Error creating page in Notion database {database_id}: {e}")
            return {"error": str(e), "status": "error"}

    def get_database_id(self, database_name: str) -> str:
        """
        Get the database ID from a database name.

        Args:
            database_name: Name of the database

        Returns:
            Database ID
        """
        # Map of database names to IDs
        database_map = {
            "AgentBestPractices": os.getenv("NOTION_BEST_PRACTICES_DB"),
            "WorkflowPatterns": os.getenv("NOTION_WORKFLOW_PATTERNS_DB"),
            "AgentTrainingResults": os.getenv("NOTION_TRAINING_RESULTS_DB")
        }

        if database_name in database_map:
            return database_map[database_name]
        else:
            self.logger.warning(f"Unknown database name: {database_name}")
            return database_name  # Return the name as is, might be an ID already

    async def create_workflow_record(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a workflow record in Notion.

        Args:
            workflow_data: Workflow data to record

        Returns:
            Created record data
        """
        # Get the workflows database ID
        database_id = self.get_database_id("Workflows")

        # Create the workflow record
        return await self.create_page(database_id, workflow_data)
