"""
Workflow visualization component for the Advanced Agentic Workflow Engine.

This module generates visual representations of workflow state machines
and their instances, with all data coming from and being stored in Notion
to maintain it as the central hub for all workflow data.
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger

from models.notion_db_models import WorkflowInstance
from services.notion_service import NotionService
from workflow.state_machine import WorkflowStateMachine


class WorkflowVisualizer:
    """
    Generates visualizations of workflow state machines and instances.
    Stores visualization data in Notion to maintain it as the central hub.
    """

    def __init__(self, notion_service: Optional[NotionService] = None):
        """
        Initialize the workflow visualizer.

        Args:
            notion_service: Optional NotionService instance or None to create from environment
        """
        self._notion_service = notion_service
        self.logger = logger.bind(component="WorkflowVisualizer")

    @property
    async def notion_service(self) -> NotionService:
        """Get or create the Notion service."""
        if self._notion_service is None:
            self._notion_service = NotionService.from_env()
        return self._notion_service

    async def generate_workflow_diagram(
        self, workflow: WorkflowStateMachine, instance_id: Optional[str] = None
    ) -> str:
        """
        Generate a Mermaid diagram for a workflow.
        If instance_id is provided, highlights the current state.

        Args:
            workflow: Workflow state machine
            instance_id: Optional workflow instance ID to highlight current state

        Returns:
            Mermaid diagram code
        """
        return await workflow.visualize(instance_id)

    async def update_instance_visualization(
        self, workflow: WorkflowStateMachine, instance_id: str
    ) -> bool:
        """
        Update the visualization for a workflow instance in Notion.

        Args:
            workflow: Workflow state machine
            instance_id: Workflow instance ID

        Returns:
            True if update was successful
        """
        notion_svc = await self.notion_service

        # Get the instance
        instance = await workflow.get_instance(instance_id)
        if not instance:
            self.logger.error(f"Workflow instance {instance_id} not found")
            return False

        # Generate the diagram
        mermaid_diagram = await self.generate_workflow_diagram(workflow, instance_id)

        # Update the instance with the visualization
        instance.context_data["mermaid_visualization"] = mermaid_diagram
        instance.context_data["visualization_updated_at"] = datetime.now().isoformat()

        # Update in Notion
        success = await notion_svc.update_page(instance)

        if success:
            self.logger.info(f"Updated visualization for instance {instance_id}")
        else:
            self.logger.error(
                f"Failed to update visualization for instance {instance_id}"
            )

        return success

    async def generate_instance_history_timeline(self, instance_id: str) -> str:
        """
        Generate a timeline visualization of a workflow instance's history.

        Args:
            instance_id: Workflow instance ID

        Returns:
            Mermaid timeline diagram code
        """
        notion_svc = await self.notion_service

        # Query for the instance
        filter_conditions = {
            "property": "instance_id",
            "rich_text": {"equals": instance_id},
        }

        results = await notion_svc.query_database(WorkflowInstance, filter_conditions)

        if not results:
            self.logger.warning(f"Workflow instance {instance_id} not found")
            return "gantt\n    title Workflow History (Instance Not Found)\n    dateFormat YYYY-MM-DD HH:mm\n"

        instance = results[0]

        # Parse history log to extract state transitions
        transitions = []
        created_at = instance.created_at

        for entry in instance.history_log:
            # Extract timestamp if available (format: "[YYYY-MM-DD HH:mm:ss] Action")
            timestamp_match = re.match(r"\[([^\]]+)\]\s+(.+)", entry)
            if timestamp_match:
                try:
                    timestamp = datetime.fromisoformat(timestamp_match.group(1))
                    action = timestamp_match.group(2)
                except ValueError:
                    # If timestamp parsing fails, use the entry as is
                    timestamp = None
                    action = entry
            else:
                timestamp = None
                action = entry

            # Look for state transitions
            state_transition_match = re.search(
                r"Transitioned from (\w+) to (\w+)", action
            )
            if state_transition_match:
                from_state = state_transition_match.group(1)
                to_state = state_transition_match.group(2)

                transitions.append(
                    {
                        "from_state": from_state,
                        "to_state": to_state,
                        "timestamp": timestamp or created_at,
                        "action": action,
                    }
                )

                # Update for next entry
                created_at = timestamp or created_at

        # Generate Mermaid gantt chart
        mermaid = "gantt\n"
        mermaid += f"    title Workflow History Timeline - {instance.workflow_name}\n"
        mermaid += "    dateFormat YYYY-MM-DD HH:mm\n"
        mermaid += "    axisFormat %m-%d %H:%M\n\n"

        # Add sections for each state
        current_states = set()
        timeline_items = []

        # Add initial state
        initial_state = instance.initial_state or "Created"
        timeline_items.append(
            {
                "section": initial_state,
                "task": "Initial State",
                "start": instance.created_at,
                "end": transitions[0]["timestamp"] if transitions else datetime.now(),
            }
        )
        current_states.add(initial_state)

        # Add transitions
        for i, transition in enumerate(transitions):
            end_time = (
                transitions[i + 1]["timestamp"]
                if i + 1 < len(transitions)
                else datetime.now()
            )

            timeline_items.append(
                {
                    "section": transition["to_state"],
                    "task": f"Transition from {transition['from_state']}",
                    "start": transition["timestamp"],
                    "end": end_time,
                }
            )
            current_states.add(transition["to_state"])

        # Generate the chart sections and tasks
        for state in current_states:
            mermaid += f"    section {state}\n"

            # Add tasks for this state
            state_items = [item for item in timeline_items if item["section"] == state]
            for item in state_items:
                start_str = item["start"].strftime("%Y-%m-%d %H:%M")
                end_str = item["end"].strftime("%Y-%m-%d %H:%M")
                mermaid += f"    {item['task']}: {start_str}, {end_str}\n"

        return mermaid

    async def generate_workflow_dashboard(
        self, workflow: WorkflowStateMachine
    ) -> Dict[str, Any]:
        """
        Generate dashboard statistics for a workflow.

        Args:
            workflow: Workflow state machine

        Returns:
            Dashboard statistics
        """
        notion_svc = await self.notion_service

        # Query for all instances of this workflow
        filter_conditions = {
            "property": "workflow_id",
            "rich_text": {"equals": workflow.workflow_id},
        }

        all_instances = await notion_svc.query_database(
            WorkflowInstance, filter_conditions
        )

        # Collect statistics
        total_instances = len(all_instances)
        active_instances = len([i for i in all_instances if i.status == "Active"])
        completed_instances = len([i for i in all_instances if i.status == "Completed"])

        # Count instances by state
        state_counts = {}
        for instance in all_instances:
            state = instance.current_state
            state_counts[state] = state_counts.get(state, 0) + 1

        # Calculate average time in workflow
        completion_times = []
        for instance in all_instances:
            if (
                instance.status == "Completed"
                and instance.created_at
                and instance.last_transition_date
            ):
                completion_time = (
                    instance.last_transition_date - instance.created_at
                ).total_seconds() / 3600.0  # in hours
                completion_times.append(completion_time)

        avg_completion_time = (
            sum(completion_times) / len(completion_times) if completion_times else 0
        )

        # Generate dashboard data
        dashboard = {
            "workflow_id": workflow.workflow_id,
            "workflow_name": workflow.name,
            "total_instances": total_instances,
            "active_instances": active_instances,
            "completed_instances": completed_instances,
            "state_distribution": state_counts,
            "avg_completion_time_hours": avg_completion_time,
            "generated_at": datetime.now().isoformat(),
        }

        # Generate state distribution chart
        if state_counts:
            pie_chart = "pie\n"
            pie_chart += "    title Workflow State Distribution\n"
            for state, count in state_counts.items():
                pie_chart += f'    "{state}" : {count}\n'

            dashboard["state_distribution_chart"] = pie_chart

        return dashboard

    async def update_dashboard_in_notion(
        self, workflow: WorkflowStateMachine, page_id: str
    ) -> bool:
        """
        Update workflow dashboard in a Notion page.

        Args:
            workflow: Workflow state machine
            page_id: Notion page ID to update

        Returns:
            True if update was successful
        """
        notion_svc = await self.notion_service

        # Generate dashboard
        dashboard = await self.generate_workflow_dashboard(workflow)

        # Format dashboard for Notion
        dashboard_content = {
            "title": f"{workflow.name} Dashboard",
            "statistics": {
                "Total Instances": dashboard["total_instances"],
                "Active Instances": dashboard["active_instances"],
                "Completed Instances": dashboard["completed_instances"],
                "Average Completion Time": f"{dashboard['avg_completion_time_hours']:.2f} hours",
            },
            "state_distribution": dashboard["state_distribution"],
            "state_distribution_chart": dashboard.get("state_distribution_chart", ""),
            "generated_at": dashboard["generated_at"],
        }

        # Update the page with dashboard data
        # Note: This is a simplified implementation that assumes the NotionService
        # has a method to update page content. Actual implementation would depend
        # on your Notion API wrapper.
        try:
            # Convert dashboard content to Notion blocks format
            blocks = [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": dashboard_content["title"]},
                            }
                        ]
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
                                    "content": f"Generated at: {dashboard_content['generated_at']}"
                                },
                            }
                        ]
                    },
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Statistics"}}
                        ]
                    },
                },
            ]

            # Add statistics
            for key, value in dashboard_content["statistics"].items():
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"type": "text", "text": {"content": f"{key}: {value}"}}
                            ]
                        },
                    }
                )

            # Add state distribution chart if available
            if dashboard_content.get("state_distribution_chart"):
                blocks.append(
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "State Distribution"},
                                }
                            ]
                        },
                    }
                )

                blocks.append(
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "language": "mermaid",
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": dashboard_content[
                                            "state_distribution_chart"
                                        ]
                                    },
                                }
                            ],
                        },
                    }
                )

            # Update the page content
            await notion_svc.update_page_content(page_id, blocks)

            self.logger.info(f"Updated dashboard for workflow {workflow.workflow_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}")
            return False

    async def generate_workflow_comparison(
        self, workflows: List[WorkflowStateMachine]
    ) -> str:
        """
        Generate a comparison of multiple workflows.

        Args:
            workflows: List of workflow state machines

        Returns:
            Comparison chart as Mermaid diagram
        """
        # Collect data for each workflow
        workflow_data = []
        for workflow in workflows:
            dashboard = await self.generate_workflow_dashboard(workflow)
            workflow_data.append(
                {
                    "name": workflow.name,
                    "active": dashboard["active_instances"],
                    "completed": dashboard["completed_instances"],
                    "avg_time": dashboard["avg_completion_time_hours"],
                }
            )

        # Generate bar chart for active/completed instances
        bar_chart = "%%{init: {'theme': 'forest'}}%%\n"
        bar_chart += "barchart\n"
        bar_chart += "    title Workflow Comparison\n"
        bar_chart += "    x-axis [Workflow]\n"
        bar_chart += "    y-axis [Instances]\n"

        for data in workflow_data:
            bar_chart += f"    \"{data['name']}\" Active: {data['active']}, Completed: {data['completed']}\n"

        return bar_chart


class NotionWorkflowDashboard:
    """
    Maintains a workflow dashboard in Notion with real-time updates.
    All data is stored in Notion, maintaining it as the central hub.
    """

    def __init__(
        self,
        page_id: str,
        workflows: List[WorkflowStateMachine],
        notion_service: Optional[NotionService] = None,
        update_interval_minutes: int = 60,
    ):
        """
        Initialize the Notion workflow dashboard.

        Args:
            page_id: Notion page ID for the dashboard
            workflows: List of workflow state machines to track
            notion_service: Optional NotionService instance
            update_interval_minutes: Dashboard update interval
        """
        self.page_id = page_id
        self.workflows = workflows
        self._notion_service = notion_service
        self.update_interval = timedelta(minutes=update_interval_minutes)
        self.visualizer = WorkflowVisualizer(notion_service)
        self.logger = logger.bind(component="NotionWorkflowDashboard")
        self.is_running = False
        self.update_task = None

    @property
    async def notion_service(self) -> NotionService:
        """Get or create the Notion service."""
        if self._notion_service is None:
            self._notion_service = NotionService.from_env()
        return self._notion_service

    async def start(self):
        """Start the dashboard update loop."""
        if self.is_running:
            return

        self.is_running = True
        self.update_task = asyncio.create_task(self._update_loop())
        self.logger.info("Notion workflow dashboard started")

    async def stop(self):
        """Stop the dashboard update loop."""
        if not self.is_running:
            return

        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
            self.update_task = None

        self.logger.info("Notion workflow dashboard stopped")

    async def _update_loop(self):
        """Dashboard update loop."""
        await self._update_dashboard()

        while self.is_running:
            try:
                await asyncio.sleep(self.update_interval.total_seconds())
                await self._update_dashboard()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in dashboard update loop: {e}")
                await asyncio.sleep(60)  # Retry after a short delay

    async def _update_dashboard(self):
        """Update the dashboard in Notion."""
        notion_svc = await self.notion_service

        # Initialize or get dashboard blocks
        blocks = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Workflow Dashboard"}}
                    ]
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
                                "content": f"Last updated: {datetime.now().isoformat()}"
                            },
                        }
                    ]
                },
            },
        ]

        # Add workflow comparison chart
        comparison_chart = await self.visualizer.generate_workflow_comparison(
            self.workflows
        )
        blocks.append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Workflow Comparison"}}
                    ]
                },
            }
        )
        blocks.append(
            {
                "object": "block",
                "type": "code",
                "code": {
                    "language": "mermaid",
                    "rich_text": [
                        {"type": "text", "text": {"content": comparison_chart}}
                    ],
                },
            }
        )

        # Add sections for each workflow
        for workflow in self.workflows:
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {"type": "text", "text": {"content": workflow.name}}
                        ]
                    },
                }
            )

            # Get dashboard data
            dashboard = await self.visualizer.generate_workflow_dashboard(workflow)

            # Add statistics
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"Total Instances: {dashboard['total_instances']}\n"
                                },
                            },
                            {
                                "type": "text",
                                "text": {
                                    "content": f"Active Instances: {dashboard['active_instances']}\n"
                                },
                            },
                            {
                                "type": "text",
                                "text": {
                                    "content": f"Completed Instances: {dashboard['completed_instances']}\n"
                                },
                            },
                            {
                                "type": "text",
                                "text": {
                                    "content": f"Avg Completion Time: {dashboard['avg_completion_time_hours']:.2f} hours"
                                },
                            },
                        ]
                    },
                }
            )

            # Add state distribution chart if available
            if dashboard.get("state_distribution_chart"):
                blocks.append(
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "language": "mermaid",
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": dashboard["state_distribution_chart"]
                                    },
                                }
                            ],
                        },
                    }
                )

            # Add workflow diagram
            diagram = await self.visualizer.generate_workflow_diagram(workflow)
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Workflow Diagram"}}
                        ]
                    },
                }
            )
            blocks.append(
                {
                    "object": "block",
                    "type": "code",
                    "code": {
                        "language": "mermaid",
                        "rich_text": [{"type": "text", "text": {"content": diagram}}],
                    },
                }
            )

        # Update the page with all blocks
        try:
            await notion_svc.update_page_content(self.page_id, blocks)
            self.logger.info("Dashboard updated in Notion")
        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}")

    async def update_now(self):
        """Manually trigger dashboard update."""
        await self._update_dashboard()
        self.logger.info("Dashboard manually updated")
