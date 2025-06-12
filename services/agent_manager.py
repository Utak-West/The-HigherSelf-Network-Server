"""Agent Manager Service for The HigherSelf Network Server.

This module provides a service for managing AI agents and processing tasks.
It handles agent registration, task dispatching, and agent status monitoring.
The service maintains a registry of available agents, their capabilities,
and manages the execution of tasks.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import settings
from utils.logging_utils import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class AgentManager:
    """Manager for AI agents in The HigherSelf Network.

    This class handles registration, status tracking, and task routing
    for multiple AI agents with different capabilities.
    """

    def __init__(self):
        """Initialize the agent manager with default agents and task tracking.

        Sets up the initial agent registry with predefined agents and their capabilities.
        Initializes an empty task tracking system.
        """
        self.agents = {
            "content_creator": {
                "name": "Content Creator",
                "description": "Creates various types of content including blog posts, social media, and email newsletters.",
                "status": "active",
                "capabilities": [
                    "blog_post",
                    "social_media",
                    "email_newsletter",
                    "course_content",
                ],
            },
            "marketing_assistant": {
                "name": "Marketing Assistant",
                "description": "Assists with marketing tasks including campaign planning, ad copy, and audience analysis.",
                "status": "active",
                "capabilities": [
                    "campaign_plan",
                    "ad_copy",
                    "audience_analysis",
                    "content_calendar",
                ],
            },
            "research_analyst": {
                "name": "Research Analyst",
                "description": "Conducts research on various topics and provides analysis and insights.",
                "status": "active",
                "capabilities": [
                    "market_research",
                    "competitor_analysis",
                    "trend_report",
                    "literature_review",
                ],
            },
            "community_manager": {
                "name": "Community Manager",
                "description": "Manages community engagement and creates community-related content.",
                "status": "active",
                "capabilities": [
                    "community_update",
                    "engagement_strategy",
                    "member_spotlight",
                    "event_planning",
                ],
            },
        }

        # Track active tasks
        self.active_tasks = {}

    async def process_task(
        self,
        agent_id: str,
        task_type: str,
        parameters: Dict[str, Any],
        description: Optional[str] = None,
    ) -> str:
        """Process a task with the specified agent.

        Validates that the agent exists, is active, and can perform the requested
        task type before delegating the work to the agent.

        Args:
            agent_id: The ID of the agent to use
            task_type: The type of task to perform
            parameters: The parameters for the task
            description: Optional description of the task

        Returns:
            str: The result of the task as HTML content

        Raises:
            ValueError: If the agent doesn't exist, isn't active, or can't perform the task
        """
        logger.info(f"Processing task: agent='{agent_id}', type='{task_type}'")

        # Check if agent exists
        if not agent_id:
            raise ValueError("Agent ID cannot be empty")
        if not task_type:
            raise ValueError("Task type cannot be empty")

        if agent_id not in self.agents:
            raise ValueError(f"Agent not found: '{agent_id}'")

        # Check if agent is active
        if self.agents[agent_id]["status"] != "active":
            raise ValueError(
                f"Agent is not active: '{agent_id}' (current status: '{self.agents[agent_id]['status']}')"
            )

        # Check if agent can perform this task type
        if task_type not in self.agents[agent_id]["capabilities"]:
            available_capabilities = ", ".join(self.agents[agent_id]["capabilities"])
            raise ValueError(
                f"Agent '{agent_id}' cannot perform task type: '{task_type}'. "
                f"Available capabilities: [{available_capabilities}]"
            )

        # In a real implementation, this would call the appropriate agent
        # For now, we'll simulate the agent's response
        result = self._simulate_agent_response(
            agent_id, task_type, parameters, description
        )

        return result

    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get the status of an agent.

        Retrieves the current status, capabilities, and active task count
        for the specified agent.

        Args:
            agent_id: The ID of the agent

        Returns:
            Dict[str, Any]: The agent status information including:
                - agent_id: Agent identifier
                - name: Human-readable name
                - status: Current operational status
                - active_tasks: Number of tasks currently being processed
                - capabilities: List of supported task types

        Raises:
            ValueError: If the agent doesn't exist
        """
        if not agent_id:
            raise ValueError("Agent ID cannot be empty")

        if agent_id not in self.agents:
            raise ValueError(f"Agent not found: '{agent_id}'")

        return {
            "agent_id": agent_id,
            "name": self.agents[agent_id]["name"],
            "status": self.agents[agent_id]["status"],
            "active_tasks": len(
                [t for t in self.active_tasks.values() if t["agent_id"] == agent_id]
            ),
            "capabilities": self.agents[agent_id]["capabilities"],
        }

    async def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all available agents.

        Retrieves information about all registered agents, including
        their status, description, and capabilities.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing agent information
        """
        return [
            {
                "agent_id": agent_id,
                "name": agent["name"],
                "description": agent["description"],
                "status": agent["status"],
                "capabilities": agent["capabilities"],
            }
            for agent_id, agent in self.agents.items()
        ]

    def _simulate_agent_response(
        self,
        agent_id: str,
        task_type: str,
        parameters: Dict[str, Any],
        description: Optional[str] = None,
    ) -> str:
        """Simulate an agent's response to a task.

        This is a mock implementation that generates sample HTML content
        based on the task type and parameters. In a production environment,
        this would call the actual AI agent implementation.

        Args:
            agent_id: The ID of the agent
            task_type: The type of task to perform
            parameters: The parameters for the task
            description: Optional description of the task

        Returns:
            str: HTML content representing the agent's response
        """
        # In a real implementation, this would call the actual AI agent
        # For now, we'll return a simulated response based on the task type

        if task_type == "blog_post":
            title = parameters.get("title", "Untitled Blog Post")
            tone = parameters.get("tone", "informative")
            word_count = parameters.get("wordCount", 1000)

            return f"""
            <h1>{title}</h1>

            <p>This is a simulated blog post written in a {tone} tone. In a real implementation,
            this would be generated by an AI agent with approximately {word_count} words.</p>

            <p>The blog post would cover the main topic and include relevant information, examples,
            and insights. It would be structured with an introduction, several body paragraphs, and
            a conclusion.</p>

            <p>Additional instructions: {description or 'None provided'}</p>
            """

        elif task_type == "social_media":
            platform = parameters.get("platform", "Instagram")
            topic = parameters.get("topic", "general topic")
            include_hashtags = parameters.get("includeHashtags", True)
            call_to_action = parameters.get("callToAction", "")

            post = f"Check out our latest insights on {topic}! {call_to_action}"

            if include_hashtags:
                post += "\n\n#HigherSelfNetwork #PersonalGrowth #Mindfulness"

            return f"""
            <h3>Social Media Post for {platform}</h3>

            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <p>{post}</p>
            </div>

            <p>Additional instructions: {description or 'None provided'}</p>
            """

        elif task_type == "campaign_plan":
            return f"""
            <h2>Marketing Campaign Plan</h2>

            <h3>Campaign Overview</h3>
            <p>This is a simulated marketing campaign plan. In a real implementation,
            this would be generated by an AI agent based on the provided parameters.</p>

            <h3>Target Audience</h3>
            <ul>
                <li>Primary: [Audience description]</li>
                <li>Secondary: [Audience description]</li>
            </ul>

            <h3>Key Messages</h3>
            <ul>
                <li>[Key message 1]</li>
                <li>[Key message 2]</li>
                <li>[Key message 3]</li>
            </ul>

            <h3>Channels</h3>
            <ul>
                <li>Social Media</li>
                <li>Email Marketing</li>
                <li>Content Marketing</li>
            </ul>

            <h3>Timeline</h3>
            <p>Week 1: [Activities]</p>
            <p>Week 2: [Activities]</p>
            <p>Week 3: [Activities]</p>
            <p>Week 4: [Activities]</p>

            <h3>Budget Allocation</h3>
            <p>[Budget breakdown]</p>

            <h3>Success Metrics</h3>
            <ul>
                <li>[Metric 1]</li>
                <li>[Metric 2]</li>
                <li>[Metric 3]</li>
            </ul>

            <p>Additional instructions: {description or 'None provided'}</p>
            """

        # Default response for other task types
        return f"""
        <h2>{task_type.replace('_', ' ').title()} Result</h2>

        <p>This is a simulated response for a {task_type} task. In a real implementation,
        this would be generated by the {self.agents[agent_id]['name']} agent.</p>

        <p>Parameters: {json.dumps(parameters, indent=2)}</p>

        <p>Additional instructions: {description or 'None provided'}</p>
        """


# Singleton instance
_agent_manager = None


def get_agent_manager() -> AgentManager:
    """Get the singleton agent manager instance.

    Creates the instance if it doesn't already exist. This ensures that only
    one AgentManager is used throughout the application, providing consistent
    agent registration and task tracking.

    Returns:
        AgentManager: The global agent manager instance
    """
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager
