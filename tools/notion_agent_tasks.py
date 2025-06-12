#!/usr/bin/env python3
"""
Notion Agent Tasks Integration

This script sets up and manages a Notion database for AI agent tasks.
It allows staff to create tasks for AI agents and view results directly in Notion.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from notion_client import Client
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Notion API client
notion = Client(auth=os.environ.get("NOTION_API_TOKEN"))

# Notion database ID for agent tasks
NOTION_AGENT_TASKS_DB = os.environ.get("NOTION_AGENT_TASKS_DB")


# Models
class AgentTask(BaseModel):
    """Model representing an agent task."""

    task_id: str
    agent_id: str
    task_type: str
    status: str = "pending"
    priority: str = "medium"
    due_date: Optional[str] = None
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    feedback_rating: Optional[int] = None
    feedback_comments: Optional[str] = None
    notion_page_id: Optional[str] = None


class NotionTasksManager:
    """Manager for Notion agent tasks database."""

    def __init__(self, database_id: Optional[str] = None):
        """Initialize the Notion tasks manager."""
        self.database_id = database_id or NOTION_AGENT_TASKS_DB
        if not self.database_id:
            logger.warning(
                "No Notion database ID provided. Will create a new database."
            )

    def setup_database(self, parent_page_id: str) -> str:
        """
        Create a new Notion database for agent tasks.

        Args:
            parent_page_id: The ID of the parent page where the database will be created.

        Returns:
            The ID of the created database.
        """
        logger.info("Creating new Notion database for agent tasks...")

        # Create the database
        response = notion.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": "AI Agent Tasks"}}],
            properties={
                "Task ID": {"type": "title", "title": {}},
                "Agent": {
                    "type": "select",
                    "select": {
                        "options": [
                            {"name": "Content Creator", "color": "blue"},
                            {"name": "Marketing Assistant", "color": "green"},
                            {"name": "Research Analyst", "color": "orange"},
                            {"name": "Community Manager", "color": "purple"},
                        ]
                    },
                },
                "Task Type": {
                    "type": "select",
                    "select": {
                        "options": [
                            {"name": "Blog Post", "color": "blue"},
                            {"name": "Social Media Post", "color": "green"},
                            {"name": "Email Newsletter", "color": "yellow"},
                            {"name": "Marketing Campaign", "color": "orange"},
                            {"name": "Research Report", "color": "red"},
                            {"name": "Community Update", "color": "purple"},
                            {"name": "Other", "color": "gray"},
                        ]
                    },
                },
                "Status": {
                    "type": "status",
                    "status": {
                        "options": [
                            {"name": "Pending", "color": "yellow"},
                            {"name": "In Progress", "color": "blue"},
                            {"name": "Completed", "color": "green"},
                            {"name": "Failed", "color": "red"},
                        ]
                    },
                },
                "Priority": {
                    "type": "select",
                    "select": {
                        "options": [
                            {"name": "Low", "color": "blue"},
                            {"name": "Medium", "color": "yellow"},
                            {"name": "High", "color": "red"},
                        ]
                    },
                },
                "Due Date": {"type": "date", "date": {}},
                "Created At": {"type": "date", "date": {}},
                "Created By": {"type": "rich_text", "rich_text": {}},
                "Feedback Rating": {"type": "number", "number": {"format": "number"}},
                "Parameters": {"type": "rich_text", "rich_text": {}},
            },
        )

        database_id = response["id"]
        logger.info(f"Created Notion database with ID: {database_id}")

        # Update environment variable
        with open(".env", "r") as f:
            env_content = f.read()

        if "NOTION_AGENT_TASKS_DB=" in env_content:
            env_content = env_content.replace(
                f"NOTION_AGENT_TASKS_DB={NOTION_AGENT_TASKS_DB or ''}",
                f"NOTION_AGENT_TASKS_DB={database_id}",
            )
        else:
            env_content += f"\nNOTION_AGENT_TASKS_DB={database_id}"

        with open(".env", "w") as f:
            f.write(env_content)

        self.database_id = database_id
        return database_id

    def create_task(self, task: AgentTask) -> str:
        """
        Create a new task in the Notion database.

        Args:
            task: The task to create.

        Returns:
            The ID of the created Notion page.
        """
        logger.info(f"Creating Notion task: {task.task_id}")

        # Format parameters for Notion
        parameters_text = json.dumps(task.parameters, indent=2)

        # Create the page
        response = notion.pages.create(
            parent={"database_id": self.database_id},
            properties={
                "Task ID": {"title": [{"text": {"content": task.task_id}}]},
                "Agent": {"select": {"name": self._format_agent_name(task.agent_id)}},
                "Task Type": {
                    "select": {"name": self._format_task_type(task.task_type)}
                },
                "Status": {"status": {"name": self._format_status(task.status)}},
                "Priority": {"select": {"name": self._format_priority(task.priority)}},
                "Created At": {"date": {"start": task.created_at}},
                "Parameters": {"rich_text": [{"text": {"content": parameters_text}}]},
            },
        )

        # Add due date if provided
        if task.due_date:
            notion.pages.update(
                page_id=response["id"],
                properties={"Due Date": {"date": {"start": task.due_date}}},
            )

        # Add created by if provided
        if task.created_by:
            notion.pages.update(
                page_id=response["id"],
                properties={
                    "Created By": {
                        "rich_text": [{"text": {"content": task.created_by}}]
                    }
                },
            )

        # Add task description and parameters as content
        blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Task Description"}}
                    ]
                },
            }
        ]

        if task.description:
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": task.description}}
                        ]
                    },
                }
            )

        blocks.extend(
            [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Parameters"}}
                        ]
                    },
                },
                {
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [
                            {"type": "text", "text": {"content": parameters_text}}
                        ],
                        "language": "json",
                    },
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Results"}}]
                    },
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Results will appear here once the task is completed."
                                },
                            }
                        ]
                    },
                },
            ]
        )

        notion.blocks.children.append(block_id=response["id"], children=blocks)

        logger.info(f"Created Notion task page with ID: {response['id']}")
        return response["id"]

    def update_task_result(
        self, task_id: str, result: str, status: str = "completed"
    ) -> None:
        """
        Update a task with its result.

        Args:
            task_id: The ID of the task to update.
            result: The result of the task.
            status: The new status of the task.
        """
        logger.info(f"Updating task result for task: {task_id}")

        # Find the task page
        query_result = notion.databases.query(
            database_id=self.database_id,
            filter={"property": "Task ID", "title": {"equals": task_id}},
        )

        if not query_result["results"]:
            logger.error(f"Task not found: {task_id}")
            return

        page_id = query_result["results"][0]["id"]

        # Update the status
        notion.pages.update(
            page_id=page_id,
            properties={
                "Status": {"status": {"name": self._format_status(status)}},
            },
        )

        # Find the Results heading block
        blocks = notion.blocks.children.list(block_id=page_id)
        result_block_id = None

        for block in blocks["results"]:
            if (
                block["type"] == "heading_2"
                and block["heading_2"]["rich_text"][0]["text"]["content"] == "Results"
            ):
                # Get the next block (which should be the paragraph to update)
                next_blocks = notion.blocks.children.list(block_id=block["id"])
                if next_blocks["results"]:
                    result_block_id = next_blocks["results"][0]["id"]
                break

        if result_block_id:
            # Update the existing result block
            notion.blocks.update(
                block_id=result_block_id,
                paragraph={
                    "rich_text": [{"type": "text", "text": {"content": result}}]
                },
            )
        else:
            # Append a new result block
            notion.blocks.children.append(
                block_id=page_id,
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": result}}]
                        },
                    }
                ],
            )

        logger.info(f"Updated result for task: {task_id}")

    def update_feedback(
        self, task_id: str, rating: int, comments: Optional[str] = None
    ) -> None:
        """
        Update a task with feedback.

        Args:
            task_id: The ID of the task to update.
            rating: The feedback rating (1-5).
            comments: Optional feedback comments.
        """
        logger.info(f"Updating feedback for task: {task_id}")

        # Find the task page
        query_result = notion.databases.query(
            database_id=self.database_id,
            filter={"property": "Task ID", "title": {"equals": task_id}},
        )

        if not query_result["results"]:
            logger.error(f"Task not found: {task_id}")
            return

        page_id = query_result["results"][0]["id"]

        # Update the rating
        properties = {"Feedback Rating": {"number": rating}}

        notion.pages.update(page_id=page_id, properties=properties)

        # Add feedback comments as content
        if comments:
            notion.blocks.children.append(
                block_id=page_id,
                children=[
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "Feedback"}}
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"type": "text", "text": {"content": comments}}
                            ]
                        },
                    },
                ],
            )

        logger.info(f"Updated feedback for task: {task_id}")

    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent tasks from the Notion database.

        Args:
            limit: The maximum number of tasks to return.

        Returns:
            A list of tasks.
        """
        logger.info(f"Getting recent tasks (limit: {limit})")

        query_result = notion.databases.query(
            database_id=self.database_id,
            sorts=[{"property": "Created At", "direction": "descending"}],
            page_size=limit,
        )

        tasks = []
        for page in query_result["results"]:
            properties = page["properties"]

            task = {
                "task_id": self._get_title_property(properties, "Task ID"),
                "agent_id": self._get_select_property(properties, "Agent"),
                "task_type": self._get_select_property(properties, "Task Type"),
                "status": self._get_status_property(properties, "Status"),
                "priority": self._get_select_property(properties, "Priority"),
                "created_at": self._get_date_property(properties, "Created At"),
                "due_date": self._get_date_property(properties, "Due Date"),
                "created_by": self._get_text_property(properties, "Created By"),
                "feedback_rating": self._get_number_property(
                    properties, "Feedback Rating"
                ),
                "notion_page_id": page["id"],
                "notion_url": page["url"],
            }

            tasks.append(task)

        return tasks

    # Helper methods
    def _format_agent_name(self, agent_id: str) -> str:
        """Format agent ID for Notion display."""
        mapping = {
            "content_creator": "Content Creator",
            "marketing_assistant": "Marketing Assistant",
            "research_analyst": "Research Analyst",
            "community_manager": "Community Manager",
        }
        return mapping.get(agent_id, "Other")

    def _format_task_type(self, task_type: str) -> str:
        """Format task type for Notion display."""
        mapping = {
            "blog_post": "Blog Post",
            "social_media": "Social Media Post",
            "email_newsletter": "Email Newsletter",
            "campaign_plan": "Marketing Campaign",
            "market_research": "Research Report",
            "community_update": "Community Update",
        }
        return mapping.get(task_type, "Other")

    def _format_status(self, status: str) -> str:
        """Format status for Notion display."""
        mapping = {
            "pending": "Pending",
            "in_progress": "In Progress",
            "completed": "Completed",
            "failed": "Failed",
        }
        return mapping.get(status, "Pending")

    def _format_priority(self, priority: str) -> str:
        """Format priority for Notion display."""
        mapping = {"low": "Low", "medium": "Medium", "high": "High"}
        return mapping.get(priority, "Medium")

    def _get_title_property(self, properties: Dict[str, Any], name: str) -> str:
        """Extract title property from Notion properties."""
        if name in properties and properties[name]["title"]:
            return properties[name]["title"][0]["text"]["content"]
        return ""

    def _get_select_property(self, properties: Dict[str, Any], name: str) -> str:
        """Extract select property from Notion properties."""
        if name in properties and properties[name]["select"]:
            return properties[name]["select"]["name"]
        return ""

    def _get_status_property(self, properties: Dict[str, Any], name: str) -> str:
        """Extract status property from Notion properties."""
        if name in properties and properties[name]["status"]:
            return properties[name]["status"]["name"]
        return ""

    def _get_date_property(
        self, properties: Dict[str, Any], name: str
    ) -> Optional[str]:
        """Extract date property from Notion properties."""
        if name in properties and properties[name]["date"]:
            return properties[name]["date"]["start"]
        return None

    def _get_text_property(self, properties: Dict[str, Any], name: str) -> str:
        """Extract rich text property from Notion properties."""
        if name in properties and properties[name]["rich_text"]:
            return properties[name]["rich_text"][0]["text"]["content"]
        return ""

    def _get_number_property(
        self, properties: Dict[str, Any], name: str
    ) -> Optional[int]:
        """Extract number property from Notion properties."""
        if name in properties and properties[name]["number"] is not None:
            return properties[name]["number"]
        return None


def main():
    """Main function to set up the Notion database."""
    parent_page_id = os.environ.get("NOTION_PARENT_PAGE_ID")

    if not parent_page_id:
        logger.error("NOTION_PARENT_PAGE_ID environment variable is required.")
        return

    manager = NotionTasksManager()

    if not manager.database_id:
        database_id = manager.setup_database(parent_page_id)
        logger.info(f"Created Notion database: {database_id}")
    else:
        logger.info(f"Using existing Notion database: {manager.database_id}")


if __name__ == "__main__":
    main()
