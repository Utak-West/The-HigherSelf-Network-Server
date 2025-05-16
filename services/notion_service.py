"""
Notion integration service for The HigherSelf Network Server.
Handles all interactions with the Notion API, following the standardized
data structures and patterns defined in the Pydantic models.
"""

import os
import json
from loguru import logger
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
from models.video_models import VideoContent
from models.video_transaction_models import VideoTransaction, VideoTransactionStatus

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
        # self.logger removed, use global loguru logger
        logger.info(f"Notion service initialized with {len(self.db_mappings)} database mappings for {self.__class__.__name__}")

        # Check if we're in testing mode
        if is_api_disabled("notion"):
            logger.warning(f"TESTING MODE ACTIVE for {self.__class__.__name__}: Notion API calls will be simulated")

    @classmethod
    def from_env(cls) -> 'NotionService':
        """Create a NotionService instance using environment variables."""
        # Check if we're in test mode - check both TEST_MODE and TESTING
        if os.environ.get('TEST_MODE', '').lower() == 'true' or os.environ.get('TESTING', '').lower() == 'true':
            # Create a mock config for testing
            token = "mock_token_for_testing"
            logger.info("Test mode active: Using mock Notion configuration")
        else:
            # Use real token from environment
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
                logger.info(f"[TESTING MODE] Simulated creating page in {db_type} database")
                return f"test_page_id_{db_type}_{model.id if hasattr(model, 'id') else id(model)}"

            response = self.client.pages.create(
                parent={"database_id": db_id},
                properties=properties
            )

            return response["id"]

        except Exception as e:
            logger.error(f"Error creating Notion page: {e}")
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
                logger.info(f"[TESTING MODE] Simulated updating page {model.page_id}")
                return True

            self.client.pages.update(
                page_id=model.page_id,
                properties=properties
            )

            return True

        except Exception as e:
            logger.error(f"Error updating Notion page: {e}")
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
                # Force disable the API in testing mode
                from config.testing_mode import TestingMode
                TestingMode.add_disabled_api("notion")

                TestingMode.log_attempted_api_call(
                    api_name="notion",
                    endpoint="databases.query",
                    method="POST",
                    params=query_params
                )
                logger.info(f"[TESTING MODE] Simulated querying {db_type} database")
                # Return empty list in testing mode
                return []

            response = self.client.databases.query(**query_params)

            results = []
            for page in response.get("results", []):
                try:
                    model = self._notion_to_model(page, model_class)
                    results.append(model)
                except ValidationError as e:
                    logger.warning(f"Error converting Notion page to model: {e}")

            return results

        except Exception as e:
            logger.error(f"Error querying Notion database: {e}")
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

            # logger.info already here, no change needed for this specific block's logger call
            logger.info(f"Updated history log for workflow instance {workflow_instance.instance_id}")
            return True

        except Exception as e:
            # logger.error already here
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

    # Video Transaction Methods

    async def create_video_transaction(self, transaction: VideoTransaction) -> str:
        """
        Create a video transaction record in Notion.

        Args:
            transaction: VideoTransaction model

        Returns:
            ID of the created page
        """
        try:
            # Ensure we have a database mapping for VideoTransaction
            if "VideoTransaction" not in self.db_mappings:
                # If not in mappings, try to get from environment
                import os
                self.db_mappings["VideoTransaction"] = os.environ.get("NOTION_VIDEO_TRANSACTIONS_DB", "")

                if not self.db_mappings["VideoTransaction"]:
                    raise ValueError("No database mapping found for VideoTransaction")

            db_id = self.db_mappings["VideoTransaction"]
            properties = self._model_to_notion_properties(transaction)

            # Check if Notion API is disabled in testing mode
            if is_api_disabled("notion"):
                TestingMode.log_attempted_api_call(
                    api_name="notion",
                    endpoint="pages.create",
                    method="POST",
                    params={"parent": {"database_id": db_id}, "properties": properties}
                )
                logger.info(f"[TESTING MODE] Simulated creating video transaction in Notion")
                return f"test_page_id_VideoTransaction_{transaction.transaction_id}"

            response = self.client.pages.create(
                parent={"database_id": db_id},
                properties=properties
            )

            transaction_id = response["id"]
            logger.info(f"Created video transaction in Notion with ID: {transaction_id}")
            return transaction_id

        except Exception as e:
            logger.error(f"Error creating video transaction in Notion: {e}")
            raise

    async def update_video_transaction(self, page_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a video transaction in Notion.

        Args:
            page_id: Notion page ID
            updates: Dictionary of fields to update

        Returns:
            True if update was successful
        """
        try:
            # Convert updates to Notion properties format
            properties = {}

            for key, value in updates.items():
                if key == "transaction_status":
                    properties["transaction_status"] = {
                        "select": {"name": value}
                    }
                elif key == "payment_status":
                    properties["payment_status"] = {
                        "select": {"name": value}
                    }
                elif key == "updated_at":
                    properties["updated_at"] = {
                        "date": {"start": value.isoformat()}
                    }
                elif key == "expires_at" and value:
                    properties["expires_at"] = {
                        "date": {"start": value.isoformat()}
                    }
                # Add other fields as needed

            # Check if Notion API is disabled in testing mode
            if is_api_disabled("notion"):
                TestingMode.log_attempted_api_call(
                    api_name="notion",
                    endpoint="pages.update",
                    method="PATCH",
                    params={"page_id": page_id, "properties": properties}
                )
                logger.info(f"[TESTING MODE] Simulated updating video transaction {page_id}")
                return True

            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )

            logger.info(f"Updated video transaction in Notion with ID: {page_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating video transaction in Notion: {e}")
            return False

    async def get_video_transaction(self, transaction_id: str) -> Optional[VideoTransaction]:
        """
        Get a video transaction from Notion by ID.

        Args:
            transaction_id: Notion page ID

        Returns:
            VideoTransaction model or None if not found
        """
        try:
            # Check if Notion API is disabled in testing mode
            if is_api_disabled("notion"):
                TestingMode.log_attempted_api_call(
                    api_name="notion",
                    endpoint="pages.retrieve",
                    method="GET",
                    params={"page_id": transaction_id}
                )
                logger.info(f"[TESTING MODE] Simulated retrieving video transaction {transaction_id}")

                # Return a mock transaction in testing mode
                return VideoTransaction(
                    id=transaction_id,
                    transaction_id=f"vt-test-{transaction_id[-8:]}",
                    video_id=f"vid-test-{transaction_id[-8:]}",
                    customer_email="test@example.com",
                    customer_name="Test User",
                    transaction_type="premium_feature",
                    transaction_status=VideoTransactionStatus.COMPLETED,
                    payment_id=f"pay-test-{transaction_id[-8:]}",
                    payment_status="completed",
                    amount=29.99,
                    currency="usd",
                    features=[{
                        "feature_id": "feat-001",
                        "feature_type": "export_4k",
                        "name": "4K Export",
                        "description": "Export video in 4K resolution",
                        "price": 29.99
                    }],
                    business_entity_id="test_entity",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

            # Retrieve the page from Notion
            page = self.client.pages.retrieve(page_id=transaction_id)

            # Convert to model
            transaction = self._notion_to_model(page, VideoTransaction)
            return transaction

        except Exception as e:
            logger.error(f"Error getting video transaction from Notion: {e}")
            return None

    async def find_transaction_by_payment_id(self, payment_id: str) -> Optional[VideoTransaction]:
        """
        Find a video transaction by payment ID.

        Args:
            payment_id: Payment ID to search for

        Returns:
            VideoTransaction model or None if not found
        """
        try:
            # Ensure we have a database mapping for VideoTransaction
            if "VideoTransaction" not in self.db_mappings:
                # If not in mappings, try to get from environment
                import os
                self.db_mappings["VideoTransaction"] = os.environ.get("NOTION_VIDEO_TRANSACTIONS_DB", "")

                if not self.db_mappings["VideoTransaction"]:
                    raise ValueError("No database mapping found for VideoTransaction")

            db_id = self.db_mappings["VideoTransaction"]

            # Prepare query
            query_params = {
                "database_id": db_id,
                "filter": {
                    "property": "payment_id",
                    "rich_text": {
                        "equals": payment_id
                    }
                }
            }

            # Check if Notion API is disabled in testing mode
            if is_api_disabled("notion"):
                TestingMode.log_attempted_api_call(
                    api_name="notion",
                    endpoint="databases.query",
                    method="POST",
                    params=query_params
                )
                logger.info(f"[TESTING MODE] Simulated querying for transaction with payment ID {payment_id}")

                # Return a mock transaction in testing mode
                return VideoTransaction(
                    id=f"test_page_id_VideoTransaction_{payment_id}",
                    transaction_id=f"vt-{payment_id}",
                    video_id=f"vid-test-{payment_id[-8:]}",
                    customer_email="test@example.com",
                    customer_name="Test User",
                    transaction_type="premium_feature",
                    transaction_status=VideoTransactionStatus.PENDING,
                    payment_id=payment_id,
                    payment_status="pending",
                    amount=29.99,
                    currency="usd",
                    features=[{
                        "feature_id": "feat-001",
                        "feature_type": "export_4k",
                        "name": "4K Export",
                        "description": "Export video in 4K resolution",
                        "price": 29.99
                    }],
                    business_entity_id="test_entity",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

            # Query Notion
            response = self.client.databases.query(**query_params)

            # Check if any results
            if not response["results"]:
                return None

            # Convert first result to model
            transaction = self._notion_to_model(response["results"][0], VideoTransaction)
            return transaction

        except Exception as e:
            logger.error(f"Error finding transaction by payment ID: {e}")
            return None

    async def find_video_content_by_task_id(self, task_id: str) -> Optional[VideoContent]:
        """
        Find video content by task ID.

        Args:
            task_id: Task ID to search for

        Returns:
            VideoContent model or None if not found
        """
        try:
            # Ensure we have a database mapping for VideoContent
            if "VideoContent" not in self.db_mappings:
                # If not in mappings, try to get from environment
                import os
                self.db_mappings["VideoContent"] = os.environ.get("NOTION_VIDEO_CONTENT_DB", "")

                if not self.db_mappings["VideoContent"]:
                    raise ValueError("No database mapping found for VideoContent")

            db_id = self.db_mappings["VideoContent"]

            # Prepare query
            query_params = {
                "database_id": db_id,
                "filter": {
                    "property": "task_id",
                    "rich_text": {
                        "equals": task_id
                    }
                }
            }

            # Check if Notion API is disabled in testing mode
            if is_api_disabled("notion"):
                TestingMode.log_attempted_api_call(
                    api_name="notion",
                    endpoint="databases.query",
                    method="POST",
                    params=query_params
                )
                logger.info(f"[TESTING MODE] Simulated querying for video content with task ID {task_id}")

                # Return a mock video content in testing mode
                return VideoContent(
                    id=f"test_page_id_VideoContent_{task_id}",
                    title=f"Test Video - {task_id[-8:]}",
                    description="Test video description",
                    content_type="VIDEO",
                    stage="IDEA",
                    business_entity_id="test_entity",
                    topic="Test Topic",
                    resolution="1920x1080",
                    video_status="pending",
                    task_id=task_id,
                    created_by="Test Agent",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

            # Query Notion
            response = self.client.databases.query(**query_params)

            # Check if any results
            if not response["results"]:
                return None

            # Convert first result to model
            video_content = self._notion_to_model(response["results"][0], VideoContent)
            return video_content

        except Exception as e:
            logger.error(f"Error finding video content by task ID: {e}")
            return None




